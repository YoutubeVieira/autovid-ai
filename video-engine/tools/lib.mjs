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
