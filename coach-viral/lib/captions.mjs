/* Modèle « face caméra » : votre vidéo, avec sous-titres mot à mot et titres en boîte (format ASS rendu par FFmpeg).
   Le style est un objet de réglages, qu'on peut déduire d'une image de référence. */
import { writeFile, mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { run, W, H } from "./render.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const FONTS = process.env.FONTS_DIR || path.join(here, "..", "assets", "fonts");

export const DEFAULT_STYLE = {
  police: "Inter",
  gras: true,
  taille: 100,
  couleur_texte: "#FFFFFF",
  couleur_mot_actif: "#FFD400",
  couleur_contour: "#000000",
  epaisseur_contour: 8,
  position_sous_titres: 0.62,
  mots_par_groupe: 2,
  majuscules: false,
  titre_couleur_texte: "#FFFFFF",
  titre_couleur_boite: "#000000",
  titre_couleur_bordure: "#F28C28",
  titre_taille: 56,
  titre_position: 0.14
};

/* Couleur #RRGGBB -> &H00BBGGRR (format ASS). */
export function assColor(hex, alpha = "00") {
  const m = /^#?([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i.exec(hex || "");
  if (!m) return "&H00FFFFFF";
  return `&H${alpha}${m[3]}${m[2]}${m[1]}`.toUpperCase();
}

function ts(t) {
  t = Math.max(0, t);
  const h = Math.floor(t / 3600), m = Math.floor((t % 3600) / 60), s = Math.floor(t % 60), cs = Math.floor((t % 1) * 100);
  return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}.${String(cs).padStart(2, "0")}`;
}

const escapeAss = (s) => String(s).replace(/[{}\\]/g, "").replace(/\n/g, " ");

/* Regroupe les mots ({ mot, debut, fin }) par paquets, sans dépasser une pause de 0,6 s. */
export function groupWords(words, size = 2) {
  const groups = [];
  let cur = [];
  for (const w of words) {
    const prev = cur[cur.length - 1];
    if (cur.length >= size || (prev && w.debut - prev.fin > 0.6)) { groups.push(cur); cur = []; }
    cur.push(w);
  }
  if (cur.length) groups.push(cur);
  return groups;
}

/* words : [{ mot, debut, fin }] ; titles : [{ texte, debut, fin }] */
export function buildAss(words, titles = [], style = {}) {
  const s = { ...DEFAULT_STYLE, ...style };
  const bold = s.gras ? -1 : 0;
  const subY = Math.round(H * (1 - s.position_sous_titres));
  const titleY = Math.round(H * s.titre_position);
  const head = [
    "[Script Info]", "ScriptType: v4.00+", `PlayResX: ${W}`, `PlayResY: ${H}`, "WrapStyle: 0", "ScaledBorderAndShadow: yes", "",
    "[V4+ Styles]",
    "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
    `Style: Mots,${s.police},${s.taille},${assColor(s.couleur_texte)},${assColor(s.couleur_texte)},${assColor(s.couleur_contour)},&H80000000,${bold},0,0,0,100,100,0,0,1,${s.epaisseur_contour},2,2,60,60,${subY},1`,
    `Style: TitreBord,${s.police},${s.titre_taille},${assColor(s.titre_couleur_bordure)},${assColor(s.titre_couleur_bordure)},${assColor(s.titre_couleur_bordure)},&H00000000,-1,0,0,0,100,100,0,0,3,22,0,8,120,120,${titleY},1`,
    `Style: Titre,${s.police},${s.titre_taille},${assColor(s.titre_couleur_texte)},${assColor(s.titre_couleur_texte)},${assColor(s.titre_couleur_boite)},&H00000000,-1,0,0,0,100,100,0,0,3,17,0,8,120,120,${titleY},1`,
    "",
    "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
  ];
  const lines = [];
  for (const t of titles) {
    const txt = escapeAss(t.texte);
    lines.push(`Dialogue: 0,${ts(t.debut)},${ts(t.fin)},TitreBord,,0,0,0,,{\\fad(120,120)}${txt}`);
    lines.push(`Dialogue: 1,${ts(t.debut)},${ts(t.fin)},Titre,,0,0,0,,{\\fad(120,120)}${txt}`);
  }
  const active = assColor(s.couleur_mot_actif);
  for (const g of groupWords(words, s.mots_par_groupe)) {
    const end = g[g.length - 1].fin;
    /* Une ligne par mot prononcé : le mot en cours change de couleur, petit effet de « pop » à l'apparition. */
    g.forEach((w, k) => {
      const until = k < g.length - 1 ? g[k + 1].debut : end;
      const text = g.map((x, j) => {
        let m = escapeAss(x.mot.trim());
        if (s.majuscules) m = m.toUpperCase();
        return j === k ? `{\\c${active}}${m}{\\c${assColor(s.couleur_texte)}}` : m;
      }).join(" ");
      const pop = k === 0 ? "{\\fscx88\\fscy88\\t(0,90,\\fscx100\\fscy100)}" : "";
      lines.push(`Dialogue: 2,${ts(w.debut)},${ts(Math.max(until, w.debut + 0.05))},Mots,,0,0,0,,${pop}${text}`);
    });
  }
  return head.concat(lines).join("\n") + "\n";
}

/* Met la vidéo au format 9:16 et incruste sous-titres et titres. */
export async function renderFacecam(video, words, titles, style, out) {
  const dir = await mkdtemp(path.join(tmpdir(), "facecam-"));
  try {
    const ass = path.join(dir, "sous-titres.ass");
    await writeFile(ass, buildAss(words, titles, style));
    const esc = (p) => p.replace(/\\/g, "/").replace(/:/g, "\\:").replace(/'/g, "\\'");
    await run("ffmpeg", ["-y", "-loglevel", "error", "-i", video,
      "-vf", `scale=${W}:${H}:force_original_aspect_ratio=increase,crop=${W}:${H},setsar=1,subtitles='${esc(ass)}':fontsdir='${esc(FONTS)}'`,
      "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out]);
    return out;
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
}
