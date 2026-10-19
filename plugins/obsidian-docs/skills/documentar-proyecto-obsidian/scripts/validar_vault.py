#!/usr/bin/env python3
"""
Validador de documentación en Obsidian.

Uso:
    python3 validar_vault.py "<carpeta del proyecto>" [--vault "<raíz del vault>"] [--json]

Revisa:
  - Frontmatter obligatorio (titulo, tipo, estado, audiencia, actualizado, etiquetas)
  - Callout [!abstract] al inicio
  - Placeholders sin rellenar ({{...}}, TODO, lorem, foo/bar)
  - Enlaces [[wikilinks]] y ![[embeds]] rotos
  - Notas huérfanas (nadie las enlaza)
  - Notas de flujo/arquitectura/datos sin diagrama Mermaid
  - Existencia de "00 - Inicio.md" y validez de los .canvas
  - Posibles secretos (contraseñas, tokens, cadenas de conexión)
  - Carpetas vacías

Código de salida: 0 si no hay errores, 1 si hay errores (las advertencias no fallan).
Solo usa la librería estándar de Python.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

CAMPOS_OBLIGATORIOS = ["titulo", "tipo", "estado", "audiencia", "actualizado", "etiquetas"]
TIPOS_CON_DIAGRAMA = {"flujo", "arquitectura", "datos"}
TIPOS_SIN_ABSTRACT = {"indice"}  # los MOC usan [!abstract] también, pero no se exige

RE_FENCE = re.compile(r"^\s*>?\s*(```|~~~)")
RE_LINK = re.compile(r"(!?)\[\[([^\]\|#\^]*)(?:[#\^][^\]\|]*)?(?:\|[^\]]*)?\]\]")
# TODO solo en mayúsculas: "todo" es una palabra normal en español
RE_PLACEHOLDER = re.compile(r"\{\{[^}]*\}\}|\bTODO\b|\b[Ll]orem ipsum\b|\bfoo/bar\b")
RE_SECRETOS = [
    (re.compile(r"(password|contraseña|passwd|pwd)\s*[:=]\s*['\"]?[^\s'\"<]{4,}", re.I), "posible contraseña"),
    (re.compile(r"(api[_-]?key|secret|token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}", re.I), "posible token/clave"),
    (re.compile(r"\b(sk|pk|ghp|gho|xox[abp])[-_][A-Za-z0-9]{16,}"), "posible clave de API"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "posible clave AWS"),
    (re.compile(r"(Server|Data Source)=[^;]+;.*(Password|Pwd)=[^;<]+", re.I), "cadena de conexión con contraseña"),
    (re.compile(r"(postgres|mysql|mongodb(\+srv)?|redis)://[^:\s]+:[^@\s<]+@", re.I), "URL con credenciales"),
]


def leer_frontmatter(texto):
    if not texto.startswith("---"):
        return None, texto
    fin = texto.find("\n---", 3)
    if fin == -1:
        return None, texto
    bloque = texto[3:fin]
    datos = {}
    for linea in bloque.splitlines():
        m = re.match(r"^([A-Za-z_áéíóúñ]+)\s*:\s*(.*)$", linea)
        if m:
            datos[m.group(1).strip()] = m.group(2).strip().strip('"\'')
    cuerpo = texto[fin + 4:]
    return datos, cuerpo


def lineas_fuera_de_codigo(cuerpo):
    """Devuelve (num_linea, linea) solo de líneas que no están dentro de bloques de código."""
    dentro = False
    for i, linea in enumerate(cuerpo.splitlines(), 1):
        if RE_FENCE.match(linea):
            dentro = not dentro
            continue
        if not dentro:
            yield i, linea


def main():
    ap = argparse.ArgumentParser(description="Valida la documentación de un proyecto en Obsidian.")
    ap.add_argument("carpeta", help="Carpeta del proyecto dentro del vault")
    ap.add_argument("--vault", help="Raíz del vault (para resolver enlaces a notas fuera del proyecto)")
    ap.add_argument("--json", action="store_true", help="Salida en JSON")
    args = ap.parse_args()

    raiz = Path(args.carpeta).expanduser().resolve()
    vault = Path(args.vault).expanduser().resolve() if args.vault else raiz
    if not raiz.is_dir():
        print(f"❌ No existe la carpeta: {raiz}")
        sys.exit(2)

    errores, avisos = [], []

    def err(archivo, msg):
        errores.append({"archivo": str(archivo.relative_to(raiz)) if isinstance(archivo, Path) else archivo, "problema": msg})

    def aviso(archivo, msg):
        avisos.append({"archivo": str(archivo.relative_to(raiz)) if isinstance(archivo, Path) else archivo, "problema": msg})

    # Índice de todos los archivos del vault (Obsidian resuelve por nombre)
    nombres_vault = {}
    for p in vault.rglob("*"):
        if p.is_file() and not any(part.startswith(".") for part in p.relative_to(vault).parts):
            nombres_vault.setdefault(p.stem.lower(), []).append(p)
            nombres_vault.setdefault(p.name.lower(), []).append(p)
            rel = p.relative_to(vault).as_posix().lower()
            nombres_vault.setdefault(rel, []).append(p)
            nombres_vault.setdefault(rel.rsplit(".", 1)[0], []).append(p)

    notas = [p for p in raiz.rglob("*.md") if not any(part.startswith(".") for part in p.relative_to(raiz).parts)]
    canvases = [p for p in raiz.rglob("*.canvas")]
    entrantes = {p.resolve(): 0 for p in notas}

    if not (raiz / "00 - Inicio.md").exists():
        err("(proyecto)", "Falta '00 - Inicio.md' en la raíz del proyecto")

    for nota in notas:
        texto = nota.read_text(encoding="utf-8", errors="replace")
        es_plantilla = "Plantillas" in nota.parts
        fm, cuerpo = leer_frontmatter(texto)

        # Frontmatter
        if fm is None:
            err(nota, "Sin frontmatter YAML")
            fm = {}
        else:
            faltan = [c for c in CAMPOS_OBLIGATORIOS if c not in fm]
            if faltan:
                err(nota, f"Frontmatter incompleto, faltan: {', '.join(faltan)}")

        tipo = fm.get("tipo", "").lower()

        # Abstract
        if tipo not in TIPOS_SIN_ABSTRACT and "[!abstract]" not in cuerpo[:1500]:
            aviso(nota, "No abre con un callout > [!abstract] (resumen para no técnicos)")

        # Diagramas
        if tipo in TIPOS_CON_DIAGRAMA and "```mermaid" not in cuerpo:
            aviso(nota, f"Nota de tipo '{tipo}' sin diagrama Mermaid")

        # Relacionado
        if tipo not in {"inicio", "glosario", "indice"} and "Relacionado" not in cuerpo:
            aviso(nota, "Falta la sección '## 🔗 Relacionado'")

        # Placeholders, enlaces y secretos (fuera de bloques de código)
        for n, linea in lineas_fuera_de_codigo(cuerpo):
            if not es_plantilla and RE_PLACEHOLDER.search(linea):
                err(nota, f"Placeholder sin rellenar en línea ~{n}: {linea.strip()[:80]}")
            for m in RE_LINK.finditer(linea):
                destino = m.group(2).strip().rstrip("\\").strip()  # [[nota\\|alias]] dentro de tablas
                if not destino:
                    continue  # enlace a la misma nota (#encabezado)
                clave = destino.lower()
                candidatos = nombres_vault.get(clave) or nombres_vault.get(clave + ".md")
                if not candidatos:
                    if not es_plantilla:
                        err(nota, f"Enlace roto: [[{destino}]] (línea ~{n})")
                else:
                    for c in candidatos:
                        if c.resolve() in entrantes and c.resolve() != nota.resolve():
                            entrantes[c.resolve()] += 1
        for n, linea in enumerate(texto.splitlines(), 1):
            for rx, desc in RE_SECRETOS:
                if rx.search(linea):
                    err(nota, f"🔐 {desc} en línea {n}. Reemplázala por <SECRETO: ver gestor de claves>")

        if len(texto.splitlines()) > 400:
            aviso(nota, f"Nota muy larga ({len(texto.splitlines())} líneas): considera dividirla")

    # Enlaces desde canvas también cuentan como entrantes
    for cv in canvases:
        try:
            data = json.loads(cv.read_text(encoding="utf-8"))
        except Exception as e:
            err(cv, f"Canvas con JSON inválido: {e}")
            continue
        for nodo in data.get("nodes", []):
            if nodo.get("type") == "file":
                f = nodo.get("file", "")
                destino = (vault / f)
                if not destino.exists():
                    err(cv, f"El canvas apunta a un archivo que no existe: {f}")
                elif destino.resolve() in entrantes:
                    entrantes[destino.resolve()] += 1

    # Huérfanas
    for p, cnt in entrantes.items():
        if cnt == 0 and p.name != "00 - Inicio.md":
            aviso(p, "Nota huérfana: ninguna otra nota ni el canvas la enlazan")

    # Carpetas vacías
    for d in raiz.rglob("*"):
        if d.is_dir() and not d.name.startswith(".") and not any(d.iterdir()):
            aviso(d, "Carpeta vacía")

    if not canvases:
        aviso("(proyecto)", "No hay ningún .canvas (se recomienda 'Mapa del proyecto.canvas')")

    resumen = {
        "carpeta": str(raiz),
        "notas": len(notas),
        "canvas": len(canvases),
        "errores": errores,
        "advertencias": avisos,
    }

    if args.json:
        print(json.dumps(resumen, ensure_ascii=False, indent=2))
    else:
        print(f"📚 {len(notas)} notas · 🗺️ {len(canvases)} canvas · carpeta: {raiz}\n")
        if errores:
            print(f"❌ {len(errores)} errores")
            for e in errores:
                print(f"   • {e['archivo']}: {e['problema']}")
            print()
        if avisos:
            print(f"⚠️  {len(avisos)} advertencias")
            for a in avisos:
                print(f"   • {a['archivo']}: {a['problema']}")
            print()
        if not errores and not avisos:
            print("✅ Todo en orden.")
        elif not errores:
            print("✅ Sin errores (revisa las advertencias).")

    sys.exit(1 if errores else 0)


if __name__ == "__main__":
    main()
