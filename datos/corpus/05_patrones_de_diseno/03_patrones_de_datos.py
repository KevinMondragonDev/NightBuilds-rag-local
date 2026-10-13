"""
Tema 10 — Patrones de diseño | Lección 3: Patrones de ingeniería de datos
===========================================================================

CÓMO USAR ESTA LECCIÓN: igual que las anteriores (predice, ejecuta, compara, tu turno).

    Los de las lecciones 1 y 2 son patrones de CÓDIGO. Estos son patrones de DATOS:
    no dependen del lenguaje y son los que te preguntarán en una entrevista de
    Data Engineering.

    Patrón                  Pregunta que responde
    ----------------------  ----------------------------------------------------
    Carga idempotente       ¿Qué pasa si el job corre dos veces?
    Incremental (watermark) ¿Cómo proceso solo lo nuevo?
    Cuarentena (DLQ)        ¿Qué hago con las filas malas?
    Write-Audit-Publish     ¿Cómo evito publicar datos rotos?
    Historial (SCD tipo 2)  ¿Cómo sé qué valor tenía un dato en el pasado?
    Capas (medallion)       ¿Dónde vive cada versión de los datos?

TIEMPO: 2 h · ANTES DE EMPEZAR: lección 2 y 04_pipelines/02_carga_y_monitoreo.py

CALENTAMIENTO (sin mirar apuntes, responde en un comentario antes de empezar):
    1. Define «idempotente» y da las dos recetas para conseguirlo en PostgreSQL.
    2. ¿Qué problema resuelve el patrón Repository?
    3. ¿Qué hiciste con las filas rechazadas en tu sideproject de calidad de datos?
"""

from datetime import date

# ════════════════════════════════════════════════════════════════════
# PASO 1 — Carga idempotente
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: ejecutar N veces = ejecutar una vez. Se consigue cargando por CLAVE
# (upsert) o reemplazando la PARTICIÓN completa. Nunca con «append» a ciegas.

lote = [{"id": 1, "monto": 10}, {"id": 2, "monto": 20}]

tabla_append: list[dict] = []
tabla_upsert: dict[int, dict] = {}

for _ in range(3):  # el job se relanza tres veces
    tabla_append.extend(lote)
    tabla_upsert.update({fila["id"]: fila for fila in lote})

print("[paso 1] append:", len(tabla_append), "| upsert:", len(tabla_upsert))
# SALIDA ESPERADA:
#   [paso 1] append: 6 | upsert: 2

# 👉 TU TURNO 1: implementa la otra variante, «reemplazar la partición»: una
#    tabla dict[fecha -> list[dict]] donde cargar(fecha, filas) sustituye todo lo
#    de ese día. Cárgala tres veces y comprueba que no crece.


# REFLEXIONA: el upsert no borra una fila que ya no viene en el origen;
# reemplazar la partición sí. ¿Cuál quieres para un extracto diario completo?


# ════════════════════════════════════════════════════════════════════
# PASO 2 — Carga incremental con marca de agua (watermark)
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: guardas «hasta dónde llegué» (la mayor fecha o id procesado) y en la
# siguiente ejecución pides solo lo posterior. La marca se actualiza DESPUÉS de
# cargar con éxito, nunca antes.

origen = [{"id": i, "fecha": date(2026, 7, i)} for i in range(1, 7)]
estado = {"marca": date(2026, 7, 3)}  # en la vida real: un archivo o una tabla de control


def extraer_nuevos(origen, marca):
    return [fila for fila in origen if fila["fecha"] > marca]


nuevos = extraer_nuevos(origen, estado["marca"])
# ... aquí iría la carga ...
estado["marca"] = max(fila["fecha"] for fila in nuevos)
print("[paso 2]", [f["id"] for f in nuevos], "| nueva marca:", estado["marca"])
# SALIDA ESPERADA:
#   [paso 2] [4, 5, 6] | nueva marca: 2026-07-06

# 👉 TU TURNO 2: ejecuta extraer_nuevos otra vez sin datos nuevos en el origen.
#    El código de arriba falla al actualizar la marca. ¿Por qué? Arréglalo.


# REFLEXIONA: llega con retraso una fila con fecha 2026-07-02 (datos tardíos).
# ¿La recogerá este diseño? ¿Qué cambiarías? (Compara con reto_14.)


# ════════════════════════════════════════════════════════════════════
# PASO 3 — Cuarentena de filas malas (dead letter)
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: una fila mala no debe tumbar el lote ni desaparecer en silencio. Se
# aparta con su MOTIVO, el resto sigue, y alguien revisa la cuarentena.


def separar(filas):
    buenas, cuarentena = [], []
    for fila in filas:
        try:
            buenas.append({**fila, "monto": float(fila["monto"])})
        except (ValueError, TypeError) as error:
            cuarentena.append({**fila, "motivo": type(error).__name__})
    return buenas, cuarentena


buenas, cuarentena = separar([{"id": 1, "monto": "10"}, {"id": 2, "monto": "diez"}, {"id": 3, "monto": None}])
print("[paso 3]", len(buenas), cuarentena)
# SALIDA ESPERADA:
#   [paso 3] 1 [{'id': 2, 'monto': 'diez', 'motivo': 'ValueError'}, {'id': 3, 'monto': None, 'motivo': 'TypeError'}]

