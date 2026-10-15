# 📚 obsidian-docs · Plugin para Google Antigravity

Documenta **cualquier proyecto** (software, Power BI/datos, infraestructura, automatizaciones, procesos de negocio) en un **Vault de Obsidian**, con:

- 🗂️ Estructura organizada (Diátaxis + índices MOC + numeración de carpetas)
- 🖼️ Diagramas Mermaid (contexto, secuencia, estados, ER, procesos con áreas, línea de tiempo) y un **Canvas** con el mapa del proyecto
- 🗣️ Doble nivel de lectura: resumen para no técnicos + detalle técnico plegable
- 💡 Ejemplos con datos concretos, glosario con analogías, FAQ, runbooks y decisiones (ADR)
- ✅ Validador automático (enlaces rotos, huérfanas, placeholders, secretos expuestos)
- 📋 Requerimientos e historias de usuario desde notas o reuniones, con épicas, criterios de aceptación, **tablero de avance** (sin iniciar · por hacer · en progreso · en revisión · hecho · bloqueado) y **cronograma Gantt**, que se actualizan solos al documentar
- 🔀 Gestión de git: commits atómicos por proyecto con mensajes claros (Conventional Commits en español), push seguro y hooks que bloquean secretos

## 📦 Contenido

```
obsidian-docs/
├── plugin.json
├── skills/
│   ├── documentar-proyecto-obsidian/    ← crea la documentación desde cero
│   │   ├── SKILL.md
│   │   ├── references/                  ← estructura, guía visual, plantillas, ejemplo, checklist
│   │   └── scripts/validar_vault.py     ← validador (solo Python estándar)
│   ├── actualizar-documentacion-obsidian/ ← sincroniza tras cambios, registra ADR e incidentes
│   ├── auditar-vault-obsidian/          ← califica la documentación y propone mejoras
│   ├── requerimientos-historias/        ← notas → épicas e historias de usuario; avance, tablero y cronograma
│   │   ├── SKILL.md
│   │   ├── references/                  ← guía de historias (INVEST, criterios), plantillas
│   │   └── scripts/requerimientos.py    ← listar, siguiente-id, mover, sincronizar
│   └── git-documentacion/               ← pull, commits claros por proyecto, push seguro, hooks
│       ├── SKILL.md
│       ├── references/                  ← convención de commits, solución de problemas
│       └── scripts/git_vault.py         ← preparar, estado, validar-mensaje, escanear-secretos, instalar-hooks
├── rules/
│   ├── estilo-obsidian.md               ← reglas de estilo al editar notas del vault
│   └── git-seguro.md                    ← prohíbe comandos destructivos y exige la convención de commits
└── agents/revisor-documentacion.md      ← subagente revisor independiente (solo lectura)
```

## 🚀 Instalación

