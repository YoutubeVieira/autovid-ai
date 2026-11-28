"""Musiques et ambiances VARIEES (CC0, synthese): une nouvelle piste a chaque graine.
    python3 make_music.py --mood suspense --seed 7 --out music_gen/suspense_7.mp3
    python3 make_music.py --ambiance pluie --seed 3 --out music_gen/pluie_3.mp3
Humeurs: aventure, suspense, victoire, calme, joyeux, melancolique. Ambiances: pluie, vent, oiseaux, grillons, foule, riviere.
Necessite numpy + scipy (pip install numpy scipy) et ffmpeg."""
import argparse
import os
import subprocess
import tempfile
import wave

import numpy as np
from scipy.signal import butter, sosfilt

SR = 44100
MOODS = {  # tempo, gammes, progressions (degres, qualite), style
    "aventure": dict(bpm=(112, 132), scales=["maj", "pent"], keys=[60, 62, 65, 67], prog=[[(0, "M"), (7, "M"), (9, "m"), (5, "M")], [(0, "M"), (5, "M"), (7, "M"), (0, "M")], [(9, "m"), (5, "M"), (0, "M"), (7, "M")]], style="fun"),
    "joyeux": dict(bpm=(120, 140), scales=["maj", "pent"], keys=[62, 64, 67, 69], prog=[[(0, "M"), (5, "M"), (9, "m"), (7, "M")], [(0, "M"), (9, "m"), (5, "M"), (7, "M")]], style="fun"),
    "suspense": dict(bpm=(84, 100), scales=["min"], keys=[57, 59, 52, 54], prog=[[(0, "m"), (8, "M"), (7, "M"), (0, "m")], [(0, "m"), (5, "m"), (7, "M"), (0, "m")], [(0, "m"), (1, "M"), (0, "m"), (11, "M")]], style="tense"),
    "melancolique": dict(bpm=(66, 80), scales=["min"], keys=[57, 60, 62], prog=[[(0, "m"), (8, "M"), (3, "M"), (7, "M")], [(0, "m"), (5, "m"), (8, "M"), (7, "M")]], style="calm"),
    "calme": dict(bpm=(72, 88), scales=["maj", "pent"], keys=[60, 65, 67], prog=[[(0, "M"), (9, "m"), (5, "M"), (7, "M")], [(0, "M"), (5, "M"), (0, "M"), (7, "M")]], style="calm"),
    "victoire": dict(bpm=(126, 140), scales=["maj"], keys=[65, 67, 72], prog=[[(0, "M"), (7, "M"), (5, "M"), (0, "M")]], style="win"),
}
SCALES = {"maj": [0, 2, 4, 5, 7, 9, 11], "pent": [0, 2, 4, 7, 9], "min": [0, 2, 3, 5, 7, 8, 10]}
T = lambda d: np.arange(int(SR * d)) / SR


def env(n, a, r):
    e = np.ones(n)
    na, nr = max(1, int(a * SR)), max(1, min(n, int(r * SR)))
    e[:na] = np.linspace(0, 1, na)
    e[-nr:] *= np.linspace(1, 0, nr)
    return e


def tone(freq, dur, wave="square", vol=0.3, a=0.005, r=0.08):
    t = T(dur)
    ph = 2 * np.pi * freq * t
    w = {"square": np.sign(np.sin(ph)), "tri": 2 / np.pi * np.arcsin(np.sin(ph)), "sine": np.sin(ph), "saw": 2 * ((freq * t) % 1) - 1}[wave]
    return w * vol * env(len(t), a, min(r, dur))


def lp(x, fc):
    return sosfilt(butter(2, fc, "low", fs=SR, output="sos"), x)


def hp(x, fc):
    return sosfilt(butter(2, fc, "high", fs=SR, output="sos"), x)


def bp(x, a, b):
    return sosfilt(butter(2, [a, b], "band", fs=SR, output="sos"), x)


def put(buf, x, t0):
    i = int(t0 * SR)
    if i < len(buf):
        buf[i:i + len(x)] += x[: len(buf) - i]


NOTE = lambda m: 440.0 * 2 ** ((m - 69) / 12)


