"""
Tema 11 — APIs con FastAPI | Lección 2: Modelos y validación con Pydantic
===========================================================================

CÓMO USAR ESTA LECCIÓN: igual que la lección 1.
    python 02_modelos_y_validacion.py
    uvicorn 02_modelos_y_validacion:app --reload   ->  http://127.0.0.1:8000/docs

    Un modelo de Pydantic describe la forma de un dato (campos y tipos) y lo
    valida solo. Si conoces Java/Spring: es un DTO con @NotNull, @Min o @Size
    escritos como tipos.

TIEMPO: 1.5 h · ANTES DE EMPEZAR: lección 1

CALENTAMIENTO (sin mirar apuntes, responde en un comentario antes de empezar):
    1. ¿Cómo declaras un parámetro de ruta con tipo y qué pasa si llega otro tipo?
    2. ¿Quién responde 422: tu código o FastAPI?
    3. ¿Qué hace raise HTTPException(status_code=404)?
"""

from datetime import datetime
from typing import Literal

from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field, field_validator

app = FastAPI(title="Banco de práctica", version="0.2.0")
MOVIMIENTOS: dict[int, dict] = {}

# ════════════════════════════════════════════════════════════════════
# PASO 1 — Un modelo de entrada
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: declaras los campos con su tipo y sus reglas. Si el JSON que llega
# no cumple, FastAPI responde 422 explicando qué campo falla y por qué.


class MovimientoEntrada(BaseModel):
    cuenta_id: int = Field(gt=0)
    tipo: Literal["compra", "deposito", "retiro", "transferencia"]
    monto: float = Field(gt=0, description="Siempre positivo; el tipo indica el sentido")
    comercio: str | None = Field(default=None, max_length=50)

    # PASO 3 — Una regla que depende de varios campos o necesita código
    @field_validator("comercio")
    @classmethod
    def limpiar_comercio(cls, valor):
        return valor.strip().title() if valor else valor


# 👉 TU TURNO 1: añade el campo opcional `categoria`, que solo acepte las 6
#    categorías válidas del módulo de limpieza.


# ════════════════════════════════════════════════════════════════════
# PASO 2 — Un modelo de salida distinto del de entrada
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: lo que recibes y lo que devuelves no son lo mismo: el id y la fecha
# los pone el servidor. response_model filtra la respuesta: lo que no esté en el
# modelo NO sale, aunque esté en tus datos (aquí, `interno`).


class MovimientoSalida(MovimientoEntrada):
    id: int
    creado_en: datetime


@app.post("/movimientos", response_model=MovimientoSalida, status_code=status.HTTP_201_CREATED)
def crear_movimiento(entrada: MovimientoEntrada):
    nuevo_id = len(MOVIMIENTOS) + 1
    MOVIMIENTOS[nuevo_id] = {**entrada.model_dump(), "id": nuevo_id, "creado_en": datetime(2026, 7, 1, 12, 0),
                             "interno": "no debe salir en la respuesta"}
    return MOVIMIENTOS[nuevo_id]


@app.get("/movimientos/{movimiento_id}", response_model=MovimientoSalida)
def obtener_movimiento(movimiento_id: int):
    if movimiento_id not in MOVIMIENTOS:
        raise HTTPException(status_code=404, detail="No existe")
    return MOVIMIENTOS[movimiento_id]


# 👉 TU TURNO 2: añade DELETE /movimientos/{id} que responda 204 sin cuerpo, y 404
#    si no existe.

# 👉 TU TURNO 3: añade con @model_validator(mode="after") la regla entre campos
#    «solo las compras pueden llevar comercio» (repasa la validación entre
#    columnas de 02_limpieza_y_eficiencia/02_limpieza_texto_y_nulos.py).

# ════════════════════════════════════════════════════════════════════
# DEMOSTRACIÓN
# ════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    cliente = TestClient(app)
    casos = [
        {"cuenta_id": 7, "tipo": "compra", "monto": 250.0, "comercio": "  walmart "},
        {"cuenta_id": 7, "tipo": "regalo", "monto": 250.0},
        {"cuenta_id": 7, "tipo": "compra", "monto": -5},
        {"tipo": "compra", "monto": 10},
    ]
    for cuerpo in casos:
        r = cliente.post("/movimientos", json=cuerpo)
        if r.status_code == 201:
            print(r.status_code, r.json())
        else:
            error = r.json()["detail"][0]
            print(r.status_code, error["loc"], "->", error["msg"])
# SALIDA ESPERADA:
#   201 {'cuenta_id': 7, 'tipo': 'compra', 'monto': 250.0, 'comercio': 'Walmart', 'id': 1, 'creado_en': '2026-07-01T12:00:00'}
#   422 ['body', 'tipo'] -> Input should be 'compra', 'deposito', 'retiro' or 'transferencia'
#   422 ['body', 'monto'] -> Input should be greater than 0
#   422 ['body', 'cuenta_id'] -> Field required
#
# REFLEXIONA:
#   - En la respuesta 201 no aparece «interno». ¿Qué línea lo evitó? ¿Por qué es
#     importante en una API que sirve datos de clientes?
#   - Validar en la API y validar en el pipeline de limpieza: ¿se sustituyen o se suman?
#
# RETO DE LA LECCIÓN (pasos 1 a 3):
#   Añade PUT /movimientos/{id} (reemplazo completo) y PATCH /movimientos/{id}
#   (solo los campos enviados: mira model_dump(exclude_unset=True)).
#   Devuelve 404, 422 y 200 según corresponda y pruébalo en /docs.
