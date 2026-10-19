"""Mode « fun » : clip court d'humour, d'animaux ou généré par IA, sans analyse anatomique.

Accroche en deux lignes, ralenti + zoom sur le moment fort (pic de mouvement), flash, tremblement, micro-pause,
beat phonk et bruitages calés, son d'origine gardé dessous, mention « VIDÉO GÉNÉRÉE PAR IA » si demandée.
"""
import subprocess
from pathlib import Path

import cv2
import numpy as np

from . import gfx, sfx
from .analyze import motion_curve
from .combat import normalize
from .media import FPS, H, W, info
from .pose import iter_frames
from .render import match_loudness

SLOW = 0.4             # vitesse du ralenti
PRE = 1.4              # secondes (source) ralenties avant le moment fort
HIT = 8                # images de micro-pause
DEFAULT_TEXTS = [("ATTENDS", "LA SUITE"), ("REGARDE", "BIEN"), ("", "")]


def peak_frame(path, n):
    """Image du moment fort : le pic de mouvement, en évitant le tout début et la toute fin."""
    curve, fps = motion_curve(path, fps=10)
    t = np.arange(len(curve)) / fps
    lo, hi = 0.2 * n / FPS, 0.85 * n / FPS
    ok = (t >= lo) & (t <= hi)
    if not ok.any():
        return n // 2
    smooth = np.convolve(curve, np.ones(3) / 3, mode="same")
    return int(t[ok][np.argmax(smooth[ok])] * FPS)


def build_timeline(n, peak, max_before=4.0, max_after=6.0):
    """[(image source, phase, temps local)] : normal → ralenti → micro-pause → normal."""
    start = max(0, int(peak - (PRE + max_before) * FPS))
    s0 = max(start, int(peak - PRE * FPS))
    end = min(n, int(peak + max_after * FPS))
    tl = [(i, "hook", (i - start) / FPS) for i in range(start, s0)]
    steps = int((peak - s0) / SLOW)
    tl += [(s0 + j * SLOW, "slow", j / FPS) for j in range(steps)]
    tl += [(peak, "hit", j / FPS) for j in range(HIT)]
    tl += [(i, "after", (i - peak) / FPS) for i in range(peak, end)]
    return tl


