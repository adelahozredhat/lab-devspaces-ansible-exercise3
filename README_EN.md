# lab-devspaces-ansible-exercise3

**This exercise is designed to be completed inside OpenShift Dev Spaces.**

Lab image versions (check with `python3 --version`, `ansible --version`, `ansible-test --version`):

| Tool | Version in Dev Spaces |
| ---- | --------------------- |
| Python | **3.12** (`python3.12`) |
| ansible-core | **2.21.x** |
| ansible-test | **2.21.x** |

Commands in this guide use `--python 3.12`. If `python3 --version` shows something else, substitute the number.

## What is an Ansible collection?

An **Ansible collection** is a versioned package that groups reusable content under a **namespace** and a **name** (`namespace.collection_name`). Inside it can include, among other things:

- **Python modules, plugins, and utilities** (`plugins/`), including `module_utils` shared by several modules.
- **Roles** (`roles/`) with the usual structure of tasks, handlers, meta, etc.
- **Playbooks**, documentation, Galaxy metadata (`galaxy.yml`), Ansible requirements (`meta/runtime.yml`), and **tests** under `tests/`.

Collections are published on [Ansible Galaxy](https://galaxy.ansible.com/), installed with `ansible-galaxy collection install`, and in playbooks modules are referenced with the **FQCN** (fully qualified collection name), for example `namespace_example.collection_example.get_servers`.

## Goal of this lab

Understand the **structure** of a collection and how the role, the module, the tests, and `ansible-test` fit together. Walk the tree, locate each piece, and **run** the tools below.

**Done when:** the collection is installed, and `sanity` (with `--exclude tests/output/`), `units` (`--venv`), and `integration` exit 0. The sample playbook must run with the integration variables.

## Contents of `template-ansible-collection-develop`

In the `template-ansible-collection-develop/` directory there is a template-style project. The actual collection lives in:

`template-ansible-collection-develop/ansible_collections/namespace_example/collection_example/`

According to `galaxy.yml`, the collection is identified as **`namespace_example.collection_example`**: namespace `namespace_example`, name `collection_example`.

When you walk the tree, use **this guide** and the collection `README.md`. The role README is a short description of the sample; `roles/get_server_example_role/tests/test.yml` is leftover Galaxy scaffolding (it expects a `prueba-result.txt` that is not shipped) and is **not** part of the lab: do not run it.

### Included role: `get_server_example_role`

In `roles/get_server_example_role/` there is a sample role that:

- Invokes the collection module `namespace_example.collection_example.get_servers` with variables (`example_username`, `example_password`, `example_url`, `example_techgroups`, and so on).
- `example_techgroups` is a YAML **list** (the module declares `type: list`).
- Registers the result, shows a `debug`, and writes the output to `{{ playbook_dir }}/prueba.txt`.

It shows **how a role consumes a module from the same collection** using the FQCN. The role has **no** `defaults/`: those variables come from `tests/integration/integration_config.yml` (or `-e` when you run the playbook).

### Module and supporting code (plugins)

Under `plugins/` you will find:

| Path | Description |
| :--- | :---------- |
| `plugins/modules/get_servers.py` | **`get_servers`** module: obtains server lists (with their *hostvars*) via a HAIINV-style API; options such as `username`, `password`, `url`, `proxy`, `techgroups`, `environment`. |
| `plugins/module_utils/haiinv.py` | Shared utilities to talk to the API. |
| `plugins/module_utils/exceptions.py` | Exceptions used by the module and the utilities. |

In Ansible documentation, this kind of file under `plugins/modules/` is often called a module-type **plugin** generically; here the lab focus is to see **where the Python code lives** and how it relates to the role and the tests.

The helper concatenates `url + techgroup + environment` when calling the API. Against the public sample JSON the hosts come back nested (`hosts.hosts` in the `debug`). That is the sample module’s behaviour, not a failure of your run.

### Other useful folders for orientation

- `meta/runtime.yml`: supported Ansible version (`requires_ansible`). This template already ships `">=2.10"` (no `2.19` ceiling) for Dev Spaces ansible-core **2.21**.
- `playbooks/playbook.yml`: usage example (needs `example_*` variables; see below).
- `tests/unit/`: unit tests (module and `module_utils`). The helper file is named `commun_test.py` (historical typo for *common*).
- `tests/integration/targets/get_server/`: integration target that exercises the module.
- `tests/output/`: created by `ansible-test` during your runs (JUnit, coverage). Do not treat leftover files as proof of a previous run. Exclude this directory when running sanity. It is listed in `.gitignore`.
- Collection `requirements.txt`: only declares `requests`. **Do not** `pip install -r requirements.txt` into the Dev Spaces system Python; `ansible-test --requirements` installs deps in its own venvs.

## Environment (OpenShift Dev Spaces)

The `devfile.yaml` file defines a workspace with the **ansible-devspaces** image. You do not need to install Ansible by hand.

## Tests with `ansible-test` and coverage

All of the following commands must be run **from the collection root directory** (where `galaxy.yml` is):

```bash
cd template-ansible-collection-develop/ansible_collections/namespace_example/collection_example
```

### Install the collection

Check `meta/runtime.yml`. It must be `requires_ansible: ">=2.10"`. If an older copy still ends with `<=2.19`, change it and save: Dev Spaces ansible-core **2.21.2** does not satisfy that ceiling and `ansible-galaxy collection install` aborts.

```bash
ansible-galaxy collection install . -p ~/.ansible/collections --force
```

**Do not follow Galaxy’s Hint** to set `COLLECTIONS_ON_ANSIBLE_VERSION_MISMATCH=ignore` as an environment variable: on ansible-core 2.21 it is **not enough** and the install still fails.

If you cannot edit `runtime.yml`, create an `ansible.cfg` in that directory:

```ini
[defaults]
collections_on_ansible_version_mismatch = ignore
```

Galaxy does **not** copy `galaxy.yml` into the install path: you get `MANIFEST.json` and `FILES.json`. Verify the install like this:

```bash
ansible-galaxy collection list | grep namespace_example
ls ~/.ansible/collections/ansible_collections/namespace_example/collection_example/MANIFEST.json
```

The `ansible-test` `--requirements` flag installs test dependencies when needed.

### Sanity (`sanity`)

Checks format, syntax, module documentation, and other standard checks of the Ansible ecosystem:

```bash
ansible-test sanity -v --python 3.12 --requirements --exclude tests/output/
```

`--exclude tests/output/` is required after you have already run `units`/`integration` (or if leftover files remain): otherwise sanity walks thousands of JUnit XML files.

If the `ansible-doc` test fails with a WARNING *Collection … does not support Ansible version 2.21*, go back to `meta/runtime.yml` (same issue as Galaxy).

### Unit tests (`units`)

Runs the Python tests under `tests/unit/` (`get_servers` module and `module_utils`).

In the **ansible-devspaces** image, system Python may ship **pytest-ansible**, which breaks `ansible-test units` (collection paths with `:`). `ansible-test` **does not forward** `PYTEST_ADDOPTS` to the pytest subprocess.

**Solution:** use **`--venv`**. `ansible-test` creates a virtualenv and installs only the `units` dependencies; **pytest-ansible** from the image does not get in there.

The collection declares in **`tests/unit/requirements.txt`** the **`requests`** dependency: without it, `plugins/module_utils/haiinv.py` loads an empty stub (`class Haiinv: pass`) and the module tests fail.

```bash
ansible-test units --venv --python 3.12 --requirements --coverage
```

This should exit 0. The `set_module_args` helper in `tests/unit/modules/commun_test.py` sets the serialization profile (`_ANSIBLE_PROFILE = 'legacy'`) that ansible-core 2.19+ requires. If you see `No serialization profile was specified.`, the helper is not being applied.

`tests/unit/modules/test_integration_get_servers.py` is **not** the integration target: those are unit tests that hit the public JSON. Real integration is the next step.

### Integration tests (`integration`)

Runs the `get_server` target under `tests/integration/` (uses `tests/integration/integration_config.yml` and a public sample JSON):

```bash
ansible-test integration --python 3.12 --requirements
```

This warning is **expected**; the target runs on the workspace itself and the exit code should still be 0:

```text
WARNING: Unable to determine context for the following test targets, they will be run on the target host: get_server
```

You can combine integration with coverage:

```bash
ansible-test integration --python 3.12 --requirements --coverage
```

The integration inventory uses `python3.12`. `ansible-test --python 3.12` sets the interpreter for the run. This target does not need `sudo`.

### Sample playbook

`playbooks/playbook.yml` includes the role but **does not** define `example_*`. Run it with the integration file:

```bash
ansible-playbook playbooks/playbook.yml -e @tests/integration/integration_config.yml
```

Without `-e`, Ansible fails with undefined variables (`example_environment`, and so on).

The role writes the result to **`playbooks/prueba.txt`** (the playbook’s `playbook_dir`), not the collection root. The `debug` may show nested hosts (`hosts.hosts`); that is the shape the sample module returns against this JSON.

### Code coverage reports

After `units` or `integration` with `--coverage`:

```bash
ansible-test coverage combine --requirements
ansible-test coverage report --requirements
ansible-test coverage html --requirements
```

Without `--requirements`, `ansible-test` may demand a specific `coverage` module that is not on system Python.

In Dev Spaces, `--requirements` pip installs into `~/.local` (`Defaulting to user installation because normal site-packages is not writeable`). The **first** `coverage combine` sometimes ends with `FATAL: Version 7.10.7 of the Python "coverage" module must be installed` even though pip just installed it. **Run the same command again**; the second attempt usually works.

The HTML lands at `tests/output/reports/coverage/index.html`. Open it from the IDE (Simple Browser / preview); do not expect a desktop browser.

## Summary (checklist)

| Step | Action |
|------|--------|
| 1 | Walk `plugins/`, `roles/`, `playbooks/`, `tests/`, `meta/runtime.yml`, `galaxy.yml`. |
| 2 | Confirm `requires_ansible: ">=2.10"` (no `<=2.19`). |
| 3 | `ansible-galaxy collection install . -p ~/.ansible/collections --force` and verify with `collection list` / `MANIFEST.json`. |
| 4 | `ansible-test sanity --python 3.12 --requirements --exclude tests/output/` |
| 5 | `ansible-test units --venv --python 3.12 --requirements --coverage` |
| 6 | `ansible-test integration --python 3.12 --requirements` (the context WARNING is normal). |
| 7 | `ansible-playbook playbooks/playbook.yml -e @tests/integration/integration_config.yml` (look at `playbooks/prueba.txt`). |
| 8 | (Optional) `ansible-test coverage combine/report/html --requirements` (if `combine` asks for coverage 7.10.7, rerun the command). |

## Expected result

- You know where the module, role, playbook, and tests live.
- The collection installs under `~/.ansible/collections` against ansible-core 2.21 (`MANIFEST.json` present).
- `sanity` (excluding `tests/output/`), `units --venv`, and `integration` exit 0.
- The sample playbook runs with the variables from `integration_config.yml` and leaves `playbooks/prueba.txt`.

## References

- [Using collections](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html)
- [Developing collections](https://docs.ansible.com/ansible/latest/dev_guide/developing_collections.html)
- [ansible-test](https://docs.ansible.com/ansible/latest/dev_guide/testing_integration.html)
