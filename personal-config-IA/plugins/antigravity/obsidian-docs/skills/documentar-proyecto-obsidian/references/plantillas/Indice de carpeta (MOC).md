---
titulo: "{{Nombre de la sección}}"
tipo: indice
estado: vigente
audiencia: [negocio, tecnico]
actualizado: "{{AAAA-MM-DD}}"
etiquetas: [tipo/indice]
---

# {{emoji}} {{Nombre de la sección}}

> [!abstract] Qué encontrarás aquí
> {{Una frase. Ej.: "Todo lo que pasa paso a paso dentro del sistema, desde que el cliente pide hasta que recibe."}}

| Nota | En una línea | Audiencia | Estado |
|---|---|---|---|
| [[{{Nota 1}}]] | {{…}} | 👩‍💼🛠️ | 🟢 vigente |
| [[{{Nota 2}}]] | {{…}} | 🛠️ | 🟡 borrador |

> [!tip]- Vista automática (requiere el plugin Dataview)
> ```dataview
> TABLE tipo, estado, actualizado
> FROM "{{ruta/de/la/carpeta}}"
> WHERE file.name != this.file.name
> SORT actualizado DESC
> ```

⬅️ Volver a [[00 - Inicio]]
