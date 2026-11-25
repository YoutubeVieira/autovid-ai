/* Voix off : plusieurs moteurs interchangeables.
   - kokoro     : gratuit, tourne sur le serveur (CPU), voix fixes FR / PT-BR / EN. Poids Apache-2.0 : vente autorisée.
   - chatterbox : gratuit, clonage de VOTRE voix à partir de 10 s d'audio. Licence MIT : vente autorisée. GPU conseillé.
   - fal        : Chatterbox hébergé chez fal.ai, payé à l'usage (environ 0,025 $ pour 1 000 caractères), clonage.
   - edge       : voix Microsoft très réalistes et gratuites, mais réservées à un usage PERSONNEL
                  (désactivées automatiquement quand la vente est activée).
   - test       : son de test, pour les essais automatiques. */
import { writeFile, readFile, mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { run, mediaDuration } from "./render.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const PY = process.env.PYTHON || "python3";
const SCRIPTS = path.join(here, "..", "voix");

export const VOICES = {
  kokoro: {
    fr: [{ id: "ff_siwis", nom: "Siwis (femme)" }],
    pt: [{ id: "pf_dora", nom: "Dora (femme)" }, { id: "pm_santa", nom: "Santa (homme)" }],
    en: [{ id: "af_heart", nom: "Heart (femme)" }, { id: "am_michael", nom: "Michael (homme)" }]
  },
  edge: {
    fr: [{ id: "fr-FR-DeniseNeural", nom: "Denise (femme)" }, { id: "fr-FR-HenriNeural", nom: "Henri (homme)" }, { id: "fr-FR-VivienneMultilingualNeural", nom: "Vivienne (femme)" }],
    pt: [{ id: "pt-BR-FranciscaNeural", nom: "Francisca (femme)" }, { id: "pt-BR-AntonioNeural", nom: "Antonio (homme)" }],
    en: [{ id: "en-US-AriaNeural", nom: "Aria (femme)" }, { id: "en-US-GuyNeural", nom: "Guy (homme)" }]
  }
};

const KOKORO_LANG = { fr: "f", pt: "p", en: "a" };

/* Moteurs utilisables selon la configuration du serveur. */
export function enginesAvailable(env = process.env) {
  const list = (env.VOIX_MOTEURS || "kokoro,chatterbox,edge").split(",").map((s) => s.trim()).filter(Boolean);
  const sale = env.VENTE === "1";
  return list.filter((m) => {
    if (m === "edge" && sale) return false;
    if (m === "fal" && !env.FAL_KEY) return false;
    return ["kokoro", "chatterbox", "edge", "fal", "test"].includes(m);
  });
}

export function cloneEngines(env = process.env) {
  return enginesAvailable(env).filter((m) => m === "chatterbox" || m === "fal");
}

/* Rend un texte en fichier audio. opts : { moteur, langue, voix, echantillon (wav de clonage), vitesse } */
export async function synthesize(text, out, opts = {}, env = process.env) {
  const engine = opts.moteur || "kokoro";
  if (!enginesAvailable(env).includes(engine)) throw new Error(`Moteur de voix « ${engine} » indisponible sur ce serveur.`);
  const clean = String(text || "").replace(/\s+/g, " ").trim().slice(0, 2000);
  if (!clean) throw new Error("Texte de la voix off vide.");
  const lang = ["fr", "pt", "en"].includes(opts.langue) ? opts.langue : "fr";
  const dir = await mkdtemp(path.join(tmpdir(), "voix-"));
  try {
    const txt = path.join(dir, "texte.txt");
    await writeFile(txt, clean);
    const raw = path.join(dir, "brut.wav");
    if (engine === "test") {
      const d = Math.min(12, 0.5 + clean.split(" ").length * 0.33);
      await run("ffmpeg", ["-y", "-loglevel", "error", "-f", "lavfi", "-i", `sine=f=240:d=${d.toFixed(2)}`, raw]);
    } else if (engine === "kokoro") {
      const voice = pick(VOICES.kokoro[lang], opts.voix);
      await run(PY, [path.join(SCRIPTS, "kokoro_tts.py"), txt, raw, KOKORO_LANG[lang], voice, String(opts.vitesse || 1)]);
    } else if (engine === "edge") {
      const voice = pick(VOICES.edge[lang], opts.voix);
      const mp3 = path.join(dir, "brut.mp3");
      await run(PY, ["-m", "edge_tts", "--voice", voice, "--file", txt, "--write-media", mp3]);
      await run("ffmpeg", ["-y", "-loglevel", "error", "-i", mp3, raw]);
    } else if (engine === "chatterbox") {
      if (!opts.echantillon) throw new Error("Enregistrez d'abord votre voix dans l'onglet Voix.");
      await run(PY, [path.join(SCRIPTS, "chatterbox_tts.py"), txt, raw, lang, opts.echantillon]);
    } else if (engine === "fal") {
      if (!opts.echantillon) throw new Error("Enregistrez d'abord votre voix dans l'onglet Voix.");
      await falSynthesize(clean, lang, opts.echantillon, raw, env);
    }
    /* Normalisation : volume régulier, 48 kHz, léger blanc au début. */
    await run("ffmpeg", ["-y", "-loglevel", "error", "-i", raw, "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000", "-ac", "1", out]);
    return { fichier: out, duree: await mediaDuration(out), moteur: engine };
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
}

function pick(list, wanted) {
  return (list.find((v) => v.id === wanted) || list[0]).id;
}

/* fal.ai, file d'attente synchrone. Les noms des champs viennent de la documentation du modèle Chatterbox
   (text, audio_url) ; ils sont réglables avec FAL_CHAMP_* si fal les change. */
export function falRequest(text, lang, sampleB64, env = process.env) {
  const model = env.FAL_MODELE || "fal-ai/chatterbox/text-to-speech/multilingual";
  const body = {
    [env.FAL_CHAMP_TEXTE || "text"]: text,
    [env.FAL_CHAMP_AUDIO || "audio_url"]: "data:audio/wav;base64," + sampleB64
  };
  if ((env.FAL_CHAMP_LANGUE ?? "custom_audio_language") !== "") body[env.FAL_CHAMP_LANGUE || "custom_audio_language"] = lang;
  return {
    url: "https://fal.run/" + model,
    init: { method: "POST", headers: { Authorization: "Key " + env.FAL_KEY, "Content-Type": "application/json" }, body: JSON.stringify(body) }
  };
}

async function falSynthesize(text, lang, sample, out, env) {
  const b64 = (await readFile(sample)).toString("base64");
  const { url, init } = falRequest(text, lang, b64, env);
  const res = await fetch(url, init);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error("fal.ai a refusé la demande (" + res.status + ") : " + JSON.stringify(data).slice(0, 300));
  const audioUrl = data?.audio?.url || data?.audio_url || data?.url;
  if (!audioUrl) throw new Error("Réponse de fal.ai sans audio : " + JSON.stringify(data).slice(0, 300));
  const audio = await fetch(audioUrl);
  if (!audio.ok) throw new Error("Téléchargement de l'audio impossible.");
  await writeFile(out, Buffer.from(await audio.arrayBuffer()));
}

/* Prépare l'échantillon de clonage : mono 24 kHz, silences coupés, 5 à 30 s. */
export async function prepareSample(input, out) {
  await run("ffmpeg", ["-y", "-loglevel", "error", "-i", input,
    "-af", "silenceremove=start_periods=1:start_threshold=-45dB:stop_periods=-1:stop_threshold=-45dB:stop_duration=0.6,loudnorm,aresample=24000",
    "-ac", "1", "-t", "30", out]);
  const d = await mediaDuration(out);
  if (d < 5) throw new Error(`Enregistrement trop court (${d.toFixed(1)} s de voix). Parlez au moins 10 secondes.`);
  return d;
}

/* Phrase de consentement à lire à voix haute : prouve que c'est bien la personne qui parle. */
export function consentSentence(lang = "fr", rand = Math.random) {
  const code = String(1000 + Math.floor(rand() * 9000));
  const s = {
    fr: `Je confirme que c'est ma propre voix et j'autorise Coach Viral à la reproduire pour mes vidéos. Mon code est ${code.split("").join(" ")}.`,
    pt: `Eu confirmo que esta é a minha própria voz e autorizo o Coach Viral a reproduzi-la nos meus vídeos. Meu código é ${code.split("").join(" ")}.`,
    en: `I confirm this is my own voice and I allow Coach Viral to reproduce it for my videos. My code is ${code.split("").join(" ")}.`
  };
  return { code, phrase: s[lang] || s.fr };
}
