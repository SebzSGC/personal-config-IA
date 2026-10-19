#!/usr/bin/env python3
"""
reglas_sesion.py · Hook «SessionStart» de Claude Code para el plugin obsidian-docs.

Claude Code no tiene «rules» como Antigravity. Este hook hace lo mismo: al iniciar la sesión, si el
proyecto abierto usa obsidian-docs (tiene .obsidian-docs.json, es un vault con .obsidian/ o está dentro
del repositorio de vaults), le pasa a Claude el texto de las reglas de rules/ como contexto.
Si el proyecto no tiene nada que ver con Obsidian, no agrega nada.

Entrada (stdin, JSON de Claude Code): cwd, source, …
Salida (stdout): {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "…"}} o nada.
Ante cualquier error no imprime nada (nunca bloquea la sesión).
"""
import json
import os
import re
import sys
from pathlib import Path

RAIZ_PLUGIN = Path(__file__).resolve().parents[1]
REGLAS = RAIZ_PLUGIN / "rules"
ORDEN = ["ciclo-documentacion.md", "estilo-obsidian.md", "git-seguro.md"]


def leer_json(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None


def aplica(cwd: Path) -> bool:
    for p in [cwd, *cwd.parents]:
        if (p / ".obsidian-docs.json").is_file() or (p / ".obsidian").is_dir():
            return True
    g = leer_json(Path.home() / ".obsidian-docs.json") or {}
    repo = g.get("repoDocumentacion")
    if repo:
        try:
            cwd.relative_to(Path(os.path.expanduser(repo)).resolve())
            return True
        except ValueError:
            pass
    return False


def sin_frontmatter(texto: str) -> str:
    return re.sub(r"\A---\s*\n.*?\n---\s*\n", "", texto, count=1, flags=re.S).strip()


def principal():
    try:
        entrada = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        entrada = {}
    cwd = Path(entrada.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()).resolve()
    if not aplica(cwd):
        return None
    partes = []
    for nombre in ORDEN:
        f = REGLAS / nombre
        if f.is_file():
            partes.append(sin_frontmatter(f.read_text(encoding="utf-8")))
    if not partes:
        return None
    texto = ("Este proyecto usa el plugin obsidian-docs. Reglas activas en esta sesión "
             "(los skills del plugin se llaman con el prefijo obsidian-docs:):\n\n" + "\n\n".join(partes))
    return {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": texto}}


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    try:
        salida = principal()
    except Exception:  # un fallo del hook nunca debe bloquear la sesión
        salida = None
    if salida:
        sys.stdout.write(json.dumps(salida, ensure_ascii=False))
