/* Coach IA : toutes les demandes faites à Claude.
   Chaque fonction reçoit le client Anthropic en paramètre, ce qui permet de la tester sans réseau. */
import * as z from "zod/v4";
import { betaZodOutputFormat } from "@anthropic-ai/sdk/helpers/beta/zod";
import { GeminiError } from "./gemini.mjs";

export const MODEL = process.env.COACH_MODEL || "claude-opus-5-5";

export class CoachError extends Error {
  constructor(code, message) {
    super(message);
    this.code = code;
  }
}

const PLATFORMS = { tiktok: "TikTok", instagram: "Instagram Reels", youtube: "YouTube Shorts" };
const LANGS = { fr: "French", pt: "Brazilian Portuguese", en: "English" };

const BASE_RULES = [
  "You are a short-form video growth coach (TikTok, Instagram Reels, YouTube Shorts).",
  "Be concrete and actionable: give exact wording, timings in seconds and on-screen text, never vague advice.",
  "Be honest: nobody can guarantee virality. Scores are estimates based on known short-video best practices",
  "(hook in the first 2 seconds, on-screen text, pacing, clear payoff, call to action, sound, length, trends).",
  "Never invent statistics, view counts or facts about the creator that were not given to you.",
  "Do not encourage buying followers, engagement bait that breaks platform rules, misleading claims or copyrighted music reuse."
].join("\n");

function system(lang) {
  return BASE_RULES + "\nWrite every text field in " + (LANGS[lang] || LANGS.fr) + ".";
}

/* ---------- Schémas des réponses ---------- */

export const IdeasSchema = z.object({
  ideas: z.array(z.object({
    titre: z.string(),
    accroche: z.string().describe("First sentence said or shown in the first 2 seconds"),
    texte_ecran: z.string().describe("On-screen text for the opening"),
    format: z.string().describe("Format: talking head, tutorial, before/after, POV, list, story..."),
    duree_secondes: z.number(),
    script: z.array(z.object({
      temps: z.string().describe("Time range, e.g. 0-2s"),
      visuel: z.string(),
      parole: z.string()
    })),
    appel_action: z.string(),
    legende: z.string(),
    hashtags: z.array(z.string()),
    pourquoi_ca_marche: z.string()
  }))
});

export const ScoreSchema = z.object({
  score_global: z.number().describe("0-100"),
  resume: z.string(),
  criteres: z.array(z.object({
    nom: z.string(),
    note: z.number().describe("0-10"),
    constat: z.string(),
    conseil: z.string()
  })),
  accroches_alternatives: z.array(z.string()),
  priorites: z.array(z.string()).describe("Top fixes, most important first"),
  limites: z.string().describe("What could not be judged from the material provided")
});

export const ProfileSchema = z.object({
  score_profil: z.number().describe("0-100"),
  resume: z.string(),
  chiffres_lus: z.array(z.object({ indicateur: z.string(), valeur: z.string() }))
    .describe("Only figures actually visible in the screenshots or given in the text"),
  forces: z.array(z.string()),
  faiblesses: z.array(z.string()),
  plan_7_jours: z.array(z.object({ jour: z.string(), action: z.string(), idee_video: z.string() })),
  frequence_conseillee: z.string(),
  meilleurs_formats: z.array(z.string())
});

export const AdaptSchema = z.object({
  versions: z.array(z.object({
    plateforme: z.enum(["tiktok", "instagram", "youtube"]),
    titre: z.string().describe("Title (YouTube Shorts) or empty string"),
    legende: z.string(),
    hashtags: z.array(z.string()),
    conseils: z.string().describe("Platform-specific posting tips: cover, timing, audio, length")
  }))
});

/* ---------- Appel commun ---------- */

function imageBlocks(images) {
  return (images || []).map((data) => ({
    type: "image",
    source: { type: "base64", media_type: "image/jpeg", data }
  }));
}

