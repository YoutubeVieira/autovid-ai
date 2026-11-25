import { test } from "node:test";
import assert from "node:assert/strict";
import net from "node:net";
import Anthropic from "@anthropic-ai/sdk";
import * as coach from "../lib/coach.mjs";
import { createServer, errorReply, allowed } from "../server.mjs";
import { fakeClient, SAMPLES } from "./fake.mjs";

async function withServer(client, fn, opts = {}) {
  const srv = createServer({ client, ...opts }).listen(0);
  await new Promise((r) => srv.once("listening", r));
  const base = `http://127.0.0.1:${srv.address().port}`;
  try { await fn(base); } finally { srv.close(); }
}
function rawStatus(base, rawPath) {
  const { port } = new URL(base);
  return new Promise((resolve, reject) => {
    const sock = net.connect(Number(port), "127.0.0.1", () => sock.write(`GET ${rawPath} HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n`));
    let data = "";
    sock.on("data", (c) => (data += c));
    sock.on("end", () => resolve(Number(data.split(" ")[1])));
    sock.on("error", reject);
  });
}
const post = (base, path, body, headers = {}) =>
  fetch(base + path, { method: "POST", headers: { "Content-Type": "application/json", ...headers }, body: JSON.stringify(body) });

test("la demande à Claude utilise le bon modèle, le format structuré et le relais en cas de refus", async () => {
  const client = fakeClient({ output: SAMPLES.ideas });
  const out = await coach.ideas(client, { niche: "capoeira", nombre: 3, plateforme: "tiktok", langue: "pt" });
  assert.deepEqual(out, SAMPLES.ideas);
  const p = client.calls[0];
  assert.equal(p.model, "claude-opus-5-5");
  assert.equal(p.fallbacks, "default");
  assert.deepEqual(p.betas, ["server-side-fallback-2026-07-01"]);
  assert.equal(p.output_config.effort, "medium");
  assert.equal(p.output_config.format.type, "json_schema");
  assert.match(p.system, /Brazilian Portuguese/);
  assert.match(p.messages[0].content, /Create 3 short video ideas/);
  assert.equal(p.thinking, undefined, "pas de thinking désactivé (refusé par ce modèle)");
});

test("le nombre d'idées est borné", async () => {
  const client = fakeClient({ output: SAMPLES.ideas });
  await coach.ideas(client, { niche: "x", nombre: 99 });
  assert.match(client.calls[0].messages[0].content, /Create 8 /);
});

test("le score envoie les images avant le texte", async () => {
  const client = fakeClient({ output: SAMPLES.score });
  await coach.score(client, { images: ["QUJD", "REVG"], description: "d", duree: 12.4 });
  const c = client.calls[0].messages[0].content;
  assert.equal(c[0].type, "image");
  assert.equal(c[0].source.media_type, "image/jpeg");
  assert.equal(c[2].type, "text");
  assert.match(c[2].text, /Duration: 12 seconds/);
  assert.equal(client.calls[0].output_config.effort, "high");
});

test("refus, réponse coupée et réponse illisible deviennent des erreurs claires", async () => {
  await assert.rejects(coach.adapt(fakeClient({ output: SAMPLES.adapt, stop_reason: "refusal" }), { contenu: "x", plateformes: ["tiktok"] }), { code: "refus" });
  await assert.rejects(coach.adapt(fakeClient({ output: SAMPLES.adapt, stop_reason: "max_tokens" }), { contenu: "x", plateformes: ["tiktok"] }), { code: "trop_long" });
  await assert.rejects(coach.adapt(fakeClient({}), { contenu: "x", plateformes: ["tiktok"] }), { code: "reponse_invalide" });
});