def compose(mood, seed, bars=8):
    cfg = MOODS[mood]
    rnd = np.random.default_rng(seed)
    bpm = int(rnd.integers(cfg["bpm"][0], cfg["bpm"][1] + 1))
    key = int(rnd.choice(cfg["keys"]))
    scale = SCALES[str(rnd.choice(cfg["scales"]))]
    prog = cfg["prog"][int(rnd.integers(0, len(cfg["prog"])))]
    beat = 60 / bpm
    total = bars * 4 * beat
    m = np.zeros(int(SR * total) + SR)
    wave_lead = str(rnd.choice(["square", "tri", "saw"]))
    motif = [int(rnd.choice(scale)) for _ in range(4)]
    for bar in range(bars):
        deg, q = prog[bar % len(prog)]
        root = key + deg
        triad = [root, root + (3 if q == "m" else 4), root + 7]
        t0 = bar * 4 * beat
        for k in range(8):
            put(m, tone(NOTE(root - 24), beat / 2, "tri" if cfg["style"] != "tense" else "saw", 0.34 if cfg["style"] != "tense" else 0.17), t0 + k * beat / 2)
        if cfg["style"] in ("fun", "win"):
            pat = rnd.permutation(3)
            for k in range(16):
                put(m, tone(NOTE(triad[pat[k % 3]] + 12), beat / 4, "square", 0.11, 0.003, 0.05), t0 + k * beat / 4)
            for k in range(4):
                kick = np.sin(2 * np.pi * np.cumsum(np.linspace(150, 45, int(0.25 * SR))) / SR) * np.exp(-T(0.25) * 14) * 0.8
                put(m, kick, t0 + k * beat)
                put(m, hp(rnd.standard_normal(int(0.05 * SR)), 6000) * np.exp(-T(0.05) * 70) * 0.2, t0 + k * beat + beat / 2)
                if k % 2:
                    put(m, hp(rnd.standard_normal(int(0.18 * SR)), 1500) * np.exp(-T(0.18) * 22) * 0.45, t0 + k * beat)
            for k in range(4):
                n_ = root + 12 + (motif[k] if bar % 2 == 0 else int(rnd.choice(scale)))
                put(m, tone(NOTE(n_), beat * float(rnd.choice([0.5, 1.0])), wave_lead, 0.15, 0.005, 0.1), t0 + k * beat)
        elif cfg["style"] == "tense":
            for nn in triad:
                put(m, lp(tone(NOTE(nn), 4 * beat, "saw", 0.07, 0.8, 1.2), 900), t0)
            put(m, np.sin(2 * np.pi * np.cumsum(np.linspace(120, 40, int(0.4 * SR))) / SR) * np.exp(-T(0.4) * 9) * 0.8, t0)
            put(m, tone(NOTE(root + 24 + (bar % 2)), 0.25, "sine", 0.1, 0.02, 0.2), t0 + 3 * beat)
        else:
            for nn in triad:
                put(m, tone(NOTE(nn + 12), 4 * beat, "sine", 0.12, 1.0, 1.4), t0)
            for k in range(8):
                put(m, tone(NOTE(triad[(k + bar) % 3] + 24), beat / 2, "sine", 0.1, 0.004, 0.25), t0 + k * beat / 2)
    return np.tanh(1.2 * m[: int(SR * total)]), dict(mood=mood, seed=seed, bpm=bpm, key=key, duree=round(total, 1))


def ambiance(kind, seed, dur=24.0):
    rnd = np.random.default_rng(seed)
    n = int(SR * dur)
    t = T(dur)
    if kind == "pluie":
        x = hp(rnd.standard_normal(n), 1200) * 0.5 + bp(rnd.standard_normal(n), 300, 900) * 0.2
    elif kind == "vent":
        x = bp(rnd.standard_normal(n), 200, 1500) * (0.5 + 0.5 * np.sin(2 * np.pi * (0.12 + 0.1 * rnd.random()) * t))
    elif kind == "riviere":
        x = lp(rnd.standard_normal(n), 2500) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.7 * t + rnd.random() * 6)) * 0.6 + hp(rnd.standard_normal(n), 3000) * 0.08
    elif kind == "grillons":
        x = np.zeros(n)
        for _ in range(int(dur * 3)):
            f0, t0 = 3800 + rnd.random() * 1200, rnd.random() * (dur - 0.6)
            for k in range(int(rnd.integers(3, 6))):
                put(x, np.sin(2 * np.pi * f0 * T(0.04)) * np.hanning(int(0.04 * SR)) * 0.25, t0 + k * 0.07)
        x += lp(rnd.standard_normal(n), 400) * 0.03
    elif kind == "oiseaux":
        x = np.zeros(n)
        for _ in range(int(dur * 1.4)):
            f0, d, t0 = 2200 + rnd.random() * 2200, 0.12 + rnd.random() * 0.2, rnd.random() * (dur - 0.5)
            for k in range(int(rnd.integers(1, 5))):
                f = np.interp(np.arange(int(d * SR)), [0, d * SR * 0.5, d * SR], [f0, f0 * (1.2 + rnd.random() * 0.4), f0 * 0.9])
                put(x, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.hanning(int(d * SR)) * 0.3, t0 + k * (d + 0.05))
        x += bp(rnd.standard_normal(n), 300, 1200) * 0.03
    elif kind == "foule":
        x = bp(rnd.standard_normal(n), 250, 2200) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.3 * t + rnd.random() * 6) * np.sin(2 * np.pi * 1.7 * t)) * 0.6
    else:
        raise ValueError(kind)
    x = x * np.minimum(1, np.minimum(t, dur - t) / 1.0)           # fondu entree/sortie 1 s
    return x, dict(ambiance=kind, seed=seed, duree=dur)


def save_mp3(x, path):
    x = x * (0.8 / (np.max(np.abs(x)) or 1))
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        w = os.path.join(tmp, "a.wav")
        with wave.open(w, "w") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(SR)
            f.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", w, "-c:a", "libmp3lame", "-b:a", "128k", path], check=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mood", choices=list(MOODS))
    ap.add_argument("--ambiance")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    x, info = compose(a.mood, a.seed) if a.mood else ambiance(a.ambiance, a.seed)
    save_mp3(x, a.out)
    print(info, "->", a.out)
