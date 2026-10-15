---
titulo: "{{Título corto en lenguaje del usuario}}"
tipo: historia
id: "{{HU-NNN}}"
epica: "{{EP-NN}}"
estado: borrador              # estado del DOCUMENTO: borrador mientras se refina, vigente cuando está lista
estado_historia: backlog      # backlog | por-hacer | en-progreso | en-revision | hecho | bloqueado | descartado
prioridad: media              # critica | alta | media | baja
puntos: "{{1 | 2 | 3 | 5 | 8 | 13}}"
responsable: "{{Nombre}}"
sprint: "{{Sprint N o vacío}}"
inicio: "{{AAAA-MM-DD o vacío}}"
fin: "{{AAAA-MM-DD o vacío}}"
progreso: 0                   # lo calcula requerimientos.py (criterios y tareas marcados)
depende_de: []
origen: "{{[[Nota de origen]]}}"
audiencia: [negocio, tecnico]
actualizado: "{{AAAA-MM-DD}}"
etiquetas: [tipo/historia, epica/{{EP-NN}}]
---

# 📗 {{HU-NNN}} · {{Título}}

> [!abstract] En pocas palabras
> {{Qué necesita la persona y qué gana, en una frase sin jerga.}}

## 🙋 Historia
**Como** {{rol concreto: "operario de planta", no "usuario"}}
**quiero** {{acción o capacidad}}
**para** {{beneficio medible o razón de negocio}}.

## ✅ Criterios de aceptación
<!-- Cada criterio se marca [x] cuando está verificado. El % de avance sale de aquí y de las tareas. -->
- [ ] **{{Escenario 1}}** — Dado {{contexto}}, cuando {{acción}}, entonces {{resultado observable}}.
- [ ] **{{Escenario 2}}** — Dado {{…}}, cuando {{…}}, entonces {{…}}.

## 💡 Ejemplo
> [!example] {{Caso real con datos}}
> {{Ej.: Ana, operaria de la línea 2, abre el enlace a las 6:05 a. m. y responde las 12 preguntas en 3 minutos.}}

## 🛠️ Tareas
- [ ] {{Tarea técnica o de gestión}}

## 🔗 Afecta a la documentación
<!-- Notas del vault que cambiarán cuando esta historia se construya. Sirve para actualizar el avance al documentar. -->
- [[{{Flujo o componente}}]]

## ❓ Dudas abiertas
> [!question] Pendiente de confirmar
> {{Lo que no está claro en la nota de origen.}}

## 📝 Bitácora
- {{AAAA-MM-DD}} · Creada desde [[{{Nota de origen}}]]

## 🔗 Relacionado
- [[Requerimientos]] · [[{{EP-NN Épica}}|{{EP-NN}}]] · [[Tablero de avance]]
