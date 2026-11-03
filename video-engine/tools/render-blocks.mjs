#!/usr/bin/env node
/* Rendu d'une longue vidéo par blocs (reprise possible), puis assemblage et compression.
   Chaque bloc = N images (60 s par défaut) dans out/blocs/<projet>/bloc-XXX.mp4 ; un bloc déjà rendu est conservé.
   Usage : node tools/render-blocks.mjs <projet> [--bloc 1800] [--concurrency 4] [--crf 23] [--assemble-only]
   Sortie : out/<projet>-final.mp4 */
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { root } from "./lib.mjs";

const args = process.argv.slice(2), name = args[0];
const opt = (f, d) => { const i = args.indexOf(f); return i > 0 ? args[i + 1] : d; };
if (!name) { console.log("Usage : node tools/render-blocks.mjs <projet> [--bloc 1800] [--concurrency 4] [--crf 23] [--assemble-only]"); process.exit(1); }
const propsFile = path.join(root, ".cache", name + ".props.json");
if (!fs.existsSync(propsFile)) { console.log("Lancez d'abord : node tools/build-props.mjs " + name); process.exit(1); }
const props = JSON.parse(fs.readFileSync(propsFile, "utf8"));
const total = props.scenes.reduce((n, s) => n + s.durationInFrames, 0);
const size = Number(opt("--bloc", 1800)), comp = props.format === "16:9" ? "MapStoryWide" : "MapStory";
const dir = path.join(root, "out", "blocs", name);
fs.mkdirSync(dir, { recursive: true });
const win = process.platform === "win32";
const bin = path.join(root, "node_modules", ".bin", win ? "remotion.cmd" : "remotion");
const n = Math.ceil(total / size), files = [];
for (let i = 0; i < n; i++) {
  const a = i * size, b = Math.min(total - 1, a + size - 1), f = path.join(dir, "bloc-" + String(i).padStart(3, "0") + ".mp4");
  files.push(f);
  if (args.includes("--assemble-only") || (fs.existsSync(f) && fs.statSync(f).size > 10000)) { console.log("bloc " + (i + 1) + "/" + n + " : déjà rendu"); continue; }
  const common = ["--props=" + propsFile, "--gl=angle", "--concurrency=" + opt("--concurrency", "4"), "--crf=" + opt("--crf", "23")];
  if (fs.existsSync("/opt/pw-browsers/chromium")) common.push("--browser-executable=/opt/pw-browsers/chromium");
  const t0 = Date.now();
  console.log("bloc " + (i + 1) + "/" + n + " : images " + a + " à " + b);
  const r = spawnSync(bin, ["render", "src/index.ts", comp, f, "--codec=h264", "--frames=" + a + "-" + b, ...common], { cwd: root, stdio: ["ignore", "ignore", "inherit"], shell: win });
  if (r.status !== 0) { console.error("Échec du bloc " + (i + 1) + " : relancez la même commande, les blocs terminés sont conservés."); process.exit(1); }
  console.log("  fait en " + Math.round((Date.now() - t0) / 1000) + " s");
}
const list = path.join(dir, "liste.txt");
fs.writeFileSync(list, files.map(f => "file '" + f.replace(/\\/g, "/") + "'").join("\n"));
const out = path.join(root, "out", name + "-final.mp4");
/* Le mixage voix + bruitages + nappe peut toucher 0 dB : on normalise le volume (−16 LUFS) et on plafonne le pic à −2 dB. */
const r = spawnSync("ffmpeg", ["-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", list, "-c:v", "libx264", "-crf", opt("--crf", "23"), "-preset", "medium", "-af", "loudnorm=I=-16:TP=-2.0:LRA=11", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out], { stdio: "inherit" });
if (r.status !== 0) process.exit(1);
console.log("Terminé : " + out);
