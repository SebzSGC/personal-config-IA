#!/usr/bin/env python3
"""
git_vault.py · Ayudante de git para repositorios de documentación Obsidian
(un vault/carpeta por proyecto dentro del mismo repositorio).

Comandos:
  preparar        <repo> [--init] [--remoto URL]   Configura .gitignore, .gitattributes y git para Obsidian
  estado          <repo> [--fetch] [--json]        Resume cambios agrupados por proyecto + borradores de commit
  validar-mensaje <archivo | ->                    Revisa que un mensaje de commit siga la convención
  escanear-secretos <repo> [--todo]                Busca secretos y archivos pesados en lo preparado (staged)
  instalar-hooks  <repo>                           Instala hooks commit-msg y pre-commit que hacen cumplir lo anterior

Solo usa la librería estándar de Python 3.8+ y el comando git.
Códigos de salida: 0 = OK, 1 = problemas encontrados, 2 = error de uso.
"""
import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import unicodedata
from pathlib import Path

# ───────────────────────── Convención de commits ─────────────────────────
TIPOS = {
    "feat": "Nuevo proyecto documentado o nueva sección grande",
    "docs": "Contenido nuevo o actualizado (el tipo más común)",
    "fix": "Corrige errores: enlaces rotos, datos equivocados, diagramas que no renderizan",
    "refactor": "Reorganiza (mueve, renombra, divide notas) sin cambiar el significado",
    "style": "Solo formato: espacios, tablas, emojis, frontmatter sin cambio de contenido",
    "chore": "Configuración del vault, plantillas, .gitignore, plugins de Obsidian",
    "revert": "Deshace un commit anterior",
}
MAX_CABECERA = 72
MAX_LINEA_CUERPO = 100
GENERICOS = {
    "cambios", "cambio", "update", "updates", "actualizacion", "actualización", "actualizaciones",
    "wip", "fix", "arreglos", "varios", "misc", "test", "prueba", "commit", "docs", "documentacion",
    "documentación", "ajustes", "cambios varios", "mejoras", "...", ".",
}
RE_CABECERA = re.compile(r"^(?P<tipo>[A-Za-z]+)\s*(?:\((?P<alcance>[^)]*)\))?(?P<rompe>!)?:(?P<espacio>\s*)(?P<asunto>.+)$")

# ───────────────────────── Seguridad ─────────────────────────
RE_SECRETOS = [
    (re.compile(r"(password|contraseña|passwd|pwd)\s*[:=]\s*['\"]?[^\s'\"<]{4,}", re.I), "posible contraseña"),
    (re.compile(r"(api[_-]?key|secret|token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}", re.I), "posible token/clave"),
    (re.compile(r"\b(sk|pk|ghp|gho|github_pat|xox[abp])[-_][A-Za-z0-9_]{16,}"), "posible clave de API"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "posible clave AWS"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "llave privada"),
    (re.compile(r"(Server|Data Source)=[^;]+;.*(Password|Pwd)=[^;<]+", re.I), "cadena de conexión con contraseña"),
    (re.compile(r"(postgres|mysql|mongodb(\+srv)?|redis|sqlserver)://[^:\s/]+:[^@\s<]+@", re.I), "URL con credenciales"),
]
LIMITE_AVISO_MB = 10
LIMITE_BLOQUEO_MB = 50
EXT_TEXTO = {".md", ".canvas", ".json", ".txt", ".csv", ".yml", ".yaml", ".js", ".ts", ".py", ".sql", ".dax", ".m", ".env", ".ini", ".cfg", ".xml", ".html", ".css"}

GITIGNORE = """\
# ── Obsidian: estado local de cada persona (no se comparte) ──
# (**/ = en la raíz o dentro de cada proyecto, si cada uno es un vault aparte)
**/.obsidian/workspace.json
**/.obsidian/workspace-mobile.json
**/.obsidian/workspaces.json
**/.obsidian/cache
**/.trash/

# ── Sistema operativo ──
.DS_Store
Thumbs.db
desktop.ini

# ── Archivos temporales de Office ──
~$*

# ── Generados ──
Dashboard*.html
"""

GITATTRIBUTES = """\
# Normaliza finales de línea (evita conflictos entre Windows y Mac/Linux)
* text=auto eol=lf
*.md      text eol=lf diff=markdown
*.canvas  text eol=lf
*.json    text eol=lf

# Binarios: git no intenta mezclarlos ni mostrar diff de texto
*.png  binary
*.jpg  binary
*.jpeg binary
*.gif  binary
*.webp binary
*.pdf  binary
*.docx binary
*.xlsx binary
*.pptx binary
*.pbix binary
*.zip  binary
*.excalidraw.md text eol=lf
"""

