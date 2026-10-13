"""
Tema 10 — Patrones de diseño | Lección 2: Patrones que aparecen en todo pipeline
==================================================================================

CÓMO USAR ESTA LECCIÓN: igual que la lección 1 (predice, ejecuta, compara, tu turno).

    Ya conoces Singleton, Factory, Strategy, Decorator y Observer
    (01_core_python/02_organizacion_y_poo/05_poo_patrones_diseno.py).
    Aquí van otros cinco y, sobre todo, CUÁNDO usar cada uno.

    Patrón            Problema que resuelve
    ----------------  ------------------------------------------------------------
    Template Method   Todos los pipelines siguen los mismos pasos; cambia el detalle
    Adapter           Dos fuentes dan lo mismo con interfaces distintas
    Repository        El código de negocio no debe saber dónde se guardan los datos
    Builder           Un objeto con muchas opciones es incómodo de construir
    Cadena de pasos   Una transformación es una secuencia de pasos pequeños

TIEMPO: 2.5 h · ANTES DE EMPEZAR: lección 1 y 01_core_python/02_organizacion_y_poo/05_poo_patrones_diseno.py

CALENTAMIENTO (sin mirar apuntes, responde en un comentario antes de empezar):
    1. ¿Qué es un Protocol y en qué se diferencia de heredar de una clase?
    2. ¿Por qué una función debe RECIBIR sus dependencias en lugar de crearlas?
    3. Nombra los cinco patrones que ya conoces y un uso de cada uno.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from functools import reduce
from typing import Callable, Protocol

# ════════════════════════════════════════════════════════════════════
# PASO 1 — Template Method: el esqueleto fijo, los detalles variables
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: la clase base define el ORDEN (extraer -> transformar -> cargar) y las
# subclases rellenan cada paso. El orden no se puede romper por error.


class PipelineBase(ABC):
    def ejecutar(self) -> int:  # el «template method»: no se sobrescribe
        filas = self.extraer()
        filas = self.transformar(filas)
        self.cargar(filas)
        return len(filas)

    @abstractmethod
    def extraer(self) -> list[dict]: ...

    def transformar(self, filas: list[dict]) -> list[dict]:  # paso opcional
        return filas

    @abstractmethod
    def cargar(self, filas: list[dict]) -> None: ...


class PipelineCompras(PipelineBase):
    def __init__(self):
        self.destino = []

    def extraer(self):
        return [{"id": 1, "monto": 100}, {"id": 2, "monto": -5}]

    def transformar(self, filas):
        return [fila for fila in filas if fila["monto"] > 0]

    def cargar(self, filas):
        self.destino.extend(filas)


p = PipelineCompras()
print("[paso 1]", p.ejecutar(), p.destino)
# SALIDA ESPERADA:
#   [paso 1] 1 [{'id': 1, 'monto': 100}]

# 👉 TU TURNO 1: añade a PipelineBase un paso validar(filas) entre transformar y
#    cargar, que por defecto lance ValueError si la lista está vacía.
#    Crea un pipeline que lo dispare.


# REFLEXIONA: Template Method usa herencia; la lección 1 decía «composición antes
# que herencia». ¿Cuándo compensa aquí la herencia?


# ════════════════════════════════════════════════════════════════════
# PASO 2 — Adapter: hacer encajar una interfaz que no controlas
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: tu código espera .leer() -> list[dict]. Una biblioteca externa ofrece
# otra cosa. No cambias tu código ni la biblioteca: pones un adaptador en medio.


class ClienteApiExterno:
    """Imagina que es de un proveedor: no puedes modificarlo."""

    def fetch_page(self, page: int) -> dict:
        datos = {1: [{"ID": 1, "Amount": "10.0"}], 2: [{"ID": 2, "Amount": "7.5"}], 3: []}
        return {"items": datos[page]}


class FuenteApi:
    """Adaptador: convierte fetch_page() paginado en leer() con tus nombres de campo."""

    def __init__(self, cliente: ClienteApiExterno):
        self._cliente = cliente

    def leer(self) -> list[dict]:
        filas, pagina = [], 1
        while items := self._cliente.fetch_page(pagina)["items"]:
            filas += [{"id": i["ID"], "monto": float(i["Amount"])} for i in items]
            pagina += 1
        return filas


print("[paso 2]", FuenteApi(ClienteApiExterno()).leer())
# SALIDA ESPERADA:
#   [paso 2] [{'id': 1, 'monto': 10.0}, {'id': 2, 'monto': 7.5}]

# 👉 TU TURNO 2: escribe un adaptador para este otro «proveedor», que devuelve
#    tuplas: class ClienteLegado:  def dump(self): return [(1, "10,0"), (2, "7,5")]
#    (ojo con la coma decimal).


# COMPRUEBA: tu adaptador devuelve exactamente lo mismo que FuenteApi.


# ════════════════════════════════════════════════════════════════════
# PASO 3 — Repository: el negocio no sabe dónde viven los datos
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: un repositorio ofrece operaciones con vocabulario de negocio
# (guardar, buscar_por_cuenta) y esconde el SQL. En los tests se usa uno en
# memoria. (Si conoces Java/Spring: es el @Repository de Spring Data.)


class RepositorioMovimientos(Protocol):
    def guardar(self, movimiento: dict) -> None: ...
    def buscar_por_cuenta(self, cuenta_id: int) -> list[dict]: ...


class RepositorioEnMemoria:
    def __init__(self):
        self._datos: dict[int, dict] = {}

    def guardar(self, movimiento):
        self._datos[movimiento["id"]] = movimiento  # misma clave = se reemplaza

    def buscar_por_cuenta(self, cuenta_id):
        return [m for m in self._datos.values() if m["cuenta_id"] == cuenta_id]


def gasto_de_cuenta(repo: RepositorioMovimientos, cuenta_id: int) -> float:
    return sum(m["monto"] for m in repo.buscar_por_cuenta(cuenta_id))


repo = RepositorioEnMemoria()
for mov in [{"id": 1, "cuenta_id": 7, "monto": 50.0}, {"id": 2, "cuenta_id": 7, "monto": 25.0},
            {"id": 1, "cuenta_id": 7, "monto": 50.0}]:
    repo.guardar(mov)
print("[paso 3]", gasto_de_cuenta(repo, 7))
# SALIDA ESPERADA:
#   [paso 3] 75.0

# 👉 TU TURNO 3: escribe RepositorioPostgres con los mismos dos métodos, usando
#    psycopg y la base banco_python (crea una tabla movimientos). guardar() debe
#    ser un UPSERT. gasto_de_cuenta() tiene que funcionar sin cambios.


# REFLEXIONA: el movimiento 1 se guardó dos veces y el total es 75, no 125.
# ¿Qué propiedad tiene guardar()? ¿Por qué importa en un pipeline que se reintenta?


# ════════════════════════════════════════════════════════════════════
# PASO 4 — Builder: construir paso a paso algo con muchas opciones
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: en lugar de un constructor con 9 parámetros, métodos que se encadenan
# y un build() final que valida. Lo usas cada día: SparkSession.builder.appName(...).


@dataclass
class Trabajo:
    origen: str
    destino: str
    reintentos: int = 0
    pasos: list[str] = field(default_factory=list)


class TrabajoBuilder:
    def __init__(self):
        self._origen = self._destino = None
        self._reintentos, self._pasos = 0, []

    def desde(self, origen):
        self._origen = origen
        return self  # devolver self permite encadenar

    def hacia(self, destino):
        self._destino = destino
        return self

    def con_reintentos(self, n):
        self._reintentos = n
        return self

    def paso(self, nombre):
        self._pasos.append(nombre)
        return self

    def build(self) -> Trabajo:
        if not self._origen or not self._destino:
            raise ValueError("faltan origen o destino")
        return Trabajo(self._origen, self._destino, self._reintentos, self._pasos)


trabajo = TrabajoBuilder().desde("s3://raw").hacia("s3://clean").paso("limpiar").con_reintentos(3).build()
print("[paso 4]", trabajo)
# SALIDA ESPERADA:
#   [paso 4] Trabajo(origen='s3://raw', destino='s3://clean', reintentos=3, pasos=['limpiar'])

# 👉 TU TURNO 4: añade .particionado_por(columna) y haz que build() falle si se
#    piden reintentos negativos.


# REFLEXIONA: en Python, ¿cuándo basta un dataclass con valores por defecto y
# argumentos con nombre, y cuándo compensa de verdad un Builder?


# ════════════════════════════════════════════════════════════════════
# PASO 5 — Cadena de pasos: una transformación es una lista de funciones
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: cada paso recibe datos y devuelve datos. La cadena los aplica en
# orden. Añadir, quitar o reordenar pasos no toca el código de ninguno.

Paso = Callable[[list[dict]], list[dict]]


def encadenar(*pasos: Paso) -> Paso:
    return lambda filas: reduce(lambda datos, paso: paso(datos), pasos, filas)


def quitar_negativos(filas):
    return [f for f in filas if f["monto"] > 0]


def a_centavos(filas):
    return [{**f, "monto": round(f["monto"] * 100)} for f in filas]


limpiar = encadenar(quitar_negativos, a_centavos)
print("[paso 5]", limpiar([{"id": 1, "monto": 1.5}, {"id": 2, "monto": -3.0}]))
# SALIDA ESPERADA:
#   [paso 5] [{'id': 1, 'monto': 150}]

# 👉 TU TURNO 5: escribe un paso `registrar(nombre)` que devuelva un Paso que
#    imprima cuántas filas pasan por ese punto y las deje pasar sin cambios.
#    Intercálalo dos veces en la cadena.


# REFLEXIONA: ¿en qué se parece esto a df.pipe(f).pipe(g) de pandas y a las
# transformaciones encadenadas de un DataFrame de Spark?


# ════════════════════════════════════════════════════════════════════
# CUÁNDO **NO** USAR UN PATRÓN
# ════════════════════════════════════════════════════════════════════
#   - Si solo hay UN caso, no hagas una fábrica ni una estrategia: espera al segundo.
#   - Singleton esconde dependencias y complica los tests: casi siempre es mejor
#     crear el objeto una vez y PASARLO (lección 1, paso 3).
#   - Un patrón que nadie del equipo reconoce es peor que un if claro.
#   Señal de que hace falta: estás copiando y pegando, o un cambio pequeño te
#   obliga a tocar muchos archivos.

# ════════════════════════════════════════════════════════════════════
# RETO DE LA LECCIÓN (usa los pasos 1 a 5)
# ════════════════════════════════════════════════════════════════════
# Toma tu solución de 04_retos_de_python/reto_11_mini_etl.py o reto_12_etl_json.py.
# Los dos hacen casi lo mismo con formatos distintos. Únelos en un solo diseño:
#   - una fuente por formato tras un mismo contrato (Adapter),
#   - los pasos de limpieza como cadena,
#   - el destino detrás de un repositorio.
# Añadir un tercer formato (Parquet) no debe modificar ningún archivo existente.