def fun(src, out, workdir, texts=None, handle=None, ai=None, label_ia=None, music=None, accent=gfx.ORANGE,
        projet=None):
    """texts : 3 paires (ligne 1, ligne 2) pour le début, le ralenti et la fin. label_ia : True / False / None
    (None = demandé à Claude avec --ai, sinon pas de mention). projet : projet.json modifié dans la plateforme."""
    from . import projet as pj_mod
    pj = pj_mod.load(projet)
    peak_at = None
    if pj:
        texts = [tuple(t)[:2] for t in pj.get("textes", [])] or texts
        label_ia = pj.get("mention_ia", label_ia)
        peak_at = pj.get("moment_fort")
        r = pj.get("reglages", {})
        handle = r.get("handle", handle) or None
        accent = pj_mod.hex_rgb(r.get("accent")) or accent
    work = Path(workdir)
    work.mkdir(parents=True, exist_ok=True)
    out = Path(out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    base = work / "base.mp4"
    print("1/4 normalisation 9:16")
    normalize(str(src), base)
    n = int(round(info(str(base))["duration"] * FPS))
    peak = int(float(peak_at) * FPS) if peak_at is not None else peak_frame(str(base), n)
    peak = min(max(peak, 1), n - 1)
    tl = build_timeline(n, peak)
    print(f"2/4 moment fort à {peak / FPS:.2f} s → montage de {len(tl) / FPS:.1f} s")
    if not texts and ai:
        from .ai import fun_texts
        got = fun_texts(base, [int(n * 0.1), peak, int(n * 0.9)])
        if got:
            texts, guess = got
            label_ia = guess if label_ia is None else label_ia
    texts = [tuple(t) for t in (texts or DEFAULT_TEXTS)] + [("", "")] * 3
    by_phase = {"hook": texts[0], "slow": texts[1], "hit": texts[1], "after": texts[2]}
    print("   textes : " + " | ".join(" / ".join(t) for t in texts[:3] if any(t)))

    print("3/4 rendu image par image")
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-vf", "noise=alls=4:allf=t,vignette=angle=PI/5",
                            "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-maxrate", "16M", "-bufsize", "32M",
                            "-pix_fmt", "yuv420p", str(work / "video.mp4")], stdin=subprocess.PIPE)
    rng = np.random.default_rng(1)
    src_h = min(info(str(src))["height"], info(str(src))["width"] * 16 / 9)
    zmax = float(np.clip(src_h / 900, 1.25, 1.5))         # source basse définition : zoom plus doux
    center = np.array([W * 0.5, H * 0.4])
    slow_len = sum(1 for _, ph, _ in tl if ph == "slow") / FPS
    stream = iter_frames(base, W, H, start=tl[0][0] / FPS if tl[0][0] else None)
    buf, idx = {}, int(tl[0][0]) - 1           # la timeline avance toujours : lecture en flux, 3 images en mémoire
    for k, (s, ph, lt) in enumerate(tl):
        while idx < int(s) + 1:
            nxt = next(stream, None)
            if nxt is None:
                break
            idx += 1
            buf[idx] = nxt
            buf.pop(idx - 3, None)
        lo = min(int(s), idx)
        fr = s - lo
        img = buf.get(lo, buf[max(buf)]).astype(np.float32)
        if fr > 1e-3 and lo + 1 in buf:
            img = img * (1 - fr) + buf[lo + 1] * fr
        z = {"slow": 1 + (zmax - 1) * gfx.ease(lt / max(slow_len, 0.1)), "hit": zmax,
             "after": zmax - (zmax - 1) * gfx.ease(lt / 0.6)}.get(ph, 1.0)
        dx = dy = 0.0
        if ph == "hit" or (ph == "after" and lt < 0.12):
            a = 16 * (1 - min((lt if ph == "hit" else HIT / FPS + lt) / 0.4, 1))
            dx, dy = rng.uniform(-a, a, 2)
        if z > 1.001 or dx or dy:
            M = np.array([[z, 0, W / 2 - z * center[0] + dx], [0, z, H * 0.45 - z * center[1] + dy]])
            img = cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REFLECT)
        if (ph == "hit" and lt < 0.1) or (ph == "slow" and lt < 0.08):
            a = 0.6 * (1 - lt / 0.1)
            img = img * (1 - a) + 255 * a
            img[:, 8:, 0] = img[:, :-8, 0].copy()
            img[:, :-8, 2] = img[:, 8:, 2].copy()
        l1, l2 = by_phase[ph]
        t0 = 3.0 if ph == "hit" else lt
        if l1:
            gfx.paste(img, gfx.text_sprite(l1, 104, gfx.WHITE, stroke=9), W / 2, 330, gfx.pop(t0))
        if l2:
            gfx.paste(img, gfx.text_sprite(l2, 118, gfx.YELLOW, stroke=9), W / 2, 460, gfx.pop(t0 - 0.15))
        if label_ia:
            gfx.paste(img, gfx.text_sprite("VIDÉO GÉNÉRÉE PAR IA", 30, gfx.WHITE, stroke=3, shadow=3), W / 2, 150, 1, 0.6)
        if handle:
            gfx.paste(img, gfx.text_sprite(handle, 40, gfx.WHITE, stroke=3, shadow=4), W / 2, 1745, 1, 0.55)
        prog = int(W * (k + 1) / len(tl))
        img[0:12, :prog] = img[0:12, :prog] * 0.1 + np.array(accent, np.float32) * 0.9
        enc.stdin.write(np.clip(img, 0, 255).astype(np.uint8).tobytes())
    enc.stdin.close()
    enc.wait()

    print("4/4 son + export")
    sr, spf = sfx.SR, sfx.SR // FPS
    N = len(tl) * spf
    if music:
        mus = sfx.read_wav(music)
        mus = np.tile(mus, (int(np.ceil(N / max(len(mus), 1))), 1))[:N] if len(mus) else np.zeros((N, 2))
    else:
        mus = sfx.music_phonk(N / sr + 0.1)[:N]
    mix = mus * 0.5
    if info(str(src))["has_audio"]:
        orig = sfx.read_wav(str(src))
        o = np.zeros((N, 2))
        for k, (s, ph, _) in enumerate(tl):
            if ph in ("hook", "after"):
                ch = orig[int(s * spf): int(s * spf) + spf]
                o[k * spf: k * spf + len(ch)] = ch
        mix = mix + o * 0.6

    def put(name, t, g=1.0, **kw):
        x = sfx.LIB[name](**kw) * g
        i = int(t * sr)
        if 0 <= i < N:
            x = x[: N - i]
            mix[i: i + len(x)] += x * 0.8

    t_slow = next((k for k, f in enumerate(tl) if f[1] == "slow"), 0) / FPS
    t_hit = next((k for k, f in enumerate(tl) if f[1] == "hit"), 0) / FPS
    put("low_whoosh", t_slow, 0.9, d=0.5)
    put("reverse_hit", max(t_hit - 0.45, 0), 0.8)
    put("swish", max(t_hit - 0.1, 0), 0.9)
    put("sub_boom", t_hit, 1.0)
    put("slap", t_hit, 0.6)
    put("shutter", t_hit, 0.4)
    put("low_whoosh", t_hit + HIT / FPS, 0.6, d=0.4)
    sfx.write_wav(work / "audio.wav", mix / (np.abs(mix).max() or 1) * 0.9)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(work / "video.mp4"), "-i", str(work / "audio.wav"),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    str(work / "mux.mp4")], check=True)
    match_loudness(str(work / "mux.mp4"), str(out), -14)
    pj_mod.save({"mode": "fun", "source": str(Path(src).resolve()), "moment_fort": round(peak / FPS, 2),
                 "duree_source": round(n / FPS, 2), "textes": [list(t) for t in texts[:3]],
                 "mention_ia": bool(label_ia), "reglages": {"handle": handle or "", "accent": pj_mod.rgb_hex(accent)},
                 "notes": ""}, out.with_suffix(".projet.json"))
    return str(out)
