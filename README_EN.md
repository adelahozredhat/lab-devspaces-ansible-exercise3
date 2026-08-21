# lab-devspaces-ansible-exercise3

## What is an Ansible collection?

An **Ansible collection** is a versioned package that groups reusable content under a **namespace** and a **name** (`namespace.collection_name`). Inside it can include, among other things:

- **Python modules, plugins, and utilities** (`plugins/`), including `module_utils` shared by several modules.
- **Roles** (`roles/`) with the usual structure of tasks, handlers, meta, etc.
- **Playbooks**, documentation, Galaxy metadata (`galaxy.yml`), Ansible requirements (`meta/runtime.yml`), and **tests** under `tests/`.

Collections are published on [Ansible Galaxy](https://galaxy.ansible.com/), installed with `ansible-galaxy collection install`, and in playbooks modules are referenced with the **FQCN** (fully qualified collection name), for example `namespace_example.collection_example.get_servers`.

## Goal of this lab

This exercise is designed mainly to **understand the structure** of an Ansible collection and how the role, the module, the tests, and `ansible-test` fit together. **It is not essential to modify the code** to get value from the lab: it is enough to walk the directory tree, locate each piece, and run the quality tools indicated below.

## Contents of `template-ansible-collection-develop`

In the `template-ansible-collection-develop/` directory there is a template-style project. The actual collection lives in:

`template-ansible-collection-develop/ansible_collections/namespace_example/collection_example/`

According to `galaxy.yml`, the collection is identified as **`namespace_example.collection_example`**: namespace `namespace_example`, name `collection_example`.

### Included role: `get_server_example_role`

In `roles/get_server_example_role/` there is a sample role that:

- Invokes the collection module `namespace_example.collection_example.get_servers` with variables (`example_username`, `example_password`, `example_url`, etc.).
- Registers the result, shows a `debug`, and writes the output to a sample file.

It is useful to see **how a role consumes a module from the same collection** using the FQCN.

### Module and supporting code (plugins)

Under `plugins/` you will find:

| Path | Description |
| :--- | :---------- |
| `plugins/modules/get_servers.py` | **`get_servers`** module: obtains server lists (with their *hostvars*) via a HAIINV-style API; options such as `username`, `password`, `url`, `proxy`, `techgroups`, `environment`. |
| `plugins/module_utils/haiinv.py` | Shared utilities to talk to the API. |
| `plugins/module_utils/exceptions.py` | Exceptions used by the module and the utilities. |

In Ansible documentation, this kind of file under `plugins/modules/` is often called a module-type **plugin** generically; here the lab focus is to see **where the Python code lives** and how it relates to the role and the tests.

### Other useful folders for orientation

- `meta/runtime.yml`: supported Ansible version (`requires_ansible`).
- `playbooks/playbook.yml`: usage example.
- `tests/unit/`: unit tests (module and `module_utils`).
- `tests/integration/targets/get_server/`: integration target that exercises the module.
- `tests/output/`: outputs from previous runs (JUnit, coverage reports in `tests/output/reports/`); it is useful to know them when reviewing results in an IDE or CI.

## Environment (OpenShift Dev Spaces)

The `devfile.yaml` file defines a workspace with the **ansible-devspaces** image, suitable for running `ansible` and `ansible-test` without installing tools by hand on your local machine.

## Tests with `ansible-test` and coverage

All of the following commands must be run **from the collection root directory** (where `galaxy.yml` is):

```bash
cd template-ansible-collection-develop/ansible_collections/namespace_example/collection_example
ansible-galaxy collection install . -p ~/.ansible/collections --force
```

Adjust the Python version (`3.11`, etc.) to what is available in the container. The `--requirements` flag installs test dependencies when needed.

### Sanity (`sanity`)

Checks format, syntax, module documentation, and other standard checks of the Ansible ecosystem:

```bash
ansible-test sanity -v --python 3.11 --requirements
```

To ignore artifacts under `tests/output/` if they bother the analyzer:

```bash
ansible-test sanity -v --python 3.11 --requirements --exclude tests/output/
```

### Unit tests (`units`)

Runs the Python tests under `tests/unit/` (`get_servers` module and `module_utils`).

In the **ansible-devspaces** image, the system Python ships **pytest-ansible**, which breaks `ansible-test units` (collection paths with `:`). Also, `ansible-test` **does not forward** `PYTEST_ADDOPTS` to the pytest subprocess, and uninstalling system packages often fails (no pip on `/usr/bin/python3` or no permissions).

**Recommended solution:** use **`--venv`**. `ansible-test` creates a virtualenv and installs only the `units` dependencies (pytest, xdist, mock, etc.); **pytest-ansible** from the image does **not** get in there.

The collection declares in **`tests/unit/requirements.txt`** the **`requests`** dependency: without it, `plugins/module_utils/haiinv.py` loads an empty stub (`class Haiinv: pass`) and the module tests fail.

```bash
ansible-test units --venv --python 3.11 --requirements --coverage
```

### Integration tests (`integration`)

Runs the `get_server` target and the rest of the targets defined under `tests/integration/`:

```bash
ansible-test integration --python 3.11 --requirements
```

In many environments privileges are needed for certain scenarios; if the documentation or the environment requires it, you can put `sudo` in front of the command.

You can combine integration with coverage collection (depending on the `ansible-test` version):

```bash
ansible-test integration --python 3.11 --requirements --coverage
```

### Code coverage reports

After running `units` or `integration` with `--coverage`, Ansible leaves coverage data that you can **combine and dump** into readable reports:

```bash
ansible-test coverage combine
ansible-test coverage report
ansible-test coverage html --requirements
```

The resulting HTML can be opened in a browser to review **which lines of the module and `module_utils` are covered** by the tests. The repository already has a sample XML report in `tests/output/reports/coverage.xml` from a previous run.

## References

- [Using collections](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html)
- [Developing collections](https://docs.ansible.com/ansible/latest/dev_guide/developing_collections.html)
- [ansible-test](https://docs.ansible.com/ansible/latest/dev_guide/testing_integration.html)
