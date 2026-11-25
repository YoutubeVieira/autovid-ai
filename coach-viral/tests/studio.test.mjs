import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, writeFile, readFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { wrap, sceneDurations, sceneStarts, renderVideo, mediaDuration, run } from "../lib/render.mjs";
import { buildAss, groupWords, assColor, renderFacecam } from "../lib/captions.mjs";
import { enginesAvailable, cloneEngines, falRequest, consentSentence, synthesize, prepareSample } from "../lib/voice.mjs";
import { Billing, openDb, QUOTAS } from "../lib/billing.mjs";
import { createServer } from "../server.mjs";
import * as studio from "../lib/studio.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const FIXTURE = path.join(here, "fixtures", "court.webm");

const VERSION = {
  titre: "La main tendue", legende: "Ce soir, prends sa main.", hashtags: ["couple"], ambiance_musique: "piano doux", pourquoi_mieux: "Accroche plus directe.",
  scenes: [
    { haut: "Le silence fait plus de bruit que les cris.", bas: "Prends sa main ce soir.", voix: "Le silence fait plus de bruit que les cris.", prompt_image: "", duree: 3 },
    { haut: "Une main tendue répare tout.", bas: "", voix: "Une main tendue répare tout.", prompt_image: "", duree: 3 }
  ]
};

/* ---------- Rendu ---------- */

test("coupure des lignes équilibrée", () => {
  assert.deepEqual(wrap("C'est le silence qui fait peur."), ["C'est le silence", "qui fait peur."]);
  assert.deepEqual(wrap(""), []);
  assert.ok(wrap("a ".repeat(40)).every((l) => l.length <= 30));
});

test("durées : assez longues pour la voix, fondus pris en compte", () => {
  assert.deepEqual(sceneDurations([{}, { duree: 6 }, {}], [4.5, 2, 0], 3), [5.3, 6, 3]);
  const { starts, total } = sceneStarts([5, 4, 3]);
  assert.deepEqual(starts, [0, 4.6, 8.2]);
  assert.ok(Math.abs(total - 11.2) < 1e-9);
});

test("rendu complet d'une vidéo citation 1080x1920 avec voix", { timeout: 180_000 }, async () => {
  const dir = await mkdtemp(path.join(tmpdir(), "t-rendu-"));
  const voix = path.join(dir, "v.wav");
  await run("ffmpeg", ["-y", "-loglevel", "error", "-f", "lavfi", "-i", "sine=f=220:d=3.5", voix]);
  const img = path.join(dir, "i.png");
  await run("ffmpeg", ["-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc2=s=800x600", "-frames:v", "1", img]);
  const out = path.join(dir, "o.mp4");
  const r = await renderVideo({ scenes: [{ haut: "Haut", bas: "Bas", image: img, voixFichier: voix }, { haut: "Sans image", bas: "" }] }, out);
  assert.deepEqual(r.scenes, [4.3, 3]);
  const probe = await run("ffprobe", ["-v", "error", "-show_entries", "stream=codec_type,width,height", "-of", "csv=p=0", out]);
  assert.match(probe, /video,1080,1920/);
  assert.match(probe, /audio/);
  assert.ok(Math.abs((await mediaDuration(out)) - 6.9) < 0.15);
});

/* ---------- Sous-titres ---------- */

const WORDS = [
  { mot: "Voici", debut: 0.1, fin: 0.4 }, { mot: "trois", debut: 0.45, fin: 0.7 }, { mot: "outils", debut: 0.75, fin: 1.1 },
  { mot: "gratuits", debut: 2.0, fin: 2.4 }
];

test("regroupement des mots, coupé aux pauses", () => {
  assert.deepEqual(groupWords(WORDS, 2).map((g) => g.map((w) => w.mot)), [["Voici", "trois"], ["outils"], ["gratuits"]]);
  assert.deepEqual(groupWords(WORDS, 4).map((g) => g.length), [3, 1]);
});

test("fichier ASS : couleurs, mot actif, titre en boîte", () => {
  assert.equal(assColor("#F28C28"), "&H00288CF2");
  const ass = buildAss(WORDS, [{ texte: "Titre {piège}", debut: 0, fin: 2 }], { majuscules: true, couleur_mot_actif: "#00FF00" });
  assert.match(ass, /PlayResX: 1080/);
  assert.match(ass, /\{\\c&H0000FF00\}VOICI/);
  assert.match(ass, /TitreBord,,0,0,0,,\{\\fad\(120,120\)\}Titre piège/);
  assert.equal((ass.match(/Style: Mots/g) || []).length, 1);
  assert.equal((ass.match(/,Mots,/g) || []).length, 4);
});

test("rendu face caméra au format 9:16", { timeout: 120_000 }, async () => {
  const dir = await mkdtemp(path.join(tmpdir(), "t-face-"));
  const out = path.join(dir, "f.mp4");
  await renderFacecam(FIXTURE, WORDS, [{ texte: "3 outils gratuits", debut: 0, fin: 2 }], {}, out);
  assert.match(await run("ffprobe", ["-v", "error", "-show_entries", "stream=width,height", "-of", "csv=p=0", out]), /1080,1920/);
});

