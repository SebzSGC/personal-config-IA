# Convención de commits para documentación

Basada en **Conventional Commits 1.0**, adaptada a documentación y escrita en español.

```
tipo(proyecto): descripción corta en minúscula, sin punto      ← máx. 72 caracteres
                                                                ← línea en blanco
Qué cambió:
- Viñeta por nota o cambio, en lenguaje llano                   ← máx. 100 caracteres por línea
- …

Por qué:
Motivo del cambio (quién lo pidió, qué problema resuelve).

Impacto: qué cambia para quien usa el sistema o proceso         ← opcional
Pendiente: lo que quedó por confirmar                           ← opcional
Refs: ADR-004, #123                                             ← opcional
```

## Tipos

| Tipo | Úsalo cuando… | Ejemplo de cabecera |
|---|---|---|
| `feat` | Se documenta un **proyecto nuevo** o una sección grande nueva (ej. toda la operación) | `feat(app-encuestas): crea la documentación del proyecto` |
| `docs` | Contenido nuevo o actualizado — **el más común** | `docs(informe-junta): agrega KPI de costo por unidad` |
| `fix` | Se corrige algo que estaba **mal**: dato, fórmula, enlace roto, diagrama que no renderiza | `fix(informe-junta): corrige fórmula de productividad` |
| `refactor` | Se **reorganiza** sin cambiar el significado: mover, renombrar, dividir notas | `refactor(cierre-contable): divide el glosario por área` |
| `style` | Solo **formato**: tablas, emojis, espacios, frontmatter sin cambio de contenido | `style(app-encuestas): unifica emojis de sección` |
| `chore` | Configuración del vault, plantillas, `.gitignore`, plugins de Obsidian | `chore(vault): agrega plantilla de runbook` |
| `revert` | Deshace un commit anterior (`git revert` lo genera solo) | `Revert "docs(informe-junta): …"` |

Un `!` después del proyecto marca un **cambio que rompe** algo para los lectores (notas movidas de lugar, enlaces externos que dejan de funcionar):
`refactor(informe-junta)!: mueve indicadores a la carpeta 40 - Datos`.

## El proyecto entre paréntesis

- Es el nombre de la carpeta del proyecto en **minúsculas, sin tildes, con guiones**: `Informe Junta` → `informe-junta`, `Cierre Contable` → `cierre-contable`.
- `vault` para cambios que no son de un proyecto (configuración, plantillas globales, `.gitignore`).
- Si un cambio toca dos proyectos **por la misma razón** (ej. renombrar un término en ambos), haz dos commits con el mismo "Por qué".

## La descripción (cabecera)

- Verbo en presente, minúscula: **agrega, actualiza, corrige, elimina, reorganiza, documenta, marca como obsoleta, reemplaza, completa**.
- Di **qué** cambió de forma concreta. Nombra la nota o el tema.
- Sin punto final, ≤ 72 caracteres en total.

| ❌ Malo | Por qué | ✅ Bueno |
|---|---|---|
| `update` | No dice nada | `docs(informe-junta): actualiza cifras de productividad a sept. 2026` |
| `docs: cambios varios` | Genérico, sin proyecto | `docs(app-encuestas): documenta despliegue con Docker` |
| `Docs(Informe Junta): Agregué el flujo.` | Mayúsculas, espacios, pasado, punto | `docs(informe-junta): agrega flujo de generación mensual` |
| `fix(informe-junta): arreglos` | No dice qué se arregló | `fix(informe-junta): corrige enlace roto al runbook de Power BI` |
| `docs(informe-junta): actualiza glosario, flujo, modelo, KPI y runbook y agrega ADR` | Mezcla intenciones, demasiado largo | Dos commits: uno `docs(...)` para el contenido y otro para el ADR |
| `docs(informe-junta): wip` | Trabajo a medias no se sube a `main` | Termina el cambio o súbelo en una rama |

## El cuerpo

- **Qué cambió**: una viñeta por nota (o grupo de notas) con el **título de la nota** entre «comillas latinas», en lenguaje llano. Menciona secciones nuevas, cambios de estado y cifras clave.
- **Por qué**: obligatorio salvo en cambios triviales (`style`, `chore` evidentes). Sale del Historial de cambios, del ADR o de lo que dijo el usuario.
- **Impacto**: cuando alguien que usa el proceso/sistema debe enterarse.
- No pegues diffs ni código largo: el diff ya está en git.

## Requerimientos e historias de usuario

- Los cambios en `15 - Requerimientos/` van en el commit del proyecto, con el pie **`Refs:`** listando los ID: `Refs: HU-003, HU-004`.
- Si una actualización de documentación hizo avanzar historias, el mismo commit las referencia: así el historial de git conecta *qué se documentó* con *qué requerimiento avanzó*.

| Situación | Cabecera |
|---|---|
| Historias nuevas | `docs(app-encuestas): agrega 5 historias de la épica EP-01` |
| Cambio de estado | `docs(app-encuestas): actualiza avance de HU-003 a en revisión` |
| Varias del sprint | `docs(app-encuestas): actualiza avance del sprint 4` |
| Replanificación | `docs(app-encuestas): replanifica EP-02 al 14 de noviembre` |
| Descartar | `docs(app-encuestas): descarta HU-006 recordatorio por WhatsApp` |

## Ejemplos completos

### Contenido nuevo + actualización
```
docs(informe-junta): agrega KPI de costo por unidad

Qué cambió:
- Nueva nota «Costo por unidad» con fórmula, ejemplo de septiembre y diagrama.
- «Flujo de generación mensual»: nueva sección «¿Y si algo sale mal?» que
  enlaza al runbook de Power BI.

Por qué:
Gerencia pidió incluir el costo por unidad en el informe de junta desde
octubre 2026.

Pendiente: confirmar si el costo incluye mano de obra indirecta.
```

### Corrección
```
fix(app-encuestas): corrige enlace roto en «Arquitectura general»

Qué cambió:
- «Arquitectura general» apuntaba a «Servicio de autenticación», que no
  existe; ahora enlaza a «Referencia API».

Por qué:
El dashboard de documentación marcaba 1 enlace roto en el proyecto.
```

### Reorganización
```
refactor(cierre-contable): renombra «Glosario contable» a «Glosario»

Qué cambió:
- Mueve `Glosario contable.md` → `Glosario.md` y actualiza los 3 enlaces.

Por qué:
Unificar el nombre con la convención del resto de proyectos.
```

### Nota obsoleta + decisión
```
docs(informe-junta): marca como obsoleto el cálculo manual del KPI

Qué cambió:
- «Cálculo manual de productividad» pasa a estado obsoleto y enlaza a su
  reemplazo, «Productividad (%)».
- Nuevo «ADR-002 Calcular KPIs solo en Power BI».

Por qué:
Había dos versiones de la cifra y no coincidían en la junta de septiembre.

Impacto: el Excel de cálculo manual deja de usarse desde noviembre.
Refs: ADR-002
```

### Configuración del vault
```
chore(vault): configura git para Obsidian

Qué cambió:
- .gitignore excluye workspace.json, .trash/ y temporales de Office.
- .gitattributes normaliza finales de línea y marca binarios.
```
