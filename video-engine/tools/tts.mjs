#!/usr/bin/env node
/* Produit la voix off de chaque scène : public/projects/<projet>/audio/<scène>.wav
   et .cache/<projet>.audio.json (durées réelles, utilisées pour caler la vidéo).

   Les voix sont décrites dans voices.json ; le projet choisit la sienne ("voice": "test"), ou VOICE=<id> pour forcer.
   Fournisseurs :
     gemini  voix Google (mêmes modèles et voix que second-souffle-pwa/tools/generate-audio.js).
             Entrée : { "provider": "gemini", "voiceName": "Sulafat", "model": "gemini-3.8-flash-tts" }
             Variable : GEMINI_API_KEY (jamais dans le code)
     espeak  voix locale, sans clé ni réseau (robotique : pour essayer le montage, pas pour publier)
   Un fichier déjà produit pour le même texte, la même voix et le même fournisseur n'est pas régénéré.

   Usage : node tools/tts.mjs <projet> */
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { spawnSync } from "node:child_process";
import { root, loadProject, loadVoice, wav, decodeAudio, readWav } from "./lib.mjs";

const name = process.argv[2];
if (!name) { console.log("Usage : node tools/tts.mjs <projet>"); process.exit(1); }
const project = loadProject(name);
const voiceId = process.env.VOICE || (typeof project.voice === "string" ? project.voice : "test");
const V = loadVoice(voiceId);
const provider = V.provider;
const MODEL = process.env.TTS_MODEL || V.model || "gemini-3.8-flash-tts";
const VOICE = V.voiceName || voiceId;
const LANG = project.lang || "pt-BR";
const MIN_INTERVAL = Number(process.env.TTS_MIN_INTERVAL || 6000);
const sleep = ms => new Promise(r => setTimeout(r, ms));
let last = 0;

async function gemini(text) {
  const key = process.env.GEMINI_API_KEY;
  if (!key) throw new Error("GEMINI_API_KEY manquante (ou TTS_PROVIDER=espeak).");
  const body = { contents: [{ parts: [{ text }] }], generationConfig: { responseModalities: ["AUDIO"], speechConfig: { voiceConfig: { prebuiltVoiceConfig: { voiceName: VOICE } } } } };
  const url = (process.env.TTS_BASE_URL || "https://generativelanguage.googleapis.com/v1beta") + "/models/" + encodeURIComponent(MODEL) + ":generateContent";
  for (let tries = 0; ; tries++) {
    const gap = last + MIN_INTERVAL - Date.now();   // cadence régulière pour rester sous la limite par minute
    if (gap > 0) await sleep(gap);
    last = Date.now();
    const res = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json", "x-goog-api-key": key }, body: JSON.stringify(body) });
    if (res.status === 429 || res.status >= 500) {
      if (tries >= 6) throw new Error("Service de voix : HTTP " + res.status + " répété. Relancez plus tard, les scènes déjà produites sont conservées.");
      const ms = Math.min(120000, 15000 * (tries + 1));
      console.log("  HTTP " + res.status + " : pause de " + ms / 1000 + " s puis reprise");
      await sleep(ms); continue;
    }
    if (!res.ok) throw new Error("Service de voix : HTTP " + res.status + " " + (await res.text()).slice(0, 300));
    const j = await res.json();
    const parts = j.candidates?.[0]?.content?.parts;
    const inline = parts?.find(p => p.inlineData || p.inline_data);
    if (!inline) throw new Error("Réponse sans audio : " + JSON.stringify(j).slice(0, 300));
    const d = inline.inlineData || inline.inline_data;
    const { pcm, rate } = decodeAudio(Buffer.from(d.data, "base64"), d.mimeType || d.mime_type);
    return wav(pcm, rate);
  }
}

function espeak(text) {
  const tmp = path.join(root, ".cache", "espeak-" + process.pid + ".wav");
  fs.mkdirSync(path.dirname(tmp), { recursive: true });
  const voice = LANG.toLowerCase().startsWith("pt") ? "pt-br" : LANG.slice(0, 2).toLowerCase();
  const r = spawnSync("espeak-ng", ["-v", V.espeakVoice || voice, "-s", String(V.speed || 150), "-p", String(V.pitch || 40), "-w", tmp, text]);
  if (r.error || r.status !== 0) throw new Error("espeak-ng introuvable ou en erreur (apt-get install espeak-ng) : " + (r.error?.message || r.stderr));
  const { pcm, rate } = readWav(fs.readFileSync(tmp));
  fs.unlinkSync(tmp);
  return wav(pcm, rate);
}

const outDir = path.join(root, "public/projects", name, "audio");
fs.mkdirSync(outDir, { recursive: true });
fs.mkdirSync(path.join(root, ".cache"), { recursive: true });
const manifest = {};
console.log("Voix off « " + name + " » : voix « " + voiceId + " » (" + provider + (provider === "gemini" ? ", " + MODEL + ", " + VOICE : "") + ")");
for (const s of project.scenes) {
  const hash = crypto.createHash("sha1").update([provider, MODEL, voiceId, JSON.stringify(V), LANG, s.text].join("|")).digest("hex").slice(0, 10);
  const file = path.join(outDir, s.id + "." + hash + ".wav");
  let buf;
  if (fs.existsSync(file)) { buf = fs.readFileSync(file); console.log("  =  " + s.id + " (déjà produit)"); }
  else {
    for (const old of fs.readdirSync(outDir)) if (old.startsWith(s.id + ".")) fs.unlinkSync(path.join(outDir, old));
    buf = provider === "gemini" ? await gemini(s.text) : espeak(s.text);
    fs.writeFileSync(file, buf); console.log("  ok " + s.id);
  }
  const { pcm, rate } = readWav(buf);
  manifest[s.id] = { file: "projects/" + name + "/audio/" + path.basename(file), seconds: +(pcm.length / 2 / rate).toFixed(3), provider };
}
fs.writeFileSync(path.join(root, ".cache", name + ".audio.json"), JSON.stringify(manifest, null, 1));
console.log("Durées écrites dans .cache/" + name + ".audio.json");
