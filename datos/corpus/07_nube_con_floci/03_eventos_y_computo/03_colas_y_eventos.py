"""
Tema 12 — Nube con Floci | Lección 3: Colas y eventos (SQS, SNS, eventos de S3)
=================================================================================

Hasta ahora tus pipelines corren «a una hora». En la nube muchos corren «cuando
pasa algo»: llega un archivo, se crea un pedido. Para eso existen las colas.

CÓMO USAR ESTA LECCIÓN: con Floci arrancado (lección 2).
    python 03_colas_y_eventos.py        # tarda unos 10 s: hay esperas a propósito

    Servicio  Idea                                   Analogía
    --------  -------------------------------------  ---------------------------
    SQS       Cola: un mensaje lo procesa UN lector  La fila de una ventanilla
    SNS       Tema: un mensaje llega a TODOS         Un altavoz
    S3 events S3 avisa cuando se crea un objeto      El timbre de la puerta

    pip install boto3

TIEMPO: 2 h · ANTES DE EMPEZAR: lección 2

CALENTAMIENTO (sin mirar apuntes, responde en un comentario antes de empezar):
    1. ¿Qué es la clave de un objeto en S3? ¿Hay carpetas?
    2. ¿Qué cambia en tu código entre Floci y AWS real?
    3. ¿Qué es la cuarentena (dead letter) en un pipeline y para qué sirve el umbral?
"""

import json
import os
import time

import boto3

ENDPOINT = os.environ.get("AWS_ENDPOINT_URL", "http://localhost:4566")


def cliente(servicio: str):
    return boto3.client(servicio, endpoint_url=ENDPOINT, region_name="us-east-1",
                        aws_access_key_id="test", aws_secret_access_key="test")


sqs, sns, s3 = cliente("sqs"), cliente("sns"), cliente("s3")


def crear_cola(nombre: str, **atributos) -> tuple[str, str]:
    """Crea (o recrea vacía) una cola y devuelve su URL y su ARN."""
    try:
        sqs.delete_queue(QueueUrl=sqs.get_queue_url(QueueName=nombre)["QueueUrl"])
    except sqs.exceptions.QueueDoesNotExist:
        pass
    url = sqs.create_queue(QueueName=nombre, Attributes=atributos)["QueueUrl"]
    arn = sqs.get_queue_attributes(QueueUrl=url, AttributeNames=["QueueArn"])["Attributes"]["QueueArn"]
    return url, arn


