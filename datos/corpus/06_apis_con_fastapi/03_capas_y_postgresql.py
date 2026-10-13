"""
Tema 11 — APIs con FastAPI | Lección 3: Capas, dependencias y PostgreSQL
==========================================================================

CÓMO USAR ESTA LECCIÓN: igual que las anteriores.
    python 03_capas_y_postgresql.py
    uvicorn 03_capas_y_postgresql:app --reload

    Aquí se juntan tres cosas que ya conoces:
        - el patrón Repository       (05_patrones_de_diseno/02, paso 3)
        - la inyección de dependencias (05_patrones_de_diseno/01, paso 3)
        - PostgreSQL desde Python    (01_ingesta_de_datos/02)

    Tres capas (en Java/Spring se llaman igual):
        Controller  ->  las funciones con @router.get     (HTTP: códigos, parámetros)
        Service     ->  funciones de negocio              (reglas, sin HTTP ni SQL)
        Repository  ->  una clase por almacenamiento      (SQL, sin reglas)

    pip install fastapi uvicorn httpx "psycopg[binary]"

TIEMPO: 2.5 h · ANTES DE EMPEZAR: lección 2, 05_patrones_de_diseno/01 y 02, y 01_ingesta_de_datos/02

CALENTAMIENTO (sin mirar apuntes, responde en un comentario antes de empezar):
    1. ¿Qué esconde un repositorio y qué vocabulario usa?
    2. Explica la inyección de dependencias en una frase.
    3. ¿Para qué sirve response_model?
"""

from typing import Protocol

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

# ════════════════════════════════════════════════════════════════════
# PASO 1 — El repositorio: solo datos
# ════════════════════════════════════════════════════════════════════


class RepositorioCuentas(Protocol):
    def obtener(self, cuenta_id: int) -> dict | None: ...
    def guardar_saldo(self, cuenta_id: int, saldo: float) -> None: ...


class RepositorioEnMemoria:
    def __init__(self):
        self._cuentas = {1: {"id": 1, "saldo": 1000.0}, 2: {"id": 2, "saldo": 50.0}}

    def obtener(self, cuenta_id):
        return self._cuentas.get(cuenta_id)

    def guardar_saldo(self, cuenta_id, saldo):
        self._cuentas[cuenta_id]["saldo"] = saldo


# 👉 TU TURNO 1: escribe RepositorioPostgres(conexion) con los mismos dos métodos
#    sobre la tabla cuentas de banco_python. Consultas con parámetros (%s).


# ════════════════════════════════════════════════════════════════════
# PASO 2 — El servicio: solo reglas de negocio
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: no sabe nada de HTTP (lanza excepciones propias, no HTTPException) ni
# de SQL (recibe el repositorio). Por eso se puede probar con un assert.


class CuentaNoExiste(Exception): ...


class SaldoInsuficiente(Exception): ...


def retirar(repo: RepositorioCuentas, cuenta_id: int, monto: float) -> float:
    cuenta = repo.obtener(cuenta_id)
    if cuenta is None:
        raise CuentaNoExiste(cuenta_id)
    if cuenta["saldo"] < monto:
        raise SaldoInsuficiente(cuenta_id)
    nuevo_saldo = round(cuenta["saldo"] - monto, 2)
    repo.guardar_saldo(cuenta_id, nuevo_saldo)
    return nuevo_saldo


# 👉 TU TURNO 2: escribe el servicio transferir(repo, origen, destino, monto).
#    ¿Qué pasa si falla entre el retiro y el depósito? Anótalo: lo resuelves en el
#    turno 4 con una transacción.


# ════════════════════════════════════════════════════════════════════
# PASO 3 — El controlador: solo HTTP, con la dependencia inyectada
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: Depends(funcion) le dice a FastAPI «antes de llamarme, ejecuta esta
# función y pásame lo que devuelva». El endpoint no sabe qué repositorio recibe.

_repo_compartido = RepositorioEnMemoria()


def obtener_repo() -> RepositorioCuentas:
    return _repo_compartido


class Retiro(BaseModel):
    monto: float


router = APIRouter(prefix="/cuentas", tags=["cuentas"])


@router.post("/{cuenta_id}/retiros")
def crear_retiro(cuenta_id: int, retiro: Retiro, repo: RepositorioCuentas = Depends(obtener_repo)):
    try:
        return {"cuenta_id": cuenta_id, "saldo": retirar(repo, cuenta_id, retiro.monto)}
    except CuentaNoExiste:
        raise HTTPException(status_code=404, detail="La cuenta no existe")
    except SaldoInsuficiente:
        raise HTTPException(status_code=409, detail="Saldo insuficiente")


app = FastAPI(title="Banco de práctica", version="0.3.0")
app.include_router(router)

# 👉 TU TURNO 3: escribe obtener_repo_postgres() que abra una conexión con psycopg
#    (credenciales en variables de entorno), la entregue con `yield` y la cierre al
#    terminar la petición. Cambia el Depends para usarla.

# 👉 TU TURNO 4: añade POST /transferencias. Con PostgreSQL, las dos operaciones
#    van en UNA transacción: si la segunda falla, la primera se deshace.

# ════════════════════════════════════════════════════════════════════
# DEMOSTRACIÓN
# ════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    cliente = TestClient(app)
    for cuenta_id, monto in [(1, 300), (2, 300), (9, 10)]:
        r = cliente.post(f"/cuentas/{cuenta_id}/retiros", json={"monto": monto})
        print(r.status_code, r.json())
# SALIDA ESPERADA:
#   200 {'cuenta_id': 1, 'saldo': 700.0}
#   409 {'detail': 'Saldo insuficiente'}
#   404 {'detail': 'La cuenta no existe'}
#
# REFLEXIONA:
#   - ¿Qué capa tendrías que tocar para cambiar PostgreSQL por DynamoDB? ¿Y para
#     cambiar el límite de retiro? ¿Y para devolver 422 en vez de 409?
#   - ¿Por qué retirar() no lanza HTTPException directamente?
#
# RETO DE LA LECCIÓN (pasos 1 a 3):
#   Separa este archivo en un paquete: api/routers/cuentas.py, api/servicios.py,
#   api/repositorios.py, api/dependencias.py y api/main.py. Debe arrancar con
#   `uvicorn api.main:app` contra PostgreSQL.
