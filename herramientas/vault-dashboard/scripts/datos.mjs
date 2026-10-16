#!/usr/bin/env node
/**
 * Escanea un repositorio real y deja los datos en src/data/datos.json para verlos con `npm run dev`.
 * Usa el mismo escáner (Python) que el plugin, así lo que ves en desarrollo es lo que verá el usuario.
 *
 *   npm run datos -- --repo "C:/ruta/repo-de-documentacion" [--modo repo]
 */
import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const raiz = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const escaner = path.resolve(raiz, "../../plugins/antigravity/obsidian-docs/skills/dashboard-documentacion/scripts/escanear.py");
const args = [escaner, ...process.argv.slice(2), "--salida", path.join(raiz, "src", "data", "datos.json")];
const candidatos = process.platform === "win32" ? [["py", ["-3"]], ["python", []]] : [["python3", []], ["python", []]];
for (const [cmd, pre] of candidatos) {
  const r = spawnSync(cmd, [...pre, ...args], { stdio: "inherit" });
  if (!r.error) process.exit(r.status ?? 1);
}
console.error("❌ No encontré Python 3 (py, python3 o python).");
process.exit(1);
