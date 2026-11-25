/* Serveur du Coach viral : application web, coach IA, studio vidéo, voix off et abonnement.
   La clé de l'API reste ici, jamais dans le navigateur. */
import http from "node:http";
import { readFile, readdir, mkdir, writeFile, rm, stat } from "node:fs/promises";
import { createHash } from "node:crypto";
import path from "node:path";
import { fileURLToPath } from "node:url";
import Anthropic from "@anthropic-ai/sdk";
import * as coach from "./lib/coach.mjs";
import { CoachError } from "./lib/coach.mjs";
import * as studio from "./lib/studio.mjs";
import { NewVersion } from "./lib/studio.mjs";
import { synthesize, prepareSample, consentSentence, enginesAvailable, cloneEngines, VOICES } from "./lib/voice.mjs";
import { renderFacecam } from "./lib/captions.mjs";
import { run as runCmd } from "./lib/render.mjs";
import { QUOTAS } from "./lib/billing.mjs";
import { Radar } from "./lib/radar.mjs";

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

/* ---------- Studio, voix, abonnement ---------- */

const ID = /^[a-f0-9]{24}$/;
const UPLOAD_TYPES = { "video/mp4": ".mp4", "video/quicktime": ".mov", "video/webm": ".webm", "image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "audio/mpeg": ".mp3", "audio/wav": ".wav", "audio/x-wav": ".wav", "audio/webm": ".webm", "audio/ogg": ".ogg", "audio/mp4": ".m4a" };
const MAX_UPLOAD = 150 * 1024 * 1024;

/* File d'attente : une seule fabrication de vidéo à la fois (le rendu prend tout le processeur). */
export class Jobs {
  constructor(parallel = Number(process.env.RENDUS_SIMULTANES || 1)) { this.jobs = new Map(); this.queue = []; this.active = 0; this.parallel = parallel; }
  add(owner, fn) {
    const id = studio.newId();
    const job = { id, owner, etat: "en_attente", etape: "En attente", resultat: null, erreur: null, cree: Date.now() };
    this.jobs.set(id, job);
    this.queue.push(async () => {
      job.etat = "en_cours";
      try { job.resultat = await fn((etape) => { job.etape = etape; }); job.etat = "termine"; job.etape = "Terminé"; }
      catch (e) { job.etat = "erreur"; job.erreur = e instanceof CoachError ? e.message : "La fabrication a échoué : " + String(e.message || e).slice(0, 300); if (!(e instanceof CoachError)) console.error(e); }
    });
    this.pump();
    return job;
  }
  pump() {
    while (this.active < this.parallel && this.queue.length) {
      const task = this.queue.shift();
      this.active++;
      task().finally(() => { this.active--; this.pump(); });
    }
  }
  get(id, owner) { const j = this.jobs.get(id); return j && j.owner === owner ? j : null; }
}

function readRaw(req, max) {
  return new Promise((resolve, reject) => {
    let size = 0;
    const chunks = [];
    req.on("data", (c) => {
      size += c.length;
      if (size > max) { reject(new CoachError("entree", "Fichier trop lourd (150 Mo au maximum).")); req.destroy(); return; }
      chunks.push(c);
    });
    req.on("end", () => resolve(Buffer.concat(chunks)));
    req.on("error", reject);
  });
}

async function serveFile(res, file, name, download) {
  try {
    const data = await readFile(file);
    const type = file.endsWith(".mp4") ? "video/mp4" : file.endsWith(".mp3") ? "audio/mpeg" : file.endsWith(".wav") ? "audio/wav" : "application/octet-stream";
    const headers = { "Content-Type": type, "Cache-Control": "private, max-age=3600" };
    if (download) headers["Content-Disposition"] = `attachment; filename="${name}"`;
    res.writeHead(200, headers);
    res.end(data);
  } catch {
    res.writeHead(404); res.end();
  }
}

export function createServer({ client, accessCode = process.env.CODE_ACCES || "", billing = null, stripe = null, env = process.env, dataDir = studio.DATA } = {}) {
  const jobs = new Jobs();
  /* Radar de tendances : un par utilisateur ; celui du propriétaire (« moi ») tourne chaque jour tout seul. */
  const radars = new Map();
  const radarOf = (uid) => {
    if (!radars.has(uid)) radars.set(uid, new Radar({ client, dir: path.join(dataDir, "radar", uid), env }));
    return radars.get(uid);
  };

  const dirs = { uploads: path.join(dataDir, "televersements"), out: path.join(dataDir, "sorties"), voix: path.join(dataDir, "voix") };
  const sale = Boolean(billing);
  if (!sale) radarOf("moi").schedule();
  setInterval(() => { studio.cleanup(dirs.out); studio.cleanup(dirs.uploads, 24); }, 3600_000).unref();

  /* Qui fait la demande : l'abonné (clé), ou « moi » en usage personnel. */
  function who(req) {
    if (!sale) return { id: "moi", key: null };
    const key = String(req.headers["x-cle"] || "");
    if (!billing.isActive(key)) return null;
    return { id: createHash("sha256").update(key).digest("hex").slice(0, 24), key };
  }
  function quota(user, type) {
    if (sale && !billing.consume(user.key, type)) throw new CoachError("quota", "Quota du mois atteint pour cette fonction. Il se renouvelle le 1er du mois.");
  }
  const uploadPath = async (user, id) => {
    if (!ID.test(id || "")) throw new CoachError("entree", "Fichier inconnu.");
    const dir = path.join(dirs.uploads, user.id);
    const f = (await readdir(dir).catch(() => [])).find((n) => n.startsWith(id + "."));
    if (!f) throw new CoachError("entree", "Fichier introuvable ou expiré. Téléversez-le à nouveau.");
    return path.join(dir, f);
  };
  const sampleOf = (user) => path.join(dirs.voix, user.id + ".wav");
  const hasSample = async (user) => Boolean(await stat(sampleOf(user)).catch(() => null));

  async function handle(req, res, url) {
    const p = url.pathname;

    if (p === "/api/sante") {
      return send(res, 200, {
        ok: true, code_requis: Boolean(accessCode) && !sale, vente: sale, prix: env.PRIX_AFFICHE || "1,99 € / mois",
        moteurs_voix: enginesAvailable(env), clonage: cloneEngines(env), voix: VOICES, quotas: sale ? QUOTAS : null
      });
    }

    /* Déclenchement du radar par un robot externe (GitHub Actions, cron) avec un jeton secret. */
    if (p === "/api/radar/declencher" && req.method === "POST") {
      if (!env.RADAR_JETON || req.headers["x-jeton-radar"] !== env.RADAR_JETON) return send(res, 401, { erreur: "Jeton invalide." });
      const r = radarOf("moi");
      if (url.searchParams.has("attendre")) return send(res, 200, await r.run());
      r.run().catch(() => {});
      return send(res, 202, { lance: true });
    }

    /* Abonnement */
    if (p === "/api/stripe/webhook" && req.method === "POST") {
      if (!sale) return send(res, 404, { erreur: "Vente désactivée." });
      const raw = await readRaw(req, 1024 * 1024);
      try {
        billing.handleEvent(stripe.webhooks.constructEvent(raw, req.headers["stripe-signature"], env.STRIPE_WEBHOOK_SECRET));
        return send(res, 200, { recu: true });
      } catch { return send(res, 400, { erreur: "Signature invalide." }); }
    }
    if (p.startsWith("/api/abonnement/")) {
      if (!sale) return send(res, 404, { erreur: "Vente désactivée sur ce serveur." });
      const b = req.method === "POST" ? await readBody(req) : {};
      if (p === "/api/abonnement/payer") return send(res, 200, { url: await billing.checkout() });
      if (p === "/api/abonnement/activer") {
        try { return send(res, 200, { cle: await billing.activate(str(b.session, 300)) }); }
        catch (e) { return send(res, 400, { erreur: e.message }); }
      }
      const key = String(req.headers["x-cle"] || "");
      if (!billing.subscriber(key)) return send(res, 401, { erreur: "Clé d'abonnement inconnue." });
      if (p === "/api/abonnement/etat") return send(res, 200, { actif: billing.isActive(key), usage: billing.usage(key) });
      if (p === "/api/abonnement/portail") return send(res, 200, { url: await billing.portal(key) });
      return send(res, 404, { erreur: "Service inconnu." });
    }

    /* Accès */
    if (!sale && accessCode && req.headers["x-code-acces"] !== accessCode) return send(res, 401, { erreur: "Code d'accès incorrect." });
    const user = who(req);
    if (!user) return send(res, 402, { erreur: "Abonnement requis.", abonnement: true });

    /* Fichiers produits */
    const fm = /^\/api\/fichiers\/([a-f0-9]{24}(?:-voix)?\.(?:mp4|mp3|wav))$/.exec(p);
    if (fm && req.method === "GET") {
      const job = [...jobs.jobs.values()].find((j) => j.owner === user.id && j.resultat && Object.values(j.resultat).includes(fm[1]));
      if (!job) return send(res, 404, { erreur: "Fichier introuvable." });
      return serveFile(res, path.join(dirs.out, fm[1]), fm[1], url.searchParams.has("telecharger"));
    }

    /* Suivi d'une fabrication */
    const jm = /^\/api\/travaux\/([a-f0-9]{24})$/.exec(p);
    if (jm && req.method === "GET") {
      const j = jobs.get(jm[1], user.id);
      if (!j) return send(res, 404, { erreur: "Travail introuvable." });
      return send(res, 200, { id: j.id, etat: j.etat, etape: j.etape, resultat: j.resultat, erreur: j.erreur });
    }

    /* Téléversement brut (vidéo, image, son) */
    if (p === "/api/fichier" && req.method === "POST") {
      const ext = UPLOAD_TYPES[String(req.headers["content-type"] || "").split(";")[0]];
      if (!ext) return send(res, 415, { erreur: "Type de fichier non pris en charge." });
      const data = await readRaw(req, MAX_UPLOAD);
      if (!data.length) return send(res, 400, { erreur: "Fichier vide." });
      const id = studio.newId();
      const dir = path.join(dirs.uploads, user.id);
      await mkdir(dir, { recursive: true });
      await writeFile(path.join(dir, id + ext), data);
      return send(res, 200, { id });
    }

    /* Voix : échantillon de clonage */
    if (p === "/api/voix/phrase" && req.method === "GET") {
      return send(res, 200, consentSentence(lang(url.searchParams.get("langue"))));
    }
    if (p === "/api/voix/echantillon") {
      if (req.method === "GET") return send(res, 200, { enregistre: await hasSample(user) });
      if (req.method === "DELETE") { await rm(sampleOf(user), { force: true }); return send(res, 200, { supprime: true }); }
    }

    if (p === "/api/radar" && req.method === "GET") {
      const r = radarOf(user.id);
      const niches = await r.niches();
      const resultats = {};
      for (const n of niches) resultats[n.nom] = (await r.results(n.nom))[0] || null;
      return send(res, 200, { niches, resultats, en_cours: r.running, planifie: !sale && Boolean(env.RADAR_HEURE) });
    }

    if (req.method !== "POST") return send(res, 405, { erreur: "Méthode non permise." });
    const ip = req.socket.remoteAddress || "?";
    if (!allowed(ip, Date.now(), Number(env.LIMITE_PAR_HEURE || 60))) return send(res, 429, { erreur: "Limite de demandes atteinte pour cette heure." });
    const b = await readBody(req);

    if (p === "/api/voix/echantillon") {
      if (b.consentement !== true) return send(res, 400, { erreur: "Cochez la case : vous confirmez que c'est votre propre voix." });
      const src = await uploadPath(user, b.fichier);
      await mkdir(dirs.voix, { recursive: true });
      const duree = await prepareSample(src, sampleOf(user)).catch((e) => { throw new CoachError("entree", e.message); });
      await rm(src, { force: true });
      return send(res, 200, { enregistre: true, duree });
    }

    if (p === "/api/voix/essai") {
      quota(user, "voix");
      const texte = str(b.texte, 600);
      if (!texte) return send(res, 400, { erreur: "Écrivez un texte à lire." });
      const opts = { moteur: str(b.moteur, 20), voix: str(b.voix, 60), langue: lang(b.langue), echantillon: (await hasSample(user)) ? sampleOf(user) : null };
      const job = jobs.add(user.id, async () => {
        const id = studio.newId();
        await mkdir(dirs.out, { recursive: true });
        const wav = path.join(dirs.out, id + ".wav");
        await synthesize(texte, wav, opts, env).catch((e) => { throw new CoachError("voix", e.message); });
        const mp3 = path.join(dirs.out, id + "-voix.mp3");
        await runCmd("ffmpeg", ["-y", "-loglevel", "error", "-i", wav, "-b:a", "160k", mp3]);
        return { wav: id + ".wav", voix: id + "-voix.mp3" };
      });
      return send(res, 202, { travail: job.id });
    }

    if (p === "/api/studio/analyser") {
      quota(user, "analyse");
      const work = path.join(dataDir, "travail", studio.newId());
      await mkdir(work, { recursive: true });
      try {
        let file;
        if (b.lien) file = await studio.download(str(b.lien, 1000), work);
        else file = await uploadPath(user, b.fichier);
        const ex = await studio.extract(file, work);
        const out = await studio.analyze(client, { ...ex, consigne: str(b.consigne, 1000), sujet: str(b.sujet, 300), langue: lang(b.langue) });
        return send(res, 200, { ...out, transcription: ex.transcription, duree: ex.duree });
      } finally {
        await rm(work, { recursive: true, force: true });
      }
    }

    if (p === "/api/studio/creer") {
      quota(user, "analyse");
      const sujet = str(b.sujet, 300);
      if (!sujet) return send(res, 400, { erreur: "Indiquez le sujet de la vidéo." });
      return send(res, 200, await studio.create(client, { sujet, consigne: str(b.consigne, 1000), langue: lang(b.langue) }));
    }

    if (p === "/api/studio/style") {
      quota(user, "analyse");
      const imgs = images(b.images);
      if (!imgs.length) return send(res, 400, { erreur: "Ajoutez au moins une image de référence." });
      return send(res, 200, await studio.styleFromImage(client, { images: imgs, langue: lang(b.langue) }));
    }

    if (p === "/api/studio/fabriquer") {
      quota(user, "video");
      const gabarit = ["face_camera", "clips"].includes(b.gabarit) ? b.gabarit : "citation";
      const style = typeof b.style === "object" && b.style ? b.style : {};
      if (gabarit === "clips") {
        const video = await uploadPath(user, b.video);
        const job = jobs.add(user.id, (step) => studio.produceClips(client, video, { nombre: b.nombre, langue: lang(b.langue), style }, dirs.out, renderFacecam, step));
        return send(res, 202, { travail: job.id });
      }
      if (gabarit === "face_camera") {
        const video = await uploadPath(user, b.video);
        const langue = lang(b.langue);
        const job = jobs.add(user.id, async (step) => {
          const work = path.join(dataDir, "travail", studio.newId());
          await mkdir(work, { recursive: true });
          try {
            step("Transcription mot à mot");
            const mots = await studio.transcribeWords(video, work).catch(() => { throw new CoachError("transcription", "Transcription impossible : installez faster-whisper sur le serveur (voir le guide)."); });
            step("Titres");
            const titres = b.titres === false ? { titres: [] } : await studio.titlesFor(client, { mots, langue });
            step("Montage");
            await mkdir(dirs.out, { recursive: true });
            const id = studio.newId();
            await renderFacecam(video, mots, titres.titres, style, path.join(dirs.out, id + ".mp4"));
            return { video: id + ".mp4" };
          } finally { await rm(work, { recursive: true, force: true }); }
        });
        return send(res, 202, { travail: job.id });
      }
      const parsed = NewVersion.safeParse(b.version);
      if (!parsed.success || !parsed.data.scenes.length || parsed.data.scenes.length > 8) return send(res, 400, { erreur: "Version de vidéo invalide." });
      const imgs = {};
      for (const [k, v] of Object.entries(b.images || {})) if (v) imgs[k] = await uploadPath(user, v);
      const musique = b.musique ? await uploadPath(user, b.musique) : null;
      const opts = {
        moteur: str(b.moteur, 20) || "kokoro", voix: str(b.voix, 60), langue: lang(b.langue), images: imgs, musique,
        echantillon: (await hasSample(user)) ? sampleOf(user) : null,
        style: { couleur: style.couleur, taille: Number(style.taille) || undefined, zoom: style.zoom }, env
      };
      const job = jobs.add(user.id, (step) => studio.produce(parsed.data, opts, dirs.out, step));
      return send(res, 202, { travail: job.id });
    }

    if (p === "/api/radar/niches") {
      const list = (Array.isArray(b.niches) ? b.niches : []).slice(0, 5).map((n) => ({
        nom: str(n?.nom, 80), public: str(n?.public, 200), langue: lang(n?.langue),
        subreddits: (Array.isArray(n?.subreddits) ? n.subreddits : String(n?.subreddits || "").split(/[ ,]+/))
          .map((x) => String(x).replace(/^r\//, "").trim()).filter((x) => /^[A-Za-z0-9_]{2,30}$/.test(x)).slice(0, 5)
      })).filter((n) => n.nom);
      await radarOf(user.id).saveNiches(list);
      return send(res, 200, { niches: list });
    }
    if (p === "/api/radar/lancer") {
      const r = radarOf(user.id);
      const only = str(b.niche, 80) || null;
      const count = only ? 1 : (await r.niches()).length;
      if (!count) return send(res, 400, { erreur: "Ajoutez d'abord une niche." });
      for (let i = 0; i < count; i++) quota(user, "analyse");
      if (r.running) return send(res, 409, { erreur: "Le radar est déjà en train de chercher." });
      r.run(only).catch(() => {});
      return send(res, 202, { lance: true });
    }

    /* Coach */
    const route = routes[p.slice(5)];
    if (!route) return send(res, 404, { erreur: "Service inconnu." });
    const call = route(b);
    quota(user, "analyse");
    return send(res, 200, await call(client));
  }

  return http.createServer(async (req, res) => {
    const url = new URL(req.url, "http://x");
    if (!url.pathname.startsWith("/api/")) {
      if (req.method !== "GET" && req.method !== "HEAD") { res.writeHead(405); res.end(); return; }
      return serveStatic(req, res);
    }
    try {
      await handle(req, res, url);
    } catch (e) {
      if (!(e instanceof CoachError)) console.error(e);
      const [status, obj] = e instanceof CoachError && e.code === "quota" ? [429, { erreur: e.message }] : errorReply(e);
      if (!res.headersSent) send(res, status, obj);
    }
  });
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  if (!process.env.ANTHROPIC_API_KEY) console.warn("Attention : ANTHROPIC_API_KEY n'est pas définie, l'IA ne répondra pas.");
  let billing = null, stripe = null;
  if (process.env.VENTE === "1") {
    const { default: Stripe } = await import("stripe");
    const { Billing, openDb } = await import("./lib/billing.mjs");
    stripe = new Stripe(process.env.STRIPE_SECRET_KEY);
    billing = new Billing({ db: openDb(path.join(studio.DATA, "abonnes.sqlite")), stripe, price: process.env.STRIPE_PRIX, publicUrl: process.env.URL_PUBLIQUE });
  }
  const port = Number(process.env.PORT || 8080);
  createServer({ client: new Anthropic(), billing, stripe }).listen(port, process.env.HOST || undefined, () => console.log(`Coach viral prêt sur http://localhost:${port}`));
}
