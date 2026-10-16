import { haceCuanto, fecha, numero, nombreNota, carpetaNota, ETIQUETAS_ESTADO } from "../utils.js";

export function Panel({ titulo, total, children, vacio, ancho }) {
  const sinDatos = !children || (Array.isArray(children) && children.length === 0);
  return (
    <section className={`panel lista ${ancho ? "ancho-" + ancho : ""}`}>
      <h2>
        {titulo}
        {total != null && <span className="contador">{numero(total)}</span>}
      </h2>
      {sinDatos ? <p className="vacio">{vacio || "Nada por aquí."}</p> : <ul>{children}</ul>}
    </section>
  );
}

function Fila({ izquierda, derecha, sub, onClick, titulo }) {
  const Comp = onClick ? "button" : "div";
  return (
    <li>
      <Comp className="fila" onClick={onClick} title={titulo}>
        <span className="fila-izq">
          <span className="fila-texto">{izquierda}</span>
          {sub && <span className="fila-sub">{sub}</span>}
        </span>
        {derecha != null && <span className="fila-der">{derecha}</span>}
      </Comp>
    </li>
  );
}

const MAX = 8;
const recortar = (arr) => arr.slice(0, MAX);
const resto = (arr) => (arr.length > MAX ? <li className="mas">y {arr.length - MAX} más…</li> : null);

export function CambiosRecientes({ p, onNota }) {
  return (
    <Panel titulo="Cambios recientes" vacio="Sin historial de git todavía.">
      {recortar(p.cambiosRecientes).map((c) => (
        <Fila
          key={c.archivo}
          izquierda={nombreNota(c.archivo)}
          sub={[carpetaNota(c.archivo), c.mensaje].filter(Boolean).join(" · ")}
          derecha={`${haceCuanto(c.fecha)} · ${c.autor}`}
          titulo={`${fecha(c.fecha)} · commit ${c.hash}\n${c.mensaje}`}
          onClick={c.archivo.endsWith(".md") ? () => onNota(c.archivo.replace(/\.md$/, "")) : undefined}
        />
      ))}
    </Panel>
  );
}

export function Autores({ p }) {
  return (
    <Panel titulo="Autores" vacio="Sin historial de git todavía.">
      {p.autores.map((a) => (
        <Fila key={a.nombre} izquierda={a.nombre} derecha={`${a.commits} ${a.commits === 1 ? "commit" : "commits"} · ${haceCuanto(a.ultimo)}`} titulo={`Último commit: ${fecha(a.ultimo)}`} />
      ))}
    </Panel>
  );
}

export function MasEnlazadas({ p, onNota }) {
  return (
    <Panel titulo="Notas más enlazadas" vacio="Ninguna nota recibe enlaces todavía.">
      {recortar(p.masEnlazadas).map((n) => (
        <Fila key={n.nota} izquierda={nombreNota(n.nota)} sub={carpetaNota(n.nota)} derecha={`${n.entrantes} ${n.entrantes === 1 ? "entrante" : "entrantes"}`} onClick={() => onNota(n.nota)} />
      ))}
    </Panel>
  );
}

export function EnlacesRotos({ p, onNota }) {
  return (
    <Panel titulo="Enlaces a notas inexistentes" total={p.rotos.length} vacio="✅ Ningún enlace roto.">
      {recortar(p.rotos).map((r) => (
        <Fila
          key={r.destino}
          izquierda={r.destino}
          derecha={`desde ${r.desde.length === 1 ? nombreNota(r.desde[0]) : r.desde.length + " notas"}`}
          titulo={"Enlazada desde:\n" + r.desde.join("\n")}
          onClick={r.desde[0] && !r.desde[0].endsWith(".canvas") ? () => onNota(r.desde[0]) : undefined}
        />
      ))}
      {resto(p.rotos)}
    </Panel>
  );
}

