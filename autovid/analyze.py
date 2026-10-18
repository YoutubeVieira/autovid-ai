"""Analyse d'une vidéo de référence → « ADN » de montage (format, rythme, audio, mise en page)."""
import json
import re
from pathlib import Path

import numpy as np

from .media import audio_mono, gray_frames, info, run

SR = 22050
HOP = 512


def scene_cuts(path, threshold=0.25, min_gap=0.2):
    """Instants des coupes franches. Les détections trop rapprochées (flash, double image) sont fusionnées."""
    out = run(["ffmpeg", "-hide_banner", "-i", path, "-vf",
               f"select='gt(scene,{threshold})',showinfo", "-an", "-f", "null", "-"])
    cuts = []
    for t in (float(x) for x in re.findall(r"pts_time:([0-9.]+)", out)):
        if not cuts or t - cuts[-1] > min_gap:
            cuts.append(round(t, 3))
    return cuts


def motion_curve(path, fps=10):
    """Énergie de mouvement image par image (différence moyenne entre images), échantillonnée à `fps`."""
    frames = gray_frames(path, fps=fps, w=64, h=112)
    if len(frames) < 2:
        return np.zeros(1), fps
    diff = np.abs(np.diff(frames, axis=0)).mean(axis=(1, 2))
    return np.concatenate([[0.0], diff]), fps


def onset_envelope(samples):
    n = len(samples) // HOP
    if n < 4:
        return np.zeros(1)
    rms = np.sqrt((samples[: n * HOP].reshape(n, HOP) ** 2).mean(axis=1))
    return np.maximum(np.diff(rms, prepend=rms[0]), 0)


def beat_track(samples):
    """Tempo (BPM) par autocorrélation + grille de temps forts calée sur la meilleure phase."""
    env = onset_envelope(samples)
    hop_t = HOP / SR
    if env.max() <= 0:
        return {"bpm": None, "beats": [], "onsets": []}
    x = env - env.mean()
    ac = np.correlate(x, x, "full")[len(x) - 1:]
    lags = np.arange(len(ac)) * hop_t
    m = (lags >= 60 / 180) & (lags <= 60 / 60)
    period = lags[m][np.argmax(ac[m])]
    bpm = 60 / period
    while bpm > 160:   # on replie les tempos « double temps » dans une plage musicale lisible
        bpm /= 2
    while bpm < 70:
        bpm *= 2
    period = 60 / bpm
    step = period / hop_t
    phases = np.arange(0, step, 1)
    scores = [env[np.round(np.arange(p, len(env), step)).astype(int).clip(0, len(env) - 1)].sum() for p in phases]
    phase = phases[int(np.argmax(scores))] * hop_t
    duration = len(samples) / SR
    beats = [round(t, 3) for t in np.arange(phase, duration, period)]
    thr = env.mean() + 2 * env.std()
    onsets = [round(i * hop_t, 3) for i in range(1, len(env) - 1)
              if env[i] > thr and env[i] >= env[i - 1] and env[i] >= env[i + 1]]
    return {"bpm": round(float(bpm), 1), "beats": beats, "onsets": onsets}


def loudness(path):
    out = run(["ffmpeg", "-hide_banner", "-i", path, "-vn", "-af", "ebur128", "-f", "null", "-"])
    summary = out[out.rfind("Summary:"):]
    i = re.search(r"I:\s+(-?[0-9.]+) LUFS", summary)
    lra = re.search(r"LRA:\s+([0-9.]+) LU", summary)
    return {"integrated_lufs": float(i.group(1)) if i else None, "lra_lu": float(lra.group(1)) if lra else None}


