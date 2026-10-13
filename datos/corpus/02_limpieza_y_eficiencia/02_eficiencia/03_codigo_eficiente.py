"""
Tema 7 — Limpieza y eficiencia | Lección 3: Código Python eficiente
=====================================================================

TIEMPO: 2 h · ANTES DE EMPEZAR: 01_fundamentos y 01_core_python/03_python_avanzado/03_comprension_listas.py

CÓMO USAR ESTA LECCIÓN: predice, ejecuta, compara con la salida esperada, tu turno.
    python 05_ingenieria_de_datos/02_limpieza_y_eficiencia/02_eficiencia/03_codigo_eficiente.py

    Los tiempos cambian de una máquina a otra: los ejemplos imprimen COMPARACIONES
    (¿es más rápido?), no segundos. Tú sí debes mirar los números.

CALENTAMIENTO (sin mirar apuntes):
    1. ¿Qué diferencia hay entre [x for x in datos] y (x for x in datos)?
    2. ¿Qué estructura usarías para saber si un id ya lo viste: lista o set? ¿Por qué?
    3. ¿Qué devuelve enumerate(["a", "b"])?
"""

import csv
import sys
import timeit
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

DATOS = Path(__file__).resolve().parents[2] / "datos"

# ════════════════════════════════════════════════════════════════════
# PASO 1 — Medir antes de optimizar
# ════════════════════════════════════════════════════════════════════
# APRENDERÁS: a sustituir «creo que es lento» por un número.
# CONCEPTO: timeit ejecuta una función muchas veces y devuelve el tiempo total.
# Sin medir, optimizas lo que no importa.

numeros = list(range(200_000))


def con_bucle():
    total = 0
    for n in numeros:
        total += n * n
    return total


def con_sum():
    return sum(n * n for n in numeros)


t_bucle = timeit.timeit(con_bucle, number=5)
t_sum = timeit.timeit(con_sum, number=5)
print("[paso 1] mismo resultado:", con_bucle() == con_sum(), "| tiempos medidos:", t_bucle > 0 and t_sum > 0)
# SALIDA ESPERADA:
#   [paso 1] mismo resultado: True | tiempos medidos: True

# 👉 TU TURNO 1: imprime t_bucle y t_sum. Añade una tercera versión con una
#    comprensión de LISTA dentro de sum y mídela. Ordena las tres.


# REFLEXIONA: ¿la diferencia es grande o pequeña? ¿Merecería la pena reescribir
# código por ella?

# ════════════════════════════════════════════════════════════════════
# PASO 2 — La estructura de datos correcta
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: `x in lista` recorre la lista entera (O(n)). `x in conjunto` va
# directo (O(1)). Con datos grandes, esto sí cambia todo: no es un 20 % más
# rápido, son órdenes de magnitud.

ids_lista = list(range(20_000))
ids_set = set(ids_lista)
buscados = range(19_000, 20_000)

t_lista = timeit.timeit(lambda: [x in ids_lista for x in buscados], number=1)
t_set = timeit.timeit(lambda: [x in ids_set for x in buscados], number=1)
print("[paso 2] el set es al menos 50 veces más rápido:", t_lista > 50 * t_set)
# SALIDA ESPERADA:
#   [paso 2] el set es al menos 50 veces más rápido: True

# 👉 TU TURNO 2: imprime cuántas veces más rápido es en tu máquina. Repítelo con
#    200,000 ids: ¿la diferencia crece, se mantiene o baja? ¿Por qué?


# ════════════════════════════════════════════════════════════════════
# PASO 3 — Herramientas que evitan bucles a mano
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: la biblioteca estándar ya resolvió lo más común.
#     Counter              contar           defaultdict(list)   agrupar
#     combinations(x, 2)   todos los pares  zip / enumerate     recorrer en paralelo
#     a & b, a | b, a - b  operaciones de conjuntos

with open(DATOS / "movimientos.csv", encoding="utf-8") as f:
    movimientos = list(csv.DictReader(f))

por_tipo = Counter(m["tipo"] for m in movimientos)
cuentas_por_tipo = defaultdict(set)
for m in movimientos:
    cuentas_por_tipo[m["tipo"]].add(m["cuenta_id"])
solo_compran = cuentas_por_tipo["compra"] - cuentas_por_tipo["deposito"]
print("[paso 3]", por_tipo.most_common(2), "| cuentas con compras y sin depósitos:", len(solo_compran),
      "| pares de categorías:", len(list(combinations(["a", "b", "c", "d", "e", "f"], 2))))
# SALIDA ESPERADA:
#   [paso 3] [('compra', 247), ('deposito', 81)] | cuentas con compras y sin depósitos: 0 | pares de categorías: 15

# 👉 TU TURNO 3: sin bucles anidados ni contadores manuales:
#    a) el comercio más frecuente de CADA categoría;
#    b) las cuentas que tienen retiros pero ninguna transferencia.


# ════════════════════════════════════════════════════════════════════
# PASO 4 — Generadores: memoria constante
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: una lista guarda todos sus elementos. Un generador produce uno cada
# vez que se le pide y lo olvida. Con `yield`, una función se vuelve generador:
# así se procesa un archivo de 50 GB con 100 MB de memoria.

lista = [n * 2 for n in range(100_000)]
generador = (n * 2 for n in range(100_000))
print("[paso 4] misma suma:", sum(lista) == sum(generador),
      "| el generador ocupa 1000 veces menos:", sys.getsizeof(lista) > 1000 * sys.getsizeof(generador))
# SALIDA ESPERADA:
#   [paso 4] misma suma: True | el generador ocupa 1000 veces menos: True

# 👉 TU TURNO 4: escribe leer_movimientos(ruta) con yield, que entregue un dict
#    por fila con `monto` ya como float. Úsalo para sumar las compras en una
#    sola pasada, sin crear ninguna lista.


# COMPRUEBA: recorre tu generador dos veces seguidas. ¿Qué devuelve la segunda?
# REFLEXIONA: el generador ahorra memoria. ¿Qué pierdes a cambio?

# ════════════════════════════════════════════════════════════════════
# PASO 5 — Encontrar el cuello de botella
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: cuando algo va lento, no adivines: perfila.
#     python -m cProfile -s cumtime mi_script.py
# te dice en qué función se va el tiempo.


def lenta(n=3000):
    """Devuelve los números de 0 a n-1 que no son múltiplos de 7."""
    descartados = [x for x in range(n) if x % 7 == 0]
    resultado = []
    for x in range(n):
        if x not in descartados:
            resultado = resultado + [x]
    return resultado


print("[paso 5]", len(lenta()))
# SALIDA ESPERADA:
#   [paso 5] 2571

# 👉 TU TURNO 5: lenta() tiene DOS problemas de eficiencia. Mídela, localízalos
#    (pista: pasos 2 y 4) y escribe rapida().


# COMPRUEBA: rapida() == lenta() y es al menos 50 veces más rápida.

# ════════════════════════════════════════════════════════════════════
# RETO DE LA LECCIÓN (pasos 1 a 5)
# ════════════════════════════════════════════════════════════════════
# Escribe top_n_por_grupo(filas, clave_grupo, clave_valor, n) que reciba un
# ITERABLE de dicts (puede ser tu generador del paso 4) y devuelva, por grupo, los
# n valores más altos, recorriendo los datos una sola vez y sin guardar todas las
# filas. Busca el módulo heapq.
# COMPRUEBA: con n=1 y agrupando por cuenta_id, coincide con la compra más grande
# de cada cuenta calculada con pandas.
