#!/usr/bin/env python3
"""
vinculo.py · Une un repositorio de código (o carpeta de trabajo) con su vault de documentación
y dice qué toca hacer: documentar, actualizar, guardar en git o nada.

Comandos:
  estado    [--ruta R] [--fetch] [--json]     Diagnóstico y sugerencia del siguiente paso
  vincular  --proyecto P [--repo R] [--ruta R] [--local]
                                              Crea/actualiza .obsidian-docs.json en la raíz del código.
                                              --repo se guarda en ~/.obsidian-docs.json (ruta de esta máquina)
                                              salvo que pases --local
  marcar    [--ruta R]                        Anota en «00 - Inicio.md» el último commit de código ya documentado

Archivos de configuración (ver references/vinculo.md):
  <raíz del código>/.obsidian-docs.json   {"vault": {"proyecto": "Informe Junta", "repo": "../docs-bi"}}
  ~/.obsidian-docs.json                   {"repoDocumentacion": "C:/Users/yo/docs-bi"}
  <raíz del repo de docs>/.obsidian-docs.json  {"dashboard": {...}}   (lo usa el dashboard)

Solo librería estándar de Python 3.8+.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ARCHIVO = ".obsidian-docs.json"
INICIO = "00 - Inicio.md"
SUGERENCIAS = {
    "vincular": "Vincular este proyecto con su vault (vinculo.py vincular --proyecto … --repo …)",
    "documentar": "Crear la documentación desde cero (skill documentar-proyecto-obsidian)",
    "actualizar": "Actualizar la documentación con los cambios de código (skill actualizar-documentacion-obsidian)",
    "guardar": "Hay cambios de documentación sin commit: cerrar con git (skill git-documentacion, flujo C)",
    "subir": "Hay commits de documentación sin subir: git pull --rebase y git push",
    "al-dia": "La documentación está al día",
}


# ───────────────────────── Utilidades ─────────────────────────
def git(cwd, *args):
    try:
        r = subprocess.run(["git", "-C", str(cwd), "-c", "core.quotepath=off", *args],
                           stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    except OSError:
        return None
    return r.stdout.decode("utf-8", "replace").strip() if r.returncode == 0 else None


def cambios_git(cwd, *rutas):
    """Archivos con cambios sin commit (git status -z: sin comillas ni escapes)."""
    try:
        r = subprocess.run(["git", "-C", str(cwd), "status", "--porcelain", "-z", "--", *rutas],
                           stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    except OSError:
        return []
    if r.returncode != 0:
        return []
    partes, out, i = r.stdout.decode("utf-8", "replace").split("\0"), [], 0
    while i < len(partes):
        e = partes[i]
        if len(e) > 3:
            out.append(e[3:])
            if e[0] in "RC":
                i += 1  # la ruta anterior del renombrado viene en la siguiente entrada
        i += 1
    return out


def leer_json(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None


def escribir_json(p, datos):
    Path(p).write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def config_global_ruta():
    return Path.home() / ARCHIVO


def buscar_local(desde):
    """Busca .obsidian-docs.json desde la carpeta dada hacia arriba."""
    d = Path(desde).resolve()
    for p in [d, *d.parents]:
        if (p / ARCHIVO).is_file():
            return p / ARCHIVO
    return None


def raiz_git(ruta):
    r = git(ruta, "rev-parse", "--show-toplevel")
    return Path(r).resolve() if r else None


def vault_contenedor(ruta):
    """Si la ruta está dentro de un vault (carpeta con .obsidian), devuelve esa carpeta."""
    d = Path(ruta).resolve()
    for p in [d, *d.parents]:
        if (p / ".obsidian").is_dir():
            return p
    return None


def leer_fm_clave(texto, clave):
    if not texto.lstrip("\ufeff").startswith("---"):
        return None
    t = texto.lstrip("\ufeff")
    fin = t.find("\n---", 3)
    m = re.search(rf"^{re.escape(clave)}\s*:\s*(.*)$", t[3:fin], re.M)
    return m.group(1).strip().strip("\"'") if m else None


# ───────────────────────── Resolución ─────────────────────────
def resolver(ruta):
    ruta = Path(ruta).resolve()
    res = {"ruta": str(ruta), "config_local": None, "codigo": None, "repo_docs": None,
           "proyecto": None, "vault": None, "fuente": None, "avisos": []}
    glob = leer_json(config_global_ruta()) or {}
    local_p = buscar_local(ruta)
    local = leer_json(local_p) if local_p else None
    if local_p and local is None:
        res["avisos"].append(f"{local_p} no es un JSON válido")

    # Caso 1: estamos dentro del propio repositorio de documentación (o de un vault)
    vault = vault_contenedor(ruta)
    if vault:
        repo = raiz_git(vault) or vault.parent
        res.update(repo_docs=str(repo), vault=str(vault), proyecto=vault.name, fuente="dentro-del-vault")
        return res

    # Caso 2: carpeta de código con .obsidian-docs.json
    if local and isinstance(local.get("vault"), dict):
        v = local["vault"]
        base = local_p.parent
        res["config_local"] = str(local_p)
        res["codigo"] = str(raiz_git(base) or base)
        repo = v.get("repo") or glob.get("repoDocumentacion")
        if repo:
            repo = Path(os.path.expanduser(repo))
            repo = (base / repo).resolve() if not repo.is_absolute() else repo.resolve()
            res["repo_docs"] = str(repo)
        else:
            res["avisos"].append("No sé dónde está el repositorio de documentación: falta «repo» en "
                                 f"{ARCHIVO} y «repoDocumentacion» en {config_global_ruta()}")
        res["proyecto"] = v.get("proyecto")
        if res["repo_docs"] and res["proyecto"]:
            res["vault"] = str(Path(res["repo_docs"]) / res["proyecto"])
        res["fuente"] = "vinculo"
        return res

    res["codigo"] = str(raiz_git(ruta) or ruta)
    res["fuente"] = "sin-vinculo"
    return res


# ───────────────────────── Comandos ─────────────────────────
def calcular_estado(ruta, fetch=False):
    r = resolver(ruta)
    e = dict(r, vinculado=r["vault"] is not None, vault_existe=False, tiene_inicio=False,
             tiene_requerimientos=False, docs_sin_commit=[], docs_por_subir=0, docs_por_traer=0,
             commit_codigo_documentado=None, commits_codigo_sin_documentar=None, codigo_sin_commit=0,
             antes=[], sugerencia=None)
    if not e["vinculado"]:
        e["sugerencia"] = "vincular"
        return e
    vault = Path(r["vault"])
    repo = Path(r["repo_docs"])
    e["vault_existe"] = vault.is_dir()
    e["tiene_inicio"] = (vault / INICIO).is_file()
    e["tiene_requerimientos"] = any(p.is_dir() and "requerimientos" in p.name.lower() for p in vault.iterdir()) if vault.is_dir() else False

    if git(repo, "rev-parse", "--is-inside-work-tree") == "true":
        if fetch:
            git(repo, "fetch", "--quiet")
        e["docs_sin_commit"] = cambios_git(repo, r["proyecto"])
        ab = git(repo, "rev-list", "--left-right", "--count", "@{u}...HEAD")
        if ab:
            detras, adelante = (int(x) for x in ab.split())
            e["docs_por_traer"], e["docs_por_subir"] = detras, adelante
    else:
        e["avisos"].append(f"{repo} no es un repositorio git")

    # Código: commits desde el último commit documentado
    codigo = Path(r["codigo"]) if r["codigo"] else None
    mismo_repo = codigo is not None and codigo.resolve() == repo.resolve()
    if codigo and not mismo_repo and git(codigo, "rev-parse", "--is-inside-work-tree") == "true":
        if e["tiene_inicio"]:
            marca = leer_fm_clave((vault / INICIO).read_text(encoding="utf-8", errors="replace"), "commit_codigo")
            e["commit_codigo_documentado"] = marca
        marca = e["commit_codigo_documentado"]
        if marca and git(codigo, "cat-file", "-e", f"{marca}^{{commit}}") is not None:
            n = git(codigo, "rev-list", "--count", f"{marca}..HEAD")
        else:
            desde = git(repo, "log", "-1", "--format=%cI", "--", r["proyecto"]) if e["vault_existe"] else None
            n = git(codigo, "rev-list", "--count", f"--since={desde}", "HEAD") if desde else None
            if marca:
                e["avisos"].append(f"El commit_codigo {marca} no existe en el repositorio de código; uso fechas")
        e["commits_codigo_sin_documentar"] = int(n) if n is not None and n.isdigit() else None
        # el propio .obsidian-docs.json no cuenta como cambio que haya que documentar
        e["codigo_sin_commit"] = len([f for f in cambios_git(codigo) if Path(f).name != ARCHIVO])

    if e["docs_por_traer"]:
        e["antes"].append("sincronizar")
    if not e["vault_existe"] or not e["tiene_inicio"]:
        e["sugerencia"] = "documentar"
    elif (e["commits_codigo_sin_documentar"] or 0) > 0 or e["codigo_sin_commit"] > 0:
        e["sugerencia"] = "actualizar"
    elif e["docs_sin_commit"]:
        e["sugerencia"] = "guardar"
    elif e["docs_por_subir"]:
        e["sugerencia"] = "subir"
    else:
        e["sugerencia"] = "al-dia"
    return e


def cmd_estado(a):
    e = calcular_estado(a.ruta, a.fetch)
    if a.json:
        print(json.dumps(e, ensure_ascii=False, indent=2))
        return 0
    print(f"📁 Trabajo: {e['codigo'] or e['ruta']}")
    if e["vinculado"]:
        print(f"📚 Vault: {e['vault']}  ({'existe' if e['vault_existe'] else 'NO existe'})")
        if e["commits_codigo_sin_documentar"] is not None:
            print(f"   Código: {e['commits_codigo_sin_documentar']} commit(s) sin documentar · {e['codigo_sin_commit']} archivo(s) sin commit")
        print(f"   Docs: {len(e['docs_sin_commit'])} archivo(s) sin commit · ⬆️ {e['docs_por_subir']} por subir · ⬇️ {e['docs_por_traer']} por traer")
    for av in e["avisos"]:
        print(f"   ⚠️ {av}")
    if e["antes"]:
        print("   Antes de nada: git pull --rebase en el repositorio de documentación")
    print(f"👉 {e['sugerencia']}: {SUGERENCIAS[e['sugerencia']]}")
    return 0


def cmd_vincular(a):
    ruta = Path(a.ruta).resolve()
    raiz = raiz_git(ruta) or ruta
    p = raiz / ARCHIVO
    datos = leer_json(p) or {}
    v = datos.setdefault("vault", {})
    v["proyecto"] = a.proyecto
    if a.repo:
        if a.local:
            v["repo"] = a.repo.replace("\\", "/")
        else:
            g = leer_json(config_global_ruta()) or {}
            g["repoDocumentacion"] = str(Path(os.path.expanduser(a.repo)).resolve()).replace("\\", "/")
            escribir_json(config_global_ruta(), g)
            print(f"✔ Repositorio de documentación guardado para esta máquina en {config_global_ruta()}")
    escribir_json(p, datos)
    print(f"✔ {p} → proyecto «{a.proyecto}»")
    e = calcular_estado(raiz)
    print(f"   Vault: {e['vault']} ({'existe' if e['vault_existe'] else 'aún no existe'}) · siguiente paso: {e['sugerencia']}")
    return 0


def cmd_marcar(a):
    r = resolver(a.ruta)
    if not r["vault"] or not r["codigo"]:
        print("❌ No hay vínculo código ↔ vault. Usa primero: vinculo.py vincular --proyecto …")
        return 2
    inicio = Path(r["vault"]) / INICIO
    if not inicio.is_file():
        print(f"❌ No existe {inicio}")
        return 2
    h = git(r["codigo"], "rev-parse", "--short", "HEAD")
    if not h:
        print("❌ El código no es un repositorio git con commits")
        return 2
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "requerimientos-historias" / "scripts"))
    from requerimientos import poner_fm
    texto = inicio.read_text(encoding="utf-8")
    inicio.write_text(poner_fm(texto, {"commit_codigo": h}), encoding="utf-8", newline="\n")
    print(f"✔ {INICIO}: commit_codigo = {h}")
    return 0


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Vínculo entre el código y su vault de documentación.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("estado"); p.add_argument("--ruta", default="."); p.add_argument("--fetch", action="store_true"); p.add_argument("--json", action="store_true")
    p = sub.add_parser("vincular"); p.add_argument("--proyecto", required=True); p.add_argument("--repo"); p.add_argument("--ruta", default="."); p.add_argument("--local", action="store_true")
    p = sub.add_parser("marcar"); p.add_argument("--ruta", default=".")
    a = ap.parse_args()
    return {"estado": cmd_estado, "vincular": cmd_vincular, "marcar": cmd_marcar}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
