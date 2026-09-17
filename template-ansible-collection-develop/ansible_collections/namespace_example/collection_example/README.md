# Ansible Collection - namespace_example.collection_example

Example collection with a module that queries a HAIINV-style JSON endpoint.

## Modules

| Name | Purpose |
| :--- | :------ |
| `namespace_example.collection_example.get_servers` | Get a list of servers with their hostvars |

## Installation

From the collection root (the directory that contains `galaxy.yml`):

```bash
ansible-galaxy collection install . -p ~/.ansible/collections --force
```

Galaxy copies the content into `~/.ansible/collections/ansible_collections/namespace_example/collection_example/`. After install you will see `MANIFEST.json` / `FILES.json` there, not `galaxy.yml`. Check with:

```bash
ansible-galaxy collection list | grep namespace_example
```

Do **not** `pip install -r requirements.txt` into the Dev Spaces system Python. Use `ansible-test ... --requirements` for tests.

## Using the collection

Reference modules with the FQCN:

```yaml
---
- hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: Example get information
      namespace_example.collection_example.get_servers:
        username: "{{ example_username }}"
        password: "{{ example_password }}"
        url: "{{ example_url }}"
        proxy: "{{ example_proxy }}"
        techgroups: "{{ example_techgroups }}"
        environment: "{{ example_environment }}"
```

`techgroups` is a **list**. In YAML you can pass a single item as:

```yaml
example_techgroups:
  - lab_test_rh_1
```

A sample playbook lives in `playbooks/playbook.yml` (needs `-e @tests/integration/integration_config.yml`). The role writes `prueba.txt` next to that playbook (`playbook_dir`).

Further details: [using collections](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html).

## Maintainers

* Alejandro de la Hoz (adelahoz@redhat.com)
