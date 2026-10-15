---
titulo: Arquitectura general
tipo: arquitectura
estado: vigente
audiencia: [tecnico, negocio]
responsable: "{{Responsable}}"
actualizado: "{{AAAA-MM-DD}}"
etiquetas: [tipo/arquitectura]
---

# 🏗️ Arquitectura general

> [!abstract] En pocas palabras
> {{Cómo está armado el sistema, como si describieras un edificio: "Tiene tres pisos: lo que ve el cliente (app), donde se toman decisiones (servidor) y donde se guarda todo (base de datos)".}}

## 🗺️ Nivel 1 · Contexto (para todos)
¿Quién lo usa y con qué otros sistemas habla?

```mermaid
flowchart LR
    u1([👤 {{Actor}}]) -->|{{acción}}| S[⚙️ {{Sistema}}]
    S -->|{{dato}}| ext1[(🔌 {{Sistema externo}})]
```

## 🧱 Nivel 2 · Piezas principales (contenedores)

```mermaid
flowchart TD
    subgraph Usuario
      FE[🖥️ {{Frontend}}]
    end
    subgraph Servidor
      BE[⚙️ {{Backend / API}}]
      JOB[⏰ {{Tareas programadas}}]
    end
    DB[(🗄️ {{Base de datos}})]
    FE -->|HTTPS / JSON| BE
    BE --> DB
    JOB --> DB
```

| Pieza | Qué hace (en llano) | Tecnología | Nota |
|---|---|---|---|
| {{Frontend}} | {{Pantallas que ve el usuario}} | {{React 19}} | [[{{Componente}}]] |

## ⚙️ Cómo se comunican
{{Protocolos, colas, eventos, frecuencia. Ejemplo concreto: "Cuando un cliente paga, la pasarela avisa al servidor en menos de 5 s por un webhook".}}

> [!info]- Detalle técnico
> {{Versiones, puertos, patrones (MVC, hexagonal, estrella…), librerías clave, decisiones con enlace a ADR.}}

## 🌐 Entornos

| Entorno | Para qué | URL / ubicación | Datos |
|---|---|---|---|
| Desarrollo | {{probar cambios}} | {{…}} | ficticios |
| Producción | {{uso real}} | {{…}} | reales |

## ⚠️ Puntos débiles conocidos
- {{Punto único de falla, deuda técnica…}}

## 🔗 Relacionado
- [[Integraciones]] · [[Modelo de datos]] · [[Despliegue]] · [[Decisiones]]
