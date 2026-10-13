# 📦 Paquetes, estilo y documentación

> **Objetivo:** convertir funciones sueltas en un paquete que otra persona puede instalar, entender y cambiar.
> **Tiempo:** 2 h · **Antes de empezar:** lecciones 1 y 2 (Git) y `01_core_python/02_organizacion_y_poo/01_modulos_paquetes.py`

**Cómo usar esta lección:** se hace en la terminal, en una carpeta nueva **fuera de este repositorio** y con Git desde el primer minuto. Cada paso da los comandos, lo que debes ver y un «tu turno». Escribe los comandos, no los pegues.

**Calentamiento (sin mirar apuntes):**
1. ¿Qué diferencia hay entre un módulo y un paquete?
2. ¿Qué hace `git add -p`?
3. ¿Qué dice un buen mensaje de commit?

---

## Paso 1 — La estructura mínima

**Aprenderás:** qué archivos convierten una carpeta en algo instalable.

**Concepto:** el código va en `src/<paquete>/`, los tests en `tests/` y la descripción del proyecto en `pyproject.toml`. Separar `src/` evita que Python importe la carpeta por accidente en lugar del paquete instalado.

```bash
mkdir -p ~/limpiador/src/limpiador ~/limpiador/tests && cd ~/limpiador && git init
```

`src/limpiador/reglas.py`:

```python
def quitar_duplicados(filas, clave="id"):
    vistos, resultado = set(), []
    for fila in filas:
        if fila[clave] not in vistos:
            vistos.add(fila[clave])
            resultado.append(fila)
    return resultado
```

`src/limpiador/__init__.py` (decide qué se ve desde fuera):

```python
from .reglas import quitar_duplicados

__all__ = ["quitar_duplicados"]
```

`pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "limpiador"
version = "0.1.0"
requires-python = ">=3.10"
```

**👉 Tu turno 1:** crea los tres archivos y haz el primer commit. Añade un `.gitignore` con `__pycache__/`, `.venv/` y `*.egg-info/`.

**Comprueba:** `git status` no muestra nada pendiente.

## Paso 2 — Instalarlo en modo editable

**Concepto:** `pip install -e .` no copia tu código: deja un enlace a la carpeta. Cualquier cambio se ve al instante, y el paquete se importa desde **cualquier** directorio, como una biblioteca más.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
cd /tmp && python -c "from limpiador import quitar_duplicados; print(quitar_duplicados([{'id': 1}, {'id': 1}, {'id': 2}]))"
```

**Salida esperada:**

```
[{'id': 1}, {'id': 2}]
```

**👉 Tu turno 2:** mueve al paquete tres de tus reglas de `02_limpieza_y_eficiencia` (añade `pandas` a `dependencies` en `pyproject.toml` y vuelve a instalar). Expónlas en `__init__.py`.

**Comprueba:** desde `/tmp`, `python -c "import limpiador; print(limpiador.__file__)"` apunta a tu carpeta `src/`.

**Reflexiona:** ¿qué ventaja tiene esto frente a copiar `reglas.py` al proyecto donde lo necesitas?

## Paso 3 — Estilo automático con ruff

**Concepto:** el estilo no se discute ni se revisa a mano: lo aplica una herramienta. `ruff check` avisa de problemas (imports sin usar, variables sin definir) y `ruff format` deja el formato uniforme. Las convenciones están en `99_notas/convenciones.md`.

Añade esto **al final** de `src/limpiador/reglas.py`, tal cual, con sus defectos:

```python
import os
def total( filas ):
    x=[f["monto"] for f in filas]
    return sum(x)
```

```bash
pip install ruff
ruff check .
```

**Salida esperada** (entre otros avisos, que cambian según tu versión de ruff):

```
F401 [*] `os` imported but unused
```

```bash
ruff check --fix . && ruff format . && git diff
```

**👉 Tu turno 3:** lee el `git diff`: ¿qué cambió `ruff format`? Pasa ruff a tus tres reglas y déjalas sin avisos. Renombra `x` a algo que diga qué contiene (eso ruff no lo hace por ti).

**Reflexiona:** ¿por qué conviene ejecutar el formateador **antes** de cada commit y no al final del proyecto?

## Paso 4 — Documentar para quien no eres tú

**Concepto:** los *type hints* dicen qué entra y qué sale; el *docstring* dice qué hace, qué recibe, qué devuelve y qué puede fallar. Juntos alimentan `help()`, el autocompletado del editor y a quien revise tu código.

```python
def quitar_duplicados(filas: list[dict], clave: str = "id") -> list[dict]:
    """Elimina las filas repetidas según `clave`, conservando la primera.

    Args:
        filas: registros a depurar.
        clave: campo que identifica a cada registro.

    Returns:
        Una lista nueva, en el orden original, sin repetidos.

    Raises:
        KeyError: si alguna fila no tiene el campo `clave`.
    """
```

```bash
python -c "import limpiador; help(limpiador.quitar_duplicados)"
```

**👉 Tu turno 4:** añade type hints y docstring a todas tus funciones públicas.

**Comprueba:** `help()` de cada una se entiende sin abrir el código.

**Reflexiona:** un docstring que dice «quita duplicados» encima de `quitar_duplicados`, ¿aporta algo? ¿Qué información sí aportaría?

## Paso 5 — Configuración en un solo sitio

**Concepto:** rutas, límites y listas de valores válidos repartidos por el código son difíciles de encontrar y de cambiar. Un `dataclass` los agrupa, les pone tipo y, con `frozen=True`, impide modificarlos por accidente.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    monto_maximo: float = 100_000.0
    tipos_validos: tuple[str, ...] = ("compra", "deposito", "retiro", "transferencia")
```

```bash
python -c "
from dataclasses import dataclass
@dataclass(frozen=True)
class Config:
    monto_maximo: float = 100_000.0
c = Config()
c.monto_maximo = 5"
```

**Salida esperada** (última línea):

```
dataclasses.FrozenInstanceError: cannot assign to field 'monto_maximo'
```

**👉 Tu turno 5:** crea `src/limpiador/config.py` y sustituye las constantes sueltas de tus reglas. Las funciones reciben la configuración como parámetro, con un valor por defecto.

**Reflexiona:** ¿por qué `tipos_validos` es una tupla y no una lista?

---

## Reto de la lección (pasos 1 a 5)

Añade un comando de consola: que al instalar el paquete exista `limpiar entrada.csv salida.parquet`. Busca `[project.scripts]` en la documentación de `pyproject.toml`.

**Comprueba:** en un entorno virtual recién creado, tras `pip install -e .`, el comando funciona desde cualquier carpeta.
