#!/usr/bin/env python3
"""
escanear.py · Lee un repositorio de documentación (un vault de Obsidian por carpeta de primer nivel)
y produce el JSON que muestra el dashboard.

    python3 escanear.py --repo "<ruta del repositorio>" [--modo proyecto|repo] [--salida datos.json]

Solo librería estándar de Python 3.8+ y git en el PATH (si no hay git, usa las fechas de los archivos).
Las reglas de estados y avance de historias se importan de requerimientos.py (skill
requerimientos-historias), para que el tablero del vault y el dashboard digan siempre lo mismo.
"""
import argparse
import datetime as dt
import json
import math
import os
import re
import subprocess
import time
import sys
import unicodedata
from pathlib import Path
from urllib.parse import unquote_to_bytes

_REQ = Path(__file__).resolve().parents[2] / "requerimientos-historias" / "scripts"
sys.path.insert(0, str(_REQ))
from requerimientos import AVANCE_POR_ESTADO, ESTADOS, SINONIMOS  # noqa: E402  (única fuente de verdad)

# ───────────────────────── Configuración ─────────────────────────
CARPETAS_IGNORADAS = {".git", ".obsidian", ".trash", ".github", ".vscode", "node_modules",
                      "vault-dashboard", "_dashboard", "dashboard"}
CAMPOS_OBLIGATORIOS = ["titulo", "tipo", "estado", "audiencia", "actualizado", "etiquetas"]
TIPOS_CON_DIAGRAMA = {"flujo", "arquitectura", "datos"}
MAX_CAMBIOS_RECIENTES = 15
SEMANAS_ACTIVIDAD = 12

# Equivalencias de clases Unicode: [^\W\d_] = letra · [^\W_] = letra o número · \w = letra, número o _
RE_FENCE = re.compile(r"^\s*(?:>\s*)*(```|~~~)")
RE_LINK = re.compile(r"(!?)\[\[([^\]\|#\^]*)(?:[#\^][^\]\|]*)?(?:\|[^\]]*)?\]\]")
RE_MDLINK = re.compile(r"\[[^\]]*\]\((?!https?:|mailto:|obsidian:|#)([^)\s]+\.md)(?:#[^)]*)?\)")
RE_TAG = re.compile(r"(?:^|\s)#([\w\-/]*(?:[^\W\d]|[\-/])[\w\-/]*)")
# TODO en mayúsculas: "todo" es una palabra en español
RE_PLACEHOLDER = re.compile(r"\{\{[^}]*\}\}|(?<![^\W\d_])TODO(?![^\W\d_])|(?<![A-Za-z0-9_])[Ll]orem ipsum(?![A-Za-z0-9_])")
RE_CLAVE_FM = re.compile(r"^((?:[^\W\d])[\w\-]*)\s*:\s*(.*)$")
RE_ENLACE_TXT = re.compile(r"\[\[([^\]|]*\|)?([^\]]*)\]\]")
RE_CASILLA = re.compile(r"^\s*[-*]\s+\[( |x|X)\]\s+(.*)$")


# ───────────────────────── Utilidades (mismo comportamiento que JavaScript) ─────────────────────────
def es_verdadero(v):
    """Verdad al estilo JavaScript: las listas (aunque vacías) son verdaderas; '' y None no."""
    return v is not None and v != "" and v is not False


def js_str(v):
    if v is None:
        return ""
    if isinstance(v, list):
        return ",".join(js_str(x) for x in v)
    return str(v)


def js_num(v):
    """Number(v) de JavaScript para los valores que puede traer el frontmatter."""
    if v is None:
        return math.nan
    s = js_str(v).strip()
    if s == "":
        return 0.0
    if re.fullmatch(r"[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?", s):
        return float(s)
    if re.fullmatch(r"0[xX][0-9a-fA-F]+", s):
        return float(int(s, 16))
    if s in ("Infinity", "+Infinity"):
        return math.inf
    if s == "-Infinity":
        return -math.inf
    return math.nan


