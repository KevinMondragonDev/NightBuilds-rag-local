"""
Tema 6 — Ingesta de datos | Lección 4: Consumir APIs REST
===========================================================

TIEMPO: 2 h · ANTES DE EMPEZAR: lección 3 y 02_funciones_y_poo/02_excepciones

CÓMO USAR ESTA LECCIÓN: predice, ejecuta, compara con la salida esperada, tu turno.
    python 05_ingenieria_de_datos/01_ingesta_de_datos/03_web_y_apis/04_apis_rest.py     (necesita internet; tarda ~5 s)

    APIs públicas sin clave que usa la lección:
        https://api.frankfurter.dev/v1/   tipos de cambio
        https://httpbin.org/              devuelve lo que le envías: perfecta para practicar

    pip install requests pandas

CALENTAMIENTO (sin mirar apuntes):
    1. ¿Qué diferencia hay entre r.text y r.json()?
    2. ¿Para qué sirve el parámetro timeout?
    3. ¿Qué hace record_path en pd.json_normalize?
"""

import pandas as pd
import requests

CAMBIO = "https://api.frankfurter.dev/v1"
PRUEBAS = "https://httpbin.org"

# ════════════════════════════════════════════════════════════════════
# PASO 1 — Parámetros: no escribas la URL a mano
# ════════════════════════════════════════════════════════════════════
# APRENDERÁS: a construir peticiones sin errores de formato.
# CONCEPTO: una API REST expone recursos en URLs. Lo que va después de «?» son
# parámetros de consulta. Pásalos como dict en `params`: requests los codifica
# (espacios, acentos, comas) por ti.

r = requests.get(f"{CAMBIO}/2026-07-01", params={"base": "USD", "symbols": "MXN"}, timeout=10)
print("[paso 1]", r.url, "->", r.json()["rates"]["MXN"])
# SALIDA ESPERADA:
#   [paso 1] https://api.frankfurter.dev/v1/2026-07-01?base=USD&symbols=MXN -> 17.5341

# 👉 TU TURNO 1: pide a httpbin.org/get los parámetros ciudad="Querétaro" y
#    q="tipo de cambio". Imprime r.url. ¿Cómo quedaron el acento y los espacios?


# ════════════════════════════════════════════════════════════════════
# PASO 2 — Códigos de estado: la respuesta puede ser un error
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: 2xx éxito · 4xx el error es TUYO (petición mal hecha) · 5xx el error
# es del SERVIDOR. requests NO lanza excepción por un 404: tienes que mirar el
# código o llamar a raise_for_status().
#     200 OK · 201 creado · 400 mal formada · 401 sin autenticar · 403 sin permiso
#     404 no existe · 429 demasiadas peticiones · 500/503 fallo del servidor

for codigo in (404, 503):
    r = requests.get(f"{PRUEBAS}/status/{codigo}", timeout=10)
    try:
        r.raise_for_status()
    except requests.HTTPError:
        culpa = "mía" if 400 <= r.status_code < 500 else "del servidor"
        print(f"[paso 2] {r.status_code}: la culpa es {culpa}")
# SALIDA ESPERADA:
#   [paso 2] 404: la culpa es mía
#   [paso 2] 503: la culpa es del servidor

# 👉 TU TURNO 2: pide una fecha imposible a la API de tipo de cambio
#    (/v1/2026-13-45). ¿Qué código devuelve? ¿Y qué trae el cuerpo?


# REFLEXIONA: ¿en cuáles de estos tiene sentido REINTENTAR y en cuáles no?
# 400, 401, 404, 429, 503. (Relaciónalo con 04_retos_de_python/reto_10.)

# ════════════════════════════════════════════════════════════════════
# PASO 3 — Enviar datos: cabeceras y POST
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: GET lee, POST crea, PUT reemplaza, DELETE borra. Las CABECERAS llevan
# información sobre la petición (quién eres, qué formato quieres). El cuerpo de
# un POST va en `json=`.

r = requests.post(f"{PRUEBAS}/post", json={"nombre": "Ana"},
                  headers={"X-Proyecto": "certificacion-python"}, timeout=10)
eco = r.json()
print("[paso 3]", r.status_code, eco["json"], eco["headers"]["X-Proyecto"])
# SALIDA ESPERADA:
#   [paso 3] 200 {'nombre': 'Ana'} certificacion-python

# 👉 TU TURNO 3: envía una cabecera Authorization: Bearer mi-token-falso a
#    httpbin.org/bearer. ¿Qué responde con la cabecera y sin ella?
#    En un proyecto real, ¿de dónde saldría ese token? (No del código.)


# ════════════════════════════════════════════════════════════════════
# PASO 4 — Cuando la red falla
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: además de los códigos de error, la petición puede no llegar a
# completarse. Son excepciones distintas y conviene distinguirlas:
#     requests.Timeout          tardó demasiado
#     requests.ConnectionError  sin red, o el servidor no existe
#     requests.HTTPError        4xx / 5xx (la lanza raise_for_status)

try:
    requests.get(f"{PRUEBAS}/delay/5", timeout=2)
except requests.Timeout:
    print("[paso 4] timeout: el servidor tardó más de 2 s")
# SALIDA ESPERADA:
#   [paso 4] timeout: el servidor tardó más de 2 s

# 👉 TU TURNO 4: escribe pedir(url, **kwargs) que devuelva el JSON y convierta los
#    tres tipos de fallo en un mensaje distinto para cada uno.
#    Pruébala con una URL que no exista: https://esto-no-existe.invalid


# ════════════════════════════════════════════════════════════════════
# PASO 5 — De la API a un DataFrame
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: casi nunca te sirve el JSON tal cual. Lo conviertes en una tabla con
# tipos correctos.

r = requests.get(f"{CAMBIO}/2026-07-01..2026-07-10", params={"base": "USD", "symbols": "MXN"}, timeout=10)
cambio = pd.DataFrame([{"fecha": fecha, "mxn": valores["MXN"]} for fecha, valores in r.json()["rates"].items()])
cambio["fecha"] = pd.to_datetime(cambio["fecha"])
print("[paso 5]", cambio.shape, cambio["mxn"].max(), str(cambio.loc[cambio["mxn"].idxmax(), "fecha"].date()))
# SALIDA ESPERADA:
#   [paso 5] (8, 2) 17.5754 2026-07-08

# 👉 TU TURNO 5: haz lo mismo para julio a septiembre de 2026.
#    ¿Cuántas filas hay? ¿Por qué no son 92? ¿Qué día fue más caro el dólar?


# ════════════════════════════════════════════════════════════════════
# RETO DE LA LECCIÓN (pasos 1 a 5)
# ════════════════════════════════════════════════════════════════════
# Muchas APIs devuelven los datos por páginas. Simúlalo: escribe
# tipos_de_cambio(inicio, fin) que pida la API MES A MES en un bucle, junte los
# resultados y devuelva un único DataFrame sin fechas repetidas. Cada llamada con
# timeout y hasta 3 reintentos con espera creciente (solo en los errores en los
# que tiene sentido reintentar).
# COMPRUEBA: enero a septiembre de 2026 devuelve 192 filas, las mismas que pedir
# todo el rango en una sola llamada.
