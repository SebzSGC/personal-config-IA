---
name: flujo-documentacion
description: Punto de entrada del plugin obsidian-docs. Úsala siempre que haya que crear, actualizar, revisar, guardar o consultar la documentación de un proyecto en Obsidian — "documenta esto", "actualiza la doc", "¿la documentación está al día?", "sincroniza el vault", "sube la documentación" — y al terminar cualquier tarea que cambie el código, los datos o el proceso de un proyecto con .obsidian-docs.json. Decide el camino (crear, actualizar, requerimientos, auditar) y cierra siempre con el mismo ciclo de git.
---

# Flujo de documentación (orquestador)

> [!note] Cómo ejecutar los scripts de este plugin
> - Las rutas `scripts/…` y `../…` de este skill son **relativas a la carpeta de este `SKILL.md`**, no a la terminal (que arranca en el proyecto abierto). Antes de ejecutar, conviértelas a ruta absoluta, p. ej. `"<carpeta de este SKILL.md>/scripts/…"` o `"<carpeta de este SKILL.md>/../documentar-proyecto-obsidian/scripts/validar_vault.py"`.
> - Ubicación del plugin: en **Claude Code**, `${CLAUDE_PLUGIN_ROOT}`. En **Antigravity**, `%USERPROFILE%\.gemini\config\plugins\obsidian-docs` (Windows), `~/.gemini/config/plugins/obsidian-docs` (macOS/Linux) o `.agents/plugins/obsidian-docs` dentro del proyecto.
> - Donde dice `python3`: en **Windows** usa `py -3` (o `python` si `py` no existe); en macOS/Linux, `python3`.

**Objetivo:** que la documentación nunca se quede atrás del código y que cada cambio quede en git con un mensaje que se entienda sin abrir los archivos. Este skill no escribe notas por sí mismo: decide qué skill usar y **siempre** termina con el mismo cierre.

## 1 · Ubicarte (siempre primero)

```bash
python3 scripts/vinculo.py estado --fetch
```

Te dice dónde está el vault del proyecto, si existe, cuántos commits de código faltan por documentar, qué hay sin commit o sin subir y **qué sigue**:

| `sugerencia` | Qué haces |
|---|---|
| `vincular` | El código no sabe cuál es su vault. Pregunta al usuario (máx. 2 preguntas): nombre del proyecto en el vault y ruta del repositorio de documentación. Luego `vinculo.py vincular --proyecto "<Proyecto>" --repo "<ruta>"` y vuelve a ejecutar `estado`. Ver `references/vinculo.md` |
| `documentar` | Camino **Crear** |
| `actualizar` | Camino **Actualizar** |
| `guardar` / `subir` | Directo al **Cierre** (pasos 5 y 6) |
| `al-dia` | Nada que hacer; dilo en una línea |

Si `antes` contiene `sincronizar`, primero trae los cambios del repo de documentación (skill `git-documentacion`, flujo B). **Nunca documentes encima de un repo desactualizado.**

## 2 · Elegir el camino

| Situación | Skill | Notas |
|---|---|---|
| **Crear**: no existe el vault o no tiene `00 - Inicio.md` | `documentar-proyecto-obsidian` | Si el repo de docs no tiene git todavía: `git-documentacion` flujo A o A2 |
| **Actualizar**: hubo cambios de código, datos o proceso (lo dice `estado` o el usuario) | `actualizar-documentacion-obsidian` | Incluye mover las historias afectadas (paso 4b) |
| **Requerimientos**: notas de reunión, ideas, «la HU-003 ya está en pruebas» | `requerimientos-historias` | |
| **Revisar**: "¿está bien la documentación?", antes de entregar | `auditar-vault-obsidian` y el agente `revisor-documentacion` | Solo lectura; propone, no corrige sin permiso |
| **Ver el estado** de todo | `dashboard-documentacion` | |

Un mismo pedido puede necesitar varios caminos (p. ej. un cambio de código que termina una historia = Actualizar con su paso 4b). Hazlos en ese orden: Crear → Actualizar → Requerimientos, y **un solo Cierre al final**.

## 3 · Cierre (obligatorio, siempre en este orden)

1. **Validar** — `python3 ../documentar-proyecto-obsidian/scripts/validar_vault.py "<vault>"`. Corrige los errores que causaste; los de seguridad bloquean el commit.
2. **Historias** — si existe `15 - Requerimientos/`: `python3 ../requerimientos-historias/scripts/requerimientos.py sincronizar "<vault>"`.
3. **Historial** — si actualizaste, la entrada de `Historial de cambios.md` debe existir (con «⚠️ Cambia para ti» si afecta a usuarios).
4. **Marca de código** — si hay vínculo con un repo de código: `python3 scripts/vinculo.py marcar`. Anota en `00 - Inicio.md` hasta qué commit de código está documentado, para que la próxima vez `estado` cuente solo lo nuevo. Hazlo **antes** de los commits para que entre en el mismo.
5. **Commits** — skill `git-documentacion`, flujo C: un commit por proyecto con `tipo(proyecto): …`, cuerpo «Qué cambió / Por qué» tomado del Historial y pie `Refs:` con las historias. **Muestra el plan y espera el sí del usuario.**
6. **Push** — `git pull --rebase` y `git push`. Nunca forzar.
7. **Dashboard** — `python3 ../dashboard-documentacion/scripts/generar_dashboard.py --repo "<repo de docs>"` si el usuario lo usa (o ofrécelo en una línea).
8. **Informe** al usuario, en este formato:

```
📚 Documentación de <Proyecto>
- Notas: <creadas / modificadas>
- Historias: <movidas y a qué estado>  (si aplica)
- Commits: <hash> <mensaje>  ·  push: hecho / pendiente de tu confirmación
- Pendiente de confirmar: <dudas marcadas con [!question]>
```

## 4 · Mientras trabajas en el código

La regla `ciclo-documentacion` está siempre activa y te recuerda esto en cualquier conversación:

- Documenta **por cambio terminado**, no por archivo: al cerrar una funcionalidad, un arreglo o un cambio de configuración, no a mitad de la tarea.
- **Sí requiere documentación:** comportamiento visible, arquitectura, modelo de datos, medidas/KPI, endpoints, configuración, pasos de operación, dependencias, decisiones de diseño (ADR), incidentes (runbook).
- **No requiere:** formato, comentarios, pruebas, refactor sin cambio visible. En ese caso no toques el vault y dilo en una línea: «Documentación: sin cambios necesarios (refactor interno)».
- Si el usuario hace commits del código, que el del cambio vaya **antes** del Cierre: la marca de `vinculo.py marcar` apunta al último commit, y lo que quede sin commit se volverá a contar como pendiente.
- Si no estás seguro de algo, documenta lo seguro y deja `> [!question] Pendiente de confirmar`; nunca inventes el motivo de un cambio.

## Reglas que nunca cambian

- Git del vault solo a través de `git-documentacion` (y la regla `git-seguro`): rutas explícitas, un proyecto por commit, sin `--force`, sin `--no-verify`, push con confirmación.
- No borres ni reescribas notas del usuario; marca `estado: obsoleto` y enlaza el reemplazo.
- Nunca termines una tarea con cambios del vault sin commit **sin decírselo al usuario**.

## Recursos
- `scripts/vinculo.py` — `estado`, `vincular`, `marcar`.
- `references/vinculo.md` — formato de `.obsidian-docs.json` y casos (un repo de docs para varios proyectos, equipos, carpetas sin git).