def num_json(x):
    return int(x) if isinstance(x, float) and x.is_integer() else x


def js_round(x):
    return int(math.floor(x + 0.5))


def u16(s, n):
    """s.slice(0, n) contando unidades UTF-16, como JavaScript."""
    b = s.encode("utf-16-le", "surrogatepass")
    if len(b) <= 2 * n:
        return s
    return b[: 2 * n].decode("utf-16-le", "surrogatepass")


def limpiar(s):
    return re.sub(r"^[\"']|[\"']$", "", js_str(s).strip())


def decodificar(s):
    if re.search(r"%(?![0-9A-Fa-f]{2})", s):
        return s
    try:
        return unquote_to_bytes(s).decode("utf-8")
    except UnicodeDecodeError:
        return s


def slug_js(v):
    s = unicodedata.normalize("NFKD", js_str(v))
    s = re.sub(r"[̀-ͯ]", "", s).lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def _clave_letra(ch):
    base = unicodedata.normalize("NFKD", ch)
    sin_acento = "".join(c for c in base if not unicodedata.combining(c)).casefold() or ch.casefold()
    return (2, sin_acento, 1 if ch.lower() == "ñ" else 0)


def clave_es(texto, numerico=False):
    """Orden alfabético en español (aprox. a localeCompare('es', {numeric}))."""
    primaria, acentos, mayus = [], [], []
    partes = re.findall(r"\d+|\D", texto) if numerico else list(texto)
    for p in partes:
        if numerico and p.isdigit():
            primaria.append((1, int(p), 0))
        elif p.isdigit():
            primaria.append((1, int(p), 0))
        elif p.isalpha():
            primaria.append(_clave_letra(p))
        else:
            primaria.append((0, ord(p), 0))
        acentos.append(unicodedata.normalize("NFD", p).casefold())
        mayus.append(0 if p == p.lower() else 1)
    return (primaria, acentos, mayus)


def a_posix(p):
    return p.replace(os.sep, "/") if os.sep != "/" else p


def listar_archivos(d, acc=None):
    acc = [] if acc is None else acc
    try:
        entradas = sorted(os.scandir(d), key=lambda e: e.name.upper())
    except OSError:
        return acc
    for e in entradas:
        if e.name.startswith(".") or e.name in CARPETAS_IGNORADAS:
            continue
        if e.is_dir(follow_symlinks=False):
            listar_archivos(e.path, acc)
        else:
            acc.append(e.path)
    return acc


def leer_texto(p):
    with open(p, "r", encoding="utf-8", errors="replace", newline="") as f:
        return f.read()


def lineas_de(t):
    return re.split(r"\r?\n", t)


def leer_frontmatter(texto):
    """Frontmatter YAML simple: clave: valor, listas [a, b] y listas con guiones."""
    t = texto[1:] if texto.startswith("﻿") else texto
    if not t.startswith("---"):
        return None, t
    fin = t.find("\n---", 3)
    if fin == -1:
        return None, t
    fm, clave_lista = {}, None
    for linea in lineas_de(t[3:fin]):
        item = re.match(r"^\s+-\s+(.*)$", linea)
        if item and clave_lista:
            fm[clave_lista].append(limpiar(item.group(1)))
            continue
        m = RE_CLAVE_FM.match(linea)
        if not m:
            continue
        k, v = m.group(1), m.group(2).strip()
        if v == "":
            fm[k] = []
            clave_lista = k
            continue
        clave_lista = None
        if v.startswith("[") and v.endswith("]"):
            fm[k] = [x for x in (limpiar(x) for x in v[1:-1].split(",")) if x]
        else:
            fm[k] = limpiar(re.sub(r"\s+#.*$", "", v))
    cuerpo = re.sub(r"^[^\n]*\n", "", t[fin + 4:], count=1)
    return fm, cuerpo


