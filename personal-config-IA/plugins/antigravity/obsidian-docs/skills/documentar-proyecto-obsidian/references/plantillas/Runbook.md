---
titulo: "Runbook · {{Problema}}"
tipo: operacion
estado: vigente
audiencia: [tecnico]
severidad: "{{🔴 alta | 🟠 media | 🟡 baja}}"
responsable: "{{Equipo de guardia}}"
actualizado: "{{AAAA-MM-DD}}"
etiquetas: [tipo/runbook]
---

# 🚑 {{Problema}}

> [!danger] Síntoma
> {{Cómo se nota: alerta, mensaje, queja típica de usuario. Ej.: "Los clientes reportan 'Error 503' al pagar".}}

| Severidad | Impacto | Escalar a | Tiempo máximo antes de escalar |
|---|---|---|---|
| {{🔴 Alta}} | {{Nadie puede pagar}} | {{Nombre / canal}} | {{15 min}} |

## 🔎 Diagnóstico rápido

```mermaid
flowchart TD
    A{{{¿El servidor responde?}}} -- No --> B[Reiniciar servicio · paso 1]
    A -- Sí --> C{{{¿La base de datos responde?}}}
    C -- No --> D[Ver paso 2]
    C -- Sí --> E[Revisar pasarela · paso 3]
```

## 🪜 Pasos de solución
1. **{{Verificar …}}**
   ```bash
   {{comando}}
   ```
   Esperado: `{{salida}}`
2. **{{…}}**

> [!warning] No hagas
> {{Acciones peligrosas que tientan pero empeoran el problema.}}

## ✅ Cómo confirmar que se resolvió
- {{…}}

## 📝 Después del incidente
- Registra en [[Historial de cambios]] y, si fue grave, crea un postmortem.

## 🔗 Relacionado
- [[Monitoreo y alertas]] · [[{{Componente}}]]
