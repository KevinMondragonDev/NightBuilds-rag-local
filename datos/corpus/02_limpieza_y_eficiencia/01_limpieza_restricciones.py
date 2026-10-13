"""
Tema 7 — Limpieza y eficiencia | Lección 1: Diagnóstico, tipos, rangos y duplicados
=====================================================================================

TIEMPO: 2 h · ANTES DE EMPEZAR: 01_teoria_y_ejercicios/02_analisis_datos/03_pandas.py y 04_pandas_avanzado.py

CÓMO USAR ESTA LECCIÓN: predice, ejecuta, compara con la salida esperada, tu turno.
    python 06_ingenieria_de_datos/02_limpieza_y_eficiencia/01_limpieza_restricciones.py

    Los EJEMPLOS usan una tabla pequeña inventada (MUESTRA) para que veas cada
    idea a simple vista. Los «TU TURNO» se hacen sobre el archivo real,
    datos/transacciones_sucias.csv, que tiene los mismos problemas... y más.

    pip install pandas

CALENTAMIENTO (sin mirar apuntes):
    1. ¿Qué hace errors="coerce"? (Si no lo recuerdas, lo verás en el paso 2.)
    2. ¿Cómo cuentas los nulos de cada columna de un DataFrame?
    3. ¿Qué diferencia hay entre df.duplicated() y df.drop_duplicates()?
"""

from pathlib import Path

import pandas as pd

DATOS = Path(__file__).resolve().parents[1] / "datos"

MUESTRA = pd.DataFrame({
    "id":    ["1", "2", "2", "3", "4", "4", "5"],
    "fecha": ["2026-03-01 10:00", "02/03/2026 11:30", "02/03/2026 11:30", "2031-03-03 09:00",
              "2026-03-04 08:15", "2026-03-04 08:15", "2026-03-05 19:45"],
    "monto": ["120.50", "$1,300.00", "$1,300.00", "80", "-45.00", "60.00", ""],
})

# ════════════════════════════════════════════════════════════════════
# PASO 1 — Diagnosticar antes de tocar nada
# ════════════════════════════════════════════════════════════════════
# APRENDERÁS: a medir un problema antes de arreglarlo.
# CONCEPTO: limpiar sin diagnosticar es borrar a ciegas. Primero CUENTAS: cuántas
# filas, cuántos vacíos, cuántos valores que no son lo que deberían. Lee siempre
# los datos sucios como texto (dtype=str) para verlos tal como vienen.

no_numericos = pd.to_numeric(MUESTRA["monto"], errors="coerce").isna()
print("[paso 1]", MUESTRA.shape, "| montos que no son número:", int(no_numericos.sum()),
      "->", MUESTRA.loc[no_numericos, "monto"].tolist())
# SALIDA ESPERADA:
#   [paso 1] (7, 3) | montos que no son número: 3 -> ['$1,300.00', '$1,300.00', '']

# 👉 TU TURNO 1: lee transacciones_sucias.csv con dtype=str. Sin modificar nada:
#    a) filas y columnas, y nulos por columna;
#    b) cuántos montos NO se convierten a número directamente, con 5 ejemplos.


# COMPRUEBA: 1,560 filas y 7 columnas.
# REFLEXIONA: en MUESTRA el monto vacío es "" y no NaN. ¿Qué hace read_csv con las
# celdas vacías? ¿Por qué importa esa diferencia al contar?

# ════════════════════════════════════════════════════════════════════
# PASO 2 — Tipos: que un número sea número y una fecha, fecha
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: cada columna sucia tiene VARIOS motivos para no convertirse. Los
# quitas uno a uno y lo que siga sin convertirse queda como nulo (errors="coerce"),
# a la vista, en lugar de romper el programa.

limpia = MUESTRA.copy()
limpia["monto"] = pd.to_numeric(
    limpia["monto"].str.replace("$", "", regex=False).str.replace(",", "", regex=False), errors="coerce")

