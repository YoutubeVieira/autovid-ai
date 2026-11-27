"""Pack 2 (CC0, synthese pure, aucun echantillon tiers): creatures, catastrophes, voix-effets (rires, pleurs, peur) et musiques.
Necessite numpy + scipy:   pip install numpy scipy      Usage: python3 make_sfx2.py [dossier]
Les sons de voix sont synthetises par formants: ils sonnent 'dessin anime', pas comme des enregistrements reels."""
import json
import os
import subprocess
import sys
import wave

import numpy as np
from scipy.signal import butter, lfilter, sosfilt

SR = 44100
out = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(11)
T = lambda d: np.arange(int(SR * d)) / SR


def env(n, a=0.01, r=0.1):
    e = np.ones(n)
    na, nr = max(1, int(a * SR)), max(1, int(r * SR))
    e[:na] = np.linspace(0, 1, na)
    e[-nr:] *= np.linspace(1, 0, nr)
    return e


def lp(x, fc, order=2):
    return sosfilt(butter(order, fc, "low", fs=SR, output="sos"), x)


def hp(x, fc, order=2):
    return sosfilt(butter(order, fc, "high", fs=SR, output="sos"), x)


def bp(x, f0, f1, order=2):
    return sosfilt(butter(order, [f0, f1], "band", fs=SR, output="sos"), x)


def norm(x, peak=0.89):
    m = np.max(np.abs(x)) or 1.0
    return x * (peak / m)


def mixin(*pairs, length=None):
    n = length or max(len(x) + int(o * SR) for x, o in pairs)
    m = np.zeros(n)
    for x, o in pairs:
        i = int(o * SR)
        m[i:i + len(x)] += x[: n - i]
    return m


# ---------- sources vocales (formants)
FORM = {"a": (800, 1200, 2800), "o": (500, 900, 2700), "u": (350, 700, 2600), "i": (300, 2300, 3000), "e": (450, 2100, 2800), "é": (400, 2200, 2900)}


def voice(f0_curve, dur, vowel="a", breath=0.03, vib=(0, 0), bw=90):
    """Train d'impulsions glottales a f0 variable filtre par 3 formants."""
    n = int(SR * dur)
    f0 = np.interp(np.arange(n), np.linspace(0, n, len(f0_curve)), f0_curve)
    if vib[0]:
        f0 = f0 * (1 + vib[1] * np.sin(2 * np.pi * vib[0] * T(dur)))
    ph = np.cumsum(f0) / SR
    src = (2 * (ph % 1.0) - 1.0)                       # dent de scie = riche en harmoniques
    src = src - lp(src, 80)                            # pas de continu
    src += breath * rng.standard_normal(n)
    y = np.zeros(n)
    for f, g in zip(FORM[vowel], (1.0, 0.7, 0.35)):
        y += g * bp(src, max(60, f - bw), min(SR / 2 - 100, f + bw), 2)
    return y


def save(name, x, desc, use, M, peak=0.89):
    x = norm(x, peak)
    path = os.path.join(out, name + ".wav")
    with wave.open(path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())
    M.append({"file": name + ".wav", "duration_s": round(len(x) / SR, 2), "description": desc, "use": use})


M = []

