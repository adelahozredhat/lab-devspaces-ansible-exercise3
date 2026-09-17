# lab-devspaces-ansible-exercise3

**Este ejercicio está pensado para realizarse dentro de OpenShift Dev Spaces.**

Versiones de la imagen del laboratorio (compruébalas con `python3 --version`, `ansible --version`, `ansible-test --version`):

| Herramienta | Versión en Dev Spaces |
| ----------- | --------------------- |
| Python | **3.12** (`python3.12`) |
| ansible-core | **2.21.x** |
| ansible-test | **2.21.x** |

Los comandos de esta guía usan `--python 3.12`. Si `python3 --version` muestra otra, sustituye el número.

## ¿Qué es una colección de Ansible?

Una **colección de Ansible** es un paquete versionado que agrupa contenido reutilizable bajo un **espacio de nombres** y un **nombre** (`namespace.nombre_coleccion`). Dentro puede convivir, entre otras cosas:

- **Módulos, plugins y utilidades Python** (`plugins/`), incluidos los `module_utils` compartidos por varios módulos.
- **Roles** (`roles/`) con la estructura habitual de tareas, handlers, meta, etc.
- **Playbooks**, documentación, metadatos de Galaxy (`galaxy.yml`), requisitos de Ansible (`meta/runtime.yml`) y **pruebas** bajo `tests/`.

