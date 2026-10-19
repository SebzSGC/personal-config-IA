---
name: dashboard-documentacion
description: Genera el dashboard de la documentación (un solo HTML interactivo que abre con doble clic) con el estado de todos los proyectos del repositorio de vaults de Obsidian — salud, grafo de notas, enlaces rotos, cambios recientes, pendientes, y la pestaña de requerimientos con cronograma y tablero. Úsala cuando el usuario pida el dashboard, ver el estado de la documentación o de las historias de todos los proyectos, indique en qué repositorio guarda sus vaults, y al final del Cierre de flujo-documentacion.
---

# Dashboard de la documentación

> [!note] Cómo ejecutar los scripts de este plugin
> - Las rutas `scripts/…` y `../…` de este skill son **relativas a la carpeta de este `SKILL.md`**, no a la terminal (que arranca en el proyecto abierto). Antes de ejecutar, conviértelas a ruta absoluta, p. ej. `"<carpeta de este SKILL.md>/scripts/…"` o `"<carpeta de este SKILL.md>/../documentar-proyecto-obsidian/scripts/validar_vault.py"`.
> - Ubicación del plugin: en **Claude Code**, `${CLAUDE_PLUGIN_ROOT}`. En **Antigravity**, `%USERPROFILE%\.gemini\config\plugins\obsidian-docs` (Windows), `~/.gemini/config/plugins/obsidian-docs` (macOS/Linux) o `.agents/plugins/obsidian-docs` dentro del proyecto.
> - Donde dice `python3`: en **Windows** usa `py -3` (o `python` si `py` no existe); en macOS/Linux, `python3`.

El dashboard **vive en el repositorio de vaults** (un repo git con un vault de Obsidian por carpeta), no en este plugin. Este skill aporta el motor (escaneo y generación); el repo de vaults aporta la interfaz y recibe el resultado:

```
<repo de vaults>/
├── .obsidian-docs.json   ← opciones del dashboard (opcional)
├── _dashboard/
│   ├── plantilla.html    ← interfaz compilada (va a git)
│   ├── fuente/           ← código React de la interfaz (va a git)
│   ├── generar-dashboard.cmd / .sh · generar.py   ← doble clic
│   └── Dashboard.html    ← resultado (en .gitignore)
└── <Proyecto A>/ <Proyecto B>/ …
```

Solo necesita **Python 3.8+** y git. No hace falta Node.

## 1 · Saber cuál es el repositorio de vaults

El repositorio queda anotado una sola vez por equipo en `~/.obsidian-docs.json` → `repoDocumentacion` (es la misma clave que usa `vinculo.py vincular`).

- Si el usuario **indica** el repositorio ("mis vaults están en `C:\Users\yo\documentacion`"), regístralo con `--guardar` en el paso 2.
- Si no lo indica, ejecuta el paso 2 **sin** `--repo`: el script lo toma del proyecto actual (`.obsidian-docs.json`) o de `~/.obsidian-docs.json`.
- Si responde `❌ No sé cuál es tu repositorio de vaults`, **pregúntale al usuario** en qué carpeta (repo git) guarda sus vaults. Si aún no lo tiene clonado en este equipo, que te dé la URL y clónalo con el skill `git-documentacion`. Luego repite con `--repo "<ruta>" --guardar`.

## 2 · Generar

```bash
python3 scripts/generar_dashboard.py [--repo "<repo de vaults>" --guardar] [--abrir]
```

| Opción | Para qué |
|---|---|
| `--repo` · `--guardar` | Repositorio de vaults; con `--guardar` queda recordado para la próxima vez |
| `--salida` | Dónde guardar el HTML. Por defecto `<repo de vaults>/_dashboard/Dashboard.html` |
| `--titulo`, `--modo proyecto\|repo` | Título y modo de vault (`proyecto`: un vault por carpeta, lo normal) |
| `--pull` | `git pull --ff-only` antes de escanear |
| `--abrir` | Abre el HTML al terminar |
| `--json <archivo>` | Guarda también los datos del escaneo (útil para depurar) |

Las opciones fijas del equipo van en `<repo de vaults>/.obsidian-docs.json`:

```json
{ "dashboard": { "titulo": "Documentación Invamer", "modoVault": "proyecto", "pullAntes": false } }
```

Si el script dice que el repositorio **no tiene `_dashboard/plantilla.html`**, ese repo aún no tiene la carpeta del dashboard: díselo al usuario y que copie `_dashboard/` desde otro repo de vaults suyo (no la inventes ni la recrees).

El usuario también puede generarlo sin el agente con doble clic en `_dashboard/generar-dashboard.cmd` (o `.sh`) del repo de vaults.

## Qué contarle al usuario

Resume en 2–4 líneas lo que muestra la salida del script (una línea por proyecto con notas, enlaces rotos, huérfanas y salud) y señala lo que pide atención: salud < 65, enlaces rotos, historias vencidas o bloqueadas. No describas la interfaz; remite al archivo.

## Reglas

- `Dashboard.html` es un archivo **generado**: está en `_dashboard/.gitignore`; nunca le hagas commit. Si el usuario lo quiere compartir, que lo envíe él.
- Los datos salen del frontmatter y de git. Si algo se ve mal en el dashboard, se corrige en las notas (o con `requerimientos.py`), nunca editando el HTML.
- Los estados y el avance de las historias usan las mismas reglas que `requerimientos.py` (`escanear.py` las importa de ahí): el tablero del vault y el dashboard siempre dicen lo mismo.
- Para cambiar la **interfaz**, se edita `_dashboard/fuente/` del repo de vaults y se compila con `npm run publicar` (ver `_dashboard/README.md`); commit de `fuente/` y `plantilla.html` juntos.

## Recursos
- `scripts/generar_dashboard.py` — genera el HTML en el repo de vaults y recuerda el repo (`--guardar`).
- `scripts/escanear.py` — escanea el repositorio y produce el JSON (se puede usar solo: `--repo … --salida datos.json`).
