"""
Tema 7 — Limpieza y eficiencia | Lección 4: pandas eficiente
==============================================================

TIEMPO: 1.5 h · ANTES DE EMPEZAR: lección 3 de esta sección

CÓMO USAR ESTA LECCIÓN: predice, ejecuta, compara con la salida esperada, tu turno.
    python 05_ingenieria_de_datos/02_limpieza_y_eficiencia/02_eficiencia/04_pandas_eficiente.py

CALENTAMIENTO (sin mirar apuntes):
    1. ¿Con qué módulo mides cuánto tarda una función?
    2. ¿Por qué `x in conjunto` es más rápido que `x in lista`?
    3. ¿Qué hace df.apply(funcion, axis=1)?
"""

import timeit
from pathlib import Path

import numpy as np
import pandas as pd

DATOS = Path(__file__).resolve().parents[2] / "datos"
df = pd.concat([pd.read_csv(DATOS / "movimientos.csv")] * 50, ignore_index=True)  # 20,000 filas

# ════════════════════════════════════════════════════════════════════
# PASO 1 — Fila a fila contra columna entera
# ════════════════════════════════════════════════════════════════════
# APRENDERÁS: por qué en pandas casi nunca se escribe un bucle.
# CONCEPTO: una operación sobre la columna entera («vectorizada») se ejecuta en C.
# Un bucle o un apply ejecuta Python fila por fila. De más lenta a más rápida:
#     iloc en bucle  <  iterrows  <  itertuples  <  apply  <  vectorizado


def con_apply():
    return df.apply(lambda fila: fila["monto"] * 0.015 if fila["tipo"] == "compra" else 0.0, axis=1)


def vectorizado():
    return np.where(df["tipo"] == "compra", df["monto"] * 0.015, 0.0)


t_apply = timeit.timeit(con_apply, number=1)
t_vector = timeit.timeit(vectorizado, number=1)
print("[paso 1] mismo resultado:", np.allclose(con_apply(), vectorizado()),
      "| vectorizado al menos 20 veces más rápido:", t_apply > 20 * t_vector)
# SALIDA ESPERADA:
#   [paso 1] mismo resultado: True | vectorizado al menos 20 veces más rápido: True

# 👉 TU TURNO 1: añade las versiones con iterrows y con itertuples. Mide las
#    cuatro, imprime los segundos y ordénalas.


# REFLEXIONA: si la vectorización es tan rápida, ¿en qué caso real seguirías
# usando apply?

# ════════════════════════════════════════════════════════════════════
# PASO 2 — Condiciones sin if
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: un if por fila se convierte en una operación por columna:
#     np.where(condición, si, no)                  dos casos
#     np.select([c1, c2], [v1, v2], default=v3)    varios casos
#     pd.cut(columna, bins, labels)                rangos numéricos

nivel = pd.cut(df["monto"], bins=[0, 500, 5000, np.inf], labels=["bajo", "medio", "alto"], right=False)
print("[paso 2]", nivel.value_counts().sort_index().to_dict())
# SALIDA ESPERADA:
#   [paso 2] {'bajo': 8500, 'medio': 8650, 'alto': 2850}

# 👉 TU TURNO 2: obtén la misma clasificación con np.select y comprueba con un
#    assert que coincide con pd.cut. ¿Cuál se lee mejor?


# ════════════════════════════════════════════════════════════════════
# PASO 3 — Cálculos por grupo sin bucles
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: groupby().agg() devuelve UNA fila por grupo. groupby().transform()
# devuelve una fila por FILA ORIGINAL, con el valor de su grupo: sirve para
# comparar cada fila con su grupo.

media_cuenta = df.groupby("cuenta_id")["monto"].transform("mean")
df["desviacion"] = df["monto"] - media_cuenta
print("[paso 3]", len(media_cuenta) == len(df), "| suma de desviaciones ~ 0:", abs(df["desviacion"].sum()) < 1e-3)
# SALIDA ESPERADA:
#   [paso 3] True | suma de desviaciones ~ 0: True

# 👉 TU TURNO 3: marca como «atípico» cada movimiento que supere en 3 veces la
#    mediana de su categoría. ¿Cuántos hay?


# REFLEXIONA: ¿por qué la suma de las desviaciones respecto a la media da cero?

# ════════════════════════════════════════════════════════════════════
# PASO 4 — Memoria
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: el texto repetido es lo que más ocupa. Como «category», pandas guarda
# cada valor distinto una sola vez y un número pequeño por fila.

antes = df["tipo"].memory_usage(deep=True)
despues = df["tipo"].astype("category").memory_usage(deep=True)
print("[paso 4] category ocupa al menos 5 veces menos:", antes > 5 * despues)
# SALIDA ESPERADA:
#   [paso 4] category ocupa al menos 5 veces menos: True

# 👉 TU TURNO 4: mide df.memory_usage(deep=True).sum() antes y después de convertir
#    a category todas las columnas de texto repetido y de reducir los enteros con
#    pd.to_numeric(..., downcast="integer"). ¿Qué porcentaje ahorraste?


# REFLEXIONA: ¿convertirías a category una columna con un valor distinto por fila
# (por ejemplo, el id)? ¿Qué pasaría con la memoria?

# ════════════════════════════════════════════════════════════════════
# RETO DE LA LECCIÓN (pasos 1 a 4)
# ════════════════════════════════════════════════════════════════════
# Elige una regla de limpieza de las lecciones 1 o 2 que hayas escrito con apply o
# con un bucle. Reescríbela vectorizada, demuestra con un assert que el resultado
# es idéntico y anota cuántas veces más rápida es.
