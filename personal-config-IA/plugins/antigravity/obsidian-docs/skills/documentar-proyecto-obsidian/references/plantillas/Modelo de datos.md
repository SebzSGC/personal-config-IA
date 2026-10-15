---
titulo: Modelo de datos
tipo: datos
estado: vigente
audiencia: [tecnico, negocio]
actualizado: "{{AAAA-MM-DD}}"
etiquetas: [tipo/datos]
---

# 🗄️ Modelo de datos

> [!abstract] En pocas palabras
> {{Qué información guarda el sistema y cómo se relaciona. Ej.: "Guardamos clientes, sus pedidos y lo que compró en cada pedido. Un cliente puede tener muchos pedidos."}}

## 🗺️ Diagrama

```mermaid
erDiagram
    {{TABLA_A}} ||--o{ {{TABLA_B}} : "{{relación}}"
    {{TABLA_A}} {
        int id PK
        string nombre
    }
```

> [!tip] Cómo leer el diagrama
> `||--o{` = "uno a muchos": **un** cliente tiene **cero o muchos** pedidos.

## 📋 Diccionario de datos

### {{Tabla}}
**Qué representa:** {{…}} · **Filas aprox.:** {{…}} · **Se actualiza:** {{…}}

| Campo | Tipo | Significado (en llano) | Ejemplo | ¿Obligatorio? |
|---|---|---|---|---|
| `id` | entero | Número único del registro | `1042` | ✅ |

## 🔄 Origen y linaje

```mermaid
flowchart LR
    src[(📥 {{Origen}})] -->|{{ETL / carga}}| stg[{{Staging}}] --> dw[(🗄️ {{Destino}})] --> rep[📊 {{Informe}}]
```

## 🔒 Datos sensibles
| Campo | Tipo de dato | Protección |
|---|---|---|
| {{correo}} | Personal | {{enmascarado en reportes}} |

## 🔗 Relacionado
- [[Indicadores y métricas]] · [[Arquitectura general]]
