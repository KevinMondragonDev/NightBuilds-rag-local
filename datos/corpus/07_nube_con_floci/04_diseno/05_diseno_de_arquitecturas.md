# 📐 Diseñar en la nube (y comprobarlo en Floci)

> **Objetivo:** pasar de «sé usar S3 y SQS» a «sé decidir qué servicios usar y por qué». Es lo que evalúa una entrevista de diseño.
> **Tiempo:** 2 h · **Antes de empezar:** lecciones 1 a 4

**Calentamiento (sin mirar apuntes):**
1. ¿Cuándo SQS y cuándo SNS?
2. Da un caso en el que Lambda no sirve.
3. ¿Cuándo DynamoDB y cuándo PostgreSQL?

---

## El método en 6 pasos

Úsalo siempre en este orden. Los tres primeros son **sin código**.

| # | Paso | Pregunta que respondes |
|---|---|---|
| 1 | **Requisitos** | ¿Cuántos datos, cada cuánto, qué tan rápido se necesitan, quién los consume, qué pasa si se pierden? |
| 2 | **Diagrama** | Cajas (servicios) y flechas (datos). Si no cabe en una hoja, simplifica. |
| 3 | **Decisiones** | Por cada caja: qué alternativa descartaste y por qué. |
| 4 | **Fallos** | Recorre cada flecha: ¿qué pasa si falla aquí? ¿Se reintenta, se pierde, se duplica? |
| 5 | **Prototipo en Floci** | Crea los recursos con un script y pasa un dato de punta a punta. |
| 6 | **Lo que Floci no te dice** | Costo, permisos reales (IAM), límites y latencia: se estiman o se prueban en AWS. |

## Tabla de decisión rápida

| Necesitas… | Usa | Y no… | Porque |
|---|---|---|---|
| Guardar archivos de cualquier tamaño | S3 | una base de datos | barato, ilimitado, lo leen Spark y Athena |
| Desacoplar quien produce de quien procesa | SQS | una llamada directa | si el consumidor cae, los mensajes esperan |
| Avisar a varios sistemas del mismo hecho | SNS → varias SQS | una cola compartida | cada consumidor va a su ritmo |
| Código corto ante un evento (< 15 min) | Lambda | un servidor encendido | pagas por ejecución |
| Proceso largo o pesado | ECS / EMR / Glue | Lambda | límite de tiempo y memoria |
| Leer por clave en milisegundos | DynamoDB | PostgreSQL | escala sin administrar |
| Consultas con JOIN y agregados | PostgreSQL (RDS) / Redshift | DynamoDB | no hay JOIN en DynamoDB |
| SQL sobre archivos de S3 | Athena | cargar todo en una base | no hay servidor que mantener |
| Varios pasos con dependencias | Step Functions / Airflow (MWAA) | Lambdas que se llaman entre sí | reintentos e historial visibles |
| Guardar una contraseña | Secrets Manager | una variable en el código | rotación y auditoría |

## Paso a paso guiado: un ejemplo resuelto a medias

**Caso:** cada sucursal sube al final del día un CSV de movimientos. Finanzas quiere el resumen por cuenta disponible en una API antes de las 7:00.

1. **Requisitos** (ya respondidos): 200 archivos/día, ~5 MB cada uno, lote diario, tolerancia cero a perder un archivo, duplicados no aceptables.
2. **Diagrama:**

   ```
   sucursal ──CSV──► S3 (raw) ──evento──► SQS ──► Lambda (valida y agrega) ──► DynamoDB ──► API
                                           │                                │
                                           └──► DLQ (archivos que fallan)   └──► S3 (clean, Parquet)
   ```

3. **Decisiones:** 👉 **tu turno.** Completa la tabla.

   | Caja | Alternativa descartada | Por qué |
   |---|---|---|
   | SQS entre S3 y Lambda | S3 → Lambda directo | |
   | Lambda | un servidor con cron | |
   | DynamoDB | PostgreSQL | |
   | Parquet en clean | CSV | |

4. **Fallos:** 👉 **tu turno.** ¿Qué pasa si…?
   - la Lambda falla a la mitad de un archivo
   - el mismo archivo se sube dos veces
   - llega un archivo con el doble de columnas
   - DynamoDB rechaza escrituras durante un minuto

5. **Prototipo:** 👉 **tu turno.** Escribe `infra.py` que cree todos los recursos en Floci (bucket, colas, tabla, función y conexiones) y que se pueda ejecutar dos veces sin fallar. Después sube un CSV y comprueba que el resumen aparece en DynamoDB.

6. **Lo que Floci no te dice:** 👉 **tu turno.** Con la [calculadora de precios de AWS](https://calculator.aws/), estima el costo mensual de este diseño. ¿Qué servicio pesa más?

## Katas de diseño

Aplica los 6 pasos. Entrega por cada una: una hoja con el diagrama, la tabla de decisiones y la lista de fallos. Prototipa en Floci solo la que más te interese.

1. **Tipo de cambio diario.** Una función descarga cada mañana el tipo de cambio de una API y lo deja disponible para otros pipelines. La API a veces no responde.
2. **Alertas de fraude.** Cada compra de más de $50,000 debe generar un aviso en menos de un minuto a dos equipos distintos, sin que uno dependa del otro.
3. **Reprocesar un año.** Descubres un error en la limpieza. Hay que volver a procesar 365 días de archivos sin afectar a la carga diaria.
4. **De lote a casi tiempo real.** El resumen diario ahora se quiere cada 5 minutos. ¿Qué cajas cambian y cuáles se quedan?

## Límites de un emulador

- **Permisos:** Floci acepta cualquier credencial y, por defecto, no aplica las políticas de IAM. En AWS, un permiso que falta es el error más común. Escribe igualmente la política mínima de cada pieza: qué acciones, sobre qué recurso.
- **Rendimiento y costo:** no son representativos.
- **Detalles:** nombres de bucket únicos en todo el mundo, cuotas, consistencia y latencia entre regiones solo existen en AWS.

Cuando un diseño te funcione aquí, llévalo a la **capa gratuita de AWS** con un presupuesto y una alerta de facturación, y bórralo al terminar.

## Pregunta para pensar

¿Cuál de tus diseños seguiría funcionando igual si mañana cambias AWS por Google Cloud? ¿Qué parte de tu código lo permite? (Repasa Repository y Adapter en `05_patrones_de_diseno/01_patrones_de_codigo/02`.)
