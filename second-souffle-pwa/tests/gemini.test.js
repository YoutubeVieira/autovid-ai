/* Tests du module Gemini : requête, réponse, erreurs. Aucun appel réseau. Lancer : node tests/gemini.test.js */
var assert = require("assert");
require("../js/gemini.js");
var G = globalThis.SS.gemini, failures = 0;
function test(name, fn) { return Promise.resolve().then(fn).then(function () { console.log("ok   " + name); }, function (e) { failures++; console.log("FAIL " + name + "\n     " + e.message); }); }
function resp(status, body) { return Promise.resolve({ ok: status >= 200 && status < 300, status: status, json: function () { return Promise.resolve(body); }, text: function () { return Promise.resolve(typeof body === "string" ? body : JSON.stringify(body)); } }); }
var base = { key: "K", model: "gemini-test", lang: "pt", profile: "knees flagged", history: [{ role: "user", text: "Oi" }] };

(async function () {
  await test("requête : clé dans l'en-tête, jamais dans l'adresse", function () {
    var r = G.buildRequest(base);
    assert.ok(r.url.endsWith("/models/gemini-test:generateContent"));
    assert.ok(r.url.indexOf("K") < 0 || r.url.indexOf("key=") < 0);
    assert.strictEqual(r.init.headers["x-goog-api-key"], "K");
    assert.strictEqual(r.init.method, "POST");
  });
  await test("requête : consigne système, langue, profil, recherche facultative", function () {
    var b = JSON.parse(G.buildRequest(base).init.body);
    assert.ok(b.systemInstruction.parts[0].text.indexOf("Brazilian Portuguese") > 0);
    assert.ok(b.systemInstruction.parts[0].text.indexOf("knees flagged") > 0);
    assert.strictEqual(b.tools, undefined);
    var c = JSON.parse(G.buildRequest(Object.assign({}, base, { search: true })).init.body);
    assert.deepStrictEqual(c.tools, [{ google_search: {} }]);
  });
  await test("requête : l'historique commence par l'utilisateur et garde 10 messages", function () {
    var h = [{ role: "model", text: "a" }];
    for (var i = 0; i < 14; i++) h.push({ role: i % 2 ? "model" : "user", text: "m" + i });
    var b = JSON.parse(G.buildRequest(Object.assign({}, base, { history: h })).init.body);
    assert.strictEqual(b.contents[0].role, "user"); assert.ok(b.contents.length <= 10);
  });
  await test("réponse : texte, parties de réflexion ignorées, sources dédoublonnées et sûres", function () {
    var r = G.parseResponse({ candidates: [{ content: { parts: [{ text: "pense", thought: true }, { text: "Bonjour " }, { text: "Léo" }] },
      groundingMetadata: { groundingChunks: [{ web: { uri: "https://a.example/x", title: "A" } }, { web: { uri: "https://a.example/x", title: "A bis" } }, { web: { uri: "javascript:alert(1)", title: "mauvais" } }, { web: { uri: "http://b.example", title: "B" } }] } }] });
    assert.strictEqual(r.text, "Bonjour Léo");
    assert.deepStrictEqual(r.sources.map(function (s) { return s.uri; }), ["https://a.example/x", "http://b.example"]);
  });
  await test("réponse : bloquée ou vide", function () {
    assert.throws(function () { G.parseResponse({ promptFeedback: { blockReason: "SAFETY" } }); }, function (e) { return e.kind === "blocked"; });
    assert.throws(function () { G.parseResponse({ candidates: [{ content: { parts: [] }, finishReason: "SAFETY" }] }); }, function (e) { return e.kind === "blocked"; });
  });
  await test("erreurs : clé, modèle, limite, autre", function () {
    assert.strictEqual(G.errorKind(403, ""), "key"); assert.strictEqual(G.errorKind(400, "API key not valid"), "key");
    assert.strictEqual(G.errorKind(404, ""), "model"); assert.strictEqual(G.errorKind(429, ""), "rate"); assert.strictEqual(G.errorKind(500, ""), "other");
  });
  await test("ask : succès", async function () {
    var r = await G.ask(function () { return resp(200, { candidates: [{ content: { parts: [{ text: "OK" }] } }] }); }, base);
    assert.strictEqual(r.text, "OK");
  });
  await test("ask : 403 devient une erreur de clé, 429 une limite", async function () {
    await assert.rejects(G.ask(function () { return resp(403, { error: { message: "denied" } }); }, base), function (e) { return e.kind === "key" && e.status === 403; });
    await assert.rejects(G.ask(function () { return resp(429, "slow"); }, base), function (e) { return e.kind === "rate"; });
  });
  await test("ask : panne réseau", async function () {
    await assert.rejects(G.ask(function () { return Promise.reject(new TypeError("Failed to fetch")); }, base), function (e) { return e.kind === "net"; });
  });
  console.log(failures ? "\n" + failures + " test(s) en échec" : "\nTous les tests passent");
  process.exit(failures ? 1 : 0);
})();
