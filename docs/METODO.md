# 07 — Capstone: retos de la industria

El cierre del programa. Aquí ya no hay pasos ni hitos marcados: recibes un problema como los que resuelve un equipo de datos, y tú decides el alcance, el diseño y cómo demostrar que funciona.

Los retos salen de lo que más piden las vacantes de Data Engineer en 2026 (pipelines, SQL, AWS, modelado, calidad de datos, lakehouse y, en crecimiento, datos para IA) y todos se pueden hacer **en tu máquina y sin pagar nada**.

## Los retos

Elige **uno**. Si quieres un portafolio completo, el orden recomendado es 2 → 1 → 6 → 3 → 4 → 5.

| # | Reto | Repositorio | Construyes | Nivel |
|---|---|---|---|---|
| 1 | Data lake en AWS local | `sideproject-data-lake` | Capas en S3, catálogo, consultas SQL sobre Parquet y un tablero | Intermedio |
| 2 | Data warehouse con dbt | `sideproject-data-warehouse` | Modelo estrella en PostgreSQL, en estilo ELT, con pruebas y un cuadro de mando | Intermedio |
| 3 | Un ETL a producción | `sideproject-etl-produccion` | Un pipeline tuyo convertido en algo desplegable, vigilado y seguro | Avanzado |
| 4 | RAG local | `sideproject-rag-local` | El pipeline de datos de un asistente que responde sobre documentos, todo en local | Avanzado |
| 5 | Casi tiempo real | `sideproject-tiempo-real` | Eventos que llegan sin parar, procesados y dibujados en vivo | Avanzado |
| 6 | Gobierno de datos | `sideproject-gobierno-de-datos` | Inventario de datos personales, hallazgos de una auditoría y controles que se aplican solos | Intermedio |

Todos terminan igual: **los datos se sirven con una API y se muestran en una visualización interactiva con D3.js**. Un pipeline que nadie puede ver no convence a nadie.

## Relación con la maestría

Cada reto pone a trabajar asignaturas de la Maestría en Análisis y Visualización de Datos Masivos:

| Asignatura | Dónde se usa |
|---|---|
| Bases de Datos para Datos Masivos | Reto 4 (documentos y vectores) y reto 5 (Redis) |
| Gobierno del Dato y Toma de Decisiones | Reto 6 entero, reto 2 (indicadores y cuadro de mando) y reto 3 (datos personales, permisos) |
| Técnicas de Inteligencia Artificial | Reto 4 |
| Ingeniería para el Procesado Masivo de Datos | Reto 1 (y Spark como extensión) |
| Visualización Interactiva de la Información · Herramientas de Visualización | Todos: la entrega final es en D3.js |

## Lo que está comprobado que funciona en local

Probado con Floci (emulador de AWS), PostgreSQL 17 y un modelo de embeddings local, el 12 de octubre de 2026:

| Pieza | Funciona | Límite que debes conocer |
|---|---|---|
| S3 + catálogo de Glue + consultas con Athena sobre Parquet particionado | Sí; los resultados coinciden con pandas | Las particiones se detectan solas (`MSCK REPAIR` no existe) y Athena no crea tablas con `CREATE TABLE … WITH (…) AS`: las capas las escribe tu código |
| Step Functions (orquestación) | Sí | — |
| Secrets Manager | Sí | — |
| SQS, SNS, Lambda, DynamoDB | Sí (sección `06/07_nube_con_floci`) | — |
| Redshift | A medias | Por dentro es PostgreSQL: acepta SQL normal, pero no `COPY` desde S3. **Por eso el warehouse se hace directamente en PostgreSQL** |
| Bedrock (modelos de IA) | No sirve | Devuelve respuestas vacías. **Por eso el RAG usa modelos locales** |
| Búsqueda por similitud con `pgvector` y embeddings locales (`fastembed`, modelo multilingüe) | Sí, en español | El modelo se descarga la primera vez (unos 20 s) |
| Generar la respuesta con un modelo de lenguaje local (Ollama) | **Sin comprobar** | Requiere instalar Ollama y descargar un modelo de varios GB |