export function Huerfanas({ p, onNota }) {
  return (
    <Panel titulo="Notas huérfanas" total={p.huerfanas.length} vacio="✅ Todas las notas están enlazadas.">
      {recortar(p.huerfanas).map((h) => (
        <Fila key={h} izquierda={nombreNota(h)} sub={carpetaNota(h)} onClick={() => onNota(h)} titulo="Ninguna nota ni canvas enlaza aquí" />
      ))}
      {resto(p.huerfanas)}
    </Panel>
  );
}

export function Etiquetas({ p }) {
  return (
    <Panel titulo="Etiquetas" total={p.etiquetas.length} vacio="Sin etiquetas.">
      {recortar(p.etiquetas).map((t) => (
        <Fila key={t.etiqueta} izquierda={`#${t.etiqueta}`} derecha={t.n} />
      ))}
      {resto(p.etiquetas)}
    </Panel>
  );
}

export function Pendientes({ p, onNota }) {
  return (
    <Panel titulo="Pendientes por confirmar" total={p.pendientes.length} vacio="✅ Nada pendiente de confirmar." ancho={2}>
      {recortar(p.pendientes).map((q, i) => (
        <Fila key={i} izquierda={q.texto} sub={nombreNota(q.nota)} onClick={() => onNota(q.nota)} />
      ))}
      {resto(p.pendientes)}
    </Panel>
  );
}

export function Problemas({ p, onNota }) {
  return (
    <Panel titulo="Problemas de calidad" total={p.problemas.length} vacio="✅ Sin problemas de calidad." ancho={2}>
      {recortar(p.problemas).map((q, i) => (
        <Fila key={i} izquierda={q.problema} sub={nombreNota(q.nota)} onClick={!q.nota.endsWith(".canvas") ? () => onNota(q.nota) : undefined} />
      ))}
      {resto(p.problemas)}
    </Panel>
  );
}

const COLORES_ESTADO = {
  vigente: "var(--verde)", aceptada: "var(--verde)", borrador: "var(--amarillo)", propuesta: "var(--amarillo)",
  obsoleto: "var(--gris)", reemplazada: "var(--gris)", descartada: "var(--gris)", "sin definir": "var(--borde-fuerte)",
};

export function EstadoDocumentacion({ p }) {
  const total = Object.values(p.estados).reduce((a, b) => a + b, 0) || 1;
  const entradas = Object.entries(p.estados).sort((a, b) => b[1] - a[1]);
  const tipos = Object.entries(p.tipos).sort((a, b) => b[1] - a[1]);
  return (
    <section className="panel lista">
      <h2>Estado de la documentación</h2>
      <div className="barra-apilada" role="img" aria-label={entradas.map(([k, v]) => `${k}: ${v}`).join(", ")}>
        {entradas.map(([k, v]) => (
          <span key={k} style={{ width: `${(v / total) * 100}%`, background: COLORES_ESTADO[k] || "var(--gris)" }} title={`${ETIQUETAS_ESTADO[k] || k}: ${v}`} />
        ))}
      </div>
      <ul className="leyenda-estados">
        {entradas.map(([k, v]) => (
          <li key={k}><i style={{ background: COLORES_ESTADO[k] || "var(--gris)" }} />{ETIQUETAS_ESTADO[k] || k}<b>{v}</b></li>
        ))}
      </ul>
      <h3 className="subtitulo">Notas por tipo</h3>
      <div className="chips">
        {tipos.map(([k, v]) => <span key={k} className="chip">{k} <b>{v}</b></span>)}
      </div>
    </section>
  );
}

export function SinConfirmar({ p }) {
  if (!p.sinConfirmar.length) return null;
  const nombres = { "??": "nuevo", M: "modificado", D: "borrado", A: "agregado", R: "renombrado" };
  return (
    <Panel titulo="Cambios sin commit" total={p.sinConfirmar.length}>
      {recortar(p.sinConfirmar).map((c) => (
        <Fila key={c.archivo} izquierda={c.archivo} derecha={nombres[c.estado] || c.estado} titulo="Este archivo cambió en disco pero no se ha hecho commit/push" />
      ))}
      {resto(p.sinConfirmar)}
    </Panel>
  );
}
