/* Serveur du Coach viral : sert l'application web et relaie les demandes vers Claude.
   La clé de l'API reste ici, jamais dans le navigateur. */
import http from "node:http";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import Anthropic from "@anthropic-ai/sdk";
import * as coach from "./lib/coach.mjs";
import { CoachError } from "./lib/coach.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const WEB = path.join(here, "web");
const MAX_BODY = 12 * 1024 * 1024;
const MAX_IMAGES = 8;
const MAX_IMAGE_B64 = 1.5 * 1024 * 1024;
const TYPES = {
  ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8",
  ".json": "application/json", ".webmanifest": "application/manifest+json", ".svg": "image/svg+xml", ".png": "image/png"
};

/* ---------- Validation des demandes ---------- */

const str = (v, max) => (typeof v === "string" ? v.trim().slice(0, max) : "");
const lang = (v) => (["fr", "pt", "en"].includes(v) ? v : "fr");
const platform = (v) => (["tiktok", "instagram", "youtube"].includes(v) ? v : "tiktok");

function images(v) {
  if (!Array.isArray(v)) return [];
  if (v.length > MAX_IMAGES) throw new CoachError("entree", `${MAX_IMAGES} images au maximum.`);
  return v.map((s) => {
    if (typeof s !== "string" || s.length > MAX_IMAGE_B64 || !/^[A-Za-z0-9+/=]+$/.test(s)) {
      throw new CoachError("entree", "Une image est invalide ou trop lourde.");
    }
    return s;
  });
}

export const routes = {
  ideas(b) {
    const niche = str(b.niche, 300);
    if (!niche) throw new CoachError("entree", "Indiquez votre niche ou votre sujet.");
    return (client) => coach.ideas(client, {
      niche, audience: str(b.audience, 300), objectif: str(b.objectif, 300), ton: str(b.ton, 100),
      contraintes: str(b.contraintes, 500), plateforme: platform(b.plateforme), nombre: b.nombre, langue: lang(b.langue)
    });
  },
  score(b) {
    const i = {
      description: str(b.description, 2000), transcription: str(b.transcription, 6000), legende: str(b.legende, 2200),
      duree: Number(b.duree) > 0 ? Math.min(Number(b.duree), 3600) : 0,
      images: images(b.images), plateforme: platform(b.plateforme), langue: lang(b.langue)
    };
    if (!i.images.length && !i.description && !i.transcription) {
      throw new CoachError("entree", "Ajoutez une vidéo, une description ou le texte de la vidéo.");
    }
    return (client) => coach.score(client, i);
  },
  profile(b) {
    const i = {
      pseudo: str(b.pseudo, 100), niche: str(b.niche, 300), stats: str(b.stats, 6000),
      images: images(b.images), langue: lang(b.langue)
    };
    if (!i.images.length && !i.stats) throw new CoachError("entree", "Ajoutez des captures d'écran ou vos statistiques.");
    return (client) => coach.profile(client, i);
  },
  adapt(b) {
    const plateformes = Array.isArray(b.plateformes) ? b.plateformes.filter((p) => ["tiktok", "instagram", "youtube"].includes(p)) : [];
    const contenu = str(b.contenu, 4000);
    if (!contenu) throw new CoachError("entree", "Décrivez la vidéo ou collez son script.");
    if (!plateformes.length) throw new CoachError("entree", "Choisissez au moins une plateforme.");
    return (client) => coach.adapt(client, { contenu, legende: str(b.legende, 2200), plateformes, langue: lang(b.langue) });
  }
};

/* ---------- Limite de débit simple par adresse ---------- */

const hits = new Map();
export function allowed(ip, now = Date.now(), perHour = Number(process.env.LIMITE_PAR_HEURE || 30)) {
  const list = (hits.get(ip) || []).filter((t) => now - t < 3600_000);
  if (list.length >= perHour) { hits.set(ip, list); return false; }
  list.push(now);
  hits.set(ip, list);
  return true;
}

