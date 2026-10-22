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


# --------------------------------------------------------------------------- kit « réaction » (phonk / drill 808)
# Profil mesuré sur la vidéo réaction de référence : ~71 % de l'énergie sous 120 Hz, très peu d'aigus.

def sub_boom(d=1.2):
    """Impact 808 : sub qui tombe 70 → 32 Hz, longue queue, attaque claquée."""
    t = _t(d)
    f = 32 + 38 * np.exp(-t * 9)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.6)
    click = _bp(rng.standard_normal(len(t)), 900, 4000) * np.exp(-t * 120) * 0.4
    return _stereo(np.tanh(2.6 * (body + click)) * 0.95)


def low_whoosh(d=0.5):
    """Souffle grave (moins de sifflement que le whoosh classique)."""
    t = _t(d)
    n = _bp(rng.standard_normal(len(t)), 120, 1100)
    env = np.sin(np.pi * (t / d) ** 0.8) ** 2
    return _stereo(n * env * 1.4)


def reverse_hit(d=0.45):
    """Montée inversée avant un impact."""
    t = _t(d)
    n = _bp(rng.standard_normal(len(t)), 300, 5000) * (t / d) ** 3
    tone = np.sin(2 * np.pi * np.cumsum(60 + 200 * (t / d)) / SR) * (t / d) ** 2 * 0.5
    return _stereo((n + tone) * 0.8)


LIB.update({"sub_boom": sub_boom, "low_whoosh": low_whoosh, "reverse_hit": reverse_hit})


# réglés pour coller au profil mesuré de la vidéo réaction : ~72 % sub, 19 % basses, 8 % médiums
BASS_GAIN, COW_GAIN, SNARE_GAIN, REESE_GAIN = 0.15, 1.2, 1.4, 1.3


def music_phonk(duration, bpm=143, seed=11):
    """Beat phonk/drill sombre : 808 qui glissent, kicks lourds, cowbell phonk, peu d'aigus."""
    r = np.random.default_rng(seed)
    beat = 60 / bpm
    n = int(duration * SR) + SR
    out = np.zeros((n, 2))

    def put(sig, at, gain=1.0):
        i = int(at * SR)
        if i < n:
            sig = sig[: n - i]
            out[i: i + len(sig)] += sig * gain

    tk = _t(0.45)
    kick = _stereo(np.tanh(4 * np.sin(2 * np.pi * np.cumsum(42 + 140 * np.exp(-tk * 38)) / SR) * np.exp(-tk * 9)))
    tc = _t(0.18)
    cow = _stereo(_bp(np.sign(np.sin(2 * np.pi * 540 * tc)) + np.sign(np.sin(2 * np.pi * 800 * tc)), 450, 2200)
                  * np.exp(-tc * 22) * 0.35)
    snare = _stereo(_bp(r.standard_normal(len(_t(0.22))), 180, 3500) * np.exp(-_t(0.22) * 18))
    hat = _stereo(_hp(r.standard_normal(len(_t(0.03))), 6000) * np.exp(-_t(0.03) * 120))
    notes = [43.65, 43.65, 51.91, 38.89]                       # Fa, Fa, Lab, Mib (graves)
    bars = int(duration / (4 * beat)) + 2
    for b in range(bars):
        t0 = b * 4 * beat
        for k in (0, 0.75, 2.5):
            put(kick, t0 + k * beat, 1.0)
        put(snare, t0 + 2 * beat, SNARE_GAIN)
        for k in np.arange(0, 4, 0.5):
            put(hat, t0 + k * beat, 0.12)
        for k, step in enumerate((0, 0.5, 1.5, 2, 3, 3.5)):     # cowbell phonk en motif syncopé
            put(cow * (1.0 + 0.5 * (k % 3 == 0)), t0 + step * beat, COW_GAIN)
        f0, f1 = notes[b % 4], notes[(b + 1) % 4]
        tb = _t(4 * beat)
        glide = f0 + (f1 - f0) * np.clip((tb - 3.4 * beat) / (0.5 * beat), 0, 1)   # glissé de 808 en fin de mesure
        bass = np.tanh(2.2 * np.sin(2 * np.pi * np.cumsum(glide) / SR)) * np.minimum(1, tb * 60) * np.exp(-tb * 0.35)
        put(_stereo(_lp(bass, 140)), t0, BASS_GAIN)
        # couche « reese » une octave au-dessus : remplit 120–500 Hz comme dans la référence
        reese = np.tanh(3 * (np.sin(2 * np.pi * np.cumsum(glide * 2) / SR) + np.sin(2 * np.pi * np.cumsum(glide * 2.01) / SR)))
        put(_stereo(_bp(reese, 120, 480) * np.minimum(1, tb * 8) * np.minimum(1, (4 * beat - tb) * 8)), t0, REESE_GAIN)
    return out[: int(duration * SR)]


# --------------------------------------------------------------------------- bruits de contact (selon le coup)

