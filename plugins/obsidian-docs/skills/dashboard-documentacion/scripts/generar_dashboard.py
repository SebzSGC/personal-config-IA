#!/usr/bin/env python3
"""
generar_dashboard.py · Genera el dashboard de la documentación en UN archivo HTML que abre con doble clic.

    python3 generar_dashboard.py [--repo R] [--guardar] [--salida S] [--titulo T] [--modo proyecto|repo] [--pull] [--abrir]

El dashboard vive en el REPOSITORIO DE VAULTS, no en el plugin:

    <repo de vaults>/
    ├── .obsidian-docs.json      ← opciones del dashboard (opcional, va a git)
    ├── _dashboard/
    │   ├── plantilla.html       ← interfaz compilada (va a git)
    │   ├── fuente/              ← código React de la interfaz (va a git; solo para cambiarla)
    │   ├── generar.py · generar-dashboard.cmd/.sh   ← lanzadores con doble clic
    │   └── Dashboard.html       ← lo que genera este script (NO va a git: .gitignore)
    └── <Proyecto A>/ <Proyecto B>/ …   ← un vault por carpeta

¿De qué repositorio? (primera opción que exista)
  1. --repo  (con --guardar queda recordado en ~/.obsidian-docs.json → "repoDocumentacion")
  2. .obsidian-docs.json en la carpeta actual o superiores: {"vault": {"repo": …}} o {"dashboard": …} (raíz del repo de vaults)
  3. ~/.obsidian-docs.json → "repoDocumentacion"
  4. Si hay terminal interactiva, lo pregunta y ofrece guardarlo

Opciones del dashboard (en <repo de vaults>/.obsidian-docs.json, todas opcionales):
  {"dashboard": {"titulo": "Documentación Invamer", "modoVault": "proyecto", "vaultObsidian": null,
                 "salida": null, "pullAntes": false}}
No necesita Node ni npm. Solo librería estándar de Python 3.8+.
"""
import argparse
import html
import json
import os
import re
import subprocess
import sys
import webbrowser
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ_PLUGIN = AQUI.parents[2]
sys.path.insert(0, str(AQUI))
from escanear import escanear_repositorio  # noqa: E402

CARPETA = "_dashboard"
PLANTILLA = "plantilla.html"
SALIDA = "Dashboard.html"
MARCADOR = "__DATOS_DASHBOARD__"
ARCHIVO = ".obsidian-docs.json"
GLOBAL = Path.home() / ARCHIVO


