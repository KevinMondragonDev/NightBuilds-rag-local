"""
Tema 12 — Nube con Floci | Lección 4: Lambda y DynamoDB
=========================================================

En la lección 3 TÚ ejecutabas el consumidor. Con Lambda, la nube lo ejecuta por
ti cuando llega el evento: no hay servidor encendido esperando.

CÓMO USAR ESTA LECCIÓN: con Floci arrancado (lección 2).
    python 04_lambda_y_dynamodb.py
    La primera vez tarda (Floci descarga la imagen de Python para Lambda).

    Servicio   Idea
    ---------  ----------------------------------------------------------------
    Lambda     Una función que se ejecuta ante un evento; pagas por ejecución
    DynamoDB   Base NoSQL clave-valor: lecturas por clave en milisegundos

    pip install boto3

TIEMPO: 2.5 h · ANTES DE EMPEZAR: lección 3

CALENTAMIENTO (sin mirar apuntes, responde en un comentario antes de empezar):
    1. Recibir un mensaje de SQS, ¿lo borra? ¿Qué pasa si no lo borras?
    2. ¿Cuándo SQS y cuándo SNS?
    3. Un evento de S3, ¿trae el archivo o su clave? ¿Por qué?
"""

import io
import json
import os
import time
import zipfile

import boto3

ENDPOINT = os.environ.get("AWS_ENDPOINT_URL", "http://localhost:4566")


def cliente(servicio: str):
    return boto3.client(servicio, endpoint_url=ENDPOINT, region_name="us-east-1",
                        aws_access_key_id="test", aws_secret_access_key="test")


lam, dynamo, sqs = cliente("lambda"), cliente("dynamodb"), cliente("sqs")

# ════════════════════════════════════════════════════════════════════
# PASO 1 — Una función Lambda es un «handler» dentro de un zip
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: Lambda llama a handler(event, context). `event` es un dict con lo que
# disparó la función; lo que devuelves es la respuesta. El código se sube en un zip.

CODIGO = '''
def handler(event, context):
    montos = [m["monto"] for m in event.get("movimientos", [])]
    return {"cantidad": len(montos), "total": sum(montos)}
'''


