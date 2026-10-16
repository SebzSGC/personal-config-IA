import { ESTADOS_REQ, PRIORIDADES, ICONO_TIPO, esVencida, fechaCorta, iniciales } from "../utils.js";

export default function TableroKanban({ items, epicas, seleccion, onSeleccionar, mostrarDescartados }) {
  const columnas = ESTADOS_REQ.filter((e) => e.id !== "descartado" || mostrarDescartados);
  const nombreEpica = Object.fromEntries(epicas.map((e) => [e.id, e.titulo]));
  const orden = (a, b) => (PRIORIDADES[a.prioridad]?.orden ?? 9) - (PRIORIDADES[b.prioridad]?.orden ?? 9) || a.id.localeCompare(b.id, "es", { numeric: true });

  return (
    <div className="kanban" role="list">
      {columnas.map((col) => {
        const tarjetas = items.filter((i) => i.estado === col.id).sort(orden);
        const puntos = tarjetas.reduce((a, i) => a + (i.puntos || 0), 0);
        return (
          <section key={col.id} className="k-columna" role="listitem" aria-label={col.nombre}>
            <header style={{ "--c": col.color }}>
              <span className="k-punto" />
              <h3>{col.nombre}</h3>
              <span className="contador">{tarjetas.length}</span>
              {puntos > 0 && <span className="k-puntos" title="Puntos de historia">{puntos} pts</span>}
            </header>
            <div className="k-tarjetas">
              {tarjetas.length === 0 && <p className="k-vacio">—</p>}
              {tarjetas.map((i) => {
                const vencida = esVencida(i);
                return (
                  <button key={i.id} className={`k-tarjeta ${seleccion === i.id ? "sel" : ""}`} onClick={() => onSeleccionar(i.id)}>
                    <span className="k-titulo">{i.titulo}</span>
                    {i.bloqueo && i.estado === "bloqueado" && <span className="k-bloqueo">🚧 {i.bloqueo}</span>}
                    {i.epica && <span className="k-epica" title={nombreEpica[i.epica] || i.epica}>{i.epica} · {nombreEpica[i.epica] || ""}</span>}
                    <span className="k-progreso" aria-label={`Avance ${i.progreso} %`}><span style={{ width: `${i.progreso}%`, background: col.color }} /></span>
                    <span className="k-pie">
                      <span className="k-id">{ICONO_TIPO[i.tipo]} {i.id}</span>
                      {i.prioridad && <span title={`Prioridad ${PRIORIDADES[i.prioridad]?.nombre}`}>{PRIORIDADES[i.prioridad]?.icono}</span>}
                      {i.puntos != null && <span className="k-pts">{i.puntos}</span>}
                      {i.dependeDe.length > 0 && <span title={`Depende de ${i.dependeDe.join(", ")}`}>🔗</span>}
                      <span className={`k-fecha ${vencida ? "vencida" : ""}`} title={vencida ? "Vencida" : "Fecha fin"}>{i.fin ? (vencida ? "⏰ " : "") + fechaCorta(i.fin) : ""}</span>
                      <span className="avatar" title={i.responsable || "Sin responsable"}>{i.responsable ? iniciales(i.responsable) : "?"}</span>
                    </span>
                  </button>
                );
              })}
            </div>
          </section>
        );
      })}
    </div>
  );
}
