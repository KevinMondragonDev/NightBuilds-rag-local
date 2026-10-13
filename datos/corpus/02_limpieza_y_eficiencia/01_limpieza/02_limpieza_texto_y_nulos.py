"""
Tema 7 — Limpieza y eficiencia | Lección 2: Texto, categorías y nulos
=======================================================================

TIEMPO: 2 h · ANTES DE EMPEZAR: lección 1 de esta sección

CÓMO USAR ESTA LECCIÓN: predice, ejecuta, compara con la salida esperada, tu turno.
    python 05_ingenieria_de_datos/02_limpieza_y_eficiencia/01_limpieza/02_limpieza_texto_y_nulos.py

    Ejemplos sobre MUESTRA (pequeña e inventada); «TU TURNO» sobre el archivo real.

CALENTAMIENTO (sin mirar apuntes):
    1. ¿Por qué se lee un archivo sucio con dtype=str?
    2. Dos filas con el mismo id y distinto monto: ¿por qué no basta drop_duplicates?
    3. ¿Qué tres cosas puedes hacer con un valor fuera de rango?
"""

import difflib
from pathlib import Path

import pandas as pd

DATOS = Path(__file__).resolve().parents[2] / "datos"
TIPOS_VALIDOS = {"compra", "deposito", "retiro", "transferencia"}
CATEGORIAS_VALIDAS = {"supermercado", "restaurantes", "servicios", "entretenimiento", "viajes", "gasolina"}

MUESTRA = pd.DataFrame({
    "tipo":      ["compra", "COMPRA", "Compra ", "depósito", "deposito", "compra", "compra"],
    "comercio":  ["Walmart", "Walmart", "Toks", None, None, "Netflix", "Toks"],
    "categoria": ["supermercado", " Supermercado ", "restaurante", None, None, "entretenimento", None],
    "monto":     [200.0, 350.0, None, 1000.0, 500.0, 199.0, 420.0],
})

# ════════════════════════════════════════════════════════════════════
# PASO 1 — Categorías: un conjunto cerrado de valores
# ════════════════════════════════════════════════════════════════════
# APRENDERÁS: a detectar y unificar variantes del mismo valor.
# CONCEPTO: una columna categórica solo puede tomar ciertos valores. Todo lo que
# se salga es sospechoso. Primero normalizas lo mecánico (espacios, mayúsculas,
# acentos) y solo después miras qué queda fuera.

print("[paso 1] antes:", sorted(MUESTRA["tipo"].unique()))
tipo = (MUESTRA["tipo"].str.strip().str.lower()
        .str.normalize("NFKD").str.encode("ascii", "ignore").str.decode("ascii"))  # quita acentos
print("[paso 1] después:", sorted(tipo.unique()), "| fuera del conjunto:", int((~tipo.isin(TIPOS_VALIDOS)).sum()))
# SALIDA ESPERADA:
#   [paso 1] antes: ['COMPRA', 'Compra ', 'compra', 'deposito', 'depósito']
#   [paso 1] después: ['compra', 'deposito'] | fuera del conjunto: 0

# 👉 TU TURNO 1: en el archivo real, lista los valores distintos de `tipo` con su
#    conteo (value_counts con dropna=False) y normalízalos.


# COMPRUEBA con assert: solo quedan los 4 tipos válidos.

# ════════════════════════════════════════════════════════════════════
# PASO 2 — Lo que la normalización mecánica no arregla
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: «restaurante» y «entretenimento» no se arreglan con strip ni lower.
# Dos herramientas: un diccionario de equivalencias (preciso, hay que mantenerlo)
# y la coincidencia aproximada (automática, puede equivocarse).

categoria = MUESTRA["categoria"].str.strip().str.lower()
aproximada = categoria.map(
    lambda valor: (difflib.get_close_matches(valor, CATEGORIAS_VALIDAS, n=1, cutoff=0.8) or [None])[0]
    if isinstance(valor, str) else valor)
