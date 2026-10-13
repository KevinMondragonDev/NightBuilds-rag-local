# 🌿 Git: ramas, conflictos y remotos

> **Objetivo:** trabajar en paralelo sin romper `main` y colaborar a través de GitHub.
> **Tiempo:** 1.5 h · **Antes de empezar:** lección 1

**Calentamiento (sin mirar apuntes):**
1. Las tres zonas por las que pasa un archivo en Git.
2. ¿Qué diferencia hay entre `git restore` y `git revert`?
3. ¿Para qué sirve `git add -p`?

---

## Teoría

Una **rama** es un puntero a un commit. Crear una es instantáneo y no copia archivos.

| Comando | Para qué |
|---|---|
| `git switch -c nombre` | Crear una rama y pasar a ella |
| `git switch main` | Cambiar de rama |
| `git branch -v` | Ver ramas |
| `git merge nombre` | Traer otra rama a la actual |
| `git branch -d nombre` | Borrar una rama ya fusionada |
| `git stash` / `git stash pop` | Guardar cambios a medias y recuperarlos |

**Conflicto:** dos ramas cambiaron las mismas líneas. Git marca el archivo:

```
<<<<<<< HEAD
lo que hay en tu rama
=======
lo que viene de la otra
>>>>>>> otra-rama
```

Editas el archivo hasta dejarlo como debe quedar, `git add` y `git commit`.

**Remotos:**

| Comando | Para qué |
|---|---|
| `git clone <url>` | Copiar un repositorio |
| `git remote -v` | Ver remotos |
| `git push -u origin rama` | Subir una rama por primera vez |
| `git fetch` | Traer cambios sin tocar tus archivos |
| `git pull` | `fetch` + `merge` |

**Flujo de trabajo habitual (GitHub flow):** rama corta desde `main` → commits → `push` → *pull request* → revisión → merge → borrar la rama.

## Ejercicios

Sigue en `~/practica_git`.

1. Crea la rama `regla-duplicados`, añade una función y haz commit. Vuelve a `main`: ¿está la función? Fusiona y comprueba.
2. Provoca un **conflicto**: desde `main`, crea dos ramas que cambien la **misma línea** de formas distintas. Fusiona la primera, luego la segunda. Resuélvelo conservando lo mejor de ambas.
3. Con cambios a medias en una rama, te piden un arreglo urgente en `main`. Usa `git stash`, haz el arreglo y recupera tu trabajo.
4. Crea un repositorio vacío en GitHub, conéctalo como `origin` y sube `main`.
5. **Pull request contigo mismo:** crea una rama, súbela, abre un PR en GitHub, deja un comentario en una línea, corrígelo con otro commit y fusiona desde GitHub. Trae el resultado a tu máquina.
6. Simula a un compañero: edita un archivo desde la web de GitHub. En local, edita **otra** línea del mismo archivo y haz commit. Intenta `git push`. ¿Qué dice? Resuélvelo.

## Comprueba

```bash
git log --oneline --graph --all   # se ven las ramas y los merges
git branch -a                     # no quedan ramas ya fusionadas
git status                        # "Your branch is up to date with 'origin/main'"
```

## Pregunta para pensar

En el ejercicio 6 podías usar `git pull` (merge) o `git pull --rebase`. ¿En qué se diferencia el historial que deja cada uno?

<details>
<summary>💡 Pista</summary>

- Ejercicio 2: después de editar el archivo, busca que no quede ningún `<<<<<<<`.
- Ejercicio 4: `git remote add origin <url>` y `git push -u origin main`.

</details>
