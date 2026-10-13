"""
Tema 9 — Pipelines | Lección 2: Carga idempotente, validación y logging
=========================================================================

TIEMPO: 2.5 h · ANTES DE EMPEZAR: lección 1 (y su reto: el ETL por fecha que duplica)

CÓMO USAR ESTA LECCIÓN: predice, ejecuta, compara con la salida esperada, tu turno.
    export PGPASSWORD="tu_clave"
    python 06_ingenieria_de_datos/04_pipelines/02_carga_y_monitoreo.py

CALENTAMIENTO (sin mirar apuntes):
    1. ¿Qué diferencia hay entre ETL y ELT? ¿Dónde transforma cada uno?
    2. En el reto de la lección 1, ¿qué pasó al cargar dos veces el mismo día? ¿Por qué?
    3. ¿Qué garantiza una transacción?
"""

import logging
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
movimientos = pd.read_csv(DATOS / "movimientos.csv", parse_dates=["fecha"])
dia = movimientos[movimientos["fecha"].dt.date.astype(str) == "2026-07-01"][["id", "cuenta_id", "fecha", "tipo", "monto"]]

with engine.begin() as con:
    con.execute(text("DROP TABLE IF EXISTS analitica.movimientos_dia"))
    con.execute(text("""CREATE TABLE analitica.movimientos_dia (
        id INT PRIMARY KEY, cuenta_id INT, fecha TIMESTAMP, tipo TEXT, monto NUMERIC(12,2))"""))


def contar() -> int:
    with engine.connect() as con:
        return con.execute(text("SELECT count(*) FROM analitica.movimientos_dia")).scalar()


# ════════════════════════════════════════════════════════════════════
# PASO 1 — El problema: un pipeline se relanza
# ════════════════════════════════════════════════════════════════════
# APRENDERÁS: por qué «append» es peligroso.
# CONCEPTO: los pipelines fallan y se reintentan; es lo normal. Si cada intento
# AÑADE filas, cada reintento duplica. (Aquí la clave primaria lo impide y la
# carga falla; sin ella, tendrías el doble de filas sin enterarte.)

dia.to_sql("movimientos_dia", engine, schema="analitica", if_exists="append", index=False)
try:
    dia.to_sql("movimientos_dia", engine, schema="analitica", if_exists="append", index=False)
    segundo_intento = "duplicó"
except Exception:
    segundo_intento = "rechazado por la clave primaria"
print("[paso 1] filas:", contar(), "| segundo intento:", segundo_intento)
# SALIDA ESPERADA:
#   [paso 1] filas: 4 | segundo intento: rechazado por la clave primaria

# 👉 TU TURNO 1: crea una tabla igual pero SIN clave primaria y carga el día tres
#    veces con append. ¿Cuántas filas quedan? ¿Qué error viste? (Ninguno: ese es el problema.)


# ════════════════════════════════════════════════════════════════════
# PASO 2 — Idempotencia (a): borrar e insertar la partición
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: IDEMPOTENTE = ejecutar N veces deja lo mismo que ejecutar una.
# Receta 1: en UNA transacción, borras todo lo del día y lo vuelves a insertar.
# Si falla a la mitad, el ROLLBACK deja la tabla como estaba.


def cargar_dia(df: pd.DataFrame, fecha: str) -> None:
    with engine.begin() as con:
        con.execute(text("DELETE FROM analitica.movimientos_dia WHERE fecha::date = :dia"), {"dia": fecha})
        df.to_sql("movimientos_dia", con, schema="analitica", if_exists="append", index=False)


for _ in range(3):
    cargar_dia(dia, "2026-07-01")
print("[paso 2] filas tras 3 ejecuciones:", contar())
# SALIDA ESPERADA:
#   [paso 2] filas tras 3 ejecuciones: 4

# 👉 TU TURNO 2: provoca un fallo a mitad: una versión de cargar_dia que lance una
#    excepción entre el DELETE y el to_sql.


# COMPRUEBA: tras el fallo siguen las 4 filas. ¿Qué habría pasado sin engine.begin()?

# ════════════════════════════════════════════════════════════════════
# PASO 3 — Idempotencia (b): UPSERT
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: Receta 2: «inserta, y si la clave ya existe, actualiza». Necesita una
# clave primaria. Sirve cuando llegan correcciones de filas sueltas.

