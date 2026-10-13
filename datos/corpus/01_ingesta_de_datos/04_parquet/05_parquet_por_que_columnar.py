"""
Tema 6 — Ingesta de datos | Lección 5: Parquet, el formato del big data
=========================================================================

TIEMPO: 1.5 h · ANTES DE EMPEZAR: lección 1 de esta sección (paso 4: primer contacto con Parquet)

CÓMO USAR ESTA LECCIÓN: predice, ejecuta, compara con la salida esperada, tu turno.
    python 05_ingenieria_de_datos/01_ingesta_de_datos/04_parquet/05_parquet_por_que_columnar.py

    Los ejemplos crean 300,000 movimientos en una carpeta temporal. Los tamaños y
    tiempos cambian según la máquina: se imprimen COMPARACIONES. Tú mira los números.

    pip install pandas pyarrow numpy

POR QUÉ UNA SECCIÓN ENTERA: en un data lake casi todo es Parquet. Spark, Athena,
Snowflake, DuckDB y Polars lo leen de forma nativa. Entender cómo guarda los datos
explica por qué unas consultas tardan segundos y otras horas sobre los mismos datos.

CALENTAMIENTO (sin mirar apuntes):
    1. ¿De qué tipo vuelve una fecha al leer un CSV? ¿Y al leer un Parquet?
    2. ¿Qué hace chunksize en read_csv y para qué sirve?
    3. Una consulta solo necesita 2 de 40 columnas. ¿Qué tiene que leer con un CSV?
"""

import tempfile
import timeit
from pathlib import Path

import numpy as np
import pandas as pd

TMP = Path(tempfile.mkdtemp())
rng = np.random.default_rng(7)
N = 300_000
movimientos = pd.DataFrame({
    "id": np.arange(N),
    "cuenta_id": rng.integers(1, 5_000, N),
    "fecha": pd.Timestamp("2026-01-01") + pd.to_timedelta(rng.integers(0, 270 * 24 * 3600, N), unit="s"),
    "tipo": rng.choice(["compra", "deposito", "retiro", "transferencia"], N, p=[0.6, 0.2, 0.1, 0.1]),
    "categoria": rng.choice(["supermercado", "restaurantes", "servicios", "viajes", "gasolina"], N),
    "monto": rng.lognormal(6, 0.9, N).round(2),
})

# ════════════════════════════════════════════════════════════════════
# PASO 1 — Por filas o por columnas
# ════════════════════════════════════════════════════════════════════
# APRENDERÁS: la idea de la que salen todas las ventajas de Parquet.
# CONCEPTO: un CSV guarda fila tras fila: para leer UNA columna hay que recorrer
# todas. Parquet guarda columna tras columna: los valores de «monto» están juntos.
#
#     CSV (por filas)                 Parquet (por columnas)
#     1,compra,120.5                  id:    1, 2, 3
#     2,deposito,900.0                tipo:  compra, deposito, compra
#     3,compra,45.0                   monto: 120.5, 900.0, 45.0
#
# Valores parecidos y juntos se comprimen mucho mejor, y cada columna guarda su tipo.

movimientos.to_csv(TMP / "mov.csv", index=False)
movimientos.to_parquet(TMP / "mov.parquet", index=False)
tam_csv, tam_parquet = (TMP / "mov.csv").stat().st_size, (TMP / "mov.parquet").stat().st_size
print("[paso 1] Parquet ocupa menos de la mitad:", tam_parquet < tam_csv / 2,
      "| conserva la fecha:", pd.api.types.is_datetime64_any_dtype(pd.read_parquet(TMP / "mov.parquet")["fecha"]))
# SALIDA ESPERADA:
#   [paso 1] Parquet ocupa menos de la mitad: True | conserva la fecha: True

# 👉 TU TURNO 1: imprime los dos tamaños en MB y cuántas veces más pequeño es el
#    Parquet. ¿Qué columna crees que se comprime mejor y cuál peor? Anótalo:
#    lo compruebas en la lección 6.


# ════════════════════════════════════════════════════════════════════
# PASO 2 — Leer solo lo que necesitas
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: como cada columna está en su propio bloque, pedir dos columnas lee
# dos bloques y se salta el resto del archivo. Se llama «poda de columnas» y es la
# razón por la que SELECT * es caro en un data lake.