def leer_json(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None


def guardar_global(**valores):
    """Actualiza ~/.obsidian-docs.json sin tocar las demás claves. Solo escribe si algo cambió."""
    g = leer_json(GLOBAL)
    g = g if isinstance(g, dict) else {}
    if all(g.get(k) == v for k, v in valores.items()):
        return
    g.update(valores)
    try:
        GLOBAL.write_text(json.dumps(g, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except OSError:
        pass


def ruta(p):
    return str(p).replace("\\", "/")


def buscar_repo(arg):
    if arg:
        return Path(os.path.expanduser(arg)).resolve(), "--repo"
    d = Path.cwd().resolve()
    for p in [d, *d.parents]:
        cfg = leer_json(p / ARCHIVO)
        if not isinstance(cfg, dict):
            continue
        if isinstance(cfg.get("dashboard"), dict):
            return p, str(p / ARCHIVO)
        repo = (cfg.get("vault") or {}).get("repo")
        if repo:
            r = Path(os.path.expanduser(repo))
            return (r if r.is_absolute() else (p / r)).resolve(), str(p / ARCHIVO)
        break
    g = leer_json(GLOBAL) or {}
    if g.get("repoDocumentacion"):
        return Path(os.path.expanduser(g["repoDocumentacion"])).resolve(), str(GLOBAL)
    if sys.stdin.isatty():
        r = input("Ruta del repositorio donde guardas tus vaults: ").strip().strip('"')
        if r:
            r = Path(os.path.expanduser(r)).resolve()
            if input(f"¿Recordarla en {GLOBAL} para la próxima vez? [S/n] ").strip().lower() in ("", "s", "si", "sí", "y"):
                guardar_global(repoDocumentacion=ruta(r))
            return r, "pregunta"
    return None, None


def a_json_para_html(datos):
    s = json.dumps(datos, ensure_ascii=False, separators=(",", ":"))
    # Dentro de <script> no puede aparecer "</script>"; y los sustitutos sueltos no son UTF-8 válido
    s = s.replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    return re.sub(r"[\ud800-\udfff]", lambda m: "\\u%04x" % ord(m.group()), s)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Genera el dashboard HTML del repositorio de vaults.")
    ap.add_argument("--repo", help="Carpeta del repositorio de vaults")
    ap.add_argument("--guardar", action="store_true", help="Recordar --repo en ~/.obsidian-docs.json para la próxima vez")
    ap.add_argument("--salida", help=f"Archivo HTML a crear (por defecto <repo>/{CARPETA}/{SALIDA})")
    ap.add_argument("--titulo")
    ap.add_argument("--modo", choices=["proyecto", "repo"], help="proyecto: un vault por carpeta (predeterminado) · repo: un solo vault")
    ap.add_argument("--pull", action="store_true", help="git pull --ff-only antes de escanear")
    ap.add_argument("--abrir", action="store_true", help="Abrir el HTML al terminar")
    ap.add_argument("--json", help="Guardar también los datos del escaneo en este archivo JSON")
    a = ap.parse_args()

    repo, origen = buscar_repo(a.repo)
    if not repo:
        print("❌ No sé cuál es tu repositorio de vaults. Usa --repo \"<ruta>\" --guardar (queda recordado en "
              f"{GLOBAL}).")
        return 2
    if not repo.is_dir():
        print(f"❌ No existe la carpeta {repo}")
        return 2
    # Recordar el repo (si se pidió) y dónde está este plugin, para los lanzadores de _dashboard/
    extra = {"pluginObsidianDocs": ruta(RAIZ_PLUGIN)}
    if a.repo and a.guardar:
        extra["repoDocumentacion"] = ruta(repo)
    guardar_global(**extra)

    plantilla = repo / CARPETA / PLANTILLA
    if not plantilla.is_file():
        print(f"❌ Este repositorio no tiene {CARPETA}/{PLANTILLA}.\n"
              f"   El dashboard vive en el repo de vaults: copia la carpeta {CARPETA}/ desde otro repo de vaults "
              f"o compílala desde {CARPETA}/fuente con «npm run publicar».")
        return 2
    cfg = (leer_json(repo / ARCHIVO) or {}).get("dashboard") or {}
    titulo = a.titulo or cfg.get("titulo") or "Dashboard de documentación"
    modo = a.modo or cfg.get("modoVault") or "proyecto"
    salida = Path(os.path.expanduser(a.salida or cfg.get("salida") or str(repo / CARPETA / SALIDA))).resolve()

    print(f"📂 Repositorio de vaults: {repo}  (desde {origen})")
    if a.pull or cfg.get("pullAntes"):
        print("⬇️  git pull…")
        r = subprocess.run(["git", "-C", str(repo), "pull", "--ff-only"])
        if r.returncode != 0:
            print("⚠️  No se pudo hacer git pull (se continúa con lo que hay en disco).")

    print("🔎 Escaneando proyectos…")
    datos = escanear_repositorio(str(repo), modo)
    datos["config"] = {"titulo": titulo, "vaultObsidian": cfg.get("vaultObsidian") or datos["repositorio"], "modoVault": modo}
    for p in datos["proyectos"]:
        print(f"   • {p['nombre']}: {p['notas']} notas, {len(p['rotos'])} enlaces rotos, "
              f"{len(p['huerfanas'])} huérfanas, salud {p['salud']}/100")
    if a.json:
        Path(a.json).write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")

    texto = plantilla.read_text(encoding="utf-8")
    if texto.count(MARCADOR) != 1:
        print(f"❌ La plantilla no tiene exactamente un marcador {MARCADOR}")
        return 2
    salida_html = texto.replace(MARCADOR, a_json_para_html(datos))
    salida_html = re.sub(r"<title>.*?</title>", f"<title>{html.escape(titulo)}</title>", salida_html, count=1, flags=re.S)
    salida.parent.mkdir(parents=True, exist_ok=True)
    tmp = salida.with_name(salida.name + ".tmp")
    tmp.write_text(salida_html, encoding="utf-8", newline="\n")
    os.replace(tmp, salida)
    print(f"\n✅ Listo ({salida.stat().st_size // 1024} KB): {salida}\n   Ábrelo con doble clic; no necesita servidor ni internet.")
    if a.abrir:
        webbrowser.open(salida.as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())
