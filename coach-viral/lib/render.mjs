/* Moteur de rendu : transforme une « recette » en vidéo verticale 1080x1920, avec FFmpeg.
   Style « citation » : image au centre qui zoome lentement, fond flou de la même image,
   texte blanc en haut et en bas, voix off, fondu enchaîné entre les scènes. */
import { spawn } from "node:child_process";
import { writeFile, mkdtemp, rm, copyFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
export const FONT = process.env.FONT_FILE || path.join(here, "..", "assets", "fonts", "Inter-SemiBold.otf");
export const W = 1080, H = 1920, IMG = 1080, FPS = 30;
const IMG_Y = Math.round((H - IMG) / 2);
const XFADE = 0.4;

export function run(cmd, args, { input, cwd } = {}) {
  return new Promise((resolve, reject) => {
    const p = spawn(cmd, args, { stdio: ["pipe", "pipe", "pipe"], cwd });
    let out = "", err = "";
    p.stdout.on("data", (d) => (out += d));
    p.stderr.on("data", (d) => (err += d));
    p.on("error", (e) => reject(new Error(`${cmd} introuvable : ${e.message}`)));
    p.on("close", (code) => (code === 0 ? resolve(out) : reject(new Error(`${cmd} a échoué (${code}) : ${err.slice(-800)}`))));
    if (input) p.stdin.end(input); else p.stdin.end();
  });
}

export async function mediaDuration(file) {
  const out = await run("ffprobe", ["-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", file]);
  return parseFloat(out) || 0;
}

/* Coupe un texte en lignes équilibrées d'au plus `max` caractères, sans couper les mots
   (évite un mot seul sur la dernière ligne). */
export function wrap(text, max = 30) {
  const lines = greedy(text, max);
  if (lines.length < 2) return lines;
  let best = lines;
  for (let m = max - 1; m >= 8; m--) {
    const t = greedy(text, m);
    if (t.length !== lines.length) break;
    best = t;
  }
  return best;
}

function greedy(text, max) {
  const words = String(text || "").replace(/\s+/g, " ").trim().split(" ").filter(Boolean);
  const lines = [];
  let cur = "";
  for (const w of words) {
    if (!cur) cur = w;
    else if ((cur + " " + w).length <= max) cur += " " + w;
    else { lines.push(cur); cur = w; }
  }
  if (cur) lines.push(cur);
  return lines;
}

function hex(c, fallback) {
  return /^#?[0-9a-f]{6}$/i.test(c || "") ? "0x" + c.replace("#", "") : fallback;
}

/* Les filtres FFmpeg ne reçoivent que des noms de fichiers simples, relatifs au dossier de travail :
   un chemin Windows (C:\…) ou un nom avec apostrophe casserait la syntaxe des filtres. */
/* Filtres drawtext d'un bloc de lignes. anchor "bottom" : la dernière ligne finit à y ; "top" : la première commence à y. */
function textFilters(lines, files, { y, anchor, size, color, fadeIn, dur }) {
  const lh = Math.round(size * 1.28);
  const top = anchor === "bottom" ? y - lines.length * lh : y;
  const alpha = `if(lt(t\\,${fadeIn})\\,0\\,if(lt(t\\,${fadeIn + 0.35})\\,(t-${fadeIn})/0.35\\,if(gt(t\\,${(dur - 0.35).toFixed(2)})\\,max(0\\,(${dur.toFixed(2)}-t)/0.35)\\,1)))`;
  return lines.map((_, i) =>
    `drawtext=fontfile=police.otf:textfile=${files[i]}:fontsize=${size}:fontcolor=${color}` +
    `:shadowcolor=black@0.65:shadowx=0:shadowy=3:x=(w-text_w)/2:y=${top + i * lh}:alpha='${alpha}'`
  );
}

/* Rend une scène en segment vidéo muet. */
export async function renderScene(scene, out, dir, idx, style = {}) {
  const d = scene.duree;
  const n = Math.max(1, Math.round(d * FPS));
  let size = style.taille || 54;
  const color = hex(style.couleur, "0xFFFFFF");
  const zoomOut = style.zoom === "out";
  const z = zoomOut ? `1.12-0.12*on/${n}` : `1+0.12*on/${n}`;
  const inputs = scene.image
    ? ["-framerate", String(FPS), "-loop", "1", "-t", d.toFixed(3), "-i", path.resolve(scene.image)]
    : ["-f", "lavfi", "-t", d.toFixed(3), "-i", `gradients=s=1080x1080:c0=0x2B1F4A:c1=0xC2557A:x0=0:y0=0:x1=1080:y1=1080:r=${FPS}`];

  const write = async (name, lines) => {
    const files = [];
    for (let i = 0; i < lines.length; i++) {
      const f = `${name}-${idx}-${i}.txt`;
      await writeFile(path.join(dir, f), lines[i]);
      files.push(f);
    }
    return files;
  };
  const hautLines = wrap(scene.haut, style.largeur || 30);
  const basLines = wrap(scene.bas, style.largeur || 30);
  /* Un mot très long réduit la taille du texte pour ne pas sortir de l'écran. */
  const longest = Math.max(0, ...hautLines.concat(basLines).map((l) => l.length));
  const max = style.largeur || 30;
  if (longest > max) size = Math.max(28, Math.floor((size * max) / longest));
  const hautFiles = await write("haut", hautLines);
  const basFiles = await write("bas", basLines);

  const filters = [
    `[0:v]scale=2160:2160:force_original_aspect_ratio=increase,crop=2160:2160,setsar=1,split[a][b]`,
    `[a]scale=${W}:${H}:force_original_aspect_ratio=increase,crop=${W}:${H},gblur=sigma=40,eq=brightness=-0.12:saturation=0.9[bg]`,
    `[b]zoompan=z='${z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=${IMG}x${IMG}:fps=${FPS}[fg]`,
    `[bg][fg]overlay=0:${IMG_Y}:shortest=1,format=yuv420p` +
      [...textFilters(hautLines, hautFiles, { y: IMG_Y - 28, anchor: "bottom", size, color, fadeIn: 0.15, dur: d }),
       ...textFilters(basLines, basFiles, { y: IMG_Y + IMG + 34, anchor: "top", size, color, fadeIn: 0.6, dur: d })]
        .map((f) => "," + f).join("") + `[v]`
  ];
  await copyFile(FONT, path.join(dir, "police.otf")).catch(() => {});
  await run("ffmpeg", ["-y", "-loglevel", "error", ...inputs, "-filter_complex", filters.join(";"),
    "-map", "[v]", "-frames:v", String(n), "-r", String(FPS), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", path.resolve(out)], { cwd: dir });
  return out;
}

/* Durée de chaque scène : assez pour la voix, au moins `min` secondes. */
export function sceneDurations(scenes, voiceDurations, min = 3) {
  return scenes.map((s, i) => {
    const v = voiceDurations[i] || 0;
    const wanted = Number(s.duree) > 0 ? Number(s.duree) : 0;
    return Math.max(min, wanted, v ? v + 0.8 : 0);
  });
}

/* Positions de départ des scènes, compte tenu du fondu enchaîné. */
export function sceneStarts(durations) {
  const starts = [];
  let t = 0;
  durations.forEach((d, i) => { starts.push(t); t += d - (i < durations.length - 1 ? XFADE : 0); });
  return { starts, total: t };
}

/* recipe : { scenes: [{ haut, bas, image?, voixFichier? , duree? }], style?, musique? } */
export async function renderVideo(recipe, out) {
  const dir = await mkdtemp(path.join(tmpdir(), "rendu-"));
  try {
    const scenes = recipe.scenes;
    if (!scenes?.length) throw new Error("La recette ne contient aucune scène.");
    const voiceDur = await Promise.all(scenes.map((s) => (s.voixFichier ? mediaDuration(s.voixFichier) : 0)));
    const durs = sceneDurations(scenes, voiceDur, recipe.style?.dureeMin || 3);
    const segs = [];
    for (let i = 0; i < scenes.length; i++) {
      segs.push(await renderScene({ ...scenes[i], duree: durs[i] }, path.join(dir, `s${i}.mp4`), dir, i, recipe.style));
    }
    const { starts, total } = sceneStarts(durs);

    /* Vidéo : fondus enchaînés, fondu au noir final. */
    const vIn = segs.flatMap((s) => ["-i", s]);
    const vf = [];
    let last = "[0:v]";
    for (let i = 1; i < segs.length; i++) {
      const label = `[x${i}]`;
      vf.push(`${last}[${i}:v]xfade=transition=fade:duration=${XFADE}:offset=${(starts[i]).toFixed(3)}${label}`);
      last = label;
    }
    vf.push(`${last}fade=t=out:st=${Math.max(0, total - 0.6).toFixed(3)}:d=0.6[v]`);

    /* Audio : chaque voix posée au début de sa scène (+0,2 s), musique de fond en boucle, plus basse. */
    const aIn = [];
    const af = [];
    const mix = [];
    let k = segs.length;
    scenes.forEach((s, i) => {
      if (!s.voixFichier) return;
      aIn.push("-i", s.voixFichier);
      const ms = Math.round((starts[i] + 0.2) * 1000);
      af.push(`[${k}:a]aresample=48000,aformat=channel_layouts=stereo,adelay=${ms}|${ms}[va${k}]`);
      mix.push(`[va${k}]`);
      k++;
    });
    if (recipe.musique) {
      aIn.push("-stream_loop", "-1", "-i", recipe.musique);
      af.push(`[${k}:a]aresample=48000,aformat=channel_layouts=stereo,volume=${recipe.volumeMusique ?? 0.18},atrim=0:${total.toFixed(3)}[mu]`);
      mix.push("[mu]");
      k++;
    }
    const args = ["-y", "-loglevel", "error", ...vIn, ...aIn];
    if (mix.length) {
      af.push(`${mix.join("")}amix=inputs=${mix.length}:normalize=0:duration=longest,apad,atrim=0:${total.toFixed(3)},afade=t=out:st=${Math.max(0, total - 0.6).toFixed(3)}:d=0.6[a]`);
      args.push("-filter_complex", [...vf, ...af].join(";"), "-map", "[v]", "-map", "[a]", "-c:a", "aac", "-b:a", "160k");
    } else {
      args.push("-filter_complex", vf.join(";"), "-map", "[v]");
    }
    args.push("-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-t", total.toFixed(3), out);
    await run("ffmpeg", args);
    return { fichier: out, duree: total, scenes: durs };
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
}
