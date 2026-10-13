# 🚀 NightBuilds: cómo se trabajan

Cada módulo del programa, y cada sección del módulo 05, termina con un **NightBuild**: un proyecto completo (un ETL o una API) que vive en **su propio repositorio**, con el nombre que indica el reto.

Hay dos tamaños, y el prefijo del repositorio dice cuál es:

| Categoría | Prefijo | Tamaño | Qué es |
|---|---|---|---|
| **DevSandbox** | `DevSandbox-` | Hasta 8 h | Un proyecto pequeño para practicar un tema: un espacio para probar, equivocarte y terminar rápido |
| **NightBuilds** | `NightBuilds-` | 8 h o más | Un proyecto grande, con varias piezas (base de datos, orquestador, nube, API) y decisiones de diseño |

Las reglas, el README y la rúbrica son los mismos para los dos; en este documento «NightBuild» se refiere a cualquiera de ellos.

La diferencia con un ejercicio: un ejercicio demuestra que entendiste un tema; un NightBuild demuestra que sabes **juntar varios** y terminar algo que otra persona puede clonar y ejecutar.

## Reglas

1. **Sin solución.** Los retos dan el caso, los hitos y cómo comprobar cada uno. El diseño es tuyo.
2. **Por hitos.** Cada hito es pequeño y deja algo que funciona. Un commit (o más) por hito. No empieces el siguiente sin pasar el «comprueba» del actual.
3. **Sin IA para escribir el código.** Documentación y tus apuntes, sí. Si te atoras más de 30 minutos, anota la duda y pide una revisión con preguntas, no la respuesta.
4. **Datos de práctica, dicho con claridad.** En el README pones de dónde salen los datos. Nada de «en producción».
5. **Terminado es mejor que perfecto.** Primero todos los hitos; después «Súbelo de nivel».

## El README de cada NightBuild

| Sección | Contenido |
|---|---|
| Qué hace | Dos frases y un diagrama (a mano y fotografiado, vale) |
| Cómo se ejecuta | Los comandos exactos, desde `git clone` |
| Decisiones | 3 decisiones técnicas y la alternativa que descartaste |
| Qué aprendí | Lo que más te costó |
| Siguiente paso | Qué harías con una semana más |

## Cómo se evalúa

Con [`RUBRICA.md`](RUBRICA.md): seis criterios, cuatro niveles. Úsala primero para autoevaluarte y después para la revisión.

## Antes de darlo por terminado

- [ ] En una carpeta nueva: `git clone`, instalar y ejecutar funciona siguiendo solo el README.
- [ ] Los tests pasan.
- [ ] No hay contraseñas ni datos personales en el historial (`git log -p`).
- [ ] Puedes explicarlo en 5 minutos sin mirar el código.
- [ ] Respondiste las «preguntas para defenderlo» del reto.

## Mapa de NightBuilds

En el orden en que se hacen. Cada uno tiene su carpeta y su repositorio con el mismo nombre.

| Módulo | Repositorio | Categoría | Tipo |
|---|---|---|---|
| `01_fundamentos` | `DevSandbox-estado-de-cuenta` | DevSandbox | ETL en Python puro |
| `02_funciones_y_poo` | `DevSandbox-validador-de-datos` | DevSandbox | Biblioteca + ETL |
| `03_python_para_datos` | `DevSandbox-tipo-de-cambio` | DevSandbox | ETL + análisis + tablero |
| `04_retos_de_python` | `DevSandbox-monitor-de-logs` | DevSandbox | ETL incremental |
| `05/01_ingesta_de_datos` | `DevSandbox-ingesta-multifuente` | DevSandbox | ETL (extracción) |
| `05/02_limpieza_y_eficiencia` | `DevSandbox-calidad-de-datos` | DevSandbox | ETL (limpieza) |
| `05/03_ingenieria_de_software` | `DevSandbox-limpiador` | DevSandbox | Paquete instalable |
| `05/04_pipelines` | `NightBuilds-pipeline-banco` | NightBuilds | ETL orquestado con Airflow |
| `05/05_patrones_de_diseno` | `NightBuilds-mini-framework-etl` | NightBuilds | Framework de ETL |
| `05/06_apis_con_fastapi` | `NightBuilds-api-banco` | NightBuilds | API REST |
| `05/07_nube_con_floci` | `NightBuilds-data-lake-eventos` | NightBuilds | ETL por eventos + API, en Floci |
| `05/08_python_tipado_y_arquitectura_limpia` | `NightBuilds-guardia-de-prompts` | NightBuilds | Servicio de seguridad delante de un modelo de lenguaje |
| `06_spark` | `NightBuilds-lakehouse-spark` | NightBuilds | ETL distribuido |
| `07_retos_de_integracion` | `NightBuilds-ingesta-s3` | NightBuilds | ETL en la nube (Floci) |
| `08_capstone` | Uno de seis: `NightBuilds-data-lake`, `-data-warehouse`, `-etl-produccion`, `-rag-local`, `-tiempo-real` o `-gobierno-de-datos` | NightBuilds | Problema abierto, con API y visualización en D3.js |
