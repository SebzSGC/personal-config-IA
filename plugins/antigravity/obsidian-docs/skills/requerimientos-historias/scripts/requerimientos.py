#!/usr/bin/env python3
"""
requerimientos.py · Gestión de requerimientos e historias de usuario dentro de un vault de Obsidian.

La fuente de verdad es el frontmatter de cada nota (tipo: historia | requerimiento | epica).
Este script NUNCA reescribe el contenido de una nota: solo cambia campos puntuales del frontmatter,
agrega líneas a la bitácora y regenera el bloque automático del "Tablero de avance".

Comandos:
  listar        <proyecto> [--json] [--estado E]      Lista historias/requerimientos con alertas de consistencia
  siguiente-id  <proyecto> <HU|RF|RNF|EP>            Próximo identificador libre (ej. HU-007)
  mover         <proyecto> <ID> <estado> [--nota T] [--fecha AAAA-MM-DD] [--bloqueo T]
                                                       Cambia el estado de una historia y lo registra en su bitácora
  sincronizar   <proyecto> [--hoy AAAA-MM-DD]         Recalcula el % de avance y regenera el Tablero de avance

<proyecto> es la carpeta del proyecto (la raíz del vault).
Estados: backlog (sin iniciar) · por-hacer · en-progreso · en-revision · hecho · bloqueado · descartado
Solo librería estándar de Python 3.8+.
"""
import argparse
import datetime as dt
import json
import re
import sys
import unicodedata
from pathlib import Path

ESTADOS = {
    "backlog": "Sin iniciar",
    "por-hacer": "Por hacer",
    "en-progreso": "En progreso",
    "en-revision": "En revisión",
    "hecho": "Hecho",
    "bloqueado": "Bloqueado",
    "descartado": "Descartado",
}
ICONO_ESTADO = {"backlog": "⚪", "por-hacer": "🔵", "en-progreso": "🟡", "en-revision": "🟣",
                "hecho": "🟢", "bloqueado": "🔴", "descartado": "⚫"}
SINONIMOS = {
    "sin-iniciar": "backlog", "no-iniciada": "backlog", "no-iniciado": "backlog", "pendiente": "backlog",
    "todo": "por-hacer", "to-do": "por-hacer", "por-iniciar": "por-hacer", "lista": "por-hacer",
    "en-curso": "en-progreso", "progreso": "en-progreso", "in-progress": "en-progreso", "doing": "en-progreso",
    "revision": "en-revision", "en-pruebas": "en-revision", "qa": "en-revision", "review": "en-revision",
    "terminada": "hecho", "terminado": "hecho", "finalizada": "hecho", "finalizado": "hecho", "done": "hecho",
    "completada": "hecho", "completado": "hecho", "bloqueada": "bloqueado", "blocked": "bloqueado",
    "descartada": "descartado", "cancelada": "descartado", "cancelado": "descartado",
}
AVANCE_POR_ESTADO = {"backlog": 0, "por-hacer": 0, "en-progreso": 30, "en-revision": 80, "hecho": 100,
                     "bloqueado": None, "descartado": 0}
PRIORIDADES = {"critica": "🔺 Crítica", "alta": "⬆️ Alta", "media": "➖ Media", "baja": "⬇️ Baja"}
TIPOS_TRABAJO = {"historia", "requerimiento"}
PREFIJOS = {"HU": "historia", "RF": "requerimiento", "RNF": "requerimiento", "EP": "epica"}
INICIO_AUTO = "<!-- inicio:tablero-automatico (no editar a mano: lo regenera requerimientos.py) -->"
FIN_AUTO = "<!-- fin:tablero-automatico -->"
RE_CHECK = re.compile(r"^\s*[-*]\s+\[( |x|X)\]\s+(.*)$")


# ───────────────────────── Frontmatter ─────────────────────────
def separar(texto):
    t = texto.lstrip("﻿")
    if not t.startswith("---"):
        return None, t
    fin = t.find("\n---", 3)
    if fin == -1:
        return None, t
    return t[3:fin].strip("\n"), t[fin + 4:].lstrip("\r\n")


def limpiar(v):
    return v.strip().strip("\"'")


