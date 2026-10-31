#!/usr/bin/env node
/* Analyse une vidéo de référence : fiche technique, changements de plan, volume, planche d'images clés.
   Sortie : .cache/analyse/<nom>/{info.json, planche.png, couverture.png?}
   Usage : node tools/analyze-video.mjs <fichier.mp4> [--every 6]   (une image toutes les N secondes, 6 par défaut)
   Ensuite, REGARDER la planche (outil Read sur planche.png) : l'outil mesure, il ne juge pas le style. */
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { root } from "./lib.mjs";

const file = process.argv[2];
if (!file || !fs.existsSync(file)) { console.log("Usage : node tools/analyze-video.mjs <fichier.mp4> [--every 6]"); process.exit(1); }
const ei = process.argv.indexOf("--every"), every = ei > 0 ? Number(process.argv[ei + 1]) : 6;
const name = path.basename(file).replace(/\.[^.]+$/, "").replace(/[^\w.-]+/g, "_").slice(0, 60);
const out = path.join(root, ".cache", "analyse", name);
fs.mkdirSync(out, { recursive: true });
const run = (cmd, args) => spawnSync(cmd, args, { encoding: "utf8", maxBuffer: 1 << 26 });

const probe = JSON.parse(run("ffprobe", ["-v", "error", "-print_format", "json", "-show_format", "-show_streams", file]).stdout || "{}");
const v = (probe.streams || []).find(s => s.codec_type === "video" && s.disposition?.attached_pic !== 1) || {};
const hasAudio = (probe.streams || []).some(s => s.codec_type === "audio");
const hasCover = (probe.streams || []).some(s => s.disposition?.attached_pic === 1);
const duration = Number(probe.format?.duration || 0);

const cuts = [];
const sc = run("ffmpeg", ["-v", "info", "-i", file, "-an", "-vf", "select='gt(scene,0.35)',showinfo", "-f", "null", "-"]).stderr || "";
for (const m of sc.matchAll(/pts_time:([\d.]+)/g)) cuts.push(+Number(m[1]).toFixed(2));

let loudness = null;
if (hasAudio) {
  const a = run("ffmpeg", ["-i", file, "-af", "volumedetect", "-vn", "-f", "null", "-"]).stderr || "";
  loudness = { mean_db: Number(/mean_volume: (-?[\d.]+)/.exec(a)?.[1]), max_db: Number(/max_volume: (-?[\d.]+)/.exec(a)?.[1]) };
}

const n = Math.max(1, Math.floor(duration / every));
const cols = Math.min(5, n), rows = Math.ceil(n / cols);
run("ffmpeg", ["-v", "error", "-y", "-i", file, "-map", "0:v:0", "-vf", `fps=1/${every},scale=240:-1,tile=${cols}x${rows}`, "-frames:v", "1", path.join(out, "planche.png")]);
if (hasCover) run("ffmpeg", ["-v", "error", "-y", "-i", file, "-an", "-map", "0:v:1", "-frames:v", "1", path.join(out, "couverture.png")]);

const info = {
  fichier: path.basename(file), duree_s: +duration.toFixed(1), largeur: v.width, hauteur: v.height,
  format: v.width && v.height ? (v.height > v.width ? "vertical 9:16 (short)" : "horizontal 16:9") : "inconnu",
  fps: v.r_frame_rate, audio: hasAudio, loudness, couverture_integree: hasCover,
  changements_de_plan: cuts.length, instants_changements_s: cuts.slice(0, 60),
  lecture: cuts.length === 0 ? "aucune coupe détectée : plan continu (animation sur fond fixe, motion design)" : cuts.length / duration > 0.25 ? "montage nerveux (plus d'une coupe toutes les 4 s)" : "montage posé",
  images_par_planche: n, intervalle_s: every
};
fs.writeFileSync(path.join(out, "info.json"), JSON.stringify(info, null, 1));
console.log(JSON.stringify(info, null, 1));
console.log("Planche : " + path.join(out, "planche.png") + " (à regarder avec Read)");
