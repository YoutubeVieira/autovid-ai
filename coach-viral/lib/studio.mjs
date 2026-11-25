/* Studio : analyse d'une vidéo (lien ou fichier) et création d'une nouvelle version, originale et améliorée,
   dans le même style. Puis fabrication de la vidéo : images, voix off, rendu. */
import * as z from "zod/v4";
import { mkdir, readdir, readFile, rm, stat, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { randomBytes } from "node:crypto";
import { ask, CoachError } from "./coach.mjs";
import { run, mediaDuration, renderVideo } from "./render.mjs";
import { synthesize } from "./voice.mjs";

const PY = process.env.PYTHON || "python3";
const TRANSCRIRE = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "voix", "transcrire.py");
export const DATA = process.env.DOSSIER_DONNEES || path.join(process.cwd(), "donnees");
const MAX_LINK_SECONDS = 180;

export const newId = () => randomBytes(12).toString("hex");

/* ---------- Format de la recette ---------- */

const Scene = z.object({
  haut: z.string().describe("Text shown above the image (max ~90 characters)"),
  bas: z.string().describe("Text shown below the image (max ~90 characters), can be empty"),
  voix: z.string().describe("Voice-over spoken during this scene (natural spoken language)"),
  prompt_image: z.string().describe("Detailed English prompt to generate the scene image, in the same visual style"),
  duree: z.number().describe("Seconds, 3 to 8")
});

export const NewVersion = z.object({
  titre: z.string(),
  scenes: z.array(Scene),
  legende: z.string(),
  hashtags: z.array(z.string()),
  ambiance_musique: z.string().describe("Music mood to look for, e.g. soft piano, emotional strings"),
  pourquoi_mieux: z.string()
});

export const AnalysisSchema = z.object({
  style: z.object({
    format: z.string().describe("e.g. emotional quote over 3D animated image, story, tutorial"),
    visuel: z.string().describe("Visual style: rendering, colours, framing, lighting"),
    texte: z.string().describe("How on-screen text is laid out and written"),
    voix: z.string().describe("Voice-over: tone, pace, gender if audible; or 'no voice' / 'unknown'"),
    rythme: z.string(),
    duree_secondes: z.number()
  }),
  pourquoi_ca_marche: z.array(z.string()),
  a_ameliorer: z.array(z.string()),
  nouvelle_version: NewVersion
});

const ORIGINAL = [
  "The new version must be ORIGINAL: new wording, new angle, no sentence copied from the source,",
  "no reuse of the source creator's characters, brand, watermark, username or footage. Keep only the general style and format.",
  "Scene count: 1 to 6. First 2 seconds must hook. Voice-over must sound natural when read aloud and fit the scene durations",
  "(about 2.5 words per second). On-screen texts are short and readable on a phone."
].join("\n");

export function analyze(client, i) {
  const text = [
    "Analyse this short video's style and why it works, then write an improved ORIGINAL video in the same style.",
    `Duration: ${Math.round(i.duree || 0)} s.`,
    i.transcription ? `Transcript of the audio: ${i.transcription}` : "No transcript available.",
    i.consigne && `Creator's instructions for the new version: ${i.consigne}`,
    i.sujet && `Subject for the new version: ${i.sujet}`,
    `The ${i.images.length} images are frames taken in order across the video.`,
    ORIGINAL
  ].filter(Boolean).join("\n");
  return ask(client, {
    lang: i.langue,
    content: [...i.images.map((data) => ({ type: "image", source: { type: "base64", media_type: "image/jpeg", data } })), { type: "text", text }],
    schema: AnalysisSchema,
    effort: "high"
  });
}

export function create(client, i) {
  const text = [
    "Write an ORIGINAL short vertical video in this style: one striking cinematic 3D animated image per scene (Pixar-like lighting),",
    "an emotional or useful sentence above the image, a short punchline below it, and a warm voice-over.",
    `Subject: ${i.sujet}.`,
    i.consigne && `Creator's instructions: ${i.consigne}`,
    ORIGINAL
  ].filter(Boolean).join("\n");
  return ask(client, { lang: i.langue, content: text, schema: NewVersion, effort: "medium" });
}

/* ---------- Modèle déduit d'une image de référence ---------- */