print("[paso 2]", aproximada.dropna().tolist(), "| sin categoría:", int(aproximada.isna().sum()))
# SALIDA ESPERADA:
#   [paso 2] ['supermercado', 'supermercado', 'restaurantes', 'entretenimiento'] | sin categoría: 3

# 👉 TU TURNO 2: en el archivo real, normaliza `categoria`. Hay una variante que la
#    coincidencia aproximada con cutoff=0.8 NO resuelve. Encuéntrala, explica por
#    qué se le escapa y arréglala con un diccionario de equivalencias.


# COMPRUEBA con assert: ignorando nulos, solo quedan las 6 categorías válidas.
# REFLEXIONA: ¿qué riesgo tiene bajar el cutoff a 0.5 para «arreglarlo todo»?

# ════════════════════════════════════════════════════════════════════
# PASO 3 — Validar entre columnas
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: una fila puede ser válida columna a columna y aun así imposible:
# una compra sin categoría, un depósito con comercio. Además, a veces una columna
# permite RECUPERAR otra: si sé el comercio, sé la categoría.

limpia = MUESTRA.assign(tipo=tipo, categoria=aproximada)
sin_categoria = (limpia["tipo"] == "compra") & limpia["categoria"].isna()
por_comercio = limpia.dropna(subset=["categoria"]).groupby("comercio")["categoria"].first()
limpia["categoria"] = limpia["categoria"].fillna(limpia["comercio"].map(por_comercio))
print("[paso 3] compras sin categoría:", int(sin_categoria.sum()),
      "| tras deducirla del comercio:", int(((limpia["tipo"] == "compra") & limpia["categoria"].isna()).sum()))
# SALIDA ESPERADA:
#   [paso 3] compras sin categoría: 1 | tras deducirla del comercio: 0

# 👉 TU TURNO 3: en el archivo real:
#    a) ¿cuántas compras no tienen categoría?
#    b) ¿hay depósitos, retiros o transferencias CON comercio o categoría?
#    c) deduce la categoría a partir del comercio y cuenta cuántas quedan sin resolver.


# REFLEXIONA: ¿qué supuesto haces al deducir la categoría del comercio? Piensa en
# Walmart: ¿siempre es «supermercado»?

# ════════════════════════════════════════════════════════════════════
# PASO 4 — Nulos: primero entender por qué faltan
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: descartar o rellenar cambia el resultado. Antes de elegir, pregunta
# si faltan AL AZAR o si faltan más en algún grupo. Imputar hace que los datos
# «se vean» completos, pero inventa valores.

total_descartando = limpia.dropna(subset=["monto"])["monto"].sum()
mediana_compras = limpia.loc[limpia["tipo"] == "compra", "monto"].median()
total_imputando = limpia["monto"].fillna(mediana_compras).sum()
print("[paso 4] descartando:", total_descartando, "| imputando la mediana:", total_imputando)
# SALIDA ESPERADA:
#   [paso 4] descartando: 2669.0 | imputando la mediana: 2944.0

# 👉 TU TURNO 4: en el archivo real:
#    a) ¿cuántos montos faltan? ¿Faltan más en algún tipo o cuenta, o es al azar?
#    b) compara el gasto total por categoría descartando esas filas e imputando la
#       mediana del comercio. ¿Cuánto cambia, en porcentaje?


# REFLEXIONA: ¿en qué análisis sería peligroso imputar y preferirías dejar el nulo?

# ════════════════════════════════════════════════════════════════════
# RETO DE LA LECCIÓN (pasos 1 a 4)
# ════════════════════════════════════════════════════════════════════
# Escribe normalizar_categoria(serie, validas, equivalencias=None) que aplique, en
# este orden: strip, minúsculas, quitar acentos, equivalencias y coincidencia
# aproximada. Lo que siga sin ser válido queda como nulo. Devuelve también
# cuántos valores corrigió cada paso.
# COMPRUEBA: sobre MUESTRA["categoria"] devuelve 4 valores válidos y 3 nulos.
