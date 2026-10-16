import { useMemo, useState } from "react";
import Gantt from "./Gantt.jsx";
import TableroKanban from "./TableroKanban.jsx";
import { ESTADOS_REQ, estadoReq, esVencida, fechaCorta, numero } from "../utils.js";

const normalizar = (s) => String(s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

export default function Requerimientos({ p, vista, onVista, seleccion, onSeleccionar }) {
  const req = p.requerimientos;
  const [epica, setEpica] = useState("");
  const [responsable, setResponsable] = useState("");
  const [texto, setTexto] = useState("");
  const [descartados, setDescartados] = useState(false);

  const responsables = useMemo(() => [...new Set(req.items.map((i) => i.responsable).filter(Boolean))].sort(), [req]);
  const filtrados = useMemo(() => req.items.filter((i) =>
    (descartados || i.estado !== "descartado") &&
    (!epica || (epica === "_sin" ? !i.epica : i.epica === epica)) &&
    (!responsable || (responsable === "_sin" ? !i.responsable : i.responsable === responsable)) &&
    (!texto || normalizar(`${i.id} ${i.titulo} ${i.historia}`).includes(normalizar(texto)))
  ), [req, epica, responsable, texto, descartados]);

  const activos = req.items.filter((i) => i.estado !== "descartado");
  const vencidas = activos.filter(esVencida);
  const bloqueadas = activos.filter((i) => i.estado === "bloqueado");
  const r = req.resumen;
  const enCurso = r.conteo["en-progreso"] + r.conteo["en-revision"];

  const alertas = useMemo(() => {
    const out = [];
    const porId = Object.fromEntries(req.items.map((i) => [i.id, i]));
    for (const i of activos) {
      if (i.estado === "bloqueado") out.push({ id: i.id, nivel: "rojo", texto: `Bloqueada: ${i.bloqueo || "sin motivo registrado"}` });
      if (esVencida(i)) out.push({ id: i.id, nivel: "rojo", texto: `Vencida desde el ${fechaCorta(i.fin)} (${estadoReq(i.estado).nombre})` });
      if (i.estado === "hecho" && i.criterios.some((c) => !c.hecho)) out.push({ id: i.id, nivel: "naranja", texto: "Hecha con criterios de aceptación sin marcar" });
      for (const d of i.dependeDe) {
        const dep = porId[d];
        if (!dep) out.push({ id: i.id, nivel: "naranja", texto: `Depende de ${d}, que no existe` });
        else if (["en-progreso", "en-revision", "hecho"].includes(i.estado) && !["hecho", "descartado"].includes(dep.estado))
          out.push({ id: i.id, nivel: "naranja", texto: `Avanza antes que su dependencia ${d} (${estadoReq(dep.estado).nombre})` });
      }
      if (i.tipo === "historia" && !i.criterios.length) out.push({ id: i.id, nivel: "gris", texto: "Sin criterios de aceptación" });
      if (i.estado === "por-hacer" && (!i.inicio || !i.fin)) out.push({ id: i.id, nivel: "gris", texto: "Por hacer pero sin fechas planificadas" });
    }
    return out;
  }, [req]);

  return (
    <div className="requerimientos">
      {/* Indicadores */}
      <div className="kpis">
        <div className="kpi kpi-avance">
          <span className="kpi-etq">Avance general</span>
          <strong>{r.avance} %</strong>
          <span className="kpi-barra"><span style={{ width: `${r.avance}%` }} /></span>
          <span className="kpi-sub">{r.puntos ? `${numero(r.puntosHechos)} de ${numero(r.puntos)} puntos hechos` : "Sin estimaciones"}</span>
        </div>
        <div className="kpi"><span className="kpi-etq">Hechas</span><strong>{r.conteo.hecho}<small> / {r.total}</small></strong><span className="kpi-sub">historias y requerimientos</span></div>
        <div className="kpi"><span className="kpi-etq">En curso</span><strong>{enCurso}</strong><span className="kpi-sub">{r.conteo["en-progreso"]} en progreso · {r.conteo["en-revision"]} en revisión</span></div>
        <div className="kpi"><span className="kpi-etq">Por iniciar</span><strong>{r.conteo["por-hacer"] + r.conteo.backlog}</strong><span className="kpi-sub">{r.conteo["por-hacer"]} por hacer · {r.conteo.backlog} sin iniciar</span></div>
        <div className={`kpi ${bloqueadas.length || vencidas.length ? "kpi-alerta" : ""}`}>
          <span className="kpi-etq">Atención</span>
          <strong>{bloqueadas.length + vencidas.length}</strong>
          <span className="kpi-sub">{bloqueadas.length} bloqueadas · {vencidas.length} vencidas</span>
        </div>
      </div>

      {/* Distribución por estado */}
      <div className="distribucion" role="img" aria-label={ESTADOS_REQ.map((e) => `${e.nombre}: ${r.conteo[e.id]}`).join(", ")}>
        <div className="barra-apilada grande">
          {ESTADOS_REQ.filter((e) => e.id !== "descartado" && r.conteo[e.id]).map((e) => (
            <span key={e.id} style={{ flex: r.conteo[e.id], background: e.color }} title={`${e.nombre}: ${r.conteo[e.id]}`} />
          ))}
        </div>
        <ul className="leyenda-estados en-linea">
          {ESTADOS_REQ.filter((e) => e.id !== "descartado" || r.conteo.descartado).map((e) => (
            <li key={e.id}><i style={{ background: e.color }} />{e.nombre}<b>{r.conteo[e.id]}</b></li>
          ))}
        </ul>
      </div>

      {/* Barra de herramientas */}
      <section className="panel">
        <div className="herramientas">
          <div className="segmentado" role="group" aria-label="Vista">
            <button className={vista === "cronograma" ? "activo" : ""} onClick={() => onVista("cronograma")}>📅 Cronograma</button>
            <button className={vista === "tablero" ? "activo" : ""} onClick={() => onVista("tablero")}>📋 Tablero</button>
          </div>
          <select value={epica} onChange={(e) => setEpica(e.target.value)} aria-label="Filtrar por épica">
            <option value="">Todas las épicas</option>
            {req.epicas.map((e) => <option key={e.id} value={e.id}>{e.id} · {e.titulo}</option>)}
            {req.items.some((i) => !i.epica) && <option value="_sin">Sin épica</option>}
          </select>
          <select value={responsable} onChange={(e) => setResponsable(e.target.value)} aria-label="Filtrar por responsable">
            <option value="">Todos los responsables</option>
            {responsables.map((x) => <option key={x} value={x}>{x}</option>)}
            {req.items.some((i) => !i.responsable) && <option value="_sin">Sin responsable</option>}
          </select>
          <input type="search" placeholder="Buscar ID o texto…" value={texto} onChange={(e) => setTexto(e.target.value)} aria-label="Buscar historia" />
          {r.conteo.descartado > 0 && (
            <label className="check"><input type="checkbox" checked={descartados} onChange={(e) => setDescartados(e.target.checked)} /> Descartadas</label>
          )}
          <span className="tenue">{filtrados.length} de {req.items.length}</span>
        </div>
        {vista === "tablero"
          ? <TableroKanban items={filtrados} epicas={req.epicas} seleccion={seleccion} onSeleccionar={onSeleccionar} mostrarDescartados={descartados} />
          : <Gantt items={filtrados} epicas={req.epicas} seleccion={seleccion} onSeleccionar={onSeleccionar} />}
      </section>

      {/* Épicas y alertas */}
      <div className="paneles">
        <section className="panel lista">
          <h2>Épicas<span className="contador">{req.epicas.length}</span></h2>
          {req.epicas.length === 0 ? <p className="vacio">Sin épicas.</p> : (
            <ul>
              {req.epicas.map((e) => (
                <li key={e.id}>
                  <button className="fila" onClick={() => { setEpica(e.id); }} title={e.objetivo}>
                    <span className="fila-izq">
                      <span className="fila-texto">{e.id} · {e.titulo}</span>
                      <span className="mini-barra"><span style={{ width: `${e.progreso}%` }} /></span>
                    </span>
                    <span className="fila-der">{e.progreso} % · {e.items} ítems</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
        <section className="panel lista ancho-2">
          <h2>Alertas<span className="contador">{alertas.length}</span></h2>
          {alertas.length === 0 ? <p className="vacio">✅ Sin alertas: nada vencido ni bloqueado.</p> : (
            <ul>
              {alertas.slice(0, 10).map((a, k) => (
                <li key={k}>
                  <button className="fila" onClick={() => onSeleccionar(a.id)}>
                    <span className="fila-izq"><span className="fila-texto"><span className={`semaforo ${a.nivel}`} />{a.texto}</span></span>
                    <span className="fila-der">{a.id}</span>
                  </button>
                </li>
              ))}
              {alertas.length > 10 && <li className="mas">y {alertas.length - 10} más…</li>}
            </ul>
          )}
        </section>
      </div>
    </div>
  );
}