def lineas_fuera_de_codigo(cuerpo):
    out, dentro = [], False
    for linea in lineas_de(cuerpo):
        if RE_FENCE.match(linea):
            dentro = not dentro
            continue
        if not dentro:
            out.append(linea)
    return out


def primer_resumen(cuerpo):
    lineas = lineas_de(cuerpo)
    i = next((n for n, l in enumerate(lineas) if re.match(r"^\s*>\s*\[!abstract\]", l, re.I)), -1)
    if i == -1:
        p = next((l for l in lineas if l.strip() and not l.startswith(("#", ">", "|", "```"))), None)
        return u16(p.strip(), 220) if p else ""
    partes = []
    j = i + 1
    while j < len(lineas) and re.match(r"^\s*>", lineas[j]):
        partes.append(re.sub(r"^\s*>\s?", "", lineas[j]))
        j += 1
    s = " ".join(partes).replace("**", "")
    return u16(RE_ENLACE_TXT.sub(r"\2", s).strip(), 260)


def git(repo, *args):
    try:
        r = subprocess.run(["git", "-C", str(repo), "-c", "core.quotepath=off", *args],
                           stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    except OSError:
        return None
    if r.returncode != 0:
        return None
    return r.stdout.decode("utf-8", "replace")


def iso_ms(ms):
    """Fecha ISO en UTC con milisegundos, como Date.toISOString() de JavaScript."""
    d = dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc) + dt.timedelta(milliseconds=ms)
    return d.strftime("%Y-%m-%dT%H:%M:%S.") + f"{ms % 1000:03d}Z"


def a_fecha(iso):
    return dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))


# ───────────────────────── Git ─────────────────────────
def leer_historial_git(repo):
    salida = git(repo, "log", "-n", "3000", "--format=%x1e%H%x1f%an%x1f%aI%x1f%s", "--name-only")
    if salida is None:
        return None
    commits = []
    for bloque in salida.split("\x1e"):
        if not bloque.strip():
            continue
        cabecera, *archivos = bloque.split("\n")
        hash_, autor, fecha, mensaje = (cabecera.split("\x1f") + ["", "", "", ""])[:4]
        commits.append({"hash": hash_, "autor": autor, "fecha": fecha, "mensaje": mensaje,
                        "archivos": [a.strip() for a in archivos if a.strip()]})
    return commits


# ───────────────────────── Requerimientos e historias ─────────────────────────
TIPOS_REQ = {"historia", "requerimiento", "epica"}
ORDEN_ESTADOS = list(ESTADOS)


def norm_estado(v):
    s = slug_js(v if es_verdadero(v) else "backlog")
    return s if s in ESTADOS else SINONIMOS.get(s, "backlog")


def fecha_iso(v):
    s = js_str(v) if es_verdadero(v) else ""
    return s[:10] if re.match(r"^\d{4}-\d{2}-\d{2}", s) else None


def lista(v):
    vals = v if isinstance(v, list) else ([v] if es_verdadero(v) else [])
    return [x for x in (js_str(x).upper() for x in vals) if x]


def secciones_req(cuerpo):
    out, actual, dentro = {}, "_", False
    for l in lineas_de(cuerpo):
        if re.match(r"^\s*(```|~~~)", l):
            dentro = not dentro
        m = None if dentro else re.match(r"^#{2,3}\s+(.*)$", l)
        if m:
            actual = slug_js(re.sub(r"^[\W_]+", "", m.group(1)))
            out.setdefault(actual, [])
            continue
        out.setdefault(actual, []).append("" if dentro else l)
    return out


def seccion(secs, *claves):
    for k, v in secs.items():
        if any(k.startswith(c) for c in claves):
            return v
    return []


def casillas(lineas):
    out = []
    for l in lineas:
        m = RE_CASILLA.match(l)
        if m:
            out.append({"texto": m.group(2).replace("**", "").strip(), "hecho": m.group(1).lower() == "x"})
    return out


