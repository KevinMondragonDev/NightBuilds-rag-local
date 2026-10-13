# ☁️ Computación en la nube (conceptos)

> **Objetivo:** entender el vocabulario de la nube que aparece en cualquier pipeline de datos. Sin código.
> **Tiempo:** 1 h · **Antes de empezar:** la sección `04_pipelines`

**Calentamiento (sin mirar apuntes):**
1. Nombra tres servicios en la nube que uses a diario (correo, almacenamiento, vídeo…). ¿Dónde crees que se ejecutan?
2. ¿Dónde se ejecuta hoy tu pipeline de la sección de pipelines y quién lo enciende?
3. ¿Qué pasaría con ese pipeline si tu portátil se apaga?

---

## Teoría

**Nube** = alquilar cómputo, almacenamiento y servicios por internet y pagar por uso, en lugar de comprar y mantener servidores.

| Modelo | Qué alquilas | Tú gestionas | Ejemplos |
|---|---|---|---|
| **IaaS** | Máquinas, redes, discos | Sistema operativo, software, datos | EC2, Compute Engine |
| **PaaS** | Una plataforma lista | Tu código y tus datos | Elastic Beanstalk, App Engine, RDS |
| **SaaS** | La aplicación terminada | Solo tus datos | Gmail, Snowflake, Power BI |

| Despliegue | Qué es |
|---|---|
| **Pública** | Infraestructura del proveedor, compartida |
| **Privada** | Infraestructura dedicada a una organización |
| **Híbrida** | Mezcla de ambas |
| **Multinube** | Varios proveedores a la vez |

**Conceptos clave**

- **Escalabilidad:** vertical (máquina más grande) u horizontal (más máquinas).
- **Elasticidad:** escalar sola, hacia arriba y hacia abajo, según la demanda.
- **Región y zona de disponibilidad:** dónde están físicamente los datos. Afecta a latencia, costo y cumplimiento legal.
- **Responsabilidad compartida:** el proveedor asegura la nube; tú aseguras lo que pones dentro (accesos, cifrado, datos).
- **CapEx frente a OpEx:** inversión inicial frente a gasto mensual.
- **Serverless:** no gestionas servidores y pagas por ejecución (Lambda, Athena, EMR Serverless).

**Servicios de datos equivalentes**

| Necesidad | AWS | Azure | Google Cloud |
|---|---|---|---|
| Almacenamiento de objetos | S3 | Blob Storage | Cloud Storage |
| Data warehouse | Redshift | Synapse | BigQuery |
| Spark gestionado | EMR / Glue | HDInsight / Databricks | Dataproc |
| Orquestación | MWAA / Step Functions | Data Factory | Cloud Composer |
| Base relacional gestionada | RDS | Azure SQL | Cloud SQL |
| Identidad y permisos | IAM | Entra ID | IAM |

## Ejercicios

Responde por escrito, con tus palabras, en un archivo `respuestas_nube.md`.

1. Clasifica como IaaS, PaaS o SaaS: una máquina EC2, PostgreSQL en RDS, Snowflake, AWS Lambda, Databricks, un bucket de S3. Justifica las dudosas.
2. Tu pipeline procesa 50 GB cada noche durante 20 minutos y el resto del día no hace nada. ¿Servidor encendido 24 h o serverless? Argumenta con costo y operación.
3. Un banco mexicano quiere guardar datos de clientes en la nube. ¿Qué tres preguntas harías antes de elegir la región?
4. Según la responsabilidad compartida, ¿quién responde si…?
   - se quema un disco del centro de datos
   - un bucket queda público por error
   - se filtra una clave de acceso subida a GitHub
5. Dibuja (a mano vale) dónde viviría en AWS cada pieza de tus DevSandbox de ingesta y calidad de datos: datos crudos, datos limpios, el código, la base de datos y el programador de tareas.

## Pregunta para pensar

«La nube siempre es más barata.» ¿En qué caso sería falso?

## Conecta con el resto del repositorio

- `07_retos_de_integracion/reto_15` y `reto_16`: S3 con `boto3`.
- `06_spark/01_ruta_sparksql/fase_10_despliegue_cluster`: Spark en clúster.
