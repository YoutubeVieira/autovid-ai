/* Parcours Studio et Voix dans un navigateur, avec une fausse IA et une voix de test : node tests/smoke-studio.mjs
   Option : SCREENS=dossier pour enregistrer des captures d'écran. */
import assert from "node:assert/strict";
import path from "node:path";
import { mkdtemp } from "node:fs/promises";
import { tmpdir } from "node:os";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";
import { run } from "../lib/render.mjs";

process.env.IMAGES = "aucun";
process.env.TRANSCRIPTION = "0";
const { createServer } = await import("../server.mjs");
const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const here = path.dirname(fileURLToPath(import.meta.url));
const SCREENS = process.env.SCREENS;

const VERSION = {
  titre: "La patience de la roda", legende: "La capoeira m'a appris à attendre mon tour.", hashtags: ["capoeira", "patience"],
  ambiance_musique: "berimbau doux", pourquoi_mieux: "Accroche personnelle dès la première seconde.",
  scenes: [
    { haut: "Dans la roda, celui qui se précipite tombe.", bas: "La capoeira m'a appris la patience.", voix: "Dans la roda, celui qui se précipite tombe.", prompt_image: "", duree: 3 },
    { haut: "Attendre son moment, c'est déjà jouer.", bas: "Et toi, tu sais attendre ?", voix: "Attendre son moment, c'est déjà jouer.", prompt_image: "", duree: 3 }
  ]
};
const STYLE = {
  gabarit: "face_camera", description: "Sous-titres blancs contour noir, titres en boîte noire bordée d'orange.",
  citation: { couleur: "#FFFFFF", taille: 54, zoom: "in", style_image: "3D" },
  face_camera: { taille: 100, couleur_texte: "#FFFFFF", couleur_mot_actif: "#FFD400", couleur_contour: "#000000", epaisseur_contour: 8, position_sous_titres: 0.62, mots_par_groupe: 2, majuscules: false, titre_couleur_texte: "#FFFFFF", titre_couleur_boite: "#000000", titre_couleur_bordure: "#F28C28", titre_position: 0.14 }
};
const calls = [];
const THEMES = { themes: [{ theme: "Défi ginga 7 jours", pourquoi_maintenant: "Vidéos du défi en hausse cette semaine", accroches: ["J'ai fait la ginga 7 jours de suite", "b", "c"], format: "défi", potentiel: 81, concurrence: "faible", sources: ["https://exemple.fr/a"] }] };
const client = { beta: { messages: {
 async create() { return { stop_reason: "end_turn", content: [{ type: "text", text: "Signal : défi ginga" }] }; },
 async parse(p) {
  calls.push(p);
  const t = JSON.stringify(p.messages[0].content);
  const out = /reference screenshots/.test(t) ? STYLE : /short-video themes/.test(t) ? THEMES : VERSION;
  return { stop_reason: "end_turn", parsed_output: out };
} } } };

const dataDir = await mkdtemp(path.join(tmpdir(), "smoke-data-"));
const srv = createServer({ client, dataDir, env: { VOIX_MOTEURS: "kokoro,test", PRIX_AFFICHE: "1,99 €" } }).listen(0);
await new Promise((r) => srv.once("listening", r));
const base = `http://127.0.0.1:${srv.address().port}/`;
const browser = await chromium.launch();
const errors = [];
try {
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("console", (m) => { if (m.type() === "error" && !/status of (4|5)\d\d/.test(m.text())) errors.push(m.text()); });
  const shot = async (n) => SCREENS && page.screenshot({ path: path.join(SCREENS, n + ".png"), fullPage: true });
  await page.goto(base);

  /* Radar de tendances (onglet Idées) */
  await page.waitForSelector("#rd-add");
  await page.fill(".rd-nom", "capoeira débutants");
  await page.click("#rd-go");
  await page.waitForSelector(".theme", { timeout: 30_000 });
  assert.match(await page.textContent(".theme"), /Défi ginga 7 jours/);
  await shot("9-radar");
  await page.click(".rd-film");
  await page.waitForSelector("#sujet");
  assert.match(await page.inputValue("#sujet"), /Défi ginga 7 jours/);

  /* Studio, à partir d'un sujet */
  await page.check('input[name=mode][value=sujet]');
  await page.fill("#sujet", "ce que la capoeira m'a appris");
  await page.click("#f-studio button[type=submit]");
  await page.waitForSelector("#sc-h-1");
  assert.equal(await page.inputValue("#sc-h-0"), VERSION.scenes[0].haut);
  await page.fill("#sc-b-1", "Et toi, tu sais attendre ton tour ?");
  await page.selectOption("#st-moteur", "test");
  await shot("6-studio-version");
  await page.click("#btn-fab");
  await page.waitForSelector("video.result", { timeout: 120_000 });
  const dur = await page.$eval("video.result", (v) => new Promise((r) => (v.readyState >= 1 ? r(v.duration) : v.addEventListener("loadedmetadata", () => r(v.duration)))));
  assert.ok(dur > 5 && dur < 8, "durée " + dur);
  assert.equal(await page.locator("a[download='voix-off.mp3']").count(), 1);
  await shot("7-studio-video");

  /* Style à partir d'une image de référence */
  const ref = path.join(dataDir, "ref.png");
  await run("ffmpeg", ["-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc2=s=540x960", "-frames:v", "1", ref]);
  await page.click("#ref-style summary");
  await page.setInputFiles("#ref-img", ref);
  await page.waitForSelector("#ref-res .swatch");
  assert.equal(await page.isChecked('input[name=mode][value=face]'), true);
  assert.equal(calls.at(-1).messages[0].content[0].type, "image");

  /* Face caméra : sans faster-whisper sur le serveur, un message clair s'affiche */
  await page.setInputFiles("#face-file", path.join(here, "fixtures/court.webm"));
  await page.click("#f-studio button[type=submit]");
  await page.waitForSelector("#r-studio .err", { timeout: 60_000 });
  assert.match(await page.textContent("#r-studio .err"), /faster-whisper|Transcription/);

  /* Clips : sans faster-whisper, message clair */
  await page.check('input[name=mode][value=clips]');
  await page.setInputFiles("#clips-file", path.join(here, "fixtures/court.webm"));
  await page.click("#f-studio button[type=submit]");
  await page.waitForSelector("#r-studio .err", { timeout: 60_000 });

  /* Voix : essai, et formulaire de clonage absent quand le serveur n'a pas de moteur de clonage */
  await page.click(".tabs [data-vue=voix]");
  await page.waitForSelector("#vx-go");
  await page.selectOption("#vx-moteur", "test");
  await page.click("#vx-go");
  await page.waitForSelector("#vx-res audio", { timeout: 60_000 });
  assert.match(await page.textContent("main"), /clonage n'est pas activé/);
  await shot("8-voix");

  assert.deepEqual(errors, []);
  console.log("Parcours Studio et Voix : OK");
} finally {
  await browser.close();
  srv.close();
}
