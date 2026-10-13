"""
Tema 6 — Ingesta de datos | Lección 3: Datos de la web y JSON
===============================================================

TIEMPO: 1.5 h · ANTES DE EMPEZAR: lecciones 1 y 2; diccionarios y listas anidadas

CÓMO USAR ESTA LECCIÓN: predice, ejecuta, compara con la salida esperada, tu turno.
    python 06_ingenieria_de_datos/01_ingesta_de_datos/03_web_y_json.py     (necesita internet)

    pip install requests beautifulsoup4 lxml pandas

CALENTAMIENTO (sin mirar apuntes):
    1. ¿Por qué no se construye SQL con f-strings? Di el nombre del problema.
    2. ¿Qué hace una transacción si algo falla antes del COMMIT?
    3. Dado d = {"a": {"b": [10, 20]}}, ¿cómo obtienes el 20?
"""

import io
import json

import pandas as pd
import requests
from bs4 import BeautifulSoup

# ════════════════════════════════════════════════════════════════════
# PASO 1 — Pedir algo a un servidor
# ════════════════════════════════════════════════════════════════════
# APRENDERÁS: qué trae una respuesta HTTP además de los datos.
# CONCEPTO: requests.get devuelve un objeto con el código de estado (200 = bien),
# las cabeceras y el cuerpo. SIEMPRE con timeout: sin él, el programa puede
# quedarse esperando para siempre.

r = requests.get("https://api.frankfurter.dev/v1/2026-07-01?base=USD&symbols=MXN", timeout=10)
print("[paso 1]", r.status_code, r.headers["Content-Type"].split(";")[0], r.text)
# SALIDA ESPERADA:
#   [paso 1] 200 application/json {"amount":1.0,"base":"USD","date":"2026-07-01","rates":{"MXN":17.5341}}

# 👉 TU TURNO 1: pide el tipo de cambio del 2026-07-02 de USD a MXN y EUR.
#    Imprime r.url, r.encoding y los bytes de r.content.


# REFLEXIONA: r.text es un str. ¿Puedes hacer r.text["rates"]? ¿Por qué no?

# ════════════════════════════════════════════════════════════════════
# PASO 2 — JSON: de texto a diccionarios, y de vuelta
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: JSON es texto con forma de dict y list de Python.
#     json.loads(texto) -> objeto      json.dumps(objeto) -> texto
#     r.json() es un atajo de json.loads(r.text)

datos = json.loads(r.text)
print("[paso 2]", type(datos).__name__, datos["rates"]["MXN"], "|", json.dumps({"ciudad": "Querétaro"}, ensure_ascii=False))
# SALIDA ESPERADA:
#   [paso 2] dict 17.5341 | {"ciudad": "Querétaro"}

# 👉 TU TURNO 2: guarda `datos` en un archivo .json con sangría de 2 espacios y
#    vuelve a leerlo con json.load (sin la s). Comprueba que es igual al original.


# REFLEXIONA: ¿qué imprime json.dumps({"ciudad": "Querétaro"}) SIN ensure_ascii=False?

# ════════════════════════════════════════════════════════════════════
# PASO 3 — De JSON anidado a una tabla
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: las APIs devuelven objetos dentro de objetos. json_normalize los
# aplana: los dicts anidados pasan a columnas «cliente.nombre», y con record_path
# obtienes una fila por cada elemento de una lista interna.

PEDIDOS = [
    {"id": 1, "fecha": "2026-07-03", "cliente": {"nombre": "Ana López", "ciudad": "Querétaro"},
     "productos": [{"sku": "LAP-01", "precio": 25000, "cantidad": 1}, {"sku": "MOU-07", "precio": 550, "cantidad": 2}]},
    {"id": 2, "fecha": "2026-07-04", "cliente": {"nombre": "Bruno Díaz", "ciudad": "CDMX"},
     "productos": [{"sku": "TEC-03", "precio": 1800, "cantidad": 1}]},
    {"id": 3, "fecha": "2026-07-04", "cliente": {"nombre": "Carla Méndez", "ciudad": None}, "productos": []},
]

por_pedido = pd.json_normalize(PEDIDOS)
por_producto = pd.json_normalize(PEDIDOS, record_path="productos", meta=["id", ["cliente", "nombre"]])
print("[paso 3]", list(por_pedido.columns))
print("[paso 3]", por_producto.shape, list(por_producto.columns))
# SALIDA ESPERADA:
#   [paso 3] ['id', 'fecha', 'productos', 'cliente.nombre', 'cliente.ciudad']
#   [paso 3] (3, 5) ['sku', 'precio', 'cantidad', 'id', 'cliente.nombre']

# 👉 TU TURNO 3: calcula el importe total de cada pedido (precio × cantidad).


# COMPRUEBA: el pedido 1 suma 26,100 y el 2 suma 1,800.
# REFLEXIONA: el pedido 3 no aparece en por_producto. ¿Por qué? ¿Es un problema?

# ════════════════════════════════════════════════════════════════════
# PASO 4 — Cuando no hay API: leer HTML
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: una página web es un árbol de etiquetas. BeautifulSoup lo recorre:
# find trae la primera coincidencia, find_all todas. pd.read_html extrae <table>.

HTML = """
<html><head><title>Reportes de julio</title></head><body>
<table>
  <tr><th>sucursal</th><th>ventas</th><th>clientes</th></tr>
  <tr><td>Centro</td><td>152000</td><td>310</td></tr>
  <tr><td>Juriquilla</td><td>98000</td><td>190</td></tr>
</table>
<a href="/descargas/ventas_julio.csv">Ventas</a>
<a href="/descargas/clientes_julio.csv">Clientes</a>
<a href="/ayuda.html">Ayuda</a>
</body></html>
"""

soup = BeautifulSoup(HTML, "html.parser")
tabla = pd.read_html(io.StringIO(HTML))[0]
print("[paso 4]", soup.title.text, "|", len(soup.find_all("a")), "enlaces |", tabla.shape, int(tabla["ventas"].sum()))
# SALIDA ESPERADA:
#   [paso 4] Reportes de julio | 3 enlaces | (2, 3) 250000

# 👉 TU TURNO 4: con BeautifulSoup (sin read_html), extrae la tabla a una lista de
#    diccionarios y saca solo los enlaces que terminan en .csv.


# COMPRUEBA: 2 diccionarios y 2 enlaces. ¿De qué tipo te quedó "ventas": str o int?
# REFLEXIONA: si un sitio ofrece una API y también puedes leer su HTML, ¿cuál
# usarías en un pipeline diario? ¿Cuál se rompe antes y por qué?

# ════════════════════════════════════════════════════════════════════
# RETO DE LA LECCIÓN (pasos 1 a 4)
# ════════════════════════════════════════════════════════════════════
# Escribe descargar(url, destino) que guarde un archivo en disco y devuelva la
# ruta. Si ya existe, no lo descarga otra vez. Si el servidor responde con un
# código distinto de 200, lanza una excepción con el código y la URL.
# COMPRUEBA: la segunda llamada con la misma URL no hace ninguna petición
# (demuéstralo con un print o midiendo el tiempo).
