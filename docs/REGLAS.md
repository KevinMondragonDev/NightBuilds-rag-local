# 🚀 Sideprojects: cómo se trabajan

Cada módulo del repositorio termina con un **reto de sideproject**: un proyecto pequeño pero completo (un ETL o una API) que vive en **su propio repositorio**, con el nombre que indica el reto y siempre con el prefijo `sideproject-`.

La diferencia con un ejercicio: un ejercicio demuestra que entendiste un tema; un sideproject demuestra que sabes **juntar varios** y terminar algo que otra persona puede clonar y ejecutar.

## Reglas

1. **Sin solución.** Los retos dan el caso, los hitos y cómo comprobar cada uno. El diseño es tuyo.
2. **Por hitos.** Cada hito es pequeño y deja algo que funciona. Un commit (o más) por hito. No empieces el siguiente sin pasar el «comprueba» del actual.
3. **Sin IA para escribir el código.** Documentación y tus apuntes, sí. Si te atoras más de 30 minutos, anota la duda y pide una revisión con preguntas, no la respuesta.
4. **Datos de práctica, dicho con claridad.** En el README pones de dónde salen los datos. Nada de «en producción».
5. **Terminado es mejor que perfecto.** Primero todos los hitos; después «Súbelo de nivel».

## El README de cada sideproject

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
