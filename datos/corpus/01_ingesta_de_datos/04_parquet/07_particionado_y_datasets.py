"""
Tema 6 — Ingesta de datos | Lección 7: Particionado y conjuntos de archivos
=============================================================================

TIEMPO: 2 h · ANTES DE EMPEZAR: lección 6

CÓMO USAR ESTA LECCIÓN: predice, ejecuta, compara con la salida esperada, tu turno.
    python 05_ingenieria_de_datos/01_ingesta_de_datos/04_parquet/07_particionado_y_datasets.py

    pip install pandas pyarrow polars

CALENTAMIENTO (sin mirar apuntes):
    1. ¿Qué es un grupo de filas y qué guarda el pie del archivo?
    2. ¿Qué es el «predicate pushdown»?
    3. ¿Por qué importa el orden en el que se escriben las filas?
"""

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl
import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.parquet as pq

TMP = Path(tempfile.mkdtemp())
rng = np.random.default_rng(7)
N = 120_000
movimientos = pd.DataFrame({
    "id": np.arange(N),
    "cuenta_id": rng.integers(1, 5_000, N),
    "fecha": pd.Timestamp("2026-07-01") + pd.to_timedelta(rng.integers(0, 6 * 24 * 3600, N), unit="s"),
    "tipo": rng.choice(["compra", "deposito", "retiro", "transferencia"], N, p=[0.6, 0.2, 0.1, 0.1]),
    "monto": rng.lognormal(6, 0.9, N).round(2),
})
movimientos["dia"] = movimientos["fecha"].dt.strftime("%Y-%m-%d")

# ════════════════════════════════════════════════════════════════════
# PASO 1 — Un conjunto de datos es una carpeta, no un archivo
# ════════════════════════════════════════════════════════════════════
# APRENDERÁS: cómo se organizan los datos grandes en disco o en S3.
# CONCEPTO: en big data una «tabla» son muchos archivos Parquet dentro de una
# carpeta. Si la carpeta se organiza por el valor de una columna (dia=2026-07-01/),
# esa columna es la PARTICIÓN: su valor está en la ruta, no dentro del archivo.

RAIZ = TMP / "movimientos"
movimientos.to_parquet(RAIZ, partition_cols=["dia"], index=False)
print("[paso 1]", sorted(p.name for p in RAIZ.iterdir()))
# SALIDA ESPERADA:
#   [paso 1] ['dia=2026-07-01', 'dia=2026-07-02', 'dia=2026-07-03', 'dia=2026-07-04', 'dia=2026-07-05', 'dia=2026-07-06']

# 👉 TU TURNO 1: abre UNO de los archivos de dentro con pq.ParquetFile e imprime
#    sus columnas. ¿Está «dia»? ¿De dónde la saca entonces el lector?


# ════════════════════════════════════════════════════════════════════
# PASO 2 — Leer una partición es abrir una carpeta
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: filtrar por la columna de partición no lee estadísticas ni grupos:
# directamente NO ABRE las demás carpetas. Es el filtro más barato que existe, y
# por eso casi todo se particiona por fecha.

conjunto = ds.dataset(RAIZ, format="parquet", partitioning="hive")
un_dia = conjunto.to_table(filter=ds.field("dia") == "2026-07-03")
archivos_dia = [f for f in conjunto.get_fragments(filter=ds.field("dia") == "2026-07-03")]
print("[paso 2] archivos del conjunto:", len(conjunto.files), "| abiertos para un día:", len(archivos_dia),
      "| filas:", un_dia.num_rows == int((movimientos["dia"] == "2026-07-03").sum()))
# SALIDA ESPERADA:
#   [paso 2] archivos del conjunto: 6 | abiertos para un día: 1 | filas: True

# 👉 TU TURNO 2: lee con pandas solo dos días usando
#        pd.read_parquet(RAIZ, filters=[("dia", "in", ["2026-07-01", "2026-07-02"])])
#    y comprueba el número de filas contra el DataFrame original.


# REFLEXIONA: cada noche llega un día nuevo. Con esta estructura, ¿qué hay que
# reescribir? ¿Y si la tabla fuera un único archivo?

# ════════════════════════════════════════════════════════════════════
# PASO 3 — Particionar de más: el problema de los archivos pequeños
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: cada valor distinto de la partición es una carpeta con, al menos, un
# archivo. Particionar por una columna con miles de valores crea miles de archivos
# diminutos: abrir cada uno cuesta más que leerlo. Regla práctica: particiones de
# decenas o cientos de MB, y por columnas con POCOS valores distintos.

muestra = movimientos.head(20_000)
# pyarrow se niega por defecto a crear más de 1,024 particiones: es un aviso. Aquí lo forzamos para verlo.
muestra.to_parquet(TMP / "por_cuenta", partition_cols=["cuenta_id"], index=False, max_partitions=10_000)
por_cuenta = list((TMP / "por_cuenta").rglob("*.parquet"))
por_dia = list(RAIZ.rglob("*.parquet"))
print("[paso 3] archivos particionando por día:", len(por_dia), "| por cuenta, más de 4000:", len(por_cuenta) > 4000)
# SALIDA ESPERADA:
#   [paso 3] archivos particionando por día: 6 | por cuenta, más de 4000: True