def slap(d=0.35):
    """Claque cuir / peau : attaque sèche dans les médiums-aigus (coup de pied qui touche, pao, gant)."""
    t = _t(d)
    n = rng.standard_normal(len(t))
    snap = _bp(n, 1200, 6000) * np.exp(-t * 90)
    body = _bp(n, 180, 900) * np.exp(-t * 30)
    return _stereo(np.tanh(2.5 * (snap + 0.8 * body)) * 0.9)


def bag_thump(d=0.8):
    """Sac de frappe : « boum » lourd et mat, puis la chaîne qui tinte."""
    t = _t(d)
    f = 60 + 50 * np.exp(-t * 25)
    thud = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 8)
    leather = _bp(rng.standard_normal(len(t)), 300, 2500) * np.exp(-t * 45)
    chain = sum(np.sin(2 * np.pi * fr * t) for fr in (3150, 4420, 5870)) * np.exp(-(t - 0.08).clip(0) * 9) \
        * (t > 0.08) * 0.05
    return _stereo(np.tanh(2.0 * (thud + 0.6 * leather)) * 0.9 + chain)


def body_thud(d=0.5):
    """Coup qui rentre dans le corps : sourd, étouffé."""
    t = _t(d)
    f = 90 + 60 * np.exp(-t * 30)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 14) + _lp(rng.standard_normal(len(t)), 700) * np.exp(-t * 35)
    return _stereo(np.tanh(2.2 * x) * 0.9)


def swish(d=0.28):
    """Coup dans le vide : souffle court et aigu."""
    t = _t(d)
    n = _bp(rng.standard_normal(len(t)), 1500, 7000)
    return _stereo(np.tanh(1.5 * n * np.sin(np.pi * t / d) ** 3) * 0.8)


def spin_whoosh(d=0.9):
    """Rotation (meia-lua, armada, aú) : souffle qui tourne gauche ↔ droite en montant."""
    t = _t(d)
    n = rng.standard_normal(len(t))
    lo = _bp(n, 150, 1200)
    hi = _bp(n, 1200, 5000) * (t / d)
    env = np.sin(np.pi * (t / d) ** 0.8) ** 2
    x = (lo + 0.7 * hi) * env * 1.3
    pan = np.sin(2 * np.pi * 1.6 * t)
    return np.stack([x * (1 - 0.8 * pan.clip(0)), x * (1 + 0.8 * pan.clip(-1, 0))], axis=1)


LIB.update({"slap": slap, "bag_thump": bag_thump, "body_thud": body_thud, "swish": swish, "spin_whoosh": spin_whoosh})


def contact_fx(contact, kind):
    """Bruits (nom, décalage, gain) au moment du contact selon ce qui est touché et le type de coup."""
    cible = contact.get("cible", "air")
    if cible == "aucun":
        return []
    if cible == "air":
        return [("swish", -0.12, 0.9)]
    if cible == "corps":
        return [("body_thud", 0.0, 1.0)] + ([("slap", 0.0, 0.7)] if kind in ("pied", "poing") else [])
    return [("bag_thump", 0.0, 1.0), ("slap", 0.0, 0.5 if kind == "genou" else 0.8)]   # sac / pao


# --------------------------------------------------------------------------- ambiance documentaire

def ambiance_sombre(duration, seed=5):
    """Nappe sombre de documentaire : drone grave qui respire, souffle filtré, battement sourd lent."""
    r = np.random.default_rng(seed)
    t = np.arange(int(duration * SR)) / SR
    lfo = 0.6 + 0.4 * np.sin(2 * np.pi * t / 11)
    drone = sum(np.sin(2 * np.pi * f * t + p) * g for f, p, g in ((55, 0, 0.5), (55.4, 1, 0.4), (82.4, 2, 0.25), (110.2, 0.5, 0.12)))
    air = _bp(r.standard_normal(len(t)), 300, 1400) * 0.06 * (0.5 + 0.5 * np.sin(2 * np.pi * t / 7 + 1))
    x = drone * 0.35 * lfo + air
    beat = np.zeros_like(t)                    # battement de cœur lointain toutes les 2,4 s
    th = _t(0.35)
    thump = np.sin(2 * np.pi * np.cumsum(48 + 30 * np.exp(-th * 30)) / SR) * np.exp(-th * 14)
    for start in np.arange(1.0, duration, 2.4):
        for off, g in ((0, 0.5), (0.28, 0.32)):
            i = int((start + off) * SR)
            seg = thump[: max(len(t) - i, 0)]
            beat[i: i + len(seg)] += seg * g
    x = x + beat * 0.6
    fade = np.minimum(1, np.minimum(t / 2.0, (duration - t) / 2.0).clip(0))
    return _stereo(np.tanh(x * 1.2) * 0.8 * fade)


def tension_hit(d=2.0):
    """Coup sourd de changement de chapitre, avec traîne grave."""
    t = _t(d)
    body = np.sin(2 * np.pi * np.cumsum(40 + 25 * np.exp(-t * 6)) / SR) * np.exp(-t * 1.8)
    air = _bp(rng.standard_normal(len(t)), 200, 3000) * np.exp(-t * 3) * 0.3
    return _stereo(np.tanh(1.8 * (body + air)) * 0.9)


LIB.update({"tension_hit": tension_hit})
