"""
Tema 7 — Limpieza y eficiencia | Lección 5: Polars
====================================================

pandas es el estándar y lo seguirás usando. Polars es la alternativa moderna:
escrita en Rust, usa todos los núcleos, y tiene un modo «perezoso» que optimiza
la consulta antes de ejecutarla (la misma idea que Spark, en una sola máquina).

CÓMO USAR ESTA LECCIÓN: predice, ejecuta, compara con la salida esperada, tu turno.
    python 06_ingenieria_de_datos/02_limpieza_y_eficiencia/05_polars.py

    pandas                               Polars
    -----------------------------------  ------------------------------------------
    df[df["monto"] > 100]                df.filter(pl.col("monto") > 100)
    df["x"] = df["a"] * 2                df.with_columns((pl.col("a") * 2).alias("x"))
    df[["a", "b"]]                       df.select("a", "b")
    df.groupby("k")["v"].sum()           df.group_by("k").agg(pl.col("v").sum())
    df.merge(otro, on="k")               df.join(otro, on="k")
    índice                               no existe
    NaN / None                           null

    pip install polars

TIEMPO: 1.5 h · ANTES DE EMPEZAR: lección 4 de esta carpeta

CALENTAMIENTO (sin mirar apuntes, responde en un comentario antes de empezar):
    1. ¿Por qué una operación vectorizada es más rápida que apply?
    2. ¿Qué devuelve groupby().transform() que no devuelve agg()?
    3. ¿Qué estructura hace que el texto repetido ocupe menos memoria en pandas?
"""

from pathlib import Path

import polars as pl

RUTA = Path(__file__).resolve().parents[1] / "datos" / "movimientos.csv"

# ════════════════════════════════════════════════════════════════════
# PASO 1 — Leer y mirar
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: Polars infiere tipos y NO tiene índice. Las fechas se piden con
# try_parse_dates o se convierten después.

df = pl.read_csv(RUTA, try_parse_dates=True)
print("[paso 1]", df.shape, df.schema["fecha"], df.schema["monto"])
# SALIDA ESPERADA:
#   [paso 1] (400, 7) Datetime(time_unit='us', time_zone=None) Float64

# 👉 TU TURNO 1: imprime df.head(3) y df.describe(). ¿Cómo muestra Polars los
#    nulos de `comercio`? ¿Cuántos hay? (df.null_count())


# ════════════════════════════════════════════════════════════════════
# PASO 2 — Expresiones: filter, select, with_columns
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: en Polars no asignas columnas: describes EXPRESIONES con pl.col(...)
# y el motor las ejecuta en paralelo. Nada se modifica: cada método devuelve un
# DataFrame nuevo, así que se encadenan.

compras = (
    df.filter(pl.col("tipo") == "compra")
    .with_columns(
        (pl.col("monto") * 0.015).round(2).alias("comision"),
        pl.col("fecha").dt.month().alias("mes"),
    )
    .select("id", "mes", "categoria", "monto", "comision")
)
print("[paso 2]", compras.shape, compras.columns)
# SALIDA ESPERADA:
#   [paso 2] (247, 5) ['id', 'mes', 'categoria', 'monto', 'comision']

# 👉 TU TURNO 2: añade una columna `nivel` con "bajo" (< 500), "medio" (< 5000) o
#    "alto", usando pl.when(...).then(...).when(...).then(...).otherwise(...).


# REFLEXIONA: en pandas escribirías df["comision"] = ... ¿Qué ventaja tiene que
# Polars NO modifique el DataFrame original?


# ════════════════════════════════════════════════════════════════════
# PASO 3 — Agrupar
# ════════════════════════════════════════════════════════════════════

por_categoria = (
    compras.group_by("categoria")
    .agg(pl.len().alias("compras"), pl.col("monto").sum().round(2).alias("total"))
    .sort("total", descending=True)
)
print("[paso 3]", por_categoria.row(0), "| categorías:", por_categoria.height)
# SALIDA ESPERADA:
#   [paso 3] ('viajes', 38, 26472.47) | categorías: 6

# 👉 TU TURNO 3: gasto total por mes y categoría, y la compra más grande de cada
#    cuenta. Comprueba un par de valores contra tu resultado con pandas.


# ════════════════════════════════════════════════════════════════════
# PASO 4 — Modo perezoso (lazy): describir primero, ejecutar al final
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: scan_csv NO lee el archivo: construye un plan. Polars lo optimiza
# (lee solo las columnas necesarias, filtra mientras lee) y lo ejecuta en
# collect(). Es la evaluación perezosa de Spark (05_spark, fase 01).

consulta = (
    pl.scan_csv(RUTA)
    .filter(pl.col("tipo") == "compra")
    .group_by("categoria")
    .agg(pl.col("monto").mean().round(2).alias("ticket_promedio"))
    .sort("categoria")
)
print("[paso 4]", type(consulta).__name__, "->", consulta.collect().row(0))
# SALIDA ESPERADA:
#   [paso 4] LazyFrame -> ('entretenimiento', 543.41)

# 👉 TU TURNO 4: imprime consulta.explain(). Busca en el plan qué columnas lee del
#    CSV (PROJECT) y dónde aplica el filtro (SELECTION). ¿Lee las 7 columnas?


# REFLEXIONA: ¿por qué el modo perezoso puede leer menos datos que read_csv
# seguido de los mismos pasos?


# ════════════════════════════════════════════════════════════════════
# PASO 5 — Convivir con pandas
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: no es una cosa o la otra. Conviertes en los bordes:
#     pl.from_pandas(df_pandas)        df_polars.to_pandas()      (necesitan pyarrow)
#
# 👉 TU TURNO 5: repite el ejercicio 1 de 04_pandas_eficiente.py (la comisión sobre
#    100,000 filas) con Polars y mídelo con timeit junto a tu versión vectorizada
#    de pandas. Después hazlo con 5 millones de filas. ¿Cambia la diferencia?


# ════════════════════════════════════════════════════════════════════
# CUÁNDO USAR CADA UNO
# ════════════════════════════════════════════════════════════════════
#   pandas   ecosistema enorme, lo que encontrarás en casi todo código existente,
#            perfecto hasta unos pocos GB.
#   Polars   archivos grandes en una sola máquina, pipelines nuevos donde importa
#            el tiempo o la memoria.
#   Spark    cuando los datos no caben en una máquina (módulo 05_spark).

# ════════════════════════════════════════════════════════════════════
# RETO DE LA LECCIÓN (pasos 1 a 5)
# ════════════════════════════════════════════════════════════════════
# Reescribe en Polars, en modo perezoso, tres reglas de limpieza de las lecciones
# 1 y 2 sobre transacciones_sucias.csv (léelo con infer_schema_length=0 para que
# todo llegue como texto). Demuestra con un assert que el resultado coincide con
# el de tu versión en pandas.
