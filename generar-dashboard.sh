#!/usr/bin/env bash
# Genera el dashboard de la documentación (skill dashboard-documentacion del plugin obsidian-docs).
# La primera vez pregunta la ruta del repositorio de documentación y la recuerda.
cd "$(dirname "${BASH_SOURCE[0]}")"
exec python3 plugins/antigravity/obsidian-docs/skills/dashboard-documentacion/scripts/generar_dashboard.py --abrir "$@"
