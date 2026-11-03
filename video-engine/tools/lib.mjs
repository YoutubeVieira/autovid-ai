import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
export const FPS = 30;

export function loadProject(name) {
  const file = path.join(root, "projects", name + ".json");
  if (!fs.existsSync(file)) throw new Error("Projet introuvable : " + file);
  return JSON.parse(fs.readFileSync(file, "utf8"));
}

export function loadVoice(id) {
  const all = JSON.parse(fs.readFileSync(path.join(root, "voices.json"), "utf8"));
  const v = all[id];
  if (!v || id.startsWith("_")) throw new Error("Voix inconnue « " + id + " ». Voix disponibles : " + Object.keys(all).filter(k => !k.startsWith("_")).join(", "));
  return v;
}

/* WAV mono 16 bits : en-tête + données PCM */
export function wav(pcm, rate) {
  const h = Buffer.alloc(44);
  h.write("RIFF", 0); h.writeUInt32LE(36 + pcm.length, 4); h.write("WAVEfmt ", 8);
  h.writeUInt32LE(16, 16); h.writeUInt16LE(1, 20); h.writeUInt16LE(1, 22);
  h.writeUInt32LE(rate, 24); h.writeUInt32LE(rate * 2, 28); h.writeUInt16LE(2, 32); h.writeUInt16LE(16, 34);
  h.write("data", 36); h.writeUInt32LE(pcm.length, 40);
  return Buffer.concat([h, pcm]);
}

/* Le service peut répondre en WAV complet ou en PCM brut avec la fréquence dans le type MIME. */
export function decodeAudio(buf, mime) {
  if (buf.length > 44 && buf.toString("ascii", 0, 4) === "RIFF" && buf.toString("ascii", 8, 12) === "WAVE") return readWav(buf);
  const m = /rate=(\d+)/.exec(mime || "");
  return { pcm: buf, rate: m ? Number(m[1]) : 24000 };
}

export function readWav(buf) {
  let pos = 12, rate = 24000, channels = 1, bits = 16, data = null;
  while (pos + 8 <= buf.length) {
    const id = buf.toString("ascii", pos, pos + 4); let size = buf.readUInt32LE(pos + 4);
    if (id === "fmt ") { channels = buf.readUInt16LE(pos + 10); rate = buf.readUInt32LE(pos + 12); bits = buf.readUInt16LE(pos + 22); }
    if (id === "data") { if (pos + 8 + size > buf.length) size = buf.length - pos - 8; data = buf.subarray(pos + 8, pos + 8 + size); break; }
    pos += 8 + size + (size % 2);
  }
  if (!data) throw new Error("WAV sans données audio.");
  if (channels !== 1 || bits !== 16) throw new Error("Il faut du WAV mono 16 bits (reçu " + channels + " canal, " + bits + " bits).");
  return { pcm: data, rate };
}

export const wavSeconds = buf => { const { pcm, rate } = readWav(buf); return pcm.length / 2 / rate; };

/* Découpe un texte en groupes de mots courts pour les sous-titres (style short : 2 à 3 mots) */
export function chunkWords(text, max = 3) {
  const words = text.trim().split(/\s+/).filter(Boolean);
  const out = [];
  let cur = [];
  for (const w of words) {
    cur.push(w);
    const endsSentence = /[.!?…]$/.test(w), endsClause = /[,;:]$/.test(w);
    if (cur.length >= max || endsSentence || (endsClause && cur.length >= 2)) { out.push(cur.join(" ")); cur = []; }
  }
  if (cur.length) out.push(cur.join(" "));
  return out;
}

/* Répartit la durée de la scène entre les groupes, au prorata du nombre de lettres. */
export function chunkTimings(chunks, seconds) {
  const w = chunks.map(c => Math.max(3, c.replace(/[^\p{L}\p{N}]/gu, "").length) + 2);
  const total = w.reduce((a, b) => a + b, 0);
  let t = 0;
  return chunks.map((text, i) => { const from = t; t += (w[i] / total) * seconds; return { text, from: +from.toFixed(3), to: +t.toFixed(3) }; });
}

/* Découpe l'audio d'un chapitre (une seule requête de voix) en une piste par scène.
   On repère les silences, puis, pour chaque frontière, on choisit le silence le plus long
   proche de l'endroit attendu (proportion de lettres cumulées). Renvoie des WAV mono 16 bits. */
export function splitByPauses(buf, texts) {
  const { pcm, rate } = readWav(buf);
  const n = pcm.length / 2, win = Math.round(rate * 0.01), total = n / rate;
  const env = [];
  for (let i = 0; i + win <= n; i += win) { let s = 0; for (let j = 0; j < win; j++) { const v = pcm.readInt16LE((i + j) * 2); s += v * v; } env.push(Math.sqrt(s / win)); }
  const thr = Math.max(...env) * 0.04, sil = [];
  for (let i = 0; i < env.length;) {
    if (env[i] < thr) { let j = i; while (j < env.length && env[j] < thr) j++; const a = i * 0.01, b = j * 0.01; if (b - a >= 0.12 && a > 0.2 && b < total - 0.2) sil.push({ c: (a + b) / 2, d: b - a }); i = j; } else i++;
  }
  // poids de chaque scène : lettres + pauses de ponctuation (. ! ? : ; pèsent plus que la virgule)
  const w = texts.map(t => Math.max(1, t.replace(/[^\p{L}\p{N}]/gu, "").length) + 7 * (t.match(/[.!?…]/g) || []).length + 4 * (t.match(/[:;]/g) || []).length + 2 * (t.match(/,/g) || []).length);
  const sum = w.reduce((x, y) => x + y, 0), N = texts.length;
  const exp = w.map(x => total * x / sum);
  const M = sil.length;
  // programmation dynamique : N-1 coupures parmi les silences ; coût = écart relatif des durées de scène - bonus de pause longue
  const INF = 1e18, best = Array.from({ length: N }, () => new Array(M + 1).fill(INF)), from = Array.from({ length: N }, () => new Array(M + 1).fill(-1));
  const seg = (t0, t1, k) => ((t1 - t0 - exp[k]) / exp[k]) ** 2;
  const bonus = d => 0.35 * Math.min(d, 0.8) / 0.8;
  for (let j = 0; j < M; j++) best[0][j] = seg(0, sil[j].c, 0) - bonus(sil[j].d);
  for (let k = 1; k < N - 1; k++) for (let j = 0; j < M; j++) for (let i = 0; i < j; i++) {
    if (best[k - 1][i] >= INF) continue;
    const c = best[k - 1][i] + seg(sil[i].c, sil[j].c, k) - bonus(sil[j].d);
    if (c < best[k][j]) { best[k][j] = c; from[k][j] = i; }
  }
  const cuts = [];
  if (N > 1 && M >= N - 1) {
    let bj = -1, bc = INF;
    for (let j = 0; j < M; j++) { const c = best[N - 2][j] + seg(sil[j].c, total, N - 1); if (c < bc) { bc = c; bj = j; } }
    for (let k = N - 2, j = bj; k >= 0; k--) { cuts.unshift(sil[j].c); j = from[k][j]; }
  } else { let acc = 0; for (let k = 0; k < N - 1; k++) { acc += exp[k]; cuts.push(acc); } }
  const edges = [0, ...cuts.map(t => Math.round(t * rate)), n];
  return edges.slice(0, -1).map((a, i) => wav(pcm.subarray(a * 2, edges[i + 1] * 2), rate));
}
