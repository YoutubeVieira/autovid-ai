#!/usr/bin/env node
/* Tests sans réseau ni navigateur : WAV, découpe des sous-titres, validité des projets. Usage : node tools/test.mjs */
import assert from "node:assert";
import fs from "node:fs";
import path from "node:path";
import { plan } from "./daily-plan.mjs";
import { parsePexelsPhotos, parsePexelsVideos, parsePixabayPhotos, parsePixabayVideos, mention } from "./media-search.mjs";
import { summarize } from "./tts-usage.mjs";
import { root, loadVoice, splitByPauses, wav, readWav, wavSeconds, chunkWords, chunkTimings } from "./lib.mjs";

const pcm = Buffer.alloc(24000 * 2); // 1 s de silence à 24 kHz
assert.strictEqual(wavSeconds(wav(pcm, 24000)), 1);
assert.strictEqual(readWav(wav(pcm, 22050)).rate, 22050);

assert.deepStrictEqual(chunkWords("Em maio de 1940, a Alemanha invade a França."), ["Em maio de", "1940, a Alemanha", "invade a França."]);
const t = chunkTimings(["um dois", "três"], 3);
assert.strictEqual(t[0].from, 0);
assert.ok(Math.abs(t.at(-1).to - 3) < 0.01, "les sous-titres couvrent toute la durée");
assert.ok(t.every((c, i) => i === 0 || c.from >= t[i - 1].to - 1e-9), "sous-titres ordonnés");

const geo = JSON.parse(fs.readFileSync(path.join(root, "public/geo/europe.json"), "utf8"));
const ids = new Set(geo.features.map(f => f.properties.id));

for (const f of fs.readdirSync(path.join(root, "projects")).filter(f => f.endsWith(".json"))) {
  const p = JSON.parse(fs.readFileSync(path.join(root, "projects", f), "utf8"));
  const seen = new Set();
  for (const s of p.scenes) {
    assert.ok(!seen.has(s.id), f + " : scène en double " + s.id); seen.add(s.id);
    assert.ok(s.text && s.camera && s.camera.zoom > 0, f + " : scène " + s.id + " incomplète");
    for (const it of s.items || []) if (it.kind === "stat") assert.ok(typeof it.value === "number" && it.label, f + " : stat incomplète en " + s.id);
    for (const iso of Object.keys(s.fills || {})) assert.ok(ids.has(iso), f + " : pays inconnu " + iso);
  }
  if (p.theme === "finance") {  // une vidéo finance sans faits sourcés ne passe pas
    assert.ok(Array.isArray(p.faits) && p.faits.length > 0, f + " : projet finance sans registre « faits »");
    for (const x of p.faits) assert.ok(x.id && x.claim && x.source && /^\d{4}-\d{2}(-\d{2})?$/.test(x.date || ""), f + " : fait incomplet (id, claim, source, date AAAA-MM[-JJ]) : " + JSON.stringify(x).slice(0, 80));
    const fid = new Set(p.faits.map(x => x.id));
    for (const s of p.scenes) for (const r of s.faits || []) assert.ok(fid.has(r), f + " : scène " + s.id + " cite un fait inconnu " + r);
    for (const s of p.scenes) if (/\d/.test(s.text) || (s.items || []).some(i => i.kind === "stat")) assert.ok((s.faits || []).length, f + " : scène " + s.id + " contient un chiffre sans fait sourcé (champ faits)");
  }
}
assert.strictEqual(loadVoice("test").provider, "espeak");
assert.throws(() => loadVoice("inconnue"), /Voix inconnue/);
for (const f of fs.readdirSync(path.join(root, "projects")).filter(f => f.endsWith(".json")))
  loadVoice(JSON.parse(fs.readFileSync(path.join(root, "projects", f), "utf8")).voice || "test");