const Hex = z.string().describe("Colour as #RRGGBB");
export const StyleSchema = z.object({
  gabarit: z.enum(["citation", "face_camera"]).describe("citation = still image centered with text above/below; face_camera = person talking with word-by-word captions"),
  description: z.string(),
  citation: z.object({
    couleur: Hex, taille: z.number().describe("Font size in px for a 1080x1920 frame, 40-72"),
    zoom: z.enum(["in", "out"]), style_image: z.string().describe("English prompt fragment describing the image style to reproduce")
  }),
  face_camera: z.object({
    taille: z.number().describe("Caption font size px for 1080x1920, 70-130"),
    couleur_texte: Hex, couleur_mot_actif: Hex, couleur_contour: Hex, epaisseur_contour: z.number(),
    position_sous_titres: z.number().describe("Vertical position of captions from top, 0-1"),
    mots_par_groupe: z.number().describe("1-4"), majuscules: z.boolean(),
    titre_couleur_texte: Hex, titre_couleur_boite: Hex, titre_couleur_bordure: Hex,
    titre_position: z.number().describe("Vertical position of title boxes from top, 0-1")
  })
});

export function styleFromImage(client, i) {
  return ask(client, {
    lang: i.langue,
    content: [
      ...i.images.map((data) => ({ type: "image", source: { type: "base64", media_type: "image/jpeg", data } })),
      { type: "text", text: "These are reference screenshots of a short vertical video style the creator wants to reproduce. Measure the layout (positions as fractions of height), colours, sizes, casing and caption grouping, choose the closest template, and fill both template settings. Do not describe or copy any person, logo or watermark." }
    ],
    schema: StyleSchema,
    effort: "medium"
  });
}

export const TitlesSchema = z.object({
  titres: z.array(z.object({ texte: z.string().describe("Max 45 characters"), debut: z.number(), fin: z.number() }))
});

/* Titres en boîte (chapitres) placés aux moments clés du discours. */
export function titlesFor(client, i) {
  const text = [
    "Here is a word-timed transcript of a talking-head short video. Write 2 to 5 short punchy title boxes shown at key moments",
    "(first one at the very start as the hook, then one per new idea). Each stays 2 to 4 seconds. Times in seconds.",
    JSON.stringify(i.mots.map((w) => [w.mot, w.debut]))
  ].join("\n");
  return ask(client, { lang: i.langue, content: text, schema: TitlesSchema, effort: "low" });
}

/* Fin du message d'erreur d'un outil (la ligne utile est en général la dernière). */
export function detail(e) {
  const lines = String(e?.message || e).split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
  const last = lines.slice(-2).join(" ").slice(-300);
  if (/No module named 'faster_whisper'|introuvable/.test(last)) return "installez faster-whisper sur le serveur (voir le guide).";
  return last || "erreur inconnue";
}

export async function transcribeWords(file, dir) {
  const wav = path.join(dir, "audio-mots.wav");
  await run("ffmpeg", ["-y", "-loglevel", "error", "-i", file, "-vn", "-ac", "1", "-ar", "16000", wav]);
  const out = await run(PY, [TRANSCRIRE, wav, process.env.WHISPER_MODELE || "small", "--mots"]);
  return JSON.parse(out);
}

/* ---------- Récupération d'une vidéo ---------- */

/* Télécharge une vidéo depuis un lien (TikTok, Instagram, YouTube…) avec yt-dlp.
   À réserver à vos propres vidéos ou à celles que vous avez le droit d'utiliser. */
export async function download(url, dir) {
  if (!/^https:\/\/[^\s]+$/i.test(url)) throw new CoachError("entree", "Lien invalide : il doit commencer par https://");
  await mkdir(dir, { recursive: true });
  const out = path.join(dir, "source.%(ext)s");
  try {
    await run(PY, ["-m", "yt_dlp", "--no-playlist", "--quiet", "--no-warnings",
      "--match-filter", `duration <= ${MAX_LINK_SECONDS}`, "--max-filesize", "120M",
      "-f", "best[ext=mp4][height<=1280]/best[height<=1280]/best", "-o", out, url]);
  } catch (e) {
    throw new CoachError("lien", "Impossible de récupérer cette vidéo (lien privé, trop longue ou site non pris en charge). Téléversez le fichier à la place.");
  }
  const f = (await readdir(dir)).find((n) => n.startsWith("source."));
  if (!f) throw new CoachError("lien", `Vidéo introuvable ou plus longue que ${MAX_LINK_SECONDS / 60} minutes.`);
  return path.join(dir, f);
}

