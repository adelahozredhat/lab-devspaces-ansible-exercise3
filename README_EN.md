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

**Done when:** the collection is installed, `sanity` (with `--exclude tests/output/`) and `integration` pass, and if `units` fails on ansible-core 2.21 you understand why (units section). The sample playbook must run with the integration variables.

## Contents of `template-ansible-collection-develop`

In the `template-ansible-collection-develop/` directory there is a template-style project. The actual collection lives in:

`template-ansible-collection-develop/ansible_collections/namespace_example/collection_example/`

According to `galaxy.yml`, the collection is identified as **`namespace_example.collection_example`**: namespace `namespace_example`, name `collection_example`.

### Included role: `get_server_example_role`

In `roles/get_server_example_role/` there is a sample role that:

- Invokes the collection module `namespace_example.collection_example.get_servers` with variables (`example_username`, `example_password`, `example_url`, etc.).
- Registers the result, shows a `debug`, and writes the output to a sample file.

It shows **how a role consumes a module from the same collection** using the FQCN. The role has **no** `defaults/`: those variables come from `tests/integration/integration_config.yml` (or `-e` when you run the playbook).

### Module and supporting code (plugins)

Under `plugins/` you will find:

| Path | Description |
| :--- | :---------- |
| `plugins/modules/get_servers.py` | **`get_servers`** module: obtains server lists (with their *hostvars*) via a HAIINV-style API; options such as `username`, `password`, `url`, `proxy`, `techgroups`, `environment`. |
| `plugins/module_utils/haiinv.py` | Shared utilities to talk to the API. |
| `plugins/module_utils/exceptions.py` | Exceptions used by the module and the utilities. |

In Ansible documentation, this kind of file under `plugins/modules/` is often called a module-type **plugin** generically; here the lab focus is to see **where the Python code lives** and how it relates to the role and the tests.

### Other useful folders for orientation

- `meta/runtime.yml`: supported Ansible version (`requires_ansible`). **Dev Spaces ships ansible-core 2.21**; if the file caps at `<=2.19`, Galaxy and `ansible-doc` fail. It must be at least `requires_ansible: ">=2.10"` (no `2.19` ceiling).
- `playbooks/playbook.yml`: usage example (needs `example_*` variables; see below).
- `tests/unit/`: unit tests (module and `module_utils`).
- `tests/integration/targets/get_server/`: integration target that exercises the module.
- `tests/output/`: **leftovers from previous runs** (JUnit, coverage). Not your result. Treat them only as sample reports; exclude this directory when running sanity.

## Environment (OpenShift Dev Spaces)

The `devfile.yaml` file defines a workspace with the **ansible-devspaces** image. You do not need to install Ansible by hand.

## Tests with `ansible-test` and coverage

All of the following commands must be run **from the collection root directory** (where `galaxy.yml` is):

```bash
cd template-ansible-collection-develop/ansible_collections/namespace_example/collection_example
```

### Install the collection

Check `meta/runtime.yml`. If `requires_ansible` ends with `<=2.19`, change it to `">=2.10"` and save: Dev Spaces ansible-core **2.21.2** does not satisfy that ceiling and `ansible-galaxy collection install` aborts.

```bash
ansible-galaxy collection install . -p ~/.ansible/collections --force
```

If you cannot edit `runtime.yml`, create an `ansible.cfg` in that directory:

```ini
[defaults]
collections_on_ansible_version_mismatch = ignore
```

(The `COLLECTIONS_ON_ANSIBLE_VERSION_MISMATCH` environment variable is **not enough** on ansible-core 2.21.)

The `ansible-test` `--requirements` flag installs test dependencies when needed.

### Sanity (`sanity`)

Checks format, syntax, module documentation, and other standard checks of the Ansible ecosystem:

```bash
ansible-test sanity -v --python 3.12 --requirements --exclude tests/output/
```

