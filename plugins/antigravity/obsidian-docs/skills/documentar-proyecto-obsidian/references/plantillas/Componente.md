---
titulo: "{{Nombre del componente}}"
tipo: componente
estado: vigente
audiencia: [tecnico]
responsable: "{{Responsable}}"
actualizado: "{{AAAA-MM-DD}}"
ubicacion: "{{ruta/en/el/repositorio}}"
etiquetas: [tipo/componente, capa/{{frontend|backend|datos|infra}}]
---

# 🧩 {{Nombre del componente}}

> [!abstract] En pocas palabras
> {{Qué hace en una frase y por qué existe. Ej.: "Calcula el valor del domicilio según la distancia; sin él, todos los pedidos cobrarían tarifa fija."}}

## 📥 Recibe → ⚙️ Hace → 📤 Entrega

```mermaid
flowchart LR
    in[📥 {{Entrada}}] --> c[⚙️ {{Componente}}] --> out[📤 {{Salida}}]
```

| | Descripción | Ejemplo real |
|---|---|---|
| 📥 Entrada | {{…}} | `{{"direccion": "Cra 70 #45-10"}}` |
| 📤 Salida | {{…}} | `{{"valor": 6500}}` |

## 💡 Ejemplo paso a paso
> [!example] {{Situación real}}
> 1. {{…}}
> 2. {{…}}
> **Resultado:** {{…}}

## 🔌 Depende de / lo usan
- **Depende de:** [[{{Componente A}}]], {{librería}}
- **Lo usan:** [[{{Flujo X}}]]

> [!info]- Detalle técnico
> - Ubicación: `{{ruta}}`
> - Fragmento clave (≤ 25 líneas):
> ```{{lenguaje}}
> {{código}}
> ```
> - Configuración: `{{VARIABLE}}` — {{qué controla}}

## ⚠️ Cuidado al modificar
- {{efectos secundarios, pruebas que deben pasar}}

## 🔗 Relacionado
- [[Arquitectura general]] · [[{{Flujo}}]]
