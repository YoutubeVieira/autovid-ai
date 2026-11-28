"""Pack de bruitages libres de droits, SYNTHETISES par ce script (aucun echantillon tiers) -> CC0.
Usage: python3 make_sfx.py [dossier_sortie]   (bibliotheque standard uniquement)"""
import json
import math
import os
import random
import struct
import sys
import wave

SR = 44100
out = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
rnd = random.Random(7)


def env(t, dur, a=0.005, r=0.1):
    return min(1.0, t / a) * (1.0 if t < dur - r else max(0.0, (dur - t) / r))


def tone(freq, dur, vol=0.5, a=0.005, r=0.12, harm=(1.0,), decay=0.0, f_end=None):
    n = int(SR * dur)
    s, ph = [], 0.0
    for i in range(n):
        t = i / SR
        f = freq if f_end is None else freq + (f_end - freq) * (t / dur)
        ph += 2 * math.pi * f / SR
        v = sum(h * math.sin(ph * (k + 1)) for k, h in enumerate(harm)) / sum(harm)
        s.append(v * vol * env(t, dur, a, r) * (math.exp(-decay * t) if decay else 1.0))
    return s


def noise(dur, vol=0.4, a=0.005, r=0.1, lp=0.3, bp=None):
    n = int(SR * dur)
    s, y, y2 = [], 0.0, 0.0
    for i in range(n):
        t = i / SR
        x = rnd.uniform(-1, 1)
        y += lp * (x - y)
        v = y
        if bp:  # filtre passe-haut simple pour 'whoosh' clair
            y2 += bp * (v - y2)
            v = v - y2
        s.append(v * vol * env(t, dur, a, r))
    return s


def mix(*tracks, offsets=None):
    offsets = offsets or [0] * len(tracks)
    n = max(len(t) + int(o * SR) for t, o in zip(tracks, offsets))
    m = [0.0] * n
    for t, o in zip(tracks, offsets):
        o = int(o * SR)
        for i, v in enumerate(t):
            m[o + i] += v
    return m


def save(name, samples, desc, use):
    peak = max(abs(v) for v in samples) or 1.0
    g = 0.89 / peak if peak > 0.89 else 1.0
    path = os.path.join(out, name + ".wav")
    with wave.open(path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, v * g)) * 32767)) for v in samples))
    return {"file": name + ".wav", "duration_s": round(len(samples) / SR, 2), "description": desc, "use": use}


M = []
M.append(save("pop", tone(520, 0.09, 0.7, a=0.002, r=0.07, f_end=900, decay=18), "Bulle courte", "apparition d'un personnage, +1"))
M.append(save("ding", mix(tone(1319, 0.5, 0.5, r=0.4, decay=5, harm=(1, 0.3)), tone(1976, 0.5, 0.25, r=0.4, decay=6)), "Clochette claire", "badge +1 HABITANT"))
M.append(save("coin", mix(tone(988, 0.07, 0.5, r=0.02, harm=(1, 0.5)), tone(1319, 0.35, 0.5, r=0.3, decay=6, harm=(1, 0.5)), offsets=[0, 0.07]), "Piece de jeu", "gain, emploi, recompense"))
M.append(save("level_up", mix(*[tone(f, 0.16, 0.45, r=0.05, harm=(1, 0.4)) for f in (523, 659, 784, 1047)], tone(1047, 0.5, 0.4, r=0.4, decay=4), offsets=[0, 0.1, 0.2, 0.3, 0.42]), "Arpege montant", "palier atteint (100 habitants)"))
M.append(save("whoosh", noise(0.45, 0.8, a=0.12, r=0.3, lp=0.12, bp=0.02), "Souffle rapide", "changement de plan, zoom"))
M.append(save("swoosh_up", mix(noise(0.35, 0.6, a=0.2, r=0.12, lp=0.25, bp=0.03), tone(300, 0.35, 0.15, a=0.2, r=0.1, f_end=900)), "Souffle montant", "titre qui entre"))
M.append(save("click", mix(tone(2400, 0.015, 0.8, a=0.0005, r=0.01), noise(0.02, 0.4, a=0.0005, r=0.01, lp=0.9)), "Clic sec", "bouton, interface"))
M.append(save("tick", tone(1800, 0.03, 0.6, a=0.0005, r=0.025, decay=40), "Tic leger", "compteur qui monte"))
M.append(save("error_buzz", tone(110, 0.35, 0.6, a=0.01, r=0.1, harm=(1, 0.8, 0.6, 0.5)), "Buzzer grave", "porte fermee, TRANCADA / bloque"))
M.append(save("stamp", mix(tone(70, 0.25, 0.9, a=0.001, r=0.2, decay=14, f_end=40), noise(0.08, 0.5, a=0.001, r=0.07, lp=0.5)), "Tampon / impact sourd", "carton-titre, apparition d'un gros chiffre"))
M.append(save("sparkle", mix(*[tone(1500 + 380 * i, 0.12, 0.3, a=0.002, r=0.1, decay=12) for i in range(6)], offsets=[i * 0.05 for i in range(6)]), "Scintillement", "mot cle surligne"))
fan = [(523, 0.14), (523, 0.14), (523, 0.14), (659, 0.45), (587, 0.14), (659, 0.14), (784, 0.7)]
t0, tr, offs = 0.0, [], []
for f, d in fan:
    tr.append(tone(f, d + 0.05, 0.4, a=0.005, r=0.06, harm=(1, 0.6, 0.4, 0.2)))
    offs.append(t0)
    t0 += d
