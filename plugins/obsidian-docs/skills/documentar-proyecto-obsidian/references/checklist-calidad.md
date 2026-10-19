# ✅ Checklist de calidad (obligatorio antes de entregar)

Corre primero el validador automático:

```bash
# En Windows usa `py -3` (o `python`) en lugar de `python3`
python3 "<carpeta del plugin>/skills/documentar-proyecto-obsidian/scripts/validar_vault.py" "<ruta del proyecto en el vault>"
```

`<carpeta del plugin>` es la que indica la nota «Cómo ejecutar los scripts de este plugin» del `SKILL.md` (en Claude Code, la ruta ya viene escrita ahí; en Antigravity, normalmente `~/.gemini/config/plugins/obsidian-docs`).

Luego revisa manualmente:

## Estructura
- [ ] Existe `00 - Inicio.md` y desde ahí se llega a cualquier nota en ≤ 2 clics.
- [ ] Cada carpeta numerada tiene su índice (MOC) con tabla.
- [ ] No hay carpetas vacías ni notas huérfanas (sin enlaces entrantes).
- [ ] Existe `Mapa del proyecto.canvas` y abre sin errores.

## Contenido
- [ ] Toda nota tiene frontmatter completo (`titulo, tipo, estado, audiencia, actualizado, etiquetas`).
- [ ] Toda nota abre con `> [!abstract]` comprensible para alguien no técnico.
- [ ] Ningún `{{placeholder}}`, "TODO", "lorem" o `foo/bar` quedó en el vault.
- [ ] Cada flujo, arquitectura y modelo de datos tiene al menos un diagrama Mermaid.
- [ ] Cada concepto abstracto tiene un `> [!example]` con datos reales del proyecto.
- [ ] Todo término técnico aparece en el Glosario y está enlazado la primera vez que se usa.
- [ ] Lo técnico profundo está en callouts plegables `[!info]-`.
- [ ] Indicadores: fórmula en llano + ejemplo numérico + fórmula técnica.

## Veracidad y seguridad
- [ ] Todo dato viene del código, archivos o del usuario. Lo dudoso está en `> [!question] Pendiente de confirmar`.
- [ ] No hay contraseñas, tokens, cadenas de conexión ni datos personales reales.
- [ ] Rutas de código y comandos fueron verificados (existen).

## Prueba de lectura (hazla mentalmente)
- [ ] 👩‍💼 **Gerente:** leyendo solo `00 - Inicio` + `Resumen ejecutivo`, ¿puede explicar el proyecto en 3 frases?
- [ ] 🆕 **Nuevo técnico:** con `Primeros pasos`, ¿puede ejecutarlo sin preguntar a nadie?
- [ ] 🚑 **Soporte de guardia:** ante la falla más probable, ¿encuentra el runbook en < 1 minuto?
