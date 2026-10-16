#!/usr/bin/env node
/**
 * Compila la interfaz y la copia como plantilla al skill dashboard-documentacion del plugin.
 * Uso: npm run publicar   (después, commit de la plantilla con el resto del cambio)
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const raiz = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const destino = path.resolve(raiz, "../../plugins/antigravity/obsidian-docs/skills/dashboard-documentacion/assets/plantilla.html");

const { build } = await import("vite");
await build({ root: raiz, logLevel: "warn" });
const html = fs.readFileSync(path.join(raiz, "dist", "index.html"), "utf8");
const n = html.split("__DATOS_DASHBOARD__").length - 1;
if (n !== 1) {
  console.error(`❌ La compilación debe tener exactamente un marcador __DATOS_DASHBOARD__ (tiene ${n}). Revisa index.html.`);
  process.exit(1);
}
fs.mkdirSync(path.dirname(destino), { recursive: true });
fs.writeFileSync(destino, html);
console.log(`✅ Plantilla publicada (${(html.length / 1024).toFixed(0)} KB): ${path.relative(process.cwd(), destino)}`);
