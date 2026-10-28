#!/usr/bin/env node
/* Génère les fichiers de voix off à partir de docs/voiceover-manifest.csv.
   Aucune dépendance : Node 18 ou plus récent.

   Essai sans clé (vérifie le découpage, les noms de fichiers et les silences) :
     node tools/generate-audio.js --dry-run --lang fr --only w.respiration
   Essai réel d'une phrase par langue :
     node tools/generate-audio.js --test
   Tout produire :
     node tools/generate-audio.js --lang all

   Variables d'environnement (jamais dans le code) :
     GEMINI_API_KEY   clé d'API Google (AI Studio)
     TTS_MODEL        identifiant du modèle de voix, à copier depuis la documentation Google
     VOICE_FR, VOICE_EN, VOICE_PT   nom d'une voix prédéfinie, une par langue
     TTS_STYLE_FR, TTS_STYLE_EN, TTS_STYLE_PT   consigne de ton (facultatif)

   Les fichiers sont écrits en WAV dans le dossier --out (audio-out par défaut). Les séances de
   bien-être sont assemblées avec leurs silences. Un fichier déjà produit n'est pas régénéré.
   Cette partie n'a pas été testée avec le vrai service : lancez d'abord --test. */
"use strict";
const fs = require("fs"), path = require("path");

const args = process.argv.slice(2);
const has = f => args.includes(f);
const opt = (f, d) => { const i = args.indexOf(f); return i >= 0 && args[i + 1] ? args[i + 1] : d; };
const DRY = has("--dry-run"), TEST = has("--test");
const LANG = opt("--lang", TEST ? "all" : null), ONLY = opt("--only", ""), OUT = opt("--out", "audio-out");
if (!LANG) { console.log("Indiquez --lang fr|en|pt|all, ou --test, ou --dry-run. Lisez l'en-tête du fichier."); process.exit(1); }
const LANGS = LANG === "all" ? ["fr", "en", "pt"] : [LANG];
const KEY = process.env.GEMINI_API_KEY, MODEL = process.env.TTS_MODEL;
if (!DRY && (!KEY || !MODEL)) { console.log("Il faut GEMINI_API_KEY et TTS_MODEL (ou utilisez --dry-run)."); process.exit(1); }
const VOICE = { fr: process.env.VOICE_FR, en: process.env.VOICE_EN, pt: process.env.VOICE_PT };
const STYLE = {
  fr: process.env.TTS_STYLE_FR || "Dis ce texte en français, d'un ton chaleureux, calme et encourageant, à un rythme moyen : ",
  en: process.env.TTS_STYLE_EN || "Say this in English, in a warm, calm, encouraging tone, at a medium pace: ",
  pt: process.env.TTS_STYLE_PT || "Diga este texto em português do Brasil, em tom caloroso, calmo e encorajador, em ritmo médio: "
};

/* ---------- CSV ---------- */
function parseCsv(text) {
  const rows = []; let row = [], cur = "", q = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) { if (c === '"' && text[i + 1] === '"') { cur += '"'; i++; } else if (c === '"') q = false; else cur += c; }
    else if (c === '"') q = true;
    else if (c === ",") { row.push(cur); cur = ""; }
    else if (c === "\n") { row.push(cur); rows.push(row); row = []; cur = ""; }
    else if (c !== "\r") cur += c;
  }
  if (cur || row.length) { row.push(cur); rows.push(row); }
  return rows;
}
const csv = parseCsv(fs.readFileSync(path.join(__dirname, "..", "docs", "voiceover-manifest.csv"), "utf8"));
const head = csv.shift();
let items = csv.filter(r => r.length >= 7).map(r => ({ cat: r[0], id: r[1], lang: r[2], text: r[3], pause: Number(r[4]) || 0, est: Number(r[5]) || 1 }));
items = items.filter(i => LANGS.includes(i.lang) && i.id.startsWith(ONLY));
if (TEST) { const seen = {}; items = items.filter(i => (seen[i.lang] ? false : (seen[i.lang] = true))); }

