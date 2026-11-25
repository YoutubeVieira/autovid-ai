#!/usr/bin/env python3
"""Musique d'ambiance originale et douce (nappes d'accords + petite mélodie + carillon à chaque exercice).
Aucune source extérieure : tout est synthétisé, donc libre de droits.

    python music.py --duration 214.8 --chimes 30.2,50.8 --out musique.wav
"""
import argparse, wave
import numpy as np

SR = 44100


def note(f, dur, amp, attack=1.5, release=2.5):
    t = np.arange(int(dur * SR)) / SR
    env = np.minimum(1, t / attack) * np.minimum(1, (dur - t) / release).clip(0)
    # son doux : fondamentale + octave légère + léger désaccord (chorus)
    s = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 1.003 * t) + 0.18 * np.sin(2 * np.pi * 2 * f * t)
    return amp * env * s


def bell(f, dur=3.0, amp=0.25):
    t = np.arange(int(dur * SR)) / SR
    env = np.exp(-t * 2.2) * np.minimum(1, t / 0.005)
    return amp * env * (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 4))


def midi(n):
    return 440 * 2 ** ((n - 69) / 12)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration", type=float, required=True)
    ap.add_argument("--chimes", default="")
    ap.add_argument("--out", default="musique.wav")
    a = ap.parse_args()
    n = int((a.duration + 4) * SR)
    L, R = np.zeros(n), np.zeros(n)

    def add(sig, at, pan=0.5):
        i = int(at * SR); j = min(n, i + len(sig))
        L[i:j] += sig[: j - i] * (1 - pan); R[i:j] += sig[: j - i] * pan

    # progression : Cmaj9 - Am7 - Fmaj7 - G6, 8 s par accord
    chords = [[48, 55, 64, 71, 74], [45, 52, 60, 67, 72], [41, 53, 57, 64, 69], [43, 50, 59, 64, 67]]
    bar = 8.0
    rng = np.random.default_rng(7)
    k = 0
    while k * bar < a.duration:
        ch = chords[k % 4]
        for m, nn in enumerate(ch):
            add(note(midi(nn), bar + 2.5, 0.05 if m else 0.07), k * bar, pan=0.3 + 0.1 * m)
        # mélodie : quelques notes de piano doux, pentatonique, pas à chaque mesure
        if k % 2 == 1 or k > 3:
            scale = [72, 74, 76, 79, 81, 84]
            for b in range(4):
                if rng.random() < 0.55:
                    add(bell(midi(int(rng.choice(scale))), 2.5, 0.07), k * bar + b * 2 + 0.5, pan=rng.uniform(0.3, 0.7))
        k += 1

    for c in [float(x) for x in a.chimes.split(",") if x.strip()]:
        add(bell(midi(84), 3, 0.18), c, 0.45); add(bell(midi(91), 3, 0.12), c + 0.12, 0.55)

    # écho léger pour l'espace
    for d, g in ((0.29, 0.25), (0.53, 0.15)):
        s = int(d * SR)
        L[s:] += g * R[:-s]; R[s:] += g * L[:-s]
    # fondu de fin
    t = np.arange(n) / SR
    fade = np.clip((a.duration - t) / 4, 0, 1) * np.clip(t / 2, 0, 1)
    st = np.stack([L * fade, R * fade], 1)
    st = st / (np.abs(st).max() + 1e-9) * 0.8
    st = st[: int(a.duration * SR)]
    with wave.open(a.out, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32767).astype("<i2").tobytes())
    print("Musique :", a.out)


if __name__ == "__main__":
    main()
