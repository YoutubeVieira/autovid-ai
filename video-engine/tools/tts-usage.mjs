#!/usr/bin/env node
/* Consommation de la voix Gemini : requêtes réussies par jour (heure du Pacifique, comme le quota de Google) et par modèle,
   d'après serie/tts-usage.jsonl (écrit par tools/tts.mjs à chaque requête réussie). Ne contient ni clé ni texte.
   Limite du compte gratuit mesurée : 10 requêtes par jour et par modèle. Usage : node tools/tts-usage.mjs [--limite 10] */
import fs from "node:fs";
import path from "node:path";
import { root } from "./lib.mjs";

export function summarize(lines, limit = 10, tz = "America/Los_Angeles") {
  const day = ts => new Date(ts).toLocaleDateString("en-CA", { timeZone: tz });
  const out = {};
  for (const l of lines) {
    const k = day(l.ts) + " | " + l.modele;
    const o = (out[k] = out[k] || { requetes: 0, caracteres: 0, secondes_audio: 0, projets: new Set() });
    o.requetes++; o.caracteres += l.caracteres || 0; o.secondes_audio += l.secondes_audio || 0; o.projets.add(l.projet);
  }
  return Object.entries(out).sort().map(([k, o]) => ({ jour_modele: k, requetes: o.requetes, reste_sur_limite: Math.max(0, limit - o.requetes), caracteres: o.caracteres, secondes_audio: +o.secondes_audio.toFixed(0), projets: [...o.projets] }));
}

if (import.meta.url === "file://" + process.argv[1]) {
  const f = path.join(root, "serie", "tts-usage.jsonl");
  const li = process.argv.indexOf("--limite"), limit = li > 0 ? Number(process.argv[li + 1]) : 10;
  if (!fs.existsSync(f)) { console.log("Aucune requête enregistrée depuis l'ajout du compteur."); process.exit(0); }
  const lines = fs.readFileSync(f, "utf8").split("\n").filter(Boolean).map(x => JSON.parse(x));
  for (const r of summarize(lines, limit)) console.log(r.jour_modele.padEnd(44) + String(r.requetes).padStart(3) + " requête(s), reste " + r.reste_sur_limite + "/" + limit + " ; " + r.caracteres + " caractères ; " + r.secondes_audio + " s d'audio ; " + r.projets.join(", "));
}