t_todo = timeit.timeit(lambda: pd.read_parquet(TMP / "mov.parquet"), number=3)
t_dos = timeit.timeit(lambda: pd.read_parquet(TMP / "mov.parquet", columns=["tipo", "monto"]), number=3)
t_csv = timeit.timeit(lambda: pd.read_csv(TMP / "mov.csv", usecols=["tipo", "monto"]), number=3)
print("[paso 2] dos columnas es más rápido que todo:", t_dos < t_todo,
      "| y más rápido que pedirlas al CSV:", t_dos < t_csv)
# SALIDA ESPERADA:
#   [paso 2] dos columnas es más rápido que todo: True | y más rápido que pedirlas al CSV: True

# 👉 TU TURNO 2: imprime los tres tiempos. Con usecols el CSV también devuelve dos
#    columnas: ¿por qué sigue siendo más lento?


# REFLEXIONA: Athena cobra por los bytes que LEE. ¿Qué cuesta más: SELECT * o
# SELECT tipo, monto? ¿Y si el archivo fuera un CSV?

# ════════════════════════════════════════════════════════════════════
# PASO 3 — Compresión
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: Parquet comprime cada columna por separado. Se elige el códec:
#     snappy   rápido y razonable (el habitual por defecto)
#     zstd     comprime más, algo más lento al escribir
#     gzip     comprime bien, lento
#     none     sin comprimir
# Menos bytes = menos disco, menos red y, a menudo, lectura más rápida.

tamanos = {}
for codec in ["none", "snappy", "zstd"]:
    ruta = TMP / f"mov_{codec}.parquet"
    movimientos.to_parquet(ruta, index=False, compression=None if codec == "none" else codec)
    tamanos[codec] = ruta.stat().st_size
print("[paso 3] de mayor a menor:", sorted(tamanos, key=tamanos.get, reverse=True))
# SALIDA ESPERADA:
#   [paso 3] de mayor a menor: ['none', 'snappy', 'zstd']

# 👉 TU TURNO 3: mide además cuánto tarda en ESCRIBIR y en LEER cada códec.
#    Haz una tabla: códec, MB, segundos de escritura, segundos de lectura.


# REFLEXIONA: escribes una vez y lees mil. ¿Qué códec elegirías para la capa
# histórica de un data lake? ¿Y para un archivo temporal entre dos pasos?

# ════════════════════════════════════════════════════════════════════
# PASO 4 — El esquema viaja con los datos
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: un CSV no dice de qué tipo es cada columna: cada lector lo adivina, y
# a veces adivina distinto (un código postal «01000» que se vuelve 1000). Parquet
# guarda el esquema dentro del archivo: tipos, nombres y si admite nulos.

con_nulos = movimientos.head(5).assign(codigo_postal=["01000", "76000", None, "64000", "44100"])
con_nulos.to_csv(TMP / "cp.csv", index=False)
con_nulos.to_parquet(TMP / "cp.parquet", index=False)
print("[paso 4] CSV:", pd.read_csv(TMP / "cp.csv")["codigo_postal"].iloc[0],
      "| Parquet:", pd.read_parquet(TMP / "cp.parquet")["codigo_postal"].iloc[0])
# SALIDA ESPERADA:
#   [paso 4] CSV: 1000.0 | Parquet: 01000

# 👉 TU TURNO 4: ¿por qué el CSV devolvió 1000.0 y no 1000? (Mira qué hay en la
#    tercera fila.) Arregla la lectura del CSV con dtype. Con Parquet no hizo falta.


# REFLEXIONA: ¿quién es responsable de los tipos con CSV: quien escribe o cada
# uno de los que leen? ¿Y con Parquet?

# ════════════════════════════════════════════════════════════════════
# CUÁNDO **NO** USAR PARQUET
# ════════════════════════════════════════════════════════════════════
#   - Para intercambiar un archivo pequeño con alguien que lo abrirá en Excel: CSV.
#   - Para escribir fila a fila muchas veces por segundo: Parquet se escribe por
#     lotes; para eso hay bases de datos, colas o formatos por filas (Avro).
#   - Para editar una fila: un archivo Parquet no se modifica, se reescribe.

# ════════════════════════════════════════════════════════════════════
# RETO DE LA LECCIÓN (pasos 1 a 4)
# ════════════════════════════════════════════════════════════════════
# Convierte datos/transacciones_sucias.csv a Parquet SIN perder información: todo
# como texto (está sucio a propósito) y con un nombre de columna por cada original.
# Después conviértelo otra vez a CSV y demuestra con un assert que es idéntico al
# original. ¿Qué habría pasado si hubieras dejado que pandas adivinara los tipos?
