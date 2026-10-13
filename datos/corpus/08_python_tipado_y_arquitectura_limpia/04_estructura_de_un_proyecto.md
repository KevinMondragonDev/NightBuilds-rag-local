# 🧱 De un archivo a un proyecto: carpetas, tipos estrictos y reglas que se cumplen solas

> **Objetivo:** llevar la arquitectura de la lección 3 a un proyecto real, donde la regla de dependencia no dependa de la buena voluntad de nadie.
> **Tiempo:** 2 h · **Antes de empezar:** lección 3 y `03_ingenieria_de_software/03_paquetes_y_estilo.md`

**Cómo usar esta lección:** se hace en la terminal, en un proyecto nuevo. Cada paso da lo que debes escribir, lo que debes ver y un «tu turno».

**Calentamiento (sin mirar apuntes):**
1. Las tres capas y hacia dónde apuntan las flechas de `import`.
2. ¿Qué es un puerto y quién lo define: quien lo necesita o quien lo implementa?
3. ¿Qué es la raíz de composición?

---

## Paso 1 — Una carpeta por capa

**Aprenderás:** dónde va cada archivo y por qué.

**Concepto:** la estructura de carpetas debe contar la arquitectura. Quien abre el proyecto ve primero **qué hace** el sistema (casos de uso), no qué framework usa.

```
banco/
├── pyproject.toml
├── src/banco/
│   ├── dominio/              entidades, reglas y excepciones. Solo Python
│   │   ├── cuenta.py
│   │   └── errores.py
│   ├── casos_de_uso/         una acción por archivo + los puertos que necesita
│   │   ├── puertos.py
│   │   └── retirar_dinero.py
│   ├── adaptadores/          la tecnología concreta
│   │   ├── api/              entrada: FastAPI
│   │   ├── postgres/         salida: repositorios con psycopg
│   │   └── memoria/          salida: los dobles para tests
│   └── arranque.py           raíz de composición: el único que importa de todo
└── tests/
    ├── dominio/              sin dobles, sin red, en milisegundos
    ├── casos_de_uso/         con adaptadores de memoria
    └── adaptadores/          los únicos que necesitan PostgreSQL
```

| Si el archivo… | Va en |
|---|---|
| Solo tiene reglas y no importa ninguna biblioteca externa | `dominio/` |
| Coordina entidades y puertos para cumplir una petición | `casos_de_uso/` |
| Importa `fastapi`, `psycopg`, `boto3`, `requests` o `pandas` | `adaptadores/` |
| Decide qué adaptador se usa | `arranque.py` |

**👉 Tu turno 1:** crea el proyecto y reparte el código de la lección 3 en estas carpetas. Instálalo con `pip install -e .`.

**Comprueba:** `python -c "from banco.casos_de_uso.retirar_dinero import RetirarDinero"` funciona.

**Reflexiona:** `pandas` va en adaptadores. ¿Qué pasa con una regla de negocio que hoy está escrita como una operación de pandas?

## Paso 2 — Tipos estrictos desde el primer día

**Concepto:** en un proyecto nuevo, `mypy --strict` es gratis; activarlo al cabo de un año cuesta semanas. Con las capas, además, los tipos de los puertos son el contrato entre equipos.

Añade a `pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.10"
strict = true
warn_unreachable = true
files = ["src"]
```

```bash
pip install mypy && mypy
```

**Salida esperada:**

```
Success: no issues found in 8 source files
```

(El número de archivos depende de cuántos hayas creado.)

**👉 Tu turno 2:** quita una anotación de retorno en un caso de uso y vuelve a pasar `mypy`. Después quita el `if cuenta is None` del caso de uso. Lee los dos errores.

## Paso 3 — Que la regla de dependencia la vigile una herramienta

**Concepto:** «el dominio no importa de adaptadores» es una regla que alguien romperá un viernes por la tarde. `import-linter` la comprueba: lee los `import` del proyecto y falla si una capa interna depende de una externa.

Añade a `pyproject.toml`:

```toml
[tool.importlinter]
root_package = "banco"

[[tool.importlinter.contracts]]
name = "Las capas solo dependen hacia dentro"
type = "layers"
layers = [
    "banco.arranque",
    "banco.adaptadores",
    "banco.casos_de_uso",
    "banco.dominio",
]
```

```bash
pip install import-linter && lint-imports
```

**Salida esperada** (última parte):

```
Las capas solo dependen hacia dentro KEPT

Contracts: 1 kept, 0 broken.
```

**👉 Tu turno 3:** rompe la regla a propósito: en `dominio/cuenta.py` escribe `from banco.adaptadores.memoria import repositorio`. Ejecuta `lint-imports`.

**Comprueba:** ahora dice `BROKEN` y señala el archivo y la línea.

**Reflexiona:** ¿por qué esta comprobación es más fiable que una revisión de código?

## Paso 4 — Tests por capa

**Concepto:** cada capa se prueba de una forma distinta, y la mayoría de los tests deben estar donde son rápidos.

| Capa | Qué prueba | Necesita | Cuántos |
|---|---|---|---|
| Dominio | Las reglas | Nada | Muchos |
| Casos de uso | La coordinación | Adaptadores de memoria | Bastantes |
| Adaptadores | Que el SQL y el HTTP funcionan | PostgreSQL, cliente de pruebas | Pocos |

**👉 Tu turno 4:** escribe dos tests por capa. Ejecuta solo los rápidos: `pytest tests/dominio tests/casos_de_uso`.

**Comprueba:** esos pasan con PostgreSQL apagado y en menos de un segundo.

## Paso 5 — Todo junto en la integración continua

**Concepto:** estilo, tipos, arquitectura y tests se comprueban en cada cambio, en este orden (de lo más rápido a lo más lento):

```bash
ruff check . && mypy && lint-imports && pytest
```

**👉 Tu turno 5:** crea un flujo de GitHub Actions que ejecute esa línea en cada pull request. Abre un PR que rompa la arquitectura y comprueba que queda en rojo.

---

## Errores típicos

- **El dominio «anémico»:** entidades que solo tienen datos y toda la lógica en los casos de uso. Las reglas van en la entidad.
- **El caso de uso que sabe de HTTP:** devuelve un código de estado o un diccionario pensado para la API.
- **El adaptador con reglas:** una consulta SQL que decide cuándo un retiro es válido.
- **Puertos por si acaso:** un contrato para algo que solo tendrá una implementación y nunca se probará aparte.

## Reto de la lección (pasos 1 a 5)

Añade una segunda entrada al mismo sistema: una línea de comandos (`banco retirar --cuenta 1 --monto 100`) que use **el mismo** caso de uso que la API.

**Comprueba:** no modificaste ningún archivo de `dominio/` ni de `casos_de_uso/`, y `lint-imports` sigue en verde.