def leer_fm(texto):
    bloque, cuerpo = separar(texto)
    fm = {}
    if bloque is None:
        return fm, cuerpo
    clave_lista = None
    for linea in bloque.splitlines():
        item = re.match(r"^\s+-\s+(.*)$", linea)
        if item and clave_lista:
            fm[clave_lista].append(limpiar(item.group(1)))
            continue
        m = re.match(r"^([\w\-áéíóúñ]+)\s*:\s*(.*)$", linea)
        if not m:
            continue
        k, v = m.group(1), m.group(2).strip()
        if v == "":
            fm[k] = []
            clave_lista = k
            continue
        clave_lista = None
        if v.startswith("[") and v.endswith("]"):
            fm[k] = [limpiar(x) for x in v[1:-1].split(",") if limpiar(x)]
        else:
            fm[k] = limpiar(re.sub(r"\s+#.*$", "", v)) if not v.startswith(('"', "'")) else limpiar(v)
    return fm, cuerpo


def formatear(valor):
    if isinstance(valor, list):
        return "[" + ", ".join(str(x) for x in valor) + "]"
    s = str(valor)
    if s == "" or re.search(r"[:#\[\]{}]|^\s|\s$", s) or s.startswith(("@", "`", "!", "&", "*", "|", ">")):
        return '"' + s.replace('"', '\\"') + '"'
    return s


def poner_fm(texto, cambios):
    """Cambia o agrega claves del frontmatter sin tocar el resto del archivo."""
    t = texto.lstrip("﻿")
    if not t.startswith("---"):
        cab = "---\n" + "".join(f"{k}: {formatear(v)}\n" for k, v in cambios.items()) + "---\n"
        return cab + t
    fin = t.find("\n---", 3)
    lineas = t[3:fin].strip("\n").splitlines()
    for k, v in cambios.items():
        nueva = f"{k}: {formatear(v)}"
        for i, l in enumerate(lineas):
            if re.match(rf"^{re.escape(k)}\s*:", l):
                # eliminar ítems de lista en líneas siguientes (formato con guiones)
                j = i + 1
                while j < len(lineas) and re.match(r"^\s+-\s+", lineas[j]):
                    j += 1
                lineas[i:j] = [nueva]
                break
        else:
            lineas.append(nueva)
    return "---\n" + "\n".join(lineas) + "\n" + t[fin + 1:]


