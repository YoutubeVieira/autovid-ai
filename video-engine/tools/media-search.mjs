#!/usr/bin/env node
/* Recherche et téléchargement d'images / vidéos libres (Pexels, Pixabay) avec registre de licences et de mentions.
   Clés lues dans l'environnement (JAMAIS dans un fichier ni dans le dépôt) : PEXELS_API_KEY, PIXABAY_API_KEY.
   Rien n'est téléchargé sans --telecharger ; chaque téléchargement écrit une entrée dans media-manifest.json
   (source, auteur, licence, mention) que le test et le contrôle qualité exigent.

   Chercher :      node tools/media-search.mjs pexels video "terre depuis l'espace" [--n 6] [--orientation landscape]
   Télécharger :   node tools/media-search.mjs pexels video "terre depuis l'espace" --telecharger <id>
   Puis, dans un projet :  { "kind": "media", "src": "media/pexels-<id>.mp4", "credit": "<mention affichée>" }
   NON TESTÉ avec les vrais services (réseau bloqué dans la session de développement) : les analyseurs de réponses sont testés
   avec des réponses d'exemple ; les formats réels peuvent différer légèrement. */
import fs from "node:fs";
import path from "node:path";
import { root } from "./lib.mjs";

/* ---- analyseurs (purs, testés) ---- */
export function parsePexelsPhotos(j) {
  return (j.photos || []).map(p => ({ provider: "pexels", type: "photo", id: String(p.id), page: p.url, auteur: p.photographer, largeur: p.width, hauteur: p.height, fichier: p.src?.large2x || p.src?.original, ext: "jpg" }));
}
export function parsePexelsVideos(j) {
  return (j.videos || []).map(v => {
    const f = (v.video_files || []).filter(x => x.file_type === "video/mp4").sort((a, b) => Math.abs(a.width - 1920) - Math.abs(b.width - 1920))[0];
    return f && { provider: "pexels", type: "video", id: String(v.id), page: v.url, auteur: v.user?.name, largeur: f.width, hauteur: f.height, duree_s: v.duration, fichier: f.link, ext: "mp4" };
  }).filter(Boolean);
}
export function parsePixabayPhotos(j) {
  return (j.hits || []).map(h => ({ provider: "pixabay", type: "photo", id: String(h.id), page: h.pageURL, auteur: h.user, largeur: h.imageWidth, hauteur: h.imageHeight, fichier: h.largeImageURL, ext: "jpg" }));
}
export function parsePixabayVideos(j) {
  return (j.hits || []).map(h => {
    const f = h.videos?.large?.url ? h.videos.large : h.videos?.medium;
    return f && { provider: "pixabay", type: "video", id: String(h.id), page: h.pageURL, auteur: h.user, largeur: f.width, hauteur: f.height, duree_s: h.duration, fichier: f.url, ext: "mp4" };
  }).filter(Boolean);
}
export const licence = p => p === "pexels" ? "Licence Pexels (usage libre, gratuit ; mention du site et de l'auteur recommandée, obligatoire via l'API)" : "Licence de contenu Pixabay (usage libre, gratuit ; mention non obligatoire, appréciée)";
export const mention = it => (it.provider === "pexels" ? "Pexels" : "Pixabay") + " · " + (it.auteur || "auteur inconnu");

/* ---- accès réseau ---- */
async function search(provider, type, q, n, orientation) {
  if (provider === "pexels") {
    const key = process.env.PEXELS_API_KEY; if (!key) throw new Error("Variable PEXELS_API_KEY absente (réglages de l'environnement).");
    const url = (type === "video" ? "https://api.pexels.com/videos/search" : "https://api.pexels.com/v1/search") + "?query=" + encodeURIComponent(q) + "&per_page=" + n + "&orientation=" + orientation;
    const r = await fetch(url, { headers: { Authorization: key } });
    if (!r.ok) throw new Error("Pexels : HTTP " + r.status);
    const j = await r.json(); return type === "video" ? parsePexelsVideos(j) : parsePexelsPhotos(j);
  }
  const key = process.env.PIXABAY_API_KEY; if (!key) throw new Error("Variable PIXABAY_API_KEY absente (réglages de l'environnement).");
  const base = type === "video" ? "https://pixabay.com/api/videos/" : "https://pixabay.com/api/";
  const r = await fetch(base + "?key=" + encodeURIComponent(key) + "&q=" + encodeURIComponent(q) + "&per_page=" + Math.max(3, n) + (type === "photo" ? "&image_type=photo&orientation=" + (orientation === "landscape" ? "horizontal" : "vertical") : ""));
  if (!r.ok) throw new Error("Pixabay : HTTP " + r.status);
  const j = await r.json(); return type === "video" ? parsePixabayVideos(j) : parsePixabayPhotos(j);
}

if (import.meta.url === "file://" + process.argv[1]) {
  const a = process.argv.slice(2), [provider, type, q] = a;
  const opt = (f, d) => { const i = a.indexOf(f); return i > 0 ? a[i + 1] : d; };
  if (!["pexels", "pixabay"].includes(provider) || !["photo", "video"].includes(type) || !q) { console.log("Usage : node tools/media-search.mjs <pexels|pixabay> <photo|video> \"requête\" [--n 6] [--orientation landscape|portrait] [--telecharger <id>]"); process.exit(1); }
  const items = await search(provider, type, q, Number(opt("--n", 6)), opt("--orientation", "landscape"));
  const want = opt("--telecharger", null);
  if (!want) { for (const it of items) console.log(`${it.id}  ${it.type}  ${it.largeur}x${it.hauteur}${it.duree_s ? "  " + it.duree_s + " s" : ""}  ${mention(it)}  ${it.page}`); console.log(items.length + " résultat(s). Pour télécharger : --telecharger <id>"); process.exit(0); }
  const it = items.find(x => x.id === want); if (!it) { console.log("Identifiant " + want + " absent des résultats de cette requête."); process.exit(1); }
  const dir = path.join(root, "public", "media"); fs.mkdirSync(dir, { recursive: true });
  const rel = "media/" + it.provider + "-" + it.id + "." + it.ext;
  const r = await fetch(it.fichier); if (!r.ok) throw new Error("Téléchargement : HTTP " + r.status);
  fs.writeFileSync(path.join(root, "public", rel), Buffer.from(await r.arrayBuffer()));
  const mf = path.join(root, "media-manifest.json");
  const m = fs.existsSync(mf) ? JSON.parse(fs.readFileSync(mf, "utf8")) : { medias: [] };
  m.medias = m.medias.filter(x => x.src !== rel);
  m.medias.push({ src: rel, fournisseur: it.provider, id: it.id, page: it.page, auteur: it.auteur, licence: licence(it.provider), mention: mention(it), requete: q, telecharge: new Date().toISOString().slice(0, 10) });
  fs.writeFileSync(mf, JSON.stringify(m, null, 1));
  console.log("Téléchargé : public/" + rel + "\nMention à afficher : " + mention(it) + "\nEntrée ajoutée à media-manifest.json");
}
