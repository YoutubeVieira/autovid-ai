/* Parcours complet dans un navigateur (Playwright), avec une fausse IA : node tests/smoke.mjs
   Option : SCREENS=dossier pour enregistrer des captures d'écran. */
import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";
import { createServer } from "../server.mjs";
import { SAMPLES } from "./fake.mjs";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const here = path.dirname(fileURLToPath(import.meta.url));
const SCREENS = process.env.SCREENS;

const calls = [];
const client = {
  beta: { messages: { async parse(p) {
    calls.push(p);
    const text = JSON.stringify(p.messages[0].content);
    const key = /video ideas/.test(text) ? "ideas" : /Rate this short video/.test(text) ? "score" : /Analyse this creator/.test(text) ? "profile" : "adapt";
    return { stop_reason: "end_turn", parsed_output: SAMPLES[key] };
  } } }
};

const srv = createServer({ client, accessCode: "" }).listen(0);
await new Promise((r) => srv.once("listening", r));
const base = `http://127.0.0.1:${srv.address().port}/`;
const browser = await chromium.launch();
const errors = [];
try {
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("console", (m) => { if (m.type() === "error" && !/status of 400/.test(m.text())) errors.push(m.text()); });
  await page.goto(base);
  const shot = async (n) => SCREENS && page.screenshot({ path: path.join(SCREENS, n + ".png"), fullPage: true });

  /* Idées */
  await page.fill("#niche", "capoeira pour débutants");
  await page.click("#f-idees button[type=submit]");
  await page.waitForSelector(".idea");
  assert.match(await page.textContent(".idea .hook"), /jamais fait de capoeira/);
  assert.match(await page.textContent(".idea .hashtags"), /#capoeira #debutant/);
  await shot("1-idees");

  /* Idée -> publication pré-remplie */
  await page.click("[data-publier='0']");
  assert.match(await page.inputValue("#contenu"), /3 mouvements pour débuter/);

  /* Score avec une vraie vidéo : 6 images extraites dans le navigateur */
  await page.click(".tabs [data-vue=score]");
  await page.setInputFiles("#video-s", path.join(here, "fixtures/court.webm"));
  await page.waitForFunction(() => document.querySelectorAll("#thumbs-s img").length === 6);
  assert.match(await page.textContent("#video-s-nom"), /8 s/);
  await page.fill("#desc-s", "3 mouvements de base");
  await page.click("#f-score button[type=submit]");
  await page.waitForSelector(".ring");
  assert.equal((await page.textContent(".ring b")).trim(), "62");
  const scoreCall = calls.at(-1);
  const imgs = scoreCall.messages[0].content.filter((c) => c.type === "image");
  assert.equal(imgs.length, 6);
  assert.match(scoreCall.messages[0].content.at(-1).text, /Duration: 8 seconds/);
  await shot("2-score");

  /* Historique après rechargement */
  await page.reload();
  await page.waitForSelector(".history");
  assert.match(await page.textContent(".history"), /62/);

  /* Profil */
  await page.click(".tabs [data-vue=profil]");
  await page.fill("#stats", "1200 abonnés, 300 vues en moyenne");
  await page.click("#f-profil button[type=submit]");
  await page.waitForSelector("#r-profil .ring");
  assert.match(await page.textContent("#r-profil"), /Plan sur 7 jours/);
  await shot("3-profil");

  /* Publier */
  await page.click(".tabs [data-vue=publier]");
  await page.fill("#contenu", "Tutoriel capoeira");
  await page.uncheck("input[value=instagram]");
  await page.click("#f-pub button[type=submit]");
  await page.waitForSelector("#r-pub section.card");
  assert.deepEqual(JSON.stringify(calls.at(-1).messages[0].content).match(/tiktok|instagram|youtube/g).filter((v, i, a) => a.indexOf(v) === i), ["tiktok", "youtube"]);
  assert.equal(await page.locator("#r-pub section.card").count(), 2);
  assert.equal(await page.getAttribute("#r-pub a", "href"), "https://www.tiktok.com/upload");
  await shot("4-publier");

  /* Réglages : la langue part avec les demandes, l'erreur serveur s'affiche */
  await page.click("#btn-reglages");
  await page.selectOption("#r-langue", "pt");
  await page.click("#r-ok");
  await page.click(".tabs [data-vue=idees]");
  await page.click("#f-idees button[type=submit]");
  await page.waitForSelector(".idea");
  assert.match(calls.at(-1).system, /Brazilian Portuguese/);
  await page.fill("#niche", "");
  await page.evaluate(() => { document.getElementById("niche").required = false; });
  await page.click("#f-idees button[type=submit]");
  await page.waitForSelector("#r-idees .err");
  assert.match(await page.textContent("#r-idees .err"), /niche/);

  /* Thème sombre */
  await page.emulateMedia({ colorScheme: "dark" });
  await page.click(".tabs [data-vue=score]");
  await shot("5-score-sombre");

  assert.deepEqual(errors, []);
  console.log("Parcours navigateur : OK (" + calls.length + " demandes à la fausse IA)");
} finally {
  await browser.close();
  srv.close();
}
