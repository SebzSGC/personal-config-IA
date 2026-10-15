---
trigger: model_decision
description: "Aplica estas reglas siempre que crees o edites notas Markdown dentro de un Vault de Obsidian (carpetas con .obsidian/ o notas con [[wikilinks]]), o cuando documentes un proyecto."
---

# Reglas de estilo para documentación en Obsidian

1. Toda nota nueva lleva frontmatter con: `titulo, tipo, estado, audiencia, actualizado, etiquetas`. Fechas en formato `AAAA-MM-DD`.
2. Toda nota abre con `> [!abstract] En pocas palabras` escrito para una persona no técnica (máx. 3 líneas).
3. Usa `[[wikilinks]]` para enlazar notas internas, nunca enlaces Markdown `[texto](ruta.md)`.
4. Procesos, arquitecturas y modelos de datos llevan diagrama Mermaid (máx. ~15 nodos, etiquetas en lenguaje llano).
5. Cada concepto abstracto lleva un `> [!example]` con datos concretos y realistas del proyecto.
6. Los detalles técnicos profundos van en callouts plegables `> [!info]- Detalle técnico`.
7. Frases cortas, voz activa, sin jerga sin definir: enlaza términos a `[[Glosario#Término]]`.
8. Termina cada nota con `## 🔗 Relacionado`.
9. Nunca escribas secretos (contraseñas, tokens, cadenas de conexión) ni datos personales reales: usa `<SECRETO: ver gestor de claves>`.
10. Nunca inventes datos: lo no confirmado va en `> [!question] Pendiente de confirmar`.
11. No borres notas del usuario: márcalas `estado: obsoleto` y enlaza su reemplazo.
12. Cada proyecto es un vault independiente: nunca uses `[[wikilinks]]` hacia notas de otro proyecto; usa `[Texto](obsidian://open?vault=<Proyecto>&file=<nota>)` con espacios como `%20`.
