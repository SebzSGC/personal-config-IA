# Guía: de notas a historias de usuario

## 1. Leer las notas como un analista

Recorre la nota de origen y clasifica cada frase:

| La frase es… | Ejemplo en una nota | Se convierte en |
|---|---|---|
| Una **necesidad** de alguien | «los operarios no tienen correo, solo celular» | Historia de usuario |
| Una **condición de calidad** | «debe aguantar 600 personas el mismo día» | Requerimiento no funcional (RNF) |
| Una **función concreta del sistema** sin un usuario claro | «exportar a Excel» | Historia (si hay quien la use) o RF |
| Una **regla** | «que sea anónima» | Criterio de aceptación de las historias afectadas (o historia propia si es transversal) |
| Una **idea sin validar** | «¿recordatorio por WhatsApp? revisar con TI» | Historia en `backlog` + `[!question]` |
| Un **problema actual** | «la encuesta en papel tarda 3 semanas en tabularse» | Contexto de la épica (objetivo / indicador) |

Agrupa las necesidades por **resultado de negocio** → cada grupo es una épica (2 a 8 historias). Una épica se nombra por el resultado: «Analizar resultados», no «Módulo de reportes».

## 2. Redactar la historia (INVEST)

```
Como <rol concreto>
quiero <capacidad, sin decir cómo se implementa>
para <beneficio medible o razón de negocio>.
```

| Letra | Significa | Pregunta de control |
|---|---|---|
| **I**ndependiente | Se puede construir sola (o la dependencia está en `depende_de`) | ¿Puede entregarse sin esperar a otra? |
| **N**egociable | Dice el qué, no el cómo | ¿Menciona tecnologías o pantallas exactas? Quítalas |
| **V**aliosa | Alguien gana algo | ¿El «para» es un beneficio real? |
| **E**stimable | El equipo entiende el alcance | ¿Hay dudas que impiden estimar? → `[!question]` |
| **S**mall (pequeña) | Cabe en un sprint (≤ 8 puntos) | Si es 13+, divídela |
| **T**esteable | Tiene criterios verificables | ¿Cada criterio se puede comprobar con sí/no? |

| ❌ Mala | Por qué | ✅ Buena |
|---|---|---|
| «Como usuario quiero un login» | Rol genérico, sin beneficio | «Como operario quiero entrar con el código de mi planta para que mi respuesta quede en mi área sin identificarme» |
| «Como admin quiero una tabla en React con filtros» | Impone la solución | «Como analista de Gestión Humana quiero filtrar resultados por planta para preparar el plan de cada jefe» |
| «El sistema debe ser rápido» | No es verificable | RNF: «responder en < 2 s para el 95 % de los envíos con 600 usuarios en la misma hora» |
| «Como operario quiero responder, ver resultados, exportar y recibir recordatorios» | Son 4 historias | Divídela por capacidad |

## 3. Criterios de aceptación (Dado / Cuando / Entonces)

- 2 a 5 por historia. Cada uno es un **checkbox**: el avance de la historia se calcula con ellos.
- Concretos y observables: textos exactos de mensajes, cifras, tiempos.
- Incluye el camino feliz **y** al menos un caso de error o borde.

```markdown
- [ ] **Código válido** — Dado un código de planta vigente, cuando lo ingreso, entonces entro a la encuesta de mi planta.
- [ ] **Código inválido** — Dado un código que no existe, cuando lo ingreso, entonces veo «Código no reconocido, revisa tu carné».
- [ ] **Ya respondió** — Dado que ya envié la encuesta, cuando vuelvo a entrar, entonces veo «Ya respondiste esta encuesta».
```

## 4. Dividir historias grandes

| Patrón | De | A |
|---|---|---|
| Por flujo (feliz / errores) | «Pagar el pedido» | «Pagar con tarjeta» + «Reintentar pago rechazado» |
| Por tipo de dato o canal | «Notificar al cliente» | «Notificar por correo» + «Notificar por WhatsApp» |
| Por regla de negocio | «Calcular comisión» | «Comisión estándar» + «Comisión con descuento por volumen» |
| Por operación (CRUD) | «Gestionar encuestas» | «Crear encuesta» + «Cerrar encuesta» + «Duplicar encuesta» |
| Por calidad (primero simple) | «Resultados en tiempo real» | «Resultados al cierre del día» → luego «en tiempo real» |

## 5. Prioridad y estimación

- **Prioridad** (sugiérela, el usuario decide): `critica` = sin esto no hay producto / riesgo legal; `alta` = parte del objetivo de la épica; `media` = mejora importante; `baja` = deseable.
- **Puntos** (Fibonacci 1-2-3-5-8-13): **solo** si el usuario o el equipo los da. Si no, déjalos vacíos: el tablero mostrará «sin estimación».
- **Fechas** (`inicio`, `fin`): solo si están acordadas. Una historia sin fechas aparece en «Sin fechas planificadas», no en el cronograma.

## 6. Qué escribir en «🔗 Afecta a la documentación»

Las notas del vault que cambiarán cuando la historia se construya (flujos, componentes, modelo de datos, guías). Esto permite que, al actualizar la documentación, el agente sepa qué historia avanzó. Si la nota aún no existe, no la enlaces (sería un enlace roto): escribe su nombre sin corchetes.

## 7. Ejemplo completo: de la nota a las historias

**Nota de origen (fragmento):**
> - los operarios no tienen correo corporativo, solo celular
> - que sea anónima!! (si no, no responden con sinceridad)
> - debe aguantar 600 personas respondiendo el mismo día

**Resultado:**

| ID | Tipo | Título | Épica | Prioridad | Duda |
|---|---|---|---|---|---|
| HU-001 | Historia | Responder la encuesta desde el celular | EP-01 | crítica | — |
| HU-002 | Historia | Garantizar el anonimato | EP-01 | crítica | ¿Legal debe aprobar? |
| RNF-001 | Requerimiento | Soportar 600 respuestas simultáneas | EP-01 | alta | ¿En una hora o en el día? |

HU-002 en detalle:

```markdown
## 🙋 Historia
**Como** operario
**quiero** que mi respuesta no se pueda relacionar con mi nombre ni mi cédula
**para** responder con sinceridad.

## ✅ Criterios de aceptación
- [ ] Dado que respondo, entonces la base de datos no guarda nombre, cédula ni teléfono.
- [ ] Dado un área con menos de 5 respuestas, entonces sus resultados no se muestran por separado.
- [ ] Legal revisa y aprueba el tratamiento de datos.
```

## 8. Mensajes de commit de requerimientos

| Situación | Mensaje |
|---|---|
| Historias nuevas | `docs(app-encuestas): agrega 5 historias de la épica EP-01` · `Refs: EP-01, HU-001, HU-002…` |
| Cambio de estado | `docs(app-encuestas): actualiza avance de HU-003 a en revisión` · `Refs: HU-003` |
| Varias del sprint | `docs(app-encuestas): actualiza avance del sprint 4` (cuerpo: una viñeta por historia) |
| Replanificación | `docs(app-encuestas): replanifica EP-02 al 14 de noviembre` (cuerpo: el porqué) |
| Descartar | `docs(app-encuestas): descarta HU-006 recordatorio por WhatsApp` (cuerpo: la decisión) |
