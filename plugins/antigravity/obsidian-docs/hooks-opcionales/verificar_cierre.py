#!/usr/bin/env python3
"""
verificar_cierre.py · Hook «Stop» de Antigravity (opcional) para el plugin obsidian-docs.

Cuando el agente va a terminar, revisa cada carpeta de trabajo con vinculo.py. Si la documentación
quedó atrás del código o tiene cambios sin commit, le pide UNA vez que siga el skill flujo-documentacion
(o que diga por qué no hace falta). Si el estado no cambia, no vuelve a insistir: nunca deja al agente
en un ciclo.

Entrada (stdin, JSON de Antigravity): workspacePaths, conversationId, …
Salida (stdout): {"decision": "continue", "reason": "…"} para seguir; {} para dejarlo terminar.
Ante cualquier error, deja terminar (nunca bloquea por un fallo propio).
"""
import hashlib
import json
import sys
import tempfile
from pathlib import Path

RAIZ_PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ_PLUGIN / "skills" / "flujo-documentacion" / "scripts"))


def principal():
    try:
        entrada = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        entrada = {}
    from vinculo import calcular_estado  # noqa: E402

    avisos = []
    for ws in entrada.get("workspacePaths") or []:
        if not Path(ws).is_dir():
            continue
        e = calcular_estado(ws)
        if not e.get("vinculado") or e.get("fuente") == "sin-vinculo":
            continue
        s = e.get("sugerencia")
        if s == "actualizar":
            n = e.get("commits_codigo_sin_documentar") or 0
            avisos.append(f"«{e['proyecto']}»: {n} commit(s) de código y {e.get('codigo_sin_commit', 0)} archivo(s) "
                          "sin reflejar en la documentación")
        elif s in ("guardar", "subir"):
            avisos.append(f"«{e['proyecto']}»: la documentación tiene cambios sin commit o sin subir")
    if not avisos:
        return {}

    # Insistir una sola vez por estado y conversación
    huella = hashlib.sha256(json.dumps([entrada.get("conversationId"), avisos]).encode()).hexdigest()[:16]
    marca = Path(tempfile.gettempdir()) / f"obsidian-docs-cierre-{huella}"
    if marca.exists():
        return {}
    marca.write_text("1", encoding="utf-8")
    return {
        "decision": "continue",
        "reason": ("Antes de terminar (regla ciclo-documentacion): " + "; ".join(avisos) + ". "
                   "Sigue el skill flujo-documentacion (Actualizar + Cierre: validar, historias, marca, commit, "
                   "push con confirmación). Si el cambio no afecta la documentación, dilo al usuario en una línea "
                   "y termina; si hay cambios sin commit, díselo y pregunta si los subes."),
    }


if __name__ == "__main__":
    try:
        salida = principal()
    except Exception:  # un fallo del hook nunca debe bloquear al agente
        salida = {}
    sys.stdout.write(json.dumps(salida, ensure_ascii=False))
