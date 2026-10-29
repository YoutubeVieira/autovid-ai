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
   Chaque phrase est produite deux fois : une voix de femme (dossier f) et une voix d'homme (dossier m).
   Pour n'en produire qu'une : --gender f   ou   --gender m.

   Variables d'environnement (jamais dans le code) :
     GEMINI_API_KEY   clé d'API Google (AI Studio)
     TTS_MODEL        identifiant du modèle de voix (gemini-3.8-flash-tts pour la qualité maximale, gemini-3.8-flash-lite-tts pour l économie)
     VOICE_F, VOICE_M   voix de femme et voix d'homme (Sulafat et Achird par défaut), les mêmes dans les trois langues
     TTS_MODEL          modèle de voix (gemini-3.8-flash-tts par défaut)
     VOICE_FR_F, VOICE_FR_M, VOICE_EN_F, VOICE_EN_M, VOICE_PT_F, VOICE_PT_M   voix propres à une langue (facultatif)
     VOICE_WELLNESS_F, VOICE_WELLNESS_M   voix des séances de bien-être (Vindemiatrix et Charon par défaut)
     AUDITION_VOICES  voix à comparer avec --audition, séparées par des virgules
     AUDITION_MODELS  modèles à comparer avec --audition (par défaut gemini-3.8-flash-tts et gemini-3.8-flash-lite-tts)
     TTS_STYLE_MODE   none (défaut), metadata ou inline : où placer la consigne de ton
                      none      aucune consigne, le texte seul est envoyé (le plus sûr pour un premier essai)
                      metadata  consigne dans speech_metadata.style de chaque partie (nouveaux modèles)
                      inline    consigne écrite devant le texte (anciens modèles)
     TTS_STYLE_FR, TTS_STYLE_EN, TTS_STYLE_PT   consigne de ton, utilisée si le mode n'est pas none

   Quotas : le script ne force jamais. Une demande toutes les 6 secondes (TTS_MIN_INTERVAL). Si Google répond
   « quota atteint », il attend (jusqu'à minuit heure du Pacifique pour le quota du jour) puis reprend seul.
   Si vous l'arrêtez (Ctrl+C), relancez la même commande : les fichiers déjà produits sont conservés.

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
const KEY = process.env.GEMINI_API_KEY, MODEL = process.env.TTS_MODEL || "gemini-3.8-flash-tts";
if (!DRY && !SELFTEST && !KEY) { console.log("Il faut la variable GEMINI_API_KEY (ou utilisez --dry-run)."); process.exit(1); }
const { adapt } = require("./audio-fixes.js");
const GENDER = opt("--gender", "both");
const GENDERS = GENDER === "f" ? ["f"] : GENDER === "m" ? ["m"] : ["f", "m"];
const VOICE_DEFAULT = { f: "Sulafat", m: "Achird" };          // coach, séances, motivation
const VOICE_WELLNESS_DEFAULT = { f: "Vindemiatrix", m: "Charon" }; // séances de bien-être : plus douces
function voiceFor(item, g) {
  const L = item.lang.toUpperCase(), G = g.toUpperCase();
  const well = item.cat === "bienetre" ? (process.env["VOICE_WELLNESS_" + G] || VOICE_WELLNESS_DEFAULT[g]) : null;
  return well || process.env["VOICE_" + L + "_" + G] || process.env["VOICE_" + G] || VOICE_DEFAULT[g];
}
const AUDITION_MODELS = (process.env.AUDITION_MODELS || "gemini-3.8-flash-tts,gemini-3.8-flash-lite-tts").split(",").map(x => x.trim()).filter(Boolean);
const AUDITION_VOICES = (process.env.AUDITION_VOICES || "Achird,Sadaltager,Orus,Charon,Sulafat,Vindemiatrix,Achernar,Aoede").split(",").map(x => x.trim()).filter(Boolean);
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
const MIN_INTERVAL = (process.env.TTS_MIN_INTERVAL === undefined ? 6 : Number(process.env.TTS_MIN_INTERVAL)) * 1000;  // secondes entre deux demandes
const MIN_WAIT = (process.env.TTS_MIN_WAIT === undefined ? 60 : Number(process.env.TTS_MIN_WAIT)) * 1000;              // pause minimale après un refus de quota
let lastCall = 0, waitStep = 0;
const hhmm = t => new Date(t).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
const dur = ms => ms >= 3600000 ? Math.floor(ms / 3600000) + " h " + Math.round((ms % 3600000) / 60000) + " min" : ms >= 60000 ? Math.round(ms / 60000) + " min" : Math.round(ms / 1000) + " s";

/* Le quota par jour de Google se renouvelle à minuit, heure du Pacifique. */
function untilPacificMidnight(now) {
  const f = new Intl.DateTimeFormat("en-US", { timeZone: "America/Los_Angeles", hour12: false, hour: "numeric", minute: "numeric", second: "numeric" }).formatToParts(new Date(now));
  const g = t => Number((f.find(p => p.type === t) || {}).value) % 24;
  return ((24 - g("hour")) * 3600 - g("minute") * 60 - g("second")) * 1000;
}

/* Lit le refus de quota : délai demandé par Google, quota du jour ou de la minute, quota nul. */
function readQuota(status, headers, text) {
  const q = { zero: false, perDay: false, waitMs: 0 };
  if (/limit:\s*0\b/.test(text)) q.zero = true;
  if (/PerDay|per day|daily/i.test(text)) q.perDay = true;
  const m = /"retryDelay"\s*:\s*"(\d+(?:\.\d+)?)s"/.exec(text) || /retry in (\d+(?:\.\d+)?)s/i.exec(text);
  if (m) q.waitMs = Number(m[1]) * 1000;
  const ra = Number(headers.get && headers.get("retry-after"));
  if (ra > 0) q.waitMs = Math.max(q.waitMs, ra * 1000);
  return q;
}

async function synth(item, voice, model) {
  if (DRY) return { pcm: tone(Math.max(0.4, item.est - item.pause), RATE_DEFAULT), rate: RATE_DEFAULT };
  const speech = voice ? { voiceConfig: { prebuiltVoiceConfig: { voiceName: voice } } } : undefined;
  const part = { text: STYLE_MODE === "inline" ? STYLE[item.lang] + item.text : item.text };
  if (STYLE_MODE === "metadata") part.speech_metadata = { style: STYLE[item.lang] };
  const body = { contents: [{ parts: [part] }], generationConfig: { responseModalities: ["AUDIO"], speechConfig: speech } };
  const url = (process.env.TTS_BASE_URL || "https://generativelanguage.googleapis.com/v1beta") + "/models/" + encodeURIComponent(model || MODEL) + ":generateContent";
  let failures = 0;
  for (;;) {
    const gap = lastCall + MIN_INTERVAL - Date.now();      // cadence régulière : on reste sous la limite par minute
    if (gap > 0) await sleep(gap);
    lastCall = Date.now();
    const res = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json", "x-goog-api-key": KEY }, body: JSON.stringify(body) });
    if (res.status === 429) {
      const text = await res.text(), q = readQuota(res.status, res.headers, text);
      if (q.zero) throw new Error("Cette clé n'a aucun quota pour ce modèle (limite 0). Essayez TTS_MODEL=gemini-3.8-flash-lite-tts ou une autre clé. " + text.slice(0, 200));
      let ms;
      if (q.perDay) ms = untilPacificMidnight(Date.now()) + 120000;
      else { waitStep = Math.min(waitStep + 1, 6); ms = Math.max(q.waitMs + 5000, MIN_WAIT * waitStep); }
      console.log("Quota atteint (" + (q.perDay ? "limite du jour" : "limite par minute") + "). Pause de " + dur(ms) + ", reprise vers " + hhmm(Date.now() + ms) + ". Laissez la fenêtre ouverte, ne l'éteignez pas.");
      await sleep(ms);
      continue;                                               // un refus de quota n'est jamais un échec : on attend, puis on reprend
    }
    if (res.status >= 500) {
      if (++failures >= 6) throw new Error("Service de voix : erreurs répétées (HTTP " + res.status + "). Relancez plus tard, les fichiers déjà produits sont conservés.");
      await sleep(Math.min(60000, 2000 * Math.pow(2, failures)));
      continue;
    }
    if (!res.ok) throw new Error("Service de voix : HTTP " + res.status + " " + (await res.text()).slice(0, 300));
    waitStep = 0;
    const j = await res.json();
    const parts = (((j.candidates || [])[0] || {}).content || {}).parts;
    const inline = parts && parts.find(p => p.inlineData || p.inline_data);
    if (!inline) throw new Error("Réponse sans audio : " + JSON.stringify(j).slice(0, 300));
    const d = inline.inlineData || inline.inline_data;
    return decodeAudio(Buffer.from(d.data, "base64"), d.mimeType || d.mime_type);
  }
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
  console.log((DRY ? "[essai sans service] " : "") + AUDITION_VOICES.length + " voix × " + AUDITION_MODELS.length + " modèle(s) × " + LANGS.length + " langue(s)");
  const short = m => /lite/i.test(m) ? "lite" : /flash/i.test(m) ? "flash" : m.replace(/[^a-z0-9.-]/gi, "");
  for (const it of all.filter(i => LANGS.includes(i.lang))) {
    const dir = path.join(OUT, it.lang); fs.mkdirSync(dir, { recursive: true });
    for (const m of AUDITION_MODELS) for (const v of AUDITION_VOICES) {
      const file = path.join(dir, "voix-" + v + "-" + short(m) + ".wav");
      if (fs.existsSync(file) && !DRY) continue;
      try { const r = await synth(it, v, m); fs.writeFileSync(file, wav(r.pcm, r.rate)); console.log("ok   " + it.lang + " " + v + " " + short(m)); }
      catch (e) { console.log("échec " + it.lang + " " + v + " " + short(m) + " : " + e.message.slice(0, 160)); }
    }
  }
  console.log("Écoutez les fichiers voix-*.wav dans " + path.resolve(OUT) + " puis choisissez une voix et un modèle.");
}
if (AUDITION) { audition().catch(e => { console.log("ÉCHEC : " + e.message); process.exit(1); }); return; }

/* ---------- production ---------- */
(async () => {
  console.log((DRY ? "[essai sans service] " : "") + items.length + " phrases × " + GENDERS.length + " voix, langues : " + LANGS.join(", "));
  const segs = {};                       // séances de bien-être à assembler : "lang|genre|id" -> [{id, pcm, rate, pause}]
  let done = 0, skipped = 0;
  for (const g of GENDERS) {
    for (const base of items) {
      const it = Object.assign({}, base, { text: adapt(base.text, base.lang, g) });
      const dir = path.join(OUT, it.lang, g); fs.mkdirSync(dir, { recursive: true });
      const file = path.join(dir, it.id + ".wav");
      let pcm, rate;
      if (fs.existsSync(file) && !DRY) { const b = fs.readFileSync(file); pcm = b.subarray(44); rate = b.readUInt32LE(24); skipped++; }
      else { ({ pcm, rate } = await synth(it, voiceFor(it, g))); fs.writeFileSync(file, wav(pcm, rate)); done++; if (!DRY && done % 10 === 0) console.log(done + " fichiers produits"); }
      if (it.cat === "bienetre") {
        const k = it.lang + "|" + g + "|" + it.id.replace(/\.\d+$/, "");
        (segs[k] = segs[k] || []).push({ id: it.id, pcm, rate, pause: it.pause });
      }
    }
  }
  for (const k of Object.keys(segs)) {
    const [lang, g, base] = k.split("|"), list = segs[k].sort((a, b) => a.id.localeCompare(b.id)), rate = list[0].rate;
    const out = Buffer.concat(list.flatMap(s => [s.pcm, silence(s.pause, rate)]));
    fs.writeFileSync(path.join(OUT, lang, g, base + ".wav"), wav(out, rate));
    console.log("séance assemblée : " + lang + "/" + g + "/" + base + ".wav (" + (out.length / 2 / rate).toFixed(0) + " s, " + list.length + " phrases)");
  }
  console.log("Terminé : " + done + " produits, " + skipped + " déjà présents. Dossier : " + path.resolve(OUT));
})().catch(e => { console.log("ÉCHEC : " + e.message); process.exit(1); });
