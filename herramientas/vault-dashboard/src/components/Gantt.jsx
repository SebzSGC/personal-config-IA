import { useMemo, useRef, useState, useEffect } from "react";
import {
  aFecha, hoyLocal, diasEntre, sumarDias, estadoReq, esVencida, ICONO_TIPO, PRIORIDADES, fechaCorta,
} from "../utils.js";

const ZOOM = { ajustar: { px: null, nombre: "Ajustar" }, dias: { px: 34, nombre: "Días" }, semanas: { px: 14, nombre: "Semanas" }, meses: { px: 5, nombre: "Meses" } };
const ALTO_FILA = 36;
const ALTO_CAB = 50;
const mesFmt = new Intl.DateTimeFormat("es-CO", { month: "long", year: "numeric" });
const mesCortoFmt = new Intl.DateTimeFormat("es-CO", { month: "short" });

export default function Gantt({ items, epicas, seleccion, onSeleccionar }) {
  const [zoom, setZoom] = useState("ajustar");
  const [visible, setVisible] = useState(800);
  const [plegadas, setPlegadas] = useState(() => new Set());
  const [anchoIzq, setAnchoIzq] = useState(320);
  const scroll = useRef(null);

  useEffect(() => {
    const ajustar = () => setAnchoIzq(window.innerWidth < 700 ? 170 : 320);
    ajustar();
    window.addEventListener("resize", ajustar);
    const ro = new ResizeObserver(([e]) => setVisible(e.contentRect.width));
    if (scroll.current) ro.observe(scroll.current);
    return () => { window.removeEventListener("resize", ajustar); ro.disconnect(); };
  }, []);

  // ── Filas: épica → sus ítems (ordenados por inicio) → "Sin épica"
  const filas = useMemo(() => {
    const porInicio = (a, b) => (a.inicio || "9999").localeCompare(b.inicio || "9999") || a.id.localeCompare(b.id, "es", { numeric: true });
    const out = [];
    const grupos = [...epicas.map((e) => ({ epica: e, hijos: items.filter((i) => i.epica === e.id) }))];
    const sueltos = items.filter((i) => !i.epica || !epicas.some((e) => e.id === i.epica));
    if (sueltos.length) grupos.push({ epica: { id: "_sin", titulo: "Sin épica", progreso: null }, hijos: sueltos });
    for (const g of grupos) {
      if (!g.hijos.length) continue;
      const conFechas = g.hijos.filter((h) => h.inicio && h.fin);
      const ini = conFechas.length ? conFechas.map((h) => h.inicio).sort()[0] : null;
      const fin = conFechas.length ? conFechas.map((h) => h.fin).sort().at(-1) : null;
      const activos = g.hijos.filter((h) => h.estado !== "descartado");
      const peso = (h) => h.puntos || 1;
      const prog = activos.length ? Math.round(activos.reduce((a, h) => a + h.progreso * peso(h), 0) / activos.reduce((a, h) => a + peso(h), 0)) : 0;
      out.push({ ...g.epica, fila: "epica", inicio: ini, fin, progreso: prog, n: g.hijos.length });
      if (!plegadas.has(g.epica.id)) for (const h of [...g.hijos].sort(porInicio)) out.push({ ...h, fila: "item" });
    }
    return out;
  }, [items, epicas, plegadas]);

  // ── Escala de tiempo
  const { inicio, dias } = useMemo(() => {
    const fechas = items.flatMap((i) => [i.inicio, i.fin]).filter(Boolean).map(aFecha);
    const hoy = hoyLocal();
    const min = new Date(Math.min(hoy, ...fechas));
    const max = new Date(Math.max(hoy, ...fechas));
    let ini = sumarDias(min, -7);
    ini = sumarDias(ini, -((ini.getDay() + 6) % 7)); // alinear al lunes
    const total = Math.max(42, diasEntre(ini, max) + 21);
    return { inicio: ini, dias: total };
  }, [items]);
  const px = ZOOM[zoom].px ?? Math.min(40, Math.max(4, (visible - anchoIzq - 60) / dias));
  const ancho = dias * px;
  const x = (iso) => diasEntre(inicio, aFecha(iso)) * px;
  const xHoy = diasEntre(inicio, hoyLocal()) * px;

  // Al cambiar a una escala fija, llevar la línea de hoy a la vista (en "Ajustar" todo cabe)
  useEffect(() => {
    if (!scroll.current) return;
    scroll.current.scrollLeft = zoom === "ajustar" ? 0 : Math.max(0, xHoy - (visible - anchoIzq) * 0.35);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [zoom]);

  const meses = useMemo(() => {
    const out = [];
    let d = new Date(inicio);
    while (diasEntre(inicio, d) < dias) {
      const sig = new Date(d.getFullYear(), d.getMonth() + 1, 1);
      const a = Math.max(0, diasEntre(inicio, d));
      const b = Math.min(dias, diasEntre(inicio, sig));
      const nombre = ((b - a) * px > 120 ? mesFmt.format(d) : mesCortoFmt.format(d)).replace(/^./, (c) => c.toUpperCase());
      out.push({ clave: d.toISOString(), x: a * px, w: (b - a) * px, nombre });
      d = sig;
    }
    return out;
  }, [inicio, dias, px]);
  const marcas = useMemo(() => {
    const out = [];
    const paso = px >= 24 ? 1 : 7;
    for (let i = 0; i < dias; i += paso) {
      const d = sumarDias(inicio, i);
      out.push({ x: i * px, etiqueta: px * paso >= 18 ? d.getDate() : "", finde: paso === 1 && (d.getDay() === 0 || d.getDay() === 6) });
    }
    return out;
  }, [inicio, dias, px]);

  // ── Dependencias (flechas)
  const posFila = new Map(filas.map((f, idx) => [f.fila === "item" ? f.id : "ep:" + f.id, idx]));
  const flechas = filas.filter((f) => f.fila === "item" && f.inicio && f.fin).flatMap((f) =>
    f.dependeDe.map((d) => {
      const dep = filas.find((g) => g.fila === "item" && g.id === d);
      if (!dep || !dep.inicio || !dep.fin) return null;
      const x1 = x(dep.fin) + px, y1 = posFila.get(dep.id) * ALTO_FILA + ALTO_FILA / 2;
      const x2 = x(f.inicio), y2 = posFila.get(f.id) * ALTO_FILA + ALTO_FILA / 2;
      const codo = Math.max(x1 + 10, Math.min(x2 - 10, x1 + 10));
      const camino = x2 - 14 > x1
        ? `M${x1},${y1} H${codo} V${y2} H${x2 - 2}`
        : `M${x1},${y1} h10 V${(y1 + y2) / 2} H${x2 - 12} V${y2} H${x2 - 2}`;
      return { clave: `${d}-${f.id}`, camino, activa: seleccion === f.id || seleccion === d };
    }).filter(Boolean));

  const alternar = (id) => setPlegadas((s) => { const n = new Set(s); n.has(id) ? n.delete(id) : n.add(id); return n; });

  if (!items.length) return <p className="vacio">No hay historias que coincidan con los filtros.</p>;

  return (
    <div className="gantt">
      <div className="gantt-barra">
        <div className="segmentado" role="group" aria-label="Escala del cronograma">
          {Object.entries(ZOOM).map(([k, z]) => (
            <button key={k} className={zoom === k ? "activo" : ""} onClick={() => setZoom(k)}>{z.nombre}</button>
          ))}
        </div>
        <button className="boton-texto" onClick={() => { if (scroll.current) scroll.current.scrollLeft = Math.max(0, xHoy - (visible - anchoIzq) * 0.35); }}>Ir a hoy</button>
        <div className="gantt-leyenda">
          {["por-hacer", "en-progreso", "en-revision", "hecho", "bloqueado"].map((e) => (
            <span key={e}><i style={{ background: estadoReq(e).color }} />{estadoReq(e).nombre}</span>
          ))}
          <span><i className="vencida" />Vencida</span>
        </div>
      </div>

      <div className="gantt-scroll" ref={scroll} style={{ "--izq": `${anchoIzq}px` }}>
        <div className="gantt-lienzo" style={{ width: anchoIzq + ancho }}>
          {/* Cabecera */}
          <div className="g-fila g-cab" style={{ height: ALTO_CAB }}>
            <div className="g-izq g-cab-izq">Épica / historia</div>
            <div className="g-der" style={{ width: ancho }}>
              {meses.map((m) => <div key={m.clave} className="g-mes" style={{ left: m.x, width: m.w }}>{m.nombre}</div>)}
              {marcas.map((m) => <div key={m.x} className={`g-dia ${m.finde ? "finde" : ""}`} style={{ left: m.x, width: px >= 24 ? px : 7 * px }}>{m.etiqueta}</div>)}
            </div>
          </div>

          {/* Cuerpo */}
          <div className="g-cuerpo" style={{ height: filas.length * ALTO_FILA }}>
            <div className="g-rejilla" style={{ left: anchoIzq, width: ancho }}>
              {marcas.map((m) => <div key={m.x} className={`g-linea ${m.finde ? "finde" : ""}`} style={{ left: m.x, width: px >= 24 ? px : undefined }} />)}
              <div className="g-hoy" style={{ left: xHoy }}><span>Hoy</span></div>
            </div>

            <svg className="g-flechas" style={{ left: anchoIzq }} width={ancho} height={filas.length * ALTO_FILA} aria-hidden="true">
              <defs>
                <marker id="punta" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto">
                  <path d="M0,0 L8,4 L0,8 z" fill="context-stroke" />
                </marker>
              </defs>
              {flechas.map((f) => <path key={f.clave} d={f.camino} className={f.activa ? "activa" : ""} markerEnd="url(#punta)" />)}
            </svg>

            {filas.map((f) => (f.fila === "epica"
              ? <FilaEpica key={"ep" + f.id} f={f} x={x} px={px} ancho={ancho} plegada={plegadas.has(f.id)} onAlternar={() => alternar(f.id)} />
              : <FilaItem key={f.id} f={f} x={x} px={px} ancho={ancho} sel={seleccion === f.id} onClick={() => onSeleccionar(f.id)} />))}
          </div>
        </div>
      </div>
    </div>
  );
}

function FilaEpica({ f, x, px, ancho, plegada, onAlternar }) {
  const tieneBarra = f.inicio && f.fin;
  return (
    <div className="g-fila g-epica" style={{ height: ALTO_FILA }}>
      <button className="g-izq" onClick={onAlternar} aria-expanded={!plegada} title={plegada ? "Mostrar historias" : "Ocultar historias"}>
        <span className="g-chevron">{plegada ? "▸" : "▾"}</span>
        <span className="g-id">{f.id === "_sin" ? "—" : f.id}</span>
        <span className="g-titulo">{f.titulo}</span>
        <span className="g-cuenta">{f.n}</span>
      </button>
      <div className="g-der" style={{ width: ancho }}>
        {tieneBarra && (
          <div className="g-barra-epica" style={{ left: x(f.inicio), width: x(f.fin) - x(f.inicio) + px }} title={`${f.titulo}: ${f.progreso} %`}>
            <span style={{ width: `${f.progreso}%` }} />
            <em>{f.progreso} %</em>
          </div>
        )}
      </div>
    </div>
  );
}

function FilaItem({ f, x, px, ancho, sel, onClick }) {
  const e = estadoReq(f.estado);
  const vencida = esVencida(f);
  const tieneBarra = f.inicio && f.fin;
  const w = tieneBarra ? x(f.fin) - x(f.inicio) + px : 0;
  const etiquetaDentro = w > 120;
  const titulo = `${f.id} · ${f.titulo}\n${e.nombre} · ${f.progreso} %\n${fechaCorta(f.inicio)} → ${fechaCorta(f.fin)}${f.responsable ? "\n" + f.responsable : ""}${vencida ? "\n⏰ Vencida" : ""}${f.bloqueo ? "\n🚧 " + f.bloqueo : ""}`;
  return (
    <div className={`g-fila g-item ${sel ? "sel" : ""}`} style={{ height: ALTO_FILA }}>
      <button className="g-izq" onClick={onClick} title={titulo}>
        <span className="g-punto" style={{ background: e.color }} />
        <span className="g-id">{f.id}</span>
        <span className="g-titulo">{f.titulo}</span>
        {f.prioridad && <span className="g-prio" title={`Prioridad ${PRIORIDADES[f.prioridad]?.nombre || f.prioridad}`}>{PRIORIDADES[f.prioridad]?.icono}</span>}
      </button>
      <div className="g-der" style={{ width: ancho }}>
        {tieneBarra ? (
          <button
            className={`g-barra estado-${f.estado} ${vencida ? "vencida" : ""} ${sel ? "sel" : ""}`}
            style={{ left: x(f.inicio), width: w, "--c": e.color, "--p": `${f.progreso}%` }}
            onClick={onClick}
            title={titulo}
          >
            {etiquetaDentro && <span className="g-etq">{ICONO_TIPO[f.tipo]} {f.id} · {f.progreso} %</span>}
          </button>
        ) : (
          <span className="g-sinfecha">Sin fechas · {e.nombre}</span>
        )}
        {tieneBarra && !etiquetaDentro && (
          <span className="g-etq-fuera" style={{ left: x(f.inicio) + w + 6 }}>{f.id} · {f.progreso} %{vencida ? " ⏰" : ""}</span>
        )}
        {tieneBarra && etiquetaDentro && vencida && <span className="g-etq-fuera" style={{ left: x(f.inicio) + w + 6 }}>⏰ vencida</span>}
      </div>
    </div>
  );
}
