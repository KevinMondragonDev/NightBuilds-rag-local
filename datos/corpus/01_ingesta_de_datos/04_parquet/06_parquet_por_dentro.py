"""
Tema 6 — Ingesta de datos | Lección 6: Parquet por dentro
===========================================================

TIEMPO: 2 h · ANTES DE EMPEZAR: lección 5

CÓMO USAR ESTA LECCIÓN: predice, ejecuta, compara con la salida esperada, tu turno.
    python 05_ingenieria_de_datos/01_ingesta_de_datos/04_parquet/06_parquet_por_dentro.py

    Aquí se usa pyarrow directamente: es la biblioteca que pandas, Polars y Spark
    usan por debajo para leer y escribir Parquet.

CALENTAMIENTO (sin mirar apuntes):
    1. ¿Por qué pedir dos columnas a un Parquet es más rápido que pedírselas a un CSV?
    2. ¿Qué códec comprime más: snappy o zstd? ¿Cuál es la contrapartida?
    3. ¿Dónde guarda Parquet el tipo de cada columna?
"""

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

TMP = Path(tempfile.mkdtemp())
rng = np.random.default_rng(7)
N = 300_000
movimientos = pd.DataFrame({
    "id": np.arange(N),
    "cuenta_id": rng.integers(1, 5_000, N),
    "fecha": pd.Timestamp("2026-01-01") + pd.to_timedelta(rng.integers(0, 270 * 24 * 3600, N), unit="s"),
    "tipo": rng.choice(["compra", "deposito", "retiro", "transferencia"], N, p=[0.6, 0.2, 0.1, 0.1]),
    "monto": rng.lognormal(6, 0.9, N).round(2),
})
tabla = pa.Table.from_pandas(movimientos, preserve_index=False)

# ════════════════════════════════════════════════════════════════════
# PASO 1 — La estructura: archivo -> grupos de filas -> columnas
# ════════════════════════════════════════════════════════════════════
# APRENDERÁS: qué hay dentro de un archivo Parquet.
# CONCEPTO: el archivo se divide en GRUPOS DE FILAS (row groups). Dentro de cada
# grupo, cada columna está en su propio bloque. Al final va el PIE: el esquema y
# un índice de dónde está cada bloque. Por eso un lector abre primero el final.
#
#     ┌ grupo 0 ┬ id | cuenta_id | fecha | tipo | monto ┐
#     ├ grupo 1 ┼ id | cuenta_id | fecha | tipo | monto ┤
#     ├ grupo 2 ┼ ...                                    ┤
#     └ pie ────┴ esquema + estadísticas + posiciones ──┘

pq.write_table(tabla, TMP / "mov.parquet", row_group_size=50_000)
archivo = pq.ParquetFile(TMP / "mov.parquet")
meta = archivo.metadata
print("[paso 1]", meta.num_rows, "filas |", meta.num_row_groups, "grupos |", meta.num_columns, "columnas |",
      archivo.schema_arrow.names)
# SALIDA ESPERADA:
#   [paso 1] 300000 filas | 6 grupos | 5 columnas | ['id', 'cuenta_id', 'fecha', 'tipo', 'monto']

# 👉 TU TURNO 1: imprime archivo.schema_arrow completo. ¿De qué tipo exacto es
#    «fecha»? ¿Y «tipo»? Vuelve a escribir el archivo con row_group_size=10_000:
#    ¿cuántos grupos salen?


# ════════════════════════════════════════════════════════════════════
# PASO 2 — Estadísticas: cada bloque sabe su mínimo y su máximo
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: el pie guarda, por cada columna de cada grupo, el valor mínimo, el
# máximo y cuántos nulos hay. Un lector puede decidir, SIN LEER LOS DATOS, si un
# grupo puede contener lo que busca.

id_col = archivo.schema_arrow.names.index("id")
rangos = [(meta.row_group(g).column(id_col).statistics.min, meta.row_group(g).column(id_col).statistics.max)
          for g in range(meta.num_row_groups)]
print("[paso 2] id por grupo:", rangos[:3], "...")
# SALIDA ESPERADA:
#   [paso 2] id por grupo: [(0, 49999), (50000, 99999), (100000, 149999)] ...

# 👉 TU TURNO 2: imprime el mínimo y el máximo de «monto» de cada grupo. ¿Se
#    parecen entre sí los rangos de los grupos? Compáralo con los de «id».


# REFLEXIONA: buscas id = 120000. ¿Cuántos grupos hay que leer? Buscas
# monto > 50000. ¿Cuántos? ¿De qué depende la diferencia?

