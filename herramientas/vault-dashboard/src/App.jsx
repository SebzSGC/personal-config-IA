import { useEffect, useMemo, useState } from "react";
import datos from "./datos.js";
import TarjetaProyecto from "./components/TarjetaProyecto.jsx";
import Grafo from "./components/Grafo.jsx";
import DetalleNota from "./components/DetalleNota.jsx";
import Requerimientos from "./components/Requerimientos.jsx";
import DetalleHistoria from "./components/DetalleHistoria.jsx";
import {
  CambiosRecientes, Autores, MasEnlazadas, EnlacesRotos, Huerfanas, Etiquetas,
  Pendientes, Problemas, EstadoDocumentacion, SinConfirmar,
} from "./components/Paneles.jsx";
import { fecha, haceCuanto, numero } from "./utils.js";

const normalizar = (s) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

function leerHash() {
  const q = new URLSearchParams(location.hash.slice(1));
  return { proyecto: q.get("p"), nota: q.get("n"), vista: q.get("v"), historia: q.get("h"), modo: q.get("m") };
}

export default function App() {
  const { proyectos, config = {} } = datos;
  const inicial = leerHash();
  const [actual, setActual] = useState(
    proyectos.find((p) => p.nombre === inicial.proyecto)?.nombre ?? proyectos[0]?.nombre
  );
  const [nota, setNota] = useState(inicial.nota);
  const [vista, setVista] = useState(inicial.vista === "req" ? "req" : "docs");
  const [modoReq, setModoReq] = useState(inicial.modo === "tablero" ? "tablero" : "cronograma");
  const [historia, setHistoria] = useState(inicial.historia);
  const [busqueda, setBusqueda] = useState("");

  const p = proyectos.find((x) => x.nombre === actual);
  const req = p?.requerimientos || null;
  const vistaReal = vista === "req" && req ? "req" : "docs";
  const notaSel = vistaReal === "docs" ? p?.grafo.nodos.find((n) => n.id === nota && !n.roto) || null : null;
  const historiaSel = vistaReal === "req" ? req.items.find((i) => i.id === historia) || null : null;

  useEffect(() => {
    if (!actual) return;
    const q = new URLSearchParams({ p: actual });
    if (vistaReal === "req") { q.set("v", "req"); q.set("m", modoReq); if (historia) q.set("h", historia); }
    else if (nota) q.set("n", nota);
    history.replaceState(null, "", "#" + q.toString());
    document.title = `${actual} · ${config.titulo || "Dashboard de documentación"}`;
  }, [actual, nota, historia, vistaReal, modoReq, config.titulo]);

  useEffect(() => {
    const esc = (e) => { if (e.key === "Escape") { setNota(null); setHistoria(null); } };
    window.addEventListener("keydown", esc);
    return () => window.removeEventListener("keydown", esc);
  }, []);

  const resultados = useMemo(() => {
    const q = normalizar(busqueda.trim());
    if (q.length < 2) return [];
    const out = [];
    for (const pr of proyectos) {
      for (const i of pr.requerimientos?.items || [])
        if (normalizar(i.id).includes(q) || normalizar(i.titulo).includes(q))
          out.push({ proyecto: pr.nombre, h: i });
      for (const n of pr.grafo.nodos)
        if (!n.roto && !["historia", "requerimiento"].includes(n.tipo) && (normalizar(n.titulo).includes(q) || normalizar(n.id).includes(q) || normalizar(n.resumen || "").includes(q)))
          out.push({ proyecto: pr.nombre, n });
    }
    return out.slice(0, 12);
  }, [busqueda, proyectos]);

  const irANota = (proyecto, id) => {
    setActual(proyecto);
    setVista("docs");
    setNota(id);
    setBusqueda("");
  };
  const irAHistoria = (proyecto, id) => {
    setActual(proyecto);
    setVista("req");
    setHistoria(id);
    setBusqueda("");
  };
  const elegir = (r) => (r.h ? irAHistoria(r.proyecto, r.h.id) : irANota(r.proyecto, r.n.id));

  const totales = useMemo(() => ({
    notas: proyectos.reduce((a, x) => a + x.notas, 0),
    rotos: proyectos.reduce((a, x) => a + x.rotos.length, 0),
    salud: proyectos.length ? Math.round(proyectos.reduce((a, x) => a + x.salud, 0) / proyectos.length) : 0,
  }), [proyectos]);

  if (!proyectos.length) {
    return (
      <div className="vacio-total">
        <h1>No se encontraron proyectos</h1>
        <p>El repositorio <b>{datos.repositorio}</b> no tiene carpetas con notas <code>.md</code> en el primer nivel.</p>
      </div>
    );
  }

  const onNota = (id) => setNota(id);

  return (
    <>
      <header className="cabecera">
        <div className="cabecera-titulo">
          <h1>{config.titulo || "Dashboard de documentación"}</h1>
          <span className="repo" title={datos.remoto || ""}>
            {datos.repositorio}{datos.rama ? ` · ${datos.rama}` : ""}
          </span>
        </div>
        <div className="buscador">
          <input
            type="search"
            placeholder="Buscar nota o historia (ej. HU-003)…"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && resultados[0] && elegir(resultados[0])}
            aria-label="Buscar nota"
          />
          {resultados.length > 0 && (
            <ul className="resultados">
              {resultados.map((r) => (
                <li key={r.proyecto + (r.h ? r.h.id : r.n.id)}>
                  <button onClick={() => elegir(r)}>
                    <span>{r.h ? `${r.h.id} · ${r.h.titulo}` : r.n.titulo}</span>
                    <small>{r.proyecto} · {r.h ? "Historia · " + r.h.ruta : r.n.ruta}</small>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </header>

      <main className={`contenido ${notaSel || historiaSel ? "con-detalle" : ""}`}>
        <p className="resumen-general">
          {proyectos.length} {proyectos.length === 1 ? "proyecto" : "proyectos"} · {numero(totales.notas)} notas ·
          {" "}{totales.rotos} {totales.rotos === 1 ? "enlace roto" : "enlaces rotos"} · salud promedio {totales.salud}/100.{" "}
          <span className="tenue" title={fecha(datos.generado)}>
            Generado {haceCuanto(datos.generado)}
            {datos.commit && <> desde el commit <code>{datos.commit.hash}</code> de {datos.commit.autor} ({haceCuanto(datos.commit.fecha)})</>}.
            {!datos.git && " (Sin git: se usaron las fechas de los archivos.)"}
          </span>
        </p>

        <div className="tarjetas">
          {proyectos.map((x) => (
            <TarjetaProyecto key={x.nombre} p={x} activo={x.nombre === actual} onClick={() => { setActual(x.nombre); setNota(null); setHistoria(null); }} />
          ))}
        </div>

        <nav className="pestanas" aria-label="Secciones del proyecto">
          <button className={vistaReal === "docs" ? "activa" : ""} onClick={() => setVista("docs")} aria-current={vistaReal === "docs"}>
            📚 Documentación
          </button>
          <button
            className={vistaReal === "req" ? "activa" : ""}
            onClick={() => req && setVista("req")}
            disabled={!req}
            aria-current={vistaReal === "req"}
            title={req ? "" : "Este proyecto aún no tiene historias de usuario (skill requerimientos-historias)"}
          >
            📋 Requerimientos {req ? <span className="contador">{req.resumen.total}</span> : <span className="tenue">· sin historias</span>}
          </button>
        </nav>

        {vistaReal === "req" ? (
          <Requerimientos p={p} vista={modoReq} onVista={setModoReq} seleccion={historiaSel?.id || null} onSeleccionar={setHistoria} />
        ) : (<>
        <Grafo proyecto={p} seleccion={notaSel?.id || null} onSeleccionar={setNota} />

        <div className="paneles">
          <CambiosRecientes p={p} onNota={onNota} />
          <Autores p={p} />
          <MasEnlazadas p={p} onNota={onNota} />
          <EnlacesRotos p={p} onNota={onNota} />
          <Huerfanas p={p} onNota={onNota} />
          <Etiquetas p={p} />
          <Pendientes p={p} onNota={onNota} />
          <EstadoDocumentacion p={p} />
          <Problemas p={p} onNota={onNota} />
          <SinConfirmar p={p} />
        </div>
        </>)}
      </main>

      <DetalleNota nota={notaSel} proyecto={p} config={config} onCerrar={() => setNota(null)} onNota={onNota} />
      {req && <DetalleHistoria item={historiaSel} req={req} proyecto={p.nombre} config={config} onCerrar={() => setHistoria(null)} onSeleccionar={setHistoria} />}
    </>
  );
}
