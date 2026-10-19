"""Boîte à effets façon CapCut, rendue par le code : courbes de vitesse, transitions, filtres couleur, synchro beat.

Courbes de vitesse (préréglages CapCut : Montage, Héros, Bullet, Flash in / Flash out) : vitesse en fonction de la
position dans la fenêtre analysée (u de 0 à 1, contact en `u_hit`). La vitesse change en douceur au lieu de passer
d'un coup de 100 % à 40 %.
"""
import cv2
import numpy as np

COURBES = {
    # nom : (vitesse au début, vitesse au contact, vitesse à la fin, largeur du creux autour du contact)
    "heros": (1.0, 0.25, 1.0, 0.30),       # Héros : ralenti marqué autour du coup, retour à la vitesse normale
    "bullet": (1.0, 0.12, 0.9, 0.45),      # Bullet time : très lent, longtemps
    "montage": (1.0, 0.35, 1.7, 0.25),     # Montage : ralenti puis accélération après le coup
    "flash_in": (2.6, 0.30, 0.6, 0.25),    # Flash in : arrive très vite, ralentit au contact
    "flash_out": (0.6, 0.30, 2.6, 0.25),   # Flash out : lent avant, part très vite après
}
TRANSITIONS = ("flash", "zoom", "whip", "glitch")
FILTRES = {                                 # filtres ffmpeg appliqués à l'export (après l'image, avant les sous-titres)
    "aucun": "",
    "cine": "colorbalance=rs=-0.06:gs=-0.02:bs=0.08:rh=0.08:gh=0.02:bh=-0.07,eq=contrast=1.07:saturation=1.05",
    "vif": "eq=saturation=1.35:contrast=1.06",
    "chaud": "colorbalance=rs=0.05:bs=-0.05:rm=0.06:bm=-0.05,eq=saturation=1.1",
    "froid": "colorbalance=rs=-0.05:bs=0.07:rm=-0.04:bm=0.06",
    "nb": "hue=s=0,eq=contrast=1.22:brightness=0.01",
}


def speed_at(curve, u, u_hit):
    """Vitesse (fraction de la vitesse réelle) à la position u de la fenêtre : creux lissé (cosinus) au contact."""
    v0, vh, v1, width = COURBES[curve]
    edge = v0 if u < u_hit else v1
    d = abs(u - u_hit) / max(width, 1e-3)
    if d >= 1:
        return edge
    w = 0.5 * (1 + np.cos(np.pi * d))          # 1 au contact, 0 au bord du creux
    return max(0.08, edge + (vh - edge) * w)


def ramp(src_a, src_hit, src_b, curve, fps=30):
    """Positions source (une par image de sortie) de src_a à src_b en suivant la courbe. Renvoie (avant, après)."""
    u_hit = (src_hit - src_a) / max(src_b - src_a, 1e-6)
    before, after, pos = [], [], float(src_a)
    while pos < src_b:
        (before if pos < src_hit else after).append(pos)
        u = (pos - src_a) / (src_b - src_a)
        pos += speed_at(curve, u, u_hit) * (fps / 30)
    return before, after


def transition(img, kind, lt, rng, dur=0.2):
    """Effet de transition sur l'image (float32, modifiée en place) pendant `dur` secondes après une coupe."""
    if lt >= dur:
        return
    k = 1 - lt / dur                            # force : 1 au début, 0 à la fin
    h, w = img.shape[:2]
    if kind == "flash":
        a = k * 0.6
        img[:] = img * (1 - a) + 255 * a
        img[:, 8:, 0] = img[:, :-8, 0].copy()
        img[:, :-8, 2] = img[:, 8:, 2].copy()
    elif kind == "zoom":                        # zoom blur radial (punch-in)
        acc, n = img.copy(), 1
        for s in (1.04, 1.08, 1.13):
            z = 1 + (s - 1) * k
            M = cv2.getRotationMatrix2D((w / 2, h / 2), 0, z)
            acc += cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REFLECT)
            n += 1
        img[:] = acc / n
    elif kind == "whip":                        # whip pan : flou de bougé horizontal + glissement
        size = max(int(140 * k), 1) | 1
        shift = int(w * 0.25 * k)
        img[:] = np.roll(cv2.blur(img, (size, 1)), shift, axis=1)
    elif kind == "glitch":                      # tranches décalées + séparation RVB
        out = img.copy()
        for _ in range(int(10 * k) + 2):
            y = int(rng.uniform(0, h - 40))
            hh = int(rng.uniform(10, 90))
            out[y:y + hh] = np.roll(img[y:y + hh], int(rng.uniform(-80, 80) * k), axis=1)
        d = int(18 * k) + 1
        out[:, d:, 0] = out[:, :-d, 0].copy()
        out[:, :-d, 2] = out[:, d:, 2].copy()
        img[:] = out


def beat_offset(t_hit, bpm=143):
    """Décalage à retirer au début de la musique générée pour qu'un temps fort tombe pile sur `t_hit`."""
    bar = 4 * 60 / bpm
    return (-t_hit) % bar
