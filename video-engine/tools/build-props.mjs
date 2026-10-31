#!/usr/bin/env node
/* Assemble projects/<projet>.json + durées audio -> .cache/<projet>.props.json (paramètres de rendu Remotion).
   Chaque scène dure : durée de la voix + respiration (project.pad, 0,35 s par défaut) ; sans voix : s.seconds.
   Usage : node tools/build-props.mjs <projet> [--max <secondes>] (--max coupe la vidéo : prototype) */
import fs from "node:fs";
import path from "node:path";
import { root, FPS, loadProject, chunkWords, chunkTimings } from "./lib.mjs";

const name = process.argv[2];
if (!name) { console.log("Usage : node tools/build-props.mjs <projet> [--max s]"); process.exit(1); }
const mi = process.argv.indexOf("--max");
const maxSec = mi > 0 ? Number(process.argv[mi + 1]) : Infinity;
const project = loadProject(name);
const audioFile = path.join(root, ".cache", name + ".audio.json");
const audio = fs.existsSync(audioFile) ? JSON.parse(fs.readFileSync(audioFile, "utf8")) : {};
const pad = project.pad ?? 0.35;

let t = 0;
const scenes = [];
for (const s of project.scenes) {
  const a = audio[s.id];
  const seconds = a ? a.seconds + pad : (s.seconds ?? 3);
  if (t >= maxSec) break;
  const frames = Math.max(1, Math.round(seconds * FPS));
  scenes.push({
    ...s,
    audio: a?.file,
    durationInFrames: frames,
    subtitles: chunkTimings(chunkWords(s.text, project.subtitleWords || 3), a ? a.seconds : seconds - 0.2)
  });
  t += seconds;
}
const props = { title: project.title, brand: project.brand, scenes, bg: project.bg };
fs.mkdirSync(path.join(root, ".cache"), { recursive: true });
const out = path.join(root, ".cache", name + ".props.json");
fs.writeFileSync(out, JSON.stringify(props, null, 1));
console.log(scenes.length + " scènes, " + (scenes.reduce((n, s) => n + s.durationInFrames, 0) / FPS).toFixed(1) + " s -> " + out);
