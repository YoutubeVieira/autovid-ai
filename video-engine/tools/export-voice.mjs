#!/usr/bin/env node
/* Exporte la voix off d'un projet en MP3 (voix seule, calée sur la durée des scènes) : out/audio/<projet>-voix.mp3
   Usage : node tools/export-voice.mjs <projet> [--bitrate 128k] */
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { root, FPS } from "./lib.mjs";

const name = process.argv[2];
if (!name) { console.log("Usage : node tools/export-voice.mjs <projet> [--bitrate 128k]"); process.exit(1); }
const bi = process.argv.indexOf("--bitrate"), br = bi > 0 ? process.argv[bi + 1] : "128k";
const pf = path.join(root, ".cache", name + ".props.json");
if (!fs.existsSync(pf)) { console.log("Lancez d'abord : node tools/build-props.mjs " + name); process.exit(1); }
const scenes = JSON.parse(fs.readFileSync(pf, "utf8")).scenes.filter(s => s.audio);
if (!scenes.length) { console.log("Aucun audio dans ce projet."); process.exit(1); }
const inputs = scenes.flatMap(s => ["-i", path.join(root, "public", s.audio)]);
const chains = scenes.map((s, i) => `[${i}:a]aresample=44100,aformat=channel_layouts=mono,apad=whole_dur=${(s.durationInFrames / FPS).toFixed(3)}[a${i}]`).join(";");
const concat = scenes.map((_, i) => `[a${i}]`).join("") + `concat=n=${scenes.length}:v=0:a=1[out]`;
fs.mkdirSync(path.join(root, "out", "audio"), { recursive: true });
const out = path.join(root, "out", "audio", name + "-voix.mp3");
const r = spawnSync("ffmpeg", ["-v", "error", "-y", ...inputs, "-filter_complex", chains + ";" + concat, "-map", "[out]", "-c:a", "libmp3lame", "-b:a", br, out], { stdio: "inherit" });
if (r.status !== 0) process.exit(1);
console.log(name + " : " + out + " (" + (fs.statSync(out).size / 1e6).toFixed(1) + " Mo)");
