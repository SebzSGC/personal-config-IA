import { useEffect, useMemo, useRef, useState } from "react";
import { forceSimulation, forceLink, forceManyBody, forceCenter, forceCollide, forceX, forceY } from "d3-force";
import { numero } from "../utils.js";

const ALTO = 420;

// Paleta categórica (se ve bien en claro y oscuro). El gris es el color "normal".
const PALETA_TIPO = {
  inicio: "#0f766e", resumen: "#2563eb", glosario: "#7c3aed", arquitectura: "#0891b2",
  componente: "#0e7490", flujo: "#16a34a", datos: "#9333ea", guia: "#ca8a04",
  operacion: "#ea580c", decision: "#db2777", api: "#4f46e5", faq: "#64748b", indice: "#475569",
};
const PALETA_ESTADO = {
  vigente: "#16a34a", aceptada: "#16a34a", borrador: "#ca8a04", propuesta: "#ca8a04",
  obsoleto: "#94a3b8", reemplazada: "#94a3b8", descartada: "#94a3b8",
};
const COLOR_ROTO = "#c2700c";

export default function Grafo({ proyecto, seleccion, onSeleccionar }) {
  const contenedor = useRef(null);
  const svg = useRef(null);
  const [ancho, setAncho] = useState(900);
  const [nodos, setNodos] = useState([]);
  const [aristas, setAristas] = useState([]);
  const [vista, setVista] = useState({ x: 0, y: 0, k: 1 });
  const [hover, setHover] = useState(null);
  const [modoColor, setModoColor] = useState("sencillo");
  const sim = useRef(null);
  const arrastre = useRef(null);

  // Ancho responsivo
  useEffect(() => {
    const ro = new ResizeObserver(([e]) => setAncho(Math.max(300, e.contentRect.width)));
    ro.observe(contenedor.current);
    return () => ro.disconnect();
  }, []);

  // Simulación de fuerzas (se reinicia al cambiar de proyecto)
  useEffect(() => {
    const ns = proyecto.grafo.nodos.map((n) => ({ ...n }));
    const ids = new Set(ns.map((n) => n.id));
    const ls = proyecto.grafo.aristas.filter((a) => ids.has(a.a) && ids.has(a.b)).map((a) => ({ source: a.a, target: a.b, rota: a.rota }));
    const radio = (n) => 5 + Math.sqrt(n.entrantes || 0) * 4;
    ns.forEach((n) => (n.r = radio(n)));

    sim.current?.stop();
    const s = forceSimulation(ns)
      .force("link", forceLink(ls).id((d) => d.id).distance(70).strength(0.6))
      .force("carga", forceManyBody().strength(-340))
      .force("centro", forceCenter(0, 0))
      .force("x", forceX(0).strength(0.06))
      .force("y", forceY(0).strength(0.09))
      .force("choque", forceCollide((d) => d.r + 24));
    // Se precalcula el layout (sin animación) y se encuadra de inmediato
    s.stop();
    s.tick(320);
    let frame = 0;
    s.on("tick", () => {
      if (frame++ % 2 === 0) { setNodos([...ns]); setAristas([...ls]); }
    });
    setNodos([...ns]);
    setAristas([...ls]);
    encuadrar(ns);
    sim.current = s;
    return () => s.stop();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [proyecto]);

  // Reencuadrar si cambia el ancho de la ventana
  useEffect(() => { encuadrar(); // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ancho]);

  function encuadrar(ns = nodos) {
    if (!ns.length) return;
    const xs = ns.map((n) => n.x), ys = ns.map((n) => n.y);
    const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
    const k = Math.min(1.8, (ancho - 120) / Math.max(1, x1 - x0), (ALTO - 90) / Math.max(1, y1 - y0));
    setVista({ k, x: -((x0 + x1) / 2) * k, y: -((y0 + y1) / 2) * k });
  }

  // Vecinos para resaltar al pasar el ratón / seleccionar
  const foco = hover || seleccion;
  const vecinos = useMemo(() => {
    if (!foco) return null;
    const v = new Set([foco]);
    for (const a of aristas) {
      const s = a.source.id ?? a.source, t = a.target.id ?? a.target;
      if (s === foco) v.add(t);
      if (t === foco) v.add(s);
    }
    return v;
  }, [foco, aristas]);

  const colorNodo = (n) => {
    if (n.roto) return COLOR_ROTO;
    if (modoColor === "tipo") return PALETA_TIPO[n.tipo] || "var(--nodo)";
    if (modoColor === "estado") return PALETA_ESTADO[n.estado] || "#cbd5e1";
    return "var(--nodo)";
  };

  // ── Interacción: zoom con rueda, arrastrar fondo (pan) o nodo ──
  const aMundo = (ev) => {
    const r = svg.current.getBoundingClientRect();
    return { x: (ev.clientX - r.left - ancho / 2 - vista.x) / vista.k, y: (ev.clientY - r.top - ALTO / 2 - vista.y) / vista.k };
  };
  const onWheel = (ev) => {
    ev.preventDefault();
    const r = svg.current.getBoundingClientRect();
    const px = ev.clientX - r.left - ancho / 2, py = ev.clientY - r.top - ALTO / 2;
    const k = Math.min(4, Math.max(0.25, vista.k * (ev.deltaY < 0 ? 1.12 : 1 / 1.12)));
    setVista({ k, x: px - ((px - vista.x) / vista.k) * k, y: py - ((py - vista.y) / vista.k) * k });
  };
  useEffect(() => {
    const el = svg.current;
    el.addEventListener("wheel", onWheel, { passive: false });
    return () => el.removeEventListener("wheel", onWheel);
  });
  const onPointerDownNodo = (ev, n) => {
    ev.stopPropagation();
    svg.current.setPointerCapture(ev.pointerId);
    arrastre.current = { tipo: "nodo", n, movido: false };
    sim.current.alphaTarget(0.25).restart();
    n.fx = n.x; n.fy = n.y;
  };
  const onPointerDownFondo = (ev) => {
    svg.current.setPointerCapture(ev.pointerId);
    arrastre.current = { tipo: "pan", x: ev.clientX, y: ev.clientY, vx: vista.x, vy: vista.y, movido: false };
  };
  const onPointerMove = (ev) => {
    const a = arrastre.current;
    if (!a) return;
    a.movido = true;
    if (a.tipo === "nodo") { const p = aMundo(ev); a.n.fx = p.x; a.n.fy = p.y; }
    else setVista((v) => ({ ...v, x: a.vx + ev.clientX - a.x, y: a.vy + ev.clientY - a.y }));
  };
  const onPointerUp = () => {
    const a = arrastre.current;
    arrastre.current = null;
    if (!a) return;
    if (a.tipo === "nodo") {
      sim.current.alphaTarget(0);
      a.n.fx = null; a.n.fy = null;
      if (!a.movido) onSeleccionar(a.n.roto ? null : a.n.id);
    } else if (!a.movido) onSeleccionar(null);
  };

  const mostrarEtiquetas = nodos.length <= 70;
  const leyenda = modoColor === "tipo" ? PALETA_TIPO : modoColor === "estado" ? { vigente: PALETA_ESTADO.vigente, borrador: PALETA_ESTADO.borrador, obsoleto: PALETA_ESTADO.obsoleto } : null;
  const tiposPresentes = new Set(nodos.map((n) => (modoColor === "tipo" ? n.tipo : n.estado)));

  return (
    <section className="panel grafo-panel">
      <div className="panel-cabecera">
        <h2>
          Grafo · {proyecto.nombre} · {numero(proyecto.notas)} notas, {numero(proyecto.palabras)} palabras
        </h2>
        <div className="controles">
          <div className="segmentado" role="group" aria-label="Color de los nodos">
            {[["sencillo", "Sencillo"], ["tipo", "Por tipo"], ["estado", "Por estado"]].map(([k, t]) => (
              <button key={k} className={modoColor === k ? "activo" : ""} onClick={() => setModoColor(k)}>{t}</button>
            ))}
          </div>
          <button className="boton-icono" title="Encuadrar" onClick={() => encuadrar()}>⤢</button>
        </div>
      </div>
      <div className="lienzo" ref={contenedor}>
        <svg
          ref={svg}
          width={ancho}
          height={ALTO}
          onPointerDown={onPointerDownFondo}
          onPointerMove={onPointerMove}
          onPointerUp={onPointerUp}
          role="img"
          aria-label={`Grafo de enlaces del proyecto ${proyecto.nombre}`}
        >
          <g transform={`translate(${ancho / 2 + vista.x},${ALTO / 2 + vista.y}) scale(${vista.k})`}>
            {aristas.map((a, i) => {
              const s = a.source, t = a.target;
              const activa = vecinos && vecinos.has(s.id) && vecinos.has(t.id) && (s.id === foco || t.id === foco);
              return (
                <line
                  key={i}
                  x1={s.x} y1={s.y} x2={t.x} y2={t.y}
                  className={`arista ${a.rota ? "rota" : ""} ${activa ? "activa" : ""} ${vecinos && !activa ? "atenuada" : ""}`}
                  strokeWidth={1 / Math.sqrt(vista.k)}
                />
              );
            })}
            {nodos.map((n) => {
              const atenuado = vecinos && !vecinos.has(n.id);
              const sel = n.id === seleccion;
              return (
                <g
                  key={n.id}
                  transform={`translate(${n.x},${n.y})`}
                  className={`nodo ${atenuado ? "atenuado" : ""} ${sel ? "seleccionado" : ""} ${n.roto ? "roto" : ""}`}
                  onPointerDown={(ev) => onPointerDownNodo(ev, n)}
                  onPointerEnter={() => setHover(n.id)}
                  onPointerLeave={() => setHover(null)}
                >
                  <circle r={n.r} fill={colorNodo(n)} strokeDasharray={n.roto ? "3 2" : undefined} />
                  {n.problemas > 0 && !n.roto && <circle r={n.r + 3} className="anillo-problema" />}
                  {(mostrarEtiquetas || n.id === foco || (vecinos && vecinos.has(n.id))) && (
                    <text y={n.r + 13 / vista.k} fontSize={11 / Math.sqrt(vista.k)} textAnchor="middle">
                      {n.roto ? n.titulo : n.id.split("/").pop()}
                    </text>
                  )}
                  <title>
                    {n.roto ? `Nota inexistente: ${n.titulo} (enlazada desde ${n.entrantes})` : `${n.titulo}\n${n.entrantes} enlaces entrantes · ${n.salientes} salientes`}
                  </title>
                </g>
              );
            })}
          </g>
        </svg>
        <div className="leyenda">
          {leyenda &&
            Object.entries(leyenda).filter(([k]) => tiposPresentes.has(k)).map(([k, c]) => (
              <span key={k}><i style={{ background: c }} />{k}</span>
            ))}
          <span><i style={{ background: COLOR_ROTO }} />nota inexistente</span>
          <span><i className="anillo" />con problemas</span>
          <span className="ayuda">Rueda: zoom · arrastrar: mover · clic: detalle</span>
        </div>
      </div>
    </section>
  );
}
