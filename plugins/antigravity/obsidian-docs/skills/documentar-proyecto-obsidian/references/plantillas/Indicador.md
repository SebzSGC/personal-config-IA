---
titulo: "{{Nombre del indicador}}"
tipo: datos
estado: vigente
audiencia: [negocio, tecnico]
unidad: "{{% | $ | horas}}"
frecuencia: "{{mensual}}"
meta: "{{≥ 95 %}}"
responsable: "{{Dueño del indicador}}"
actualizado: "{{AAAA-MM-DD}}"
etiquetas: [tipo/indicador]
---

# 📊 {{Nombre del indicador}}

> [!abstract] ¿Qué responde?
> {{La pregunta de negocio. Ej.: "¿Qué porcentaje de pedidos llega a tiempo?"}}

| 🎯 Meta | 📏 Unidad | 🔁 Frecuencia | 👤 Dueño | 🟢🟡🔴 Semáforo |
|---|---|---|---|---|
| {{≥ 95 %}} | {{%}} | {{Mensual}} | {{…}} | 🟢 ≥ 95 · 🟡 90–95 · 🔴 < 90 |

## 🧮 Cómo se calcula (en llano)
> {{Pedidos entregados antes de 45 min ÷ total de pedidos entregados × 100}}

## 💡 Ejemplo con números
> [!example] Septiembre 2026
> - Pedidos entregados: **1.200**
> - Entregados a tiempo: **1.128**
> - Cálculo: 1.128 ÷ 1.200 × 100 = **94 %** → 🟡

> [!info]- Fórmula técnica
> ```{{dax|sql}}
> {{Medida := DIVIDE([A], [B])}}
> ```
> Origen: `{{tabla.campo}}` · Filtros aplicados: {{…}}

## ⚠️ Cuidado al interpretar
- {{Excepciones, qué no incluye, sesgos}}

## 🔗 Relacionado
- [[Indicadores y métricas]] · [[Modelo de datos]]