# ───────────────────────── Lectura ─────────────────────────
def slug(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def normalizar_estado(v):
    s = slug(v or "backlog")
    return s if s in ESTADOS else SINONIMOS.get(s, s)


def fecha(v):
    if not v:
        return None
    try:
        return dt.date.fromisoformat(str(v)[:10])
    except ValueError:
        return None


def secciones(cuerpo):
    """Devuelve {encabezado_normalizado: [líneas]} para encabezados ##."""
    out, actual = {}, "_"
    for l in cuerpo.splitlines():
        m = re.match(r"^#{2,3}\s+(.*)$", l)
        if m:
            actual = slug(re.sub(r"^[^\w]+", "", m.group(1)))
            out.setdefault(actual, [])
        else:
            out.setdefault(actual, []).append(l)
    return out


def checks(lineas):
    res = []
    dentro = False
    for l in lineas:
        if re.match(r"^\s*(```|~~~)", l):
            dentro = not dentro
            continue
        m = RE_CHECK.match(l) if not dentro else None
        if m:
            res.append({"texto": m.group(2).strip(), "hecho": m.group(1).lower() == "x"})
    return res


def buscar(secs, *claves):
    for k, v in secs.items():
        if any(k.startswith(c) for c in claves):
            return v
    return []


def leer_items(proyecto):
    items, epicas = [], []
    for p in sorted(proyecto.rglob("*.md")):
        if any(part.startswith(".") for part in p.relative_to(proyecto).parts):
            continue
        if re.search(r"(^|/)plantillas?/", p.relative_to(proyecto).as_posix(), re.I):
            continue
        texto = p.read_text(encoding="utf-8", errors="replace")
        fm, cuerpo = leer_fm(texto)
        tipo = str(fm.get("tipo", "")).lower()
        if tipo not in TIPOS_TRABAJO and tipo != "epica":
            continue
        secs = secciones(cuerpo)
        criterios = checks(buscar(secs, "criterios"))
        tareas = checks(buscar(secs, "tareas"))
        historia = " ".join(l.strip("> ").strip() for l in buscar(secs, "historia", "requerimiento", "descripcion") if l.strip() and not l.strip().startswith("[!")).strip()
        bitacora = [l.strip()[2:].strip() for l in buscar(secs, "bitacora") if l.strip().startswith(("- ", "* "))]
        dep = fm.get("depende_de") or []
        item = {
            "id": str(fm.get("id") or p.stem.split(" ")[0]).upper(),
            "titulo": fm.get("titulo") or p.stem,
            "tipo": tipo,
            "ruta": p.relative_to(proyecto).as_posix(),
            "nota": p.stem,
            "epica": str(fm.get("epica") or "").upper() or None,
            "estado": normalizar_estado(fm.get("estado_historia")) if tipo != "epica" else None,
            "estado_crudo": fm.get("estado_historia"),
            "prioridad": slug(fm.get("prioridad") or "") or None,
            "puntos": float(fm["puntos"]) if str(fm.get("puntos", "")).replace(".", "", 1).isdigit() else None,
            "responsable": fm.get("responsable") or None,
            "sprint": fm.get("sprint") or None,
            "inicio": fm.get("inicio") or None,
            "fin": fm.get("fin") or None,
            "fin_real": fm.get("fin_real") or None,
            "bloqueo": fm.get("bloqueo") or None,
            "depende_de": [str(d).upper() for d in (dep if isinstance(dep, list) else [dep]) if d],
            "progreso_fm": int(float(fm["progreso"])) if str(fm.get("progreso", "")).replace(".", "", 1).isdigit() else None,
            "criterios": criterios,
            "tareas": tareas,
            "historia": historia[:400],
            "objetivo": historia[:400] if tipo == "epica" else None,
            "bitacora": bitacora[-8:],
        }
        item["progreso"] = calcular_progreso(item)
        (epicas if tipo == "epica" else items).append(item)
    return items, epicas


def calcular_progreso(it):
    if it["tipo"] == "epica":
        return None
    if it["estado"] == "hecho":
        return 100
    if it["estado"] == "descartado":
        return 0
    marcas = it["criterios"] + it["tareas"]
    if marcas:
        return round(100 * sum(m["hecho"] for m in marcas) / len(marcas))
    base = AVANCE_POR_ESTADO.get(it["estado"])
    return base if base is not None else (it["progreso_fm"] or 0)


def progreso_epica(ep, items):
    hijos = [i for i in items if i["epica"] == ep["id"] and i["estado"] != "descartado"]
    if not hijos:
        return 0, hijos
    pesos = [(i["puntos"] or 1) for i in hijos]
    return round(sum(i["progreso"] * w for i, w in zip(hijos, pesos)) / sum(pesos)), hijos


def alertas(items, epicas, hoy):
    out = []
    ids = {}
    for i in items + epicas:
        ids.setdefault(i["id"], []).append(i["ruta"])
    for k, rutas in ids.items():
        if len(rutas) > 1:
            out.append(("error", k, f"ID duplicado en: {', '.join(rutas)}"))
    ep_ids = {e["id"] for e in epicas}
    for i in items:
        ini, fin = fecha(i["inicio"]), fecha(i["fin"])
        if i["estado"] not in ESTADOS:
            out.append(("error", i["id"], f"estado_historia «{i['estado_crudo']}» no válido ({', '.join(ESTADOS)})"))
        if i["epica"] and i["epica"] not in ep_ids:
            out.append(("aviso", i["id"], f"la épica {i['epica']} no existe"))
        if ini and fin and fin < ini:
            out.append(("error", i["id"], "la fecha fin es anterior a la de inicio"))
        if i["estado"] in ("en-progreso", "en-revision") and not ini:
            out.append(("aviso", i["id"], "está en curso pero no tiene fecha de inicio"))
        if i["estado"] not in ("hecho", "descartado") and fin and fin < hoy:
            out.append(("aviso", i["id"], f"vencida: la fecha fin era {fin.isoformat()}"))
        if i["estado"] == "hecho" and any(not c["hecho"] for c in i["criterios"]):
            out.append(("aviso", i["id"], "marcada como hecha con criterios de aceptación sin cumplir"))
        if i["estado"] == "bloqueado" and not i["bloqueo"]:
            out.append(("aviso", i["id"], "bloqueada sin motivo (campo bloqueo)"))
        if i["tipo"] == "historia" and not i["criterios"]:
            out.append(("aviso", i["id"], "no tiene criterios de aceptación"))
        for d in i["depende_de"]:
            if d not in ids:
                out.append(("aviso", i["id"], f"depende de {d}, que no existe"))
            else:
                dep = next((x for x in items if x["id"] == d), None)
                if dep and i["estado"] in ("en-progreso", "en-revision", "hecho") and dep["estado"] not in ("hecho", "descartado"):
                    out.append(("aviso", i["id"], f"avanza antes que su dependencia {d} ({ESTADOS.get(dep['estado'], dep['estado'])})"))
        if i["puntos"] is None and i["estado"] not in ("backlog", "descartado"):
            out.append(("info", i["id"], "sin estimación (puntos)"))
    return out


def carpeta_requerimientos(proyecto):
    for d in proyecto.iterdir():
        if d.is_dir() and re.search(r"requerimientos", d.name, re.I):
            return d
    return proyecto / "15 - Requerimientos"


def encontrar(proyecto, ident):
    ident = ident.upper()
    for p in proyecto.rglob("*.md"):
        if any(part.startswith(".") for part in p.relative_to(proyecto).parts):
            continue
        fm, _ = leer_fm(p.read_text(encoding="utf-8", errors="replace"))
        if str(fm.get("id", "")).upper() == ident or (not fm.get("id") and p.stem.upper().startswith(ident + " ")):
            return p
    return None


# ───────────────────────── Tablero ─────────────────────────
def barra(p, n=10):
    llenos = round((p or 0) / 100 * n)
    return "█" * llenos + "░" * (n - llenos) + f" {p or 0} %"


def seguro_mermaid(s):
    return re.sub(r"[:#;,]", " ", str(s)).strip()[:60]


def construir_tablero(items, epicas, hoy, als):
    activos = [i for i in items if i["estado"] != "descartado"]
    total_pts = sum(i["puntos"] or 0 for i in activos)
    hechos_pts = sum(i["puntos"] or 0 for i in activos if i["estado"] == "hecho")
    avance = round(sum(i["progreso"] * (i["puntos"] or 1) for i in activos) / max(1, sum(i["puntos"] or 1 for i in activos))) if activos else 0
    cuenta = {e: sum(1 for i in items if i["estado"] == e) for e in ESTADOS}
    vencidas = [i for i in activos if i["estado"] != "hecho" and fecha(i["fin"]) and fecha(i["fin"]) < hoy]
    enlace = lambda i: f"[[{i['nota']}|{i['id']}]]"
    enlace_tabla = lambda i: f"[[{i['nota']}\\|{i['id']}]]"   # dentro de tablas el | va escapado
    pl = lambda n, s, p: f"{n} {s if n == 1 else p}"

    L = [INICIO_AUTO, "", f"> [!abstract] Avance general al {hoy.isoformat()}",
         f"> **{barra(avance, 20)}** · {pl(len(activos), 'ítem', 'ítems')} · "
         f"{pl(cuenta['hecho'], 'hecho', 'hechos')} · {cuenta['en-progreso'] + cuenta['en-revision']} en curso · "
         f"{cuenta['por-hacer']} por hacer · {cuenta['backlog']} sin iniciar"
         + (f" · **{pl(cuenta['bloqueado'], 'bloqueado', 'bloqueados')}**" if cuenta["bloqueado"] else "")
         + (f" · ⏰ **{pl(len(vencidas), 'vencido', 'vencidos')}**" if vencidas else ""),
         f"> Puntos: {hechos_pts:g} de {total_pts:g} completados." if total_pts else "> Sin estimaciones en puntos todavía.",
         ""]

    if epicas:
        L += ["## 🧩 Épicas", "", "| Épica | Avance | Ítems | Fechas |", "|---|---|---|---|"]
        for e in epicas:
            pe, hijos = progreso_epica(e, items)
            fechas = [fecha(h["inicio"]) for h in hijos if fecha(h["inicio"])] + [fecha(h["fin"]) for h in hijos if fecha(h["fin"])]
            rango = f"{min(fechas).isoformat()} → {max(fechas).isoformat()}" if fechas else "—"
            L.append(f"| [[{e['nota']}\\|{e['id']}]] {e['titulo']} | `{barra(pe)}` | {len(hijos)} | {rango} |")
        L.append("")

    L += ["## 📋 Tablero", ""]
    orden = ["bloqueado", "en-progreso", "en-revision", "por-hacer", "backlog", "hecho"]
    for est in orden:
        grupo = sorted([i for i in items if i["estado"] == est],
                       key=lambda i: (["critica", "alta", "media", "baja"].index(i["prioridad"]) if i["prioridad"] in PRIORIDADES else 9, i["id"]))
        L.append(f"### {ICONO_ESTADO[est]} {ESTADOS[est]} ({len(grupo)})")
        if not grupo:
            L += ["_Ninguno._", ""]
            continue
        L += ["| ID | Título | Prioridad | Responsable | Avance | Fin |", "|---|---|---|---|---|---|"]
        for i in grupo:
            fin = i["fin"] or "—"
            if i in vencidas:
                fin = f"⏰ {fin}"
            extra = f" — 🚧 {i['bloqueo']}" if est == "bloqueado" and i["bloqueo"] else ""
            L.append(f"| {enlace_tabla(i)} | {i['titulo']}{extra} | {PRIORIDADES.get(i['prioridad'], '—')} | {i['responsable'] or '—'} | `{barra(i['progreso'])}` | {fin} |")
        L.append("")
    descartados = [i for i in items if i["estado"] == "descartado"]
    if descartados:
        L += [f"> [!note]- ⚫ Descartados ({len(descartados)})"] + [f"> - {enlace(i)} {i['titulo']}" for i in descartados] + [""]

    con_fechas = [i for i in activos if fecha(i["inicio"]) and fecha(i["fin"])]
    L += ["## 📅 Cronograma", ""]
    if con_fechas:
        L += ["```mermaid", "gantt", "    title Cronograma de requerimientos", "    dateFormat YYYY-MM-DD",
              "    axisFormat %d %b", "    todayMarker stroke-width:2px,stroke:#0e7c86"]
        grupos = {}
        for i in con_fechas:
            grupos.setdefault(i["epica"] or "Sin épica", []).append(i)
        nombres_ep = {e["id"]: e["titulo"] for e in epicas}
        for ep, hijos in grupos.items():
            L.append(f"    section {seguro_mermaid(ep + (' ' + nombres_ep[ep] if ep in nombres_ep else ''))}")
            for i in sorted(hijos, key=lambda x: x["inicio"]):
                etiqueta = {"hecho": "done, ", "en-progreso": "active, ", "en-revision": "active, ", "bloqueado": "crit, "}.get(i["estado"], "")
                if i in vencidas:
                    etiqueta = "crit, "
                L.append(f"    {seguro_mermaid(i['id'] + ' ' + i['titulo'])} :{etiqueta}{slug(i['id'])}, {i['inicio']}, {i['fin']}")
        L += ["```", ""]
    sin_fechas = [i for i in activos if not (fecha(i["inicio"]) and fecha(i["fin"]))]
    if sin_fechas:
        L.append(f"> [!info]- Sin fechas planificadas ({len(sin_fechas)})")
        L += [f"> - {enlace(i)} {i['titulo']} · {ESTADOS.get(i['estado'], i['estado'])}" for i in sin_fechas]
        L.append("")

    imp = [a for a in als if a[0] in ("error", "aviso")]
    if imp:
        L += [f"## ⚠️ Alertas ({len(imp)})", ""]
        L += [f"- {'❌' if n == 'error' else '⚠️'} **{k}**: {m}" for n, k, m in imp]
        L.append("")
    L.append(FIN_AUTO)
    return "\n".join(L)


ENCABEZADO_TABLERO = """---
titulo: Tablero de avance
tipo: indice
estado: vigente
audiencia: [negocio, tecnico]
actualizado: {hoy}
etiquetas: [tipo/tablero, requerimientos]
---

# 📊 Tablero de avance

> [!tip] Cómo leer este tablero
> Se genera solo a partir de cada historia (estado, fechas y criterios de aceptación marcados).
> Para cambiar algo, edita la historia, no este tablero. Puedes escribir notas propias **fuera** del bloque automático.

"""


INDICE = """---
titulo: Requerimientos
tipo: indice
estado: vigente
audiencia: [negocio, tecnico]
actualizado: {hoy}
etiquetas: [tipo/indice, requerimientos]
---

# 📋 Requerimientos

> [!abstract] Qué encontrarás aquí
> Qué se va a construir (historias de usuario y requerimientos), agrupado en épicas, y en qué va cada cosa.
> El avance al día está en **[[Tablero de avance]]**.

## 🗺️ Cómo está organizado

```mermaid
flowchart LR
    N[🗒️ Notas de origen] --> H[📗 Historias y 📘 requerimientos]
    H --> E[🧩 Épicas]
    H --> T[📊 Tablero de avance]
    H -. afectan .-> D[📚 Documentación del proyecto]
```

| Estado | Significa |
|---|---|
| ⚪ Sin iniciar | Identificada, aún no planificada |
| 🔵 Por hacer | Lista y planificada (prioridad y fechas) |
| 🟡 En progreso | Alguien trabaja en ella |
| 🟣 En revisión | Construida; se verifican los criterios de aceptación |
| 🟢 Hecho | Todos los criterios de aceptación cumplidos |
| 🔴 Bloqueado | No puede avanzar (el motivo está en la historia) |
| ⚫ Descartado | Se decidió no hacerla (se conserva el registro) |

{bloque}

⬅️ Volver a [[00 - Inicio]]
"""
INICIO_IDX = "<!-- inicio:indice-automatico (lo regenera requerimientos.py) -->"
FIN_IDX = "<!-- fin:indice-automatico -->"


def bloque_indice(items, epicas, proyecto, carpeta):
    L = [INICIO_IDX, "", "## 🧩 Épicas", ""]
    if epicas:
        L += ["| Épica | Avance | Ítems |", "|---|---|---|"]
        for e in epicas:
            pe, hijos = progreso_epica(e, items)
            L.append(f"| [[{e['nota']}\\|{e['id']}]] {e['titulo']} | `{barra(pe)}` | {len(hijos)} |")
    else:
        L.append("_Aún no hay épicas._")
    sueltos = [i for i in items if not i["epica"]]
    if sueltos:
        L += ["", "**Sin épica:** " + " · ".join(f"[[{i['nota']}|{i['id']}]]" for i in sueltos)]
    origenes = sorted(p for p in carpeta.rglob("*.md") if re.search(r"origen", p.parent.name, re.I))
    L += ["", "## 🗒️ Notas de origen", ""]
    L += [f"- [[{p.stem}]]" for p in origenes] or ["_Aún no hay notas de origen._"]
    L += ["", FIN_IDX]
    return "\n".join(L)


def actualizar_indice(items, epicas, proyecto, carpeta, hoy):
    p = carpeta / "Requerimientos.md"
    bloque = bloque_indice(items, epicas, proyecto, carpeta)
    if not p.exists():
        p.write_text(INDICE.format(hoy=hoy.isoformat(), bloque=bloque), encoding="utf-8", newline="\n")
        return "creado"
    actual = p.read_text(encoding="utf-8")
    if INICIO_IDX in actual and FIN_IDX in actual:
        nuevo = actual[:actual.index(INICIO_IDX)] + bloque + actual[actual.index(FIN_IDX) + len(FIN_IDX):]
        if nuevo != actual:
            p.write_text(nuevo, encoding="utf-8", newline="\n")
            return "actualizado"
    return "sin cambios"  # índice escrito a mano: no se toca


def cmd_sincronizar(a):
    proyecto = Path(a.proyecto).expanduser().resolve()
    hoy = fecha(a.hoy) or dt.date.today()
    items, epicas = leer_items(proyecto)
    if not items and not epicas:
        print("ℹ️  No hay historias, requerimientos ni épicas en este proyecto todavía.")
        return 0
    cambiados = 0
    for i in items:
        if i["progreso_fm"] != i["progreso"]:
            p = proyecto / i["ruta"]
            p.write_text(poner_fm(p.read_text(encoding="utf-8"), {"progreso": i["progreso"]}), encoding="utf-8", newline="\n")
            cambiados += 1
    for e in epicas:
        pe, _ = progreso_epica(e, items)
        p = proyecto / e["ruta"]
        fm, _ = leer_fm(p.read_text(encoding="utf-8"))
        if str(fm.get("progreso", "")) != str(pe):
            p.write_text(poner_fm(p.read_text(encoding="utf-8"), {"progreso": pe}), encoding="utf-8", newline="\n")
            cambiados += 1
    als = alertas(items, epicas, hoy)
    carpeta = carpeta_requerimientos(proyecto)
    carpeta.mkdir(parents=True, exist_ok=True)
    tablero = carpeta / "Tablero de avance.md"
    bloque = construir_tablero(items, epicas, hoy, als)
    if tablero.exists():
        actual = tablero.read_text(encoding="utf-8")
        if INICIO_AUTO in actual and FIN_AUTO in actual:
            nuevo = actual[:actual.index(INICIO_AUTO)] + bloque + actual[actual.index(FIN_AUTO) + len(FIN_AUTO):]
        else:
            nuevo = actual.rstrip() + "\n\n" + bloque + "\n"
        nuevo = poner_fm(nuevo, {"actualizado": hoy.isoformat()})
    else:
        nuevo = ENCABEZADO_TABLERO.format(hoy=hoy.isoformat()) + bloque + "\n\n## 🔗 Relacionado\n- [[Requerimientos]]\n"
    tablero.write_text(nuevo, encoding="utf-8", newline="\n")
    estado_idx = actualizar_indice(items, epicas, proyecto, carpeta, hoy)
    print(f"✅ {len(items)} ítems, {len(epicas)} épicas · {cambiados} notas con avance actualizado · "
          f"tablero: {tablero.relative_to(proyecto)} · índice Requerimientos.md: {estado_idx}")
    inicio = next((x for x in proyecto.glob("*.md") if re.match(r"^0+\s*-\s*inicio$", x.stem, re.I)), None)
    if inicio and "[[Requerimientos" not in inicio.read_text(encoding="utf-8", errors="replace"):
        print("   ℹ️  00 - Inicio aún no enlaza a [[Requerimientos]]: agrega una línea en su sección de secciones.")
    for n, k, m in als:
        if n != "info":
            print(f"   {'❌' if n == 'error' else '⚠️'} {k}: {m}")
    return 1 if any(n == "error" for n, _, _ in als) else 0


def cmd_listar(a):
    proyecto = Path(a.proyecto).expanduser().resolve()
    hoy = fecha(a.hoy) or dt.date.today()
    items, epicas = leer_items(proyecto)
    if a.estado:
        items = [i for i in items if i["estado"] == normalizar_estado(a.estado)]
    als = alertas(items, epicas, hoy)
    if a.json:
        for e in epicas:
            e["progreso"], _ = progreso_epica(e, items)
        print(json.dumps({"items": items, "epicas": epicas,
                          "alertas": [{"nivel": n, "id": k, "mensaje": m} for n, k, m in als]}, ensure_ascii=False, indent=2))
        return 0
    for e in epicas:
        pe, hijos = progreso_epica(e, items)
        print(f"🧩 {e['id']} {e['titulo']}  {barra(pe)}  ({len(hijos)} ítems)")
    for est in ESTADOS:
        grupo = [i for i in items if i["estado"] == est]
        if grupo:
            print(f"\n{ICONO_ESTADO[est]} {ESTADOS[est]} ({len(grupo)})")
            for i in grupo:
                print(f"   {i['id']:<8} {i['titulo'][:50]:<50} {barra(i['progreso'])}  {i['responsable'] or ''}")
    if als:
        print("\nAlertas:")
        for n, k, m in als:
            print(f"   {'❌' if n == 'error' else '⚠️' if n == 'aviso' else 'ℹ️'} {k}: {m}")
    return 0


def cmd_siguiente_id(a):
    proyecto = Path(a.proyecto).expanduser().resolve()
    pref = a.prefijo.upper()
    items, epicas = leer_items(proyecto)
    nums = [int(m.group(1)) for i in items + epicas for m in [re.match(rf"^{pref}-(\d+)$", i["id"])] if m]
    ancho = 2 if pref == "EP" else 3
    print(f"{pref}-{(max(nums) + 1 if nums else 1):0{ancho}d}")
    return 0


def cmd_mover(a):
    proyecto = Path(a.proyecto).expanduser().resolve()
    nuevo = normalizar_estado(a.estado)
    if nuevo not in ESTADOS:
        print(f"❌ Estado «{a.estado}» no válido. Usa: {', '.join(ESTADOS)}")
        return 2
    p = encontrar(proyecto, a.id)
    if not p:
        print(f"❌ No encontré {a.id} en {proyecto}")
        return 2
    hoy = fecha(a.fecha) or dt.date.today()
    texto = p.read_text(encoding="utf-8")
    fm, cuerpo_actual = leer_fm(texto)
    anterior = normalizar_estado(fm.get("estado_historia"))
    if nuevo == "hecho":
        pend = [c for c in checks(buscar(secciones(cuerpo_actual), "criterios")) if not c["hecho"]]
        if pend and not a.forzar:
            n = len(pend)
            print(f"❌ {a.id.upper()} no pasa a Hecho: {'queda 1 criterio' if n == 1 else f'quedan {n} criterios'} de aceptación sin marcar:")
            for c in pend[:5]:
                print(f"   - [ ] {c['texto'][:90]}")
            print("   Márcalos con - [x] si ya se cumplen, muévela a 'en-revision', o usa --forzar si el usuario lo confirma.")
            return 1
    cambios = {"estado_historia": nuevo, "actualizado": hoy.isoformat()}
    if nuevo in ("en-progreso", "en-revision", "hecho") and not fm.get("inicio"):
        cambios["inicio"] = hoy.isoformat()
    if nuevo == "hecho":
        cambios["fin_real"] = hoy.isoformat()
    if nuevo == "bloqueado":
        if not a.bloqueo and not fm.get("bloqueo"):
            print("❌ Para bloquear indica el motivo con --bloqueo \"…\"")
            return 2
        if a.bloqueo:
            cambios["bloqueo"] = a.bloqueo
    elif fm.get("bloqueo"):
        cambios["bloqueo"] = ""
    texto = poner_fm(texto, cambios)
    entrada = f"- {hoy.isoformat()} · {ESTADOS.get(anterior, anterior)} → **{ESTADOS[nuevo]}**" + (f" · {a.nota}" if a.nota else "") + (f" · 🚧 {a.bloqueo}" if a.bloqueo else "") + (" · ⚠️ forzada con criterios pendientes" if nuevo == "hecho" and a.forzar else "")
    texto = agregar_bitacora(texto, entrada)
    p.write_text(texto, encoding="utf-8", newline="\n")
    print(f"✅ {a.id.upper()}: {ESTADOS.get(anterior, anterior)} → {ESTADOS[nuevo]}  ({p.relative_to(proyecto)})")
    if nuevo == "hecho" and a.forzar:
        print("   ⚠️ Movida con --forzar: tiene criterios de aceptación sin marcar (queda registrado en la bitácora).")
    return 0


def agregar_bitacora(texto, entrada):
    lineas = texto.split("\n")
    idx = next((i for i, l in enumerate(lineas) if re.match(r"^##\s+.*bit[aá]cora", l, re.I)), None)
    if idx is None:
        rel = next((i for i, l in enumerate(lineas) if re.match(r"^##\s+.*relacionad", l, re.I)), len(lineas))
        lineas[rel:rel] = ["## 📝 Bitácora", "", entrada, ""]
        return "\n".join(lineas)
    j = idx + 1
    while j < len(lineas) and not lineas[j].startswith("## "):
        j += 1
    k = j
    while k > idx + 1 and not lineas[k - 1].strip():
        k -= 1
    lineas[k:k] = [entrada]
    return "\n".join(lineas)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Requerimientos e historias de usuario en Obsidian.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("listar"); p.add_argument("proyecto"); p.add_argument("--json", action="store_true"); p.add_argument("--estado"); p.add_argument("--hoy")
    p = sub.add_parser("siguiente-id"); p.add_argument("proyecto"); p.add_argument("prefijo", choices=list(PREFIJOS) + [x.lower() for x in PREFIJOS])
    p = sub.add_parser("mover"); p.add_argument("proyecto"); p.add_argument("id"); p.add_argument("estado"); p.add_argument("--nota"); p.add_argument("--fecha"); p.add_argument("--bloqueo"); p.add_argument("--forzar", action="store_true", help="Permite pasar a 'hecho' con criterios sin marcar (solo con confirmación del usuario)")
    p = sub.add_parser("sincronizar"); p.add_argument("proyecto"); p.add_argument("--hoy")
    a = ap.parse_args()
    return {"listar": cmd_listar, "siguiente-id": cmd_siguiente_id, "mover": cmd_mover, "sincronizar": cmd_sincronizar}[a.cmd](a)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        sys.exit(0)
