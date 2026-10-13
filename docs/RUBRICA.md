# 📋 Rúbrica de sideprojects

Sirve para tres cosas: que sepas **antes de empezar** qué se espera, que te **autoevalúes** al terminar y que quien te revise use el mismo criterio contigo que con cualquier otra persona.

## Niveles

| Nivel | Significa |
|---|---|
| **4 · Destacado** | Va más allá de lo pedido y lo justifica |
| **3 · Logrado** | Cumple todo lo pedido. Es el objetivo |
| **2 · En desarrollo** | Funciona en el caso normal, pero falla o está incompleto en algo importante |
| **1 · Inicial** | No funciona de punta a punta, o no puede ejecutarlo otra persona |

## Criterios

| Criterio | 1 · Inicial | 2 · En desarrollo | 3 · Logrado | 4 · Destacado |
|---|---|---|---|---|
| **Funciona y es reproducible** | No se ejecuta siguiendo el README | Se ejecuta en la máquina del autor; a otra persona le faltan pasos | Clonar, instalar y ejecutar funciona con solo el README; todos los hitos pasan su «comprueba» | Además, un comando levanta todo (por ejemplo, `docker compose up`) |
| **Corrección de los datos** | Los resultados no se verificaron | Verificados a ojo en un caso | Las cifras de control cuadran (entrada = salida + rechazados) y hay comprobaciones automáticas | Además, relanzar no cambia el resultado y está demostrado |
| **Diseño y legibilidad** | Un archivo largo; nombres que no dicen nada | Dividido en funciones, pero mezclan responsabilidades | Funciones pequeñas con una tarea, nombres claros, configuración separada del código | Además, añadir un caso nuevo (fuente, regla, endpoint) no modifica código existente |
| **Robustez** | Un dato o una red mala lo rompe con un traceback | Maneja algún error, pero oculta otros o los ignora | Errores previsibles manejados con mensaje claro; nada se pierde en silencio; hay logging | Además, lo malo se aparta con su motivo y hay un umbral que detiene el proceso |
| **Pruebas** | Sin tests | Algún test del caso normal | Tests del caso normal, de bordes y de errores; pasan sin servicios externos | Además, se escribieron antes que el código en al menos una parte, o corren en CI |
| **Comunicación y defensa** | Sin README o sin explicar decisiones | README con cómo ejecutar, sin el porqué | README completo, y responde con sus palabras las «preguntas para defenderlo» | Además, explica el proyecto en 5 minutos y señala sus propias limitaciones |

## Cómo se usa

1. **Antes de empezar:** lee la columna «Logrado». Eso es lo que vas a construir.
2. **Al terminar:** márcate un nivel por criterio y escribe **una evidencia** de cada uno (un archivo, un comando, una captura). Sin evidencia, el nivel es el anterior.
3. **Revisión:** quien revisa hace lo mismo sin ver tu autoevaluación. Se comparan y se habla de las diferencias.
4. **Aprobado:** nivel 3 en «Funciona y es reproducible» y en «Corrección de los datos», y ningún criterio en 1. Lo que quede en 2 se corrige y se vuelve a revisar: un sideproject no se suspende, se mejora.

## Hoja de evaluación

| Criterio | Autoevaluación | Evidencia | Revisión | Qué mejorar |
|---|---|---|---|---|
| Funciona y es reproducible | | | | |
| Corrección de los datos | | | | |
| Diseño y legibilidad | | | | |
| Robustez | | | | |
| Pruebas | | | | |
| Comunicación y defensa | | | | |

## Integridad académica

El código lo escribes tú. Puedes consultar documentación, tus apuntes y a otras personas para **entender**; no para que lo hagan por ti. Si usaste una herramienta de IA para algo, dilo en el README y explica qué. La prueba es la defensa: lo que no puedas explicar línea a línea no cuenta como tuyo.
