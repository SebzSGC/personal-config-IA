#!/usr/bin/env bash
# Trae los cambios del repo (git pull) y vuelve a enlazar por si hay plugins nuevos.
set -e
cd "$(dirname "${BASH_SOURCE[0]}")"
echo "Trayendo cambios de GitHub..."
git pull --ff-only || { echo "No se pudo hacer pull automático (cambios locales sin subir o conflictos). Revisa: git status"; exit 1; }
./instalar.sh "$@"
