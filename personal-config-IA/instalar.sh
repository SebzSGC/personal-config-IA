#!/usr/bin/env bash
# Conecta este repositorio con Claude y Antigravity (macOS / Linux) mediante enlaces simbólicos.
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

CARPETAS=(
  "$CASA/.claude/skills|$REPO/skills"
  "$CASA/.gemini/config/skills|$REPO/skills"
  "$CASA/.claude/agents|$REPO/agents/claude"
  "$CASA/.gemini/config/agents|$REPO/agents/antigravity"
)
PLUGINS_DESTINO="$CASA/.gemini/config/plugins"
PLUGINS_REPO="$REPO/plugins/antigravity"

echo; echo "Repositorio: $REPO"
[ "$SIMULAR" = 1 ] && echo "Modo simulación: no se cambia nada."

if [ "$DESINSTALAR" = 1 ]; then
  echo; echo "Quitando enlaces (se deja una copia local de cada cosa):"
  for par in "${CARPETAS[@]}"; do desenlazar "${par%%|*}" "${par##*|}"; done
  for p in "$PLUGINS_REPO"/*/; do [ -d "$p" ] && desenlazar "$PLUGINS_DESTINO/$(basename "$p")" "${p%/}"; done
  echo; echo "Listo."; exit 0
fi

echo; echo "Skills y agentes:"
for par in "${CARPETAS[@]}"; do enlazar "${par%%|*}" "${par##*|}" 1; done

echo; echo "Plugins de Antigravity:"
hay=0
for p in "$PLUGINS_REPO"/*/; do
  [ -d "$p" ] || continue; hay=1
  enlazar "$PLUGINS_DESTINO/$(basename "$p")" "${p%/}" 0
done
[ "$hay" = 1 ] || echo "   (no hay plugins en el repo)"

# Enlaces a plugins que ya no existen en el repo
if [ -d "$PLUGINS_DESTINO" ]; then
  for e in "$PLUGINS_DESTINO"/*; do
    if [ -L "$e" ] && [[ "$(readlink "$e")" == "$PLUGINS_REPO"/* ]] && [ ! -e "$e" ]; then
      hacer "quitar enlace huérfano $(basename "$e")" rm "$e"
      RESUMEN+=("Plugin quitado (ya no está en el repo): $(basename "$e")")
    fi
  done
fi

echo
if [ "${#RESUMEN[@]}" -gt 0 ]; then echo "Para revisar:"; for r in "${RESUMEN[@]}"; do echo "   - $r"; done; fi
echo "Listo. Reinicia Claude y Antigravity para que carguen los cambios."
echo "Al agregar un plugin nuevo al repo, vuelve a ejecutar ./instalar.sh (skills y agentes no lo necesitan)."
