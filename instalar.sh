#!/usr/bin/env bash
# Conecta este repositorio con Claude y Antigravity (macOS / Linux) mediante enlaces simbólicos,
# y registra el repo como marketplace local de Claude Code ("personal-config-ia").
#   ./instalar.sh              instala o actualiza los enlaces
#   ./instalar.sh --simular    muestra lo que haría sin cambiar nada
#   ./instalar.sh --desinstalar  quita los enlaces y deja una copia local
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CASA="$HOME"
MARCA="$(date +%Y%m%d-%H%M%S)"
SIMULAR=0; DESINSTALAR=0
for a in "$@"; do
  case "$a" in
    --simular) SIMULAR=1 ;;
    --desinstalar) DESINSTALAR=1 ;;
    *) echo "Opción desconocida: $a"; exit 2 ;;
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
    echo "   (Claude Code no está en el PATH: agrega el marketplace a mano, ver README)"; return 0
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

CARPETAS=(
  "$CASA/.claude/skills|$REPO/skills"
  "$CASA/.gemini/config/skills|$REPO/skills"
  "$CASA/.claude/agents|$REPO/agents/claude"
  "$CASA/.gemini/config/agents|$REPO/agents/antigravity"
)
PLUGINS_DESTINO="$CASA/.gemini/config/plugins"
PLUGINS_REPO="$REPO/plugins"
JSON_VIEJO="$CASA/.gemini/config/plugins.json"   # registro antiguo, ya no se usa

echo; echo "Repositorio: $REPO"
[ "$SIMULAR" = 1 ] && echo "Modo simulación: no se cambia nada."

if [ "$DESINSTALAR" = 1 ]; then
  echo; echo "Quitando enlaces (se deja una copia local de cada cosa):"
  for par in "${CARPETAS[@]}"; do desenlazar "${par%%|*}" "${par##*|}"; done
  for p in "$PLUGINS_REPO"/*/; do [ -f "$p/plugin.json" ] && desenlazar "$PLUGINS_DESTINO/$(basename "$p")" "${p%/}"; done
  echo; echo "Claude Code:"; claude_plugins desinstalar
  echo; echo "Listo."; exit 0
fi

echo; echo "Skills y agentes:"
for par in "${CARPETAS[@]}"; do enlazar "${par%%|*}" "${par##*|}" 1; done

echo; echo "Plugins de Antigravity:"
hay=0
for p in "$PLUGINS_REPO"/*/; do
  [ -f "$p/plugin.json" ] || continue; hay=1
  enlazar "$PLUGINS_DESTINO/$(basename "$p")" "${p%/}" 0
done
[ "$hay" = 1 ] || echo "   (no hay plugins en el repo)"
quitar_json "$JSON_VIEJO" "$REPO/plugins/antigravity"; quitar_json "$JSON_VIEJO" "$PLUGINS_REPO"

# Enlaces a plugins que ya no existen en el repo
if [ -d "$PLUGINS_DESTINO" ]; then
  for e in "$PLUGINS_DESTINO"/*; do
    if [ -L "$e" ] && [[ "$(readlink "$e")" == "$PLUGINS_REPO"/* ]] && [ ! -e "$e" ]; then
      hacer "quitar enlace huérfano $(basename "$e")" rm "$e"
      RESUMEN+=("Plugin quitado (ya no está en el repo): $(basename "$e")")
    fi
  done
fi

echo; echo "Plugins de Claude Code:"; claude_plugins instalar

echo
if [ "${#RESUMEN[@]}" -gt 0 ]; then echo "Para revisar:"; for r in "${RESUMEN[@]}"; do echo "   - $r"; done; fi
echo "Listo. Reinicia Claude y Antigravity para que carguen los cambios."
echo "Al agregar un plugin nuevo al repo, vuelve a ejecutar ./instalar.sh (skills y agentes no lo necesitan)."
