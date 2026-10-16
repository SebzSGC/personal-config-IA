---
name: requerimientos-historias
description: Convierte notas (actas de reunión, ideas, correos, texto que pega el usuario o notas ya existentes en el vault) en requerimientos e historias de usuario con criterios de aceptación, agrupadas en épicas, dentro de la carpeta "15 - Requerimientos" del vault de Obsidian sin alterar el resto; y lleva su avance (sin iniciar, por hacer, en progreso, en revisión, hecho, bloqueado) con un Tablero de avance y un cronograma. Úsala cuando el usuario pida crear requerimientos o historias de usuario, levantar el backlog, pasar notas a historias, cambiar el estado o el avance de una historia, ver qué está en progreso o por hacer, o planificar fechas; y desde actualizar-documentacion cuando un cambio documentado avanza una historia.
---

# Requerimientos e historias de usuario

> [!note] Cómo ejecutar los scripts de este plugin
> - Las rutas `scripts/…` y `../…` de este skill son **relativas a la carpeta de este `SKILL.md`**, no a la terminal (que arranca en el proyecto abierto). Antes de ejecutar, conviértelas a ruta absoluta, p. ej. `"<carpeta de este SKILL.md>/scripts/…"` o `"<carpeta de este SKILL.md>/../documentar-proyecto-obsidian/scripts/validar_vault.py"`.
> - Ubicación habitual del plugin: `%USERPROFILE%\.gemini\config\plugins\obsidian-docs` (Windows), `~/.gemini/config/plugins/obsidian-docs` (macOS/Linux) o `.agents/plugins/obsidian-docs` dentro del proyecto.
> - Donde dice `python3`: en **Windows** usa `py -3` (o `python` si `py` no existe); en macOS/Linux, `python3`.

Objetivo: que cualquier persona abra `Tablero de avance` y sepa **qué se va a construir, en qué va cada cosa y qué está frenado**, y que el equipo técnico tenga criterios de aceptación verificables.

Herramienta: `scripts/requerimientos.py` (Python 3.8+). `<proyecto>` es la carpeta del proyecto (raíz del vault).

## Dónde vive (sin dañar la estructura del vault)

```
<Proyecto>/
├── 00 - Inicio.md                 ← solo se le AGREGA una línea con el enlace a [[Requerimientos]]
├── 10 - Visión general/ …         ← no se toca
├── 15 - Requerimientos/           ← carpeta NUEVA (encaja entre 10 y 20 sin renumerar)
│   ├── Requerimientos.md          ← índice (lo crea y mantiene el script)
│   ├── Tablero de avance.md       ← tablero + cronograma (lo regenera el script)
│   ├── Notas de origen/           ← material crudo: actas, ideas, correos
│   ├── Épicas/                    ← EP-01 …
│   └── Historias/                 ← HU-001 …, RF-001 …, RNF-001 …
├── 20 - Arquitectura/ …           ← no se toca (solo se enlaza desde «Afecta a la documentación»)
```

Si el proyecto ya tiene una carpeta cuyo nombre contiene «Requerimientos», usa esa. Nunca muevas, renombres ni reescribas notas existentes del usuario.

## Reglas (no negociables)

1. **Fuente de verdad = frontmatter de cada historia.** El tablero, el índice y el dashboard se derivan de ahí. Nunca edites a mano el bloque automático del tablero.
2. **Los ID no cambian ni se reutilizan.** Obtén el siguiente con `siguiente-id`. Una historia que ya no se hará pasa a `descartado` (no se borra).
3. **`estado` ≠ `estado_historia`.** `estado` es del documento (`borrador` mientras se refina, `vigente` cuando está lista). `estado_historia` es el avance del trabajo.
4. **Nada de inventar.** Lo que la nota no dice (fechas, responsables, estimaciones, reglas de negocio) queda vacío o como `> [!question]`. No marques criterios como cumplidos ni muevas a `hecho` sin evidencia (lo dijo el usuario, está en el código/commit, o en la documentación actualizada).
5. **Trazabilidad.** Toda historia enlaza su nota de origen; toda nota de origen lista lo que salió de ella.
6. Usa las plantillas de `references/plantillas/` y **quita los comentarios `#` y `<!-- -->` y los `{{…}}`** al crear las notas.

## Flujo A · Crear requerimientos desde notas