CONFIG_GIT = {
    "core.quotepath": "false",       # muestra tildes y ñ en vez de \303\261
    "pull.rebase": "true",           # historia lineal: sin commits "Merge branch main"
    "rebase.autoStash": "true",      # permite pull con cambios sin commit
    "push.autoSetupRemote": "true",  # el primer push de una rama crea su rama remota
    "fetch.prune": "true",           # limpia ramas remotas borradas
    "init.defaultBranch": "main",
}


# ───────────────────────── Utilidades ─────────────────────────
def git(repo, *args, ok=(0,), entrada=None):
    r = subprocess.run(
        ["git", "-C", str(repo), "-c", "core.quotepath=false", *args],
        capture_output=True, input=entrada,
    )
    if r.returncode not in ok:
        raise RuntimeError(f"git {' '.join(args)} falló: {r.stderr.decode('utf-8', 'replace').strip()}")
    return r.stdout.decode("utf-8", "replace")


def git_ok(repo, *args):
    try:
        return git(repo, *args)
    except RuntimeError:
        return None


def raiz_repo(ruta):
    out = git_ok(ruta, "rev-parse", "--show-toplevel")
    return Path(out.strip()) if out else None


def slug(texto):
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-") or "vault"


def leer_frontmatter(texto):
    if not texto.startswith("---"):
        return {}
    fin = texto.find("\n---", 3)
    if fin == -1:
        return {}
    datos = {}
    for linea in texto[3:fin].splitlines():
        m = re.match(r"^([\w]+)\s*:\s*(.*)$", linea)
        if m:
            datos[m.group(1)] = m.group(2).strip().strip("\"'")
    return datos


def encabezados(texto):
    dentro = False
    hs = []
    for l in texto.splitlines():
        if re.match(r"^\s*(```|~~~)", l):
            dentro = not dentro
            continue
        if not dentro:
            m = re.match(r"^(#{1,4})\s+(.+?)\s*$", l)
            if m:
                hs.append(m.group(2))
    return hs


def es_texto(ruta):
    return Path(ruta).suffix.lower() in EXT_TEXTO


def buscar_secretos(texto):
    hallazgos = []
    for n, linea in enumerate(texto.splitlines(), 1):
        if "<SECRETO" in linea:
            continue
        for rx, desc in RE_SECRETOS:
            if rx.search(linea):
                hallazgos.append((n, desc))
    return hallazgos


# ───────────────────────── modelo de vaults ─────────────────────────
def revisar_vaults(raiz):
    """Modelo recomendado: un vault por proyecto (cada carpeta de primer nivel con su .obsidian).
    Devuelve avisos si hay vaults anidados o proyectos sin configuración propia."""
    avisos = []
    proyectos = [d for d in raiz.iterdir() if d.is_dir() and not d.name.startswith(".") and any(d.rglob("*.md"))]
    con = [d.name for d in proyectos if (d / ".obsidian").is_dir()]
    sin = [d.name for d in proyectos if not (d / ".obsidian").is_dir()]
    if (raiz / ".obsidian").is_dir() and con:
        avisos.append("🛑 Vaults anidados: hay .obsidian en la raíz del repo Y dentro de "
                      f"{', '.join(con)}. Con un vault por proyecto, elimina el .obsidian de la raíz "
                      "(pide confirmación al usuario; muévelo a _to_delete/ si no es seguro borrarlo).")
    elif (raiz / ".obsidian").is_dir():
        avisos.append("ℹ️  El repo tiene .obsidian en la raíz (modelo 'un vault con todo'). "
                      "Si el modelo es un vault por proyecto, cada carpeta de proyecto debe tener su .obsidian.")
    if sin and con:
        avisos.append(f"ℹ️  Proyectos sin .obsidian propio: {', '.join(sin)}. Copia la carpeta .obsidian de "
                      f"«{con[0]}» (sin workspace*.json) para tener los mismos plugins y ajustes.")
    return avisos


