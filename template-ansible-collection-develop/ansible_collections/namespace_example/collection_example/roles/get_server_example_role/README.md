Role: get_server_example_role
=============================

Sample role shipped with `namespace_example.collection_example`. It calls the
collection module `get_servers` by FQCN, debugs the result, and writes it to
`{{ playbook_dir }}/prueba.txt`.

This role has no `defaults/`. Pass the `example_*` variables (see
`tests/integration/integration_config.yml`) via extra-vars or the play.

Example
-------

```yaml
- hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: Add Execution Role
      ansible.builtin.include_role:
        name: namespace_example.collection_example.get_server_example_role
```

The file `tests/test.yml` under this role is leftover Galaxy scaffolding (it
expects `prueba-result.txt`). It is **not** part of the lab; do not run it.

License
-------

GPL-2.0-or-later

Author Information
------------------

Alejandro de la Hoz (adelahoz@redhat.com)