/* Images (début, puis réparties) + transcription facultative. */
export async function extract(file, dir, { frames = 8, transcrire = process.env.TRANSCRIPTION !== "0" } = {}) {
  const duree = await mediaDuration(file);
  if (!duree) throw new CoachError("entree", "Fichier vidéo illisible.");
  const images = [];
  for (let k = 0; k < frames; k++) {
    const t = k === 0 ? Math.min(0.3, duree / 10) : (duree * k) / frames;
    const out = path.join(dir, `img${k}.jpg`);
    await run("ffmpeg", ["-y", "-loglevel", "error", "-ss", t.toFixed(2), "-i", file, "-frames:v", "1", "-vf", "scale=512:-2", "-q:v", "4", out]);
    images.push((await readFile(out)).toString("base64"));
  }
  let transcription = "";
  if (transcrire) {
    try {
      const wav = path.join(dir, "audio.wav");
      await run("ffmpeg", ["-y", "-loglevel", "error", "-i", file, "-vn", "-ac", "1", "-ar", "16000", "-t", "300", wav]);
      transcription = (await run(PY, [TRANSCRIRE, wav, process.env.WHISPER_MODELE || "small"])).trim();
    } catch {
      transcription = ""; /* pas de transcription : l'analyse se fait sur les images */
    }
  }
  return { duree, images, transcription };
}

/* ---------- Images des scènes ---------- */

/* Génère l'image d'une scène. Moteur par défaut : Pollinations (gratuit, sans clé). Sinon fond dégradé. */
export async function sceneImage(prompt, out, env = process.env) {
  const moteur = env.IMAGES || "pollinations";
  if (moteur !== "pollinations" || !prompt) return null;
  const url = "https://image.pollinations.ai/prompt/" + encodeURIComponent(prompt.slice(0, 900)) +
    "?width=1024&height=1024&nologo=true&model=flux&seed=" + Math.floor(Math.random() * 1e6);
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(90_000) });
    if (!res.ok || !/^image\//.test(res.headers.get("content-type") || "")) return null;
    await writeFile(out, Buffer.from(await res.arrayBuffer()));
    return out;
  } catch {
    return null;
  }
}

/* ---------- Fabrication complète ---------- */

/* version : NewVersion ; options : { moteur, voix, langue, echantillon, images: {index: chemin}, musique } */
export async function produce(version, options, outDir, onStep = () => {}) {
  const id = newId();
  const work = path.join(DATA, "travail", id);
  await mkdir(work, { recursive: true });
  await mkdir(outDir, { recursive: true });
  try {
    const scenes = [];
    for (let i = 0; i < version.scenes.length; i++) {
      const s = version.scenes[i];
      onStep(`Image ${i + 1}/${version.scenes.length}`);
      const image = options.images?.[i] || (await sceneImage(s.prompt_image, path.join(work, `scene${i}.jpg`)));
      onStep(`Voix ${i + 1}/${version.scenes.length}`);
      let voixFichier = null;
      if (s.voix && options.moteur !== "aucune") {
        voixFichier = (await synthesize(s.voix, path.join(work, `voix${i}.wav`), options, options.env || process.env)).fichier;
      }
      scenes.push({ haut: s.haut, bas: s.bas, image, voixFichier, duree: s.duree });
    }
    onStep("Montage");
    const out = path.join(outDir, id + ".mp4");
    const r = await renderVideo({ scenes, musique: options.musique, style: options.style }, out);
    /* Voix off seule, à exporter. */
    const voix = scenes.filter((s) => s.voixFichier).map((s) => s.voixFichier);
    let voixExport = null;
    if (voix.length) {
      voixExport = path.join(outDir, id + "-voix.mp3");
      await run("ffmpeg", ["-y", "-loglevel", "error", ...voix.flatMap((v) => ["-i", v]),
        "-filter_complex", voix.map((_, k) => `[${k}:a]`).join("") + `concat=n=${voix.length}:v=0:a=1[a]`, "-map", "[a]", "-b:a", "160k", voixExport]);
    }
    return { id, video: path.basename(out), voix: voixExport && path.basename(voixExport), duree: r.duree };
  } finally {
    await rm(work, { recursive: true, force: true });
  }
}