# ════════════════════════════════════════════════════════════════════
# PASO 1 — Enviar, recibir y BORRAR
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: recibir un mensaje NO lo elimina. Queda oculto un tiempo (visibility
# timeout). Si el lector lo procesa bien, lo borra. Si el lector muere, el mensaje
# reaparece y otro lo intenta. Así no se pierde trabajo.

cola, _ = crear_cola("pagos", VisibilityTimeout="1")
sqs.send_message(QueueUrl=cola, MessageBody=json.dumps({"pago_id": 1, "monto": 250}))

mensaje = sqs.receive_message(QueueUrl=cola, WaitTimeSeconds=1)["Messages"][0]
print("[paso 1] recibido:", mensaje["Body"])
time.sleep(1.5)  # el lector «muere» sin borrar: pasa el visibility timeout
otra_vez = sqs.receive_message(QueueUrl=cola, WaitTimeSeconds=1)["Messages"][0]
print("[paso 1] reaparece:", otra_vez["Body"])
sqs.delete_message(QueueUrl=cola, ReceiptHandle=otra_vez["ReceiptHandle"])
print("[paso 1] tras borrar:", sqs.receive_message(QueueUrl=cola, WaitTimeSeconds=1).get("Messages", []))
# SALIDA ESPERADA:
#   [paso 1] recibido: {"pago_id": 1, "monto": 250}
#   [paso 1] reaparece: {"pago_id": 1, "monto": 250}
#   [paso 1] tras borrar: []

# 👉 TU TURNO 1: envía 5 mensajes y escribe un consumidor: un bucle que recibe
#    (hasta 10 por llamada, con WaitTimeSeconds), procesa (print) y borra, hasta
#    que la cola quede vacía.


# REFLEXIONA: el mismo pago se recibió DOS veces. Si «procesar» es cobrar, ¿qué
# propiedad debe tener tu código? (05_patrones_de_diseno/02_patrones_de_datos/03, paso 1.)


# ════════════════════════════════════════════════════════════════════
# PASO 2 — Cola de mensajes muertos (DLQ)
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: un mensaje que siempre falla («veneno») bloquearía la cola para
# siempre. Con una política de reenvío, tras N intentos fallidos pasa a OTRA cola
# para revisarlo. Es la cuarentena de 05_patrones_de_diseno/02_patrones_de_datos/03 (paso 3), en la nube.

dlq, dlq_arn = crear_cola("pagos-dlq")
cola, _ = crear_cola("pagos", VisibilityTimeout="1",
                     RedrivePolicy=json.dumps({"deadLetterTargetArn": dlq_arn, "maxReceiveCount": "2"}))
sqs.send_message(QueueUrl=cola, MessageBody="esto no es JSON")

for intento in range(1, 4):
    mensajes = sqs.receive_message(QueueUrl=cola, WaitTimeSeconds=1).get("Messages", [])
    print(f"[paso 2] intento {intento}:", [m["Body"] for m in mensajes])  # «falla»: no se borra
    time.sleep(1.5)
muertos = sqs.receive_message(QueueUrl=dlq, WaitTimeSeconds=1).get("Messages", [])
print("[paso 2] en la DLQ:", [m["Body"] for m in muertos])
# SALIDA ESPERADA:
#   [paso 2] intento 1: ['esto no es JSON']
#   [paso 2] intento 2: ['esto no es JSON']
#   [paso 2] intento 3: []
#   [paso 2] en la DLQ: ['esto no es JSON']

# 👉 TU TURNO 2: mezcla 3 mensajes válidos y 1 inválido. Tu consumidor del turno 1
#    debe procesar y borrar los válidos y dejar que el inválido acabe en la DLQ
#    sin detenerse.


# ════════════════════════════════════════════════════════════════════
# PASO 3 — Un mensaje, varios destinos (SNS -> SQS, «fan-out»)
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: quien publica no sabe quién escucha. Añadir un consumidor nuevo es
# añadir una suscripción, sin tocar al que publica. Es el patrón Observer.

tema = sns.create_topic(Name="movimientos")["TopicArn"]
for nombre in ["auditoria", "antifraude"]:
    _, arn = crear_cola(nombre)
    sns.subscribe(TopicArn=tema, Protocol="sqs", Endpoint=arn, Attributes={"RawMessageDelivery": "true"})

sns.publish(TopicArn=tema, Message=json.dumps({"movimiento_id": 42}))
for nombre in ["auditoria", "antifraude"]:
    url = sqs.get_queue_url(QueueName=nombre)["QueueUrl"]
    print(f"[paso 3] {nombre}:", [m["Body"] for m in sqs.receive_message(QueueUrl=url, WaitTimeSeconds=2).get("Messages", [])])
# SALIDA ESPERADA:
#   [paso 3] auditoria: ['{"movimiento_id": 42}']
#   [paso 3] antifraude: ['{"movimiento_id": 42}']

# 👉 TU TURNO 3: añade una tercera cola «notificaciones» que SOLO reciba los
#    movimientos de tipo compra (busca FilterPolicy y MessageAttributes).


# ════════════════════════════════════════════════════════════════════
# PASO 4 — S3 avisa cuando llega un archivo
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: en lugar de preguntar cada 5 minutos «¿hay archivos nuevos?», S3
# publica un evento por cada objeto creado. Así empieza un pipeline dirigido por eventos.

BUCKET = "banco-entrada"
entrada, entrada_arn = crear_cola("archivos-nuevos")
try:
    s3.create_bucket(Bucket=BUCKET)
except s3.exceptions.BucketAlreadyOwnedByYou:
    pass
s3.put_bucket_notification_configuration(
    Bucket=BUCKET,
    NotificationConfiguration={"QueueConfigurations": [{"QueueArn": entrada_arn, "Events": ["s3:ObjectCreated:*"]}]},
)
s3.put_object(Bucket=BUCKET, Key="movimientos/fecha=2026-07-01/parte-0.csv", Body=b"id,monto\n1,10\n")

evento = json.loads(sqs.receive_message(QueueUrl=entrada, WaitTimeSeconds=3)["Messages"][0]["Body"])
registro = evento["Records"][0]
print("[paso 4]", registro["eventName"], registro["s3"]["bucket"]["name"], registro["s3"]["object"]["key"])
# SALIDA ESPERADA:
#   [paso 4] ObjectCreated:Put banco-entrada movimientos/fecha=2026-07-01/parte-0.csv

# 👉 TU TURNO 4: escribe un consumidor que, por cada evento, descargue el objeto
#    de S3, cuente sus filas y lo imprima. Sube tres archivos y obsérvalo.
#    Las claves con caracteres especiales llegan codificadas (prueba «fecha=...»
#    en AWS real): usa urllib.parse.unquote_plus.


# REFLEXIONA: el evento trae la CLAVE del archivo, no su contenido. ¿Por qué es
# buena idea? (Es la misma razón por la que en Airflow se pasan rutas entre tareas.)

# ════════════════════════════════════════════════════════════════════
# RETO DE LA LECCIÓN (pasos 1 a 4)
# ════════════════════════════════════════════════════════════════════
# Mini pipeline dirigido por eventos, todo en Floci:
#   subes un CSV a banco-entrada -> evento en una cola -> tu consumidor lo valida
#   -> si es válido lo escribe en Parquet en banco-clean; si no, el mensaje acaba
#   en una DLQ. Publica en un tema SNS «archivo_procesado» con el nº de filas.
# Demuéstralo con dos archivos buenos y uno roto.