for (const n of ["whoosh", "pop", "impact", "ding", "riser", "bed"]) assert.ok(fs.existsSync(path.join(root, "public/sfx", n + ".wav")), "bruitage manquant : " + n);
assert.ok(fs.existsSync(path.join(root, "public/geo/basemap.jpg")), "fond de carte manquant : python3 tools/make-basemap.py");
{ // découpe par pauses : 3 « phrases » (tons) séparées par des silences de longueurs différentes
  const R = 24000, seg = (sec, f) => Buffer.concat([...Array(Math.round(sec * R))].map((_, i) => { const b = Buffer.alloc(2); b.writeInt16LE(Math.round(8000 * Math.sin(2 * Math.PI * f * i / R)), 0); return b; }));
  const sil = sec => Buffer.alloc(Math.round(sec * R) * 2);
  const audio = wav(Buffer.concat([seg(1.0, 300), sil(0.5), seg(2.0, 400), sil(0.3), seg(1.0, 500)]), R);
  const parts = splitByPauses(audio, ["un", "deux deux", "trois"]);
  assert.strictEqual(parts.length, 3);
  const d = parts.map(p => wavSeconds(p));
  assert.ok(Math.abs(d[0] - 1.25) < 0.1 && Math.abs(d[1] - 2.4) < 0.15, "découpe sur les silences : " + d.map(x => x.toFixed(2)).join(" "));
  assert.ok(Math.abs(d.reduce((a, b) => a + b, 0) - 4.8) < 0.01, "aucune perte d'audio");
}
for (const f of fs.readdirSync(path.join(root, "projects")).filter(f => f.endsWith(".json"))) {
  const p = JSON.parse(fs.readFileSync(path.join(root, "projects", f), "utf8"));
  for (const s of p.scenes) for (const it of s.items || []) if (it.kind === "media") {
    assert.ok(it.credit && it.credit.length > 3, f + " : média sans mention de source en " + s.id);
    assert.ok(fs.existsSync(path.join(root, "public", it.src)), f + " : fichier média introuvable " + it.src);
  }
}
{ // planificateur : alternance et liens long <-> short
  const serie = { dernier_type: "short", videos: [
    { id: "L1", type: "long", slug: "a", titre: "A", statut: "rendu", short_lie: "S1" },
    { id: "S1", type: "short", slug: "a-60s", statut: "a_faire", long_lie: "L1" },
    { id: "L2", type: "long", slug: "b", titre: "B", statut: "a_ecrire", short_lie: null },
    { id: "S9", type: "short", slug: "z", statut: "rendu", long_lie: null } ] };
  const j1 = plan(serie);
  assert.strictEqual(j1.job.jour, "longue"); assert.strictEqual(j1.job.id, "L2");
  assert.ok(j1.issues.some(i => /orphelin/.test(i)), "short orphelin signalé");
  const j2 = plan({ ...serie, dernier_type: "long" });
  assert.strictEqual(j2.job.jour, "short"); assert.strictEqual(j2.job.long_lie, "L1");
}
{ // compteur de voix : 3 requêtes le même jour (Pacifique) sur un modèle, 1 sur un autre
  const L = [{ ts: "2026-11-03T08:00:00Z", modele: "m1", projet: "a", caracteres: 100, secondes_audio: 10 }, { ts: "2026-11-03T20:00:00Z", modele: "m1", projet: "a", caracteres: 50, secondes_audio: 5 }, { ts: "2026-11-04T02:00:00Z", modele: "m1", projet: "b", caracteres: 10, secondes_audio: 1 }, { ts: "2026-11-03T09:00:00Z", modele: "m2", projet: "a", caracteres: 5, secondes_audio: 1 }];
  const r = summarize(L, 10);
  assert.strictEqual(r.find(x => x.jour_modele === "2026-11-03 | m1").requetes, 3, "02:00Z du 4 = 18:00 PST du 3");
  assert.strictEqual(r.find(x => x.jour_modele === "2026-11-03 | m1").reste_sur_limite, 7);
  assert.strictEqual(r.length, 2);
}
{ // analyseurs Pexels / Pixabay : réponses d'exemple (les vrais services n'ont pas pu être appelés)
  const pv = parsePexelsVideos({ videos: [{ id: 7, url: "https://www.pexels.com/video/7/", duration: 12, user: { name: "A. Dupont" }, video_files: [{ file_type: "video/mp4", width: 640, height: 360, link: "u640" }, { file_type: "video/mp4", width: 1920, height: 1080, link: "u1920" }, { file_type: "video/webm", width: 1920, height: 1080, link: "w" }] }] });
  assert.strictEqual(pv[0].fichier, "u1920"); assert.strictEqual(mention(pv[0]), "Pexels · A. Dupont");
  assert.strictEqual(parsePexelsPhotos({ photos: [{ id: 3, url: "p", photographer: "B", width: 10, height: 5, src: { large2x: "L" } }] })[0].fichier, "L");
  assert.strictEqual(parsePixabayPhotos({ hits: [{ id: 9, pageURL: "pg", user: "C", imageWidth: 4, imageHeight: 3, largeImageURL: "X" }] })[0].fichier, "X");
  assert.strictEqual(parsePixabayVideos({ hits: [{ id: 1, pageURL: "pg", user: "D", duration: 5, videos: { medium: { url: "M", width: 1280, height: 720 } } }] })[0].fichier, "M");
  assert.deepStrictEqual(parsePexelsVideos({}), []);
}
// médias sous public/media : une entrée du registre (licence + mention) est obligatoire
{
  const mf = path.join(root, "media-manifest.json"), reg = fs.existsSync(mf) ? JSON.parse(fs.readFileSync(mf, "utf8")).medias : [];
  for (const f of fs.readdirSync(path.join(root, "projects")).filter(f => f.endsWith(".json"))) {
    const p = JSON.parse(fs.readFileSync(path.join(root, "projects", f), "utf8"));
    for (const s of p.scenes) for (const it of s.items || []) if (it.kind === "media" && it.src.startsWith("media/")) assert.ok(reg.some(x => x.src === it.src && x.licence && x.mention), f + " : média " + it.src + " absent de media-manifest.json (licence et mention)");
  }
}
console.log("Tests OK");