/* ---------- WAV (PCM 16 bits, mono) ---------- */
function wav(pcm, rate) {
  const h = Buffer.alloc(44);
  h.write("RIFF", 0); h.writeUInt32LE(36 + pcm.length, 4); h.write("WAVEfmt ", 8);
  h.writeUInt32LE(16, 16); h.writeUInt16LE(1, 20); h.writeUInt16LE(1, 22);
  h.writeUInt32LE(rate, 24); h.writeUInt32LE(rate * 2, 28); h.writeUInt16LE(2, 32); h.writeUInt16LE(16, 34);
  h.write("data", 36); h.writeUInt32LE(pcm.length, 40);
  return Buffer.concat([h, pcm]);
}
const silence = (sec, rate) => Buffer.alloc(Math.round(sec * rate) * 2);
function tone(sec, rate) {
  const n = Math.round(sec * rate), b = Buffer.alloc(n * 2);
  for (let i = 0; i < n; i++) b.writeInt16LE(Math.round(3000 * Math.sin(2 * Math.PI * 440 * i / rate)), i * 2);
  return b;
}
const RATE_DEFAULT = 24000;

/* ---------- service de voix ---------- */
const sleep = ms => new Promise(r => setTimeout(r, ms));
async function synth(item) {
  if (DRY) return { pcm: tone(Math.max(0.4, item.est - item.pause), RATE_DEFAULT), rate: RATE_DEFAULT };
  const body = {
    contents: [{ parts: [{ text: STYLE[item.lang] + item.text }] }],
    generationConfig: { responseModalities: ["AUDIO"], speechConfig: VOICE[item.lang] ? { voiceConfig: { prebuiltVoiceConfig: { voiceName: VOICE[item.lang] } } } : undefined }
  };
  const url = "https://generativelanguage.googleapis.com/v1beta/models/" + encodeURIComponent(MODEL) + ":generateContent";
  for (let attempt = 0; attempt < 5; attempt++) {
    const res = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json", "x-goog-api-key": KEY }, body: JSON.stringify(body) });
    if (res.status === 429 || res.status >= 500) { await sleep(2000 * Math.pow(2, attempt)); continue; }
    if (!res.ok) throw new Error("Service de voix : HTTP " + res.status + " " + (await res.text()).slice(0, 300));
    const j = await res.json();
    const part = (((j.candidates || [])[0] || {}).content || {}).parts;
    const inline = part && part.find(p => p.inlineData);
    if (!inline) throw new Error("Réponse sans audio : " + JSON.stringify(j).slice(0, 300));
    const m = /rate=(\d+)/.exec(inline.inlineData.mimeType || "");
    return { pcm: Buffer.from(inline.inlineData.data, "base64"), rate: m ? Number(m[1]) : RATE_DEFAULT };
  }
  throw new Error("Service de voix : trop d'échecs, réessayez plus tard.");
}

/* ---------- production ---------- */
(async () => {
  console.log((DRY ? "[essai sans service] " : "") + items.length + " phrases à traiter, langues : " + LANGS.join(", "));
  const segs = {};                       // séances de bien-être à assembler : "lang|id" -> [{n, pcm, rate, pause}]
  let done = 0, skipped = 0;
  for (const it of items) {
    const dir = path.join(OUT, it.lang); fs.mkdirSync(dir, { recursive: true });
    const file = path.join(dir, it.id + ".wav");
    let pcm, rate;
    if (fs.existsSync(file) && !DRY) { const b = fs.readFileSync(file); pcm = b.subarray(44); rate = b.readUInt32LE(24); skipped++; }
    else { ({ pcm, rate } = await synth(it)); fs.writeFileSync(file, wav(pcm, rate)); done++; if (!DRY && done % 10 === 0) console.log(done + " fichiers produits"); }
    if (it.cat === "bienetre") {
      const base = it.id.replace(/\.\d+$/, ""), k = it.lang + "|" + base;
      (segs[k] = segs[k] || []).push({ id: it.id, pcm, rate, pause: it.pause });
    }
  }
  for (const k of Object.keys(segs)) {
    const [lang, base] = k.split("|"), list = segs[k].sort((a, b) => a.id.localeCompare(b.id)), rate = list[0].rate;
    const out = Buffer.concat(list.flatMap(s => [s.pcm, silence(s.pause, rate)]));
    fs.writeFileSync(path.join(OUT, lang, base + ".wav"), wav(out, rate));
    console.log("séance assemblée : " + lang + "/" + base + ".wav (" + (out.length / 2 / rate).toFixed(0) + " s, " + list.length + " phrases)");
  }
  console.log("Terminé : " + done + " produits, " + skipped + " déjà présents. Dossier : " + path.resolve(OUT));
})().catch(e => { console.log("ÉCHEC : " + e.message); process.exit(1); });
