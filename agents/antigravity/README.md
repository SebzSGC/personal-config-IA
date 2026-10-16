# Agentes de Antigravity

Cada archivo `.md` aquí es un subagente global de Antigravity (queda disponible en `~/.gemini/config/agents/`).

```markdown
---
name: mi-agente
description: Cuándo debe usarlo el agente principal (sé específico).
tools:
  - view_file
  - grep_search
  - run_command
subagent: true
mainAgent: false
model: inherit
---

# System Prompt
Instrucciones del agente…
```

> `mainAgent: false` = el agente **no aparece en el selector de agentes**; solo lo invoca otro agente como subagente. Si quieres verlo y elegirlo en la sección de agentes, pon `mainAgent: true`.
> Los agentes que vienen dentro de un plugin (por ejemplo `revisor-documentacion` de obsidian-docs) **no** se copian aquí: ya los carga el plugin.
> Ojo: un nombre de herramienta mal escrito en `tools` puede dejar colgado al subagente.
