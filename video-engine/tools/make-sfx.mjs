#!/usr/bin/env node
/* Bruitages et nappe sonore synthétisés (aucune dépendance, aucun droit à vérifier) -> public/sfx/*.wav
   whoosh (mouvement de caméra), pop (apparition), impact (coup/explosion), ding (révélation), riser (montée), bed (nappe de tension en boucle).
   Usage : node tools/make-sfx.mjs */
import fs from "node:fs";
import path from "node:path";
import { root, wav } from "./lib.mjs";

const R = 44100;
let seed = 12345;
const rnd = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296) * 2 - 1;
const buf = sec => new Float32Array(Math.round(sec * R));
const TAU = Math.PI * 2;

/* filtre à variables d'état (passe-bande) */
function svf(x, freqAt, q) {
  const y = new Float32Array(x.length); let lo = 0, bp = 0;
  for (let i = 0; i < x.length; i++) {
    const f = 2 * Math.sin(Math.PI * Math.min(0.45, freqAt(i / R) / R));
    const hi = x[i] - lo - bp / q;
    bp += f * hi; lo += f * bp; y[i] = bp;
  }
  return y;
}
const norm = (x, peak = 0.9) => { let m = 1e-9; for (const v of x) m = Math.max(m, Math.abs(v)); return x.map(v => v / m * peak); };
const fade = (x, a = 0.004, b = 0.02) => { const A = a * R, B = b * R; return x.map((v, i) => v * Math.min(1, i / A, (x.length - i) / B)); };
const pcm = x => { const b = Buffer.alloc(x.length * 2); for (let i = 0; i < x.length; i++) b.writeInt16LE(Math.round(Math.max(-1, Math.min(1, x[i])) * 32767), i * 2); return b; };

function whoosh() {
  const n = buf(0.7), noise = n.map(() => rnd());
  const y = svf(noise, t => 250 * Math.pow(16, Math.min(1, t / 0.55)), 1.4);
  return fade(norm(y.map((v, i) => v * Math.pow(Math.sin(Math.PI * Math.min(1, i / n.length)), 2))), 0.02, 0.05);
}
function pop() {
  const n = buf(0.2);
  return fade(norm(n.map((_, i) => { const t = i / R, ph = TAU * (260 * t + (1500 * (1 - Math.exp(-t * 28))) / 28 * 1); return Math.sin(ph) * Math.exp(-t * 22) + 0.25 * rnd() * Math.exp(-t * 250); })), 0.0008, 0.03);
}
function impact() {
  const n = buf(1.5), noise = svf(n.map(() => rnd()), t => 180 + 2000 * Math.exp(-t * 6), 0.8);
  return fade(norm(n.map((_, i) => { const t = i / R; const s = Math.sin(TAU * (34 * t + 70 * (1 - Math.exp(-t * 9)) / 9)) * Math.exp(-t * 3.2); return Math.tanh(2.2 * (s + 0.9 * noise[i] * Math.exp(-t * 9))); })), 0.0005, 0.12);
}
function ding() {
  const n = buf(1.1);
  return fade(norm(n.map((_, i) => { const t = i / R; return (Math.sin(TAU * 1318.5 * t) + 0.6 * Math.sin(TAU * 1975.5 * t) + 0.25 * Math.sin(TAU * 2637 * t)) * Math.exp(-t * 4.2); })), 0.001, 0.1);
}
function riser() {
  const n = buf(1.8), noise = svf(n.map(() => rnd()), t => 200 * Math.pow(30, Math.min(1, t / 1.7)), 2.2);
  return fade(norm(n.map((_, i) => { const t = i / R, k = t / 1.8; return (noise[i] * 0.8 + 0.4 * Math.sin(TAU * (180 * t + 450 * t * t))) * k * k; })), 0.01, 0.03);
}
function bed() {                       // 24 s, bouclable : toutes les périodes divisent 24 s
  const D = 24, n = buf(D);
  return n.map((_, i) => {
    const t = i / R;
    const drone = Math.sin(TAU * 55 * t) * 0.5 + Math.sin(TAU * 55.35 * t) * 0.35 + Math.sin(TAU * 82.41 * t) * 0.25 + Math.sin(TAU * 110.4 * t) * 0.15 * (0.5 + 0.5 * Math.sin(TAU * t / 8));
    const swell = 0.6 + 0.4 * Math.sin(TAU * t / 12);
    const beat = Math.sin(TAU * 48 * (t % 1)) * Math.exp(-(t % 1) * 9) * 0.55 + Math.sin(TAU * 40 * ((t + 0.25) % 1)) * Math.exp(-((t + 0.25) % 1) * 12) * 0.25;
    return drone * swell * 0.55 + beat;
  });
}

const out = path.join(root, "public/sfx");
fs.mkdirSync(out, { recursive: true });
const all = { whoosh: whoosh(), pop: pop(), impact: impact(), ding: ding(), riser: riser(), bed: norm(bed(), 0.8) };
for (const [k, x] of Object.entries(all)) { fs.writeFileSync(path.join(out, k + ".wav"), wav(pcm(x), R)); console.log(k + ".wav " + (x.length / R).toFixed(2) + " s"); }
