#!/usr/bin/env node
/* Chaîne complète : voix -> durées -> rendu. Usage : node tools/make.mjs <projet> [--max s] */
import { spawnSync } from "node:child_process";
import path from "node:path";
import { root } from "./lib.mjs";

const [name, ...rest] = process.argv.slice(2);
if (!name) { console.log("Usage : node tools/make.mjs <projet> [--max s]"); process.exit(1); }
for (const [script, args] of [["tts.mjs", [name]], ["build-props.mjs", [name, ...rest]], ["render.mjs", [name]]]) {
  const r = spawnSync("node", [path.join(root, "tools", script), ...args], { stdio: "inherit", cwd: root });
  if (r.status !== 0) process.exit(r.status ?? 1);
}
