#!/usr/bin/env python3
"""
generar_dashboard.py · Genera el dashboard de la documentación en UN archivo HTML que abre con doble clic.

    python3 generar_dashboard.py [--repo R] [--salida S] [--titulo T] [--modo proyecto|repo] [--pull] [--abrir]

No necesita Node ni npm: la interfaz ya viene compilada en ../assets/plantilla.html y este script
solo le inyecta los datos del escaneo (escanear.py).

¿De qué repositorio? (primera opción que exista)
  1. --repo
  2. .obsidian-docs.json en la carpeta actual o superiores: {"vault": {"repo": …}} o {"dashboard": …} (raíz del repo de docs)
  3. ~/.obsidian-docs.json → "repoDocumentacion"
  4. Si hay terminal interactiva, lo pregunta y ofrece guardarlo en ~/.obsidian-docs.json

Opciones del dashboard (en <repo de docs>/.obsidian-docs.json, todas opcionales):
  {"dashboard": {"titulo": "Documentación Invamer", "modoVault": "proyecto", "vaultObsidian": null,
                 "salida": "C:/Users/yo/Desktop/Dashboard documentación.html", "pullAntes": false}}
Solo librería estándar de Python 3.8+.
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
sys.path.insert(0, str(AQUI))
from escanear import escanear_repositorio  # noqa: E402

PLANTILLA = AQUI.parent / "assets" / "plantilla.html"
MARCADOR = "__DATOS_DASHBOARD__"
ARCHIVO = ".obsidian-docs.json"


def leer_json(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None


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
    g = leer_json(Path.home() / ARCHIVO) or {}
    if g.get("repoDocumentacion"):
        return Path(os.path.expanduser(g["repoDocumentacion"])).resolve(), str(Path.home() / ARCHIVO)
    if sys.stdin.isatty():
        r = input("Ruta del repositorio de documentación: ").strip().strip('"')
        if r:
            r = Path(os.path.expanduser(r)).resolve()
            if input(f"¿Guardarla en {Path.home() / ARCHIVO} para la próxima vez? [S/n] ").strip().lower() in ("", "s", "si", "sí", "y"):
                g["repoDocumentacion"] = str(r).replace("\\", "/")
                (Path.home() / ARCHIVO).write_text(json.dumps(g, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            return r, "pregunta"
    return None, None


def escritorio():
    casa = Path.home()
    for c in (casa / "Desktop", casa / "OneDrive" / "Desktop", casa / "OneDrive" / "Escritorio", casa / "Escritorio"):
        if c.is_dir():
            return c
    return casa


def a_json_para_html(datos):
    s = json.dumps(datos, ensure_ascii=False, separators=(",", ":"))
    # Dentro de <script> no puede aparecer "</script>"; y los sustitutos sueltos no son UTF-8 válido
    s = s.replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    return re.sub(r"[\ud800-\udfff]", lambda m: "\\u%04x" % ord(m.group()), s)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Genera el dashboard HTML de la documentación.")
    ap.add_argument("--repo", help="Carpeta del repositorio de documentación")
    ap.add_argument("--salida", help="Archivo HTML a crear")
    ap.add_argument("--titulo")
    ap.add_argument("--modo", choices=["proyecto", "repo"], help="proyecto: un vault por carpeta (predeterminado) · repo: un solo vault")
    ap.add_argument("--pull", action="store_true", help="git pull --ff-only antes de escanear")
    ap.add_argument("--abrir", action="store_true", help="Abrir el HTML al terminar")
    ap.add_argument("--json", help="Guardar también los datos del escaneo en este archivo JSON")
    a = ap.parse_args()

    repo, origen = buscar_repo(a.repo)
    if not repo:
        print("❌ No sé qué repositorio escanear. Usa --repo \"<ruta>\" o guarda «repoDocumentacion» en "
              f"{Path.home() / ARCHIVO}.")
        return 2
    if not repo.is_dir():
        print(f"❌ No existe la carpeta {repo}")
        return 2
    if not PLANTILLA.is_file():
        print(f"❌ Falta la plantilla {PLANTILLA}. Reinstala el plugin o compílala (herramientas/vault-dashboard: npm run publicar).")
        return 2
    cfg = (leer_json(repo / ARCHIVO) or {}).get("dashboard") or {}
    titulo = a.titulo or cfg.get("titulo") or "Dashboard de documentación"
    modo = a.modo or cfg.get("modoVault") or "proyecto"
    salida = Path(os.path.expanduser(a.salida or cfg.get("salida") or str(escritorio() / "Dashboard documentación.html"))).resolve()

    print(f"📂 Repositorio: {repo}  (desde {origen})")
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

    plantilla = PLANTILLA.read_text(encoding="utf-8")
    if plantilla.count(MARCADOR) != 1:
        print(f"❌ La plantilla no tiene exactamente un marcador {MARCADOR}")
        return 2
    salida_html = plantilla.replace(MARCADOR, a_json_para_html(datos))
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
