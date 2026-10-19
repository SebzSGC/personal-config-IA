---
trigger: always_on
description: "Ciclo de documentación del plugin obsidian-docs: mantener el vault al día con cada cambio y cerrar siempre con git."
---

# Ciclo de documentación (obsidian-docs)

Aplica cuando el proyecto abierto tiene un `.obsidian-docs.json` en su raíz o cuando trabajas dentro de un vault de Obsidian (carpeta con `.obsidian/`). Si no se cumple ninguna de las dos, ignora esta regla.

1. **Al empezar** una tarea que cambie código, datos, configuración o un proceso: ejecuta `vinculo.py estado` del skill `flujo-documentacion`. Si indica `sincronizar`, trae primero los cambios del repositorio de documentación.
2. **Antes de dar por terminada** una tarea que cambió comportamiento, arquitectura, datos, configuración o pasos de operación: sigue el skill `flujo-documentacion` (camino «Actualizar» y su Cierre). Actualizar la documentación es parte de terminar la tarea, no un extra.
3. Si el cambio **no afecta** nada documentado (formato, pruebas, refactor interno), no toques el vault y dilo en una línea en tu respuesta final: «Documentación: sin cambios necesarios (motivo)».
4. Git del vault **solo** con el skill `git-documentacion`: un commit por proyecto, mensaje `tipo(proyecto): descripción` con «Qué cambió / Por qué», y push **solo** con confirmación del usuario.
5. Nunca termines con cambios del vault sin commit o sin subir **sin decírselo** al usuario en tu respuesta final.
