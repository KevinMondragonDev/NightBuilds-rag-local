"""
Tema 11 — APIs con FastAPI | Lección 4: Probar una API y manejar errores
==========================================================================

CÓMO USAR ESTA LECCIÓN:
    Este archivo ES un archivo de tests. Ejecútalo con pytest:
        pytest 04_tests_y_errores.py -v
    Verás 4 tests en verde y 1 que se salta: es tu primer «TU TURNO».

    Repasa antes 03_ingenieria_de_software/04_testing_con_pytest.py.

    pip install fastapi httpx pytest

TIEMPO: 2 h · ANTES DE EMPEZAR: lección 3 y 03_ingenieria_de_software/04_testing_con_pytest.py

CALENTAMIENTO (sin mirar apuntes, responde en un comentario antes de empezar):
    1. Las tres partes de un test.
    2. ¿Qué es un fixture y cómo lo pide un test?
    3. ¿Por qué el servicio de la lección 3 no lanza HTTPException?
"""

import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

app = FastAPI()

# ════════════════════════════════════════════════════════════════════
# PASO 1 — Un manejador de errores para toda la API
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: en lugar de un try/except en cada endpoint (lección 3), registras UNA
# vez cómo se traduce cada excepción de negocio a una respuesta HTTP.
# (Si conoces Java/Spring: es @ControllerAdvice + @ExceptionHandler.)


class CuentaNoExiste(Exception):
    def __init__(self, cuenta_id: int):
        self.cuenta_id = cuenta_id


@app.exception_handler(CuentaNoExiste)
def manejar_cuenta_no_existe(request: Request, error: CuentaNoExiste):
    return JSONResponse(status_code=404, content={"error": "cuenta_no_existe", "cuenta_id": error.cuenta_id})


# ════════════════════════════════════════════════════════════════════
# PASO 2 — Un endpoint con una dependencia que se puede sustituir
# ════════════════════════════════════════════════════════════════════


def obtener_saldos() -> dict[int, float]:
    raise RuntimeError("En producción esto consultaría PostgreSQL")


@app.get("/cuentas/{cuenta_id}/saldo")
def saldo(cuenta_id: int, saldos: dict = Depends(obtener_saldos)):
    if cuenta_id not in saldos:
        raise CuentaNoExiste(cuenta_id)
    return {"cuenta_id": cuenta_id, "saldo": saldos[cuenta_id]}


# ════════════════════════════════════════════════════════════════════
# PASO 3 — Tests: el cliente de pruebas y dependency_overrides
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: TestClient llama a la API sin levantar un servidor.
# app.dependency_overrides cambia una dependencia por otra SOLO en los tests:
# así la API se prueba sin base de datos. Es la inyección de dependencias de
# 05_patrones_de_diseno/01 (paso 3) puesta a trabajar.


@pytest.fixture
def cliente():
    app.dependency_overrides[obtener_saldos] = lambda: {1: 500.0, 2: -20.0}
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_saldo_de_una_cuenta_existente(cliente):
    respuesta = cliente.get("/cuentas/1/saldo")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"cuenta_id": 1, "saldo": 500.0}


def test_cuenta_inexistente_devuelve_404_con_cuerpo_util(cliente):
    respuesta = cliente.get("/cuentas/99/saldo")
    assert respuesta.status_code == 404
    assert respuesta.json() == {"error": "cuenta_no_existe", "cuenta_id": 99}


@pytest.mark.parametrize("ruta", ["/cuentas/abc/saldo", "/cuentas/1.5/saldo"])
def test_id_no_entero_devuelve_422(cliente, ruta):
    assert cliente.get(ruta).status_code == 422


@pytest.mark.skip(reason="TU TURNO 1: quita esta línea y haz que pase")
def test_saldo_negativo_incluye_aviso(cliente):
    # 👉 TU TURNO 1: modifica el endpoint para que, si el saldo es negativo, la
    #    respuesta incluya "en_numeros_rojos": true. Este test ya lo comprueba.
    respuesta = cliente.get("/cuentas/2/saldo")
    assert respuesta.json()["en_numeros_rojos"] is True


# 👉 TU TURNO 2: escribe un test que compruebe que, SIN el override, el endpoint
#    responde 500 (pista: TestClient(app, raise_server_exceptions=False)).

# 👉 TU TURNO 3: añade un manejador para SaldoInsuficiente (409) y su test,
#    escribiendo PRIMERO el test.

# REFLEXIONA:
#   - ¿Qué NO están probando estos tests? (Pista: el SQL real.) ¿Cómo lo cubrirías?
#   - ¿Por qué el fixture limpia dependency_overrides al terminar?
#
# RETO DE LA LECCIÓN (pasos 1 a 3):
#   Escribe la batería de tests del paquete api/ que montaste en la lección 3:
#   un test por código de estado posible de cada endpoint, con el repositorio en
#   memoria inyectado. Objetivo: 90 % de cobertura en routers y servicios.
