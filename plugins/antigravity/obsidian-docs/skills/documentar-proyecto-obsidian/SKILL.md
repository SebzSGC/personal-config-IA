---
name: documentar-proyecto-obsidian
description: Documenta cualquier proyecto (software, datos/BI, infraestructura, procesos de negocio, investigación) dentro de un Vault de Obsidian, con estructura organizada, diagramas Mermaid y Canvas, callouts, glosario y ejemplos aterrizados para lectores técnicos y no técnicos. Úsala cuando el usuario pida documentar un proyecto, crear o poblar un vault de Obsidian, generar la wiki o base de conocimiento de un proyecto, o explicar un sistema "para que cualquiera lo entienda".
---

# Documentar un proyecto en Obsidian

Tu objetivo: que **una persona no técnica entienda de qué va el proyecto en 2 minutos**
y que **una persona técnica pueda operarlo y modificarlo en 30 minutos**, leyendo el mismo vault.

## Principios (no negociables)

1. **Primero el "para qué", luego el "cómo".** Cada nota abre con un resumen en lenguaje llano (callout `[!abstract]`) antes de cualquier detalle técnico.
2. **Una nota = una idea.** Notas atómicas, enlazadas con `[[wikilinks]]`. Si una nota supera ~400 líneas, divídela.
3. **Mostrar antes que contar.** Todo proceso, arquitectura o relación lleva un diagrama Mermaid. La vista general del proyecto lleva un `.canvas`.
4. **Ejemplos aterrizados.** Cada concepto abstracto lleva un ejemplo concreto con datos realistas del propio proyecto (nombres, cifras, rutas reales). Nunca `foo/bar`.
5. **Dos niveles de lectura.** Lo técnico profundo va dentro de callouts plegables `> [!info]- Detalle técnico` para no asustar al lector de negocio.
6. **Cero jerga sin definir.** Cada término técnico se enlaza la primera vez a su nota del glosario `[[Glosario#Término]]`.
7. **Verdad verificable.** Solo documenta lo que leíste en el código, archivos o lo que el usuario confirmó. Lo que no sepas, márcalo con `> [!question] Pendiente de confirmar`.
8. **Navegable desde un solo punto.** Todo es alcanzable desde `00 - Inicio.md` en máximo 2 clics.

## Flujo de trabajo

### Paso 1 · Descubrir (no escribas nada todavía)
- Identifica el **tipo de proyecto** (ver tabla en `references/tipos-de-proyecto.md`) y qué secciones aplican.
- Lee: README, estructura de carpetas, manifiestos (`package.json`, `requirements.txt`, `pom.xml`, `.pbix`, `docker-compose.yml`…), configuración, puntos de entrada, modelos de datos, scripts, tests y commits recientes.
- Para proyectos no-software (procesos, negocio), pide o lee: objetivo, actores, entradas/salidas, frecuencia, herramientas, indicadores.
- Pregunta al usuario solo lo imprescindible (máx. 3 preguntas): ruta del vault, audiencia principal, idioma si no es obvio.

### Paso 2 · Planear la estructura
- Crea la estructura del vault según `references/estructura-vault.md`. Omite carpetas que no apliquen; no dejes carpetas vacías.
- Haz una lista de notas a crear y muéstrala al usuario como plan breve antes de escribir si el proyecto es grande (>20 notas).

### Paso 3 · Escribir con plantillas
- Usa las plantillas de `references/plantillas/`. Rellena **todas** las secciones o elimina las que no apliquen (nunca dejes "TODO" o placeholders `{{}}`).
- Orden recomendado: `00 - Inicio` → `Resumen ejecutivo` → `Glosario` → `Arquitectura / Mapa del proceso` → componentes → flujos → guías → operación → decisiones (ADR) → FAQ.
- Aplica la guía visual de `references/guia-visual.md` (Mermaid, callouts, tablas, emojis de sección, Canvas).

### Paso 4 · Conectar
- Agrega enlaces bidireccionales: cada componente enlaza a sus flujos y viceversa.
- Agrega la sección `## 🔗 Relacionado` al final de cada nota.
- Crea `Mapa del proyecto.canvas` (ver ejemplo en `references/ejemplo-canvas.canvas`).
- Actualiza los índices (MOC) de cada carpeta.

### Paso 5 · Verificar (checklist obligatorio)
Ejecuta `references/checklist-calidad.md` sobre lo creado. Corrige antes de entregar. Puedes usar el script `scripts/validar_vault.py <ruta-vault>` para detectar enlaces rotos, notas huérfanas, frontmatter faltante y placeholders.

### Paso 6 · Entregar
Resume al usuario: cuántas notas, dónde empezar (`00 - Inicio.md`), qué quedó marcado como pendiente de confirmar.
Si el vault es un repositorio git (o el usuario quiere subirlo a uno), ofrece guardar con el skill `git-documentacion`: un commit `feat(<proyecto>): crea la documentación de <Proyecto>` y push tras su confirmación.

## Convenciones del vault

| Elemento | Convención | Ejemplo |
|---|---|---|
| Carpetas | Prefijo numérico + nombre | `20 - Arquitectura` |
| Notas | Título legible, sin guiones bajos | `Flujo de facturación.md` |
| ADR | `ADR-NNN Título` | `ADR-003 Usar PostgreSQL.md` |
| Fechas | ISO `AAAA-MM-DD` | `2026-10-15` |
| Etiquetas | jerárquicas, minúsculas | `#tipo/flujo`, `#estado/vigente` |
| Adjuntos | `90 - Recursos/adjuntos/` | `diagrama-red.png` |

Frontmatter mínimo en **toda** nota:

```yaml
---
titulo: Flujo de facturación
tipo: flujo            # inicio | resumen | arquitectura | componente | flujo | guia | operacion | decision | glosario | faq | datos | api | cambios
estado: vigente        # borrador | vigente | obsoleto
audiencia: [negocio, tecnico]
responsable: Nombre Apellido
actualizado: 2026-10-15
etiquetas: [tipo/flujo, area/finanzas]
---
```

## Qué NO hacer
- No copies código completo al vault: enlaza al archivo y muestra solo el fragmento relevante (≤ 25 líneas).
- No inventes cifras, endpoints, responsables ni fechas.
- No uses diagramas con más de ~15 nodos: divídelos.
- No borres ni sobrescribas notas existentes del usuario sin confirmar; si existe una nota con el mismo nombre, actualízala respetando su contenido.
- No guardes secretos (contraseñas, tokens, cadenas de conexión). Sustituye por `<SECRETO: ver gestor de claves>`.

## Recursos
- `references/estructura-vault.md` — árbol de carpetas y propósito de cada una.
- `references/tipos-de-proyecto.md` — qué documentar según el tipo de proyecto.
- `references/guia-visual.md` — Mermaid, callouts, Canvas, tablas y estilo de redacción.
- `references/plantillas/` — una plantilla por tipo de nota.
- `references/ejemplo-completo.md` — vault de ejemplo resuelto (app de pedidos) para imitar el nivel de detalle.
- `references/ejemplo-canvas.canvas` — Canvas de ejemplo.
- `references/checklist-calidad.md` — revisión final.
- `scripts/validar_vault.py` — validador automático.
