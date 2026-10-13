"""
Tema 6 — Ingesta de datos | Lección 2: PostgreSQL desde Python
================================================================

TIEMPO: 2 h · ANTES DE EMPEZAR: lección 1 y saber escribir un SELECT con JOIN y GROUP BY

CÓMO USAR ESTA LECCIÓN: predice, ejecuta, compara con la salida esperada, tu turno.

    Preparación (una sola vez):
        createdb -U postgres banco_python
        psql -U postgres -d banco_python -f 06_ingenieria_de_datos/datos/banco.sql

    En cada terminal, antes de ejecutar (la contraseña NUNCA va en el código):
        export PGPASSWORD="tu_clave"
        python 06_ingenieria_de_datos/01_ingesta_de_datos/02_bases_de_datos_sql.py

    pip install pandas sqlalchemy "psycopg[binary]"

CALENTAMIENTO (sin mirar apuntes):
    1. ¿Qué diferencia hay entre INNER JOIN y LEFT JOIN?
    2. ¿Por qué Parquet conserva el tipo de una fecha y CSV no?
    3. ¿Qué devuelve pd.read_excel(ruta, sheet_name=None)?
"""

import os
import sys

import pandas as pd
import psycopg
from sqlalchemy import URL, create_engine, text

DB = {
    "host": os.environ.get("PGHOST", "localhost"),
    "port": int(os.environ.get("PGPORT", "5432")),
    "dbname": os.environ.get("PGDATABASE", "banco_python"),
    "user": os.environ.get("PGUSER", "postgres"),
    "password": os.environ.get("PGPASSWORD"),
}

try:
    con = psycopg.connect(**DB)
except psycopg.OperationalError as error:
    sys.exit(f"No pude conectar a PostgreSQL: {error}\n¿Creaste banco_python y exportaste PGPASSWORD? Mira la cabecera.")

# ════════════════════════════════════════════════════════════════════
# PASO 1 — Conectar y consultar con el driver (psycopg)
# ════════════════════════════════════════════════════════════════════
# APRENDERÁS: qué devuelve exactamente la base de datos a Python.
# CONCEPTO: execute envía el SQL; fetchall trae las filas como TUPLAS. El driver
# convierte cada tipo de PostgreSQL a uno de Python (DATE -> date, NUMERIC -> Decimal).

fila = con.execute("SELECT id, nombre, fecha_alta FROM clientes ORDER BY id").fetchone()
saldo = con.execute("SELECT saldo FROM cuentas WHERE id = 1").fetchone()[0]
print("[paso 1]", fila, "|", type(saldo).__name__, saldo)
# SALIDA ESPERADA:
#   [paso 1] (1, 'Ana López', datetime.date(2022, 10, 15)) | Decimal 67144.46

# 👉 TU TURNO 1: lista las tablas del esquema public consultando
#    information_schema.tables. Después trae todas las cuentas con fetchall().


# REFLEXIONA: el saldo llega como Decimal y no como float. ¿Por qué es lo correcto
# para dinero? Prueba 0.1 + 0.2 en Python.

# ════════════════════════════════════════════════════════════════════
# PASO 2 — Parámetros: nunca construyas SQL con f-strings
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: si pegas texto del usuario dentro del SQL, el usuario puede ESCRIBIR
# SQL (inyección). Con parámetros (%s), el valor viaja aparte y nunca se ejecuta.

entrada = "plus' OR '1'='1"  # lo que teclea alguien con malas intenciones

inseguro = con.execute(f"SELECT count(*) FROM clientes WHERE segmento = '{entrada}'").fetchone()[0]
seguro = con.execute("SELECT count(*) FROM clientes WHERE segmento = %s", (entrada,)).fetchone()[0]
print("[paso 2] con f-string:", inseguro, "| con parámetro:", seguro)
# SALIDA ESPERADA:
#   [paso 2] con f-string: 12 | con parámetro: 0

# 👉 TU TURNO 2: escribe clientes_de(segmento, ciudad) con dos parámetros.


# COMPRUEBA: clientes_de("basico", "Querétaro") devuelve 2 clientes.
# REFLEXIONA: ¿por qué la versión insegura devolvió los 12 clientes?

# ════════════════════════════════════════════════════════════════════
# PASO 3 — De una consulta a un DataFrame (SQLAlchemy + pandas)
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: SQLAlchemy da una interfaz común a cualquier motor. pandas la usa para
# leer (read_sql) y escribir (to_sql). Fíjate en los tipos que llegan.

