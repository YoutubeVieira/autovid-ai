import { test } from "node:test";
import assert from "node:assert/strict";
import { GeminiClient, buildRequest, jsonSchemaOf, cleanSchema } from "../lib/gemini.mjs";
import * as coach from "../lib/coach.mjs";
import { IdeasSchema, ScoreSchema, ProfileSchema, AdaptSchema } from "../lib/coach.mjs";
import { AnalysisSchema, NewVersion, StyleSchema, TitlesSchema, ClipsSchema } from "../lib/studio.mjs";
import { RadarSchema, webResearch } from "../lib/radar.mjs";
import { chooseAI } from "../server.mjs";
import { SAMPLES } from "./fake.mjs";

const ALLOWED = new Set(["$id", "$defs", "$ref", "$anchor", "type", "format", "title", "description", "enum", "items", "prefixItems",
  "minItems", "maxItems", "minimum", "maximum", "anyOf", "oneOf", "properties", "additionalProperties", "required", "propertyOrdering"]);

function keysOk(node, where = "racine") {
  if (Array.isArray(node)) return node.forEach((n) => keysOk(n, where));
  if (!node || typeof node !== "object") return;
  for (const [k, v] of Object.entries(node)) {
    assert.ok(ALLOWED.has(k), `mot-clé refusé par Gemini : ${k} (${where})`);
    if (k === "properties") for (const [n, s] of Object.entries(v)) keysOk(s, n);
    else if (!["enum", "required", "propertyOrdering"].includes(k)) keysOk(v, where + "." + k);
  }
}

test("les 10 formats de réponse se convertissent en schéma accepté par Gemini", () => {
  for (const [nom, s] of Object.entries({ IdeasSchema, ScoreSchema, ProfileSchema, AdaptSchema, AnalysisSchema, NewVersion, StyleSchema, TitlesSchema, ClipsSchema, RadarSchema })) {
    const js = jsonSchemaOf(s);
    assert.equal(js.type, "object", nom);
    keysOk(js, nom);
  }
  assert.deepEqual(cleanSchema({ $schema: "x", type: "object", properties: { a: { type: "string", pattern: "^x" } } }), { type: "object", properties: { a: { type: "string" } } });
});

test("requête REST : clé dans l'en-tête, images en inlineData, schéma JSON", () => {
  const r = buildRequest({ key: "K", model: "gemini-flash-latest", system: "S", schema: ScoreSchema,
    content: [{ type: "image", source: { type: "base64", media_type: "image/jpeg", data: "QUJD" } }, { type: "text", text: "Note" }] });
  assert.equal(r.url, "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent");
  assert.equal(r.init.headers["x-goog-api-key"], "K");
  const b = JSON.parse(r.init.body);
  assert.deepEqual(b.contents[0].parts[0], { inlineData: { mimeType: "image/jpeg", data: "QUJD" } });
  assert.deepEqual(b.systemInstruction, { parts: [{ text: "S" }] });
  assert.equal(b.generationConfig.responseMimeType, "application/json");
  assert.equal(b.generationConfig.responseJsonSchema.type, "object");
  assert.equal(b.tools, undefined);
  assert.deepEqual(JSON.parse(buildRequest({ key: "K", model: "m", content: "x", search: true }).init.body).tools, [{ google_search: {} }]);
});

function fakeFetch(handler) {
  const calls = [];
  const f = async (url, init) => { calls.push({ url, body: JSON.parse(init.body) }); return handler(url, init); };
  f.calls = calls;
  return f;
}
const ok = (obj) => ({ ok: true, status: 200, json: async () => obj, text: async () => JSON.stringify(obj) });
const fail = (status, message) => ({ ok: false, status, json: async () => ({}), text: async () => JSON.stringify({ error: { message } }) });
const answer = (text, extra = {}) => ok({ candidates: [{ content: { parts: [{ text: "réflexion", thought: true }, { text }] }, finishReason: "STOP", ...extra }] });

test("le coach marche avec Gemini : réponse validée par le schéma", async () => {
  const f = fakeFetch(() => answer(JSON.stringify(SAMPLES.ideas)));
  const client = new GeminiClient({ key: "K", fetch: f });
  const out = await coach.ideas(client, { niche: "capoeira", langue: "pt" });
  assert.deepEqual(out, SAMPLES.ideas);
  assert.match(f.calls[0].body.systemInstruction.parts[0].text, /Brazilian Portuguese/);
});

test("erreurs Gemini traduites en messages clairs", async () => {
  const cases = [
    [() => fail(429, "Resource exhausted"), "limite", /Limite gratuite/],
    [() => fail(400, "API key not valid"), "cle", /Clé Gemini invalide/],
    [() => fail(404, "not found"), "modele", /GEMINI_MODELE/],
    [() => answer("{pas du json"), "reponse_invalide", /illisible/],
    [() => answer(JSON.stringify({ ideas: "faux" })), "reponse_invalide", /incomplète/],
    [() => ok({ promptFeedback: { blockReason: "SAFETY" } }), "refus", /refusé/]
  ];
  for (const [h, code, msg] of cases) {
    await assert.rejects(coach.ideas(new GeminiClient({ key: "K", fetch: fakeFetch(h) }), { niche: "x" }), (e) => e.code === code && msg.test(e.message));
  }
});

test("radar : recherche Google de Gemini avec les sources", async () => {
  const f = fakeFetch(() => answer("Défi ginga en hausse", { groundingMetadata: { groundingChunks: [{ web: { uri: "https://exemple.fr/a" } }] } }));
  const t = await webResearch(new GeminiClient({ key: "K", fetch: f }), "capoeira", "fr");
  assert.match(t, /Défi ginga en hausse\nSources: https:\/\/exemple.fr\/a/);
  assert.deepEqual(f.calls[0].body.tools, [{ google_search: {} }]);
});

test("choix de l'IA selon les clés présentes", () => {
  const warn = console.warn; console.warn = () => {};
  try {
    assert.equal(chooseAI({ GEMINI_API_KEY: "g" }).provider, "gemini");
    assert.equal(chooseAI({ IA: "gemini", GEMINI_API_KEY: "g", GEMINI_MODELE: "m" }).model, "m");
    assert.notEqual(chooseAI({ ANTHROPIC_API_KEY: "a", GEMINI_API_KEY: "g" }).provider, "gemini");
    assert.equal(chooseAI({ IA: "gemini", ANTHROPIC_API_KEY: "a", GEMINI_API_KEY: "g" }).provider, "gemini");
  } finally { console.warn = warn; }
});
