import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, readFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { youtubeSignals, redditSignals, webResearch, scanNiche, Radar, slug } from "../lib/radar.mjs";
import { sanitizeClips, wordsInRange, produceClips } from "../lib/studio.mjs";
import { renderFacecam } from "../lib/captions.mjs";
import { run } from "../lib/render.mjs";
import { createServer } from "../server.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const THEMES = { themes: [{ theme: "Défi ginga 7 jours", pourquoi_maintenant: "Recherches en hausse", accroches: ["a", "b", "c"], format: "défi", potentiel: 78, concurrence: "faible", sources: ["https://exemple.fr/a"] }] };

function json(data, ok = true) { return { ok, json: async () => data }; }

test("YouTube : recherche des Shorts de la semaine, triés par vues", async () => {
  const urls = [];
  const fake = async (u) => {
    urls.push(u);
    if (u.includes("/search?")) return json({ items: [{ id: { videoId: "a1" } }, { id: { videoId: "b2" } }] });
    return json({ items: [
      { id: "a1", snippet: { title: "Ginga", channelTitle: "C1" }, statistics: { viewCount: "100" } },
      { id: "b2", snippet: { title: "Roda", channelTitle: "C2" }, statistics: { viewCount: "5000" } }
    ] });
  };
  const r = await youtubeSignals("capoeira", "pt", "CLE", fake, new Date("2026-11-25T00:00:00Z"));
  assert.deepEqual(r.map((x) => x.titre), ["Roda", "Ginga"]);
  assert.equal(r[0].url, "https://www.youtube.com/shorts/b2");
  const q = new URL(urls[0]).searchParams;
  assert.equal(q.get("videoDuration"), "short");
  assert.equal(q.get("regionCode"), "BR");
  assert.equal(q.get("publishedAfter"), "2026-11-18T00:00:00.000Z");
  assert.deepEqual(await youtubeSignals("x", "fr", "", fake), []);
});

test("Reddit : posts de la semaine, noms de subreddit filtrés, erreurs ignorées", async () => {
  const seen = [];
  const fake = async (u) => {
    seen.push(u);
    if (u.includes("/r/casse/")) throw new Error("réseau");
    return json({ data: { children: [{ data: { title: "Mon premier batizado", ups: 321, num_comments: 12, permalink: "/r/capoeira/x" } }] } });
  };
  const r = await redditSignals(["capoeira", "casse", "../etc", "a b"], fake);
  assert.equal(r.length, 1);
  assert.equal(r[0].url, "https://www.reddit.com/r/capoeira/x");
  assert.equal(seen.length, 2);
});

test("recherche web : outil web_search, reprise après pause", async () => {
  const calls = [];
  const client = { beta: { messages: { async create(p) {
    calls.push(JSON.parse(JSON.stringify(p)));
    if (calls.length === 1) return { stop_reason: "pause_turn", content: [{ type: "server_tool_use", id: "s1" }] };
    return { stop_reason: "end_turn", content: [{ type: "text", text: "Signal 1 https://exemple.fr" }] };
  } } } };
  const t = await webResearch(client, "capoeira", "fr");
  assert.equal(t, "Signal 1 https://exemple.fr");
  assert.equal(calls[0].tools[0].type, "web_search_20260209");
  assert.equal(calls[0].tools[0].user_location.country, "FR");
  assert.equal(calls[1].messages.length, 2);
  assert.equal(calls[1].messages[1].role, "assistant");
});

test("passage du radar : signaux réunis, thèmes déjà vus exclus, historique gardé", async () => {
  const prompts = [];
  const client = { beta: { messages: {
    async create() { return { stop_reason: "end_turn", content: [{ type: "text", text: "Tendance : défi ginga" }] }; },
    async parse(p) { prompts.push(p.messages[0].content); return { stop_reason: "end_turn", parsed_output: THEMES }; }
  } } };
  const dir = await mkdtemp(path.join(tmpdir(), "radar-"));
  const radar = new Radar({ client, dir, env: { RADAR_NICHES: "Capoeira débutants; Fitness seniors" } });
  assert.deepEqual((await radar.niches()).map((n) => n.nom), ["Capoeira débutants", "Fitness seniors"]);
  const r1 = await radar.run();
  assert.deepEqual(r1.fait.map((x) => x.themes), [1, 1]);
  await radar.run("Capoeira débutants");
  assert.match(prompts.at(-1), /Avoid repeating these themes already proposed: Défi ginga 7 jours/);
  assert.match(prompts.at(-1), /Tendance : défi ginga/);
  const saved = JSON.parse(await readFile(path.join(dir, slug("Capoeira débutants") + ".json"), "utf8"));
  assert.equal(saved.length, 2);
  assert.equal(slug("Capoeira débutants"), "capoeira-debutants");
});

