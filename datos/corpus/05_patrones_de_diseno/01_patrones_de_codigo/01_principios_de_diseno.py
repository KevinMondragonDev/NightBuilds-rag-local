"""
Tema 10 — Patrones de diseño | Lección 1: Principios antes que patrones
=========================================================================

CÓMO USAR ESTA LECCIÓN:
    Va por PASOS pequeños. En cada uno: lee el concepto, PREDICE qué imprimirá el
    ejemplo, ejecuta el archivo y compara con la salida esperada, y después haz
    «TU TURNO» justo debajo. No pases al siguiente paso sin comprobar.

        python 05_ingenieria_de_datos/05_patrones_de_diseno/01_patrones_de_codigo/01_principios_de_diseno.py

    Un patrón es una solución con nombre a un problema que se repite. Antes de los
    patrones van los principios: casi todos los patrones son formas de aplicarlos.

TIEMPO: 2 h · ANTES DE EMPEZAR: 01_core_python/02_organizacion_y_poo (POO) y tus retos 8, 11 y 12

CALENTAMIENTO (sin mirar apuntes, responde en un comentario antes de empezar):
    1. ¿Qué es una clase abstracta y para qué sirve?
    2. ¿Qué hace un decorador con la función que envuelve?
    3. En tus retos 11 y 12, ¿qué código repetiste casi igual?
"""

from dataclasses import dataclass
from typing import Callable, Protocol

FILAS = [
    {"id": 1, "monto": "120.50", "tipo": "compra"},
    {"id": 2, "monto": "-30", "tipo": "compra"},
    {"id": 3, "monto": "900", "tipo": "deposito"},
]

# ════════════════════════════════════════════════════════════════════
# PASO 1 — Una responsabilidad por función
# ════════════════════════════════════════════════════════════════════
# APRENDERÁS: a reconocer una función que hace demasiado.
# CONCEPTO: si para describir una función necesitas la palabra «y», hace más de
# una cosa. Será difícil de probar, de reutilizar y de cambiar.


def procesar_todo(filas):
    """✗ Convierte Y filtra Y suma Y muestra."""
    total = 0
    for fila in filas:
        monto = float(fila["monto"])
        if monto > 0 and fila["tipo"] == "compra":
            total += monto
    print(f"[paso 1] total compras (todo junto): {total}")


def convertir(filas):
    return [{**fila, "monto": float(fila["monto"])} for fila in filas]


def solo_compras_validas(filas):
    return [fila for fila in filas if fila["monto"] > 0 and fila["tipo"] == "compra"]


def total(filas):
    return sum(fila["monto"] for fila in filas)


procesar_todo(FILAS)
print("[paso 1] total compras (separado): ", total(solo_compras_validas(convertir(FILAS))))
# SALIDA ESPERADA:
#   [paso 1] total compras (todo junto): 120.5
#   [paso 1] total compras (separado):  120.5

# 👉 TU TURNO 1: ahora te piden el total de DEPÓSITOS. ¿Cuántas líneas tocarías en
#    procesar_todo? ¿Y en la versión separada? Escríbelo con la versión separada.


# COMPRUEBA: el total de depósitos es 900.0
# REFLEXIONA: ¿cuál de las cuatro funciones puedes probar sin capturar un print?


# ════════════════════════════════════════════════════════════════════
# PASO 2 — Depender de un contrato, no de una clase concreta
# ════════════════════════════════════════════════════════════════════
# APRENDERÁS: a definir «qué necesito» sin decir «quién me lo da».
# CONCEPTO: un Protocol describe los métodos que debe tener un objeto. Cualquier
# clase que los tenga sirve, sin heredar de nada (como una interface de Java,
# pero sin `implements`).


class Fuente(Protocol):
    def leer(self) -> list[dict]: ...


class FuenteMemoria:
    def __init__(self, filas):
        self._filas = filas

    def leer(self) -> list[dict]:
        return self._filas


class FuenteFalsaVacia:
    def leer(self) -> list[dict]:
        return []


def contar(fuente: Fuente) -> int:
    return len(fuente.leer())


print("[paso 2]", contar(FuenteMemoria(FILAS)), contar(FuenteFalsaVacia()))
# SALIDA ESPERADA:
#   [paso 2] 3 0

# 👉 TU TURNO 2: escribe FuenteCSV(ruta) que cumpla el mismo contrato leyendo
#    05_ingenieria_de_datos/datos/movimientos.csv con csv.DictReader.
#    contar() debe funcionar SIN modificarla.


# COMPRUEBA: contar(FuenteCSV(ruta)) == 400
# REFLEXIONA: ¿qué tendrías que cambiar en contar() para leer de PostgreSQL?


