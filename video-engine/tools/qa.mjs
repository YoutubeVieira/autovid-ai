#!/usr/bin/env node
/* Contrôle qualité d'une vidéo rendue AVANT le montage final / la publication.
   Mesure : durée, résolution, audio (pic, volume moyen), silences longs, images noires, poids ; puis contrôles du projet
   (npm test, mentions obligatoires pour un sujet finance). Écrit .cache/qa/<nom>.json ; code de sortie 1 s'il y a un ÉCHEC.
   Ce que l'outil NE fait PAS : juger le fond (exactitude des faits : agent verificateur-faits), ni le style, ni l'écoute.
   Usage : node tools/qa.mjs <fichier.mp4> [--projet <slug>] [--cible <secondes>] */
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { root } from "./lib.mjs";

const args = process.argv.slice(2);
const file = args[0];
const opt = f => { const i = args.indexOf(f); return i > 0 ? args[i + 1] : null; };
if (!file || !fs.existsSync(file)) { console.log("Usage : node tools/qa.mjs <fichier.mp4> [--projet slug] [--cible s]"); process.exit(1); }
const slug = opt("--projet"), cible = opt("--cible") ? Number(opt("--cible")) : null;
const run = (c, a) => spawnSync(c, a, { encoding: "utf8", maxBuffer: 1 << 26 });
const checks = [];
const add = (nom, niveau, detail) => checks.push({ nom, niveau, detail });   // niveau : OK | AVERTISSEMENT | ECHEC

const probe = JSON.parse(run("ffprobe", ["-v", "error", "-print_format", "json", "-show_format", "-show_streams", file]).stdout || "{}");
const v = (probe.streams || []).find(s => s.codec_type === "video"), a = (probe.streams || []).find(s => s.codec_type === "audio");
const dur = Number(probe.format?.duration || 0);
add("Durée", cible ? (Math.abs(dur - cible) / cible <= 0.1 ? "OK" : "AVERTISSEMENT") : "OK", dur.toFixed(1) + " s" + (cible ? " (cible " + cible + " s, tolérance 10 %)" : ""));
const fmt = v ? (v.width + "x" + v.height) : "?";
add("Résolution", v && ((v.width === 1080 && v.height === 1920) || (v.width === 1920 && v.height === 1080)) ? "OK" : "ECHEC", fmt);
if (!a) add("Audio", "ECHEC", "aucune piste audio");
else {
  const vd = run("ffmpeg", ["-i", file, "-af", "volumedetect", "-vn", "-f", "null", "-"]).stderr;
  const max = Number(/max_volume: (-?[\d.]+)/.exec(vd)?.[1]), mean = Number(/mean_volume: (-?[\d.]+)/.exec(vd)?.[1]);
  add("Pic audio", max > -1.0 ? "AVERTISSEMENT" : "OK", max + " dB (au-dessus de −1 dB : risque de saturation)");
  add("Volume moyen", mean < -26 || mean > -14 ? "AVERTISSEMENT" : "OK", mean + " dB (cible −24 à −16 dB)");
  const sd = run("ffmpeg", ["-i", file, "-af", "silencedetect=noise=-45dB:d=2.5", "-vn", "-f", "null", "-"]).stderr;
  const n = (sd.match(/silence_start/g) || []).length;
  add("Silences > 2,5 s", n ? "AVERTISSEMENT" : "OK", n + " trouvé(s)");
}
const bd = run("ffmpeg", ["-i", file, "-an", "-vf", "blackdetect=d=0.5:pix_th=0.05", "-f", "null", "-"]).stderr;
const nb = (bd.match(/black_start/g) || []).length;
add("Images noires", nb ? "AVERTISSEMENT" : "OK", nb + " séquence(s) de plus de 0,5 s");
const mb = fs.statSync(file).size / 1e6;
add("Poids", mb > 500 ? "AVERTISSEMENT" : "OK", mb.toFixed(0) + " Mo");

if (slug) {
  const pf = path.join(root, "projects", slug + ".json");
  if (!fs.existsSync(pf)) add("Projet", "ECHEC", "introuvable : " + pf);
  else {
    const p = JSON.parse(fs.readFileSync(pf, "utf8"));
    const t = run("node", [path.join(root, "tools/test.mjs")]);
    add("npm test (JSON, faits, médias, voix)", t.status === 0 ? "OK" : "ECHEC", t.status === 0 ? "ok" : (t.stderr || t.stdout).split("\n").find(l => /Error|erreur/i.test(l)) || "échec");
    const all = JSON.stringify(p.scenes).toLowerCase();
    if (p.theme === "finance") {
      add("Mention « pas un conseil en investissement »", /conseil en investissement/.test(all) ? "OK" : "ECHEC", "dans le texte ou un bandeau");
      add("Mention « aucune obligation d'achat »", /obligation d'achat/.test(all) ? "OK" : "AVERTISSEMENT", "dans le texte ou un bandeau");
      const nonConf = (p.faits || []).filter(f => f.statut === "a_confirmer");
      add("Faits à confirmer à la source", nonConf.length ? "AVERTISSEMENT" : "OK", nonConf.length + " fait(s) « a_confirmer » : " + nonConf.map(f => f.id).join(", "));
    }
    const media = p.scenes.flatMap(s => (s.items || []).filter(i => i.kind === "media"));
    add("Médias déposés", "OK", media.length + " média(s), tous avec mention de source (vérifié par npm test)");
  }
}
const fail = checks.filter(c => c.niveau === "ECHEC").length, warn = checks.filter(c => c.niveau === "AVERTISSEMENT").length;
const report = { fichier: path.basename(file), verdict: fail ? "BLOQUÉ" : warn ? "À RELIRE" : "PRÊT POUR LE MONTAGE FINAL", echecs: fail, avertissements: warn, controles: checks };
fs.mkdirSync(path.join(root, ".cache/qa"), { recursive: true });
fs.writeFileSync(path.join(root, ".cache/qa", path.basename(file).replace(/\.[^.]+$/, "") + ".json"), JSON.stringify(report, null, 1));
for (const c of checks) console.log((c.niveau === "OK" ? "  ok   " : c.niveau === "ECHEC" ? "  ECHEC" : "  avert") + "  " + c.nom + " : " + c.detail);
console.log("Verdict : " + report.verdict + " (" + fail + " échec(s), " + warn + " avertissement(s)). L'écoute, la relecture des faits et le regard sur les images restent à faire.");
process.exit(fail ? 1 : 0);