UPSERT = text("""
    INSERT INTO analitica.movimientos_dia (id, cuenta_id, fecha, tipo, monto)
    VALUES (:id, :cuenta_id, :fecha, :tipo, :monto)
    ON CONFLICT (id) DO UPDATE SET monto = EXCLUDED.monto, tipo = EXCLUDED.tipo
""")
corregido = dia.copy()
corregido.iloc[0, corregido.columns.get_loc("monto")] = 1.0  # llega una corrección
with engine.begin() as con:
    con.execute(UPSERT, corregido.to_dict("records"))
with engine.connect() as con:
    monto = con.execute(text("SELECT monto FROM analitica.movimientos_dia WHERE id = :id"),
                        {"id": int(corregido.iloc[0]["id"])}).scalar()
print("[paso 3] filas:", contar(), "| monto corregido:", float(monto))
# SALIDA ESPERADA:
#   [paso 3] filas: 4 | monto corregido: 1.0

# 👉 TU TURNO 3: quita una fila de `dia` (como si el origen la hubiera eliminado)
#    y vuelve a cargar con cada receta. ¿Cuántas filas quedan con cada una?


# REFLEXIONA: ¿cuándo elegirías borrar e insertar y cuándo UPSERT?

# ════════════════════════════════════════════════════════════════════
# PASO 4 — Validar ANTES de cargar
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: si los datos están mal, es mejor que el pipeline falle a que cargue.
# Un fallo se ve y se arregla; un dato malo cargado se propaga a los reportes.


def validar(df: pd.DataFrame) -> list[str]:
    errores = []
    if df.empty:
        errores.append("sin filas")
    if df["id"].duplicated().any():
        errores.append("ids duplicados")
    if (df["monto"] <= 0).any():
        errores.append("montos no positivos")
    return errores


malo = pd.concat([dia, dia.head(1).assign(monto=-5.0)])
print("[paso 4] día bueno:", validar(dia), "| día malo:", validar(malo))
# SALIDA ESPERADA:
#   [paso 4] día bueno: [] | día malo: ['ids duplicados', 'montos no positivos']

# 👉 TU TURNO 4: añade tres comprobaciones más (fechas del día pedido, tipos
#    válidos, cuenta_id existente en la tabla cuentas) y une validar con cargar_dia:
#    si hay errores, lanza ValueError y NO cargues nada.


# ════════════════════════════════════════════════════════════════════
# PASO 5 — Logging: saber qué pasó sin estar mirando
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: print se pierde y no dice cuándo ni con qué gravedad. logging añade
# hora y nivel (DEBUG < INFO < WARNING < ERROR), y se puede mandar a un archivo.
# log.exception, dentro de un except, guarda además el traceback.

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s", stream=sys.stdout)
log = logging.getLogger("pipeline")
log.info("extraídas %d filas del día %s", len(dia), "2026-07-01")
if validar(malo):
    log.error("validación fallida: %s", validar(malo))
# SALIDA ESPERADA:
#   INFO pipeline extraídas 4 filas del día 2026-07-01
#   ERROR pipeline validación fallida: ['ids duplicados', 'montos no positivos']

# 👉 TU TURNO 5: añade la hora al formato (%(asctime)s) y envía el log también a
#    un archivo. Haz que cada etapa registre filas de entrada, de salida y segundos.


# REFLEXIONA: son las 3 de la mañana y el pipeline falló. ¿Qué tres datos
# necesitas encontrar en el log para arreglarlo sin ejecutar nada?

# ════════════════════════════════════════════════════════════════════
# RETO DE LA LECCIÓN (pasos 1 a 5)
# ════════════════════════════════════════════════════════════════════
# Arregla tu ETL por fecha de la lección 1: validación antes de cargar, carga
# idempotente y logging. Después escribe un decorador @etapa que registre inicio,
# fin, duración y número de filas del DataFrame que devuelve la función, y que
# registre la excepción si falla. Aplícalo a extraer, transformar y cargar.
# COMPRUEBA: tres días cargados, uno de ellos tres veces: las filas no cambian.