/* Supprime les fichiers produits il y a plus de `hours` heures. */
export async function cleanup(dir, hours = 48) {
  try {
    for (const f of await readdir(dir)) {
      const p = path.join(dir, f);
      if (Date.now() - (await stat(p)).mtimeMs > hours * 3600_000) await rm(p, { recursive: true, force: true });
    }
  } catch { /* dossier absent */ }
}

/* ---------- Clips : les meilleurs moments d'une vidéo longue (comme OpusClip) ---------- */

export const ClipsSchema = z.object({
  clips: z.array(z.object({
    titre: z.string().describe("Title box shown during the first seconds, max 45 characters"),
    debut: z.number().describe("Start time in seconds, at the start of a sentence"),
    fin: z.number().describe("End time in seconds, at the end of a sentence"),
    score: z.number().describe("0-100 estimated short-video potential"),
    pourquoi: z.string()
  }))
});

export function pickClips(client, i) {
  const n = Math.min(Math.max(parseInt(i.nombre, 10) || 3, 1), 6);
  const text = [
    `From this word-timed transcript of a long video, pick the ${n} best self-contained moments for vertical short videos.`,
    `Each clip lasts ${i.min || 20} to ${i.max || 60} seconds, starts with a strong hook sentence and ends on a complete thought. Clips must not overlap.`,
    "Return times in seconds that match word timings. Sort by score, best first.",
    JSON.stringify(i.mots.map((w) => [w.mot, Math.round(w.debut * 10) / 10]))
  ].join("\n");
  return ask(client, { lang: i.langue, content: text, schema: ClipsSchema, effort: "medium" });
}

/* Garde les mots d'un clip et recale leurs temps sur le début du clip. */
export function wordsInRange(mots, debut, fin) {
  return mots.filter((w) => w.debut >= debut - 0.05 && w.fin <= fin + 0.3)
    .map((w) => ({ mot: w.mot, debut: Math.max(0, w.debut - debut), fin: Math.max(0.05, w.fin - debut) }));
}

/* Corrige des bornes impossibles (fin avant début, hors de la vidéo, trop court) et les chevauchements. */
export function sanitizeClips(clips, duree, min = 8) {
  const out = [];
  for (const c of [...clips].sort((a, b) => b.score - a.score)) {
    const debut = Math.max(0, Math.min(c.debut, duree));
    const fin = Math.min(duree, Math.max(c.fin, debut));
    if (fin - debut < min) continue;
    if (out.some((o) => debut < o.fin && fin > o.debut)) continue;
    out.push({ ...c, debut, fin });
  }
  return out;
}

export async function produceClips(client, video, options, outDir, renderFacecam, onStep = () => {}) {
  const work = path.join(DATA, "travail", newId());
  await mkdir(work, { recursive: true });
  await mkdir(outDir, { recursive: true });
  try {
    onStep("Transcription mot à mot");
    const mots = options.mots || await transcribeWords(video, work).catch((e) => {
      throw new CoachError("transcription", "Transcription impossible : " + detail(e));
    });
    if (!mots.length) throw new CoachError("transcription", "Aucune parole détectée dans la vidéo.");
    const duree = await mediaDuration(video);
    onStep("Choix des meilleurs moments");
    const { clips } = await pickClips(client, { mots, nombre: options.nombre, langue: options.langue });
    const ok = sanitizeClips(clips, duree);
    if (!ok.length) throw new CoachError("clips", "Aucun moment assez long n'a été trouvé.");
    const results = [];
    for (let k = 0; k < ok.length; k++) {
      const c = ok[k];
      onStep(`Clip ${k + 1}/${ok.length}`);
      const cut = path.join(work, `cut${k}.mp4`);
      await run("ffmpeg", ["-y", "-loglevel", "error", "-ss", c.debut.toFixed(2), "-to", c.fin.toFixed(2), "-i", video, "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-c:a", "aac", cut]);
      const id = newId();
      await renderFacecam(cut, wordsInRange(mots, c.debut, c.fin), [{ texte: c.titre, debut: 0, fin: Math.min(3.5, c.fin - c.debut) }], options.style || {}, path.join(outDir, id + ".mp4"));
      results.push({ video: id + ".mp4", titre: c.titre, score: Math.round(c.score), debut: c.debut, fin: c.fin, pourquoi: c.pourquoi });
    }
    return { clips: results, ...Object.fromEntries(results.map((r, i) => ["clip" + i, r.video])) };
  } finally {
    await rm(work, { recursive: true, force: true });
  }
}
