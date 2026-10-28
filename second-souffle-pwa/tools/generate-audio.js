#!/usr/bin/env node
/* Génère les fichiers de voix off à partir de docs/voiceover-manifest.csv.
   Aucune dépendance : Node 18 ou plus récent.

   Essai sans clé (vérifie le découpage, les noms de fichiers et les silences) :
     node tools/generate-audio.js --dry-run --lang fr --only w.respiration
   Essai réel d'une phrase par langue :
     node tools/generate-audio.js --test
   Écouter plusieurs voix sur la même phrase (une fois par langue) :
     node tools/generate-audio.js --audition
   Tout produire :
     node tools/generate-audio.js --lang all

   Variables d'environnement (jamais dans le code) :
     GEMINI_API_KEY   clé d'API Google (AI Studio)
     TTS_MODEL        identifiant du modèle de voix (gemini-3.8-flash-lite-tts d'après la page du modèle chez Google)
     VOICE_FR, VOICE_EN, VOICE_PT   nom d'une voix prédéfinie, une par langue
     VOICE_WELLNESS   voix des séances de bien-être (facultatif ; sinon la voix de la langue)
     AUDITION_VOICES  voix à comparer avec --audition, séparées par des virgules
     TTS_STYLE_MODE   none (défaut), metadata ou inline : où placer la consigne de ton
                      none      aucune consigne, le texte seul est envoyé (le plus sûr pour un premier essai)
                      metadata  consigne dans speech_metadata.style de chaque partie (nouveaux modèles)
                      inline    consigne écrite devant le texte (anciens modèles)
     TTS_STYLE_FR, TTS_STYLE_EN, TTS_STYLE_PT   consigne de ton, utilisée si le mode n'est pas none

   Les fichiers sont écrits en WAV dans le dossier --out (audio-out par défaut). Les séances de
   bien-être sont assemblées avec leurs silences. Un fichier déjà produit n'est pas régénéré.
   Cette partie n'a pas été testée avec le vrai service : lancez d'abord --test. */
"use strict";
const fs = require("fs"), path = require("path");

const args = process.argv.slice(2);
const has = f => args.includes(f);
const opt = (f, d) => { const i = args.indexOf(f); return i >= 0 && args[i + 1] ? args[i + 1] : d; };
const DRY = has("--dry-run"), TEST = has("--test"), SELFTEST = has("--selftest"), AUDITION = has("--audition");
const LANG = opt("--lang", TEST ? "all" : null), ONLY = opt("--only", ""), OUT = opt("--out", "audio-out");
if (!LANG && !SELFTEST && !AUDITION) { console.log("Indiquez --lang fr|en|pt|all, ou --test, ou --dry-run. Lisez l'en-tête du fichier."); process.exit(1); }
const LANGS = (LANG === "all" || (!LANG && AUDITION)) ? ["fr", "en", "pt"] : [LANG || "fr"];
const STYLE_MODE = process.env.TTS_STYLE_MODE || "none";
const KEY = process.env.GEMINI_API_KEY, MODEL = process.env.TTS_MODEL;
if (!DRY && !SELFTEST && (!KEY || !MODEL)) { console.log("Il faut GEMINI_API_KEY et TTS_MODEL (ou utilisez --dry-run)."); process.exit(1); }
const VOICE = { fr: process.env.VOICE_FR, en: process.env.VOICE_EN, pt: process.env.VOICE_PT };
const VOICE_WELLNESS = process.env.VOICE_WELLNESS;
const AUDITION_VOICES = (process.env.AUDITION_VOICES || "Achird,Sadaltager,Orus,Charon,Puck,Sulafat,Vindemiatrix,Achernar,Kore,Aoede,Gacrux,Leda").split(",").map(x => x.trim()).filter(Boolean);
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
const csv = SELFTEST ? [] : parseCsv(fs.readFileSync(path.join(__dirname, "..", "docs", "voiceover-manifest.csv"), "utf8"));
if (csv.length) csv.shift();
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

/* Le service peut répondre en WAV complet (en-tête RIFF) ou en PCM brut avec la fréquence dans le type MIME. */
function decodeAudio(buf, mime) {
  if (buf.length > 44 && buf.toString("ascii", 0, 4) === "RIFF" && buf.toString("ascii", 8, 12) === "WAVE") {
    let pos = 12, rate = RATE_DEFAULT, channels = 1, bits = 16, data = null;
    while (pos + 8 <= buf.length) {
      const id = buf.toString("ascii", pos, pos + 4); let size = buf.readUInt32LE(pos + 4);
      if (id === "fmt ") { channels = buf.readUInt16LE(pos + 10); rate = buf.readUInt32LE(pos + 12); bits = buf.readUInt16LE(pos + 22); }
      if (id === "data") { if (pos + 8 + size > buf.length) size = buf.length - pos - 8; data = buf.subarray(pos + 8, pos + 8 + size); break; }
      pos += 8 + size + (size % 2);
    }
    if (!data) throw new Error("WAV sans données audio.");
    if (channels !== 1 || bits !== 16) throw new Error("Format WAV non pris en charge (" + channels + " canal, " + bits + " bits) : il faut du mono 16 bits.");
    return { pcm: data, rate };
  }
  const m = /rate=(\d+)/.exec(mime || "");
  return { pcm: buf, rate: m ? Number(m[1]) : RATE_DEFAULT };
}

