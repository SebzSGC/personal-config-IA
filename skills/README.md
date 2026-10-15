# Skills

Cada **carpeta** aquí es un skill con un `SKILL.md`. El mismo formato funciona en **Claude** y en **Antigravity**, así que esta carpeta se comparte con los dos:

- `~/.claude/skills/` → apunta aquí
- `~/.gemini/config/skills/` → apunta aquí

```
skills/
└── mi-skill/
    ├── SKILL.md        ← obligatorio
    ├── references/     ← opcional: guías, plantillas
    └── scripts/        ← opcional: scripts que el skill ejecuta
```

```markdown
---
name: mi-skill
description: Qué hace y CUÁNDO usarlo. La descripción es lo que el agente lee para decidir activarlo.
---

# Mi skill
Instrucciones paso a paso…
```

Si creas un skill desde Claude o Antigravity en su carpeta global, aparece aquí automáticamente: solo falta `git add` + `commit` + `push`.
