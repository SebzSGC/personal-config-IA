---
name: auditar-vault-obsidian
description: Audita la calidad de la documentación de un proyecto en Obsidian (claridad para no técnicos, diagramas, ejemplos, enlaces rotos, notas huérfanas, desactualización, secretos expuestos) y entrega un informe con calificación y mejoras priorizadas. Úsala cuando el usuario pida revisar, auditar, evaluar o mejorar la documentación o el vault de un proyecto.
---

# Auditar un vault de Obsidian

> [!note] Cómo ejecutar los scripts de este plugin
> - Las rutas `scripts/…` y `../…` de este skill son **relativas a la carpeta de este `SKILL.md`**, no a la terminal (que arranca en el proyecto abierto). Antes de ejecutar, conviértelas a ruta absoluta, p. ej. `"<carpeta de este SKILL.md>/scripts/…"` o `"<carpeta de este SKILL.md>/../documentar-proyecto-obsidian/scripts/validar_vault.py"`.
> - Ubicación del plugin: en **Claude Code**, `${CLAUDE_PLUGIN_ROOT}`. En **Antigravity**, `%USERPROFILE%\.gemini\config\plugins\obsidian-docs` (Windows), `~/.gemini/config/plugins/obsidian-docs` (macOS/Linux) o `.agents/plugins/obsidian-docs` dentro del proyecto.
> - Donde dice `python3`: en **Windows** usa `py -3` (o `python` si `py` no existe); en macOS/Linux, `python3`.

## Flujo

1. **Validación automática.** Ejecuta:
   ```bash
   python3 ../documentar-proyecto-obsidian/scripts/validar_vault.py "<carpeta del proyecto>" --json
   ```
2. **Revisión humana** con `../documentar-proyecto-obsidian/references/checklist-calidad.md`, leyendo como tres personas: gerente, nuevo técnico, soporte de guardia.
3. **Detectar desactualización:** compara `actualizado:` de cada nota con la fecha del último cambio del código/archivos que documenta (si hay repositorio: `git log -1 --format=%cs -- <ruta>`). Más de 90 días de diferencia = desactualizada.
3b. **Requerimientos** (si existe `15 - Requerimientos/`): `python3 ../requerimientos-historias/scripts/requerimientos.py listar "<carpeta del proyecto>"` y reporta historias vencidas, bloqueadas, sin criterios de aceptación o marcadas como hechas con criterios pendientes.
4. **Calificar** cada dimensión de 1 a 5:

| Dimensión | Qué mide |
|---|---|
| 🧭 Navegación | Todo alcanzable desde `00 - Inicio` en ≤ 2 clics, índices completos |
| 🗣️ Claridad | Resúmenes sin jerga, glosario, frases cortas |
| 🖼️ Visual | Diagramas donde hacen falta, canvas, tablas |
| 💡 Ejemplos | Ejemplos concretos y realistas |
| ✅ Exactitud | Coincide con el código/proceso actual |
| 🔐 Seguridad | Sin secretos ni datos personales |

5. **Entregar el informe** como nota `90 - Recursos/Auditoría AAAA-MM-DD.md`:

```markdown
# 🔍 Auditoría de documentación · AAAA-MM-DD

> [!abstract] Resultado
> Calificación global **X,X / 5**. Lo más urgente: …

| Dimensión | Nota | Comentario |
|---|---|---|
| 🧭 Navegación | ⭐⭐⭐⭐ | … |

## 🔴 Arreglar ya (errores)
- [ ] …
## 🟡 Mejorar pronto
- [ ] …
## 🟢 Ideas
- [ ] …
```

6. **Ofrece** aplicar las correcciones (con el skill `actualizar-documentacion-obsidian`). No las apliques sin confirmación, salvo que el usuario lo haya pedido explícitamente.
