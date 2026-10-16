---
name: git-documentacion
description: Administra git en el repositorio de documentación Obsidian (un vault/carpeta por proyecto) — sincroniza (pull), valida, agrupa los cambios en commits atómicos por proyecto con mensajes claros (Conventional Commits en español) redactados a partir de la documentación actualizada, y hace push de forma segura. Úsala cuando el usuario pida subir, guardar, sincronizar, hacer commit/push/pull de la documentación, preparar el repositorio git del vault, resolver un conflicto o deshacer un commit; y al terminar de documentar o actualizar un proyecto.
---

# Git para la documentación

> [!note] Cómo ejecutar los scripts de este plugin
> - Las rutas `scripts/…` y `../…` de este skill son **relativas a la carpeta de este `SKILL.md`**, no a la terminal (que arranca en el proyecto abierto). Antes de ejecutar, conviértelas a ruta absoluta, p. ej. `"<carpeta de este SKILL.md>/scripts/…"` o `"<carpeta de este SKILL.md>/../documentar-proyecto-obsidian/scripts/validar_vault.py"`.
> - Ubicación habitual del plugin: `%USERPROFILE%\.gemini\config\plugins\obsidian-docs` (Windows), `~/.gemini/config/plugins/obsidian-docs` (macOS/Linux) o `.agents/plugins/obsidian-docs` dentro del proyecto.
> - Donde dice `python3`: en **Windows** usa `py -3` (o `python` si `py` no existe); en macOS/Linux, `python3`.

El historial de git es **la bitácora del proyecto**: alguien que lea `git log` (o el dashboard) debe entender qué cambió en la documentación **sin abrir los archivos**.

Modelo: **un repositorio, una carpeta por proyecto, y cada carpeta es un vault independiente** (con su propio `.obsidian`). Nunca un `.obsidian` en la raíz del repo a la vez que en los proyectos (vaults anidados): `preparar` y `estado` lo detectan.

Herramienta: `scripts/git_vault.py` (Python 3.8+, solo librería estándar). En los comandos, `<repo>` es la raíz del repositorio de documentación.

## Reglas de oro (no negociables)

1. **Nunca** `git push --force`, `git reset --hard`, `git clean -fd`, `git checkout -- .` ni `git rebase -i` sobre commits ya subidos sin que el usuario lo pida explícitamente y entienda que se pierde información. Para deshacer algo ya subido: `git revert`.
2. **Nunca** commit con secretos o datos personales. Si `estado` o el hook los detectan: reemplazar por `<SECRETO: ver gestor de claves>` y volver a revisar.
3. **Nunca** `git add .` ni `git add -A` a ciegas: agrega **rutas explícitas** de cada grupo (`git add -- "<ruta1>" "<ruta2>"`).
4. **Un commit = un proyecto = una intención.** No mezclar proyectos en un commit; separar la configuración del vault (`chore(vault)`).
5. **Sincroniza antes de trabajar y antes de subir** (`pull --rebase`). Historia lineal, sin commits "Merge branch…".
6. **No inventes el "por qué"** de un commit: tómalo del Historial de cambios, de los ADR, de lo que dijo el usuario o pregúntalo.
7. **Push solo con confirmación** del usuario, salvo que haya pedido explícitamente "haz commit y push sin preguntar".

## Flujo A · Primera vez (preparar el repositorio)

```bash
python3 scripts/git_vault.py preparar "<repo>"            # repositorio existente
python3 scripts/git_vault.py preparar "<repo>" --init --remoto "<URL>"   # crear uno nuevo
python3 scripts/git_vault.py instalar-hooks "<repo>"
```

- `preparar` crea/completa `.gitignore` (excluye `workspace.json`, `.trash/`, temporales) y `.gitattributes` (finales de línea LF, binarios) y configura git: `pull.rebase`, `rebase.autoStash`, `core.quotepath=false` (tildes legibles), `push.autoSetupRemote`.
- `instalar-hooks` hace que **cada commit** (también los hechos a mano o desde el plugin Obsidian Git) valide el mensaje y bloquee secretos y archivos > 50 MB.
- Si falta la identidad (`user.name` / `user.email`), pídela al usuario; no la inventes.
- Haz el primer commit de configuración: `chore(vault): configura git para Obsidian`.

## Flujo A2 · Ya existe un vault local y un repositorio remoto vacío o recién creado

Caso típico: el vault está en una carpeta del equipo (sin git) y en GitHub / Azure DevOps / Gitea ya se creó el repositorio.
**No** hagas `git init` dentro del vault y luego `push`: si el remoto se creó con README o .gitignore, el push falla por "historias no relacionadas". El camino seguro es **clonar y mover**:

1. Confirma con el usuario: URL del remoto, carpeta del vault, nombre del proyecto y si el repositorio se abrirá en Obsidian **completo** (un vault con todos los proyectos) o **por proyecto**.
2. Revisa el vault antes de subir nada con `python3 ../documentar-proyecto-obsidian/scripts/validar_vault.py "<vault>"` (también detecta secretos) y quítalos antes de seguir.
3. Clona el remoto en una carpeta **nueva** (el usuario inicia sesión si git lo pide):
   `git clone "<URL>" "<carpeta-del-repo>"`
