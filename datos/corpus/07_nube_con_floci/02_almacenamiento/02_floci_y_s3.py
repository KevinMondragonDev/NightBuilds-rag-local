"""
Tema 12 — Nube con Floci | Lección 2: Floci y S3
==================================================

Floci es un emulador de AWS que corre en tu máquina con Docker: mismos servicios,
misma API y mismo boto3, sin cuenta, sin costo y sin miedo a romper nada.
Sirve para APRENDER y DISEÑAR. No sustituye a AWS para medir rendimiento o costos.

CÓMO USAR ESTA LECCIÓN:
    1) Arranca Floci (una vez por sesión de estudio):
           cd 05_ingenieria_de_datos/07_nube_con_floci
           docker compose up -d
    2) Ejecuta el archivo, compara con la salida esperada y haz cada «TU TURNO»:
           python 02_floci_y_s3.py
       Se puede ejecutar las veces que quieras: limpia lo que crea.
    3) Repite cada paso con la CLI de AWS para ver que es lo mismo:
           export AWS_ENDPOINT_URL=http://localhost:4566 AWS_DEFAULT_REGION=us-east-1
           export AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test
           aws s3 ls

    pip install boto3 pandas

TIEMPO: 2 h · ANTES DE EMPEZAR: lección 1 (conceptos) y Docker instalado

CALENTAMIENTO (sin mirar apuntes, responde en un comentario antes de empezar):
    1. Un ejemplo de IaaS, uno de PaaS y uno de SaaS.
    2. ¿Qué significa «serverless»?
    3. ¿Por qué la zona raw se particiona por fecha de ingesta?
"""

import io
import os
from pathlib import Path

import boto3
import pandas as pd

# ════════════════════════════════════════════════════════════════════
# PASO 1 — Un cliente que apunta a Floci
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: boto3 habla con AWS por HTTP. Lo ÚNICO que cambia entre Floci y AWS
# real es la URL (endpoint_url) y las credenciales. Si esa URL sale de una
# variable de entorno, el mismo código sirve en tu máquina y en producción.

ENDPOINT = os.environ.get("AWS_ENDPOINT_URL", "http://localhost:4566")


def cliente(servicio: str):
    return boto3.client(
        servicio,
        endpoint_url=ENDPOINT,
        region_name="us-east-1",
        aws_access_key_id="test",          # Floci acepta cualquier valor no vacío
        aws_secret_access_key="test",      # en AWS real: NUNCA en el código
    )


s3 = cliente("s3")
BUCKET = "banco-raw"


def vaciar_y_borrar(bucket: str) -> None:
    """Deja el entorno limpio para poder repetir la lección."""
    try:
        for pagina in s3.get_paginator("list_objects_v2").paginate(Bucket=bucket):
            for objeto in pagina.get("Contents", []):
                s3.delete_object(Bucket=bucket, Key=objeto["Key"])
        s3.delete_bucket(Bucket=bucket)
    except s3.exceptions.NoSuchBucket:
        pass


vaciar_y_borrar(BUCKET)

# ════════════════════════════════════════════════════════════════════
# PASO 2 — Buckets y objetos
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: S3 guarda OBJETOS (bytes) dentro de BUCKETS. Cada objeto tiene una
# CLAVE (su nombre completo). No hay carpetas de verdad: «a/b/c.txt» es una clave
# con barras. Un objeto no se edita: se reemplaza entero.

s3.create_bucket(Bucket=BUCKET)
s3.put_object(Bucket=BUCKET, Key="hola.txt", Body="hola nube".encode())
contenido = s3.get_object(Bucket=BUCKET, Key="hola.txt")["Body"].read().decode()
print("[paso 2]", [b["Name"] for b in s3.list_buckets()["Buckets"] if b["Name"] == BUCKET], contenido)
# SALIDA ESPERADA:
#   [paso 2] ['banco-raw'] hola nube

# 👉 TU TURNO 2: sube el mismo objeto otra vez con otro texto y léelo.
#    ¿Hay dos objetos o uno? ¿Qué pasó con el contenido anterior?