# ================= creatures et catastrophes
n = int(SR * 1.9)
t = T(1.9)
f0 = np.interp(np.arange(n), [0, n * .15, n * .55, n], [60, 95, 75, 45]) * (1 + 0.04 * np.sin(2 * np.pi * 26 * t))
ph = np.cumsum(f0) / SR
roar = np.tanh(3.0 * (2 * (ph % 1.0) - 1.0)) + 0.5 * rng.standard_normal(n) * np.interp(np.arange(n), [0, n * .3, n], [0.2, 0.7, 0.1])
roar = lp(bp(roar, 120, 2400), 2600) * env(n, 0.05, 0.5) * (0.75 + 0.25 * np.sin(2 * np.pi * 14 * t))
save("roar", roar, "Rugissement de grand dinosaure", "T-Rex, monstre", M)
n = int(SR * 0.9)
f0 = np.interp(np.arange(n), [0, n * .3, n], [300, 520, 260])
v = voice(f0, 0.9, "a", 0.05, (8, 0.05), 150)
save("roar_small", np.tanh(2 * v) * env(len(v), 0.03, 0.2), "Cri aigu de petit dinosaure", "petit dino, creature", M)
st = np.concatenate([lp(rng.standard_normal(int(SR * .25)), 140) * np.exp(-np.arange(int(SR * .25)) / SR * 14), np.zeros(int(SR * .25))])
save("stomp", mixin((st, 0), (st * 0.8, 0.55), (st * .6, 1.1)), "Pas lourds d'un dinosaure", "dino qui marche", M)
r = lp(rng.standard_normal(int(SR * 3.5)), 90) * env(int(SR * 3.5), 0.6, 1.0) * (0.7 + 0.3 * np.sin(2 * np.pi * 7 * T(3.5)))
save("rumble", r, "Grondement sourd (tremblement de terre)", "ambiance, avant le choc", M)
d = 2.6
n = int(SR * d)
fw = np.linspace(2600, 380, n) ** 1.0
whistle = np.sin(2 * np.pi * np.cumsum(fw) / SR) * 0.4 + hp(rng.standard_normal(n), 1200) * 0.35
save("meteor_whistle", whistle * np.linspace(0.1, 1, n) ** 1.6 * env(n, 0.05, 0.02), "Sifflement d'un astéroïde qui tombe", "météorite", M)
n = int(SR * 3.2)
e = np.exp(-np.arange(n) / SR * 1.6)
boom = lp(rng.standard_normal(n), 900) * e + np.sin(2 * np.pi * np.cumsum(np.linspace(75, 28, n)) / SR) * e * 1.2
save("explosion", np.tanh(1.6 * boom) * env(n, 0.002, 0.3), "Explosion / impact géant", "impact de l'astéroïde", M, 0.95)
n = int(SR * 5)
wind = bp(rng.standard_normal(n), 300, 1800) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.35 * T(5) + 1))
save("wind_ash", wind * env(n, 1.0, 1.2), "Vent et cendres", "ciel noir après l'impact", M, 0.6)

# ================= voix-effets: rires, pleurs, peur
def laugh(f0=210, n_ha=5, vowel="a", gap=0.07, ha=0.14):
    parts, pos = [], 0.0
    for i in range(n_ha):
        d = ha * (1 - 0.03 * i)
        f = f0 * (1 - 0.05 * i) * (1 + 0.05 * rng.standard_normal())
        v = voice([f * 1.15, f * 1.05, f * 0.9], d, vowel, 0.12, (0, 0), 120) * env(int(SR * d), 0.01, 0.05) * (1 - 0.08 * i)
        parts.append((v, pos))
        pos += d + gap
    return mixin(*parts)


save("laugh_man", laugh(125, 5), "Rire d'homme (ha ha ha)", "rire", M)
save("laugh_woman", laugh(235, 5), "Rire de femme", "rire", M)
save("laugh_child", laugh(380, 6, "é", 0.06, 0.11), "Rire d'enfant", "rire", M)
save("giggle", laugh(520, 7, "i", 0.05, 0.08), "Petit rire aigu / gloussement", "rire espiègle", M)
crowd = mixin(*[(laugh(rng.choice([120, 135, 210, 240, 300, 380]), int(rng.integers(4, 8)), "a", 0.06, 0.13) * rng.uniform(0.5, 1.0), float(rng.uniform(0, 1.3))) for _ in range(9)])
save("laugh_crowd", crowd + 0.04 * hp(rng.standard_normal(len(crowd)), 2000), "Rire de foule", "ambiance, humour", M)
cry = np.concatenate([voice(np.linspace(520, 400, 20), 0.55, "a", 0.04, (6.5, 0.04), 160) * env(int(SR * .55), 0.06, 0.15),
                      hp(rng.standard_normal(int(SR * .18)), 1500) * 0.15 * np.hanning(int(SR * .18)),
                      voice(np.linspace(540, 410, 20), 0.6, "a", 0.04, (6.5, 0.04), 160) * env(int(SR * .6), 0.06, 0.2)])
