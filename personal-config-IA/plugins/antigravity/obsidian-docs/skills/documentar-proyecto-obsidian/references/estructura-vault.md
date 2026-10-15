# Estructura del vault

Basada en **Diátaxis** (tutorial · guía · referencia · explicación) adaptada a Obsidian con MOCs (Maps of Content).
**Modelo: un vault por proyecto.** La carpeta del proyecto ES el vault (tiene su propio `.obsidian/`). Si se trabaja con el repositorio de documentación, cada proyecto es una carpeta de primer nivel del repo:

```
documentacion-invamer/        ← repositorio git (NO es un vault: sin .obsidian aquí)
├── Informe Junta/            ← vault 1
│   ├── .obsidian/
│   └── 00 - Inicio.md …
└── App Encuestas/            ← vault 2
    ├── .obsidian/
    └── 00 - Inicio.md …
```

- **Proyecto nuevo:** crea la carpeta y copia `.obsidian/` de otro proyecto del repo (sin `workspace.json` ni `workspace-mobile.json`) para conservar plugins y ajustes. Si no hay ninguno, no crees `.obsidian`: Obsidian lo genera al abrir la carpeta como vault.
- **Referencias a otro proyecto:** los `[[wikilinks]]` no cruzan vaults. Usa un enlace URI: `[Informe Junta · Inicio](obsidian://open?vault=Informe%20Junta&file=00%20-%20Inicio)` y menciona el nombre del proyecto en el texto.
- Si el usuario tiene un vault personal que no es del repositorio, pregunta dónde crear el proyecto antes de escribir.

```
<Nombre del proyecto>/
├── 00 - Inicio.md                    ← Puerta de entrada (MOC principal)
├── Mapa del proyecto.canvas          ← Vista visual de todo
│
├── 10 - Visión general/
│   ├── Resumen ejecutivo.md          ← Qué es, para qué, para quién, estado (lectura de 2 min)
│   ├── Alcance y objetivos.md        ← Qué entra / qué no, indicadores de éxito
│   ├── Actores y responsables.md     ← Quién usa, quién mantiene, a quién llamar
│   └── Glosario.md                   ← Todos los términos, en lenguaje llano
│
├── 15 - Requerimientos/              ← (opcional) épicas, historias de usuario y su avance
│   ├── Requerimientos.md             ←   índice (skill requerimientos-historias)
│   ├── Tablero de avance.md          ←   tablero + cronograma, se regenera solo
│   ├── Notas de origen/  ├── Épicas/  └── Historias/
│
├── 20 - Arquitectura/                ← (en procesos: "Mapa del proceso")
│   ├── Arquitectura general.md       ← Diagrama de contexto + contenedores
│   ├── Componentes/                  ← Una nota por módulo/servicio/tabla clave/área
│   └── Integraciones.md              ← Sistemas externos y cómo se conecta
│
├── 30 - Flujos y procesos/           ← Paso a paso de lo que ocurre (diagramas de secuencia/flujo)
│
├── 40 - Datos/
│   ├── Modelo de datos.md            ← Diagrama ER + diccionario
│   └── Indicadores y métricas.md     ← KPIs, fórmulas, ejemplo de cálculo
│
├── 50 - Guías/                       ← "Cómo hago X" (orientado a tareas)
│   ├── Primeros pasos.md             ← Tutorial: de cero a funcionando
│   └── Cómo ....md
│
├── 60 - Operación/
│   ├── Despliegue.md
│   ├── Monitoreo y alertas.md
│   └── Runbooks/                     ← Qué hacer cuando X falla
│
├── 70 - Decisiones/                  ← ADRs: por qué se hizo así
│   └── ADR-001 ....md
│
├── 80 - Referencia/                  ← API, configuración, comandos, variables
│
├── 90 - Recursos/
│   ├── adjuntos/                     ← imágenes, PDFs
│   ├── FAQ.md
│   ├── Historial de cambios.md
│   └── Plantillas/                   ← copia de las plantillas para el equipo
```

## Cada carpeta numerada tiene un índice (MOC)

Nombre: igual que la carpeta sin número, ej. `20 - Arquitectura/Arquitectura.md`. Contiene:
1. Callout `[!abstract]` explicando qué hay en la carpeta en una frase.
2. Tabla con enlace, descripción de una línea y estado de cada nota.
3. (Opcional) Consulta Dataview si el usuario tiene el plugin:

````markdown
```dataview
TABLE tipo, estado, actualizado
FROM "Mi Proyecto/30 - Flujos y procesos"
SORT actualizado DESC
```
````

Siempre incluye también la tabla manual: Dataview es opcional y no todos lo tienen.

## Escalar según tamaño

| Tamaño del proyecto | Qué crear |
|---|---|
| Pequeño (script, informe, proceso simple) | `00 - Inicio`, `Resumen ejecutivo`, `Glosario`, 1 nota de flujo, 1 guía, FAQ. Sin subcarpetas si son < 8 notas. |
| Mediano (app, modelo BI, proceso de área) | Estructura completa sin `60 - Operación/Runbooks` si no hay operación 24/7. |
| Grande (plataforma, varios equipos) | Estructura completa + una subcarpeta por dominio dentro de `Componentes/`. |