# REFLEXIONA: si no se puede editar un objeto, ¿cómo «añades una fila» a un CSV
# de 5 GB que está en S3? ¿Qué te dice eso de cómo conviene partir los archivos?


# ════════════════════════════════════════════════════════════════════
# PASO 3 — Claves con prefijo: el particionado de un data lake
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: la clave ES el diseño. El formato clave=valor en la ruta (estilo Hive)
# lo entienden Spark, Athena y Glue, y permite leer solo lo que hace falta.
#     movimientos/fecha=2026-07-01/parte-0.csv

ruta_csv = Path(__file__).resolve().parents[2] / "datos" / "movimientos.csv"
movimientos = pd.read_csv(ruta_csv, parse_dates=["fecha"])
movimientos["dia"] = movimientos["fecha"].dt.date.astype(str)

for dia, grupo in movimientos[movimientos["dia"] <= "2026-07-03"].groupby("dia"):
    cuerpo = grupo.drop(columns="dia").to_csv(index=False).encode()
    s3.put_object(Bucket=BUCKET, Key=f"movimientos/fecha={dia}/parte-0.csv", Body=cuerpo)

listado = s3.list_objects_v2(Bucket=BUCKET, Prefix="movimientos/fecha=2026-07-0")
print("[paso 3]", [objeto["Key"] for objeto in listado["Contents"]])
# SALIDA ESPERADA:
#   [paso 3] ['movimientos/fecha=2026-07-01/parte-0.csv', 'movimientos/fecha=2026-07-02/parte-0.csv', 'movimientos/fecha=2026-07-03/parte-0.csv']

# 👉 TU TURNO 3: sube TODO julio con el mismo esquema de claves y lista solo la
#    semana del 6 al 12. list_objects_v2 devuelve como máximo 1,000 claves por
#    llamada: usa un paginador (mira vaciar_y_borrar).


# REFLEXIONA: ¿por qué particionar por fecha y no por cuenta_id? ¿Qué pasa con el
# número de archivos si particionas por una columna con un millón de valores?


# ════════════════════════════════════════════════════════════════════
# PASO 4 — Leer de S3 directo a un DataFrame
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: get_object devuelve un flujo de bytes; pandas lee de cualquier flujo.

objeto = s3.get_object(Bucket=BUCKET, Key="movimientos/fecha=2026-07-01/parte-0.csv")
df = pd.read_csv(io.BytesIO(objeto["Body"].read()))
print("[paso 4]", df.shape, round(df["monto"].sum(), 2))
# SALIDA ESPERADA:
#   [paso 4] (4, 7) 3085.6

# 👉 TU TURNO 4: escribe leer_particiones(bucket, prefijo) que lea TODOS los CSV
#    bajo un prefijo y devuelva un único DataFrame con una columna `fecha_particion`
#    sacada de la clave.


# COMPRUEBA: con el prefijo "movimientos/" y tus datos del turno 3, el total de
# filas coincide con las de julio en el CSV original.

# ════════════════════════════════════════════════════════════════════
# PASO 5 — Lo mismo en Parquet
# ════════════════════════════════════════════════════════════════════
# 👉 TU TURNO 5 (sin ejemplo: ya tienes todas las piezas): crea el bucket
#    banco-clean y escribe julio en Parquet, una partición por día
#    (df.to_parquet(buffer) con un io.BytesIO). Compara el tamaño total de los
#    objetos de los dos buckets sumando el campo Size del listado.


# REFLEXIONA: ¿qué línea de este archivo cambiarías para ejecutarlo contra AWS de
# verdad? Si la respuesta es «varias», revisa el paso 1.

# ════════════════════════════════════════════════════════════════════
# RETO DE LA LECCIÓN (pasos 1 a 5)
# ════════════════════════════════════════════════════════════════════
# Vuelve a 07_retos_de_integracion/reto_15_s3_file_processor.py y reto_16_s3_data_validator.py:
# ahora puedes ejecutarlos de verdad. Resuélvelos contra Floci sin escribir
# «localhost» en ninguna parte del código (solo en una variable de entorno).

vaciar_y_borrar(BUCKET)
