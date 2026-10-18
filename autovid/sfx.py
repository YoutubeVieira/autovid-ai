"""Bruitages et musique générés par synthèse (libres de droits, aucun fichier externe)."""
import wave

import numpy as np
from scipy.signal import butter, sosfilt

SR = 48000
rng = np.random.default_rng(7)


def _t(d):
    return np.arange(int(d * SR)) / SR


def _bp(x, lo, hi):
    return sosfilt(butter(2, [lo, hi], btype="band", fs=SR, output="sos"), x)


def _lp(x, f):
    return sosfilt(butter(2, f, btype="low", fs=SR, output="sos"), x)


def _hp(x, f):
    return sosfilt(butter(2, f, btype="high", fs=SR, output="sos"), x)


def _stereo(x, pan=0.0):
    return np.stack([x * (1 - max(pan, 0)), x * (1 + min(pan, 0))], axis=1)


def whoosh(d=0.45):
    """Souffle filtré qui monte puis s'éteint, balayé gauche → droite."""
    t = _t(d)
    n = rng.standard_normal(len(t))
    env = np.sin(np.pi * (t / d) ** 0.7) ** 2
    lo = _bp(n, 300, 1500) * (1 - t / d)
    hi = _bp(n, 1500, 6000) * (t / d)
    x = (lo + hi) * env
    pan = np.linspace(-0.8, 0.8, len(t))
    return np.stack([x * (1 - np.clip(pan, 0, 1)), x * (1 + np.clip(pan, -1, 0))], axis=1) * 0.9


def impact(d=0.9):
    """Coup sourd : sub qui chute 110 → 38 Hz + claquement + saturation."""
    t = _t(d)
    f = 38 + 72 * np.exp(-t * 18)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4.5)
    crack = _hp(rng.standard_normal(len(t)), 1800) * np.exp(-t * 60)
    body = _bp(rng.standard_normal(len(t)), 120, 900) * np.exp(-t * 14)
    x = np.tanh(2.2 * (sub + 0.55 * crack + 0.5 * body)) * 0.95
    return _stereo(x)


def riser(d=0.6):
    t = _t(d)
    f = 250 + 1600 * (t / d) ** 2
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.25
    noise = _hp(rng.standard_normal(len(t)), 2500) * 0.35
    return _stereo((tone + noise) * (t / d) ** 2.2)


def tick(d=0.07, f=1900):
    t = _t(d)
    return _stereo(np.sin(2 * np.pi * f * t) * np.exp(-t * 70) * 0.5)


def shutter():
    """Bruit d'arrêt sur image (déclic + souffle court)."""
    t = _t(0.25)
    click = _hp(rng.standard_normal(len(t)), 3000) * np.exp(-t * 90)
    air = _bp(rng.standard_normal(len(t)), 800, 4000) * np.exp(-t * 18) * 0.3
    return _stereo(click + air) * 0.7


LIB = {"whoosh": whoosh, "impact": impact, "riser": riser, "tick": tick, "shutter": shutter}


def music(duration, bpm=140, seed=3):
    """Beat type « drill / trap » sombre : kick, clap, charleston, 808, nappe. Mono-tempo, en boucle."""
    r = np.random.default_rng(seed)
    beat = 60 / bpm
    n = int(duration * SR) + SR
    out = np.zeros((n, 2))

    def put(sig, at, gain=1.0):
        i = int(at * SR)
        if i >= n:
            return
        sig = sig[: n - i]
        out[i: i + len(sig)] += sig * gain

    t = _t(0.5)
    kick = _stereo(np.tanh(3 * np.sin(2 * np.pi * np.cumsum(45 + 110 * np.exp(-t * 30)) / SR) * np.exp(-t * 7)))
    clap = _stereo(_bp(r.standard_normal(len(_t(0.2))), 900, 5000) * np.exp(-_t(0.2) * 25))
    hat = _stereo(_hp(r.standard_normal(len(_t(0.05))), 7000) * np.exp(-_t(0.05) * 90))
    roots = [55.0, 43.65, 65.41, 49.0]          # La, Fa, Do, Sol (graves)
    bars = int(duration / (4 * beat)) + 2
    for b in range(bars):
        t0 = b * 4 * beat
        for k in (0, 1.5, 2.5) if b % 2 == 0 else (0, 0.75, 2.5, 3.25):
            put(kick, t0 + k * beat, 0.9)
        for k in (1, 3):
            put(clap, t0 + k * beat, 0.55)
        for k in np.arange(0, 4, 0.5):
            put(hat, t0 + k * beat, 0.25 if k % 1 else 0.35)
        if b % 4 == 3:                          # roulement de charleston en fin de phrase
            for k in np.arange(3, 4, 0.125):
                put(hat, t0 + k * beat, 0.2)
        f = roots[b % 4]
        tb = _t(4 * beat)
        bass = np.tanh(1.8 * np.sin(2 * np.pi * f * tb)) * np.minimum(1, tb * 40) * np.exp(-tb * 0.5)
        put(_stereo(_lp(bass, 180)), t0, 0.55)
        pad = sum(np.sin(2 * np.pi * f * m * 2 * tb + r.uniform(0, 6)) for m in (1, 1.189, 1.498))
        env = np.minimum(1, tb * 2) * np.minimum(1, (4 * beat - tb) * 4)
        put(_stereo(_lp(pad, 900) * env), t0, 0.06)
    return out[: int(duration * SR)]


def read_wav(path):
    """Lit un fichier audio quelconque (via ffmpeg) en float stéréo 48 kHz."""
    import subprocess
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                       capture_output=True)
    if p.returncode != 0 or not p.stdout:
        return np.zeros((0, 2))
    return np.frombuffer(p.stdout, np.float32).reshape(-1, 2).astype(np.float64)


def write_wav(path, x):
    x = np.clip(x, -1, 1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype("<i2").tobytes())
