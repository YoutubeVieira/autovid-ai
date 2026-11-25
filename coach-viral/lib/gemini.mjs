/* Gemini (Google) : alternative gratuite à Claude, avec la clé gratuite de Google AI Studio.
   API REST generateContent ; réponses structurées par generationConfig.responseJsonSchema
   (champ et mots-clés acceptés vérifiés dans les types du SDK officiel @google/genai 3.6.1). */
import * as z from "zod/v4";

export const GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta";

export class GeminiError extends Error {
  constructor(kind, message, status) { super(message); this.kind = kind; this.status = status; }
}

/* Mots-clés JSON Schema acceptés par Gemini (liste du SDK) : on retire le reste ($schema…). */
const ALLOWED = new Set(["$id", "$defs", "$ref", "$anchor", "type", "format", "title", "description", "enum", "items", "prefixItems",
  "minItems", "maxItems", "minimum", "maximum", "anyOf", "oneOf", "properties", "additionalProperties", "required", "propertyOrdering"]);

export function cleanSchema(node) {
  if (Array.isArray(node)) return node.map(cleanSchema);
  if (!node || typeof node !== "object") return node;
  const out = {};
  for (const [k, v] of Object.entries(node)) {
    if (!ALLOWED.has(k)) continue;
    if (k === "properties" || k === "$defs") out[k] = Object.fromEntries(Object.entries(v).map(([n, s]) => [n, cleanSchema(s)]));
    else if (k === "enum" || k === "required" || k === "propertyOrdering") out[k] = v;
    else out[k] = cleanSchema(v);
  }
  return out;
}

export function jsonSchemaOf(zodSchema) {
  return cleanSchema(z.toJSONSchema(zodSchema));
}

/* Convertit un contenu au format Claude (texte ou blocs) en « parts » Gemini. */
export function toParts(content) {
  if (typeof content === "string") return [{ text: content }];
  return content.map((b) => {
    if (b.type === "text") return { text: b.text };
    if (b.type === "image" && b.source?.type === "base64") return { inlineData: { mimeType: b.source.media_type, data: b.source.data } };
    throw new GeminiError("entree", "Type de contenu non pris en charge : " + b.type);
  });
}

export function buildRequest({ key, model, system, content, schema, search = false, maxTokens = 16000 }) {
  const body = {
    contents: [{ role: "user", parts: toParts(content) }],
    generationConfig: { maxOutputTokens: maxTokens }
  };
  if (system) body.systemInstruction = { parts: [{ text: system }] };
  if (schema) {
    body.generationConfig.responseMimeType = "application/json";
    body.generationConfig.responseJsonSchema = jsonSchemaOf(schema);
  }
  if (search) body.tools = [{ google_search: {} }];
  return {
    url: `${GEMINI_BASE}/models/${encodeURIComponent(model)}:generateContent`,
    init: { method: "POST", headers: { "Content-Type": "application/json", "x-goog-api-key": key }, body: JSON.stringify(body) }
  };
}

export function responseText(j) {
  const c = j?.candidates?.[0];
  if (!c) {
    const br = j?.promptFeedback?.blockReason;
    throw new GeminiError(br ? "refus" : "vide", br ? "Gemini a refusé cette demande. Reformulez-la." : "Gemini n'a rien répondu. Réessayez.");
  }
  const text = (c.content?.parts || []).filter((p) => p.text && !p.thought).map((p) => p.text).join("").trim();
  if (c.finishReason === "MAX_TOKENS" && !text) throw new GeminiError("trop_long", "La réponse était trop longue. Demandez moins d'éléments.");
  if (!text) throw new GeminiError(c.finishReason === "SAFETY" ? "refus" : "vide", c.finishReason === "SAFETY" ? "Gemini a refusé cette demande. Reformulez-la." : "Réponse vide de Gemini. Réessayez.");
  return { text, finishReason: c.finishReason, sources: (c.groundingMetadata?.groundingChunks || []).map((g) => g.web?.uri).filter(Boolean) };
}

function httpError(status, message) {
  if (status === 429) return new GeminiError("limite", "Limite gratuite de Gemini atteinte. Réessayez dans une minute (ou demain si c'est la limite du jour).", status);
  if (status === 400 && /api key/i.test(message)) return new GeminiError("cle", "Clé Gemini invalide. Vérifiez-la dans Google AI Studio.", status);
  if (status === 401 || status === 403) return new GeminiError("cle", "Clé Gemini refusée. Vérifiez-la dans Google AI Studio.", status);
  if (status === 404) return new GeminiError("modele", "Modèle Gemini introuvable. Réglez GEMINI_MODELE (par exemple gemini-flash-latest).", status);
  return new GeminiError("autre", "Erreur de Gemini (" + status + ") : " + String(message).slice(0, 200), status);
}

/* Client Gemini : mêmes services que ceux que le coach demande à Claude. */
export class GeminiClient {
  constructor({ key, model = "gemini-flash-latest", fetch: f = fetch } = {}) {
    this.provider = "gemini";
    this.key = key;
    this.model = model;
    this.fetch = f;
  }
  async call(o) {
    const { url, init } = buildRequest({ key: this.key, model: this.model, ...o });
    let res;
    try { res = await this.fetch(url, init); }
    catch { throw new GeminiError("reseau", "Impossible de joindre Gemini. Vérifiez la connexion."); }
    if (!res.ok) {
      const t = await res.text().catch(() => "");
      let msg = t;
      try { msg = JSON.parse(t).error.message || t; } catch { /* texte brut */ }
      throw httpError(res.status, msg);
    }
    return responseText(await res.json());
  }
  /* Réponse JSON validée par le schéma zod. */
  async parseJson({ system, content, schema, maxTokens }) {
    const r = await this.call({ system, content, schema, maxTokens });
    let data;
    try { data = JSON.parse(r.text); }
    catch { throw new GeminiError(r.finishReason === "MAX_TOKENS" ? "trop_long" : "reponse_invalide", r.finishReason === "MAX_TOKENS" ? "La réponse était trop longue. Demandez moins d'éléments." : "Réponse illisible de Gemini. Réessayez."); }
    const parsed = schema.safeParse(data);
    if (!parsed.success) throw new GeminiError("reponse_invalide", "Réponse incomplète de Gemini. Réessayez.");
    return parsed.data;
  }
  /* Recherche Google (pour le radar) : texte + adresses des sources. */
  async search({ system, content }) {
    const r = await this.call({ system, content, search: true });
    return r.text + (r.sources.length ? "\nSources: " + r.sources.join(" ") : "");
  }
}
