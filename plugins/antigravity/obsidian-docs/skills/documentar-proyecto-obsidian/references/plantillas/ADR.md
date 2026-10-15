---
titulo: "ADR-{{NNN}} {{Decisión}}"
tipo: decision
estado: "{{propuesta | aceptada | reemplazada | descartada}}"
fecha: "{{AAAA-MM-DD}}"
decisores: [{{Nombre}}]
reemplaza: "{{ADR-NNN o vacío}}"
etiquetas: [tipo/decision]
---

# ⚖️ ADR-{{NNN}} · {{Decisión}}

> [!abstract] En pocas palabras
> Decidimos **{{qué}}** porque **{{razón principal}}**, aceptando que **{{costo / desventaja}}**.

## 🧩 Contexto
{{Qué situación obligó a decidir. Datos concretos: volumen, costos, plazos, restricciones.}}

## 🔀 Opciones evaluadas

| Criterio | {{Opción A}} ✅ | {{Opción B}} | {{Opción C}} |
|---|---|---|---|
| Costo | {{…}} | {{…}} | {{…}} |
| Facilidad | {{…}} | {{…}} | {{…}} |
| Riesgo | {{…}} | {{…}} | {{…}} |

## ✅ Decisión
{{Qué se eligió y cómo se implementa.}}

## 📉 Consecuencias
- 👍 {{…}}
- 👎 {{…}}
- 🔁 Revisar si: {{condición que haría reconsiderar}}

## 🔗 Relacionado
- [[Decisiones]] · [[{{Componente afectado}}]]
