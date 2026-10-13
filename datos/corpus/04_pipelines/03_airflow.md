# 🗓️ Orquestación con Apache Airflow

> **Objetivo:** que tu pipeline se ejecute solo, en orden, con reintentos y con historial.
> **Tiempo:** 3 h · **Antes de empezar:** lecciones 1 y 2 de esta carpeta

**Cómo usar esta lección:** Airflow se instala en un entorno virtual **aparte** (choca con otras dependencias de este repositorio). Cada paso da el comando o el código, lo que debes ver y un «tu turno». El DAG de ejemplo está en [`dags/hola_banco.py`](dags/hola_banco.py), probado con Airflow 3.

**Calentamiento (sin mirar apuntes):**
1. ¿Qué significa que una carga sea idempotente?
2. ¿Por qué se valida antes de cargar y no después?
3. Hoy, ¿quién ejecuta tu ETL de la lección 2 y cómo te enteras si falla?

---

## Paso 1 — Qué es un orquestador

**Aprenderás:** qué problema resuelve Airflow y cuál no.

**Concepto:** un orquestador decide **cuándo** y **en qué orden** se ejecuta cada tarea, reintenta las que fallan y guarda el historial. **No procesa datos**: lanza tu código.

| Término | Qué es |
|---|---|
| **DAG** | Grafo acíclico dirigido: tareas + dependencias + calendario |
| **Operador** | La plantilla de una tarea (`BashOperator`, `PythonOperator`…) |
| **Tarea** | Un operador con sus parámetros, dentro de un DAG |
| **Ejecución (DAG run)** | Una pasada del DAG para una fecha concreta |

```bash
python -m venv ~/airflow-venv && source ~/airflow-venv/bin/activate
pip install apache-airflow        # la guía oficial recomienda fijar versiones con un archivo de constraints
airflow version
airflow standalone                # base de datos, planificador y web en http://localhost:8080
```

**👉 Tu turno 1:** instálalo, arráncalo y entra a la web con el usuario que imprime `standalone`. En otra terminal: `airflow config get-value core dags_folder`. Esa carpeta es donde viven tus DAG.

**Reflexiona:** «cron ya ejecuta cosas a una hora». Nombra tres cosas que Airflow da y cron no.

## Paso 2 — Tu primer DAG

**Concepto:** un DAG es un archivo de Python. El bloque `with DAG(...)` declara el calendario; dentro se crean las tareas; `>>` declara el orden.

```python
from datetime import datetime, timedelta

from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import DAG


def transformar(ds: str) -> int:
    filas = 4 if ds == "2026-07-01" else 0
    print(f"transformando el día {ds}: {filas} filas")
    return filas


with DAG(
    dag_id="hola_banco",
    start_date=datetime(2026, 7, 1),
    schedule="@daily",                 # o cron: "0 6 * * *"
    catchup=False,
    default_args={"retries": 2, "retry_delay": timedelta(seconds=30)},
):
    extraer = BashOperator(task_id="extraer", bash_command="echo extrayendo el dia {{ ds }}")
    transformar_tarea = PythonOperator(task_id="transformar", python_callable=transformar)
    cargar = BashOperator(
        task_id="cargar",
        bash_command="echo cargando {{ ti.xcom_pull(task_ids='transformar') }} filas",
    )

    extraer >> transformar_tarea >> cargar
```

> En Airflow 2 los imports son `from airflow import DAG` y `from airflow.operators.bash import BashOperator`. Usa los de la versión que instalaste.

```bash
cp 06_ingenieria_de_datos/04_pipelines/dags/hola_banco.py "$(airflow config get-value core dags_folder)/"
airflow dags test hola_banco 2026-07-01
```

**Salida esperada** (entre muchas líneas de log, busca estas tres y el estado final):

```
extrayendo el dia 2026-07-01
transformando el día 2026-07-01: 4 filas
cargando 4 filas
... state=success ...
```

**👉 Tu turno 2:** escribe tu propio DAG `hola_tuyo` con tres `BashOperator` en cadena, **sin copiar** el de arriba. Lánzalo desde la web y abre el log de cada tarea.

**Comprueba:** `airflow dags list` lo muestra y las tres tareas terminan en verde.

## Paso 3 — La fecha lógica

**Concepto:** cada ejecución corresponde a un **día de datos**, no al momento en que corre. Si el día 5 relanzas la ejecución del día 1, debe procesar los datos del día 1. Esa fecha llega como `{{ ds }}` en las plantillas y como parámetro `ds` en las funciones. Por eso tu ETL tiene un parámetro `--fecha`.

En la salida del paso 2, la fecha que imprimen las tareas es `2026-07-01`, aunque lo ejecutaste hoy.

**👉 Tu turno 3:** ejecuta `airflow dags test hola_banco 2026-07-02`. ¿Cuántas filas «carga»? Después pon `catchup=True` en tu DAG, con un `start_date` de hace 5 días, y actívalo en la web.

**Comprueba:** se crean 5 ejecuciones, cada una con una fecha distinta.

**Reflexiona:** ¿por qué un pipeline que usa `datetime.now()` en lugar de la fecha lógica no se puede reprocesar?

## Paso 4 — Pasar información entre tareas

**Concepto:** lo que devuelve un `PythonOperator` se guarda (XCom) y otra tarea puede leerlo: así `cargar` supo que eran 4 filas. Sirve para valores **pequeños**: un número, una ruta, un id. **Nunca un DataFrame.** Entre tareas viajan rutas; los datos viven en disco, en S3 o en la base.

**👉 Tu turno 4:** haz que `extraer` escriba un archivo en `/tmp` y devuelva su ruta, y que `transformar` la reciba y cuente las líneas.

**Reflexiona:** las tareas pueden correr en máquinas distintas. ¿Qué pasa entonces con una ruta de `/tmp`? ¿Dónde debería estar el archivo?

## Paso 5 — Cuando una tarea falla

**Concepto:** una tarea que falla se reintenta según `retries` y `retry_delay`. Si agota los reintentos queda en rojo y las siguientes **no se ejecutan**. Por eso cada tarea debe ser idempotente: Airflow la va a repetir.

**👉 Tu turno 5:** haz que la tarea intermedia falle (`bash_command="exit 1"`), con 2 reintentos y 30 segundos de espera. Míralo en la web. Después arréglala y usa «Clear» sobre la tarea fallida para relanzar solo desde ahí.

**Comprueba:** la tarea se intenta 3 veces y la siguiente queda como `upstream_failed`.

## Paso 6 — Tareas en paralelo

**Concepto:** `a >> [b, c, d] >> e` ejecuta `b`, `c` y `d` a la vez después de `a`, y `e` espera a las tres.

**👉 Tu turno 6:** un DAG con una tarea `inicio`, tres en paralelo (una por fuente: archivo, base y API) y una final `validar`.

**Comprueba:** en la vista de grafo se ve el abanico.

**Reflexiona:** si falla una de las tres fuentes, ¿debe ejecutarse `validar`? ¿Cómo cambiarías ese comportamiento? (Busca `trigger_rule`.)

---

## Reto de la lección (pasos 1 a 6)

Orquesta tu ETL de la lección 2: un DAG diario con las tareas `extraer → transformar → validar → cargar`, que llame a tu código pasándole `{{ ds }}`. Entre tareas viaja la ruta del archivo intermedio, no los datos.

**Comprueba:** `airflow dags test tu_dag 2026-07-01` termina en `success`, y ejecutarlo dos veces deja las mismas filas en PostgreSQL.
