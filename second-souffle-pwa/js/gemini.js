/* Appel à l'IA Gemini de Google depuis l'application (la clé est celle de l'utilisateur, gardée sur son appareil).
   Fonctions pures et testables : construction de la requête, lecture de la réponse, classement des erreurs. */
(function (g) {
  var BASE = "https://generativelanguage.googleapis.com/v1beta";
  var LANGNAME = { fr: "French", en: "English", pt: "Brazilian Portuguese" };

  function systemPrompt(lang, profile) {
    return [
      "You are Léo, a virtual coach in the Second Wind app (Second Souffle), for adults over 40 who are returning to exercise.",
      "Be warm, practical and concise: at most 120 words, short paragraphs, no markdown headings.",
      "You are not a doctor. Never diagnose, never advise on medication, never prescribe extreme diets, calorie targets or supplements.",
      "If the user mentions severe or sudden pain, chest pain, dizziness, numbness, fainting or trouble breathing, tell them to stop and get medical help right away.",
      "Respect the user's sensitive areas: do not suggest exercises that load them. When you suggest an exercise, prefer one from the list in the profile.",
      "For eating advice give general guidance only and suggest a dietitian or doctor for medical conditions, pregnancy or eating disorders.",
      "If you used web search, say so briefly. Reply in " + (LANGNAME[lang] || "French") + ".",
      "User profile: " + (profile || "not provided") + "."
    ].join("\n");
  }

  /* history : [{ role: "user" | "model", text }], le dernier élément est la question en cours. */
  function buildRequest(o) {
    var hist = (o.history || []).slice(-10);
    while (hist.length && hist[0].role !== "user") hist.shift();
    var body = {
      systemInstruction: { parts: [{ text: systemPrompt(o.lang, o.profile) }] },
      contents: hist.map(function (h) { return { role: h.role, parts: [{ text: h.text }] }; }),
      generationConfig: { temperature: 0.6, maxOutputTokens: 800 }
    };
    if (o.search) body.tools = [{ google_search: {} }];
    return {
      url: (o.base || BASE) + "/models/" + encodeURIComponent(o.model) + ":generateContent",
      init: { method: "POST", headers: { "Content-Type": "application/json", "x-goog-api-key": o.key }, body: JSON.stringify(body) }
    };
  }

  function safeUrl(u) { return /^https?:\/\//i.test(String(u || "")) ? String(u) : null; }

  function parseResponse(j) {
    var c = (j && j.candidates && j.candidates[0]) || null;
    if (!c) {
      var br = j && j.promptFeedback && j.promptFeedback.blockReason;
      var e = new Error(br ? "blocked: " + br : "no candidate"); e.kind = br ? "blocked" : "other"; throw e;
    }
    var parts = (c.content && c.content.parts) || [];
    var text = parts.filter(function (p) { return p.text && !p.thought; }).map(function (p) { return p.text; }).join("").trim();
    if (!text) { var e2 = new Error(c.finishReason ? "empty: " + c.finishReason : "empty"); e2.kind = c.finishReason === "SAFETY" ? "blocked" : "other"; throw e2; }
    var sources = [], seen = {};
    var chunks = (c.groundingMetadata && c.groundingMetadata.groundingChunks) || [];
    chunks.forEach(function (ch) {
      var w = ch.web, u = w && safeUrl(w.uri);
      if (u && !seen[u] && sources.length < 5) { seen[u] = 1; sources.push({ title: String(w.title || u), uri: u }); }
    });
    return { text: text, sources: sources };
  }

  function errorKind(status, message) {
    if (status === 400 && /api key|API_KEY/i.test(message || "")) return "key";
    if (status === 401 || status === 403) return "key";
    if (status === 404) return "model";
    if (status === 429) return "rate";
    return "other";
  }

  /* fetchFn : fonction compatible avec fetch. Renvoie { text, sources } ou rejette avec une erreur portant .kind. */
  function ask(fetchFn, o) {
    var r = buildRequest(o);
    return fetchFn(r.url, r.init).then(function (res) {
      if (res.ok) return res.json().then(parseResponse);
      return res.text().then(function (t) {
        var msg = t; try { msg = JSON.parse(t).error.message || t; } catch (e) { /* texte brut */ }
        var err = new Error(String(msg).slice(0, 300)); err.kind = errorKind(res.status, msg); err.status = res.status; throw err;
      });
    }, function (e) { var err = new Error(String(e && e.message || e)); err.kind = "net"; throw err; });
  }

  g.SS = g.SS || {};
  g.SS.gemini = { BASE: BASE, systemPrompt: systemPrompt, buildRequest: buildRequest, parseResponse: parseResponse, errorKind: errorKind, ask: ask, safeUrl: safeUrl };
})(typeof window !== "undefined" ? window : globalThis);