# 👉 TU TURNO 3: añade un UMBRAL: si más del 20 % del lote va a cuarentena, lanza
#    una excepción en lugar de continuar.


# REFLEXIONA: ¿por qué un 1 % de filas malas se aparta y un 60 % debe parar el job?


# ════════════════════════════════════════════════════════════════════
# PASO 4 — Write-Audit-Publish (escribir, auditar, publicar)
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: nunca escribas directo donde leen los usuarios. Escribe en un área
# temporal, VALIDA, y solo si pasa, publica con un cambio atómico (renombrar una
# tabla, mover un puntero). Si la validación falla, lo publicado sigue intacto.

publicado = {"ventas": [{"id": 1, "monto": 10}]}


def write_audit_publish(nombre, filas, validaciones):
    temporal = list(filas)  # WRITE
    fallos = [v.__name__ for v in validaciones if not v(temporal)]  # AUDIT
    if fallos:
        return f"rechazado: {fallos}"
    publicado[nombre] = temporal  # PUBLISH (atómico)
    return "publicado"


def no_vacio(filas):
    return len(filas) > 0


def montos_positivos(filas):
    return all(fila["monto"] > 0 for fila in filas)


print("[paso 4]", write_audit_publish("ventas", [{"id": 2, "monto": -1}], [no_vacio, montos_positivos]),
      "| sigue publicado:", publicado["ventas"])
# SALIDA ESPERADA:
#   [paso 4] rechazado: ['montos_positivos'] | sigue publicado: [{'id': 1, 'monto': 10}]

# 👉 TU TURNO 4: añade la validación «el lote nuevo no puede tener menos de la
#    mitad de filas que el publicado» (detecta cargas truncadas).


# REFLEXIONA: ¿cómo harías el paso PUBLISH atómico en PostgreSQL? ¿Y en S3?


# ════════════════════════════════════════════════════════════════════
# PASO 5 — Historial de cambios (SCD tipo 2)
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: si un cliente cambia de segmento y sobrescribes la fila (tipo 1),
# pierdes el pasado. En tipo 2 CIERRAS la versión vigente y AÑADES una nueva.

dim_cliente = [{"cliente_id": 1, "segmento": "basico", "desde": date(2024, 1, 1), "hasta": None}]


def aplicar_cambio(dim, cliente_id, segmento, hoy):
    vigente = next(f for f in dim if f["cliente_id"] == cliente_id and f["hasta"] is None)
    if vigente["segmento"] == segmento:
        return  # sin cambios: no se crea versión nueva
    vigente["hasta"] = hoy
    dim.append({"cliente_id": cliente_id, "segmento": segmento, "desde": hoy, "hasta": None})


aplicar_cambio(dim_cliente, 1, "premium", date(2026, 7, 1))
aplicar_cambio(dim_cliente, 1, "premium", date(2026, 8, 1))  # idempotente
print("[paso 5]", [(f["segmento"], str(f["desde"]), str(f["hasta"])) for f in dim_cliente])
# SALIDA ESPERADA:
#   [paso 5] [('basico', '2024-01-01', '2026-07-01'), ('premium', '2026-07-01', 'None')]

# 👉 TU TURNO 5: escribe segmento_en(dim, cliente_id, fecha) que devuelva el
#    segmento que tenía el cliente en una fecha dada.


# COMPRUEBA: segmento_en(dim_cliente, 1, date(2025, 5, 5)) == "basico"
# REFLEXIONA: una compra de 2025 de este cliente, ¿a qué segmento debe sumarse en
# un reporte histórico? ¿Con tipo 1 podrías responderlo?


# ════════════════════════════════════════════════════════════════════
# PASO 6 — Capas (arquitectura medallion)
# ════════════════════════════════════════════════════════════════════
# CONCEPTO (sin código):
#   bronze / raw     tal como llegó, inmutable, particionado por fecha de ingesta
#   silver / clean   tipos correctos, sin duplicados, validado
#   gold / analítica agregados y modelos listos para el negocio
# Regla: cada capa se puede RECONSTRUIR desde la anterior. Por eso raw no se toca.
#
# 👉 TU TURNO 6: en un comentario, coloca en su capa cada archivo y tabla de la
#    sección 04_pipelines (raw.movimientos, analitica.compras_elt, el CSV...).


# ════════════════════════════════════════════════════════════════════
# RETO DE LA LECCIÓN (usa los pasos 1 a 5)
# ════════════════════════════════════════════════════════════════════
# Con 06_ingenieria_de_datos/datos/transacciones_sucias.csv y PostgreSQL, construye
# una carga DIARIA que combine cuatro patrones:
#   - incremental por fecha con una tabla de control (paso 2),
#   - cuarentena con motivo y umbral (paso 3),
#   - write-audit-publish con una tabla temporal (paso 4),
#   - y que relanzar cualquier día deje el mismo resultado (paso 1).
# Demuéstralo: ejecuta tres días, repite el segundo y enseña los conteos.
