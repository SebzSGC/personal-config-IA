---
titulo: "{{Flujo de …}}"
tipo: flujo
estado: vigente
audiencia: [negocio, tecnico]
responsable: "{{Responsable}}"
actualizado: "{{AAAA-MM-DD}}"
frecuencia: "{{cada pedido | diario 6:00 a. m. | mensual}}"
etiquetas: [tipo/flujo]
---

# 🔄 {{Flujo de …}}

> [!abstract] En pocas palabras
> {{Qué ocurre, quién lo dispara y qué se obtiene al final. Ej.: "Cuando un cliente paga, el sistema confirma el pedido, avisa a cocina y le envía un correo al cliente. Tarda menos de 10 segundos."}}

| ▶️ Empieza cuando | 🏁 Termina cuando | ⏱️ Duración típica | 🔁 Frecuencia |
|---|---|---|---|
| {{evento disparador}} | {{resultado}} | {{…}} | {{…}} |

## 🗺️ Vista general

```mermaid
flowchart LR
    A([▶️ {{Inicio}}]) --> B[{{Paso 1}}] --> C{{{¿Condición?}}}
    C -- Sí --> D[{{Paso 2}}] --> F([🏁 {{Fin}}])
    C -- No --> E[{{Alternativa}}]
```

## 🧭 Paso a paso

| # | Quién / qué | Hace | Resultado |
|---|---|---|---|
| 1 | {{Cliente}} | {{…}} | {{…}} |
| 2 | {{Sistema}} | {{…}} | {{…}} |

## 💡 Ejemplo real
> [!example] {{Pedido #1042 de Ana, $38.500}}
> {{Recorre el flujo con datos concretos, de principio a fin.}}

## 🛠️ ¿Y si algo sale mal?

| Situación | Qué ve el usuario | Qué hace el sistema | Qué hacer |
|---|---|---|---|
| {{Pago rechazado}} | {{…}} | {{…}} | {{…}} → [[{{Runbook}}]] |

> [!info]- Detalle técnico (secuencia)
> ```mermaid
> sequenceDiagram
>     autonumber
>     actor U as {{Actor}}
>     participant A as {{Componente}}
>     U->>A: {{acción}}
>     A-->>U: {{respuesta}}
> ```

## 🔗 Relacionado
- [[{{Componente}}]] · [[{{Otro flujo}}]]
