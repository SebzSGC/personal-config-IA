#!/usr/bin/env bash
# Conecta este repositorio con Claude Code y/o Google Antigravity (macOS / Linux) mediante enlaces simbólicos,
# y registra el repo como marketplace local de Claude Code ("personal-config-ia").
#   ./instalar.sh                  menú interactivo (o usa la config guardada)
#   ./instalar.sh --antigravity    instala únicamente para Google Antigravity
#   ./instalar.sh --claude         instala únicamente para Claude Code
#   ./instalar.sh --ambos          instala para ambas herramientas
#   ./instalar.sh --simular        muestra lo que haría sin cambiar nada
#   ./instalar.sh --desinstalar    quita los enlaces y deja una copia local
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CASA="$HOME"
MARCA="$(date +%Y%m%d-%H%M%S)"
ARCHIVO_CONFIG="$REPO/.instalacion.json"
SIMULAR=0; DESINSTALAR=0; NO_INTERACTIVO=0
OBJETIVO=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --simular) SIMULAR=1; shift ;;
    --desinstalar) DESINSTALAR=1; shift ;;
    --no-interactivo) NO_INTERACTIVO=1; shift ;;
    --antigravity) OBJETIVO="antigravity"; shift ;;
    --claude) OBJETIVO="claude"; shift ;;
    --ambos) OBJETIVO="ambos"; shift ;;
    -o|--objetivo) OBJETIVO="$2"; shift 2 ;;
    *) echo "Opción desconocida: $1"; exit 2 ;;
  esac
done

RESUMEN=()

hacer() { # hacer "descripción" comando...
  local d="$1"; shift
  if [ "$SIMULAR" = 1 ]; then echo "   (simulación) $d"; else "$@"; fi
}
corto() { echo "${1/#"$CASA"/\~}"; }
real() { (cd "$1" 2>/dev/null && pwd -P) || echo "$1"; }