engine = create_engine(URL.create("postgresql+psycopg", username=DB["user"], password=DB["password"],
                                  host=DB["host"], port=DB["port"], database=DB["dbname"]))
cuentas = pd.read_sql("SELECT * FROM cuentas", engine)
clientes = pd.read_sql("SELECT * FROM clientes", engine)
print("[paso 3]", cuentas.shape, "| saldo:", cuentas["saldo"].dtype,
      "| fecha_alta es fecha:", pd.api.types.is_datetime64_any_dtype(clientes["fecha_alta"]),
      "| sin ciudad:", int(clientes["ciudad"].isna().sum()))
# SALIDA ESPERADA:
#   [paso 3] (15, 4) | saldo: float64 | fecha_alta es fecha: False | sin ciudad: 4

# 👉 TU TURNO 3: fecha_alta NO llegó como fecha de pandas. Corrígelo al leer con el parámetro
#    parse_dates. Trae solo las cuentas de ahorro usando text("... :tipo") y params.


# COMPRUEBA: fecha_alta ya es de tipo fecha; hay 5 cuentas de ahorro.

# ════════════════════════════════════════════════════════════════════
# PASO 4 — ¿Quién hace el trabajo: la base o pandas?
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: puedes traer todo y agrupar en pandas, o pedirle a la base el
# resultado ya agrupado. Lo segundo mueve muchos menos datos por la red.

en_sql = pd.read_sql("""
    SELECT c.segmento, count(*) AS cuentas, sum(a.saldo) AS saldo_total
    FROM clientes c JOIN cuentas a ON a.cliente_id = c.id
    GROUP BY c.segmento ORDER BY c.segmento
""", engine)
print("[paso 4]", en_sql.to_dict("records"))
# SALIDA ESPERADA:
#   [paso 4] [{'segmento': 'basico', 'cuentas': 10, 'saldo_total': 515871.06}, {'segmento': 'plus', 'cuentas': 3, 'saldo_total': 115995.57}, {'segmento': 'premium', 'cuentas': 2, 'saldo_total': 207060.87}]

# 👉 TU TURNO 4: obtén la misma tabla con merge + groupby sobre los DataFrames del
#    paso 3 y compárala con en_sql.


# REFLEXIONA: con 15 filas da igual. ¿Cuál elegirías con 500 millones de cuentas?

# ════════════════════════════════════════════════════════════════════
# PASO 5 — Escribir, y qué significa una transacción
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: una transacción es «todo o nada». Si algo falla antes del COMMIT, la
# base deshace lo que llevaba (ROLLBACK). Así no queda dinero a medio mover.

try:
    with con.transaction():
        con.execute("UPDATE cuentas SET saldo = saldo - 500 WHERE id = 1")
        raise RuntimeError("se cayó la red entre los dos UPDATE")
        con.execute("UPDATE cuentas SET saldo = saldo + 500 WHERE id = 2")
except RuntimeError:
    pass
print("[paso 5] saldo de la cuenta 1:", con.execute("SELECT saldo FROM cuentas WHERE id = 1").fetchone()[0])
# SALIDA ESPERADA:
#   [paso 5] saldo de la cuenta 1: 67144.46

# 👉 TU TURNO 5: guarda en_sql en una tabla resumen_segmento con to_sql. Ejecuta el
#    script dos veces con if_exists="fail", "append" y "replace". Anota qué pasa.
#    Al terminar: DROP TABLE resumen_segmento.


# REFLEXIONA: ¿cuál de los tres modos de if_exists es peligroso en un pipeline
# que se reintenta? (Volverás a esto en 04_pipelines/02.)

con.close()

# ════════════════════════════════════════════════════════════════════
# RETO DE LA LECCIÓN (pasos 1 a 5)
# ════════════════════════════════════════════════════════════════════
# Escribe extraer_tabla(engine, tabla, desde=None) que devuelva un DataFrame con la
# tabla completa o, si recibe una fecha, solo las filas con fecha_alta >= desde.
# Los valores, con parámetros. El nombre de la tabla NO se puede pasar como
# parámetro: valídalo contra una lista de tablas permitidas.
# COMPRUEBA: extraer_tabla(engine, "clientes", "2022-01-01") devuelve 5 filas;
# extraer_tabla(engine, "usuarios; DROP TABLE cuentas") lanza ValueError.
