# Solución de problemas con git

> [!warning] Antes de cualquier comando que reescriba historia o descarte cambios, explica al usuario qué se perderá y espera su confirmación.

## 🔀 Conflicto al hacer `pull --rebase`

**Qué pasó:** tú y otra persona cambiaron las mismas líneas de una nota.

1. Ver qué archivos chocan: `git status` (aparecen como *both modified*).
2. Abrir cada archivo. Git marca el choque así:
   ```
   <<<<<<< HEAD
   versión que ya estaba en el remoto
   =======
   tu versión
   >>>>>>> docs(informe-junta): actualiza cifras
   ```
3. Dejar el texto correcto (normalmente **combinar ambas**: en documentación rara vez una versión anula a la otra) y borrar las marcas `<<<<<<<`, `=======`, `>>>>>>>`.
   - En el **frontmatter**: conservar la fecha `actualizado` más reciente y unir las `etiquetas`.
   - En **`.canvas`** (JSON): no mezclar a mano si es complejo; quedarse con una versión (`git checkout --theirs` o `--ours` *durante el rebase*: `--ours` = remoto, `--theirs` = tu commit) y volver a agregar a mano lo que falte en Obsidian.
4. `git add -- "<archivo>"` y `git rebase --continue`.
5. Validar el proyecto con `validar_vault.py` y luego `git push`.

Para abandonar y volver a como estaba antes del pull: `git rebase --abort`.

## ↩️ Deshacer

| Situación | Comando | ¿Pierde algo? |
|---|---|---|
| Cambié una nota y quiero volver a la última versión guardada | `git restore -- "<archivo>"` | ⚠️ Sí, los cambios sin commit de ese archivo |
| Agregué (`git add`) algo que no quería en el commit | `git restore --staged -- "<archivo>"` | No |
| Último commit **no subido** con mensaje mal escrito | `git commit --amend` | No |
| Último commit **no subido** sobra por completo | `git reset --soft HEAD~1` (los cambios quedan preparados) | No |
| Commit **ya subido** que estaba mal | `git revert <hash>` → crea un commit que lo deshace | No (queda en el historial) |
| Recuperar una nota borrada hace tiempo | `git log --diff-filter=D --oneline -- "*Nombre*"` y luego `git restore --source=<hash>~1 -- "<ruta>"` | No |
| Ver una versión vieja de una nota | `git log --oneline -- "<ruta>"` y `git show <hash>:"<ruta>"` | No |

Nunca `git push --force` en `main`. Si de verdad hay que reescribir una rama propia ya subida: `git push --force-with-lease` y solo con aprobación explícita.

## 🔐 Se subió un secreto

1. **Rotar el secreto ya** (cambiar la contraseña/token en el sistema real): borrar el commit no basta, ya pudo ser copiado.
2. Quitarlo de la nota (`<SECRETO: ver gestor de claves>`) y hacer commit `fix(<proyecto>): elimina credencial expuesta`.
3. Si además hay que borrarlo del historial (repositorio compartido fuera de la empresa), eso requiere `git filter-repo` y que todo el equipo vuelva a clonar: escalar al responsable de TI, no hacerlo sin coordinación.

## 🐘 Archivo muy pesado

- > 10 MB: aviso. > 50 MB: el hook bloquea el commit. GitHub rechaza archivos > 100 MB.
- Opciones: comprimir la imagen/PDF; guardarlo en SharePoint/Drive y enlazarlo desde la nota; o activar **Git LFS** (`git lfs install` y `git lfs track "*.pbix"`) si el servidor lo soporta.
- Si ya está en un commit local no subido: `git reset --soft HEAD~1`, quitarlo, volver a hacer commit.

## 🔑 El push pide usuario y contraseña / "Authentication failed"

- GitHub y Azure DevOps ya no aceptan la contraseña de la cuenta: se usa el **Git Credential Manager** (viene con Git para Windows; abre el navegador para iniciar sesión) o un token personal.
- No pidas ni escribas la contraseña o el token del usuario: indícale que inicie sesión él mismo cuando git lo solicite.

## 📛 Tildes o ñ aparecen como `\303\261`

`git config core.quotepath false` (lo hace `git_vault.py preparar`).

## 🪟 Avisos "LF will be replaced by CRLF"

Inofensivos. `.gitattributes` (creado por `preparar`) normaliza a LF en el repositorio; Obsidian lee ambos formatos.

## 📱 Obsidian Git y este skill a la vez

Son compatibles: ambos usan el mismo repositorio. Recomendaciones:
- En Obsidian Git, configura el mensaje de auto-commit con la convención o desactiva el auto-commit y deja que este skill haga los commits con buen mensaje.
- Los hooks instalados también validan los commits que haga Obsidian Git: si su mensaje por defecto (`vault backup: …`) no cumple, cámbialo en sus ajustes a algo como `chore(vault): respaldo automático {{date}}`.