iso = pd.to_datetime(limpia["fecha"], format="%Y-%m-%d %H:%M", errors="coerce")
dia_primero = pd.to_datetime(limpia["fecha"], format="%d/%m/%Y %H:%M", errors="coerce")
limpia["fecha"] = iso.fillna(dia_primero)  # prueba un formato y, donde falle, el otro
limpia["id"] = limpia["id"].astype(int)

print("[paso 2]", limpia["monto"].tolist(), "| fechas sin convertir:", int(limpia["fecha"].isna().sum()))
# SALIDA ESPERADA:
#   [paso 2] [120.5, 1300.0, 1300.0, 80.0, -45.0, 60.0, nan] | fechas sin convertir: 0

# 👉 TU TURNO 2: en el archivo real, convierte monto a número, fecha a fecha
#    (hay dos formatos) y cuenta_id a entero que admita nulos (dtype "Int64").


# COMPRUEBA con assert: los tres dtypes son los esperados y no perdiste filas.
# REFLEXIONA: 02/03/2026 ¿es 2 de marzo o 3 de febrero? ¿Cómo lo sabrías con datos
# reales? ¿Qué pasaría si dejaras que pandas lo adivinara?

# ════════════════════════════════════════════════════════════════════
# PASO 3 — Rangos: valores que tienen el tipo correcto pero son imposibles
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: -45 es un número válido y 2031 una fecha válida, pero no en este
# negocio. Opciones: descartar, dejar nulo, recortar (clip) o corregir con una
# regla. La elección es de NEGOCIO, no técnica: se anota y se justifica.

hoy = pd.Timestamp("2026-10-01")
print("[paso 3] montos <= 0:", int((limpia["monto"] <= 0).sum()),
      "| fechas futuras:", int((limpia["fecha"] > hoy).sum()))
# SALIDA ESPERADA:
#   [paso 3] montos <= 0: 1 | fechas futuras: 1

# 👉 TU TURNO 3: en el archivo real:
#    a) cuántos montos negativos y cuántas fechas futuras hay;
#    b) hay montos exageradamente altos: encuéntralos y explica con qué criterio
#       decides que son «exagerados» (no vale «a ojo»);
#    c) qué cuenta_id no existen en la tabla cuentas de PostgreSQL.


# REFLEXIONA: un monto negativo, ¿es un error de captura o una devolución?
# ¿Quién debería decidirlo y qué harías mientras no lo sepas?

# ════════════════════════════════════════════════════════════════════
# PASO 4 — Duplicados: iguales del todo o solo en la clave
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: hay dos casos MUY distintos.
#   Copia exacta (toda la fila igual): se borra sin miedo.
#   Misma clave, distinto contenido: una de las dos es la buena y no sabes cuál.

copias = limpia.duplicated()
misma_clave = limpia.drop_duplicates().duplicated(subset=["id"], keep=False)
print("[paso 4] copias exactas:", int(copias.sum()),
      "| ids en conflicto:", sorted(limpia.drop_duplicates().loc[misma_clave, "id"].unique().tolist()))
# SALIDA ESPERADA:
#   [paso 4] copias exactas: 1 | ids en conflicto: [4]

# 👉 TU TURNO 4: en el archivo real, cuenta las copias exactas y elimínalas. Los
#    id en conflicto NO los resuelvas todavía: sepáralos en otro DataFrame y
#    muestra un par para ver en qué se diferencian.


# COMPRUEBA: tras quitar las copias exactas quedan 1,515 filas.
# REFLEXIONA: el id 4 de MUESTRA tiene -45 y 60. ¿Con cuál te quedarías? ¿Qué
# información te falta para decidirlo bien?

# ════════════════════════════════════════════════════════════════════
# RETO DE LA LECCIÓN (pasos 1 a 4)
# ════════════════════════════════════════════════════════════════════
# Escribe diagnosticar(df) que devuelva un DataFrame con una fila por problema
# encontrado: nombre del problema, columna y número de filas afectadas.
# Tiene que servir para cualquier archivo con estas columnas, no solo para este.
# COMPRUEBA: diagnosticar(MUESTRA leída como texto) encuentra al menos 6 problemas.
