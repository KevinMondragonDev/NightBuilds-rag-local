"""
Tema 9 — Pipelines | Lección 1: ETL y ELT
===========================================

TIEMPO: 2 h · ANTES DE EMPEZAR: 01_ingesta_de_datos/02 (PostgreSQL) y 02_retos_practicos/reto_11

CÓMO USAR ESTA LECCIÓN: predice, ejecuta, compara con la salida esperada, tu turno.
    export PGPASSWORD="tu_clave"
    python 06_ingenieria_de_datos/04_pipelines/01_etl_y_elt.py
    Se puede ejecutar las veces que quieras: reemplaza lo que crea.

    pip install pandas sqlalchemy "psycopg[binary]"

CALENTAMIENTO (sin mirar apuntes):
    1. ¿Qué tres modos tiene if_exists en to_sql y qué hace cada uno?
    2. ¿Por qué conviene que la base agrupe en lugar de traer todo a pandas?
    3. En tu reto_11, ¿qué hacía cada uno de los tres módulos?
"""

from pathlib import Path
import os
import sys

import pandas as pd
from sqlalchemy import URL, create_engine, text
from sqlalchemy.exc import OperationalError

engine = create_engine(URL.create(
    "postgresql+psycopg",
    username=os.environ.get("PGUSER", "postgres"), password=os.environ.get("PGPASSWORD"),
    host=os.environ.get("PGHOST", "localhost"), port=int(os.environ.get("PGPORT", "5432")),
    database=os.environ.get("PGDATABASE", "banco_python"),
))
try:
    with engine.begin() as con:
        con.execute(text("CREATE SCHEMA IF NOT EXISTS raw"))
        con.execute(text("CREATE SCHEMA IF NOT EXISTS analitica"))
except OperationalError as error:
    sys.exit(f"No pude conectar a PostgreSQL: {error.orig}\n¿Exportaste PGPASSWORD? Mira 01_ingesta_de_datos/02_bases_de_datos_sql.py")

DATOS = Path(__file__).resolve().parents[1] / "datos"

# ════════════════════════════════════════════════════════════════════
# PASO 1 — Tres funciones con una sola tarea cada una
# ════════════════════════════════════════════════════════════════════
# APRENDERÁS: la forma de cualquier pipeline.
# CONCEPTO: un pipeline mueve datos de un origen a un destino de forma REPETIBLE.
#   extraer      lee el origen y devuelve los datos sin tocarlos
#   transformar  recibe datos y devuelve datos; no lee ni escribe nada
#   cargar       escribe en el destino y dice cuántas filas escribió
# Como transformar no toca ni archivos ni bases, se puede probar con un assert.


def extraer(ruta: Path) -> pd.DataFrame:
    return pd.read_csv(ruta)


def transformar(df: pd.DataFrame) -> pd.DataFrame:
    compras = df[df["tipo"] == "compra"].copy()
    compras["fecha"] = pd.to_datetime(compras["fecha"])
    compras["mes"] = compras["fecha"].dt.month
    return compras[["id", "cuenta_id", "fecha", "mes", "categoria", "monto"]]


def cargar(df: pd.DataFrame, tabla: str, esquema: str) -> int:
    df.to_sql(tabla, engine, schema=esquema, if_exists="replace", index=False)
    return len(df)


prueba = transformar(pd.DataFrame({"id": [1, 2], "cuenta_id": [7, 7], "fecha": ["2026-07-01 10:00"] * 2,
                                   "tipo": ["compra", "deposito"], "monto": [10.0, 99.0],
                                   "comercio": ["Toks", None], "categoria": ["restaurantes", None]}))
print("[paso 1]", len(prueba), prueba["mes"].tolist(), list(prueba.columns))
# SALIDA ESPERADA:
#   [paso 1] 1 [7] ['id', 'cuenta_id', 'fecha', 'mes', 'categoria', 'monto']

# 👉 TU TURNO 1: añade a transformar() la columna dia_semana (0 = lunes) y
#    comprueba con un assert, sobre un DataFrame de 3 filas inventado, que un
#    movimiento del 2026-07-01 da 2 (miércoles).


# REFLEXIONA: ¿por qué pudiste probar transformar() sin tener PostgreSQL encendido?

