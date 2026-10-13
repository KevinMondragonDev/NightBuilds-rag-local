"""
Tema 6 — Ingesta de datos | Lección 1: Excel, Parquet y archivos grandes
==========================================================================

TIEMPO: 1.5 h · ANTES DE EMPEZAR: 01_teoria_y_ejercicios/02_analisis_datos/05_csv.py

CÓMO USAR ESTA LECCIÓN:
    Va por PASOS pequeños. En cada uno: lee el concepto, PREDICE qué imprimirá el
    ejemplo, ejecuta el archivo, compara con la salida esperada y haz «TU TURNO»
    justo debajo. No pases al siguiente paso sin comprobar.

        python 06_ingenieria_de_datos/01_ingesta_de_datos/01_excel_y_otros_formatos.py

    pip install pandas openpyxl pyarrow

CALENTAMIENTO (sin mirar apuntes, responde en un comentario antes de empezar):
    1. ¿Qué hace index=False en df.to_csv(...)?
    2. ¿De qué tipo llega una columna de fechas al leer un CSV sin más opciones?
    3. ¿Qué parámetro de read_csv convierte "N/A" en nulo?
"""

import tempfile
from pathlib import Path

import pandas as pd

DATOS = Path(__file__).resolve().parents[1] / "datos"
TMP = Path(tempfile.mkdtemp())  # los ejemplos escriben aquí para no ensuciar el repositorio

movimientos = pd.read_csv(DATOS / "movimientos.csv", parse_dates=["fecha"])

# ════════════════════════════════════════════════════════════════════
# PASO 1 — Escribir y leer un Excel
# ════════════════════════════════════════════════════════════════════
# APRENDERÁS: a leer el formato que más usa la gente de negocio.
# CONCEPTO: read_excel y to_excel funcionan como sus equivalentes de CSV, pero un
# Excel guarda TIPOS (una fecha sigue siendo fecha) y puede tener varias HOJAS.

julio = movimientos[movimientos["fecha"].dt.month == 7]
julio.to_excel(TMP / "julio.xlsx", sheet_name="julio", index=False)
leido = pd.read_excel(TMP / "julio.xlsx")
print("[paso 1]", leido.shape, "| fecha es fecha:", pd.api.types.is_datetime64_any_dtype(leido["fecha"]))
# SALIDA ESPERADA:
#   [paso 1] (139, 7) | fecha es fecha: True

# 👉 TU TURNO 1: lee solo las columnas A a D y sáltate las 10 primeras filas de
#    datos (parámetros usecols y skiprows). ¿Qué pasa con los encabezados?


# REFLEXIONA: la fecha volvió como fecha sin pedir parse_dates. ¿Por qué con el
# CSV sí hace falta?

# ════════════════════════════════════════════════════════════════════
# PASO 2 — Varias hojas
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: ExcelWriter mantiene el archivo abierto para escribir varias hojas.
# Al leer, sheet_name=None devuelve un diccionario {nombre_de_hoja: DataFrame}.

with pd.ExcelWriter(TMP / "trimestre.xlsx") as writer:
    for mes, nombre in [(7, "julio"), (8, "agosto"), (9, "septiembre")]:
        movimientos[movimientos["fecha"].dt.month == mes].to_excel(writer, sheet_name=nombre, index=False)

hojas = pd.read_excel(TMP / "trimestre.xlsx", sheet_name=None)
print("[paso 2]", type(hojas).__name__, {nombre: len(df) for nombre, df in hojas.items()})
# SALIDA ESPERADA:
#   [paso 2] dict {'julio': 139, 'agosto': 122, 'septiembre': 139}

# 👉 TU TURNO 2: une las tres hojas en un solo DataFrame con una columna `hoja`
#    que diga de cuál viene cada fila (pd.concat).


# COMPRUEBA: el DataFrame unido tiene 400 filas y 8 columnas.

# ════════════════════════════════════════════════════════════════════
# PASO 3 — Archivos que no caben en memoria
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: chunksize convierte read_csv en un iterador de DataFrames pequeños.
# Procesas un trozo, guardas solo el resultado y pasas al siguiente.

total, trozos = 0.0, 0
for trozo in pd.read_csv(DATOS / "movimientos.csv", chunksize=100):
    total += trozo["monto"].sum()
    trozos += 1
print("[paso 3]", trozos, round(total, 2), round(movimientos["monto"].sum(), 2))
# SALIDA ESPERADA:
#   [paso 3] 4 909767.06 909767.06

# 👉 TU TURNO 3: con chunksize=50, calcula el gasto total POR CATEGORÍA sin tener
#    nunca el archivo entero en memoria. Pista: acumula en un diccionario o suma Series.


# COMPRUEBA: coincide con movimientos.groupby("categoria")["monto"].sum()
# REFLEXIONA: ¿qué cálculo NO se puede hacer trozo a trozo tan fácilmente? (Piensa
# en la mediana o en quitar duplicados.)

# ════════════════════════════════════════════════════════════════════
# PASO 4 — Parquet: el formato de los data lakes
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: CSV es texto por FILAS y no guarda tipos. Parquet es binario por
# COLUMNAS: guarda los tipos, comprime, y permite leer solo las columnas que pidas.

movimientos.to_csv(TMP / "mov.csv", index=False)
movimientos.to_parquet(TMP / "mov.parquet")
solo_dos = pd.read_parquet(TMP / "mov.parquet", columns=["fecha", "monto"])
es_fecha = pd.api.types.is_datetime64_any_dtype
print("[paso 4] fecha es fecha en CSV:", es_fecha(pd.read_csv(TMP / "mov.csv")["fecha"]),
      "| en Parquet:", es_fecha(solo_dos["fecha"]),
      "| Parquet pesa menos:", (TMP / "mov.parquet").stat().st_size < (TMP / "mov.csv").stat().st_size)
# SALIDA ESPERADA:
#   [paso 4] fecha es fecha en CSV: False | en Parquet: True | Parquet pesa menos: True

# 👉 TU TURNO 4: guarda los movimientos también en Excel y en pickle. Haz una tabla
#    con el tamaño de los cuatro archivos y si conservan el tipo de `fecha`.


# REFLEXIONA: da dos razones, vistas en este paso, por las que un data lake
# guarda Parquet y no CSV. ¿Y por qué nunca abrirías un pickle de origen desconocido?

# ════════════════════════════════════════════════════════════════════
# RETO DE LA LECCIÓN (pasos 1 a 4)
# ════════════════════════════════════════════════════════════════════
# Escribe leer_archivo(ruta) que detecte el formato por la extensión (.csv, .tsv,
# .xlsx, .parquet) y devuelva siempre un DataFrame. Si la extensión no está
# soportada, lanza un ValueError con un mensaje claro.
# COMPRUEBA: los cuatro formatos devuelven 400 filas; "datos.txt" lanza ValueError.
