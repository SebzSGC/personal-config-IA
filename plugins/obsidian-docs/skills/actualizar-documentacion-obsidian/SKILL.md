---
name: actualizar-documentacion-obsidian
description: Actualiza la documentación existente (y el avance de las historias de usuario relacionadas) de un proyecto en un Vault de Obsidian después de cambios en el código, el proceso o los datos (nueva funcionalidad, cambio de arquitectura, nueva versión, incidente). Úsala cuando el usuario diga que algo cambió y hay que reflejarlo en el vault, pida "sincronizar la documentación", registrar una versión, una decisión (ADR) o un incidente.
---

# Actualizar documentación en Obsidian

> [!note] Cómo ejecutar los scripts de este plugin
> - Las rutas `scripts/…` y `../…` de este skill son **relativas a la carpeta de este `SKILL.md`**, no a la terminal (que arranca en el proyecto abierto). Antes de ejecutar, conviértelas a ruta absoluta, p. ej. `"<carpeta de este SKILL.md>/scripts/…"` o `"<carpeta de este SKILL.md>/../documentar-proyecto-obsidian/scripts/validar_vault.py"`.
> - Ubicación del plugin: en **Claude Code**, `${CLAUDE_PLUGIN_ROOT}`. En **Antigravity**, `%USERPROFILE%\.gemini\config\plugins\obsidian-docs` (Windows), `~/.gemini/config/plugins/obsidian-docs` (macOS/Linux) o `.agents/plugins/obsidian-docs` dentro del proyecto.
> - Donde dice `python3`: en **Windows** usa `py -3` (o `python` si `py` no existe); en macOS/Linux, `python3`.

> Normalmente llegas aquí desde el skill `flujo-documentacion`, que decide el camino y hace el Cierre (validar → historias → marca de código → commits → push → dashboard).
> Requisito: el proyecto ya fue documentado con el skill `documentar-proyecto-obsidian`. Si no existe `00 - Inicio.md`, usa ese skill primero.
> Las plantillas y la guía visual están en `../documentar-proyecto-obsidian/references/`.

## Flujo

0. **Sincronizar.** Si el vault es un repositorio git, ejecuta el flujo B del skill `git-documentacion` (traer cambios de otros) antes de editar.
1. **Entender el cambio.** Identifica qué cambió leyendo, en este orden: lo que dice el usuario, los commits de código pendientes (`commit_codigo` de `00 - Inicio.md` → `git log --stat <commit_codigo>..HEAD` en el repo de código; `vinculo.py estado` te dice cuántos son), `git diff` de lo que aún no tiene commit, y archivos modificados.
2. **Mapear impacto.** Construye una tabla mental *archivo/área cambiada → notas afectadas*. Busca en el vault por:
   - la ruta del código (`ubicacion:` en frontmatter, o rutas en bloques de detalle técnico),
   - el nombre del componente, endpoint, tabla, medida o paso del proceso.
3. **Editar con precisión.** Cambia solo lo necesario; conserva el texto del usuario. Actualiza:
   - el contenido y los diagramas Mermaid afectados,
   - los ejemplos `[!example]` si los datos cambiaron,
   - `actualizado:` en el frontmatter,
   - el Glosario si aparecen términos nuevos.
4. **Registrar.**
   - Agrega una entrada arriba en `Historial de cambios.md` con la sección **"⚠️ Cambia para ti"** en lenguaje llano.
   - Si fue una decisión de diseño → crea un ADR (`70 - Decisiones/ADR-NNN …`, siguiente número libre). Si reemplaza otro, marca el anterior `estado: reemplazada` y enlázalos.
   - Si fue un incidente → crea o mejora el runbook correspondiente.
   - Si algo quedó obsoleto → `estado: obsoleto` + callout `> [!warning] Obsoleto desde AAAA-MM-DD — ver [[nueva nota]]`. No borres notas.
4b. **Avance de requerimientos.** Si el proyecto tiene historias (`15 - Requerimientos/`), aplica el flujo B del skill `requerimientos-historias`:
   - Busca las historias afectadas: ID mencionado por el usuario o en los commits (`Refs: HU-…`), o historias cuya sección «🔗 Afecta a la documentación» enlaza a las notas que acabas de cambiar.
   - Con evidencia, marca sus criterios cumplidos y muévelas con `requerimientos.py mover` (ej. `en-progreso` → `en-revision`); si no hay evidencia suficiente, pregunta.
   - Si el cambio revela trabajo nuevo no previsto, propón una historia nueva (flujo A) en vez de meterlo en una existente.
   - Ejecuta `requerimientos.py sincronizar "<proyecto>"` para recalcular avances y el Tablero de avance.
5. **Reconectar.** Actualiza índices (MOC), `## 🔗 Relacionado` y el `Mapa del proyecto.canvas` si hay notas nuevas.
6. **Validar.** Ejecuta `python3 ../documentar-proyecto-obsidian/scripts/validar_vault.py "<carpeta del proyecto>"` y corrige errores.
7. **Marcar y guardar en git.** Si el proyecto tiene vínculo con un repo de código, ejecuta `python3 ../flujo-documentacion/scripts/vinculo.py marcar` (anota en `00 - Inicio.md` hasta qué commit de código quedó documentado). Luego, si el vault es un repositorio git, usa el skill `git-documentacion` (flujo C): un commit por proyecto cuyo mensaje resume lo que acabas de registrar en `Historial de cambios.md` (el "Por qué" y el "⚠️ Cambia para ti" van al cuerpo del commit; las historias que avanzaron van en el pie `Refs: HU-003, HU-004`). Muestra el plan de commits y espera confirmación antes del push.
8. **Informar.** Lista al usuario las notas creadas/modificadas, los commits hechos y lo que quedó pendiente de confirmar.

## Reglas
- Nunca reescribas una nota completa si basta con editar una sección.
- Nunca inventes el motivo de un cambio: si no está claro, deja `> [!question] ¿Por qué se hizo este cambio?`.
- Mantén las mismas convenciones (emojis de sección, nombres, etiquetas) que ya tiene el vault.