save("cry_baby", np.tanh(1.5 * cry), "Pleurs de bébé", "bébé, détresse", M)
sob = mixin(*[(voice(np.linspace(260, 190, 10), 0.28, "o", 0.1, (5, 0.05), 120) * env(int(SR * .28), 0.03, 0.12), 0.5 * k) for k in range(5)])
save("sob", sob + 0.03 * lp(rng.standard_normal(len(sob)), 800), "Sanglots (adulte)", "tristesse", M)
sc = voice(np.interp(np.linspace(0, 1, 40), [0, .25, 1], [520, 1250, 900]), 1.0, "a", 0.08, (9, 0.03), 200)
save("scream", np.tanh(3 * sc) * env(len(sc), 0.03, 0.25), "Cri de peur", "peur, danger", M)
n = int(SR * 0.5)
gasp = bp(rng.standard_normal(n), 800, 3500) * np.sin(np.linspace(0, np.pi, n)) ** 0.7
save("gasp", gasp, "Inspiration de surprise", "peur, étonnement", M)
oh = voice(np.linspace(300, 250, 10), 0.6, "o", 0.04, (5, 0.02), 120) * env(int(SR * .6), 0.08, 0.2)
save("oh_surprise", oh, "« Oooh » de surprise (homme)", "étonnement", M)
n = int(SR * 3.0)
clap = np.zeros(n)
for _ in range(120):
    i = int(rng.uniform(0, 2.6) * SR)
    c = hp(rng.standard_normal(int(SR * .03)), 900) * np.exp(-np.arange(int(SR * .03)) / SR * 150)
    clap[i:i + len(c)] += c * rng.uniform(0.3, 1.0)
save("applause", clap * env(n, 0.3, 0.6), "Applaudissements", "victoire, élection", M)

# ================= musiques (boucles)
NOTE = lambda m: 440.0 * 2 ** ((m - 69) / 12)


def tone(freq, dur, wave="square", vol=0.3, a=0.005, r=0.08):
    t = T(dur)
    ph = 2 * np.pi * freq * t
    w = {"square": np.sign(np.sin(ph)), "tri": 2 / np.pi * np.arcsin(np.sin(ph)), "sine": np.sin(ph), "saw": 2 * ((freq * t) % 1) - 1}[wave]
    return w * vol * env(len(t), a, min(r, dur))


def kick(d=0.25):
    t = T(d)
    return np.sin(2 * np.pi * np.cumsum(np.linspace(150, 45, len(t))) / SR) * np.exp(-t * 14) * 0.8


def snare(d=0.18):
    t = T(d)
    return (hp(rng.standard_normal(len(t)), 1500) * np.exp(-t * 22) * 0.45)


def hat(d=0.05):
    t = T(d)
    return hp(rng.standard_normal(len(t)), 6000) * np.exp(-t * 70) * 0.2


