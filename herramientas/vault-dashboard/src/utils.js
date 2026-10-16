const nf = new Intl.NumberFormat("es-CO");
const rtf = new Intl.RelativeTimeFormat("es", { numeric: "auto" });
const df = new Intl.DateTimeFormat("es-CO", { dateStyle: "medium", timeStyle: "short" });

export const numero = (n) => nf.format(n ?? 0);

export function tamano(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1).replace(".", ",")} KB`;
  return `${(bytes / 1024 ** 2).toFixed(1).replace(".", ",")} MB`;
}

/** "hace 3 días", relativo al momento en que se abre el dashboard. */
export function haceCuanto(iso) {
  if (!iso) return "—";
  const seg = (new Date(iso).getTime() - Date.now()) / 1000;
  const abs = Math.abs(seg);
  if (abs < 60) return "justo ahora";
  if (abs < 3600) return rtf.format(Math.round(seg / 60), "minute");
  if (abs < 86400) return rtf.format(Math.round(seg / 3600), "hour");
  if (abs < 86400 * 30) return rtf.format(Math.round(seg / 86400), "day");
  if (abs < 86400 * 365) return rtf.format(Math.round(seg / (86400 * 30)), "month");
  return rtf.format(Math.round(seg / (86400 * 365)), "year");
}

export const fecha = (iso) => (iso ? df.format(new Date(iso)) : "—");

export const nombreNota = (id) => id.split("/").pop();
export const carpetaNota = (id) => (id.includes("/") ? id.split("/").slice(0, -1).join("/") : "");

export function enlaceObsidian(config, proyecto, rutaNota) {
  const ruta = rutaNota.endsWith(".md") ? rutaNota : rutaNota + ".md";
  const vault = config?.modoVault === "proyecto" ? proyecto : config?.vaultObsidian;
  const file = config?.modoVault === "proyecto" ? ruta : `${proyecto}/${ruta}`;
  return `obsidian://open?vault=${encodeURIComponent(vault || "")}&file=${encodeURIComponent(file)}`;
}

export function nivelSalud(s) {
  if (s >= 85) return { clase: "ok", texto: "Saludable" };
  if (s >= 65) return { clase: "aviso", texto: "Mejorable" };
  return { clase: "mal", texto: "Requiere atención" };
}

export const ETIQUETAS_ESTADO = {
  vigente: "Vigente", aceptada: "Aceptada", borrador: "Borrador", propuesta: "Propuesta",
  obsoleto: "Obsoleto", reemplazada: "Reemplazada", descartada: "Descartada", "sin definir": "Sin definir",
};

// ───────────── Requerimientos ─────────────
export const ESTADOS_REQ = [
  { id: "backlog", nombre: "Sin iniciar", color: "var(--e-backlog)" },
  { id: "por-hacer", nombre: "Por hacer", color: "var(--e-porhacer)" },
  { id: "en-progreso", nombre: "En progreso", color: "var(--e-progreso)" },
  { id: "en-revision", nombre: "En revisión", color: "var(--e-revision)" },
  { id: "hecho", nombre: "Hecho", color: "var(--e-hecho)" },
  { id: "bloqueado", nombre: "Bloqueado", color: "var(--e-bloqueado)" },
  { id: "descartado", nombre: "Descartado", color: "var(--e-descartado)" },
];
export const estadoReq = (id) => ESTADOS_REQ.find((e) => e.id === id) || ESTADOS_REQ[0];
export const PRIORIDADES = {
  critica: { nombre: "Crítica", icono: "⏫", orden: 0 },
  alta: { nombre: "Alta", icono: "🔼", orden: 1 },
  media: { nombre: "Media", icono: "➖", orden: 2 },
  baja: { nombre: "Baja", icono: "🔽", orden: 3 },
};
export const ICONO_TIPO = { historia: "📗", requerimiento: "📘", epica: "🧩" };

const DIA = 864e5;
export const aFecha = (iso) => (iso ? new Date(iso + "T00:00:00") : null);
export const hoyLocal = () => { const d = new Date(); d.setHours(0, 0, 0, 0); return d; };
export const diasEntre = (a, b) => Math.round((b - a) / DIA);
export const sumarDias = (d, n) => new Date(d.getTime() + n * DIA);
export const fechaCorta = (iso) => (iso ? new Intl.DateTimeFormat("es-CO", { day: "numeric", month: "short" }).format(aFecha(iso)) : "—");
export const esVencida = (i) => i.fin && !["hecho", "descartado"].includes(i.estado) && aFecha(i.fin) < hoyLocal();
export const iniciales = (n) => (n || "?").split(/\s+/).filter(Boolean).slice(0, 2).map((x) => x[0]).join("").toUpperCase();
