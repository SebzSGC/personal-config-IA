---
name: dashboard-documentacion
description: Genera el dashboard de la documentación (un solo HTML interactivo que abre con doble clic) con el estado de todos los proyectos del repositorio de Obsidian — salud, grafo de notas, enlaces rotos, cambios recientes, pendientes, y la pestaña de requerimientos con cronograma y tablero. Úsala cuando el usuario pida el dashboard, ver el estado de la documentación o de las historias de todos los proyectos, y al final del Cierre de flujo-documentacion.
---

# Dashboard de la documentación

> [!note] Cómo ejecutar los scripts de este plugin
> - Las rutas `scripts/…` y `../…` de este skill son **relativas a la carpeta de este `SKILL.md`**, no a la terminal (que arranca en el proyecto abierto). Antes de ejecutar, conviértelas a ruta absoluta, p. ej. `"<carpeta de este SKILL.md>/scripts/…"` o `"<carpeta de este SKILL.md>/../documentar-proyecto-obsidian/scripts/validar_vault.py"`.
> - Ubicación habitual del plugin: `%USERPROFILE%\.gemini\config\plugins\obsidian-docs` (Windows), `~/.gemini/config/plugins/obsidian-docs` (macOS/Linux) o `.agents/plugins/obsidian-docs` dentro del proyecto.
> - Donde dice `python3`: en **Windows** usa `py -3` (o `python` si `py` no existe); en macOS/Linux, `python3`.

Solo necesita **Python 3.8+** y git: la interfaz ya viene compilada en `assets/plantilla.html` y el script le inyecta los datos. No hace falta Node ni `npm install`.

## Generar

```bash
python3 scripts/generar_dashboard.py --repo "<repositorio de documentación>" [--abrir]
```

| Opción | Para qué |
|---|---|
| `--repo` | Carpeta del repositorio de documentación. Si no se pasa, la toma de `.obsidian-docs.json` (vínculo del proyecto actual) o de `~/.obsidian-docs.json` → `repoDocumentacion` |
| `--salida` | Dónde guardar el HTML. Por defecto, `Dashboard documentación.html` en el Escritorio |
| `--titulo`, `--modo proyecto\|repo` | Título y modo de vault (`proyecto`: un vault por carpeta, lo normal) |
| `--pull` | `git pull --ff-only` antes de escanear |
| `--abrir` | Abre el HTML al terminar |
| `--json <archivo>` | Guarda también los datos del escaneo (útil para revisar o depurar) |

Las opciones fijas del equipo van en `<repo de docs>/.obsidian-docs.json`:

```json
{ "dashboard": { "titulo": "Documentación Invamer", "modoVault": "proyecto", "pullAntes": false } }
```

En Windows también se puede generar con doble clic en `generar-dashboard.cmd` (raíz del repo `personal-config-IA`).

## Qué contarle al usuario

Después de generarlo, resume en 2–4 líneas lo que muestra la salida del script (una línea por proyecto con notas, enlaces rotos, huérfanas y salud) y señala lo que pide atención: salud < 65, enlaces rotos, historias vencidas o bloqueadas. No describas la interfaz; remite al archivo.

## Reglas

- El HTML es un archivo **generado**: no lo guardes dentro del repositorio de documentación ni le hagas commit (cambia en cada generación y solo produce ruido y conflictos). Si el usuario lo quiere compartir, que lo envíe él.
- Los datos salen del frontmatter y de git. Si algo se ve mal en el dashboard, se corrige en las notas (o con `requerimientos.py`), nunca editando el HTML.
- Los estados y el avance de las historias usan las mismas reglas que `requerimientos.py` (`escanear.py` las importa de ahí): el tablero del vault y el dashboard siempre dicen lo mismo.

## Recursos
- `scripts/generar_dashboard.py` — genera el HTML.
- `scripts/escanear.py` — escanea el repositorio y produce el JSON (se puede usar solo: `--repo … --salida datos.json`).
- `assets/plantilla.html` — interfaz compilada. Su código fuente está en `herramientas/vault-dashboard/` del repo `personal-config-IA`; se actualiza con `npm run publicar`.