def texto_plano(lineas):
    sel = [l for l in lineas if l.strip() and not re.match(r"^\s*#", l)
           and not re.match(r"^\s*>\s*\[!", l) and not re.match(r"^\s*<!--", l)]
    out = [RE_ENLACE_TXT.sub(r"\2", re.sub(r"^\s*>\s?", "", l).replace("**", "")).strip() for l in sel]
    return u16(" ".join(out), 500)


def construir_requerimientos(req_notas):
    if not req_notas:
        return None
    items, epicas = [], []
    for fm, cuerpo, rel, id_ in req_notas:
        tipo = js_str(fm.get("tipo")).lower()
        secs = secciones_req(cuerpo)
        nombre = os.path.basename(id_)
        base = {
            "id": js_str(fm["id"] if es_verdadero(fm.get("id")) else nombre.split(" ")[0]).upper(),
            "titulo": js_str(fm["titulo"] if es_verdadero(fm.get("titulo")) else nombre),
            "tipo": tipo,
            "nota": id_,
            "ruta": rel,
            "responsable": js_str(fm["responsable"]) if es_verdadero(fm.get("responsable")) else None,
            "actualizado": fm["actualizado"] if es_verdadero(fm.get("actualizado")) else None,
        }
        if tipo == "epica":
            base["objetivo"] = texto_plano(seccion(secs, "objetivo")) or texto_plano(seccion(secs, "_"))
            epicas.append(base)
            continue
        criterios = casillas(seccion(secs, "criterios"))
        tareas = casillas(seccion(secs, "tareas"))
        estado = norm_estado(fm.get("estado_historia"))
        marcas = criterios + tareas
        if estado == "hecho":
            progreso = 100
        elif estado == "descartado":
            progreso = 0
        elif marcas:
            progreso = js_round(100 * sum(m["hecho"] for m in marcas) / len(marcas))
        elif AVANCE_POR_ESTADO.get(estado) is not None:
            progreso = AVANCE_POR_ESTADO[estado]
        else:
            p = js_num(fm.get("progreso"))
            progreso = num_json(p) if (p == p and p != 0) else 0
        puntos = js_num(fm.get("puntos"))
        bitacora = []
        for l in seccion(secs, "bitacora"):
            if re.match(r"^\s*[-*]\s+", l):
                t = re.sub(r"^\s*[-*]\s+", "", l).replace("**", "")
                bitacora.append(RE_ENLACE_TXT.sub(r"\2", t).strip())
        base.update({
            "epica": js_str(fm["epica"]).upper() if es_verdadero(fm.get("epica")) else None,
            "estado": estado,
            "prioridad": slug_js(fm.get("prioridad")) or None,
            "puntos": num_json(puntos) if (math.isfinite(puntos) and js_str(fm.get("puntos")).strip() != "" and "puntos" in fm) else None,
            "sprint": js_str(fm["sprint"]) if es_verdadero(fm.get("sprint")) else None,
            "inicio": fecha_iso(fm.get("inicio")),
            "fin": fecha_iso(fm.get("fin")),
            "finReal": fecha_iso(fm.get("fin_real")),
            "bloqueo": js_str(fm["bloqueo"]) if es_verdadero(fm.get("bloqueo")) else None,
            "dependeDe": lista(fm.get("depende_de")),
            "progreso": progreso,
            "criterios": criterios,
            "tareas": tareas,
            "historia": texto_plano(seccion(secs, "historia", "requerimiento", "descripcion")),
            "bitacora": bitacora[-10:],
        })
        items.append(base)

    activos = [i for i in items if i["estado"] != "descartado"]

    def peso(i):
        return i["puntos"] or 1

    def promedio(lst):
        return js_round(sum(i["progreso"] * peso(i) for i in lst) / sum(peso(i) for i in lst)) if lst else 0

    for e in epicas:
        hijos = [i for i in activos if i["epica"] == e["id"]]
        e["progreso"] = promedio(hijos)
        e["items"] = len(hijos)
    orden = lambda x: clave_es(x["id"], numerico=True)  # noqa: E731
    return {
        "items": sorted(items, key=orden),
        "epicas": sorted(epicas, key=orden),
        "resumen": {
            "total": len(activos),
            "conteo": {e: sum(1 for i in items if i["estado"] == e) for e in ORDEN_ESTADOS},
            "avance": promedio(activos),
            "puntos": num_json(sum(i["puntos"] or 0 for i in activos)),
            "puntosHechos": num_json(sum(i["puntos"] or 0 for i in activos if i["estado"] == "hecho")),
        },
    }