test("clips : bornes corrigées, chevauchements retirés, mots recalés", () => {
  const ok = sanitizeClips([
    { titre: "A", debut: 10, fin: 40, score: 90, pourquoi: "" },
    { titre: "B", debut: 30, fin: 60, score: 80, pourquoi: "" },
    { titre: "C", debut: 70, fin: 65, score: 70, pourquoi: "" },
    { titre: "D", debut: 80, fin: 500, score: 60, pourquoi: "" }
  ], 100);
  assert.deepEqual(ok.map((c) => [c.titre, c.debut, c.fin]), [["A", 10, 40], ["D", 80, 100]]);
  const w = wordsInRange([{ mot: "a", debut: 9, fin: 9.5 }, { mot: "b", debut: 10.2, fin: 10.6 }, { mot: "c", debut: 39.8, fin: 40.1 }], 10, 40);
  assert.deepEqual(w.map((x) => [x.mot, +x.debut.toFixed(2)]), [["b", 0.2], ["c", 29.8]]);
});

test("clips de bout en bout sur une vraie vidéo", { timeout: 120_000 }, async () => {
  const dir = await mkdtemp(path.join(tmpdir(), "clips-"));
  const long = path.join(dir, "long.mp4");
  await run("ffmpeg", ["-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc2=s=640x360:d=30", "-f", "lavfi", "-i", "sine=d=30", "-shortest", "-c:v", "libx264", "-c:a", "aac", long]);
  const mots = Array.from({ length: 50 }, (_, i) => ({ mot: "mot" + i, debut: i * 0.55, fin: i * 0.55 + 0.4 }));
  const client = { beta: { messages: { async parse() {
    return { stop_reason: "end_turn", parsed_output: { clips: [{ titre: "Le meilleur moment", debut: 2, fin: 14, score: 88, pourquoi: "accroche" }, { titre: "Trop court", debut: 20, fin: 22, score: 50, pourquoi: "" }] } };
  } } } };
  const r = await produceClips(client, long, { mots, nombre: 2 }, dir, renderFacecam);
  assert.equal(r.clips.length, 1);
  const out = path.join(dir, r.clips[0].video);
  assert.match(await run("ffprobe", ["-v", "error", "-show_entries", "stream=width,height:format=duration", "-of", "csv=p=0", out]), /1080,1920[\s\S]*1[12]\./);
});

test("serveur : niches, lancement, déclenchement externe protégé par jeton", async () => {
  const client = { beta: { messages: {
    async create() { return { stop_reason: "end_turn", content: [{ type: "text", text: "" }] }; },
    async parse() { return { stop_reason: "end_turn", parsed_output: THEMES }; }
  } } };
  const dataDir = await mkdtemp(path.join(tmpdir(), "srv-radar-"));
  const srv = createServer({ client, dataDir, env: { RADAR_JETON: "secret", RADAR_WEB: "0" } }).listen(0);
  await new Promise((r) => srv.once("listening", r));
  const base = `http://127.0.0.1:${srv.address().port}`;
  const post = (p, body, h = {}) => fetch(base + p, { method: "POST", headers: { "Content-Type": "application/json", ...h }, body: JSON.stringify(body) });
  try {
    assert.equal((await post("/api/radar/lancer", {})).status, 400);
    const n = await (await post("/api/radar/niches", { niches: [{ nom: "Capoeira", subreddits: "r/capoeira ../x fitness", langue: "pt" }, { nom: "" }] })).json();
    assert.deepEqual(n.niches, [{ nom: "Capoeira", public: "", langue: "pt", subreddits: ["capoeira", "fitness"] }]);
    assert.equal((await post("/api/radar/declencher", {})).status, 401);
    const r = await (await post("/api/radar/declencher?attendre", {}, { "x-jeton-radar": "secret" })).json();
    assert.deepEqual(r.fait, [{ niche: "Capoeira", themes: 1 }]);
    const g = await (await fetch(base + "/api/radar")).json();
    assert.equal(g.resultats.Capoeira.themes[0].theme, "Défi ginga 7 jours");
  } finally {
    srv.close();
  }
});
