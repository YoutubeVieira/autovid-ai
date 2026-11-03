#!/usr/bin/env node
/* Rend la vidéo : out/<projet>.mp4. Usage : node tools/render.mjs <projet> [--frame N] (--frame : une image PNG de contrôle) */
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { root } from "./lib.mjs";

const name = process.argv[2];
if (!name) { console.log("Usage : node tools/render.mjs <projet> [--frame N]"); process.exit(1); }
const props = path.join(root, ".cache", name + ".props.json");
if (!fs.existsSync(props)) { console.log("Lancez d'abord : node tools/build-props.mjs " + name); process.exit(1); }
fs.mkdirSync(path.join(root, "out"), { recursive: true });
const fi = process.argv.indexOf("--frame");
const comp = JSON.parse(fs.readFileSync(props, "utf8")).format === "16:9" ? "MapStoryWide" : "MapStory";
const win = process.platform === "win32";
const bin = path.join(root, "node_modules", ".bin", win ? "remotion.cmd" : "remotion");
const common = ["--props=" + props, "--gl=angle", "--concurrency=" + (process.env.CONCURRENCY || "2")];
if (fs.existsSync("/opt/pw-browsers/chromium")) common.push("--browser-executable=/opt/pw-browsers/chromium");
const args = fi > 0
  ? ["still", "src/index.ts", comp, path.join(root, "out", name + "-f" + process.argv[fi + 1] + ".png"), "--frame=" + process.argv[fi + 1], ...common]
  : ["render", "src/index.ts", comp, path.join(root, "out", name + ".mp4"), "--codec=h264", ...common];
const r = spawnSync(bin, args, { cwd: root, stdio: "inherit", shell: win });
process.exit(r.status ?? 1);