Las colecciones se publican en [Ansible Galaxy](https://galaxy.ansible.com/), se instalan con `ansible-galaxy collection install` y en los playbooks se referencian los módulos con el **FQCN** (nombre completamente calificado), por ejemplo `namespace_example.collection_example.get_servers`.

## Objetivo de este laboratorio

Entender la **estructura** de una colección y cómo encajan el rol, el módulo, los tests y `ansible-test`. Recorre el árbol, localiza cada pieza y **ejecuta** las herramientas de más abajo.

**Criterio de hecho:** instalación de la colección, `sanity` (con `--exclude tests/output/`), `units` (`--venv`) e `integration` en código 0. El playbook de ejemplo debe poder lanzarse con las variables de integración.

## Contenido de `template-ansible-collection-develop`

En el directorio `template-ansible-collection-develop/` hay un proyecto tipo plantilla. La colección concreta vive en:

`template-ansible-collection-develop/ansible_collections/namespace_example/collection_example/`

Según `galaxy.yml`, la colección se identifica como **`namespace_example.collection_example`**: espacio de nombres `namespace_example`, nombre `collection_example`.

Al recorrer el árbol, usa **esta guía** y el `README.md` de la colección. El README del rol es un resumen del ejemplo; `roles/get_server_example_role/tests/test.yml` es andamiaje de Galaxy (espera un `prueba-result.txt` que no se entrega) y **no** forma parte del laboratorio: no lo ejecutes.

### Rol incluido: `get_server_example_role`

En `roles/get_server_example_role/` hay un rol de ejemplo que:

- Invoca el módulo de la colección `namespace_example.collection_example.get_servers` con variables (`example_username`, `example_password`, `example_url`, `example_techgroups`, etc.).
- `example_techgroups` es una **lista** YAML (el módulo declara `type: list`).
- Registra el resultado, muestra un `debug` y escribe la salida en `{{ playbook_dir }}/prueba.txt`.

Sirve para ver **cómo un rol consume un módulo propio de la misma colección** usando el FQCN. El rol **no** define `defaults/`: esas variables salen de `tests/integration/integration_config.yml` (o de `-e` al lanzar el playbook).

### Módulo y código de soporte (plugins)

En `plugins/` se incluye:

| Ruta | Descripción |
| :--- | :---------- |
| `plugins/modules/get_servers.py` | Módulo **`get_servers`**: obtiene listas de servidores (con sus *hostvars*) vía API tipo HAIINV; opciones como `username`, `password`, `url`, `proxy`, `techgroups`, `environment`. |
| `plugins/module_utils/haiinv.py` | Utilidades compartidas para hablar con la API. |
| `plugins/module_utils/exceptions.py` | Excepciones usadas por el módulo y las utilidades. |

En la documentación de Ansible, este tipo de ficheros en `plugins/modules/` suele llamarse genéricamente **plugin** de tipo módulo; aquí el foco del laboratorio es ver **dónde vive el código Python** y cómo se relaciona con el rol y los tests.

La utilidad concatena `url + techgroup + environment` al llamar a la API. Contra el JSON público de ejemplo la respuesta anida los hosts (`hosts.hosts` en el `debug`). Es el comportamiento del módulo de ejemplo, no un fallo de tu corrida.

### Otras carpetas útiles para orientarse

- `meta/runtime.yml`: versión de Ansible soportada (`requires_ansible`). Esta plantilla ya trae `">=2.10"` (sin techo `2.19`) para ansible-core **2.21** de Dev Spaces.
- `playbooks/playbook.yml`: ejemplo de uso (necesita las variables `example_*`; véase más abajo).
- `tests/unit/`: pruebas unitarias (módulo y `module_utils`). El helper se llama `commun_test.py` (typo histórico de *common*).
- `tests/integration/targets/get_server/`: target de integración que ejercita el módulo.
- `tests/output/`: lo crea `ansible-test` en tus corridas (JUnit, cobertura). No lo uses como prueba de una ejecución anterior. Al pasar sanity, excluye este directorio. Está en `.gitignore`.
- `requirements.txt` de la colección: solo declara `requests`. **No** hagas `pip install -r requirements.txt` sobre el Python del sistema de Dev Spaces; `ansible-test --requirements` instala dependencias en sus venvs.

## Entorno (OpenShift Dev Spaces)

El fichero `devfile.yaml` define un workspace con la imagen **ansible-devspaces**. No hace falta instalar Ansible a mano.

## Pruebas con `ansible-test` y cobertura

Todos los comandos siguientes deben ejecutarse **desde el directorio raíz de la colección** (donde está `galaxy.yml`):

```bash
cd template-ansible-collection-develop/ansible_collections/namespace_example/collection_example
```

### Instalar la colección

Comprueba `meta/runtime.yml`. Debe ser `requires_ansible: ">=2.10"`. Si una copia antigua termina en `<=2.19`, cámbialo y guarda: ansible-core **2.21.2** de Dev Spaces no cumple ese techo y `ansible-galaxy collection install` aborta.

```bash
ansible-galaxy collection install . -p ~/.ansible/collections --force
```

**No sigas el Hint de Galaxy** que sugiere `COLLECTIONS_ON_ANSIBLE_VERSION_MISMATCH=ignore` como variable de entorno: en ansible-core 2.21 **no basta** y el install sigue fallando.

Si no puedes editar `runtime.yml`, crea un `ansible.cfg` en ese directorio:

```ini
[defaults]
collections_on_ansible_version_mismatch = ignore
```

Galaxy **no** copia `galaxy.yml` al destino: deja `MANIFEST.json` y `FILES.json`. Comprueba la instalación así:

```bash
ansible-galaxy collection list | grep namespace_example
ls ~/.ansible/collections/ansible_collections/namespace_example/collection_example/MANIFEST.json
```

El flag `--requirements` de `ansible-test` instala dependencias de test cuando haga falta.

### Sanidad (`sanity`)

Comprueba formato, sintaxis, documentación del módulo y otras comprobaciones estándar del ecosistema Ansible:

```bash
ansible-test sanity -v --python 3.12 --requirements --exclude tests/output/
```

`--exclude tests/output/` es obligatorio si ya corriste `units`/`integration` (o si quedó basura de otra corrida): si no, sanity recorre miles de XML de JUnit.

Si falla el test `ansible-doc` con un WARNING *Collection … does not support Ansible version 2.21*, vuelve a `meta/runtime.yml` (mismo problema que Galaxy).

### Pruebas unitarias (`units`)

Ejecuta los tests Python bajo `tests/unit/` (módulo `get_servers` y `module_utils`).

En la imagen **ansible-devspaces**, el Python del sistema puede traer **pytest-ansible**, que rompe `ansible-test units` (rutas de colección con `:`). `ansible-test` **no reenvía** `PYTEST_ADDOPTS` al subproceso de pytest.

**Solución:** usar **`--venv`**. `ansible-test` crea un virtualenv e instala solo las dependencias de `units`; ahí no entra pytest-ansible de la imagen.

La colección declara en **`tests/unit/requirements.txt`** la dependencia **`requests`**: sin ella, `plugins/module_utils/haiinv.py` carga un stub vacío (`class Haiinv: pass`) y los tests del módulo fallan.

```bash
ansible-test units --venv --python 3.12 --requirements --coverage
```

Debe terminar en código 0. El helper `set_module_args` de `tests/unit/modules/commun_test.py` fija el perfil de serialización (`_ANSIBLE_PROFILE = 'legacy'`) que ansible-core 2.19+ exige. Si vieras `No serialization profile was specified.`, el helper no se está aplicando.

`tests/unit/modules/test_integration_get_servers.py` **no** es el target de integración: son unitarios que llaman al JSON público. La integración real es el paso siguiente.

### Pruebas de integración (`integration`)

Ejecuta el target `get_server` bajo `tests/integration/` (usa `tests/integration/integration_config.yml` y un JSON de ejemplo público):

```bash
ansible-test integration --python 3.12 --requirements
```

Es **esperado** este aviso; el target corre en el propio workspace y el código de salida debe ser 0:

```text
WARNING: Unable to determine context for the following test targets, they will be run on the target host: get_server
```

Puedes combinar integración con cobertura:

```bash
ansible-test integration --python 3.12 --requirements --coverage
```

El inventario de integración usa `python3.12`. `ansible-test --python 3.12` impone el intérprete de la corrida. No hace falta `sudo` en este target.

### Playbook de ejemplo

`playbooks/playbook.yml` incluye el rol pero **no** define `example_*`. Lánzalo con el fichero de integración:

```bash
ansible-playbook playbooks/playbook.yml -e @tests/integration/integration_config.yml
```

Sin `-e`, Ansible falla con variables indefinidas (`example_environment`, etc.).

El rol escribe el resultado en **`playbooks/prueba.txt`** (`playbook_dir` del playbook), no en la raíz de la colección. El `debug` puede mostrar los hosts anidados (`hosts.hosts`); es la forma que devuelve el módulo de ejemplo contra ese JSON.

### Informes de cobertura de código

Tras `units` o `integration` con `--coverage`:

```bash
ansible-test coverage combine --requirements
ansible-test coverage report --requirements
ansible-test coverage html --requirements
```

Sin `--requirements`, `ansible-test` puede pedir un módulo `coverage` concreto que no está en el Python del sistema.

En Dev Spaces el `pip` de `--requirements` instala en `~/.local` (`Defaulting to user installation because normal site-packages is not writeable`). El **primer** `coverage combine` a veces termina con `FATAL: Version 7.10.7 of the Python "coverage" module must be installed` aunque pip acabe de instalarlo. **Vuelve a lanzar el mismo comando**; a la segunda suele ir.

El HTML queda en `tests/output/reports/coverage/index.html`. Ábrelo desde el IDE (Simple Browser / preview), no esperes un navegador de escritorio.

## Resumen (checklist)

| Paso | Acción |
|------|--------|
| 1 | Recorrer `plugins/`, `roles/`, `playbooks/`, `tests/`, `meta/runtime.yml`, `galaxy.yml`. |
| 2 | Comprobar `requires_ansible: ">=2.10"` (sin `<=2.19`). |
| 3 | `ansible-galaxy collection install . -p ~/.ansible/collections --force` y verificar con `collection list` / `MANIFEST.json`. |
| 4 | `ansible-test sanity --python 3.12 --requirements --exclude tests/output/` |
| 5 | `ansible-test units --venv --python 3.12 --requirements --coverage` |
| 6 | `ansible-test integration --python 3.12 --requirements` (el WARNING de contexto es normal). |
| 7 | `ansible-playbook playbooks/playbook.yml -e @tests/integration/integration_config.yml` (mira `playbooks/prueba.txt`). |
| 8 | (Opcional) `ansible-test coverage combine/report/html --requirements` (si `combine` pide `coverage` 7.10.7, repite el comando). |

## Resultado esperado

- Sabes dónde viven el módulo, el rol, el playbook y los tests.
- La colección se instala en `~/.ansible/collections` contra ansible-core 2.21 (`MANIFEST.json` presente).
- `sanity` (excluyendo `tests/output/`), `units --venv` e `integration` terminan en código 0.
- El playbook de ejemplo corre con las variables de `integration_config.yml` y deja `playbooks/prueba.txt`.

## Referencias

- [Uso de colecciones](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html)
- [Desarrollo de colecciones](https://docs.ansible.com/ansible/latest/dev_guide/developing_collections.html)
- [ansible-test](https://docs.ansible.com/ansible/latest/dev_guide/testing_integration.html)