test("les quatre services répondent par HTTP", async () => {
  for (const [route, body, sample] of [
    ["ideas", { niche: "capoeira" }, SAMPLES.ideas],
    ["score", { description: "ma vidéo" }, SAMPLES.score],
    ["profile", { stats: "1200 abonnés" }, SAMPLES.profile],
    ["adapt", { contenu: "script", plateformes: ["tiktok", "youtube", "facebook"] }, SAMPLES.adapt]
  ]) {
    const client = fakeClient({ output: sample });
    await withServer(client, async (base) => {
      const r = await post(base, "/api/" + route, body);
      assert.equal(r.status, 200, route);
      assert.deepEqual(await r.json(), sample);
    });
    if (route === "adapt") assert.doesNotMatch(client.calls[0].messages[0].content, /facebook/);
  }
});

test("les entrées vides ou invalides sont refusées sans appeler l'IA", async () => {
  const client = fakeClient({ output: SAMPLES.score });
  await withServer(client, async (base) => {
    assert.equal((await post(base, "/api/ideas", {})).status, 400);
    assert.equal((await post(base, "/api/score", {})).status, 400);
    assert.equal((await post(base, "/api/score", { images: ["pas<du>base64"] })).status, 400);
    assert.equal((await post(base, "/api/score", { images: Array(9).fill("QUJD") })).status, 400);
    assert.equal((await post(base, "/api/adapt", { contenu: "x", plateformes: [] })).status, 400);
    assert.equal((await post(base, "/api/inconnu", {})).status, 404);
    const bad = await fetch(base + "/api/ideas", { method: "POST", body: "{pas du json" });
    assert.equal(bad.status, 400);
  });
  assert.equal(client.calls.length, 0);
});

test("le code d'accès protège l'IA depuis le tunnel, pas sur le PC lui-même", async () => {
  const client = fakeClient({ output: SAMPLES.ideas });
  await withServer(client, async (base) => {
    const tunnel = { "cf-connecting-ip": "203.0.113.9" };
    const r401 = await post(base, "/api/ideas", { niche: "x" }, tunnel);
    assert.equal(r401.status, 401);
    assert.equal((await r401.json()).code_requis, true);
    assert.equal((await post(base, "/api/ideas", { niche: "x" }, { ...tunnel, "x-code-acces": "faux" })).status, 401);
    assert.equal((await post(base, "/api/ideas", { niche: "x" }, { "x-forwarded-for": "198.51.100.1" })).status, 401);
    assert.equal((await post(base, "/api/ideas", { niche: "x" }, { ...tunnel, "x-code-acces": "secret" })).status, 200);
    assert.equal((await post(base, "/api/ideas", { niche: "x" })).status, 200, "sur le PC, sans tunnel : pas de code");
    assert.equal((await fetch(base + "/")).status, 200);
    const sante = await (await fetch(base + "/api/sante")).json();
    assert.equal(sante.code_requis, true);
    assert.equal(sante.vente, false);
  }, { accessCode: "secret" });
});

test("la page est servie et on ne peut pas sortir du dossier web", async () => {
  await withServer(fakeClient({}), async (base) => {
    const r = await fetch(base + "/");
    assert.match(r.headers.get("content-type"), /text\/html/);
    assert.match(await r.text(), /Coach Viral/);
    for (const raw of ["/../server.mjs", "/..%2fserver.mjs", "/%2e%2e/package.json"]) {
      const status = await rawStatus(base, raw);
      assert.ok(status === 403 || status === 404, raw + " -> " + status);
    }
  });
});

test("les erreurs de l'API sont traduites", () => {
  const h = new Headers();
  assert.equal(errorReply(new Anthropic.RateLimitError(429, {}, "x", h))[0], 429);
  assert.equal(errorReply(new Anthropic.AuthenticationError(401, {}, "x", h))[0], 500);
  assert.equal(errorReply(new Anthropic.APIConnectionError({ message: "x" }))[0], 503);
  assert.equal(errorReply(new Error("x"))[0], 500);
});

test("limite de débit par adresse", () => {
  const t = 1_000_000;
  assert.equal(allowed("1.1.1.1", t, 2), true);
  assert.equal(allowed("1.1.1.1", t, 2), true);
  assert.equal(allowed("1.1.1.1", t, 2), false);
  assert.equal(allowed("1.1.1.1", t + 3600_001, 2), true);
});
