"""
Tema 11 — APIs con FastAPI | Lección 1: Tu primera API
========================================================

En 01_ingesta_de_datos/03_web_y_apis/04_apis_rest.py CONSUMISTE APIs. Ahora las CONSTRUYES.
Un Data Engineer las usa para servir datos ya procesados a otras aplicaciones.

CÓMO USAR ESTA LECCIÓN:
    1) Ejecuta el archivo: verás la demostración de cada paso (usa un cliente de
       pruebas, no hace falta levantar el servidor).
           python 01_primera_api.py
    2) Levanta el servidor y juega con la documentación interactiva:
           cd 05_ingenieria_de_datos/06_apis_con_fastapi/01_construir
           uvicorn 01_primera_api:app --reload
           abre http://127.0.0.1:8000/docs
    3) Haz cada «TU TURNO» y compruébalo en /docs.

    pip install fastapi uvicorn httpx

SI YA CONOCES SPRING BOOT (opcional; si no, sáltate esta tabla):
    @RestController + @GetMapping("/x")     ->  @app.get("/x")
    @PathVariable Long id                   ->  def f(id: int)
    @RequestParam(defaultValue="10")        ->  def f(limite: int = 10)
    @RequestBody Dto dto                    ->  def f(dto: Modelo)       (lección 2)
    ResponseStatusException(NOT_FOUND)      ->  raise HTTPException(404)
    @Autowired                              ->  Depends(...)             (lección 3)
    Swagger / springdoc                     ->  /docs, incluido de serie

TIEMPO: 1.5 h · ANTES DE EMPEZAR: 01_ingesta_de_datos/03_web_y_apis/04_apis_rest.py

CALENTAMIENTO (sin mirar apuntes, responde en un comentario antes de empezar):
    1. ¿Qué significan los códigos 200, 404 y 422?
    2. ¿Qué diferencia hay entre GET y POST?
    3. En /cuentas?tipo=debito, ¿cómo se llama la parte que va después de «?»?
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.testclient import TestClient

app = FastAPI(title="Banco de práctica", version="0.1.0")

CUENTAS = {
    1: {"id": 1, "cliente": "Ana López", "tipo": "credito", "saldo": 67144.46},
    2: {"id": 2, "cliente": "Bruno Díaz", "tipo": "debito", "saldo": 109001.68},
    3: {"id": 3, "cliente": "Carla Méndez", "tipo": "debito", "saldo": -8085.75},
}

# ════════════════════════════════════════════════════════════════════
# PASO 1 — Un endpoint
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: el decorador une un verbo HTTP y una ruta con una función. Lo que la
# función devuelve (dict o lista) se convierte a JSON.


@app.get("/salud")
def salud():
    return {"estado": "ok"}


# 👉 TU TURNO 1: añade GET /version que devuelva {"version": "0.1.0"} leyendo
#    app.version (no lo escribas a mano).


# ════════════════════════════════════════════════════════════════════
# PASO 2 — Parámetros de ruta con tipo
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: el type hint VALIDA y CONVIERTE. /cuentas/2 llega como int 2.
# /cuentas/abc responde 422 sin que escribas una sola comprobación.


@app.get("/cuentas/{cuenta_id}")
def obtener_cuenta(cuenta_id: int):
    if cuenta_id not in CUENTAS:  # PASO 4: errores con código de estado
        raise HTTPException(status_code=404, detail=f"La cuenta {cuenta_id} no existe")
    return CUENTAS[cuenta_id]


# 👉 TU TURNO 2: añade GET /cuentas/{cuenta_id}/saldo que devuelva solo
#    {"cuenta_id": ..., "saldo": ...}.


# ════════════════════════════════════════════════════════════════════
# PASO 3 — Parámetros de consulta (query)
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: los parámetros de la función que NO están en la ruta son de consulta:
# /cuentas?tipo=debito&limite=1. Con valor por defecto son opcionales.
# Query(...) añade reglas: ge = mayor o igual, le = menor o igual.


@app.get("/cuentas")
def listar_cuentas(tipo: str | None = None, limite: int = Query(default=10, ge=1, le=100)):
    cuentas = [c for c in CUENTAS.values() if tipo is None or c["tipo"] == tipo]
    return cuentas[:limite]


# 👉 TU TURNO 3: añade el parámetro opcional saldo_minimo: float y un parámetro
#    `orden` que solo acepte "saldo" o "id" (busca typing.Literal).


# ════════════════════════════════════════════════════════════════════
# PASO 4 — Errores con el código correcto
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: una API habla con códigos de estado (repasa 04_apis_rest.py).
# Devolver 200 con {"error": "..."} obliga al cliente a adivinar.
# Mira obtener_cuenta: 404 si no existe; 422 lo pone FastAPI si el tipo no encaja.
#
# 👉 TU TURNO 4: en tu endpoint de saldo, responde 409 si la cuenta está en
#    números rojos, con un mensaje que lo explique.


# ════════════════════════════════════════════════════════════════════
# DEMOSTRACIÓN (se ejecuta con: python 01_primera_api.py)
# ════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    cliente = TestClient(app)
    for ruta in ["/salud", "/cuentas/2", "/cuentas/99", "/cuentas/abc", "/cuentas?tipo=debito&limite=1", "/cuentas?limite=0"]:
        r = cliente.get(ruta)
        cuerpo = r.json()
        if r.status_code == 422:
            cuerpo = cuerpo["detail"][0]["msg"]
        print(f"GET {ruta:32} -> {r.status_code} {cuerpo}")
# SALIDA ESPERADA:
#   GET /salud                           -> 200 {'estado': 'ok'}
#   GET /cuentas/2                       -> 200 {'id': 2, 'cliente': 'Bruno Díaz', 'tipo': 'debito', 'saldo': 109001.68}
#   GET /cuentas/99                      -> 404 {'detail': 'La cuenta 99 no existe'}
#   GET /cuentas/abc                     -> 422 Input should be a valid integer, unable to parse string as an integer
#   GET /cuentas?tipo=debito&limite=1    -> 200 [{'id': 2, 'cliente': 'Bruno Díaz', 'tipo': 'debito', 'saldo': 109001.68}]
#   GET /cuentas?limite=0                -> 422 Input should be greater than or equal to 1
#
# REFLEXIONA:
#   - ¿Quién generó el error de /cuentas/abc, tu código o FastAPI? ¿Qué ganas con eso?
#   - En /docs aparece cada parámetro con su tipo y sus límites. ¿De dónde sale esa información?
#
# RETO DE LA LECCIÓN (pasos 1 a 4):
#   Carga 05_ingenieria_de_datos/datos/movimientos.csv al arrancar y expón:
#     GET /movimientos                 con filtros tipo, categoria, desde, hasta y paginación (limite, desplazamiento)
#     GET /movimientos/{id}            404 si no existe
#     GET /cuentas/{id}/resumen        nº de movimientos, total gastado y categoría principal
#   Comprueba cada uno en /docs con un caso válido y uno inválido.