# ───────────────────────── Escaneo de un proyecto ─────────────────────────
def escanear_proyecto(repo, nombre, commits, indice_repo):
    dir_p = os.path.join(repo, nombre)
    archivos = listar_archivos(dir_p)
    notas_abs = [a for a in archivos if a.lower().endswith(".md")]
    canvas = [a for a in archivos if a.lower().endswith(".canvas")]
    rel_de = lambda a: a_posix(os.path.relpath(a, dir_p))  # noqa: E731

    # Índice de nombres del proyecto (Obsidian resuelve por nombre de archivo)
    indice = {}

    def registrar(clave, rel):
        indice.setdefault(clave.lower(), rel)

    for a in archivos:
        rel = rel_de(a)
        base = rel.rsplit("/", 1)[-1]
        sin_ext = re.sub(r"\.[^.]+$", "", base)
        registrar(rel, rel)
        registrar(re.sub(r"\.md$", "", rel, flags=re.I), rel)
        registrar(base, rel)
        if base.lower().endswith(".md"):
            registrar(sin_ext, rel)

    tamano = sum(os.stat(a).st_size for a in archivos)
    notas, req_notas, pendientes, problemas = [], [], [], []
    aristas, rotos, etiquetas = {}, {}, {}
    enlaces_totales = palabras_totales = 0

    for a in notas_abs:
        rel = rel_de(a)
        id_ = re.sub(r"\.md$", "", rel, flags=re.I)
        fm, cuerpo = leer_frontmatter(leer_texto(a))
        lineas = lineas_fuera_de_codigo(cuerpo)
        plano = re.sub(r"[#>*_`|\-\[\]()!]", " ", "\n".join(lineas))
        palabras = len(re.findall(r"[^\W_]+", plano))
        palabras_totales += palabras
        es_plantilla = bool(re.search(r"(^|/)plantillas?(/|$)", rel, re.I))

        # Enlaces
        salientes = set()
        for linea in lineas:
            encontrados = [m.group(2) for m in RE_LINK.finditer(linea)]
            encontrados += [decodificar(m.group(1)) for m in RE_MDLINK.finditer(linea)]
            for destino in encontrados:
                destino = (destino or "").strip()
                if not destino:
                    continue
                destino = re.sub(r"\\$", "", re.sub(r"^\./", "", destino)).strip()  # [[nota\|alias]] en tablas
                enlaces_totales += 1
                k = destino.lower()
                resuelto = indice.get(k) or indice.get(k + ".md")
                if resuelto:
                    if resuelto.lower().endswith(".md"):
                        dest_id = re.sub(r"\.md$", "", resuelto, flags=re.I)
                        if dest_id != id_:
                            salientes.add(dest_id)
                            aristas[f"{id_}→{dest_id}"] = {"a": id_, "b": dest_id}
                elif indice_repo is not None and (k in indice_repo or k + ".md" in indice_repo):
                    pass  # modo "repo": enlace válido a otro proyecto, no se dibuja
                elif not es_plantilla:
                    rotos.setdefault(destino.split("/")[-1], {})[id_] = True
            for t in RE_TAG.finditer(linea):
                if re.fullmatch(r"[0-9a-fA-F]{3,8}", t.group(1)):
                    continue  # colores hex
                tag = t.group(1).lower()
                etiquetas[tag] = etiquetas.get(tag, 0) + 1
        if fm is not None:
            fm_tags = fm["etiquetas"] if fm.get("etiquetas") is not None else fm.get("tags")
        else:
            fm_tags = None
        for t in fm_tags if isinstance(fm_tags, list) else ([fm_tags] if es_verdadero(fm_tags) else []):
            tag = re.sub(r"^#", "", js_str(t)).lower()
            if tag:
                etiquetas[tag] = etiquetas.get(tag, 0) + 1

        # Pendientes por confirmar
        lin = lineas_de(cuerpo)
        for i, l in enumerate(lin):
            m = re.match(r"^\s*>\s*\[!question\][-+]?\s*(.*)$", l, re.I)
            if m:
                txt = m.group(1).strip()
                if (not txt or re.match(r"^pendiente", txt, re.I)) and i + 1 < len(lin) and lin[i + 1] and re.match(r"^\s*>", lin[i + 1]):
                    txt = re.sub(r"^\s*>\s?", "", lin[i + 1]).strip()
                if not es_plantilla:
                    pendientes.append({"nota": id_, "texto": txt or "Pendiente de confirmar"})

        # Calidad
        tipo = js_str(fm["tipo"] if (fm is not None and es_verdadero(fm.get("tipo"))) else "").lower()
        if not es_plantilla and fm is not None and tipo in TIPOS_REQ:
            req_notas.append((fm, cuerpo, rel, id_))
        nota_problemas = []
        if not es_plantilla:
            if fm is None:
                nota_problemas.append("Sin frontmatter")
            else:
                faltan = [c for c in CAMPOS_OBLIGATORIOS if c not in fm]
                if faltan:
                    nota_problemas.append("Frontmatter incompleto: falta " + ", ".join(faltan))
            if tipo != "indice" and not re.search(r"\[!abstract\]", u16(cuerpo, 2000), re.I):
                nota_problemas.append("Sin resumen [!abstract]")
            if tipo in TIPOS_CON_DIAGRAMA and "```mermaid" not in cuerpo:
                nota_problemas.append(f"Nota de tipo '{tipo}' sin diagrama")
            if any(RE_PLACEHOLDER.search(l) for l in lineas):
                nota_problemas.append("Tiene placeholders sin rellenar")
        for p in nota_problemas:
            problemas.append({"nota": id_, "problema": p})

        def campo(k):
            return fm[k] if (fm is not None and es_verdadero(fm.get(k))) else None

        notas.append({
            "id": id_,
            "ruta": rel,
            "titulo": js_str(campo("titulo")) or os.path.basename(id_),
            "carpeta": rel.split("/")[0] if "/" in rel else "",
            "tipo": tipo or None,
            "estado": js_str(campo("estado")).lower() if campo("estado") is not None else None,
            "responsable": campo("responsable"),
            "actualizado": campo("actualizado"),
            "palabras": palabras,
            "resumen": primer_resumen(cuerpo),
            "salientes": len(salientes),
            "entrantes": 0,
            "diagramas": cuerpo.count("```mermaid"),
            "problemas": len(nota_problemas),
            "plantilla": es_plantilla,
        })

    # Los canvas también cuentan como enlace entrante
    por_canvas = set()
    for cv in canvas:
        try:
            data = json.loads(leer_texto(cv))
            nodos = data.get("nodes") if isinstance(data, dict) else data["nodes"]  # lo que no es objeto falla como en JS
            for n in nodos or []:
                if not isinstance(n, dict) or n.get("type") != "file" or not n.get("file"):
                    continue
                f = a_posix(str(n["file"])).lower()
                rel = indice.get(f) or indice.get(f.rsplit("/", 1)[-1]) or next(
                    (r for r in indice.values() if f.endswith("/" + r.lower())), None)
                if rel:
                    por_canvas.add(re.sub(r"\.md$", "", rel, flags=re.I))
                else:
                    rotos.setdefault(str(n["file"]).rsplit("/", 1)[-1], {})[rel_de(cv)] = True
        except Exception:
            problemas.append({"nota": rel_de(cv), "problema": "Canvas con JSON inválido"})

    por_id = {n["id"]: n for n in notas}
    for e in aristas.values():
        if e["b"] in por_id:
            por_id[e["b"]]["entrantes"] += 1

    def es_inicio(n):
        b = os.path.basename(n["id"])
        return bool(re.match(r"^0+\s*-\s*inicio$", b, re.I) or re.match(r"^(home|inicio|readme|index)$", b, re.I))

    huerfanas = [n["id"] for n in notas if not n["plantilla"] and n["entrantes"] == 0
                 and n["id"] not in por_canvas and not es_inicio(n)]
    hs = set(huerfanas)
    for n in notas:
        n["huerfana"] = n["id"] in hs

    # ── Git por proyecto ──
    prefijo = nombre + "/"
    cambios, autores, vistos = [], {}, set()
    actividad = [0] * SEMANAS_ACTIVIDAD
    ahora = dt.datetime.now(dt.timezone.utc)
    ultimo = None
    if commits:
        for c in commits:
            propios = [a for a in c["archivos"] if a.startswith(prefijo)]
            if not propios:
                continue
            ultimo = ultimo or c["fecha"]
            au = autores.setdefault(c["autor"], {"nombre": c["autor"], "commits": 0, "ultimo": c["fecha"]})
            au["commits"] += 1
            try:
                semana = math.floor((ahora - a_fecha(c["fecha"])).total_seconds() / (7 * 86400))
            except ValueError:
                semana = -1
            if 0 <= semana < SEMANAS_ACTIVIDAD:
                actividad[SEMANAS_ACTIVIDAD - 1 - semana] += 1
            for archivo in propios:
                if len(cambios) >= MAX_CAMBIOS_RECIENTES or archivo in vistos:
                    continue
                vistos.add(archivo)
                cambios.append({"archivo": archivo[len(prefijo):], "fecha": c["fecha"], "autor": c["autor"],
                                "mensaje": c["mensaje"], "hash": c["hash"][:7]})
    if not ultimo or commits is None:
        # milisegundos redondeados, como stats.mtime de Node (y el mismo orden en empates)
        por_fecha = sorted(((a, (os.stat(a).st_mtime_ns + 500_000) // 1_000_000) for a in archivos), key=lambda x: -x[1])
        if por_fecha:
            ultimo = iso_ms(por_fecha[0][1])
        if commits is None:
            for a, t in por_fecha[:MAX_CAMBIOS_RECIENTES]:
                cambios.append({"archivo": rel_de(a), "fecha": iso_ms(t), "autor": "local", "mensaje": "", "hash": ""})

    # ── Archivos sin confirmar en git ──
    sin_confirmar = []
    st = git(repo, "status", "--porcelain", "--", nombre)
    if st:
        for l in [x for x in st.split("\n") if x]:
            sin_confirmar.append({"estado": l[:2].strip(),
                                  "archivo": re.sub(r'^"|"$', "", l[3:]).replace(prefijo, "", 1)})

    def contar(campo):
        m = {}
        for n in notas:
            if not n["plantilla"]:
                k = n[campo] or "sin definir"
                m[k] = m.get(k, 0) + 1
        return m

    # ── Salud (0–100) ──
    reales = [n for n in notas if not n["plantilla"]]
    total = len(reales) or 1
    con_problemas = len({p["nota"] for p in problemas})
    salud = max(0, js_round(100 - 40 * (con_problemas / total) - 25 * min(1, len(rotos) / total)
                            - 20 * (len(huerfanas) / total) - 15 * min(1, len(pendientes) / total)))

    rotos_lista = sorted(({"destino": d, "desde": list(desde)} for d, desde in rotos.items()),
                         key=lambda r: -len(r["desde"]))

    return {
        "nombre": nombre,
        "requerimientos": construir_requerimientos(req_notas),
        "notas": len(reales),
        "plantillas": len(notas) - len(reales),
        "canvas": len(canvas),
        "adjuntos": len(archivos) - len(notas_abs) - len(canvas),
        "enlaces": enlaces_totales,
        "palabras": palabras_totales,
        "tamano": tamano,
        "ultimoCambio": ultimo,
        "salud": salud,
        "autores": sorted(autores.values(), key=lambda a: -a["commits"]),
        "cambiosRecientes": cambios,
        "sinConfirmar": sin_confirmar,
        "actividad": actividad,
        "masEnlazadas": [{"nota": n["id"], "titulo": n["titulo"], "entrantes": n["entrantes"]}
                         for n in sorted(reales, key=lambda n: -n["entrantes"]) if n["entrantes"] > 0][:10],
        "rotos": rotos_lista,
        "huerfanas": huerfanas,
        "etiquetas": sorted(({"etiqueta": k, "n": v} for k, v in etiquetas.items()), key=lambda x: -x["n"]),
        "estados": contar("estado"),
        "tipos": contar("tipo"),
        "pendientes": pendientes,
        "problemas": problemas,
        "grafo": {
            "nodos": reales + [{"id": "∅ " + r["destino"], "titulo": r["destino"], "roto": True,
                                "entrantes": len(r["desde"]), "salientes": 0, "palabras": 0} for r in rotos_lista],
            "aristas": [e for e in aristas.values()
                        if e["a"] in por_id and not por_id[e["a"]]["plantilla"]
                        and e["b"] in por_id and not por_id[e["b"]]["plantilla"]]
            + [{"a": d, "b": "∅ " + r["destino"], "rota": True} for r in rotos_lista for d in r["desde"] if d in por_id],
        },
    }


# ───────────────────────── Principal ─────────────────────────
def escanear_repositorio(repo, modo_vault="proyecto"):
    repo = os.path.abspath(repo)
    if not os.path.isdir(repo):
        raise FileNotFoundError(f"No existe la carpeta del repositorio: {repo}")
    commits = leer_historial_git(repo)
    carpetas = sorted(
        (e.name for e in os.scandir(repo)
         if e.is_dir(follow_symlinks=False) and not e.name.startswith(".") and e.name not in CARPETAS_IGNORADAS
         and any(a.lower().endswith(".md") for a in listar_archivos(e.path))),
        key=clave_es)

    indice_repo = set()
    for a in listar_archivos(repo):
        rel = a_posix(os.path.relpath(a, repo)).lower()
        b = rel.rsplit("/", 1)[-1]
        indice_repo.update({rel, b, re.sub(r"\.md$", "", rel), re.sub(r"\.md$", "", b)})

    proyectos = [escanear_proyecto(repo, c, commits, indice_repo if modo_vault == "repo" else None) for c in carpetas]
    commit = None
    if commits:
        c = commits[0]
        commit = {"hash": c["hash"][:7], "autor": c["autor"], "fecha": c["fecha"], "mensaje": c["mensaje"]}
    rama = (git(repo, "rev-parse", "--abbrev-ref", "HEAD") or "").strip() or None
    remoto = (git(repo, "remote", "get-url", "origin") or "").strip()
    remoto = re.sub(r"//[^@/]+@", "//", remoto) or None  # sin credenciales
    return {
        "generado": iso_ms(time.time_ns() // 1_000_000),
        "repositorio": os.path.basename(repo),
        "rama": rama,
        "remoto": remoto,
        "git": commits is not None,
        "commit": commit,
        "modoVault": modo_vault,
        "proyectos": proyectos,
    }


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Escanea el repositorio de documentación y genera el JSON del dashboard.")
    ap.add_argument("--repo", required=True, help="Carpeta del repositorio de documentación")
    ap.add_argument("--modo", default="proyecto", choices=["proyecto", "repo"])
    ap.add_argument("--salida", required=True, help="Archivo JSON de salida")
    a = ap.parse_args()
    datos = escanear_repositorio(a.repo, a.modo)
    Path(a.salida).write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✔ {len(datos['proyectos'])} proyectos escaneados → {a.salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