**Opción A · Global (todos tus proyectos)** — copia la carpeta `obsidian-docs` a:
- Windows: `%USERPROFILE%\.gemini\config\plugins\`
- macOS / Linux: `~/.gemini/config/plugins/`

**Opción B · Solo un proyecto** — copia la carpeta a `.agents/plugins/` en la raíz del proyecto.

**Opción C · CLI**
```bash
agy plugin install /ruta/a/obsidian-docs
agy plugin list
```

Reinicia Antigravity y verifica en **Customizations** que aparezcan los 5 skills, las 2 reglas y el agente.

> Requisitos: **Python 3.8+** (validador y ayudante de git) y **Git**.

## 💬 Cómo usarlo (ejemplos de prompts)

| Quiero… | Escribe |
|---|---|
| Documentar desde cero | *"Documenta este proyecto en mi vault de Obsidian en `C:\Users\yo\Vault\Proyectos`"* |
| Documentar un proceso | *"Documenta el proceso de cierre contable mensual en Obsidian; los actores son Tesorería, Contabilidad y Gerencia"* |
| Documentar un modelo Power BI | *"Documenta el modelo de Power BI de este repositorio en Obsidian, con las medidas explicadas para gerencia"* |
| Actualizar tras cambios | *"Actualiza la documentación de Obsidian con los cambios de esta semana"* |
| Registrar una decisión | *"Registra en el vault la decisión de migrar de MySQL a PostgreSQL"* |
| Revisar calidad | *"Audita la documentación del proyecto en el vault"* |
| Crear historias desde notas | *"Con estas notas de la reunión crea las historias de usuario del proyecto App Encuestas: …"* |
| Pasar una nota del vault a historias | *"Convierte la nota «2026-09-01 Reunión con Gestión Humana» en historias de usuario"* |
| Cambiar el avance | *"La HU-003 ya está en pruebas"* · *"Bloquea la HU-006: TI no aprobó WhatsApp"* |
| Ver el estado | *"¿Qué está en progreso y qué está bloqueado en App Encuestas?"* |
| Preparar git (primera vez) | *"Prepara el repositorio git del vault en `C:\Users\yo\documentacion-invamer`"* |
| Subir cambios | *"Sube los cambios de la documentación"* · *"Haz commit y push"* |
| Traer cambios del equipo | *"Sincroniza el vault antes de empezar"* |
| Deshacer | *"Deshaz el último commit del Informe Junta"* |

### 📋 Cómo quedan los requerimientos en el vault

```
App Encuestas/
├── 00 - Inicio.md            ← se le agrega una línea: 📋 [[Requerimientos]]
├── 15 - Requerimientos/      ← carpeta nueva; el resto del vault no se toca
│   ├── Requerimientos.md     ← índice con épicas y su avance
│   ├── Tablero de avance.md  ← tablero por estado + cronograma Gantt + alertas
│   ├── Notas de origen/      ← actas e ideas tal como llegaron
│   ├── Épicas/               ← EP-01, EP-02…
│   └── Historias/            ← HU-001…, RF-001…, RNF-001…
```

El avance de cada historia sale de sus **criterios de aceptación marcados** (`- [x]`). Cuando pides *"actualiza la documentación"*, el agente revisa qué historias tocó el cambio, las mueve de estado, regenera el tablero y las referencia en el commit (`Refs: HU-003`).

### 🔀 Cómo quedan los commits

```
docs(informe-junta): agrega KPI de costo por unidad

Qué cambió:
- Nueva nota «Costo por unidad» con fórmula, ejemplo de septiembre y diagrama.
- «Flujo de generación mensual»: nueva sección «¿Y si algo sale mal?».

Por qué:
Gerencia pidió incluir el costo por unidad en el informe de octubre.
```

Un commit por proyecto, tipo (`feat`, `docs`, `fix`, `refactor`, `style`, `chore`, `revert`) y el proyecto entre paréntesis.
Así el historial de git y el dashboard cuentan qué cambió sin abrir los archivos.

Validar manualmente en cualquier momento:
```bash
python3 ~/.gemini/config/plugins/obsidian-docs/skills/documentar-proyecto-obsidian/scripts/validar_vault.py "C:/Users/yo/Vault/Proyectos/Mi proyecto"
```

## 🧩 Plugins de Obsidian recomendados (opcionales)

| Plugin | Para qué |
|---|---|
| **Dataview** | Índices automáticos por carpeta (las plantillas lo incluyen plegado) |
| **Templater** | Usar las plantillas de `90 - Recursos/Plantillas` al crear notas a mano |
| **Excalidraw** | Bocetos a mano alzada además de Mermaid |

Mermaid, Canvas, callouts y propiedades funcionan **sin plugins**.

## ✏️ Personalizar
- Plantillas → `skills/documentar-proyecto-obsidian/references/plantillas/`
- Estructura de carpetas → `references/estructura-vault.md`
- Estilo y emojis → `references/guia-visual.md` y `rules/estilo-obsidian.md`
