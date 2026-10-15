---
titulo: "{{Nombre del proyecto}}"
tipo: inicio
estado: vigente
audiencia: [negocio, tecnico]
responsable: "{{Responsable}}"
actualizado: "{{AAAA-MM-DD}}"
etiquetas: [tipo/inicio]
---

# 🏠 {{Nombre del proyecto}}

> [!abstract] En pocas palabras
> {{Una o dos frases: qué hace el proyecto, para quién y qué problema resuelve. Ej.: "App que permite a los clientes de Restaurante La 70 pedir a domicilio y pagar en línea; reemplaza los pedidos por WhatsApp."}}

| 📌 Estado | 👤 Responsable | 🗓️ Actualizado | 🔗 Repositorio / origen |
|---|---|---|---|
| {{En producción / En desarrollo / Piloto}} | {{Nombre}} | {{AAAA-MM-DD}} | {{enlace}} |

## 🧭 ¿Por dónde empiezo?

| Si eres… | Lee primero | Luego |
|---|---|---|
| 👩‍💼 De negocio / directivo | [[Resumen ejecutivo]] | [[Indicadores y métricas]] |
| 🆕 Nuevo en el equipo | [[Primeros pasos]] | [[Arquitectura general]] |
| 🛠️ Técnico que da soporte | [[Runbooks]] | [[Monitoreo y alertas]] |
| 🤔 Buscas un término | [[Glosario]] | [[FAQ]] |

## 🗺️ El proyecto de un vistazo

```mermaid
flowchart LR
    %% Reemplaza con el contexto real del proyecto
    usuario([👤 {{Usuario principal}}]) -->|{{acción}}| sistema[⚙️ {{Nombre del proyecto}}]
    sistema -->|{{resultado}}| salida[📤 {{Salida principal}}]
    sistema <-->|{{datos}}| externo[(🔌 {{Sistema externo}})]
```

Vista completa e interactiva: ![[Mapa del proyecto.canvas]]

## 📚 Secciones

- 🎯 [[Visión general]] — qué, para qué, quién
- 🏗️ [[Arquitectura]] — cómo está construido
- 🔄 [[Flujos y procesos]] — qué pasa paso a paso
- 📊 [[Datos]] — qué información maneja
- 🧭 [[Guías]] — cómo hacer tareas concretas
- 🚑 [[Operación]] — mantenerlo funcionando
- ⚖️ [[Decisiones]] — por qué se hizo así
- 📖 [[Referencia]] — detalles técnicos exactos

## 🔔 Novedades recientes
- {{AAAA-MM-DD}} — {{cambio importante}} → [[Historial de cambios]]
