/* Abonnement (Stripe) : paiement mensuel, clé d'abonnement, quotas du mois.
   Pas de mot de passe : après le paiement, l'appareil reçoit une clé secrète qu'il garde.
   Les données tiennent dans un fichier SQLite. */
import { DatabaseSync } from "node:sqlite";
import { mkdirSync } from "node:fs";
import path from "node:path";
import { randomBytes, createHash } from "node:crypto";

export const QUOTAS = {
  analyse: Number(process.env.QUOTA_ANALYSES || 60),   // demandes au coach (idées, score, profil, studio)
  video: Number(process.env.QUOTA_VIDEOS || 30),       // vidéos fabriquées
  voix: Number(process.env.QUOTA_VOIX || 60)           // voix off d'essai
};

const hash = (k) => createHash("sha256").update(k).digest("hex");
const month = (d = new Date()) => d.toISOString().slice(0, 7);

export function openDb(file) {
  if (file !== ":memory:") mkdirSync(path.dirname(file), { recursive: true });
  const db = new DatabaseSync(file);
  db.exec(`
    CREATE TABLE IF NOT EXISTS abonnes (
      cle_hash TEXT PRIMARY KEY,
      session TEXT UNIQUE,
      client TEXT,
      abonnement TEXT,
      statut TEXT NOT NULL,
      cree TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS usage (
      cle_hash TEXT NOT NULL, mois TEXT NOT NULL, type TEXT NOT NULL, n INTEGER NOT NULL DEFAULT 0,
      PRIMARY KEY (cle_hash, mois, type)
    );`);
  return db;
}

export class Billing {
  constructor({ db, stripe, price, publicUrl }) {
    this.db = db;
    this.stripe = stripe;
    this.price = price;
    this.publicUrl = (publicUrl || "").replace(/\/$/, "");
  }

  async checkout() {
    const s = await this.stripe.checkout.sessions.create({
      mode: "subscription",
      line_items: [{ price: this.price, quantity: 1 }],
      success_url: this.publicUrl + "/?abonnement={CHECKOUT_SESSION_ID}",
      cancel_url: this.publicUrl + "/?abonnement=annule",
      allow_promotion_codes: true
    });
    return s.url;
  }

  /* Après le paiement : vérifie la session chez Stripe et donne une clé (une seule fois par session). */
  async activate(sessionId) {
    if (!/^cs_[A-Za-z0-9_]+$/.test(sessionId || "")) throw new Error("Session de paiement invalide.");
    const already = this.db.prepare("SELECT 1 FROM abonnes WHERE session = ?").get(sessionId);
    if (already) throw new Error("Cette clé a déjà été remise. Utilisez « Retrouver ma clé » via le lien d'abonnement si vous l'avez perdue.");
    const s = await this.stripe.checkout.sessions.retrieve(sessionId);
    if (s.status !== "complete" || !s.subscription) throw new Error("Le paiement n'est pas terminé.");
    const key = "cv_" + randomBytes(24).toString("base64url");
    const sub = typeof s.subscription === "string" ? s.subscription : s.subscription.id;
    const customer = typeof s.customer === "string" ? s.customer : s.customer?.id;
    this.db.prepare("INSERT INTO abonnes (cle_hash, session, client, abonnement, statut, cree) VALUES (?, ?, ?, ?, ?, ?)")
      .run(hash(key), sessionId, customer || null, sub, "active", new Date().toISOString());
    return key;
  }

  subscriber(key) {
    if (!key || !key.startsWith("cv_")) return null;
    return this.db.prepare("SELECT * FROM abonnes WHERE cle_hash = ?").get(hash(key)) || null;
  }

  isActive(key) {
    const s = this.subscriber(key);
    return Boolean(s && (s.statut === "active" || s.statut === "trialing"));
  }

  /* Compte une utilisation ; renvoie false si le quota du mois est atteint. */
  consume(key, type, now = new Date()) {
    const h = hash(key), m = month(now);
    const row = this.db.prepare("SELECT n FROM usage WHERE cle_hash = ? AND mois = ? AND type = ?").get(h, m, type);
    if ((row?.n || 0) >= QUOTAS[type]) return false;
    this.db.prepare("INSERT INTO usage (cle_hash, mois, type, n) VALUES (?, ?, ?, 1) ON CONFLICT(cle_hash, mois, type) DO UPDATE SET n = n + 1").run(h, m, type);
    return true;
  }

  usage(key, now = new Date()) {
    const rows = this.db.prepare("SELECT type, n FROM usage WHERE cle_hash = ? AND mois = ?").all(hash(key), month(now));
    const used = Object.fromEntries(rows.map((r) => [r.type, r.n]));
    return Object.fromEntries(Object.keys(QUOTAS).map((t) => [t, { utilise: used[t] || 0, max: QUOTAS[t] }]));
  }

  async portal(key) {
    const s = this.subscriber(key);
    if (!s?.client) throw new Error("Abonnement introuvable.");
    const p = await this.stripe.billingPortal.sessions.create({ customer: s.client, return_url: this.publicUrl + "/" });
    return p.url;
  }

  /* Événements envoyés par Stripe (signature vérifiée par l'appelant). */
  handleEvent(event) {
    if (event.type.startsWith("customer.subscription.")) {
      const sub = event.data.object;
      this.db.prepare("UPDATE abonnes SET statut = ? WHERE abonnement = ?").run(sub.status, sub.id);
    }
  }
}
