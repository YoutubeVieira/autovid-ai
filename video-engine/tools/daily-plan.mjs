#!/usr/bin/env node
/* Planificateur quotidien : dit quoi produire aujourd'hui, d'après serie/serie.json.
   Alternance : après un short -> une longue ; après une longue -> un short lié à cette longue.
   Un short sans longue liée est signalé (« orphelin ») : il faut le rattacher avant publication.
   Usage : node tools/daily-plan.mjs [--json] */
import fs from "node:fs";
import path from "node:path";
import { root } from "./lib.mjs";

export function plan(serie) {
  const v = serie.videos, byId = Object.fromEntries(v.map(x => [x.id, x]));
  const issues = [];
  for (const x of v) {
    if (x.type === "short" && (!x.long_lie || !byId[x.long_lie])) issues.push("Short orphelin : " + x.id + " (" + x.slug + ") n'est lié à aucune longue.");
    if (x.type === "long" && x.short_lie && (!byId[x.short_lie] || byId[x.short_lie].long_lie !== x.id)) issues.push("Lien incohérent entre " + x.id + " et " + x.short_lie + ".");
  }
  const todo = ["publie", "rendu"];
  let job;
  if (serie.dernier_type === "short") {
    const l = v.find(x => x.type === "long" && x.statut === "a_ecrire") || v.find(x => x.type === "long" && x.statut === "script_valide") || v.find(x => x.type === "long" && x.statut === "idee");
    job = l ? { jour: "longue", id: l.id, slug: l.slug, titre: l.titre, etape: l.statut === "idee" ? "veille + fiche d'impact + script" : l.statut === "a_ecrire" ? "script + voix + rendu" : "voix + rendu", short_a_deriver: l.short_lie } : { jour: "longue", id: null, etape: "veille : aucune longue en attente, chercher un sujet (skill veille-sujets-finance)" };
  } else {
    const l = [...v].reverse().find(x => x.type === "long" && todo.includes(x.statut) && x.short_lie && byId[x.short_lie] && !todo.includes(byId[x.short_lie].statut));
    const l2 = l || [...v].reverse().find(x => x.type === "long" && todo.includes(x.statut) && !x.short_lie);
    job = l2 ? { jour: "short", id: l2.short_lie || null, long_lie: l2.id, slug: l2.short_lie ? byId[l2.short_lie].slug : null, etape: "extraire un chapitre de " + l2.id + " (" + l2.titre + ") : script 60 s, fin avec renvoi vers la longue" } : { jour: "short", id: null, etape: "aucune longue terminée à décliner : produire une longue d'abord" };
  }
  return { job, issues };
}

if (import.meta.url === "file://" + process.argv[1]) {
  const serie = JSON.parse(fs.readFileSync(path.join(root, "serie/serie.json"), "utf8"));
  const r = plan(serie);
  if (process.argv.includes("--json")) console.log(JSON.stringify(r, null, 1));
  else { console.log("Aujourd'hui : " + r.job.jour.toUpperCase() + (r.job.id ? " " + r.job.id : "") + " : " + r.job.etape); for (const i of r.issues) console.log("  ! " + i); }
}