1. **Reunir la entrada.** Puede ser texto pegado en el chat, notas que el usuario señale del vault, o archivos. Guarda la entrada **tal cual** en `15 - Requerimientos/Notas de origen/AAAA-MM-DD <Tema>.md` (plantilla `Nota de origen.md`). Si la nota ya existe en el vault, no la copies: enlázala.
2. **Leer el contexto del proyecto** (`Resumen ejecutivo`, `Glosario`, `Actores y responsables`, flujos) para usar los mismos nombres de roles y términos.
3. **Analizar** con `references/guia-historias.md`: identificar necesidades → agrupar en épicas → redactar historias (Como / quiero / para) y requerimientos no funcionales (RNF) → criterios de aceptación Dado/Cuando/Entonces → dependencias → prioridad sugerida → dudas.
4. **Proponer antes de escribir** (si son más de 3 ítems): tabla `ID · Tipo · Título · Épica · Prioridad · Dudas` y espera el visto bueno o ajustes.
5. **Escribir** las notas (`Épicas/`, `Historias/`) con `estado: borrador`, `estado_historia: backlog` salvo que el usuario diga otra cosa. Completa «📤 Qué salió de aquí» en la nota de origen y la lista de historias en cada épica.
6. **Sincronizar:** `python3 scripts/requerimientos.py sincronizar "<proyecto>"` → calcula avances, crea/actualiza `Requerimientos.md` y `Tablero de avance.md`, y muestra alertas. Corrige errores (IDs duplicados, fechas invertidas).
7. **Conectar sin romper:** si `00 - Inicio.md` no enlaza a `[[Requerimientos]]`, agrega **una línea** en su lista de secciones (`- 📋 [[Requerimientos]] — historias de usuario y su avance · [[Tablero de avance]]`). Si existe `Mapa del proyecto.canvas`, agrega un nodo de archivo para `15 - Requerimientos/Tablero de avance.md` sin mover los existentes.
8. **Validar** con `../documentar-proyecto-obsidian/scripts/validar_vault.py "<proyecto>"` y **guardar** con el skill `git-documentacion`: `docs(<proyecto>): agrega N historias de la épica <EP>` con `Refs: EP-01, HU-001…HU-005`.

## Flujo B · Actualizar el avance

Disparadores: el usuario lo dice («la HU-003 ya está en pruebas»), o `actualizar-documentacion` documenta un cambio que corresponde a una historia.

1. **Identificar las historias afectadas**: ID mencionado por el usuario o en mensajes de commit (`Refs: HU-003`); o historias cuya sección «🔗 Afecta a la documentación» enlaza a las notas que se acaban de actualizar; o coincidencia clara de tema. Si hay duda, pregunta antes de mover.
2. **Marcar criterios cumplidos** (`- [x]`) solo con evidencia; en la bitácora, una línea de qué evidencia fue.
3. **Cambiar el estado** con el script (registra fechas y bitácora automáticamente):
   ```bash
   python3 scripts/requerimientos.py mover "<proyecto>" HU-003 en-revision --nota "Pantalla de ingreso lista; falta probar códigos inválidos"
   python3 scripts/requerimientos.py mover "<proyecto>" HU-006 bloqueado --bloqueo "TI no ha aprobado WhatsApp Business"
   ```
   Transiciones normales: `backlog → por-hacer → en-progreso → en-revision → hecho`. Para `por-hacer` la historia debe tener prioridad y, idealmente, fechas `inicio`/`fin` y responsable. Para `hecho` todos los criterios deben estar marcados (el script avisa si no).
4. **Fechas**: si cambian los plazos, edita `inicio` / `fin` en el frontmatter (formato `AAAA-MM-DD`) y anótalo en la bitácora.
5. **Sincronizar** (`sincronizar`) y revisar alertas: vencidas, bloqueadas sin motivo, avance antes que su dependencia.
6. **Guardar** con `git-documentacion`: `docs(<proyecto>): actualiza avance de HU-003 a en revisión` (o `… de 3 historias del sprint 4`) con `Refs: HU-003`.

## Flujo C · Consultar

`python3 scripts/requerimientos.py listar "<proyecto>"` (o `--estado en-progreso`, o `--json`). Responde en lenguaje llano: qué está en curso, qué sigue, qué está bloqueado y por qué, qué está vencido. Remite a `[[Tablero de avance]]` y al dashboard (pestaña Requerimientos).

## Campos del frontmatter (historia / requerimiento)

| Campo | Valores | Nota |
|---|---|---|
| `id` | `HU-001`, `RF-001`, `RNF-001` | Inmutable |
| `tipo` | `historia` · `requerimiento` | `epica` para épicas (`EP-01`) |
| `epica` | `EP-01` | Opcional pero recomendado |
| `estado_historia` | `backlog` · `por-hacer` · `en-progreso` · `en-revision` · `hecho` · `bloqueado` · `descartado` | Lo cambia `mover` |
| `prioridad` | `critica` · `alta` · `media` · `baja` | |
| `puntos` | 1, 2, 3, 5, 8, 13 | Vacío si no se ha estimado (no inventar) |
| `responsable`, `sprint` | texto | |
| `inicio`, `fin` | `AAAA-MM-DD` | Plan. `fin_real` lo pone `mover … hecho` |
| `progreso` | 0–100 | **Lo calcula el script** con criterios y tareas marcados |
| `depende_de` | `[HU-001]` | Se dibuja en el cronograma |
| `bloqueo` | texto | Obligatorio si está bloqueada |
| `origen` | `"[[Nota de origen]]"` | Trazabilidad |

## Recursos
- `references/guia-historias.md` — cómo pasar de notas a historias: INVEST, criterios, división, prioridad, ejemplos buenos y malos.
- `references/plantillas/` — Historia de usuario, Requerimiento, Épica, Nota de origen, Requerimientos (índice).
- `scripts/requerimientos.py` — `listar`, `siguiente-id`, `mover`, `sincronizar`.