/* ---------- Erreurs ---------- */

export function errorReply(e) {
  if (e instanceof CoachError) return [e.code === "entree" ? 400 : 502, { erreur: e.message }];
  if (e instanceof Anthropic.AuthenticationError) return [500, { erreur: "La clé de l'API Claude du serveur est invalide." }];
  if (e instanceof Anthropic.RateLimitError) return [429, { erreur: "Trop de demandes en même temps. Réessayez dans une minute." }];
  if (e instanceof Anthropic.BadRequestError) return [502, { erreur: "Demande refusée par l'IA (fichier trop lourd ?)." }];
  if (e instanceof Anthropic.APIConnectionError) return [503, { erreur: "Impossible de joindre l'IA. Réessayez." }];
  if (e instanceof Anthropic.APIError) return [502, { erreur: "Erreur de l'IA (" + e.status + "). Réessayez." }];
  return [500, { erreur: "Erreur inattendue du serveur." }];
}

/* ---------- Serveur HTTP ---------- */

function send(res, status, obj) {
  res.writeHead(status, { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" });
  res.end(JSON.stringify(obj));
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let size = 0;
    const chunks = [];
    req.on("data", (c) => {
      size += c.length;
      if (size > MAX_BODY) { reject(new CoachError("entree", "Envoi trop lourd.")); req.destroy(); return; }
      chunks.push(c);
    });
    req.on("end", () => {
      try { resolve(JSON.parse(Buffer.concat(chunks).toString("utf8") || "{}")); }
      catch { reject(new CoachError("entree", "Demande illisible.")); }
    });
    req.on("error", reject);
  });
}

async function serveStatic(req, res) {
  const url = new URL(req.url, "http://x");
  let rel = decodeURIComponent(url.pathname);
  if (rel.endsWith("/")) rel += "index.html";
  const file = path.normalize(path.join(WEB, rel));
  if (!file.startsWith(WEB + path.sep)) { res.writeHead(403); res.end(); return; }
  try {
    const data = await readFile(file);
    res.writeHead(200, { "Content-Type": TYPES[path.extname(file)] || "application/octet-stream", "Cache-Control": "no-cache" });
    res.end(data);
  } catch {
    res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
    res.end("Introuvable");
  }
}

export function createServer({ client, accessCode = process.env.CODE_ACCES || "" } = {}) {
  return http.createServer(async (req, res) => {
    const url = new URL(req.url, "http://x");
    if (url.pathname === "/api/sante") return send(res, 200, { ok: true, code_requis: Boolean(accessCode) });
    if (!url.pathname.startsWith("/api/")) {
      if (req.method !== "GET" && req.method !== "HEAD") { res.writeHead(405); res.end(); return; }
      return serveStatic(req, res);
    }
    if (req.method !== "POST") return send(res, 405, { erreur: "Méthode non permise." });
    if (accessCode && req.headers["x-code-acces"] !== accessCode) return send(res, 401, { erreur: "Code d'accès incorrect." });
    const ip = req.socket.remoteAddress || "?";
    if (!allowed(ip)) return send(res, 429, { erreur: "Limite de demandes atteinte pour cette heure." });
    try {
      const name = url.pathname.slice(5);
      const route = routes[name];
      if (!route) return send(res, 404, { erreur: "Service inconnu." });
      const body = await readBody(req);
      const run = route(body);
      return send(res, 200, await run(client));
    } catch (e) {
      if (!(e instanceof CoachError)) console.error(e);
      const [status, obj] = errorReply(e);
      return send(res, status, obj);
    }
  });
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  if (!process.env.ANTHROPIC_API_KEY) console.warn("Attention : ANTHROPIC_API_KEY n'est pas définie, l'IA ne répondra pas.");
  const port = Number(process.env.PORT || 8080);
  createServer({ client: new Anthropic() }).listen(port, () => console.log(`Coach viral prêt sur http://localhost:${port}`));
}