/* ---------- Voix ---------- */

test("moteurs de voix : edge retiré en mode vente, fal seulement avec clé", () => {
  assert.deepEqual(enginesAvailable({ VOIX_MOTEURS: "kokoro,edge,fal" }), ["kokoro", "edge"]);
  assert.deepEqual(enginesAvailable({ VOIX_MOTEURS: "kokoro,edge,fal", VENTE: "1", FAL_KEY: "k" }), ["kokoro", "fal"]);
  assert.deepEqual(cloneEngines({ VOIX_MOTEURS: "kokoro,chatterbox" }), ["chatterbox"]);
});

test("requête fal : champs réglables", () => {
  const r = falRequest("Bonjour", "fr", "QUJD", { FAL_KEY: "k" });
  assert.equal(r.url, "https://fal.run/fal-ai/chatterbox/text-to-speech/multilingual");
  assert.equal(r.init.headers.Authorization, "Key k");
  assert.deepEqual(JSON.parse(r.init.body), { text: "Bonjour", audio_url: "data:audio/wav;base64,QUJD", custom_audio_language: "fr" });
  const r2 = falRequest("Oi", "pt", "QQ", { FAL_KEY: "k", FAL_CHAMP_LANGUE: "", FAL_MODELE: "x/y" });
  assert.equal(r2.url, "https://fal.run/x/y");
  assert.equal(JSON.parse(r2.init.body).custom_audio_language, undefined);
});

test("phrase de consentement avec code", () => {
  const c = consentSentence("fr", () => 0.5);
  assert.equal(c.code, "5500");
  assert.match(c.phrase, /ma propre voix.*5 5 0 0/);
});

test("voix de test, normalisée", { timeout: 60_000 }, async () => {
  const dir = await mkdtemp(path.join(tmpdir(), "t-voix-"));
  const r = await synthesize("Bonjour à toutes et à tous", path.join(dir, "v.wav"), { moteur: "test" }, { VOIX_MOTEURS: "test" });
  assert.ok(r.duree > 1);
  await assert.rejects(synthesize("x", path.join(dir, "w.wav"), { moteur: "edge" }, { VOIX_MOTEURS: "test" }), /indisponible/);
});

test("échantillon de clonage trop court refusé", { timeout: 60_000 }, async () => {
  const dir = await mkdtemp(path.join(tmpdir(), "t-ech-"));
  const src = path.join(dir, "s.wav");
  await run("ffmpeg", ["-y", "-loglevel", "error", "-f", "lavfi", "-i", "sine=f=200:d=2", src]);
  await assert.rejects(prepareSample(src, path.join(dir, "o.wav")), /trop court/);
  const long = path.join(dir, "l.wav");
  await run("ffmpeg", ["-y", "-loglevel", "error", "-f", "lavfi", "-i", "sine=f=200:d=12", long]);
  assert.ok((await prepareSample(long, path.join(dir, "o2.wav"))) > 10);
});

/* ---------- Abonnement ---------- */

function fakeStripe() {
  return {
    checkout: { sessions: {
      async create(p) { this.last = p; return { url: "https://checkout.stripe.test/s" }; },
      async retrieve(id) { return id === "cs_ok" ? { status: "complete", subscription: "sub_1", customer: "cus_1" } : { status: "open", subscription: null }; }
    } },
    billingPortal: { sessions: { async create(p) { return { url: "https://portal.test/" + p.customer }; } } }
  };
}

test("abonnement : clé remise une seule fois, quotas mensuels, résiliation", async () => {
  const stripe = fakeStripe();
  const b = new Billing({ db: openDb(":memory:"), stripe, price: "price_1", publicUrl: "https://app.test/" });
  assert.equal(await b.checkout(), "https://checkout.stripe.test/s");
  assert.equal(stripe.checkout.sessions.last.success_url, "https://app.test/?abonnement={CHECKOUT_SESSION_ID}");
  await assert.rejects(b.activate("cs_pending"), /pas terminé/);
  await assert.rejects(b.activate("pas-une-session"), /invalide/);
  const key = await b.activate("cs_ok");
  assert.match(key, /^cv_/);
  await assert.rejects(b.activate("cs_ok"), /déjà été remise/);
  assert.equal(b.isActive(key), true);
  assert.equal(b.isActive("cv_faux"), false);
  const jan = new Date("2026-01-15T10:00:00Z"), feb = new Date("2026-02-01T10:00:00Z");
  for (let i = 0; i < QUOTAS.video; i++) assert.equal(b.consume(key, "video", jan), true);
  assert.equal(b.consume(key, "video", jan), false);
  assert.equal(b.consume(key, "video", feb), true);
  assert.equal(b.usage(key, jan).video.utilise, QUOTAS.video);
  assert.equal(await b.portal(key), "https://portal.test/cus_1");
  b.handleEvent({ type: "customer.subscription.deleted", data: { object: { id: "sub_1", status: "canceled" } } });
  assert.equal(b.isActive(key), false);
});

