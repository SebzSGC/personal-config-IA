# 🔗 Vínculo código ↔ vault (`.obsidian-docs.json`)

El agente que trabaja en un repositorio de código necesita saber **dónde está su documentación**. Ese dato vive en un archivo pequeño, `.obsidian-docs.json`, que puede estar en tres lugares:

| Dónde | Contenido | ¿Va a git? |
|---|---|---|
| Raíz del **repositorio de código** | `{"vault": {"proyecto": "Informe Junta"}}` | ✅ Sí, con el código: es igual para todo el equipo |
| `~/.obsidian-docs.json` (carpeta de usuario) | `{"repoDocumentacion": "C:/Users/yo/docs-bi"}` | ❌ No: es la ruta de **esta** máquina |
| Raíz del **repositorio de documentación** | `{"dashboard": {"titulo": "Documentación Invamer"}}` | ✅ Sí (opcional, opciones del dashboard) |

`vinculo.py` combina los tres: toma el **proyecto** del archivo del código y la **ruta del repo de documentación** de tu carpeta de usuario. Así el mismo `.obsidian-docs.json` funciona en todos los equipos aunque cada persona tenga el repo de docs en una ruta distinta.

## Crear el vínculo

```bash
# Desde la raíz del repositorio de código
python3 vinculo.py vincular --proyecto "Informe Junta" --repo "C:/Users/yo/docs-bi"
```

- Crea `.obsidian-docs.json` en la raíz del código con el nombre del proyecto.
- Guarda la ruta del repo de docs en `~/.obsidian-docs.json` (vale para todos tus proyectos).
- `--local` la guarda en el archivo del código en vez de en tu carpeta de usuario. Úsalo solo con una ruta **relativa** (p. ej. `"../docs-bi"`) cuando código y docs estén siempre lado a lado.

El nombre del proyecto es el de la carpeta dentro del repo de documentación (`docs-bi/Informe Junta/`), que a su vez es el vault que se abre en Obsidian.

## Casos

| Caso | Cómo queda |
|---|---|
| Un repo de docs con varios proyectos (lo normal) | Cada repo de código tiene su `.obsidian-docs.json` con su `proyecto`; todos usan la misma `repoDocumentacion` |
| Proyecto sin código (proceso, negocio) | No hace falta vínculo: trabaja dentro del vault. `vinculo.py estado` detecta la carpeta `.obsidian` y usa ese vault |
| Tienes dos repos de documentación | Pon `"repo"` en el `.obsidian-docs.json` de cada código (relativo si están lado a lado) |
| El repo de código no es git | `estado` no puede contar commits; solo revisa si el vault existe y si hay cambios sin commit en la documentación |

## Marca de código documentado

Al cerrar una actualización, `vinculo.py marcar` escribe en el frontmatter de `00 - Inicio.md`:

```yaml
commit_codigo: 4f9c2ab
```

Es el último commit del código que ya está reflejado en la documentación. `estado` cuenta los commits posteriores (`git rev-list 4f9c2ab..HEAD`); si la marca no existe, compara con la fecha del último commit del vault.

## Qué responde `estado`

| Campo (`--json`) | Significado |
|---|---|
| `vault`, `vault_existe`, `tiene_inicio` | Dónde está y si ya se documentó |
| `commits_codigo_sin_documentar` | Commits de código posteriores a la marca |
| `codigo_sin_commit` | Archivos del código con cambios sin commit (sin contar `.obsidian-docs.json`) |
| `docs_sin_commit`, `docs_por_subir`, `docs_por_traer` | Estado git del vault |
| `antes` | `["sincronizar"]` si hay que hacer `pull` del repo de docs antes de nada |
| `sugerencia` | `vincular` · `documentar` · `actualizar` · `guardar` · `subir` · `al-dia` |