def music(name, desc, use, bpm, chords, lead_scale, bars, style):
    beat = 60 / bpm
    total = bars * 4 * beat
    m = np.zeros(int(SR * total) + SR)
    rnd = np.random.default_rng(abs(hash(name)) % 1000)
    for bar in range(bars):
        root, kind = chords[bar % len(chords)]
        triad = [root, root + (3 if kind == "m" else 4), root + 7]
        t0 = bar * 4 * beat
        for k in range(8):                                     # basse en croches
            x = tone(NOTE(root - 24), beat / 2, "tri" if style != "tense" else "saw", 0.34 if style != "tense" else 0.18, 0.005, 0.1)
            m = mixin((m, 0), (x, t0 + k * beat / 2), length=len(m))
        if style in ("fun", "win"):
            for k in range(16):                                # arpege
                x = tone(NOTE(triad[k % 3] + 12), beat / 4, "square", 0.12, 0.003, 0.05)
                m = mixin((m, 0), (x, t0 + k * beat / 4), length=len(m))
            for k in range(4):                                 # batterie
                m = mixin((m, 0), (kick(), t0 + k * beat), (hat(), t0 + k * beat + beat / 2), length=len(m))
                if k % 2 == 1:
                    m = mixin((m, 0), (snare(), t0 + k * beat), length=len(m))
            for k in range(4):                                 # melodie
                n_ = root + 12 + lead_scale[int(rnd.integers(0, len(lead_scale)))]
                x = tone(NOTE(n_), beat * rnd.choice([0.5, 1.0]), "square", 0.16, 0.005, 0.1)
                m = mixin((m, 0), (x, t0 + k * beat), length=len(m))
        elif style == "tense":
            for nn in triad:                                   # nappe sombre
                x = tone(NOTE(nn), 4 * beat, "saw", 0.07, 0.8, 1.2)
                m = mixin((m, 0), (lp(x, 900), t0), length=len(m))
            m = mixin((m, 0), (kick(0.4) * 0.8, t0), (kick(0.4) * 0.6, t0 + 2 * beat), length=len(m))
            m = mixin((m, 0), (tone(NOTE(root + 24 + (bar % 2)), 0.25, "sine", 0.1, 0.02, 0.2), t0 + 3 * beat), length=len(m))
        else:                                                  # calme
            for nn in triad:
                x = tone(NOTE(nn + 12), 4 * beat, "sine", 0.12, 1.0, 1.4)
                m = mixin((m, 0), (x, t0), length=len(m))
            for k in range(8):
                x = tone(NOTE(triad[k % 3] + 24), beat / 2, "sine", 0.1, 0.004, 0.25)
                m = mixin((m, 0), (x, t0 + k * beat / 2), length=len(m))
    m = m[: int(SR * total)]
    save(name, np.tanh(1.2 * m), desc, use, M, 0.8)


MAJ = [0, 2, 4, 7, 9]
music("music_aventure", "Boucle entraînante (chiptune, do majeur)", "épisodes, arrivée des habitants", 124, [(60, "M"), (67, "M"), (69, "m"), (65, "M")], MAJ, 8, "fun")
music("music_suspense", "Boucle de tension (la mineur)", "avant la catastrophe, mystère", 92, [(57, "m"), (53, "M"), (55, "M"), (57, "m")], MAJ, 8, "tense")
music("music_victoire", "Boucle de victoire (fanfare chiptune)", "palier atteint, élection", 132, [(65, "M"), (72, "M"), (67, "M"), (60, "M")], MAJ, 4, "win")
music("music_calme", "Boucle douce (nappes + pluck)", "monde vide, nouveau départ", 80, [(60, "M"), (57, "m"), (65, "M"), (67, "M")], MAJ, 8, "calm")

# fusion dans manifest.json
mp = os.path.join(out, "manifest.json")
man = json.load(open(mp, encoding="utf-8")) if os.path.exists(mp) else {"sounds": []}
have = {s["file"] for s in man["sounds"]}
man["sounds"] += [s for s in M if s["file"] not in have]
man["license"] = "CC0 1.0 - sons synthetises par make_sfx.py et make_sfx2.py, aucun echantillon tiers"
json.dump(man, open(mp, "w"), indent=2, ensure_ascii=False)
for f in [s["file"] for s in M if s["file"].startswith("music_")]:   # musiques en mp3 (poids du depot)
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", os.path.join(out, f), "-c:a", "libmp3lame", "-b:a", "128k",
                    os.path.join(out, f.replace(".wav", ".mp3"))], check=True)
    os.remove(os.path.join(out, f))
print(len(M), "sons ajoutes ->", out)