If the `ansible-doc` test fails with a WARNING *Collection … does not support Ansible version 2.21*, go back to `meta/runtime.yml` (same issue as Galaxy).

### Unit tests (`units`)

Runs the Python tests under `tests/unit/` (`get_servers` module and `module_utils`).

In the **ansible-devspaces** image, system Python may ship **pytest-ansible**, which breaks `ansible-test units` (collection paths with `:`). `ansible-test` **does not forward** `PYTEST_ADDOPTS` to the pytest subprocess.

**Recommended solution:** use **`--venv`**. `ansible-test` creates a virtualenv and installs only the `units` dependencies; **pytest-ansible** from the image does not get in there.

The collection declares in **`tests/unit/requirements.txt`** the **`requests`** dependency: without it, `plugins/module_utils/haiinv.py` loads an empty stub (`class Haiinv: pass`) and the module tests fail.

```bash
ansible-test units --venv --python 3.12 --requirements --coverage
```

**ansible-core 2.21 note:** the `set_module_args` helper in `tests/unit/modules/commun_test.py` is the old-style one. On 2.21.x it often fails with `No serialization profile was specified.` `module_utils` tests may pass while module tests fail. That is the template vs 2.21, not your setup. The lab treats units as OK if you understand that message and integration (next section) exits 0. Updating the helper is optional (new `patch_module_args` / serialization-profile API).

### Integration tests (`integration`)

Runs the `get_server` target under `tests/integration/` (uses `tests/integration/integration_config.yml` and a public sample JSON):

```bash
ansible-test integration --python 3.12 --requirements
```

You can combine integration with coverage:

```bash
ansible-test integration --python 3.12 --requirements --coverage
```

The integration inventory may mention `python3.9`; `ansible-test --python 3.12` sets the interpreter for the run. This target does not need `sudo`.

### Sample playbook

`playbooks/playbook.yml` includes the role but **does not** define `example_*`. Run it with the integration file:

```bash
ansible-playbook playbooks/playbook.yml -e @tests/integration/integration_config.yml
```

Without `-e`, Ansible fails with undefined variables (`example_environment`, and so on).

### Code coverage reports

After `units` or `integration` with `--coverage`:

```bash
ansible-test coverage combine --requirements
ansible-test coverage report --requirements
ansible-test coverage html --requirements
```

Without `--requirements`, `ansible-test` may demand a specific `coverage` module that is not on system Python. Open the HTML in a browser. The repo has a sample XML at `tests/output/reports/coverage.xml` from a **previous** run; do not treat it as proof of your run.

## Summary (checklist)

| Step | Action |
|------|--------|
| 1 | Walk `plugins/`, `roles/`, `playbooks/`, `tests/`, `meta/runtime.yml`, `galaxy.yml`. |
| 2 | Adjust `requires_ansible` if it caps at `<=2.19`. |
| 3 | `ansible-galaxy collection install . -p ~/.ansible/collections --force` |
| 4 | `ansible-test sanity --python 3.12 --requirements --exclude tests/output/` |
| 5 | `ansible-test units --venv --python 3.12 --requirements --coverage` (see 2.21 note). |
| 6 | `ansible-test integration --python 3.12 --requirements` |
| 7 | `ansible-playbook playbooks/playbook.yml -e @tests/integration/integration_config.yml` |
| 8 | (Optional) `ansible-test coverage combine/report/html --requirements` |

## Expected result

- You know where the module, role, playbook, and tests live.
- The collection installs under `~/.ansible/collections` against ansible-core 2.21.
- `sanity` (excluding `tests/output/`) and `integration` exit 0.
- The sample playbook runs with the variables from `integration_config.yml`.

## References

- [Using collections](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html)
- [Developing collections](https://docs.ansible.com/ansible/latest/dev_guide/developing_collections.html)
- [ansible-test](https://docs.ansible.com/ansible/latest/dev_guide/testing_integration.html)
