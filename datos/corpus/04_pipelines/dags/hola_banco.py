"""DAG de ejemplo de la lección 3 (04_pipelines/03_airflow.md). Probado con Airflow 3.

Cópialo a la carpeta dags/ de tu instalación de Airflow:
    cp hola_banco.py "$(airflow config get-value core dags_folder)/"
    airflow dags test hola_banco 2026-07-01
"""

from datetime import datetime, timedelta

from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import DAG


def transformar(ds: str) -> int:
    """`ds` es la fecha lógica de la ejecución: Airflow la pasa por el nombre del parámetro."""
    filas = 4 if ds == "2026-07-01" else 0
    print(f"transformando el día {ds}: {filas} filas")
    return filas  # lo que devuelve la función queda disponible para otras tareas (XCom)


with DAG(
    dag_id="hola_banco",
    start_date=datetime(2026, 7, 1),
    schedule="@daily",
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