# 👉 TU TURNO 3: imprime el tamaño medio de un archivo en cada caso. Mide cuánto
#    tarda leer TODO el conjunto por_cuenta frente al particionado por día.


# REFLEXIONA: quieres filtrar rápido por cuenta_id, pero no puedes particionar
# por ella. ¿Qué viste en la lección 6 que sí sirve?

# ════════════════════════════════════════════════════════════════════
# PASO 4 — Añadir, reemplazar y relanzar
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: un archivo Parquet no se edita. «Actualizar» un día es reemplazar su
# carpeta entera. Con existing_data_behavior="delete_matching" se borra lo que
# había en las particiones que se escriben: cargar dos veces el mismo día no duplica.

dia_7 = movimientos.head(1_000).assign(dia="2026-07-07")
for _ in range(2):  # el job se relanza
    pq.write_to_dataset(pa.Table.from_pandas(dia_7, preserve_index=False), RAIZ, partition_cols=["dia"],
                        existing_data_behavior="delete_matching")
filas_dia_7 = ds.dataset(RAIZ, format="parquet", partitioning="hive").to_table(filter=ds.field("dia") == "2026-07-07").num_rows
print("[paso 4] filas del día 7 tras cargarlo dos veces:", filas_dia_7)
# SALIDA ESPERADA:
#   [paso 4] filas del día 7 tras cargarlo dos veces: 1000

# 👉 TU TURNO 4: repite el bucle SIN existing_data_behavior (usa una carpeta nueva
#    para no estropear esta). ¿Cuántas filas quedan? ¿Qué patrón de
#    05_patrones_de_diseno acabas de ver, con archivos en lugar de con SQL?


# ════════════════════════════════════════════════════════════════════
# PASO 5 — El esquema cambia con el tiempo
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: un día el origen añade una columna. Los archivos viejos no la tienen
# y no se reescriben. Al leer el conjunto se indica el esquema completo y los
# archivos antiguos devuelven nulos en la columna nueva.

dia_8 = movimientos.head(500).assign(dia="2026-07-08", canal="app")
pq.write_to_dataset(pa.Table.from_pandas(dia_8, preserve_index=False), RAIZ, partition_cols=["dia"])
esquema = pa.unify_schemas([f.physical_schema for f in ds.dataset(RAIZ, format="parquet", partitioning="hive").get_fragments()])
completo = ds.dataset(RAIZ, format="parquet", partitioning="hive", schema=esquema.append(pa.field("dia", pa.string()))).to_table()
print("[paso 5] columnas:", completo.column_names, "| filas con canal:", completo.num_rows - completo["canal"].null_count)
# SALIDA ESPERADA:
#   [paso 5] columnas: ['id', 'cuenta_id', 'fecha', 'tipo', 'monto', 'canal', 'dia'] | filas con canal: 500

# 👉 TU TURNO 5: lee el conjunto SIN indicar el esquema. ¿Aparece «canal»? ¿De qué
#    depende? Ahora escribe un día en el que «monto» llegue como texto: ¿qué pasa al leer?


# REFLEXIONA: añadir una columna es fácil. ¿Qué cambios de esquema NO lo son?
# (Renombrar, cambiar un tipo, borrar.) Por eso existen Iceberg y Delta Lake.

# ════════════════════════════════════════════════════════════════════
# PASO 6 — El mismo conjunto, con cualquier motor
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: Parquet es un estándar abierto. Lo que escribiste con pandas lo leen
# Polars, Spark, DuckDB o Athena sin convertir nada. Ese es el fundamento de un
# data lake: los datos no pertenecen a ninguna herramienta.

con_polars = pl.scan_parquet(RAIZ / "dia=2026-07-03" / "*.parquet").select(pl.len()).collect().item()
print("[paso 6] pandas y Polars cuentan lo mismo:", con_polars == un_dia.num_rows)
# SALIDA ESPERADA:
#   [paso 6] pandas y Polars cuentan lo mismo: True

# 👉 TU TURNO 6: Polars también entiende las particiones: prueba
#    pl.scan_parquet(RAIZ / "**/*.parquet", hive_partitioning=True) y filtra por «dia».
#    Falla por la columna «canal» del paso 5: léete el error y arréglalo.
#    Después léelo con PySpark (spark.read.parquet(str(RAIZ))) y comprueba que
#    «dia» aparece como columna y que el plan de un filtro por día muestra
#    PartitionFilters (df.filter(...).explain()).


# ════════════════════════════════════════════════════════════════════
# RETO DE LA LECCIÓN (pasos 1 a 6)
# ════════════════════════════════════════════════════════════════════
# Diseña y escribe la capa «limpia» de un data lake con los 60,000 movimientos de
# 08_capstone/datos/banco_historico/. Decide y justifica por escrito: columna de
# partición, orden dentro de cada archivo, tamaño de los grupos y códec.
# COMPRUEBA con números: cuántos archivos hay, cuánto ocupa, y cuántos archivos y
# grupos se leen para (a) un mes completo y (b) una cuenta concreta en un año.
