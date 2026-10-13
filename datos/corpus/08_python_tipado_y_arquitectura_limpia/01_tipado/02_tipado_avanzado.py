"""
Tema 13 — Python tipado y arquitectura limpia | Lección 2: Tipos que expresan el diseño
=========================================================================================

TIEMPO: 2 h · ANTES DE EMPEZAR: lección 1 y 05_patrones_de_diseno/01_patrones_de_codigo/01_principios_de_diseno.py

CÓMO USAR ESTA LECCIÓN: predice, ejecuta, compara con la salida esperada, tu turno.
    python 02_tipado_avanzado.py     y después     mypy --strict 02_tipado_avanzado.py

CALENTAMIENTO (sin mirar apuntes):
    1. ¿Comprueba Python los tipos al ejecutar? ¿Quién lo hace?
    2. ¿Qué te obliga a hacer mypy con un valor de tipo `float | None`?
    3. ¿Para qué sirve Literal?
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, NewType, Protocol, TypedDict, TypeVar

# ════════════════════════════════════════════════════════════════════
# PASO 1 — NewType: dos enteros que no deben mezclarse
# ════════════════════════════════════════════════════════════════════
# APRENDERÁS: a usar los tipos para impedir errores de negocio.
# CONCEPTO: un id de cliente y un id de cuenta son `int`, pero pasar uno donde va
# el otro es un error que ningún test trivial detecta. NewType crea un tipo
# distinto para mypy, sin costo al ejecutar.

ClienteId = NewType("ClienteId", int)
CuentaId = NewType("CuentaId", int)


def titular(cuenta: CuentaId) -> str:
    return f"titular de la cuenta {cuenta}"


cliente, cuenta = ClienteId(7), CuentaId(7)
print("[paso 1]", titular(cuenta), "|", int(cliente) == int(cuenta))
# SALIDA ESPERADA:
#   [paso 1] titular de la cuenta 7 | True

# 👉 TU TURNO 1: llama a titular(cliente) y pasa mypy. Al ejecutar funciona (los
#    dos valen 7): por eso mismo es un error peligroso.


# ════════════════════════════════════════════════════════════════════
# PASO 2 — TypedDict: la forma de un JSON
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: los datos que llegan de fuera (una API, un archivo) son diccionarios.
# TypedDict describe sus claves y tipos sin convertirlos en objetos.


class RespuestaCambio(TypedDict):
    base: str
    date: str
    rates: dict[str, float]


def mxn(respuesta: RespuestaCambio) -> float:
    return respuesta["rates"]["MXN"]


print("[paso 2]", mxn({"base": "USD", "date": "2026-07-01", "rates": {"MXN": 17.5341}}))
# SALIDA ESPERADA:
#   [paso 2] 17.5341

# 👉 TU TURNO 2: escribe respuesta["rate"] (sin la s) dentro de mxn y pasa mypy.
#    Después describe con TypedDict un evento de datos/eventos/generar_eventos.py.


# REFLEXIONA: TypedDict NO valida al ejecutar. Si la API cambia y `rates` deja de
# venir, ¿quién se entera? ¿Qué usarías en la frontera del sistema?

# ════════════════════════════════════════════════════════════════════
# PASO 3 — Protocol: el contrato de una dependencia
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: ya lo usaste en 05_patrones_de_diseno. Aquí lo importante es que mypy
# COMPRUEBA que cada implementación cumple el contrato, sin heredar de nada.


class RepositorioSaldos(Protocol):
    def obtener(self, cuenta: CuentaId) -> float | None: ...


class EnMemoria:
    def __init__(self, saldos: dict[CuentaId, float]) -> None:
        self._saldos = saldos

    def obtener(self, cuenta: CuentaId) -> float | None:
        return self._saldos.get(cuenta)


def puede_retirar(repo: RepositorioSaldos, cuenta: CuentaId, monto: float) -> bool:
    saldo = repo.obtener(cuenta)
    return saldo is not None and saldo >= monto


print("[paso 3]", puede_retirar(EnMemoria({CuentaId(1): 500.0}), CuentaId(1), 300.0))
# SALIDA ESPERADA:
#   [paso 3] True

# 👉 TU TURNO 3: cambia el nombre del método de EnMemoria a `get` y pasa mypy.
#    ¿En qué línea aparece el error: en la clase o donde se usa? ¿Por qué?


# ════════════════════════════════════════════════════════════════════
# PASO 4 — Genéricos: una misma pieza para varios tipos
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: un resultado «o valor o error» sirve igual para un float que para una
# lista. TypeVar deja el tipo abierto y mypy lo sigue: si entra un Resultado[float],
# lo que sale es un float.

T = TypeVar("T")


@dataclass(frozen=True)
class Resultado(Generic[T]):
    valor: T | None = None
    error: str | None = None

    @property
    def correcto(self) -> bool:
        return self.error is None


def convertir_monto(texto: str) -> Resultado[float]:
    try:
        return Resultado(valor=float(texto.replace("$", "").replace(",", "")))
    except ValueError:
        return Resultado(error=f"no es un monto: {texto!r}")


print("[paso 4]", convertir_monto("$1,200.50"), convertir_monto("diez").error)
# SALIDA ESPERADA:
#   [paso 4] Resultado(valor=1200.5, error=None) no es un monto: 'diez'

# 👉 TU TURNO 4: escribe primero(elementos: list[T]) -> T | None y úsala con una
#    lista de str y otra de Movimiento. Añade reveal_type(primero(["a"])) y pasa mypy.


# REFLEXIONA: ¿qué ventaja tiene devolver un Resultado frente a lanzar una
# excepción cuando limpias un millón de filas?

# ════════════════════════════════════════════════════════════════════
# PASO 5 — Funciones como valores: Callable
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: Callable[[tipos de entrada], tipo de salida] describe una función que
# se pasa como argumento. Es el tipo de los «pasos» de tus cadenas.

Regla = Callable[[float], bool]


def cumple_todas(monto: float, reglas: list[Regla]) -> bool:
    return all(regla(monto) for regla in reglas)


print("[paso 5]", cumple_todas(250.0, [lambda m: m > 0, lambda m: m < 100_000]))
# SALIDA ESPERADA:
#   [paso 5] True

# 👉 TU TURNO 5: añade a la lista una función que reciba un str. ¿Qué dice mypy?


# ════════════════════════════════════════════════════════════════════
# CONFIGURAR mypy EN UN PROYECTO (pyproject.toml)
# ════════════════════════════════════════════════════════════════════
#   [tool.mypy]
#   python_version = "3.10"
#   strict = true                 # todo anotado, sin Any implícitos
#   warn_unreachable = true
#
#   [[tool.mypy.overrides]]       # bibliotecas sin tipos: se silencian una a una
#   module = ["lark.*"]
#   ignore_missing_imports = true
#
# Empieza en strict en un proyecto nuevo. En uno existente, actívalo carpeta a carpeta.

# ════════════════════════════════════════════════════════════════════
# RETO DE LA LECCIÓN (pasos 1 a 5)
# ════════════════════════════════════════════════════════════════════
# Vuelve a tu DevSandbox-limpiador y déjalo en `mypy --strict` sin errores:
# NewType para los identificadores, TypedDict o dataclass para las filas, Protocol
# para lo que entra por parámetro y Resultado[T] en lugar de devolver None.
# COMPRUEBA: añade mypy a tu CI y rompe un tipo a propósito en una rama.