# ════════════════════════════════════════════════════════════════════
# PASO 2 — ETL: transformar FUERA del destino
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: Extract -> Transform -> Load. Python hace el trabajo y al destino
# solo llega el dato ya limpio. Se usa cuando el destino es caro o limitado, o
# cuando hay datos sensibles que no deben llegar crudos.

cargadas = cargar(transformar(extraer(DATOS / "movimientos.csv")), "compras_etl", "analitica")
with engine.connect() as con:
    en_destino = con.execute(text("SELECT count(*), round(sum(monto)::numeric, 2) FROM analitica.compras_etl")).one()
print("[paso 2] cargadas:", cargadas, "| en PostgreSQL:", en_destino[0], float(en_destino[1]))
# SALIDA ESPERADA:
#   [paso 2] cargadas: 247 | en PostgreSQL: 247 141104.85

# 👉 TU TURNO 2: compruébalo tú con psql:
#        psql -U postgres -d banco_python -c "SELECT mes, count(*) FROM analitica.compras_etl GROUP BY mes ORDER BY mes;"


# ════════════════════════════════════════════════════════════════════
# PASO 3 — ELT: cargar crudo y transformar DENTRO con SQL
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: Extract -> Load -> Transform. Primero llega todo tal cual a una capa
# «raw»; después el propio motor transforma con SQL. Es lo habitual en los data
# warehouses (Snowflake, BigQuery, Redshift) y lo que automatiza dbt.
# engine.begin() abre una transacción: si el SQL falla, no queda nada a medias.

cargar(extraer(DATOS / "movimientos.csv"), "movimientos", "raw")
with engine.begin() as con:
    con.execute(text("DROP TABLE IF EXISTS analitica.compras_elt"))
    con.execute(text("""
        CREATE TABLE analitica.compras_elt AS
        SELECT id, cuenta_id, fecha::timestamp AS fecha,
               extract(month FROM fecha::timestamp)::int AS mes, categoria, monto
        FROM raw.movimientos
        WHERE tipo = 'compra'
    """))
    iguales = con.execute(text("""
        SELECT (SELECT count(*) FROM analitica.compras_etl) = (SELECT count(*) FROM analitica.compras_elt)
           AND (SELECT round(sum(monto)::numeric, 2) FROM analitica.compras_etl)
             = (SELECT round(sum(monto)::numeric, 2) FROM analitica.compras_elt)
    """)).scalar()
print("[paso 3] ETL y ELT dan lo mismo:", iguales)
# SALIDA ESPERADA:
#   [paso 3] ETL y ELT dan lo mismo: True

# 👉 TU TURNO 3: calcula el gasto por mes y categoría en los dos estilos (pandas
#    sobre el resultado del ETL, SQL sobre raw.movimientos) y compáralos con un merge.


# COMPRUEBA: 18 filas (3 meses × 6 categorías) y ninguna diferencia.

# ════════════════════════════════════════════════════════════════════
# PASO 4 — ¿Cuál elegir?
# ════════════════════════════════════════════════════════════════════
# CONCEPTO (sin código):
#                    ETL                          ELT
#   transforma       Python / Spark               SQL en el destino
#   llega al destino solo lo limpio               todo, crudo
#   reprocesar       hay que volver al origen     se rehace desde raw
#   brilla cuando    datos sensibles, destino     data warehouse potente,
#                    limitado                     muchas transformaciones
#
# 👉 TU TURNO 4: mide con time.perf_counter cuánto tarda cada etapa (E, T y L) en
#    cada estilo. ¿Dónde se va el tiempo?


# REFLEXIONA: con 400 filas da igual. Con 400 millones y un data warehouse, ¿cuál
# elegirías? ¿Y si los datos traen números de tarjeta que no pueden guardarse sin
# enmascarar?

# ════════════════════════════════════════════════════════════════════
# RETO DE LA LECCIÓN (pasos 1 a 4)
# ════════════════════════════════════════════════════════════════════
# Añade al ETL un parámetro `fecha` para procesar solo los movimientos de un día
# y cámbialo a if_exists="append" para ir acumulando días. Ejecútalo para tres
# días distintos, y DOS veces para uno de ellos.
# COMPRUEBA: cuenta las filas. ¿Se duplicó algo? No lo arregles todavía: es el
# problema que resuelve la lección 2.