/* ---------- service de voix ---------- */
const sleep = ms => new Promise(r => setTimeout(r, ms));
async function synth(item, voiceOverride) {
  if (DRY) return { pcm: tone(Math.max(0.4, item.est - item.pause), RATE_DEFAULT), rate: RATE_DEFAULT };
  const voice = voiceOverride || (item.cat === "bienetre" && VOICE_WELLNESS ? VOICE_WELLNESS : VOICE[item.lang]);
  const speech = voice ? { voiceConfig: { prebuiltVoiceConfig: { voiceName: voice } } } : undefined;
  const part = { text: STYLE_MODE === "inline" ? STYLE[item.lang] + item.text : item.text };
  if (STYLE_MODE === "metadata") part.speech_metadata = { style: STYLE[item.lang] };
  const body = { contents: [{ parts: [part] }], generationConfig: { responseModalities: ["AUDIO"], speechConfig: speech } };
  const url = (process.env.TTS_BASE_URL || "https://generativelanguage.googleapis.com/v1beta") + "/models/" + encodeURIComponent(MODEL) + ":generateContent";
  for (let attempt = 0; attempt < 5; attempt++) {
    const res = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json", "x-goog-api-key": KEY }, body: JSON.stringify(body) });
    if (res.status === 429 || res.status >= 500) { await sleep(2000 * Math.pow(2, attempt)); continue; }
    if (!res.ok) throw new Error("Service de voix : HTTP " + res.status + " " + (await res.text()).slice(0, 300));
    const j = await res.json();
    const parts = (((j.candidates || [])[0] || {}).content || {}).parts;
    const inline = parts && parts.find(p => p.inlineData || p.inline_data);
    if (!inline) throw new Error("Réponse sans audio : " + JSON.stringify(j).slice(0, 300));
    const d = inline.inlineData || inline.inline_data;
    return decodeAudio(Buffer.from(d.data, "base64"), d.mimeType || d.mime_type);
  }
  throw new Error("Service de voix : trop d'échecs, réessayez plus tard.");
}

/* ---------- autotest ---------- */
if (SELFTEST) {
  const assert = require("assert");
  const pcm = tone(0.5, 16000);
  const a = decodeAudio(wav(pcm, 16000), "audio/wav");
  assert.strictEqual(a.rate, 16000); assert.strictEqual(a.pcm.length, pcm.length);
  const b = decodeAudio(pcm, "audio/L16;codec=pcm;rate=22050");
  assert.strictEqual(b.rate, 22050); assert.strictEqual(b.pcm.length, pcm.length);
  assert.strictEqual(parseCsv('a,"b, c",d\n1,"x ""y""",3\n')[1][1], 'x "y"');
  console.log("Autotest réussi : lecture du WAV, du PCM brut et du CSV.");
  process.exit(0);
}

/* ---------- écoute comparée des voix ---------- */
async function audition() {
  const all = parseCsv(fs.readFileSync(path.join(__dirname, "..", "docs", "voiceover-manifest.csv"), "utf8")).slice(1)
    .filter(r => r.length >= 7 && r[1] === "s.intro.standard").map(r => ({ cat: r[0], id: r[1], lang: r[2], text: r[3], pause: 0, est: Number(r[5]) || 3 }));
  console.log((DRY ? "[essai sans service] " : "") + AUDITION_VOICES.length + " voix × " + LANGS.length + " langue(s)");
  for (const it of all.filter(i => LANGS.includes(i.lang))) {
    const dir = path.join(OUT, it.lang); fs.mkdirSync(dir, { recursive: true });
    for (const v of AUDITION_VOICES) {
      const file = path.join(dir, "voix-" + v + ".wav");
      if (fs.existsSync(file) && !DRY) continue;
      try { const r = await synth(it, v); fs.writeFileSync(file, wav(r.pcm, r.rate)); console.log("ok   " + it.lang + " " + v); }
      catch (e) { console.log("échec " + it.lang + " " + v + " : " + e.message.slice(0, 160)); }
    }
  }
  console.log("Écoutez les fichiers voix-*.wav dans " + path.resolve(OUT) + " puis choisissez une voix par langue.");
}
if (AUDITION) { audition().catch(e => { console.log("ÉCHEC : " + e.message); process.exit(1); }); return; }

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
