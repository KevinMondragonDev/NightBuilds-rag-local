# 🧠 Reto 4 — RAG local: el pipeline de datos de un asistente

**Repositorio:** `sideproject-rag-local` · **Nivel:** avanzado · **Entorno:** PostgreSQL con `pgvector`, embeddings locales y un modelo de lenguaje local · **Método y evaluación:** [`README.md`](docs/METODO.md)

## El caso

Los estudiantes de este programa preguntan una y otra vez lo mismo: «¿dónde se explica la idempotencia?», «¿qué diferencia hay entre SQS y SNS?». Quieren un asistente que responda **citando la lección exacta**. El modelo de lenguaje ya existe; lo que falta, y lo que decide si el asistente acierta o inventa, es el pipeline de datos que le da el contexto correcto. Ese pipeline es tu trabajo.

RAG significa «generación aumentada por recuperación»: antes de responder, el sistema **busca** los fragmentos relevantes y se los entrega al modelo.

## Lo que debe existir al terminar

- **Ingesta** de un corpus de documentos con sus metadatos (archivo, sección, fecha).
- **Troceado** justificado: probaste al menos dos estrategias y mediste cuál recupera mejor.
- **Embeddings calculados en local** y guardados en PostgreSQL con `pgvector`.
- **Recarga incremental:** si cambia un documento, solo se recalculan sus fragmentos; si se borra, desaparecen.
- **Una API** con dos operaciones: buscar (devuelve fragmentos y puntuación) y preguntar (devuelve respuesta **con sus fuentes**).
- **Evaluación:** un conjunto de al menos 30 preguntas con la fuente correcta, y la métrica de cuántas veces esa fuente aparece entre los primeros resultados.
- **Una visualización en D3.js:** la calidad de recuperación de cada versión del pipeline y, para una pregunta, qué fragmentos se recuperaron y con qué puntuación.

## Datos

El propio repositorio del programa: sus lecciones en `.md` y `.py`. Es público, está en español y tú sabes cuáles son las respuestas correctas.

## Restricciones

- **Todo en local y sin pagar:** nada de APIs de pago. El servicio de modelos del emulador de AWS no devuelve resultados reales, así que no sirve.
- La parte de **generación** con un modelo de lenguaje local (por ejemplo con Ollama) no está comprobada en este programa: instalarlo y elegir un modelo que quepa en tu máquina es parte del reto. Si tu equipo no puede con ello, el reto sigue siendo válido entregando solo la recuperación y su evaluación.
- Ninguna respuesta sin fuente. Si no hay contexto suficiente, el asistente dice que no lo sabe.
- La evaluación se ejecuta con un comando y da un número.

## Preguntas que tu diseño debe responder

- ¿De qué tamaño son los fragmentos y por qué? ¿Se solapan?
- ¿Qué pasa si cambias de modelo de embeddings? ¿Qué hay que recalcular?
- ¿Cómo distingues un fallo de **recuperación** (no encontró el fragmento) de uno de **generación** (lo encontró y respondió mal)?
- ¿Qué índice usa la búsqueda y cuándo empezaría a hacer falta?

## Defensa: lo que te van a preguntar

- Haznos una pregunta cuya respuesta **no** está en el corpus. ¿Qué responde?
- Cambia una lección delante de nosotros. ¿Cuánto tarda en reflejarse y qué se recalculó?
- Enséñanos una pregunta que falla y explica en cuál de los pasos falla.

## Súbelo de nivel

- Búsqueda híbrida: combina similitud vectorial con búsqueda por palabras de PostgreSQL y mide si mejora.
- Añade un segundo corpus en MongoDB (documentos con estructura distinta) sin tocar el resto del pipeline.
- Filtra por metadatos: «solo en el módulo 05».
