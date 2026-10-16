import { enlaceObsidian, numero, ETIQUETAS_ESTADO } from "../utils.js";

export default function DetalleNota({ nota, proyecto, config, onCerrar, onNota }) {
  if (!nota) return null;
  const problemas = proyecto.problemas.filter((q) => q.nota === nota.id);
  const pendientes = proyecto.pendientes.filter((q) => q.nota === nota.id);
  const aristas = proyecto.grafo.aristas;
  const salen = aristas.filter((a) => a.a === nota.id && !a.rota).map((a) => a.b);
  const entran = aristas.filter((a) => a.b === nota.id).map((a) => a.a);
  const rotos = aristas.filter((a) => a.a === nota.id && a.rota).map((a) => a.b.replace(/^∅ /, ""));

  return (
    <aside className="detalle" aria-label={`Detalle de ${nota.titulo}`}>
      <div className="detalle-cabecera">
        <div>
          <p className="detalle-ruta">{nota.ruta}</p>
          <h2>{nota.titulo}</h2>
        </div>
        <button className="boton-icono" onClick={onCerrar} aria-label="Cerrar">✕</button>
      </div>

      <div className="chips">
        {nota.tipo && <span className="chip">{nota.tipo}</span>}
        {nota.estado && <span className={`chip estado-${nota.estado}`}>{ETIQUETAS_ESTADO[nota.estado] || nota.estado}</span>}
        {nota.huerfana && <span className="chip naranja">huérfana</span>}
      </div>

      {nota.resumen && <blockquote className="resumen">{nota.resumen}</blockquote>}

      <dl className="datos">
        <div><dt>Responsable</dt><dd>{nota.responsable || "—"}</dd></div>
        <div><dt>Actualizado</dt><dd>{nota.actualizado || "—"}</dd></div>
        <div><dt>Palabras</dt><dd>{numero(nota.palabras)}</dd></div>
        <div><dt>Diagramas</dt><dd>{nota.diagramas}</dd></div>
      </dl>

      {problemas.length > 0 && (
        <div className="bloque alerta">
          <h3>⚠️ Problemas</h3>
          <ul>{problemas.map((q, i) => <li key={i}>{q.problema}</li>)}</ul>
        </div>
      )}
      {pendientes.length > 0 && (
        <div className="bloque info">
          <h3>❓ Por confirmar</h3>
          <ul>{pendientes.map((q, i) => <li key={i}>{q.texto}</li>)}</ul>
        </div>
      )}

      <ListaEnlaces titulo={`Enlaza a (${salen.length})`} ids={salen} onNota={onNota} />
      <ListaEnlaces titulo={`Enlazada desde (${entran.length})`} ids={entran} onNota={onNota} />
      {rotos.length > 0 && (
        <div className="bloque">
          <h3>Enlaces rotos ({rotos.length})</h3>
          <ul>{rotos.map((r) => <li key={r} className="roto">{r}</li>)}</ul>
        </div>
      )}

      <a className="boton-primario" href={enlaceObsidian(config, proyecto.nombre, nota.ruta)}>Abrir en Obsidian</a>
    </aside>
  );
}

function ListaEnlaces({ titulo, ids, onNota }) {
  if (!ids.length) return null;
  return (
    <div className="bloque">
      <h3>{titulo}</h3>
      <ul className="enlaces">
        {ids.map((id) => (
          <li key={id}><button onClick={() => onNota(id)}>{id.split("/").pop()}</button></li>
        ))}
      </ul>
    </div>
  );
}