enlazar() { # enlazar destino origen absorber(0|1)
  local destino="$1" origen="$2" absorber="$3" n; n="$(corto "$destino")"
  [ -d "$origen" ] || hacer "crear $origen" mkdir -p "$origen"
  if [ -L "$destino" ]; then
    if [ "$(readlink "$destino")" = "$origen" ]; then echo "   [=] $n ya apunta al repo"; return; fi
    hacer "quitar enlace viejo $n" rm "$destino"
  elif [ -d "$destino" ]; then
    if [ "$absorber" = 1 ]; then
      shopt -s dotglob nullglob
      for hijo in "$destino"/*; do
        local base; base="$(basename "$hijo")"
        if [ -e "$origen/$base" ]; then
          RESUMEN+=("Conflicto: '$base' ya existe en el repo; la versión local quedó en el respaldo de $n")
        else
          hacer "incorporar al repo $n/$base" mv "$hijo" "$origen/$base"
          RESUMEN+=("Incorporado al repo: $base (desde $n) -> haz commit")
        fi
      done
      shopt -u dotglob nullglob
    fi
    if [ "$SIMULAR" = 0 ] && [ -z "$(ls -A "$destino")" ]; then
      rmdir "$destino"
    else
      hacer "respaldar $n" mv "$destino" "$destino.respaldo-$MARCA"
      RESUMEN+=("Respaldo creado: $n.respaldo-$MARCA")
    fi
  elif [ -e "$destino" ]; then
    hacer "respaldar archivo $n" mv "$destino" "$destino.respaldo-$MARCA"
    RESUMEN+=("Respaldo creado: $n.respaldo-$MARCA")
  fi
  hacer "crear $(dirname "$destino")" mkdir -p "$(dirname "$destino")"
  hacer "enlazar $n" ln -s "$origen" "$destino"
  echo "   [+] $n -> ${origen/#$REPO/repo}"
}

desenlazar() { # desenlazar destino origen
  local destino="$1" origen="$2" n; n="$(corto "$destino")"
  if [ -L "$destino" ] && [ "$(readlink "$destino")" = "$origen" ]; then
    hacer "quitar enlace $n" rm "$destino"
    hacer "copiar el repo a $n" cp -R "$origen" "$destino"
    echo "   [-] $n ahora es una copia local (ya no sigue al repo)"
  else
    echo "   [=] $n no está enlazado al repo"
  fi
}

registrar_json() {
  local archivo="$1" ruta="$2"
  [ "$SIMULAR" = 1 ] && { echo "   (simulación) registrar $ruta en $(basename "$archivo")"; return; }
  python3 -c "
import json, os, sys
archivo, ruta = sys.argv[1], sys.argv[2]
os.makedirs(os.path.dirname(archivo), exist_ok=True)
data = {'entries': []}
if os.path.exists(archivo):
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        pass
entries = data.get('entries', [])
if not any(e.get('path', '').rstrip('/') == ruta.rstrip('/') for e in entries):
    entries.append({'path': ruta})
data['entries'] = entries
with open(archivo, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)
" "$archivo" "$ruta" 2>/dev/null || true
  echo "   [+] $(basename "$archivo") -> $ruta"
}

quitar_json() {
  local archivo="$1" ruta="$2"
  [ -f "$archivo" ] || return 0
  [ "$SIMULAR" = 1 ] && { echo "   (simulación) desregistrar $ruta de $(basename "$archivo")"; return; }
  python3 -c "
import json, os, sys
archivo, ruta = sys.argv[1], sys.argv[2]
try:
    with open(archivo, 'r', encoding='utf-8') as f:
        data = json.load(f)
    entries = [e for e in data.get('entries', []) if e.get('path', '').rstrip('/') != ruta.rstrip('/')]
    if entries:
        with open(archivo, 'w', encoding='utf-8') as f:
            json.dump({'entries': entries}, f, indent=2)
    else:
        os.remove(archivo)
except Exception:
    pass
" "$archivo" "$ruta" 2>/dev/null || true
}

silencio() { "$@" >/dev/null 2>&1 || true; }

claude_plugins() { # claude_plugins instalar|desinstalar
  local mercado="$REPO/.claude-plugin/marketplace.json"
  [ -f "$mercado" ] || return 0
  if ! command -v claude >/dev/null 2>&1; then
    if [ "$1" = instalar ]; then
      echo "   (Claude Code no está en el PATH: agrega el marketplace a mano si lo instalas después, ver README)"
    fi
    return 0
  fi
  local nombre plugins
  nombre="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["name"])' "$mercado")"
  plugins="$(python3 -c 'import json,sys; print(" ".join(p["name"] for p in json.load(open(sys.argv[1]))["plugins"]))' "$mercado")"
  if [ "$1" = instalar ]; then
    hacer "registrar marketplace $nombre en Claude Code" silencio claude plugin marketplace add "$REPO"
    for p in $plugins; do
      hacer "instalar $p@$nombre en Claude Code" silencio claude plugin install "$p@$nombre"
      echo "   [+] Claude Code: $p@$nombre"
    done
  else
    for p in $plugins; do hacer "desinstalar $p@$nombre de Claude Code" silencio claude plugin uninstall "$p@$nombre"; done
    hacer "quitar marketplace $nombre de Claude Code" silencio claude plugin marketplace remove "$nombre"
    echo "   [-] Claude Code: plugins de $nombre desinstalados"
  fi
}

guardar_config() {
  local obj="$1"
  [ "$SIMULAR" = 1 ] && return 0
  python3 -c "
import json, sys
data = {'objetivo': sys.argv[1]}
with open(sys.argv[2], 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)
" "$obj" "$ARCHIVO_CONFIG" 2>/dev/null || true
}

# ───────────────────────── Resolver Objetivo ─────────────────────────
CONFIG_GUARDADA=""
if [ -f "$ARCHIVO_CONFIG" ]; then
  CONFIG_GUARDADA="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("objetivo","").lower())' "$ARCHIVO_CONFIG" 2>/dev/null || true)"
fi

if [ -z "$OBJETIVO" ]; then
  if [ "$NO_INTERACTIVO" = 0 ] && [ "$DESINSTALAR" = 0 ] && [ -t 0 ]; then
    DEFECTO_NUM=3
    if [ "$CONFIG_GUARDADA" = "antigravity" ]; then DEFECTO_NUM=1;
    elif [ "$CONFIG_GUARDADA" = "claude" ]; then DEFECTO_NUM=2; fi

    echo
    echo "========================================================"
    echo " ¿Para qué herramientas deseas configurar este equipo?"
    echo "========================================================"
    echo "  [1] Antigravity"
    echo "  [2] Claude Code"
    echo "  [3] Ambos (Antigravity y Claude)"
    if [ -n "$CONFIG_GUARDADA" ]; then
      echo "  (Configuración actual en este equipo: $CONFIG_GUARDADA)"
    fi
    read -r -p "Selecciona una opción [1-3] (por defecto: $DEFECTO_NUM): " RESP || RESP=""
    [ -z "$RESP" ] && RESP="$DEFECTO_NUM"
    case "$RESP" in
      1|antigravity|Antigravity) OBJETIVO="antigravity" ;;
      2|claude|Claude)           OBJETIVO="claude" ;;
      3|ambos|Ambos)             OBJETIVO="ambos" ;;
      *)
        echo "Opción no reconocida, usando opción por defecto [$DEFECTO_NUM]."
        case "$DEFECTO_NUM" in
          1) OBJETIVO="antigravity" ;;
          2) OBJETIVO="claude" ;;
          *) OBJETIVO="ambos" ;;
        esac
        ;;
    esac
  else
    if [ -n "$CONFIG_GUARDADA" ]; then
      OBJETIVO="$CONFIG_GUARDADA"
    else
      OBJETIVO="ambos"
    fi
  fi
else
  case "$OBJETIVO" in
    antigravity|Antigravity) OBJETIVO="antigravity" ;;
    claude|Claude)           OBJETIVO="claude" ;;
    *)                       OBJETIVO="ambos" ;;
  esac
fi

HABILITAR_ANTIGRAVITY=0
HABILITAR_CLAUDE=0
if [ "$OBJETIVO" = "antigravity" ] || [ "$OBJETIVO" = "ambos" ]; then HABILITAR_ANTIGRAVITY=1; fi
if [ "$OBJETIVO" = "claude" ] || [ "$OBJETIVO" = "ambos" ]; then HABILITAR_CLAUDE=1; fi

CARPETAS_ANTIGRAVITY=(
  "$CASA/.gemini/config/skills|$REPO/skills"
  "$CASA/.gemini/config/agents|$REPO/agents/antigravity"
)
CARPETAS_CLAUDE=(
  "$CASA/.claude/skills|$REPO/skills"
  "$CASA/.claude/agents|$REPO/agents/claude"
)
PLUGINS_DESTINO="$CASA/.gemini/config/plugins"
PLUGINS_REPO="$REPO/plugins"
JSON_PLUGINS="$CASA/.gemini/config/plugins.json"

echo; echo "Repositorio: $REPO"
echo "Objetivo:    $OBJETIVO"
[ "$SIMULAR" = 1 ] && echo "Modo simulación: no se cambia nada."

# ───────────────────────── Desinstalar ─────────────────────────
if [ "$DESINSTALAR" = 1 ]; then
  echo; echo "Quitando enlaces (se deja una copia local de cada cosa):"
  if [ "$HABILITAR_ANTIGRAVITY" = 1 ]; then
    echo; echo "Antigravity:"
    for par in "${CARPETAS_ANTIGRAVITY[@]}"; do desenlazar "${par%%|*}" "${par##*|}"; done
    for p in "$PLUGINS_REPO"/*/; do [ -f "$p/plugin.json" ] && desenlazar "$PLUGINS_DESTINO/$(basename "$p")" "${p%/}"; done
    quitar_json "$JSON_PLUGINS" "$PLUGINS_REPO"
  fi
  if [ "$HABILITAR_CLAUDE" = 1 ]; then
    echo; echo "Claude Code:"
    for par in "${CARPETAS_CLAUDE[@]}"; do desenlazar "${par%%|*}" "${par##*|}"; done
    claude_plugins desinstalar
  fi
  if [ -f "$ARCHIVO_CONFIG" ]; then
    hacer "eliminar archivo de configuración local" rm -f "$ARCHIVO_CONFIG"
  fi
  echo; echo "Listo."; exit 0
fi

# ───────────────────────── Instalar ─────────────────────────

# ── Antigravity ──
if [ "$HABILITAR_ANTIGRAVITY" = 1 ]; then
  echo; echo "Skills y agentes de Antigravity:"
  for par in "${CARPETAS_ANTIGRAVITY[@]}"; do enlazar "${par%%|*}" "${par##*|}" 1; done

  echo; echo "Plugins de Antigravity:"
  hay=0
  for p in "$PLUGINS_REPO"/*/; do
    [ -f "$p/plugin.json" ] || continue; hay=1
    enlazar "$PLUGINS_DESTINO/$(basename "$p")" "${p%/}" 0
  done
  if [ "$hay" = 1 ]; then registrar_json "$JSON_PLUGINS" "$PLUGINS_REPO"; else echo "   (no hay plugins en el repo)"; fi
  quitar_json "$JSON_PLUGINS" "$REPO/plugins/antigravity"

  # Enlaces a plugins que ya no existen en el repo
  if [ -d "$PLUGINS_DESTINO" ]; then
    for e in "$PLUGINS_DESTINO"/*; do
      if [ -L "$e" ] && [[ "$(readlink "$e")" == "$PLUGINS_REPO"/* ]] && [ ! -e "$e" ]; then
        hacer "quitar enlace huérfano $(basename "$e")" rm "$e"
        RESUMEN+=("Plugin quitado (ya no está en el repo): $(basename "$e")")
      fi
    done
  fi
else
  # Limpiar enlaces previos si no se seleccionó Antigravity
  for par in "${CARPETAS_ANTIGRAVITY[@]}"; do
    dest="${par%%|*}"; orig="${par##*|}"
    if [ -L "$dest" ] && [ "$(readlink "$dest")" = "$orig" ]; then
      hacer "quitar enlace de Antigravity $(corto "$dest")" rm "$dest"
      RESUMEN+=("Enlace de Antigravity retirado (no seleccionado): $(corto "$dest")")
    fi
  done
  for p in "$PLUGINS_REPO"/*/; do
    [ -f "$p/plugin.json" ] || continue
    dest="$PLUGINS_DESTINO/$(basename "$p")"
    if [ -L "$dest" ] && [ "$(readlink "$dest")" = "${p%/}" ]; then
      hacer "quitar enlace de plugin de Antigravity $(basename "$p")" rm "$dest"
    fi
  done
  quitar_json "$JSON_PLUGINS" "$PLUGINS_REPO"
fi

# ── Claude Code ──
if [ "$HABILITAR_CLAUDE" = 1 ]; then
  echo; echo "Skills y agentes de Claude Code:"
  for par in "${CARPETAS_CLAUDE[@]}"; do enlazar "${par%%|*}" "${par##*|}" 1; done

  echo; echo "Plugins de Claude Code:"
  claude_plugins instalar
else
  # Limpiar enlaces previos si no se seleccionó Claude
  for par in "${CARPETAS_CLAUDE[@]}"; do
    dest="${par%%|*}"; orig="${par##*|}"
    if [ -L "$dest" ] && [ "$(readlink "$dest")" = "$orig" ]; then
      hacer "quitar enlace de Claude $(corto "$dest")" rm "$dest"
      RESUMEN+=("Enlace de Claude Code retirado (no seleccionado): $(corto "$dest")")
    fi
  done
  if [ -d "$CASA/.claude" ] && [ -z "$(ls -A "$CASA/.claude" 2>/dev/null || true)" ]; then
    hacer "eliminar carpeta vacía ~/.claude" rmdir "$CASA/.claude" 2>/dev/null || true
  fi
fi

# Guardar configuración
guardar_config "$OBJETIVO"

echo
if [ "${#RESUMEN[@]}" -gt 0 ]; then echo "Para revisar:"; for r in "${RESUMEN[@]}"; do echo "   - $r"; done; fi
if [ "$OBJETIVO" = "antigravity" ]; then
  echo "Listo. Reinicia Antigravity para que cargue los cambios."
elif [ "$OBJETIVO" = "claude" ]; then
  echo "Listo. Reinicia Claude para que cargue los cambios."
else
  echo "Listo. Reinicia Claude y Antigravity para que carguen los cambios."
fi
echo "Al agregar un plugin nuevo al repo, vuelve a ejecutar ./instalar.sh (skills y agentes no lo necesitan)."