4. **Copia** (no muevas todavía) el vault completo, **incluida su carpeta `.obsidian`**, dentro del repo como carpeta del proyecto: `<carpeta-del-repo>/<Nombre del proyecto>/`. Modelo del repositorio: **un vault por proyecto** — no debe existir `.obsidian` en la raíz del repo.
5. `python3 scripts/git_vault.py preparar "<carpeta-del-repo>"` y `instalar-hooks`.
6. Commits (flujo C), normalmente dos: `chore(vault): configura git para Obsidian` y `feat(<proyecto>): crea la documentación de <Proyecto>`.
7. `git push -u origin main` (si la rama del remoto se llama distinto, usa la que trae el clon).
8. El usuario abre en Obsidian la carpeta del **proyecto** dentro del repo (*Abrir carpeta como vault*) y verifica que todo se ve igual. Solo entonces puede archivar o borrar la carpeta original **él mismo**.

Si el remoto está totalmente vacío también funciona clonar (git avisa que el repositorio está vacío; es normal).

## Flujo B · Antes de documentar (sincronizar)

```bash
python3 scripts/git_vault.py estado "<repo>" --fetch
```

| Si ves… | Haz |
|---|---|
| `⬇️ N commits por traer` y sin cambios locales | `git pull --rebase` |
| `⬇️ N commits por traer` y con cambios locales | `git pull --rebase` (el autostash guarda y reaplica tus cambios). Si hay conflicto → `references/solucion-problemas.md` |
| `🛑 rebase/merge en curso` o conflictos | Resolver primero (ver referencia). No empezar a documentar encima |
| Todo al día | Continúa |

## Flujo C · Guardar y subir cambios (el principal)

1. **Revisar** — `python3 scripts/git_vault.py estado "<repo>" --fetch --json`
   Obtienes los cambios **agrupados por proyecto**, con un borrador de mensaje por grupo, secciones nuevas/quitadas, cambios de estado (borrador → vigente), renombrados, posibles secretos y archivos pesados. Código de salida 1 = hay conflictos o secretos: resolver antes de seguir.
2. **Validar la documentación** de cada proyecto con cambios:
   `python3 ../documentar-proyecto-obsidian/scripts/validar_vault.py "<repo>/<proyecto>"`
   (cada proyecto es un vault independiente: un `[[enlace]]` a otro proyecto cuenta como roto)
   - Errores de seguridad → bloquean.
   - Otros errores (enlaces rotos, frontmatter) → corrígelos si son tuyos; si no, infórmalos y pregunta si se sube igual.
3. **Redactar el mensaje de cada grupo.** El borrador es un punto de partida: **lee el diff real** (`git diff -- "<rutas>"`, y para archivos nuevos el contenido) y la entrada más reciente de `Historial de cambios.md` del proyecto. Escribe según `references/convencion-commits.md`:
   - Cabecera `tipo(proyecto): descripción` ≤ 72 caracteres, en minúscula, sin punto, que diga **qué** cambió.
   - Cuerpo **Qué cambió** (viñetas por nota, en lenguaje llano) + **Por qué** (el motivo) + pies opcionales (`Refs: ADR-004`, `Pendiente:`).
   - Si el cambio afecta a quien usa el sistema/proceso, agrega **Impacto:** en una línea (igual a "⚠️ Cambia para ti" del Historial).
4. **Mostrar el plan al usuario** en una tabla: grupo · archivos · mensaje completo. Espera su "sí" (o ajustes).
5. **Hacer los commits**, uno por grupo, en este orden: `chore(vault)` → proyectos en orden alfabético:
   ```bash
   git add -- "<ruta1>" "<ruta2>"          # rutas del grupo (incluye la ruta anterior en renombrados)
   git commit -F "<archivo-mensaje.txt>"   # escribe el mensaje en un archivo UTF-8: soporta tildes y varias líneas
   ```
   Si un hook rechaza el commit, **lee el motivo, corrige y reintenta**. No uses `--no-verify` salvo que el usuario lo pida.
6. **Subir**:
   ```bash
   git pull --rebase      # por si alguien subió algo mientras tanto
   git push
   ```
   Si el push es rechazado (`fetch first` / `non-fast-forward`): repetir `git pull --rebase` + `git push`. Nunca forzar.
7. **Informar**: lista de commits (`git log --oneline -n <N>`), confirmación de que quedaron en el remoto (`⬆️ 0 commits sin subir`), y sugiere regenerar el dashboard (`generar-dashboard.bat`).

## Ramas: ¿directo a main o rama + PR?

| Situación | Estrategia |
|---|---|
| Una persona, cambios normales | Directo a `main` |
| Equipo, cambios pequeños (correcciones, actualizaciones de cifras) | Directo a `main` con `pull --rebase` antes del push |
| Reestructuración (mover carpetas, > 10 notas, renombrar proyecto) o documentación que debe aprobar otra persona | Rama `docs/<proyecto>/<tema>` (ej. `docs/informe-junta/nuevo-modelo-costos`) + Pull Request. Al aprobar: *squash merge* con mensaje que cumpla la convención |
| `main` protegida en el servidor | Siempre rama + PR |

## Versiones (opcional)

Cuando la documentación corresponde a una entrega formal (fin de proyecto, versión de software, auditoría), crea una etiqueta anotada por proyecto:
```bash
git tag -a "informe-junta/v1.0" -m "Documentación entregada a la junta de octubre 2026"
git push origin "informe-junta/v1.0"
```

## Recursos
- `references/convencion-commits.md` — tipos, reglas y **ejemplos buenos y malos** para cada caso.
- `references/solucion-problemas.md` — conflictos, deshacer commits, recuperar archivos, secretos ya subidos, archivos pesados.
- `scripts/git_vault.py` — `preparar`, `estado`, `validar-mensaje`, `escanear-secretos`, `instalar-hooks`.
