# 🪝 Hook de cierre (opcional, experimental)

`verificar_cierre.py` es un hook **Stop** de Antigravity: cuando el agente va a terminar, revisa con `vinculo.py` si la documentación del proyecto quedó atrás del código o tiene cambios sin commit. Si es así, le pide **una sola vez** que siga el skill `flujo-documentacion` (o que diga por qué no hace falta). Si el estado no cambia, no vuelve a insistir, y ante cualquier error deja terminar.

Es un refuerzo de la regla `ciclo-documentacion`, que ya está siempre activa.

> [!note] En Claude Code ya está activo
> El plugin lo registra solo en `claude/hooks.json` (evento `Stop`), junto con un hook `SessionStart` que le pasa a Claude las reglas de `rules/`. No hay nada que activar. Para apagarlo, deshabilita el plugin con `/plugin`.

En **Antigravity** **no se instala solo** porque:

- En la app y el IDE, Antigravity lee los hooks de `~/.gemini/config/hooks.json` (global) o `.agents/hooks.json` (proyecto), no de la carpeta del plugin.
- Hay reportes de que el evento `Stop` no se dispara en algunas versiones del IDE para Windows. Pruébalo antes de confiar en él.

## Activarlo

Agrega esto a `~/.gemini/config/hooks.json` (créalo si no existe; si ya tiene contenido, agrega solo la clave `obsidian-docs-cierre`):

**Windows**
```json
{
  "obsidian-docs-cierre": {
    "Stop": [
      { "command": "py -3 \"%USERPROFILE%\\.gemini\\config\\plugins\\obsidian-docs\\hooks-opcionales\\verificar_cierre.py\"", "timeout": 20 }
    ]
  }
}
```

**macOS / Linux**
```json
{
  "obsidian-docs-cierre": {
    "Stop": [
      { "command": "python3 ~/.gemini/config/plugins/obsidian-docs/hooks-opcionales/verificar_cierre.py", "timeout": 20 }
    ]
  }
}
```

Para desactivarlo sin borrarlo: agrega `"enabled": false` dentro de `obsidian-docs-cierre`.

## Probarlo a mano

```bash
echo '{"conversationId":"prueba","workspacePaths":["C:/ruta/al/codigo"]}' | py -3 verificar_cierre.py
```

- `{"decision": "continue", "reason": "…"}` → habría pedido actualizar la documentación.
- `{}` → todo al día (o el proyecto no tiene `.obsidian-docs.json`).