## Antes de empezar

Necesitas tener hecho el módulo `06_ingenieria_de_datos` completo. Además, cada reto usa temas que el programa **todavía no enseña** con lecciones propias; hasta que existan, tendrás que aprenderlos con la documentación oficial:

| Tema | Lo necesitan | Lección en el programa |
|---|---|---|
| SQL intermedio y modelado dimensional | Retos 1, 2 y 3 | Pendiente |
| dbt | Reto 2 | Pendiente |
| Docker y `docker compose` | Todos | Pendiente (se usa, pero no se explica) |
| Infraestructura como código y CI/CD | Reto 3 | Pendiente |
| Embeddings y búsqueda vectorial | Reto 4 | Pendiente |
| D3.js básico | Todos | Pendiente (lo cubre la asignatura de visualización de la maestría) |

## Cómo se trabaja un reto

En lugar de hitos, cinco **entregas**. Cada una se revisa antes de pasar a la siguiente.

| # | Entrega | Qué presentas |
|---|---|---|
| 1 | **Planteamiento** | Una página: para quién es, qué pregunta responde, qué queda fuera, y cómo sabrás que funciona |
| 2 | **Diseño** | Diagrama, tabla de decisiones (qué elegiste y qué descartaste) y lista de fallos previstos, con el método de `06/07_nube_con_floci/05` |
| 3 | **Datos fluyendo** | El dato viaja de punta a punta, aunque sea feo. Un comando lo levanta todo |
| 4 | **Producto** | La API y la visualización en D3.js, con pruebas y comprobaciones de calidad |
| 5 | **Defensa** | Diez minutos: demostración en vivo, una decisión difícil, una limitación y qué harías con un mes más |

Duración orientativa: **3 a 4 semanas** a 10 h por semana. Mejor en equipos de 2 o 3; también se puede hacer solo, recortando el alcance en la entrega 1.

## Cómo se evalúa

Con [`RUBRICA.md`](RUBRICA.md) y dos criterios más:

| Criterio | 1 · Inicial | 2 · En desarrollo | 3 · Logrado | 4 · Destacado |
|---|---|---|---|---|
| **Alcance y criterio** | Intenta todo y no termina nada | Termina, pero sin justificar qué dejó fuera | Alcance realista, decidido al inicio y cumplido | Además, recortó a mitad de camino y explica por qué fue la decisión correcta |
| **Visualización** | Muestra una tabla | Una gráfica que no responde a la pregunta del planteamiento | Interactiva, legible y responde a la pregunta; lee de la API, no de un archivo | Además, alguien ajeno saca la conclusión sin explicación |

Las reglas de trabajo y de integridad académica son las de [`SIDEPROJECTS.md`](REGLAS.md).

## Datos

Cada reto indica los suyos. Regla general: **datos públicos o sintéticos, nunca de tu trabajo**, y el README dice de dónde salen.

| Reto | Datos | Dónde |
|---|---|---|
| 1 Data lake | Viajes de taxi de Nueva York (público, unos 59 MB por mes) | Enlaces en el reto |
| 2 Data warehouse | Banco histórico: 60,000 movimientos y cambios de segmento (sintético) | `datos/banco_historico/` |
| 3 ETL a producción | Los de tu pipeline de partida | Tu `sideproject-pipeline-banco` |
| 4 RAG local | Las lecciones de este repositorio | El propio repositorio |
| 5 Casi tiempo real | Fuente de eventos continua (sintético) | `datos/eventos/generar_eventos.py` |
| 6 Gobierno de datos | Clientes con datos personales, accesos, solicitudes ARCO y notas de soporte (sintético) | `datos/gobierno/` |

`datos/generar_datos_proyectos.py` regenera los archivos sintéticos. **No lo abras si vas a hacer el reto 6 o el sideproject de ingesta a S3**: ahí se ve qué problemas esconden los datos.