M.append(save("fanfare", mix(*tr, offsets=offs), "Petite fanfare", "election du maire, victoire"))
crowd = noise(2.0, 0.5, a=0.3, r=0.6, lp=0.15)
for i, v in enumerate(crowd):  # modulation lente = murmure de foule en liesse
    crowd[i] = v * (0.65 + 0.35 * math.sin(i / SR * 9.0) * math.sin(i / SR * 3.1))
M.append(save("crowd_cheer", crowd, "Foule en liesse (bruit module)", "la ville se remplit, fete"))
foot = []
for k in range(2):
    foot.append(mix(noise(0.07, 0.6, a=0.002, r=0.06, lp=0.2), tone(90, 0.07, 0.5, a=0.001, r=0.06, decay=30)))
M.append(save("footsteps", mix(*foot, offsets=[0, 0.28]), "Deux pas", "arrivee d'un habitant"))


# ---- effets "montage viral" : impacts graves, montees, glitchs, zooms
def square(freq, dur, vol=0.3, a=0.002, r=0.02):
    n = int(SR * dur)
    return [(1.0 if math.sin(2 * math.pi * freq * i / SR) > 0 else -1.0) * vol * env(i / SR, dur, a, r) for i in range(n)]


def riser(dur=1.2):
    n = int(SR * dur)
    s, y, ph = [], 0.0, 0.0
    for i in range(n):
        t = i / SR
        k = t / dur
        y += (0.04 + 0.5 * k * k) * (rnd.uniform(-1, 1) - y)
        ph += 2 * math.pi * (180 + 1900 * k * k) / SR
        s.append((y * 0.7 + math.sin(ph) * 0.25) * (0.15 + 0.85 * k) * min(1.0, (dur - t) / 0.03))
    return s


boom = mix(tone(62, 0.9, 0.95, a=0.001, r=0.5, decay=4.5, f_end=34), noise(0.12, 0.7, a=0.001, r=0.1, lp=0.35),
           tone(110, 0.25, 0.5, a=0.001, r=0.2, decay=14, f_end=50))
M.append(save("boom", [max(-0.95, min(0.95, v * 1.5)) for v in boom], "Impact grave (boom)", "coupe sur un gros plan, palier, mot choc"))
M.append(save("riser", riser(1.2), "Montee de tension", "avant une revelation, avant le palier"))
M.append(save("whoosh_fast", noise(0.22, 0.95, a=0.04, r=0.15, lp=0.2, bp=0.03), "Souffle tres court", "whip pan, coupe rapide"))
M.append(save("swipe", mix(noise(0.16, 0.8, a=0.03, r=0.1, lp=0.3, bp=0.05), tone(900, 0.16, 0.12, a=0.02, r=0.1, f_end=2400)), "Glissement", "transition laterale"))
gl = []
for k in range(7):
    gl.append(square(rnd.choice([220, 330, 440, 660, 990, 1500]), rnd.uniform(0.015, 0.045), 0.35))
M.append(save("glitch", mix(*gl, offsets=[k * 0.035 for k in range(7)]), "Glitch numerique", "apparition brusque, erreur, effet 'jeu'"))
M.append(save("shutter", mix(noise(0.03, 0.7, a=0.001, r=0.025, lp=0.7), noise(0.05, 0.6, a=0.001, r=0.04, lp=0.5), offsets=[0, 0.09]), "Obturateur photo", "arret sur image, gros plan fixe"))
M.append(save("zap", tone(2600, 0.2, 0.45, a=0.001, r=0.08, harm=(1, 0.7, 0.5), f_end=180), "Zap descendant", "apparition d'un personnage"))
M.append(save("bass_drop", mix(tone(120, 0.9, 0.9, a=0.002, r=0.5, decay=3.0, f_end=28), noise(0.05, 0.4, a=0.001, r=0.04, lp=0.3)), "Chute de basse", "debut d'un plan fort, titre"))
M.append(save("pop_double", mix(tone(520, 0.08, 0.7, a=0.002, r=0.06, f_end=880, decay=18), tone(700, 0.08, 0.7, a=0.002, r=0.06, f_end=1200, decay=18), offsets=[0, 0.09]), "Double bulle", "apparition de deux habitants"))

with open(os.path.join(out, "manifest.json"), "w", encoding="utf-8") as fh:
    json.dump({"license": "CC0 1.0 - sons synthetises par make_sfx.py, aucun echantillon tiers", "sample_rate": SR, "sounds": M}, fh, indent=2, ensure_ascii=False)
with open(os.path.join(out, "LICENSE.txt"), "w", encoding="utf-8") as fh:
    fh.write("Tous les sons de ce dossier sont generes par make_sfx.py (synthese pure).\nDedie au domaine public (CC0 1.0): usage commercial libre, aucune attribution requise.\n")
print(f"{len(M)} sons -> {out}")