# ───────────────────────── preparar ─────────────────────────
def cmd_preparar(a):
    ruta = Path(a.repo).expanduser().resolve()
    raiz = raiz_repo(ruta)
    acciones = []
    if raiz is None:
        if not a.init:
            print(f"❌ {ruta} no es un repositorio git. Vuelve a ejecutar con --init para crearlo.")
            return 1
        ruta.mkdir(parents=True, exist_ok=True)
        git(ruta, "init", "-b", "main")
        raiz = ruta
        acciones.append("Repositorio git creado (rama main)")

    def fusionar(nombre, plantilla):
        p = raiz / nombre
        actual = p.read_text(encoding="utf-8") if p.exists() else ""
        existentes = {l.strip() for l in actual.splitlines()}
        nuevas = [l for l in plantilla.splitlines() if l.strip() and not l.startswith("#") and l.strip() not in existentes]
        if not actual:
            p.write_text(plantilla, encoding="utf-8")
            acciones.append(f"{nombre} creado")
        elif nuevas:
            with p.open("a", encoding="utf-8") as f:
                f.write(("\n" if not actual.endswith("\n") else "") + "\n# Agregado por git_vault.py\n" + "\n".join(nuevas) + "\n")
            acciones.append(f"{nombre}: {len(nuevas)} reglas agregadas")

    fusionar(".gitignore", GITIGNORE)
    fusionar(".gitattributes", GITATTRIBUTES)

    for k, v in CONFIG_GIT.items():
        if (git_ok(raiz, "config", "--local", "--get", k) or "").strip() != v:
            git(raiz, "config", "--local", k, v)
            acciones.append(f"git config {k} = {v}")

    # Si workspace.json ya estaba versionado, dejar de seguirlo (sin borrarlo del disco)
    seguidos = (git_ok(raiz, "ls-files", "-z") or "").split("\0")
    for f in [x for x in seguidos if re.search(r"(^|/)\.obsidian/workspace(-mobile|s)?\.json$", x)]:
        git(raiz, "rm", "--cached", "-q", "--", f)
        acciones.append(f"{f} deja de versionarse (sigue en tu disco)")

    if a.remoto:
        if git_ok(raiz, "remote", "get-url", "origin") is None:
            git(raiz, "remote", "add", "origin", a.remoto)
            acciones.append(f"Remoto origin = {a.remoto}")
        else:
            acciones.append("Ya existe un remoto 'origin' (no se modificó)")

    nombre = (git_ok(raiz, "config", "user.name") or "").strip()
    correo = (git_ok(raiz, "config", "user.email") or "").strip()
    print(f"📁 Repositorio: {raiz}")
    for x in acciones or ["Nada que cambiar: ya estaba preparado"]:
        print(f"   ✔ {x}")
    for x in revisar_vaults(raiz):
        print(f"   {x}")
    if not nombre or not correo:
        print("   ⚠️  Falta tu identidad en git. Ejecuta:\n"
              '      git config --global user.name "Nombre Apellido"\n'
              '      git config --global user.email "tu@correo.com"')
    return 0