# ════════════════════════════════════════════════════════════════════
# PASO 3 — Inyección de dependencias
# ════════════════════════════════════════════════════════════════════
# APRENDERÁS: por qué las dependencias se RECIBEN y no se crean dentro.
# CONCEPTO: si una función crea su propia conexión, no puedes probarla sin esa
# conexión. Si la recibe como parámetro, en los tests le pasas una falsa.
# Si conoces Java/Spring: es lo que hace @Autowired. En Python basta con un parámetro.


def reporte_acoplado():
    """✗ Crea su dependencia: imposible de probar sin el archivo real."""
    fuente = FuenteMemoria(FILAS)  # imagina aquí psycopg.connect(...)
    return total(solo_compras_validas(convertir(fuente.leer())))


def reporte(fuente: Fuente) -> float:
    """✓ Recibe su dependencia."""
    return total(solo_compras_validas(convertir(fuente.leer())))


print("[paso 3]", reporte(FuenteMemoria(FILAS)), reporte(FuenteFalsaVacia()))
# SALIDA ESPERADA:
#   [paso 3] 120.5 0

# 👉 TU TURNO 3: escribe una función de test (sin pytest, con assert) que
#    compruebe reporte() con una fuente falsa de 2 filas inventadas por ti.


# REFLEXIONA: ¿quién decide ahora qué fuente se usa? ¿Dónde vive esa decisión?


# ════════════════════════════════════════════════════════════════════
# PASO 4 — Composición antes que herencia
# ════════════════════════════════════════════════════════════════════
# APRENDERÁS: a combinar piezas en lugar de heredar.
# CONCEPTO: herencia = «es un». Composición = «tiene un». Con herencia, cada
# combinación nueva es una clase nueva (PipelineCSVConLog, PipelineCSVConLogYReintento...).
# Con composición, combinas objetos.


@dataclass
class Pipeline:
    fuente: Fuente
    transformaciones: list[Callable[[list[dict]], list[dict]]]

    def ejecutar(self) -> list[dict]:
        filas = self.fuente.leer()
        for transformar in self.transformaciones:
            filas = transformar(filas)
        return filas


pipeline = Pipeline(FuenteMemoria(FILAS), [convertir, solo_compras_validas])
print("[paso 4]", pipeline.ejecutar())
# SALIDA ESPERADA:
#   [paso 4] [{'id': 1, 'monto': 120.5, 'tipo': 'compra'}]

# 👉 TU TURNO 4: crea un segundo Pipeline que devuelva solo los depósitos, SIN
#    crear ninguna clase nueva. Necesitas una transformación más.


# REFLEXIONA: ¿cuántas clases harían falta con herencia para 3 fuentes × 4
# combinaciones de transformaciones?


# ════════════════════════════════════════════════════════════════════
# PASO 5 — Abierto a extensión, cerrado a modificación
# ════════════════════════════════════════════════════════════════════
# APRENDERÁS: a añadir comportamiento sin tocar el código que ya funciona.
# CONCEPTO: una cadena de if/elif crece con cada caso nuevo y obliga a editar la
# función. Un REGISTRO (diccionario nombre -> función) se amplía desde fuera.

REGLAS: dict[str, Callable[[dict], bool]] = {}


def regla(nombre):
    def registrar(funcion):
        REGLAS[nombre] = funcion
        return funcion
    return registrar


@regla("monto_positivo")
def _(fila):
    return float(fila["monto"]) > 0


@regla("tipo_valido")
def _(fila):
    return fila["tipo"] in {"compra", "deposito", "retiro", "transferencia"}


def validar(fila):
    return [nombre for nombre, cumple in REGLAS.items() if not cumple(fila)]


print("[paso 5]", [validar(fila) for fila in FILAS])
# SALIDA ESPERADA:
#   [paso 5] [[], ['monto_positivo'], []]

# 👉 TU TURNO 5: añade la regla "id_presente" SIN modificar validar().


# COMPRUEBA: validar({"monto": "5", "tipo": "compra"}) devuelve ['id_presente']
# REFLEXIONA: el decorador @regla es el patrón Registry. ¿En qué se parece al
# Factory de 01_core_python/02_organizacion_y_poo/05_poo_patrones_diseno.py?


# ════════════════════════════════════════════════════════════════════
# RETO DE LA LECCIÓN (usa los pasos 1 a 5)
# ════════════════════════════════════════════════════════════════════
# El archivo 04_retos_de_python/reto_08_refactorizacion.py te da código malo.
# Vuelve a él y refactorízalo aplicando, con nombre, al menos tres de estos
# principios. Deja un comentario encima de cada cambio diciendo cuál aplicaste.
