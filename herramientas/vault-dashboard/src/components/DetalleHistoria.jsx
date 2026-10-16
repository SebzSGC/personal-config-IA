import { enlaceObsidian, estadoReq, PRIORIDADES, ICONO_TIPO, esVencida, fechaCorta, iniciales } from "../utils.js";

export default function DetalleHistoria({ item, req, proyecto, config, onCerrar, onSeleccionar }) {
  if (!item) return null;
  const e = estadoReq(item.estado);
  const epica = req.epicas.find((x) => x.id === item.epica);
  const dependientes = req.items.filter((x) => x.dependeDe.includes(item.id));
  const vencida = esVencida(item);
  const hechos = item.criterios.filter((c) => c.hecho).length;
  const porId = Object.fromEntries(req.items.map((x) => [x.id, x]));

  return (
    <aside className="detalle detalle-historia" aria-label={`Detalle de ${item.id}`}>
      <div className="detalle-cabecera">
        <div>
          <p className="detalle-ruta">{epica ? `🧩 ${epica.id} · ${epica.titulo}` : "Sin épica"}</p>
          <h2><span className="h-id">{ICONO_TIPO[item.tipo]} {item.id}</span> {item.titulo}</h2>
        </div>
        <button className="boton-icono" onClick={onCerrar} aria-label="Cerrar">✕</button>
      </div>

      <div className="h-estado">
        <span className="pildora" style={{ "--c": e.color }}>{e.nombre}</span>
        <div className="h-avance" aria-label={`Avance ${item.progreso} %`}>
          <span style={{ width: `${item.progreso}%`, background: e.color }} />
        </div>
        <b>{item.progreso} %</b>
      </div>

      {item.estado === "bloqueado" && item.bloqueo && <div className="bloque alerta"><h3>🚧 Bloqueada</h3><p>{item.bloqueo}</p></div>}
      {vencida && <div className="bloque alerta"><h3>⏰ Vencida</h3><p>La fecha fin era el {fechaCorta(item.fin)} y aún está «{e.nombre}».</p></div>}

      <dl className="datos h-datos">
        <div><dt>Responsable</dt><dd>{item.responsable ? <><span className="avatar">{iniciales(item.responsable)}</span> {item.responsable}</> : "—"}</dd></div>
        <div><dt>Prioridad</dt><dd>{item.prioridad ? `${PRIORIDADES[item.prioridad]?.icono} ${PRIORIDADES[item.prioridad]?.nombre}` : "—"}</dd></div>
        <div><dt>Puntos</dt><dd>{item.puntos ?? "Sin estimar"}</dd></div>
        <div><dt>Sprint</dt><dd>{item.sprint || "—"}</dd></div>
        <div><dt>Inicio</dt><dd>{fechaCorta(item.inicio)}</dd></div>
        <div><dt>Fin</dt><dd className={vencida ? "rojo" : ""}>{fechaCorta(item.fin)}{item.finReal ? ` (real: ${fechaCorta(item.finReal)})` : ""}</dd></div>
      </dl>

      {item.historia && <blockquote className="resumen">{item.historia}</blockquote>}

      {item.criterios.length > 0 && (
        <div className="bloque">
          <h3>Criterios de aceptación ({hechos}/{item.criterios.length})</h3>
          <ul className="checklist">
            {item.criterios.map((c, k) => <li key={k} className={c.hecho ? "ok" : ""}><span aria-hidden="true">{c.hecho ? "☑" : "☐"}</span>{c.texto}</li>)}
          </ul>
        </div>
      )}
      {item.tareas.length > 0 && (
        <div className="bloque">
          <h3>Tareas ({item.tareas.filter((t) => t.hecho).length}/{item.tareas.length})</h3>
          <ul className="checklist">
            {item.tareas.map((c, k) => <li key={k} className={c.hecho ? "ok" : ""}><span aria-hidden="true">{c.hecho ? "☑" : "☐"}</span>{c.texto}</li>)}
          </ul>
        </div>
      )}

      {(item.dependeDe.length > 0 || dependientes.length > 0) && (
        <div className="bloque">
          <h3>Dependencias</h3>
          <ul className="enlaces">
            {item.dependeDe.map((d) => (
              <li key={d}><button onClick={() => onSeleccionar(d)} title={porId[d] ? estadoReq(porId[d].estado).nombre : "No existe"}>⬅ depende de {d}{porId[d] ? ` · ${estadoReq(porId[d].estado).nombre}` : " (no existe)"}</button></li>
            ))}
            {dependientes.map((d) => <li key={d.id}><button onClick={() => onSeleccionar(d.id)}>➡ bloquea a {d.id}</button></li>)}
          </ul>
        </div>
      )}

      {item.bitacora.length > 0 && (
        <div className="bloque">
          <h3>Bitácora</h3>
          <ol className="bitacora">
            {[...item.bitacora].reverse().map((b, k) => <li key={k}>{b}</li>)}
          </ol>
        </div>
      )}

      <a className="boton-primario" href={enlaceObsidian(config, proyecto, item.ruta)}>Abrir en Obsidian</a>
    </aside>
  );
}
