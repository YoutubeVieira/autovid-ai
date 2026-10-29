#!/usr/bin/env node
/* Vérifie, sans rien produire, que votre clé d'API Google accepte les modèles de voix.
   Affiche un résumé que vous pouvez copier dans la conversation : la clé n'y figure jamais.
   Utilisation : définir GEMINI_API_KEY, puis  node tools/verifier-cle.js */
"use strict";
const KEY = process.env.GEMINI_API_KEY;
const BASE = process.env.TTS_BASE_URL || "https://generativelanguage.googleapis.com/v1beta";
const MODELS = (process.env.CHECK_MODELS || "gemini-3.8-flash-tts,gemini-3.8-flash-lite-tts").split(",").map(s => s.trim()).filter(Boolean);
if (!KEY) { console.log("Il faut la variable GEMINI_API_KEY."); process.exit(1); }
const clean = s => String(s).split(KEY).join("[clé masquée]").replace(/\s+/g, " ").slice(0, 260);
const verdict = status => status === 200 ? "OK" : status === 400 ? "requête refusée (forme de la requête ou clé mal formée)" : status === 401 || status === 403 ? "clé refusée ou accès non autorisé à ce modèle" :
  status === 404 ? "modèle introuvable pour cette clé" : status === 429 ? "limite de demandes atteinte (niveau gratuit ou quota)" : "erreur " + status;

async function call(url, init) {
  try { const r = await fetch(url, Object.assign({ headers: { "x-goog-api-key": KEY, "Content-Type": "application/json" } }, init)); const t = await r.text(); return { status: r.status, text: t }; }
  catch (e) { return { status: 0, text: String(e.message || e) }; }
}

(async () => {
  console.log("Vérification de la clé (aucun fichier n'est produit)...\n");
  const list = await call(BASE + "/models?pageSize=200");
  if (list.status === 0) { console.log("1. Connexion à Google : IMPOSSIBLE — " + clean(list.text)); process.exit(1); }
  console.log("1. Clé reconnue par Google : " + (list.status === 200 ? "oui" : "NON — " + verdict(list.status) + " — " + clean(list.text)));
  let names = [];
  if (list.status === 200) { try { names = (JSON.parse(list.text).models || []).map(m => String(m.name).replace(/^models\//, "")); } catch (e) { /* ignoré */ } }
  const tts = names.filter(n => /tts/i.test(n));
  console.log("2. Modèles de voix visibles avec cette clé : " + (tts.length ? tts.join(", ") : "aucun"));
  for (const m of MODELS) console.log("   - " + m + " : " + (names.includes(m) ? "listé" : "non listé"));
  console.log("");
  for (const m of MODELS) {
    const body = { contents: [{ parts: [{ text: "Bonjour." }] }], generationConfig: { responseModalities: ["AUDIO"], speechConfig: { voiceConfig: { prebuiltVoiceConfig: { voiceName: "Sulafat" } } } } };
    const r = await call(BASE + "/models/" + encodeURIComponent(m) + ":generateContent", { method: "POST", body: JSON.stringify(body) });
    let detail = "";
    if (r.status === 200) { try { const p = ((JSON.parse(r.text).candidates || [])[0] || {}).content.parts.find(x => x.inlineData || x.inline_data); detail = p ? " (audio reçu)" : " (réponse sans audio)"; } catch (e) { detail = " (réponse illisible)"; } }
    else { try { detail = " — " + clean(JSON.parse(r.text).error.message); } catch (e) { detail = " — " + clean(r.text); } }
    console.log("3. Essai d'un mot avec " + m + " : " + verdict(r.status) + detail);
  }
  console.log("\nCopiez ce résumé dans la conversation. Ne copiez jamais la clé.");
})();