/* ---------- Serveur : studio et abonnement de bout en bout (fausse IA) ---------- */

async function withServer(opts, fn) {
  const srv = createServer(opts).listen(0);
  await new Promise((r) => srv.once("listening", r));
  try { await fn(`http://127.0.0.1:${srv.address().port}`); } finally { srv.close(); }
}

async function waitJob(base, id, headers = {}) {
  for (let i = 0; i < 240; i++) {
    const j = await (await fetch(`${base}/api/travaux/${id}`, { headers })).json();
    if (j.etat === "termine" || j.etat === "erreur") return j;
    await new Promise((r) => setTimeout(r, 500));
  }
  throw new Error("délai dépassé");
}

test("studio : téléversement, analyse, fabrication, téléchargement", { timeout: 240_000 }, async () => {
  process.env.IMAGES = "aucun";
  process.env.TRANSCRIPTION = "0";
  const dataDir = await mkdtemp(path.join(tmpdir(), "t-data-"));
  const calls = [];
  const client = { beta: { messages: { async parse(p) {
    calls.push(p);
    return { stop_reason: "end_turn", parsed_output: { style: { format: "citation", visuel: "3D", texte: "haut/bas", voix: "douce", rythme: "lent", duree_secondes: 8 }, pourquoi_ca_marche: ["émotion"], a_ameliorer: ["accroche"], nouvelle_version: VERSION } };
  } } } };
  await withServer({ client, dataDir, env: { VOIX_MOTEURS: "test" } }, async (base) => {
    const up = await fetch(base + "/api/fichier", { method: "POST", headers: { "Content-Type": "video/webm" }, body: await readFile(FIXTURE) });
    const { id } = await up.json();
    assert.match(id, /^[a-f0-9]{24}$/);
    const bad = await fetch(base + "/api/fichier", { method: "POST", headers: { "Content-Type": "application/x-sh" }, body: "echo" });
    assert.equal(bad.status, 415);

    const an = await fetch(base + "/api/studio/analyser", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ fichier: id, consigne: "plus émouvant" }) });
    assert.equal(an.status, 200);
    const analyse = await an.json();
    assert.equal(analyse.nouvelle_version.titre, "La main tendue");
    const content = calls[0].messages[0].content;
    assert.equal(content.filter((c) => c.type === "image").length, 8);
    assert.match(content.at(-1).text, /ORIGINAL/);
    assert.match(content.at(-1).text, /plus émouvant/);

    const fab = await fetch(base + "/api/studio/fabriquer", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ gabarit: "citation", version: analyse.nouvelle_version, moteur: "test" }) });
    assert.equal(fab.status, 202);
    const job = await waitJob(base, (await fab.json()).travail);
    assert.equal(job.etat, "termine", job.erreur);
    const vid = await fetch(`${base}/api/fichiers/${job.resultat.video}?telecharger`);
    assert.equal(vid.status, 200);
    assert.match(vid.headers.get("content-disposition"), /attachment/);
    assert.ok((await vid.arrayBuffer()).byteLength > 10_000);
    assert.equal((await fetch(`${base}/api/fichiers/${job.resultat.voix}`)).status, 200);
    assert.equal((await fetch(`${base}/api/fichiers/${"0".repeat(24)}.mp4`)).status, 404);

    const inval = await fetch(base + "/api/studio/fabriquer", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ version: { scenes: [] } }) });
    assert.equal(inval.status, 400);
    const lien = await fetch(base + "/api/studio/analyser", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ lien: "file:///etc/passwd" }) });
    assert.equal(lien.status, 400);
  });
});

test("mode vente : sans clé valide, rien ne passe ; avec clé, quotas appliqués", async () => {
  const stripe = fakeStripe();
  const billing = new Billing({ db: openDb(":memory:"), stripe, price: "p", publicUrl: "https://app.test" });
  const client = { beta: { messages: { async parse() { return { stop_reason: "end_turn", parsed_output: { ideas: [] } }; } } } };
  await withServer({ client, billing, stripe, env: { VOIX_MOTEURS: "kokoro,edge", VENTE: "1" } }, async (base) => {
    const sante = await (await fetch(base + "/api/sante")).json();
    assert.equal(sante.vente, true);
    assert.deepEqual(sante.moteurs_voix, ["kokoro"]);
    const post = (p, body, key) => fetch(base + p, { method: "POST", headers: { "Content-Type": "application/json", ...(key ? { "x-cle": key } : {}) }, body: JSON.stringify(body) });
    assert.equal((await post("/api/ideas", { niche: "x" })).status, 402);
    assert.deepEqual(await (await post("/api/abonnement/payer", {})).json(), { url: "https://checkout.stripe.test/s" });
    const { cle } = await (await post("/api/abonnement/activer", { session: "cs_ok" })).json();
    assert.equal((await post("/api/ideas", { niche: "x" }, cle)).status, 200);
    const etat = await (await fetch(base + "/api/abonnement/etat", { headers: { "x-cle": cle } })).json();
    assert.equal(etat.usage.analyse.utilise, 1);
    assert.equal((await post("/api/stripe/webhook", {})).status, 400);
  });
});
