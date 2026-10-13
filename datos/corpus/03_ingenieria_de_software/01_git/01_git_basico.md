# 🌱 Git básico

> **Objetivo:** guardar el historial de un proyecto y moverte por él con seguridad.
> **Tiempo:** 1.5 h · **Antes de empezar:** ninguno

**Calentamiento (sin mirar apuntes):**
1. ¿Qué diferencia hay entre guardar un archivo y hacer un commit?
2. ¿Qué comando de Git evitas hoy porque no terminas de entenderlo?
3. Nombra tres cosas que nunca deberían subirse a un repositorio.

---

## Teoría

Git guarda **fotos** (commits) del proyecto. Un archivo pasa por tres zonas:

```
directorio de trabajo ──git add──► staging ──git commit──► repositorio
```

| Comando | Para qué |
|---|---|
| `git init` | Crear un repositorio en la carpeta actual |
| `git status` | Qué cambió y en qué zona está |
| `git add archivo` / `git add -p` | Pasar cambios a staging (todo el archivo o por trozos) |
| `git commit -m "mensaje"` | Guardar la foto |
| `git diff` / `git diff --staged` | Cambios sin preparar / ya preparados |
| `git log --oneline --graph` | Historial |
| `git show <commit>` | Qué cambió en un commit |
| `git restore archivo` | Descartar cambios del directorio de trabajo |
| `git restore --staged archivo` | Sacar de staging sin perder los cambios |
| `git revert <commit>` | Crear un commit que deshace otro |

`.gitignore` lista lo que **nunca** se sube: datos, `.env`, `__pycache__/`, `.venv/`.

Un buen mensaje de commit: verbo en imperativo, un solo cambio, menos de 60 caracteres.
`Añade validación de montos negativos`, no `cambios` ni `arreglos varios`.

## Ejercicios

Trabaja en una carpeta nueva fuera de este repositorio (`mkdir ~/practica_git`).

1. Crea el repositorio, añade un `limpieza.py` con una función vacía y haz el primer commit. Comprueba con `git log --oneline` que aparece.
2. Modifica el archivo dos veces más, con un commit por cambio. Antes de cada `git add`, lee `git diff`.
3. Haz dos cambios **no relacionados** en el mismo archivo y guárdalos en **dos commits separados** con `git add -p`.
4. Crea `datos.csv` y `.env` con cualquier contenido. Consigue que `git status` no los muestre.
5. Rompe `limpieza.py` a propósito:
   - Sin haber hecho `add`: recupéralo.
   - Después de `add`: sácalo de staging y recupéralo.
   - Después de `commit`: deshaz el commit **sin borrar historial**.
6. Encuentra con `git log` (busca la opción adecuada) el commit en el que apareció por primera vez una línea concreta.

## Comprueba

```bash
git log --oneline        # al menos 6 commits, cada mensaje describe un cambio
git status               # "nothing to commit, working tree clean"
git check-ignore .env    # imprime .env
```

## Pregunta para pensar

`git revert` y `git reset --hard` deshacen un commit. ¿Cuál usarías en una rama que ya subiste y comparte tu equipo? ¿Por qué?

<details>
<summary>💡 Pista</summary>

- Ejercicio 3: en `git add -p`, `s` divide un trozo y `y`/`n` lo aceptan o lo saltan.
- Ejercicio 6: mira `git log -S`.

</details>