# ───────────────────────── estado ─────────────────────────
def leer_status(raiz):
    out = git(raiz, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    partes = out.split("\0")
    cambios = []
    i = 0
    while i < len(partes):
        e = partes[i]
        i += 1
        if not e:
            continue
        xy, ruta = e[:2], e[3:]
        anterior = None
        if xy[0] in "RC" or xy[1] in "RC":
            anterior = partes[i]
            i += 1
        cambios.append({"xy": xy, "ruta": ruta, "anterior": anterior})
    return cambios


def emparejar_renombrados(raiz, cambios, hay_head):
    """git solo detecta renombrados ya preparados (staged). Empareja 'eliminado' + 'nuevo'
    con contenido parecido (≥ 60 %) para mostrarlos como un renombrado."""
    import difflib
    borrados = [c for c in cambios if c["xy"] in (" D", "D ")]
    nuevos = [c for c in cambios if c["xy"] == "??"]
    usados = set()
    for b in borrados:
        antes = contenido_head(raiz, b["ruta"], hay_head) if es_texto(b["ruta"]) else ""
        if not antes:
            continue
        mejor, puntaje = None, 0.6
        for n in nuevos:
            if id(n) in usados or Path(n["ruta"]).suffix.lower() != Path(b["ruta"]).suffix.lower():
                continue
            actual = (raiz / n["ruta"]).read_text(encoding="utf-8", errors="replace")
            r = difflib.SequenceMatcher(None, antes, actual).quick_ratio()
            if r >= puntaje:
                mejor, puntaje = n, r
        if mejor:
            usados.add(id(mejor))
            usados.add(id(b))
            mejor["xy"], mejor["anterior"] = "R?", b["ruta"]
    return [c for c in cambios if id(c) not in usados or c["xy"] == "R?"]


def clasificar_estado(xy):
    if "U" in xy or xy in ("AA", "DD"):
        return "conflicto"
    if xy == "??":
        return "nuevo"
    if "R" in xy:
        return "renombrado"
    if "D" in xy:
        return "eliminado"
    if "A" in xy:
        return "nuevo"
    return "modificado"


def proyecto_de(ruta):
    partes = ruta.split("/")
    if len(partes) == 1 or partes[0].startswith("."):
        return None  # archivos del vault en general
    return partes[0]


def contenido_head(raiz, ruta, hay_head):
    if not hay_head:
        return ""
    return git_ok(raiz, "show", f"HEAD:{ruta}") or ""


def analizar_archivo(raiz, c, hay_head):
    ruta, est = c["ruta"], clasificar_estado(c["xy"])
    abs_ = raiz / ruta
    info = {"ruta": ruta, "estado": est, "anterior": c["anterior"], "preparado": c["xy"][0] not in " ?",
            "mas": 0, "menos": 0, "titulo": None, "tipo": None, "secciones_nuevas": [], "secciones_quitadas": [],
            "estado_doc": None, "estado_doc_antes": None, "id_req": None, "avance": None, "avance_antes": None,
            "solo_enlaces": False, "solo_metadatos": False,
            "secretos": [], "mb": 0.0}
    if abs_.exists() and abs_.is_file():
        info["mb"] = round(abs_.stat().st_size / 1024 / 1024, 2)

    actual = abs_.read_text(encoding="utf-8", errors="replace") if abs_.exists() and es_texto(ruta) else ""
    origen = c["anterior"] or ruta
    antes = contenido_head(raiz, origen, hay_head) if est != "nuevo" and es_texto(origen) else ""

    if es_texto(ruta) or es_texto(origen):
        a_l, d_l = antes.splitlines(), actual.splitlines()
        import difflib
        mas, menos = [], []
        for l in difflib.unified_diff(a_l, d_l, lineterm="", n=0):
            if l.startswith("+") and not l.startswith("+++"):
                mas.append(l[1:])
            elif l.startswith("-") and not l.startswith("---"):
                menos.append(l[1:])
        info["mas"], info["menos"] = len(mas), len(menos)
        cambiadas = [l for l in mas + menos if l.strip()]
        sin_fecha = [l for l in cambiadas if not re.match(r"^\s*(actualizado|updated|fecha)\s*:", l)]
        if est == "modificado" and sin_fecha:
            info["solo_enlaces"] = all("[[" in l for l in sin_fecha) and len(mas) == len(menos)
            fm_fin = actual.find("\n---", 3) if actual.startswith("---") else -1
            fm_lineas = set(actual[:fm_fin].splitlines()) if fm_fin > 0 else set()
            info["solo_metadatos"] = all(l in fm_lineas or re.match(r"^\s*[\w]+\s*:", l) for l in sin_fecha) and fm_fin > 0
        elif est == "modificado" and cambiadas and not sin_fecha:
            info["solo_metadatos"] = True

    if ruta.lower().endswith(".md"):
        fm_d, fm_a = leer_frontmatter(actual), leer_frontmatter(antes)
        info["titulo"] = fm_d.get("titulo") or fm_a.get("titulo") or Path(ruta).stem
        info["tipo"] = fm_d.get("tipo") or fm_a.get("tipo")
        info["estado_doc"], info["estado_doc_antes"] = fm_d.get("estado"), fm_a.get("estado")
        if (fm_d.get("tipo") or fm_a.get("tipo")) in ("historia", "requerimiento", "epica"):
            info["id_req"] = (fm_d.get("id") or fm_a.get("id") or "").upper() or None
            info["avance"], info["avance_antes"] = fm_d.get("estado_historia"), fm_a.get("estado_historia")
        h_a, h_d = encabezados(antes), encabezados(actual)
        if est == "modificado":
            info["secciones_nuevas"] = [h for h in h_d if h not in h_a][:6]
            info["secciones_quitadas"] = [h for h in h_a if h not in h_d][:6]
    if actual:
        info["secretos"] = buscar_secretos(actual)
    return info


ESTADOS_HU = {"backlog": "sin iniciar", "por-hacer": "por hacer", "en-progreso": "en progreso",
              "en-revision": "en revisión", "hecho": "hecho", "bloqueado": "bloqueado", "descartado": "descartado"}


def describir(f):
    """Una línea en lenguaje llano para el cuerpo del commit."""
    nombre = f"«{f['titulo']}»" if f["titulo"] else f"`{f['ruta'].split('/')[-1]}`"
    if f["estado"] == "nuevo":
        txt = f"Nueva nota {nombre}" if f["ruta"].endswith(".md") else f"Nuevo archivo {nombre}"
        if f["tipo"]:
            txt += f" ({f['tipo']})"
        return txt
    if f["estado"] == "eliminado":
        return f"Elimina {nombre}"
    if f["estado"] == "renombrado":
        return f"Mueve/renombra `{f['anterior']}` → `{f['ruta']}`"
    if re.search(r"(Tablero de avance|/Requerimientos)\.md$", f["ruta"]) and f["estado"] == "modificado":
        return f"Regenera {nombre} (automático)"
    if f["id_req"] and f["avance"] and f["avance"] != f["avance_antes"]:
        return f"{f['id_req']} {nombre}: {ESTADOS_HU.get(f['avance_antes'], f['avance_antes'] or 'nueva')} → {ESTADOS_HU.get(f['avance'], f['avance'])}"
    partes = [f"Actualiza {nombre}"]
    if f["estado_doc_antes"] and f["estado_doc"] and f["estado_doc_antes"] != f["estado_doc"]:
        partes.append(f"estado {f['estado_doc_antes']} → {f['estado_doc']}")
    if f["secciones_nuevas"]:
        partes.append("nuevas secciones: " + ", ".join(f["secciones_nuevas"]))
    if f["secciones_quitadas"]:
        partes.append("quita: " + ", ".join(f["secciones_quitadas"]))
    if f["solo_enlaces"]:
        partes.append("corrige enlaces")
    return " · ".join(partes)


def borrador(nombre_proyecto, archivos):
    md = [f for f in archivos if f["ruta"].endswith(".md")]
    estados = {f["estado"] for f in archivos}
    alcance = slug(nombre_proyecto) if nombre_proyecto else "vault"
    titulos = [f["titulo"] for f in md if f["titulo"]]

    def lista(ts, n=2):
        return ", ".join(f"«{t}»" for t in ts[:n]) + (f" y {len(ts) - n} más" if len(ts) > n else "")

    reqs = [f for f in md if f["id_req"]]
    nuevas_hu = [f for f in reqs if f["estado"] == "nuevo" and not f["id_req"].startswith("EP")]
    movidas = [f for f in reqs if f["estado"] != "nuevo" and f["avance"] and f["avance"] != f["avance_antes"]]
    solo_req = md and all(f["id_req"] or re.search(r"requerimientos", f["ruta"], re.I) for f in md)

    if nombre_proyecto is None:
        tipo, asunto = "chore", "actualiza configuración del vault"
    elif solo_req and nuevas_hu:
        epicas = sorted({f["id_req"] for f in reqs if f["id_req"].startswith("EP")})
        n = len(nuevas_hu)
        tipo, asunto = "docs", f"agrega {n} {'historia' if n == 1 else 'historias'}" + (f" de la épica {epicas[0]}" if len(epicas) == 1 else "")
    elif solo_req and len(movidas) == 1:
        m = movidas[0]
        tipo, asunto = "docs", f"actualiza avance de {m['id_req']} a {ESTADOS_HU.get(m['avance'], m['avance'])}"
    elif solo_req and movidas:
        tipo, asunto = "docs", f"actualiza avance de {len(movidas)} historias"
    elif all(re.search(r"(^|/)plantillas?/", f["ruta"], re.I) for f in archivos):
        tipo, asunto = "chore", "actualiza plantillas"
    elif estados == {"renombrado"}:
        tipo, asunto = "refactor", f"reorganiza {len(archivos)} {'nota' if len(archivos) == 1 else 'notas'}"
    elif any(f["estado"] == "nuevo" and re.match(r"^0+\s*-\s*inicio\.md$", f["ruta"].split("/")[-1], re.I) for f in archivos):
        tipo, asunto = "feat", f"crea la documentación de {nombre_proyecto}"
    elif md and all(f["solo_enlaces"] for f in md):
        tipo, asunto = "fix", f"corrige enlaces en {lista(titulos)}"
    elif md and all(f["solo_metadatos"] for f in md):
        tipo, asunto = "style", f"actualiza metadatos de {lista(titulos)}"
    elif any(f["estado_doc"] in ("obsoleto", "reemplazada") and f["estado_doc_antes"] not in ("obsoleto", "reemplazada") for f in md):
        obs = [f["titulo"] for f in md if f["estado_doc"] in ("obsoleto", "reemplazada")]
        tipo, asunto = "docs", f"marca como obsoleta {lista(obs, 1)}"
    elif estados == {"nuevo"}:
        tipo, asunto = "docs", f"agrega {lista(titulos)}" if titulos else f"agrega {len(archivos)} archivos"
    elif estados == {"eliminado"}:
        tipo, asunto = "docs", f"elimina {lista(titulos)}"
    else:
        nuevos = [f["titulo"] for f in md if f["estado"] == "nuevo"]
        if nuevos:
            otros = [f["titulo"] for f in md if f["estado"] != "nuevo"]
            if not otros:
                asunto = f"agrega {lista(nuevos)}"
            else:
                n_otros = f"{len(otros)} {'nota' if len(otros) == 1 else 'notas'}"
                opciones = [f"agrega {lista(nuevos, 1)} y actualiza «{otros[0]}»" if len(otros) == 1 else "",
                            f"agrega {lista(nuevos, 1)} y actualiza {n_otros}",
                            f"agrega {len(nuevos)} y actualiza {n_otros}"]
                asunto = next(o for o in opciones if o and len(f"docs({alcance}): {o}") <= MAX_CABECERA) if any(
                    o and len(f"docs({alcance}): {o}") <= MAX_CABECERA for o in opciones) else opciones[-1]
        else:
            asunto = f"actualiza {lista(titulos)}" if titulos else f"actualiza {len(archivos)} archivos"
        tipo = "docs"

    cabecera = f"{tipo}({alcance}): {asunto}"
    if len(cabecera) > MAX_CABECERA:
        cabecera = f"{tipo}({alcance}): actualiza {len(md) or len(archivos)} notas de {nombre_proyecto or 'vault'}"[:MAX_CABECERA]
    cuerpo = ["Qué cambió:"] + [f"- {describir(f)}" for f in archivos[:15]]
    if len(archivos) > 15:
        cuerpo.append(f"- … y {len(archivos) - 15} archivos más")
    cuerpo += ["", "Por qué:", "<COMPLETAR: motivo del cambio en lenguaje llano>"]
    ids = sorted({f["id_req"] for f in reqs if f["estado"] == "nuevo" or f in movidas or f["avance"]})
    if ids:
        cuerpo += ["", "Refs: " + ", ".join(ids)]
    return {"tipo": tipo, "alcance": alcance, "cabecera": cabecera, "cuerpo": "\n".join(cuerpo)}


def cmd_estado(a):
    raiz = raiz_repo(Path(a.repo).expanduser().resolve())
    if raiz is None:
        print("❌ No es un repositorio git. Usa: git_vault.py preparar <ruta> --init")
        return 2
    hay_head = git_ok(raiz, "rev-parse", "--verify", "-q", "HEAD") is not None
    rama = (git_ok(raiz, "rev-parse", "--abbrev-ref", "HEAD") or "").strip() or "main"
    remoto = (git_ok(raiz, "remote", "get-url", "origin") or "").strip() or None
    if a.fetch and remoto:
        git_ok(raiz, "fetch", "--quiet", "origin")
    upstream = (git_ok(raiz, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}") or "").strip() or None
    adelante = atras = 0
    if upstream and hay_head:
        c = (git_ok(raiz, "rev-list", "--left-right", "--count", f"HEAD...{upstream}") or "0 0").split()
        adelante, atras = int(c[0]), int(c[1])
    gitdir = Path((git_ok(raiz, "rev-parse", "--absolute-git-dir") or ".git").strip())
    operacion = None
    if (gitdir / "rebase-merge").exists() or (gitdir / "rebase-apply").exists():
        operacion = "rebase"
    elif (gitdir / "MERGE_HEAD").exists():
        operacion = "merge"

    cambios = emparejar_renombrados(raiz, leer_status(raiz), hay_head)
    grupos = {}
    conflictos, secretos, pesados = [], [], []
    for c in cambios:
        f = analizar_archivo(raiz, c, hay_head)
        if f["estado"] == "conflicto":
            conflictos.append(f["ruta"])
            continue
        for n, d in f["secretos"]:
            secretos.append({"ruta": f["ruta"], "linea": n, "tipo": d})
        if f["mb"] >= LIMITE_AVISO_MB:
            pesados.append({"ruta": f["ruta"], "mb": f["mb"]})
        grupos.setdefault(proyecto_de(f["ruta"]), []).append(f)

    propuesta = []
    for nombre in sorted(grupos, key=lambda x: (x is None, x or "")):
        archivos = sorted(grupos[nombre], key=lambda f: f["ruta"])
        b = borrador(nombre, archivos)
        rutas = sorted({f["ruta"] for f in archivos} | {f["anterior"] for f in archivos if f["anterior"]})
        propuesta.append({"proyecto": nombre or "(configuración del vault)", "rutas": rutas, "archivos": archivos, **b})

    ultimos = []
    if hay_head:
        for l in (git_ok(raiz, "log", "-5", "--format=%h\x1f%an\x1f%ar\x1f%s") or "").splitlines():
            h, an, ar, s = l.split("\x1f")
            ultimos.append({"hash": h, "autor": an, "cuando": ar, "asunto": s})

    resultado = {
        "repositorio": str(raiz), "rama": rama, "remoto": remoto, "upstream": upstream,
        "commits_sin_push": adelante, "commits_por_traer": atras, "operacion_en_curso": operacion,
        "conflictos": conflictos, "secretos": secretos, "archivos_pesados": pesados,
        "limpio": not cambios, "propuesta": propuesta, "ultimos_commits": ultimos,
        "avisos_vaults": revisar_vaults(raiz),
    }
    if a.json:
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
        return 1 if (conflictos or secretos) else 0

    print(f"📁 {raiz}  ·  rama {rama}" + (f"  ·  remoto {remoto}" if remoto else "  ·  ⚠️ sin remoto"))
    if upstream:
        print(f"   ⬆️ {adelante} commits sin subir  ·  ⬇️ {atras} commits por traer" + ("" if a.fetch else "  (usa --fetch para revisar el remoto)"))
    elif remoto:
        print("   ℹ️  La rama no tiene upstream: el primer push lo crea.")
    for x in resultado["avisos_vaults"]:
        print(f"   {x}")
    if operacion:
        print(f"   🛑 Hay un {operacion} en curso. Termínalo o cancélalo antes de seguir.")
    if conflictos:
        print("   🛑 Conflictos sin resolver:")
        for c in conflictos:
            print(f"      • {c}")
    if secretos:
        print("   🔐 POSIBLES SECRETOS (no hagas commit hasta quitarlos):")
        for s in secretos:
            print(f"      • {s['ruta']}:{s['linea']} → {s['tipo']}")
    for p in pesados:
        print(f"   🐘 {p['ruta']} pesa {p['mb']} MB" + (" → BLOQUEA el commit, usa Git LFS o guárdalo fuera del repo" if p["mb"] >= LIMITE_BLOQUEO_MB else " → considera Git LFS"))
    if not cambios:
        print("\n✅ No hay cambios pendientes.")
    for g in propuesta:
        n = len(g["archivos"])
        print(f"\n── {g['proyecto']} ({n} {'archivo' if n == 1 else 'archivos'}) ──")
        for f in g["archivos"]:
            icono = {"nuevo": "🟢", "modificado": "🟡", "eliminado": "🔴", "renombrado": "🔵"}.get(f["estado"], "•")
            print(f"   {icono} {f['ruta']}  (+{f['mas']} −{f['menos']})")
        print(f"   💬 Borrador:\n      {g['cabecera']}\n")
        for l in g["cuerpo"].splitlines():
            print(f"      {l}")
    return 1 if (conflictos or secretos) else 0


# ───────────────────────── validar-mensaje ─────────────────────────
def validar_mensaje(texto):
    lineas = [l for l in texto.replace("\r\n", "\n").split("\n") if not l.startswith("#")]
    while lineas and not lineas[-1].strip():
        lineas.pop()
    if not lineas or not lineas[0].strip():
        return ["El mensaje está vacío."]
    cab = lineas[0]
    if re.match(r"^(Merge |Revert \"|fixup! |squash! |amend! )", cab):
        return []
    errores = []
    m = RE_CABECERA.match(cab)
    if not m:
        return [f"La primera línea debe ser «tipo(proyecto): descripción». Tipos válidos: {', '.join(TIPOS)}.",
                "Ejemplo: docs(informe-junta): agrega flujo de generación mensual"]
    tipo, alcance, asunto = m.group("tipo"), m.group("alcance"), m.group("asunto")
    if tipo.lower() in TIPOS and tipo != tipo.lower():
        errores.append(f"El tipo va en minúsculas: «{tipo.lower()}», no «{tipo}».")
    elif tipo.lower() not in TIPOS:
        errores.append(f"Tipo «{tipo}» no válido. Usa uno de: {', '.join(TIPOS)}.")
    if m.group("espacio") != " " or re.search(r"\s\(|\)\s+:", cab.split(":")[0] + ":"):
        errores.append("Formato exacto: «tipo(proyecto): descripción» (sin espacio antes de «(» ni de «:», un espacio después de «:»).")
    if alcance is not None and not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", alcance):
        errores.append(f"El proyecto entre paréntesis debe ir en minúsculas, sin tildes ni espacios: «{slug(alcance)}».")
    if len(cab) > MAX_CABECERA:
        errores.append(f"La primera línea tiene {len(cab)} caracteres (máximo {MAX_CABECERA}).")
    if asunto.endswith("."):
        errores.append("La descripción no termina en punto.")
    if asunto[:1].isupper() and not re.match(r"^[A-Z]{2,}", asunto):
        errores.append("La descripción empieza en minúscula (ej.: «agrega…», no «Agrega…»).")
    if slug(asunto).replace("-", " ") in {slug(g).replace("-", " ") for g in GENERICOS} or len(asunto.split()) < 2:
        errores.append("La descripción es demasiado genérica: di QUÉ cambió (ej.: «actualiza KPI de productividad de septiembre»).")
    if "<COMPLETAR" in texto:
        errores.append("Quedó un marcador <COMPLETAR…> en el mensaje.")
    if len(lineas) > 1:
        if lineas[1].strip():
            errores.append("Deja una línea en blanco entre la primera línea y el cuerpo.")
        largas = [i + 1 for i, l in enumerate(lineas[2:], 2) if len(l) > MAX_LINEA_CUERPO and not re.match(r"^\s*(https?://|\S+:\s*https?://)", l)]
        if largas:
            errores.append(f"Líneas del cuerpo con más de {MAX_LINEA_CUERPO} caracteres: {', '.join(map(str, largas))}.")
    return errores


def cmd_validar_mensaje(a):
    texto = sys.stdin.read() if a.archivo == "-" else Path(a.archivo).read_text(encoding="utf-8", errors="replace")
    errores = validar_mensaje(texto)
    if errores:
        print("❌ Mensaje de commit no cumple la convención:", file=sys.stderr)
        for e in errores:
            print(f"   • {e}", file=sys.stderr)
        return 1
    print("✅ Mensaje de commit válido.")
    return 0


# ───────────────────────── escanear-secretos ─────────────────────────
def cmd_escanear_secretos(a):
    raiz = raiz_repo(Path(a.repo).expanduser().resolve())
    if raiz is None:
        print("❌ No es un repositorio git.")
        return 2
    if a.todo:
        rutas = [r for r in git(raiz, "ls-files", "-z").split("\0") if r]
        leer = lambda r: (raiz / r).read_text(encoding="utf-8", errors="replace") if (raiz / r).exists() else ""
        tam = lambda r: (raiz / r).stat().st_size if (raiz / r).exists() else 0
    else:
        rutas = [r for r in git(raiz, "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z").split("\0") if r]
        leer = lambda r: git_ok(raiz, "show", f":{r}") or ""
        tam = lambda r: int((git_ok(raiz, "cat-file", "-s", f":{r}") or "0").strip() or 0)
    problemas = 0
    for r in rutas:
        mb = tam(r) / 1024 / 1024
        if mb >= LIMITE_BLOQUEO_MB:
            print(f"🐘 {r}: {mb:.1f} MB supera el límite de {LIMITE_BLOQUEO_MB} MB (usa Git LFS o guárdalo fuera del repo)", file=sys.stderr)
            problemas += 1
        elif mb >= LIMITE_AVISO_MB:
            print(f"⚠️  {r}: {mb:.1f} MB (considera Git LFS)", file=sys.stderr)
        if es_texto(r):
            for n, d in buscar_secretos(leer(r)):
                print(f"🔐 {r}:{n} → {d}. Reemplázalo por <SECRETO: ver gestor de claves>", file=sys.stderr)
                problemas += 1
    if problemas:
        print(f"❌ Commit bloqueado: {problemas} problema(s) de seguridad.", file=sys.stderr)
        return 1
    print("✅ Sin secretos ni archivos excesivamente pesados.")
    return 0


# ───────────────────────── instalar-hooks ─────────────────────────
HOOK = """#!/bin/sh
# Instalado por git_vault.py (plugin obsidian-docs). Para saltarlo en un caso puntual: git commit --no-verify
DIR="$(cd "$(dirname "$0")" && pwd)"
PY="$(command -v python3 || command -v python || command -v py)"
if [ -z "$PY" ]; then echo "git_vault: no se encontró Python; se omite la verificación" >&2; exit 0; fi
exec "$PY" "$DIR/git_vault.py" {comando}
"""


def cmd_instalar_hooks(a):
    raiz = raiz_repo(Path(a.repo).expanduser().resolve())
    if raiz is None:
        print("❌ No es un repositorio git.")
        return 2
    ruta_hooks = (git_ok(raiz, "rev-parse", "--git-path", "hooks") or ".git/hooks").strip()
    hooks = (raiz / ruta_hooks) if not os.path.isabs(ruta_hooks) else Path(ruta_hooks)
    hooks.mkdir(parents=True, exist_ok=True)
    shutil.copy2(__file__, hooks / "git_vault.py")
    for nombre, comando in [("commit-msg", 'validar-mensaje "$1"'), ("pre-commit", 'escanear-secretos "$(git rev-parse --show-toplevel)"')]:
        p = hooks / nombre
        if p.exists() and "git_vault.py" not in p.read_text(encoding="utf-8", errors="replace"):
            p.rename(p.with_suffix(".anterior"))
            print(f"   ℹ️  Había un hook {nombre} previo: se guardó como {nombre}.anterior")
        p.write_text(HOOK.replace("{comando}", comando), encoding="utf-8", newline="\n")
        p.chmod(p.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        print(f"   ✔ Hook {nombre} instalado")
    print("✅ Desde ahora cada commit valida el mensaje y bloquea secretos o archivos de más de "
          f"{LIMITE_BLOQUEO_MB} MB.\n   Los hooks son locales: cada persona del equipo debe instalarlos en su equipo.")
    return 0


# ───────────────────────── main ─────────────────────────
def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Ayudante de git para vaults de Obsidian.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("preparar"); p.add_argument("repo"); p.add_argument("--init", action="store_true"); p.add_argument("--remoto")
    p = sub.add_parser("estado"); p.add_argument("repo"); p.add_argument("--fetch", action="store_true"); p.add_argument("--json", action="store_true")
    p = sub.add_parser("validar-mensaje"); p.add_argument("archivo")
    p = sub.add_parser("escanear-secretos"); p.add_argument("repo"); p.add_argument("--todo", action="store_true", help="Revisa todo el repositorio, no solo lo preparado")
    p = sub.add_parser("instalar-hooks"); p.add_argument("repo")
    a = ap.parse_args()
    try:
        return {"preparar": cmd_preparar, "estado": cmd_estado, "validar-mensaje": cmd_validar_mensaje,
                "escanear-secretos": cmd_escanear_secretos, "instalar-hooks": cmd_instalar_hooks}[a.cmd](a)
    except RuntimeError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:  # salida cortada (ej.: | head)
        sys.exit(0)
