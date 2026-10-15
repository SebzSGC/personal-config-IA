# Qué documentar según el tipo de proyecto

Identifica el tipo (puede ser mixto) y prioriza las notas marcadas ⭐.

| Tipo | Dónde mirar | Notas prioritarias ⭐ | Diagramas clave |
|---|---|---|---|
| **App web / API** | `package.json`, rutas, controladores, ORM/migraciones, `.env.example`, Dockerfile | Arquitectura general, Flujos de usuario, Referencia API, Modelo de datos, Primeros pasos, Despliegue | C4 contexto (`flowchart`), `sequenceDiagram`, `erDiagram` |
| **App móvil / escritorio** | pantallas, navegación, permisos, build config | Mapa de pantallas, Flujos de usuario, Build y publicación | `flowchart` de navegación, `stateDiagram` |
| **Datos / BI (Power BI, ETL, dbt)** | modelo semántico, medidas DAX, Power Query, orígenes, actualizaciones | Modelo de datos, Indicadores y métricas (con fórmula + ejemplo numérico), Linaje de datos, Calendario de actualización | `erDiagram` (estrella), `flowchart LR` de linaje |
| **Infraestructura / DevOps** | Terraform, k8s manifests, pipelines CI/CD | Arquitectura de red, Entornos, Despliegue, Runbooks, Monitoreo | `flowchart` con `subgraph` por red/entorno |
| **Librería / SDK** | API pública, ejemplos, tests | Primeros pasos, Referencia, Ejemplos de uso, Cambios | `classDiagram` |
| **Automatización / scripts** | scripts, cron, credenciales usadas | Qué hace y cuándo corre, Entradas/salidas, Qué hacer si falla | `flowchart TD`, `timeline` |
| **Machine learning** | notebooks, datasets, métricas de evaluación | Datos de entrenamiento, Modelo y métricas, Ciclo de reentrenamiento, Limitaciones | `flowchart LR` del pipeline |
| **Proceso de negocio** | entrevistas, formatos, manuales existentes | Mapa del proceso, Actores (RACI), Paso a paso, Indicadores, Excepciones | `flowchart` con carriles (`subgraph` por área), `journey` |
| **Proyecto (gestión)** | cronograma, alcance, riesgos | Alcance, Cronograma, Riesgos, Decisiones, Actas | `gantt`, `timeline`, `quadrantChart` de riesgos |

## Matriz RACI (para procesos y proyectos)

Úsala en `Actores y responsables.md`:

| Actividad | Analista | Jefe de área | TI | Gerencia |
|---|:-:|:-:|:-:|:-:|
| Cargar datos del mes | **R** | A | C | I |
| Aprobar informe | C | **R** | – | A |

R = Responsable (lo hace) · A = Aprueba · C = Consultado · I = Informado