export async function ask(client, { lang, content, schema, effort = "medium", maxTokens = 16000 }) {
  /* Gemini (gratuit) : même demande, même format de réponse. */
  if (client?.provider === "gemini") {
    try { return await client.parseJson({ system: system(lang), content, schema, maxTokens }); }
    catch (e) { if (e instanceof GeminiError) throw new CoachError(e.kind, e.message); throw e; }
  }
  const response = await client.beta.messages.parse({
    model: MODEL,
    max_tokens: maxTokens,
    betas: ["server-side-fallback-2026-07-01"],
    fallbacks: "default",
    system: system(lang),
    output_config: { effort, format: betaZodOutputFormat(schema) },
    messages: [{ role: "user", content }]
  });
  if (response.stop_reason === "refusal") {
    throw new CoachError("refus", "L'IA a refusé cette demande. Reformulez-la.");
  }
  if (response.stop_reason === "max_tokens") {
    throw new CoachError("trop_long", "La réponse était trop longue. Demandez moins d'éléments.");
  }
  if (!response.parsed_output) {
    throw new CoachError("reponse_invalide", "La réponse de l'IA était illisible. Réessayez.");
  }
  return response.parsed_output;
}

/* ---------- Les quatre services ---------- */

export function ideas(client, i) {
  const n = Math.min(Math.max(parseInt(i.nombre, 10) || 3, 1), 8);
  const text = [
    `Create ${n} short video ideas, each with a full second-by-second script.`,
    `Platform: ${PLATFORMS[i.plateforme] || "TikTok"}.`,
    `Niche / subject: ${i.niche}.`,
    i.audience && `Target audience: ${i.audience}.`,
    i.objectif && `Goal: ${i.objectif}.`,
    i.ton && `Tone: ${i.ton}.`,
    i.contraintes && `Constraints (equipment, place, time): ${i.contraintes}.`,
    "Make the hooks varied (question, bold claim, surprising visual, mistake, story). Hashtags without spaces, 3 to 6 per idea."
  ].filter(Boolean).join("\n");
  return ask(client, { lang: i.langue, content: text, schema: IdeasSchema });
}

export function score(client, i) {
  const text = [
    "Rate this short video for its viral potential and explain how to improve it.",
    `Platform: ${PLATFORMS[i.plateforme] || "TikTok"}.`,
    i.duree && `Duration: ${Math.round(i.duree)} seconds.`,
    i.description && `Creator's description: ${i.description}`,
    i.transcription && `What is said (transcript): ${i.transcription}`,
    i.legende && `Planned caption: ${i.legende}`,
    i.images?.length
      ? `The ${i.images.length} images are frames taken in order across the video (the first is at the very start).`
      : "No frames were provided: judge only from the text and say so in 'limites'.",
    "Criteria to rate (0-10 each): Accroche (0-2 s), Texte à l'écran, Rythme et montage, Clarté du message, Valeur ou émotion, Appel à l'action, Qualité image/son, Adéquation à la plateforme.",
    "Give 3 alternative hooks."
  ].filter(Boolean).join("\n");
  return ask(client, {
    lang: i.langue,
    content: [...imageBlocks(i.images), { type: "text", text }],
    schema: ScoreSchema,
    effort: "high"
  });
}

export function profile(client, i) {
  const text = [
    "Analyse this creator's short-video account and give a 7-day action plan.",
    i.pseudo && `Account: ${i.pseudo}.`,
    i.niche && `Niche: ${i.niche}.`,
    i.stats && `Statistics given by the creator:\n${i.stats}`,
    i.images?.length ? `The ${i.images.length} images are screenshots of the account or its analytics.` : "",
    "Only report figures you can actually read in the screenshots or in the text."
  ].filter(Boolean).join("\n");
  return ask(client, {
    lang: i.langue,
    content: [...imageBlocks(i.images), { type: "text", text }],
    schema: ProfileSchema,
    effort: "high"
  });
}

export function adapt(client, i) {
  const targets = (i.plateformes || []).filter((p) => PLATFORMS[p]);
  const text = [
    `Adapt this video's publication text for: ${targets.map((p) => p + " (" + PLATFORMS[p] + ")").join(", ")}.`,
    `Video content / script: ${i.contenu}`,
    i.legende && `Original caption: ${i.legende}`,
    "Respect each platform's habits and limits (YouTube Shorts title under 100 characters with #Shorts, Instagram caption with a strong first line, TikTok short caption).",
    "Return exactly one version per requested platform."
  ].filter(Boolean).join("\n");
  return ask(client, { lang: i.langue, content: text, schema: AdaptSchema, effort: "low" });
}