# ════════════════════════════════════════════════════════════════════
# PASO 3 — Filtrar sin leer: «predicate pushdown»
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: si pasas el filtro al LECTOR (en lugar de leer todo y filtrar en
# pandas), usa las estadísticas para saltarse grupos enteros. Con Spark, Athena y
# Polars ocurre lo mismo, de forma automática.


def grupos_necesarios(ruta: Path, columna: str, minimo: float, maximo: float) -> int:
    """Cuántos grupos pueden contener valores de `columna` entre minimo y maximo."""
    m = pq.ParquetFile(ruta).metadata
    indice = pq.ParquetFile(ruta).schema_arrow.names.index(columna)
    return sum(1 for g in range(m.num_row_groups)
               if m.row_group(g).column(indice).statistics.max >= minimo
               and m.row_group(g).column(indice).statistics.min <= maximo)


filtrado = pq.read_table(TMP / "mov.parquet", filters=[("id", ">=", 120_000), ("id", "<", 125_000)])
print("[paso 3] filas:", filtrado.num_rows, "| grupos leídos:", grupos_necesarios(TMP / "mov.parquet", "id", 120_000, 124_999), "de 6")
# SALIDA ESPERADA:
#   [paso 3] filas: 5000 | grupos leídos: 1 de 6

# 👉 TU TURNO 3: con pandas, compara el tiempo de
#        pd.read_parquet(ruta, filters=[("id", ">=", 120_000), ("id", "<", 125_000)])
#    frente a leerlo todo y filtrar después. Comprueba que dan las mismas filas.


# ════════════════════════════════════════════════════════════════════
# PASO 4 — El orden al escribir decide lo que se puede saltar
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: las estadísticas solo ayudan si los valores están AGRUPADOS. Los id
# estaban en orden; las cuentas, repartidas al azar por todo el archivo. Si
# ordenas por la columna por la que más se filtra antes de escribir, cada grupo
# cubre un rango estrecho y casi todos se pueden saltar.

antes = grupos_necesarios(TMP / "mov.parquet", "cuenta_id", 4_200, 4_210)
ordenada = pa.Table.from_pandas(movimientos.sort_values("cuenta_id"), preserve_index=False)
pq.write_table(ordenada, TMP / "mov_ordenado.parquet", row_group_size=50_000)
despues = grupos_necesarios(TMP / "mov_ordenado.parquet", "cuenta_id", 4_200, 4_210)
print("[paso 4] grupos para cuenta_id entre 4200 y 4210 -> sin ordenar:", antes, "| ordenado:", despues)
# SALIDA ESPERADA:
#   [paso 4] grupos para cuenta_id entre 4200 y 4210 -> sin ordenar: 6 | ordenado: 1

# 👉 TU TURNO 4: al ordenar por cuenta_id, ¿qué le pasó a la búsqueda por id?
#    Mídelo con grupos_necesarios. No se puede ordenar por todo a la vez.


# REFLEXIONA: ¿cómo decides por qué columna ordenar? ¿Qué necesitas saber de
# quienes consultan los datos?

# ════════════════════════════════════════════════════════════════════
# PASO 5 — Cómo se codifica una columna
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: antes de comprimir, Parquet CODIFICA. Una columna con pocos valores
# distintos se guarda como un diccionario (compra=0, deposito=1...) más una lista
# de números pequeños. Por eso «tipo» casi no ocupa y «monto» ocupa mucho.

grupo = meta.row_group(0)
ocupa = {grupo.column(i).path_in_schema: grupo.column(i).total_compressed_size for i in range(meta.num_columns)}
print("[paso 5] la columna que menos ocupa:", min(ocupa, key=ocupa.get), "| la que más:", max(ocupa, key=ocupa.get))
# SALIDA ESPERADA:
#   [paso 5] la columna que menos ocupa: tipo | la que más: fecha

# 👉 TU TURNO 5: imprime los bytes de cada columna y qué porcentaje del grupo es.
#    ¿Acertaste tu predicción de la lección 5? ¿Por qué «fecha» ocupa tanto si
#    todas las fechas se parecen? (Mira su precisión y si están ordenadas.)


# ════════════════════════════════════════════════════════════════════
# RETO DE LA LECCIÓN (pasos 1 a 5)
# ════════════════════════════════════════════════════════════════════
# Descarga un mes de viajes de taxi de Nueva York (unos 59 MB):
#   https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2025-01.parquet
# SIN cargarlo en memoria, responde leyendo solo el pie: cuántas filas, cuántos
# grupos, qué columnas, cuál ocupa más y por qué columna parece estar ordenado.
# Después lee solo los viajes de un día con `filters` y di cuántos grupos se leyeron.
