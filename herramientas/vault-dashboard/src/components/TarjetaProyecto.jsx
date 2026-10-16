import { haceCuanto, fecha, numero, tamano, nivelSalud } from "../utils.js";

function Actividad({ semanas }) {
  const max = Math.max(1, ...semanas);
  return (
    <div className="actividad" title={`Commits por semana (últimas ${semanas.length} semanas): ${semanas.join(", ")}`}>
      {semanas.map((v, i) => (
        <span key={i} style={{ height: `${v ? 20 + (v / max) * 80 : 6}%` }} className={v ? "con" : ""} />
      ))}
    </div>
  );
}

export default function TarjetaProyecto({ p, activo, onClick }) {
  const salud = nivelSalud(p.salud);
  return (
    <button className={`tarjeta ${activo ? "activa" : ""}`} onClick={onClick} aria-pressed={activo}>
      <div className="tarjeta-cabecera">
        <h3>{p.nombre}</h3>
        <span className={`salud ${salud.clase}`} title={`Salud de la documentación: ${salud.texto}`}>{p.salud}</span>
      </div>
      <div className="metricas">
        <div><strong>{numero(p.notas)}</strong><span>notas</span></div>
        <div><strong>{numero(p.enlaces)}</strong><span>enlaces</span></div>
        <div><strong>{tamano(p.tamano)}</strong><span>tamaño</span></div>
      </div>
      <div className="insignias">
        {p.rotos.length > 0 && <span className="insignia naranja">{p.rotos.length} {p.rotos.length === 1 ? "enlace roto" : "enlaces rotos"}</span>}
        {p.huerfanas.length > 0 && <span className="insignia naranja">{p.huerfanas.length} {p.huerfanas.length === 1 ? "huérfana" : "huérfanas"}</span>}
        {p.problemas.length > 0 && <span className="insignia roja">{p.problemas.length} {p.problemas.length === 1 ? "problema" : "problemas"}</span>}
        {p.pendientes.length > 0 && <span className="insignia azul">{p.pendientes.length} por confirmar</span>}
        {p.sinConfirmar.length > 0 && <span className="insignia gris">{p.sinConfirmar.length} sin commit</span>}
        {!p.rotos.length && !p.huerfanas.length && !p.problemas.length && !p.pendientes.length && (
          <span className="insignia verde">Todo en orden</span>
        )}
      </div>
      {p.requerimientos && (
        <div className="tarjeta-req" title={`Requerimientos: ${p.requerimientos.resumen.avance} % de avance`}>
          <span>📋 {p.requerimientos.resumen.conteo.hecho}/{p.requerimientos.resumen.total} historias hechas</span>
          <span className="mini-barra"><span style={{ width: `${p.requerimientos.resumen.avance}%` }} /></span>
          <b>{p.requerimientos.resumen.avance} %</b>
        </div>
      )}
      <div className="tarjeta-pie">
        <span title={fecha(p.ultimoCambio)}>
          Cambiado {haceCuanto(p.ultimoCambio)} · {p.autores.length} {p.autores.length === 1 ? "autor" : "autores"}
        </span>
        <Actividad semanas={p.actividad} />
      </div>
    </button>
  );
}