def layout_per_second(path):
    """Devine la mise en page : 'plein cadre', 'bandes noires' ou 'fond flouté' (vidéo paysage dans un 9:16)."""
    frames = gray_frames(path, fps=1)
    res = []
    for f in frames:
        detail = np.abs(np.diff(f, axis=1)).mean(axis=1)  # netteté par ligne
        h = len(detail)
        top, mid, bot = detail[: h // 6].mean(), detail[h // 3: 2 * h // 3].mean(), detail[-h // 6:].mean()
        lum_edges = np.concatenate([f[: h // 8], f[-h // 8:]]).mean()
        if min(top, bot) < 0.25 * mid:
            res.append("bandes_noires" if lum_edges < 25 else "fond_flou")
        else:
            res.append("plein_cadre")
    return res


def analyze(path, out_dir=None):
    path = str(path)
    meta = info(path)
    cuts = scene_cuts(path)
    bounds = [0.0] + cuts + [meta["duration"]]
    shots = [round(b - a, 3) for a, b in zip(bounds, bounds[1:]) if b - a > 0.05]
    audio = beat_track(audio_mono(path, SR)) if meta["has_audio"] else {"bpm": None, "beats": [], "onsets": []}
    beat = 60 / audio["bpm"] if audio["bpm"] else None

    def near(t, grid, tol=0.1):
        return any(abs(t - g) <= tol for g in grid)

    layouts = layout_per_second(path)
    dna = {
        "fichier": Path(path).name,
        "format": {**meta, "ratio": f"{meta['width']}:{meta['height']}",
                   "vertical": meta["height"] > meta["width"]},
        "montage": {
            "nb_coupes": len(cuts),
            "coupes_s": cuts,
            "plans_s": shots,
            "duree_plan_moyenne_s": round(float(np.mean(shots)), 3) if shots else None,
            "duree_plan_mediane_s": round(float(np.median(shots)), 3) if shots else None,
            "coupes_par_minute": round(len(cuts) / meta["duration"] * 60, 1) if meta["duration"] else 0,
            "temps_par_plan": round(float(np.median(shots)) / beat, 2) if beat and shots else None,
        },
        "audio": {
            **(loudness(path) if meta["has_audio"] else {}),
            "bpm": audio["bpm"],
            "nb_attaques": len(audio["onsets"]),
            "coupes_sur_attaque_pct": round(100 * sum(near(c, audio["onsets"]) for c in cuts) / len(cuts)) if cuts else 0,
            "coupes_sur_temps_pct": round(100 * sum(near(c, audio["beats"]) for c in cuts) / len(cuts)) if cuts else 0,
        },
        "mise_en_page": {k: layouts.count(k) for k in sorted(set(layouts))},
        "mise_en_page_par_seconde": layouts,
    }
    if out_dir:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "adn.json").write_text(json.dumps(dna, indent=2, ensure_ascii=False))
        cols = 8
        rows = max(1, int(np.ceil(meta["duration"] * 2 / cols)))
        run(["ffmpeg", "-y", "-v", "error", "-i", path, "-vf",
             f"fps=2,scale=216:-1,tile={cols}x{rows}", "-frames:v", "1", out / "planche.jpg"])
    return dna


def summary(dna):
    f, m, a = dna["format"], dna["montage"], dna["audio"]
    lines = [
        f"# ADN — {dna['fichier']}",
        f"- Format : {f['width']}x{f['height']} ({'vertical 9:16' if f['vertical'] else 'horizontal'}), "
        f"{f['fps']} i/s, {f['duration']:.2f} s, vidéo {f['video_codec']}, audio {f['audio_codec']}, {f['bitrate_kbps']} kb/s",
        f"- Montage : {m['nb_coupes']} coupes, plan médian {m['duree_plan_mediane_s']} s, "
        f"{m['coupes_par_minute']} coupes/min, ≈ {m['temps_par_plan']} temps musicaux par plan",
        f"- Audio : {a.get('integrated_lufs')} LUFS, LRA {a.get('lra_lu')} LU, ~{a['bpm']} BPM, "
        f"{a['coupes_sur_attaque_pct']} % des coupes sur une attaque audio",
        f"- Mise en page (secondes) : {dna['mise_en_page']}",
    ]
    return "\n".join(lines)