def empaquetar(codigo: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        z.writestr("handler.py", codigo)
    return buffer.getvalue()


def desplegar(nombre: str, codigo: str, variables: dict | None = None) -> None:
    try:
        lam.delete_function(FunctionName=nombre)
    except lam.exceptions.ResourceNotFoundException:
        pass
    lam.create_function(
        FunctionName=nombre,
        Runtime="python3.12",
        Handler="handler.handler",                               # archivo.función
        Role="arn:aws:iam::000000000000:role/lambda-practica",   # en AWS real: un rol con permisos mínimos
        Code={"ZipFile": empaquetar(codigo)},
        Timeout=30,
        Environment={"Variables": variables or {}},
    )
    lam.get_waiter("function_active_v2").wait(FunctionName=nombre)


desplegar("sumar-movimientos", CODIGO)
respuesta = lam.invoke(FunctionName="sumar-movimientos",
                       Payload=json.dumps({"movimientos": [{"monto": 100}, {"monto": 50.5}]}))
print("[paso 1]", respuesta["StatusCode"], json.loads(respuesta["Payload"].read()))
# SALIDA ESPERADA:
#   [paso 1] 200 {'cantidad': 2, 'total': 150.5}

# 👉 TU TURNO 1: invoca la función con un movimiento sin la clave "monto".
#    ¿Qué StatusCode devuelve invoke? ¿Dónde aparece el error? (Mira la clave
#    FunctionError de la respuesta.) Arregla el handler para que lo ignore.


# REFLEXIONA: una Lambda no guarda nada entre ejecuciones. ¿Dónde pondrías un
# contador de «movimientos procesados hoy»?


# ════════════════════════════════════════════════════════════════════
# PASO 2 — DynamoDB: una tabla con clave
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: defines solo la CLAVE (partición y, opcional, orden). El resto de los
# atributos son libres. Se lee por clave; no hay JOIN. Se diseña pensando en las
# CONSULTAS que harás, al revés que en SQL.

TABLA = "resumen_cuentas"
try:
    dynamo.delete_table(TableName=TABLA)
except dynamo.exceptions.ResourceNotFoundException:
    pass
dynamo.create_table(
    TableName=TABLA,
    KeySchema=[{"AttributeName": "cuenta_id", "KeyType": "HASH"}],
    AttributeDefinitions=[{"AttributeName": "cuenta_id", "AttributeType": "N"}],
    BillingMode="PAY_PER_REQUEST",
)
dynamo.put_item(TableName=TABLA, Item={"cuenta_id": {"N": "7"}, "total": {"N": "0"}, "movimientos": {"N": "0"}})
dynamo.update_item(  # suma atómica: segura aunque haya varias Lambdas a la vez
    TableName=TABLA, Key={"cuenta_id": {"N": "7"}},
    UpdateExpression="ADD #t :monto, movimientos :uno",
    ExpressionAttributeNames={"#t": "total"},
    ExpressionAttributeValues={":monto": {"N": "250"}, ":uno": {"N": "1"}},
)
item = dynamo.get_item(TableName=TABLA, Key={"cuenta_id": {"N": "7"}})["Item"]
print("[paso 2]", {clave: valor["N"] for clave, valor in sorted(item.items())})
# SALIDA ESPERADA:
#   [paso 2] {'cuenta_id': '7', 'movimientos': '1', 'total': '250'}

# 👉 TU TURNO 2: repite el paso con el «recurso» de boto3
#    (boto3.resource("dynamodb", ...).Table(TABLA)), que evita escribir {"N": ...}.


# REFLEXIONA: «dame todas las cuentas con total > 10,000». ¿Se puede sin recorrer
# toda la tabla? ¿Qué te dice eso de cuándo usar DynamoDB y cuándo PostgreSQL?


# ════════════════════════════════════════════════════════════════════
# PASO 3 — Cola -> Lambda -> DynamoDB
# ════════════════════════════════════════════════════════════════════
# CONCEPTO: un «event source mapping» conecta una cola con una Lambda. La nube
# lee la cola, llama a tu función con un lote de mensajes en event["Records"] y,
# si la función termina bien, borra los mensajes por ti.
#
# DENTRO de la Lambda, «localhost» es el contenedor de la función, no tu máquina.
# El endpoint se le pasa por variable de entorno. Si este paso no conecta, revisa
# en la documentación de Floci qué nombre de host ven las funciones.

CODIGO_CONSUMIDOR = '''
import json, os, boto3

dynamo = boto3.client("dynamodb", endpoint_url=os.environ["ENDPOINT_INTERNO"], region_name="us-east-1",
                      aws_access_key_id="test", aws_secret_access_key="test")

def handler(event, context):
    for registro in event["Records"]:
        mov = json.loads(registro["body"])
        dynamo.update_item(
            TableName=os.environ["TABLA"], Key={"cuenta_id": {"N": str(mov["cuenta_id"])}},
            UpdateExpression="ADD #t :monto, movimientos :uno",
            ExpressionAttributeNames={"#t": "total"},
            ExpressionAttributeValues={":monto": {"N": str(mov["monto"])}, ":uno": {"N": "1"}},
        )
    return {"procesados": len(event["Records"])}
'''

ENDPOINT_INTERNO = os.environ.get("FLOCI_ENDPOINT_INTERNO", "http://host.docker.internal:4566")
desplegar("acumular-por-cuenta", CODIGO_CONSUMIDOR, {"TABLA": TABLA, "ENDPOINT_INTERNO": ENDPOINT_INTERNO})

try:
    sqs.delete_queue(QueueUrl=sqs.get_queue_url(QueueName="movimientos")["QueueUrl"])
except sqs.exceptions.QueueDoesNotExist:
    pass
cola = sqs.create_queue(QueueName="movimientos", Attributes={"VisibilityTimeout": "60"})["QueueUrl"]
cola_arn = sqs.get_queue_attributes(QueueUrl=cola, AttributeNames=["QueueArn"])["Attributes"]["QueueArn"]
lam.create_event_source_mapping(EventSourceArn=cola_arn, FunctionName="acumular-por-cuenta", BatchSize=5)

for monto in [100, 200, 300]:
    sqs.send_message(QueueUrl=cola, MessageBody=json.dumps({"cuenta_id": 9, "monto": monto}))

item = {}
for _ in range(30):  # la Lambda corre sola: esperamos a que termine
    item = dynamo.get_item(TableName=TABLA, Key={"cuenta_id": {"N": "9"}}).get("Item", {})
    if item.get("movimientos", {}).get("N") == "3":
        break
    time.sleep(1)
print("[paso 3]", {clave: valor["N"] for clave, valor in sorted(item.items())})
# SALIDA ESPERADA:
#   [paso 3] {'cuenta_id': '9', 'movimientos': '3', 'total': '600'}

# 👉 TU TURNO 3: mira los logs de la función:
#        aws logs describe-log-groups
#        aws logs tail /aws/lambda/acumular-por-cuenta
#    Añade un print al handler, vuelve a desplegar y encuéntralo en los logs.

# 👉 TU TURNO 4: envía un mensaje que no sea JSON. ¿Qué pasa con el lote entero?
#    Añade una DLQ a la cola (lección 3, paso 2) y comprueba que el mensaje malo
#    acaba ahí.


# REFLEXIONA: si la Lambda falla después de actualizar 2 de 5 mensajes, el lote
# se reintenta y esos 2 se suman otra vez. ¿Cómo lo harías idempotente?
# (Pista: guardar los id ya procesados, o una escritura condicional.)

# ════════════════════════════════════════════════════════════════════
# RETO DE LA LECCIÓN (pasos 1 a 3)
# ════════════════════════════════════════════════════════════════════
# Convierte en Lambda el consumidor del reto de la lección 3: S3 avisa a una cola,
# la cola dispara la función, la función valida el CSV y actualiza en DynamoDB un
# resumen por cuenta. Los mensajes que fallan dos veces van a una DLQ.
