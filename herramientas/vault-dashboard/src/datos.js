/**
 * Datos del dashboard.
 *
 * - En el HTML generado, generar_dashboard.py reemplaza el contenido de
 *   <script id="datos-dashboard" type="application/json"> con el JSON del escaneo.
 * - En desarrollo (npm run dev) se usa src/data/datos.json si existe; si no, datos.ejemplo.json.
 *
 * Se exporta un objeto que se llena antes de montar la app (ver main.jsx).
 */
const datos = {};
export default datos;

const VACIO = { repositorio: "", proyectos: [], config: {} };

function leerDelHtml() {
  const el = document.getElementById("datos-dashboard");
  const texto = el?.textContent?.trim();
  if (!texto || texto.startsWith("__")) return null; // marcador sin reemplazar
  try {
    return JSON.parse(texto);
  } catch (e) {
    console.error("No se pudieron leer los datos del dashboard", e);
    return null;
  }
}

export async function cargarDatos() {
  let d = leerDelHtml();
  if (!d && import.meta.env.DEV) {
    const locales = import.meta.glob("./data/datos*.json", { import: "default" });
    const cargar = locales["./data/datos.json"] || locales["./data/datos.ejemplo.json"];
    if (cargar) d = await cargar();
  }
  Object.assign(datos, d || VACIO);
  return datos;
}
