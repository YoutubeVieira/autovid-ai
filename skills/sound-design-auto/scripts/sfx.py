#!/usr/bin/env python3
"""Sound design automatique : place un son sur chaque moment listé par l'animation, puis mixe avec la musique.

Les sons sont synthétisés ici (souffle « whoosh », « pop », petit « tick », « clic », respiration) :
aucun fichier extérieur, donc aucun problème de droits. Les moments viennent de la page HTML
(window.SFX), donc ils tombent exactement sur les animations.

    node render.js wellness-60.html --events sons.json
    python sfx.py sons.json --music musique.wav --out mix.wav [--video video-muette.mp4 --final video.mp4]
"""
import argparse, json, subprocess, wave
import numpy as np

SR = 44100
rng = np.random.default_rng(3)


def t_(d):
    return np.arange(int(d * SR)) / SR


def onepole_lowpass(x, fc):
    """Passe-bas dont la fréquence de coupure peut varier dans le temps (tableau ou nombre)."""
    fc = np.broadcast_to(np.asarray(fc, float), x.shape)
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x); acc = 0.0
    for i in range(len(x)):
        acc = (1 - a[i]) * x[i] + a[i] * acc
        y[i] = acc
    return y


def whoosh(d=0.75):
    t = t_(d); k = t / d
    env = np.sin(np.pi * k) ** 2
    noise = rng.standard_normal(len(t))
    sweep = 300 + 5200 * np.sin(np.pi * k) ** 1.5           # le souffle monte puis redescend
    lo = onepole_lowpass(noise, sweep)
    hi = noise - onepole_lowpass(noise, 200)                 # enlève le grave boueux
    s = env * (lo * 0.9 + 0.08 * onepole_lowpass(hi, sweep))
    pan = 0.2 + 0.6 * k                                      # passe de gauche à droite
    return np.stack([s * (1 - pan), s * pan], 1) * 0.9


def pop(d=0.16):
    t = t_(d)
    f = 520 * np.exp(-t * 18) + 380                          # petite goutte qui descend
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-t * 28) * np.minimum(1, t / 0.002)
    s += 0.25 * rng.standard_normal(len(t)) * np.exp(-t * 300)
    return np.stack([s, s], 1) * 0.55


def tick(d=0.09):
    t = t_(d)
    s = (np.sin(2 * np.pi * 1850 * t) + 0.5 * np.sin(2 * np.pi * 2780 * t)) * np.exp(-t * 60) * np.minimum(1, t / 0.001)
    return np.stack([s, s], 1) * 0.28


def click(d=0.12):
    t = t_(d)
    s = np.sin(2 * np.pi * 1200 * t) * np.exp(-t * 90) + 0.5 * rng.standard_normal(len(t)) * np.exp(-t * 400)
    s2 = np.concatenate([np.zeros(int(0.045 * SR)), s[: len(s) - int(0.045 * SR)] * 0.6])
    m = s + s2
    return np.stack([m, m], 1) * 0.45


def breath(d, rising):
    t = t_(d); k = t / d
    env = (np.sin(np.pi * k) ** 2) * (0.6 + 0.4 * (k if rising else 1 - k))
    n = rng.standard_normal(len(t))
    s = onepole_lowpass(n, 900 if rising else 650) * env
    return np.stack([s, s], 1) * 0.5


MAKERS = {"whoosh": lambda: whoosh(), "pop": lambda: pop(), "tick": lambda: tick(), "click": lambda: click(),
          "breathIn": lambda: breath(3.6, True), "breathOut": lambda: breath(4.4, False)}


def read_wav(path):
    with wave.open(path) as w:
        assert w.getsampwidth() == 2 and w.getframerate() == SR, "musique attendue en WAV 16 bits 44,1 kHz"
        x = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(float) / 32768
        return x.reshape(-1, w.getnchannels()) if w.getnchannels() == 2 else np.stack([x, x], 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("events")
    ap.add_argument("--music")
    ap.add_argument("--music-gain", type=float, default=0.75)
    ap.add_argument("--sfx-gain", type=float, default=0.8)
    ap.add_argument("--out", default="mix.wav")
    ap.add_argument("--video"); ap.add_argument("--final")
    a = ap.parse_args()
    ev = json.load(open(a.events, encoding="utf8"))
    n = int(ev["duration"] * SR)
    fx = np.zeros((n, 2))
    cache = {}
    for e in ev["sfx"]:
        s = cache.setdefault(e["type"], MAKERS[e["type"]]())
        i = int(e["t"] * SR)
        if i < 0 or i >= n:
            continue
        j = min(n, i + len(s))
        fx[i:j] += s[: j - i] * e.get("gain", 1)
    mix = fx * a.sfx_gain
    if a.music:
        mu = read_wav(a.music)[:n]
        mix[: len(mu)] += mu * a.music_gain
    peak = np.abs(mix).max()
    if peak > 0.97:
        mix *= 0.97 / peak
    with wave.open(a.out, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).astype("<i2").tobytes())
    print(f"{len(ev['sfx'])} sons placés. Mixage : {a.out}")
    if a.video and a.final:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", a.video, "-i", a.out, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "192k", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-shortest", "-movflags", "+faststart", a.final], check=True)
        print("Vidéo finale :", a.final)


if __name__ == "__main__":
    main()
