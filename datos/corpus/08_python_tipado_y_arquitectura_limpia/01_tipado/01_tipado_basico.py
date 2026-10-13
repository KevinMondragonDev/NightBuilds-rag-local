"""
Tema 13 — Python tipado y arquitectura limpia | Lección 1: Anotaciones de tipo y mypy
=======================================================================================

TIEMPO: 2 h · ANTES DE EMPEZAR: 03_ingenieria_de_software/02_paquetes_y_pruebas/03_paquetes_y_estilo.md (type hints y docstrings)

CÓMO USAR ESTA LECCIÓN: predice, ejecuta, compara con la salida esperada, tu turno.
    python 05_ingenieria_de_datos/08_python_tipado_y_arquitectura_limpia/01_tipado/01_tipado_basico.py
    mypy   05_ingenieria_de_datos/08_python_tipado_y_arquitectura_limpia/01_tipado/01_tipado_basico.py

    pip install mypy

CALENTAMIENTO (sin mirar apuntes):
    1. ¿Qué dos cosas dice un type hint en la firma de una función?
    2. ¿Qué hace frozen=True en un dataclass?
    3. En Pydantic, ¿qué pasa si llega un texto donde se espera un número?
"""

from dataclasses import dataclass
from typing import Literal

# ════════════════════════════════════════════════════════════════════
# PASO 1 — Python no comprueba los tipos al ejecutar
# ════════════════════════════════════════════════════════════════════
# APRENDERÁS: qué son y qué NO son las anotaciones de tipo.
# CONCEPTO: una anotación es una PROMESA escrita, no una comprobación. Python la
# ignora al ejecutar. Quien la comprueba es una herramienta aparte (mypy), antes
# de ejecutar, sobre todo el código y sin necesidad de un test.


def aplicar_iva(monto: float) -> float:
    return monto * 1.16


print("[paso 1]", round(aplicar_iva(100), 2), "|", "100" * 2)
# SALIDA ESPERADA:
#   [paso 1] 116.0 | 100100

# 👉 TU TURNO 1: descomenta la línea de abajo y ejecuta el archivo. ¿Qué error da
#    Python y en qué momento? Ahora ejecuta mypy sobre el archivo: ¿qué dice y
#    cuándo te habrías enterado con cada herramienta?
# aplicar_iva("100")

# COMPRUEBA: mypy dice
#   error: Argument 1 to "aplicar_iva" has incompatible type "str"; expected "float"  [arg-type]
# REFLEXIONA: ese error estaba en una rama del código que tus tests no ejecutan.
# ¿Quién lo habría encontrado antes: un test o mypy?

# ════════════════════════════════════════════════════════════════════
# PASO 2 — Colecciones
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: no basta con decir «lista»: se dice lista DE QUÉ.
#     list[str]   dict[str, float]   set[int]   tuple[str, int]   tuple[float, ...]


def total_por_categoria(compras: list[tuple[str, float]]) -> dict[str, float]:
    totales: dict[str, float] = {}
    for categoria, monto in compras:
        totales[categoria] = totales.get(categoria, 0.0) + monto
    return totales


print("[paso 2]", total_por_categoria([("viajes", 100.0), ("viajes", 50.0), ("gasolina", 30.0)]))
# SALIDA ESPERADA:
#   [paso 2] {'viajes': 150.0, 'gasolina': 30.0}

# 👉 TU TURNO 2: escribe categoria_principal(totales) que devuelva el nombre de la
#    categoría con más gasto. Anótala completa y comprueba con mypy que no hay errores.


# ════════════════════════════════════════════════════════════════════
# PASO 3 — «Puede no haber valor»: X | None
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: el error más común de Python es usar None como si fuera un valor.
# Si una función PUEDE devolver None, se declara, y mypy te obliga a tratar ese
# caso antes de usar el resultado.

SALDOS = {1: 500.0, 2: -20.0}


def buscar_saldo(cuenta_id: int) -> float | None:
    return SALDOS.get(cuenta_id)


def describir(cuenta_id: int) -> str:
    saldo = buscar_saldo(cuenta_id)
    if saldo is None:  # sin esta comprobación, mypy rechaza la línea siguiente
        return "cuenta inexistente"
    return f"saldo {saldo:.2f}"


print("[paso 3]", describir(1), "|", describir(99))
# SALIDA ESPERADA:
#   [paso 3] saldo 500.00 | cuenta inexistente

# 👉 TU TURNO 3: borra el `if saldo is None` (deja solo el return final) y pasa
#    mypy. Lee el error con calma: ¿qué te está avisando exactamente?


# REFLEXIONA: ¿en qué se parece `float | None` al Optional<Double> de Java?

# ════════════════════════════════════════════════════════════════════
# PASO 4 — Valores de un conjunto cerrado: Literal
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: `str` acepta cualquier texto. Si solo valen cuatro, dilo: una errata
# («conpra») deja de ser un fallo en producción y pasa a ser un error de mypy.

TipoMovimiento = Literal["compra", "deposito", "retiro", "transferencia"]


def signo(tipo: TipoMovimiento) -> int:
    return 1 if tipo == "deposito" else -1


print("[paso 4]", signo("deposito"), signo("compra"))
# SALIDA ESPERADA:
#   [paso 4] 1 -1

# 👉 TU TURNO 4: llama a signo("conpra") y pasa mypy. Después define
#    Segmento = Literal[...] y úsalo en una función.


# ════════════════════════════════════════════════════════════════════
# PASO 5 — Registros con forma: dataclass en lugar de dict
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: un dict[str, object] no dice qué claves tiene ni de qué tipo son.
# Un dataclass sí: el editor autocompleta, mypy detecta una clave mal escrita y,
# con frozen=True, nadie lo modifica por accidente.


@dataclass(frozen=True)
class Movimiento:
    id: int
    tipo: TipoMovimiento
    monto: float
    categoria: str | None = None


def gasto(movimientos: list[Movimiento]) -> float:
    return sum(m.monto for m in movimientos if m.tipo == "compra")


print("[paso 5]", gasto([Movimiento(1, "compra", 250.0, "viajes"), Movimiento(2, "deposito", 1000.0)]))
# SALIDA ESPERADA:
#   [paso 5] 250.0

# 👉 TU TURNO 5: escribe desde_fila(fila: dict[str, str]) -> Movimiento, que
#    convierta una fila de csv.DictReader. ¿Qué te obliga mypy a decidir sobre la
#    conversión de «monto» y sobre una categoría vacía?


# REFLEXIONA: ¿qué diferencia hay entre este dataclass y un modelo de Pydantic
# (06_apis_con_fastapi/01_construir/02)? ¿Cuál VALIDA al ejecutar y cuál solo DECLARA?

# ════════════════════════════════════════════════════════════════════
# RETO DE LA LECCIÓN (pasos 1 a 5)
# ════════════════════════════════════════════════════════════════════
# Toma un archivo tuyo sin anotar (por ejemplo, tu solución de reto_11_mini_etl.py)
# y anótalo entero hasta que `mypy --strict tu_archivo.py` no dé ningún error.
# COMPRUEBA: anota cuántos errores dio la primera pasada y cuántos de ellos eran
# fallos reales que no habías visto (un None sin tratar, un tipo equivocado).
