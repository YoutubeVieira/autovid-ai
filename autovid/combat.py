"""Mode « combat éducatif » : une vidéo en entrée → un short viral analysé, sans intervention.

Pipeline :
  1. normalisation 1080x1920 30 i/s + étalonnage            (ffmpeg)
  2. squelette image par image, 2 personnes                 (MediaPipe)
  3. détection des coups (pic de vitesse poignet/cheville/genou) et nom de la technique
  4. timeline : accroche → [ralenti → flash → arrêt sur image expliqué → reprise] × N → appel à l'action
  5. rendu image par image : zoom, tremblement, silhouette en avant, chaîne cinétique colorée,
     cercles d'articulations, angle, traînée, étiquettes anatomie, titres, barre de progression
  6. son : musique (fournie ou synthétisée) + ducking + bruitages + son d'origine, −14 LUFS
  7. export 1080p / 4K / 8K
"""
import json
import shutil
import subprocess
from pathlib import Path

import cv2
import numpy as np

from . import gfx, sfx
from .analyze import scene_cuts
from .anatomy import classify
from .media import FPS, H, W, info, run
from .pose import BONES, L_ANK, L_HIP, L_KNEE, L_WR, R_ANK, R_HIP, R_KNEE, R_WR, iter_frames, segment, torso_len, track
from .render import match_loudness

EFFECTORS = (L_WR, R_WR, L_ANK, R_ANK, L_KNEE, R_KNEE)
SLOW = 0.35            # vitesse du ralenti avant l'impact
SLOW_SRC = 0.5         # durée (source) ralentie avant l'impact
HOOK_FREEZE = 0.9
TORSO = {11, 12, L_HIP, R_HIP}       # épaules + hanches : segments du tronc, coloriés plus fins
RESOLUTIONS = {"1080": (1080, 1920), "1440": (1440, 2560), "4k": (2160, 3840), "8k": (4320, 7680)}


# --------------------------------------------------------------------------- 1. normalisation

def normalize(src, out, framing="auto"):
    """framing : "blur" (vidéo paysage entière sur fond flouté), "cover" (recadrage plein écran au centre,
    sujets plus grands : mieux pour les plans larges, rodas filmées de haut), "auto" = blur."""
    i = info(src)
    grade = "eq=contrast=1.1:saturation=1.22:brightness=0.01,unsharp=5:5:0.8"
    if i["height"] < 900:                         # source basse définition : agrandissement soigné avant l'étalonnage
        grade = "hqdn3d=1.5:1.5:4:4," + grade
    if i["width"] >= i["height"] and framing != "cover":
        vf = (f"[0:v]fps={FPS},split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
              f"gblur=sigma=40,eq=brightness=-0.15[bg];[b]scale={W}:{H}:force_original_aspect_ratio=decrease[fg];"
              f"[bg][fg]overlay=(W-w)/2:(H-h)/2,{grade},setsar=1[v]")
    else:
        vf = (f"[0:v]fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},"
              f"{grade},setsar=1[v]")
    run(["ffmpeg", "-y", "-v", "error", "-i", src, "-filter_complex", vf, "-map", "[v]", "-an",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-g", "15", "-pix_fmt", "yuv420p", out])


# --------------------------------------------------------------------------- 3. détection des coups

def mover_mask(tr, center_zone=None, window=FPS, min_travel=0.08):
    """Images où la personne se DÉPLACE (joueurs) — le public assis autour reste sur place.
    center_zone : rayon max (en fraction du cadre) autour du centre, pour les rodas filmées de haut."""
    s = np.array([1.0, 16 / 9])
    hip = (tr[:, L_HIP, :2] + tr[:, R_HIP, :2]) / 2 * s
    n = len(hip)
    ok = np.zeros(n, bool)
    for i in range(n):
        a, b = max(i - window, 0), min(i + window, n - 1)
        seg = hip[a:b + 1]
        seg = seg[np.isfinite(seg).all(axis=1)]
        if len(seg) > 4 and np.linalg.norm(seg.max(axis=0) - seg.min(axis=0)) > min_travel:
            ok[i] = True
    if center_zone:
        c = np.array([0.5, 0.5]) * s
        ok &= np.nan_to_num(np.linalg.norm(hip - c, axis=1), nan=9) < center_zone * s[1]
    return ok


def detect_impacts(tracks, cuts_frames, max_n=6, min_gap=1.3, threshold=0.11, movers_only=False, center_zone=None):
    s = np.array([1.0, 16 / 9])
    found = []
    n = tracks.shape[1]
    near_cut = np.zeros(n, bool)
    for c in cuts_frames:
        near_cut[max(c - 3, 0): c + 4] = True
    for k in range(tracks.shape[0]):
        tr = tracks[k]
        if np.isfinite(tr[:, 0, 0]).sum() < 10:
            continue
        torso = np.array([torso_len(p) if np.isfinite(p[0, 0]) else np.nan for p in tr])
        torso = np.where(np.isfinite(torso), torso, np.nanmedian(torso))
        hipc = (tr[:, L_HIP, :2] + tr[:, R_HIP, :2]) / 2 * s
        jump = np.concatenate([[0], np.linalg.norm(np.diff(hipc, axis=0), axis=1)])
        bad = near_cut.copy()
        if movers_only:
            bad |= ~mover_mask(tr, center_zone)
        for j in np.where(~(jump < 0.06))[0]:          # saut d'identité / de plan : on ignore ±3 images
            bad[max(j - 3, 0): j + 4] = True
        for e in EFFECTORS:
            pos = tr[:, e, :2] * s
            vis = tr[:, e, 2]
            v = np.linalg.norm(np.diff(pos, axis=0), axis=1) / torso[1:]
            v = np.concatenate([[0], v])
            v[~np.isfinite(v) | bad | (vis < 0.45) | (v > 1.2)] = 0
            if e in (L_KNEE, R_KNEE):
                v *= 0.8                         # le genou bouge aussi pendant un coup de pied : on le pénalise
            for i in range(2, n - 2):
                sustained = max(v[i - 1], v[i + 1]) > 0.45 * threshold
                if v[i] > threshold and sustained and v[i] == v[i - 2: i + 3].max():
                    hip = (tr[:, L_HIP, :2] + tr[:, R_HIP, :2]) / 2 * s
                    win = range(i, min(i + 9, n))
                    dist = [np.linalg.norm(pos[j] - hip[j]) if np.isfinite(pos[j]).all() else -1 for j in win]
                    apex = i + int(np.argmax(dist))
                    if e in (L_ANK, R_ANK, L_KNEE, R_KNEE):  # pied/genou : il faut monter, sinon c'est un déplacement
                        o_knee = R_KNEE if e in (L_ANK, L_KNEE) else L_KNEE
                        if not tr[apex, e, 1] < tr[apex, o_knee, 1] - 0.01:
                            continue
                    found.append({"frame": apex, "track": k, "eff": e, "score": float(v[i])})
    found.sort(key=lambda m: -m["score"])
    chosen = []
    for m in found:
        if all(abs(m["frame"] - c["frame"]) > min_gap * FPS for c in chosen):
            chosen.append(m)
        if len(chosen) >= max_n:
            break
    return sorted(chosen, key=lambda m: m["frame"])


# --------------------------------------------------------------------------- 4. timeline

def freeze_len(m):
    """Durée de l'arrêt sur image : le temps de lire les étiquettes, ou d'écouter la voix off."""
    base = 1.75 + 0.38 * len(m["info"]["muscles"])
    return max(base, m.get("voice_dur", 0) + 0.45)


def build_timeline(n_frames, impacts, hook=True, max_dead=3.0, hook_freeze=HOOK_FREEZE, outro_len=1.8):
    """Liste d'images de sortie : dict(src, phase, imp, lt)."""
    out = []

    def add(src, phase, imp=-1, lt=0.0):
        out.append({"src": float(min(src, n_frames - 1)), "phase": phase, "imp": imp, "lt": lt})

    def normal(a, b, first=False):
        a, b = int(a), int(b)
        if b <= a:
            return
        dead = max_dead * FPS
        if first and b - a > 1.6 * FPS:          # avant le premier coup : 1,6 s de contexte suffisent
            a = b - int(1.6 * FPS)
        if b - a > dead:                         # temps mort : on garde le début et la fin, coupe franche
            keep_a, keep_b = int(1.0 * FPS), int(1.3 * FPS)
            for s in range(a, a + keep_a):
                add(s, "normal")
            for j, s in enumerate(range(b - keep_b, b)):
                add(s, "jump" if j < 6 else "normal", lt=j / FPS)
        else:
            for s in range(a, b):
                add(s, "normal")

    if hook and impacts:
        h = max(range(len(impacts)), key=lambda j: impacts[j]["score"])
        m = impacts[h]
        s0 = max(m["frame"] - 18, 0)
        nslow = int((m["frame"] - s0) / 0.5)
        for j in range(nslow):
            add(s0 + j * 0.5, "hook_slow", h, j / FPS)
        for j in range(int(hook_freeze * FPS)):
            add(m["frame"], "hook_freeze", h, j / FPS)

    cursor = 0
    for k, m in enumerate(impacts):
        s0 = max(cursor, m["frame"] - int(SLOW_SRC * FPS))
        normal(cursor, s0, first=(k == 0))
        nslow = int((m["frame"] - s0) / SLOW)
        for j in range(nslow):
            add(s0 + j * SLOW, "slow", k, j / FPS)
        for j in range(int(freeze_len(m) * FPS)):
            add(m["frame"], "freeze", k, j / FPS)
        for j in range(8):
            add(m["frame"] + j, "post", k, j / FPS)
        cursor = m["frame"] + 8
    tail = min(n_frames, cursor + int(1.2 * FPS)) if impacts else n_frames
    normal(cursor, tail)
    last = out[-1]["src"] if out else 0
    for j in range(int(outro_len * FPS)):
        add(last, "outro", -1, j / FPS)
    if hook and impacts:                         # la coupe accroche → contenu se fait sur un flash
        first_main = next(i for i, f in enumerate(out) if not f["phase"].startswith("hook"))
        for j in range(first_main, min(first_main + 6, len(out))):
            if out[j]["phase"] == "normal":
                out[j]["phase"] = "jump"
                out[j]["lt"] = (j - first_main) / FPS
    return out


# --------------------------------------------------------------------------- 5. rendu image

class Renderer:
    def __init__(self, tracks, impacts, timeline, handle=None, accent=gfx.GREEN):
        self.tracks, self.impacts, self.tl = tracks, impacts, timeline
        self.handle, self.accent = handle, accent
        self.freeze_cache = {}
        self.total = len(timeline)
        self.rng = np.random.default_rng(1)

    def pts(self, k, frame_idx):
        p = self.tracks[k, int(round(frame_idx))]
        return p[:, :2] * np.array([W, H]), p[:, 2]

    # ---- géométrie du zoom
    def zoom_for(self, f):
        ph, lt = f["phase"], f["lt"]
        if f["imp"] < 0:
            if ph == "jump":
                return 1 + 0.14 * (1 - gfx.ease(lt / 0.2)), None
            return 1.0, None
        m = self.impacts[f["imp"]]
        xy, _ = self.pts(m["track"], m["frame"])
        eff, hip = xy[m["eff"]], (xy[L_HIP] + xy[R_HIP]) / 2
        c = (eff + hip) / 2 if np.isfinite(eff).all() and np.isfinite(hip).all() else np.array([W / 2, H / 2])
        if ph in ("slow", "hook_slow"):
            z = 1 + 0.22 * gfx.ease(lt / (SLOW_SRC / SLOW))
        elif ph in ("freeze", "hook_freeze"):
            z = 1.22 + 0.2 * gfx.ease(lt / 1.6)
        elif ph == "post":
            z = 1.42 - 0.42 * gfx.ease(lt / 0.25)
        else:
            z = 1.0
        return z, c

    def shake_for(self, f):
        if f["phase"] in ("freeze", "hook_freeze") and f["lt"] < 0.2:
            amp = 16 * (1 - f["lt"] / 0.2)
            return tuple(self.rng.uniform(-amp, amp, 2))
        return (0, 0)

    @staticmethod
    def matrix(z, c, shake=(0, 0)):
        if c is None:
            c = np.array([W / 2, H / 2])
        half_w, half_h = W / (2 * z), H / (2 * z)
        cx = float(np.clip(c[0], half_w, W - half_w))
        cy = float(np.clip(c[1], half_h, H - half_h))
        return np.array([[z, 0, W / 2 - z * cx + shake[0]], [0, z, H / 2 - z * cy + shake[1]]], np.float32)

    # ---- arrêt sur image : masque de silhouette (calculé une seule fois)
    def freeze_data(self, imp, frame_rgb):
        if imp in self.freeze_cache:
            st = self.freeze_cache[imp]
            return st["xy"], st["vis"], st["person"]
        m = self.impacts[imp]
        small = cv2.resize(frame_rgb, (540, 960))
        poses, masks = segment(small)
        ref, _ = self.pts(m["track"], m["frame"])
        best, mask = None, None
        for p, mk in zip(poses, masks or [None] * len(poses)):
            xy = p[:, :2] * np.array([W, H])
            d = np.nanmean(np.linalg.norm(xy - ref, axis=1))
            if best is None or d < best[0]:
                best, mask = (d, xy, p[:, 2]), mk
        xy, vis = (best[1], best[2]) if best is not None and best[0] < 120 else (ref, self.pts(m["track"], m["frame"])[1])
        person = cv2.resize(mask, (W, H)) if mask is not None else None
        self.freeze_cache[imp] = {"xy": xy, "vis": vis, "person": person}
        return xy, vis, person

    def freeze_scene(self, img, imp, lt, xy, person, torso):
        """Silhouette mise en avant + chaîne cinétique révélée segment par segment (image fixe → mise en cache)."""
        st = self.freeze_cache[imp]
        info_ = self.impacts[imp]["info"]
        bones = [(b, gfx.ORANGE) for b in info_["support"]] + [(b, self.accent) for b in info_["chain"]]
        done_t = max(0.2, 0.12 + (len(bones) - 1) * 0.09 + 0.16)
        if lt >= done_t and "done" in st:
            img[:] = st["done"]
            return
        if "dark" not in st:                      # fond assombri + désaturé, silhouette intacte (image fixe)
            pm = cv2.GaussianBlur(person, (0, 0), 3)[..., None]
            gray = img.mean(axis=2, keepdims=True)
            st["dark"] = img * pm + (img * 0.35 + gray * 0.65) * 0.45 * (1 - pm)
            st["solid"] = np.clip(person * 1.4, 0, 1)
        k = gfx.ease(lt / 0.2)
        if k < 1:
            img += (st["dark"] - img) * k
        else:
            img[:] = st["dark"]
        # appui en orange, chaîne motrice dans la couleur d'accent
        for n, ((a, b), col) in enumerate(bones):
            prog = gfx.ease((lt - 0.12 - n * 0.09) / 0.16)
            if prog <= 0:
                continue
            pa, pb = xy[a], xy[a] + (xy[b] - xy[a]) * prog
            th = max(int(torso * (0.22 if {a, b} <= TORSO else 0.34)), 14)
            pad = th + 60
            x0, y0 = int(max(min(pa[0], pb[0]) - pad, 0)), int(max(min(pa[1], pb[1]) - pad, 0))
            x1, y1 = int(min(max(pa[0], pb[0]) + pad, W)), int(min(max(pa[1], pb[1]) + pad, H))
            if x1 - x0 < 8 or y1 - y0 < 8:
                continue
            lm = np.zeros((y1 - y0, x1 - x0), np.uint8)   # masque calculé seulement autour du segment
            off = np.array([x0, y0])
            cv2.line(lm, tuple(map(int, pa - off)), tuple(map(int, pb - off)), 255, th, cv2.LINE_AA)
            region = lm.astype(np.float32) / 255 * st["solid"][y0:y1, x0:x1]
            gfx.glow_fill(img[y0:y1, x0:x1], region, col, alpha=0.55, glow=0.45)
        if lt >= done_t:
            st["done"] = img.copy()

    # ---- éléments dessinés dans l'espace de la scène (zoomés avec l'image)
    def scene_overlays(self, img, f, frame_rgb):
        ph, lt, imp = f["phase"], f["lt"], f["imp"]
        if imp < 0 or ph in ("post",):
            return
        m = self.impacts[imp]
        info_ = m["info"]
        if ph in ("freeze", "hook_freeze"):
            xy, vis, person = self.freeze_data(imp, frame_rgb)
        else:
            xy, vis = self.pts(m["track"], f["src"])
            person = None
        if not np.isfinite(xy).all():
            xy = np.nan_to_num(xy, nan=-1000)
        torso = torso_len(np.concatenate([xy / np.array([W, H]), vis[:, None]], axis=1)) * W

        if ph in ("freeze", "hook_freeze") and person is not None:
            self.freeze_scene(img, imp, lt, xy, person, torso)

        # squelette fin + traînée, dessinés sur un seul calque puis fondus en une fois
        over = img.copy()
        chain = {frozenset(b) for b in info_["chain"]}
        for a, b in BONES:
            if vis[a] < 0.3 or vis[b] < 0.3:
                continue
            hot = frozenset((a, b)) in chain
            gfx.line(over, xy[a], xy[b], self.accent if hot else (255, 255, 255), 4 if hot else 3)
        if ph in ("slow", "hook_slow"):          # traînée de l'extrémité qui frappe
            e = info_["effector"]
            hist = [self.pts(m["track"], max(f["src"] - d, 0))[0][e] for d in range(7)]
            for d in range(len(hist) - 1):
                if np.isfinite(hist[d]).all() and np.isfinite(hist[d + 1]).all():
                    gfx.line(over, hist[d], hist[d + 1], self.accent, max(20 - d * 3, 3))
        a_skel = 0.55 if ph in ("slow", "hook_slow") else 0.85
        cv2.addWeighted(over, a_skel, img, 1 - a_skel, 0, dst=img)
        for j in info_["joints"]:
            r = 20 + (6 * np.sin(lt * 9) if ph.endswith("freeze") else 0)
            gfx.ring(img, xy[j], r, (255, 255, 255), 4)
            gfx.dot(img, xy[j], 7, self.accent)

        # angle de l'articulation clé
        if ph == "freeze" and lt > 0.5:
            _, (a, b, c), _ = info_["angle"]
            v1, v2 = xy[a] - xy[b], xy[c] - xy[b]
            a1, a2 = np.degrees(np.arctan2(v1[1], v1[0])), np.degrees(np.arctan2(v2[1], v2[0]))
            if abs(a2 - a1) > 180:
                a2 += 360 if a2 < a1 else -360
            sweep = a1 + (a2 - a1) * gfx.ease((lt - 0.5) / 0.3)
            cv2.ellipse(img, tuple(map(int, xy[b])), (62, 62), 0, a1, sweep, gfx.YELLOW, 6, cv2.LINE_AA)

    # ---- éléments en espace écran (non zoomés)
    def screen_overlays(self, img, f, k, M):
        ph, lt, imp = f["phase"], f["lt"], f["imp"]
        acc = self.accent
        if ph in ("freeze", "hook_freeze", "post", "jump") and lt < 0.14:
            a = (1 - lt / 0.14) * (0.85 if ph != "post" else 0)
            img[:] = img * (1 - a) + 255 * a                       # flash blanc
        if ph in ("freeze", "hook_freeze") and lt < 0.1:
            img[:, 10:, 0] = img[:, :-10, 0].copy()                # décalage RVB (aberration)
            img[:, :-10, 2] = img[:, 10:, 2].copy()

        if imp >= 0:
            m = self.impacts[imp]
            info_ = m["info"]
            if ph.startswith("hook"):
                line1, line2 = info_["hook"]
                gfx.paste(img, gfx.text_sprite(line1, 92, gfx.WHITE), W / 2, 300,
                          gfx.pop(lt) if ph == "hook_slow" else 1)
                if ph == "hook_freeze":
                    gfx.paste(img, gfx.text_sprite(line2, 74, gfx.YELLOW), W / 2, 410, gfx.pop(lt))
            if ph == "freeze":
                gfx.paste(img, gfx.text_sprite(f"ANALYSE #{imp + 1}", 48, gfx.YELLOW, stroke=4, shadow=6), W / 2, 150,
                          gfx.pop(lt))
                gfx.paste(img, gfx.text_sprite(info_["nom"], 104, gfx.WHITE), W / 2, 250, gfx.pop(lt - 0.05))
                gfx.paste(img, gfx.text_sprite(info_["membre"], 44, acc, stroke=4, shadow=6), W / 2, 345,
                          gfx.pop(lt - 0.12))
                xy = self.freeze_cache.get(imp, {}).get("xy")
                if xy is not None:
                    self.anatomy_labels(img, info_, xy, lt, M)
                    name, (_, b, _), deg = info_["angle"]
                    if lt > 0.75:
                        pb = M @ np.array([xy[b][0], xy[b][1], 1.0])
                        gfx.paste(img, gfx.text_sprite(f"{name} {deg:.0f}°", 40, gfx.YELLOW, stroke=4, shadow=6),
                                  float(np.clip(pb[0], 160, W - 160)), float(np.clip(pb[1] - 95, 420, H - 300)),
                                  gfx.pop(lt - 0.75))
                risk_t = 0.55 + 0.32 * len(info_["muscles"]) + 0.2
                if info_.get("risque") and risk_t < lt <= freeze_len(m) - 0.75:
                    zone, conseil = info_["risque"]
                    gfx.paste(img, gfx.text_sprite(f"RISQUE : {zone}", 50, gfx.RED, stroke=5, shadow=8, max_w=980),
                              W / 2, 1490, gfx.pop(lt - risk_t))
                if lt > freeze_len(m) - 0.75:
                    gfx.paste(img, gfx.text_sprite("ASTUCE : " + info_["tip"], 50, gfx.WHITE, stroke=5, shadow=8, max_w=980),
                              W / 2, 1500, gfx.pop(lt - (freeze_len(m) - 0.75)))
            if ph == "slow":
                gfx.paste(img, gfx.text_sprite("RALENTI", 40, gfx.WHITE, stroke=4, shadow=6), W / 2, 150, 1, 0.8)

        if ph == "outro":
            img *= 1 - 0.55 * gfx.ease(lt / 0.3)
            gfx.paste(img, gfx.text_sprite("ABONNE-TOI", 130, gfx.WHITE), W / 2, 760, gfx.pop(lt - 0.1))
            gfx.paste(img, gfx.text_sprite("POUR LA PARTIE 2", 70, gfx.YELLOW), W / 2, 900, gfx.pop(lt - 0.3))
            gfx.paste(img, gfx.text_sprite("ENREGISTRE ET ESSAIE", 56, acc, stroke=5, shadow=8), W / 2, 1010,
                      gfx.pop(lt - 0.5))

        if self.handle:
            gfx.paste(img, gfx.text_sprite(self.handle, 40, gfx.WHITE, stroke=3, shadow=4), W / 2, 1745, 1, 0.55)
        prog = int(W * (k + 1) / self.total)                      # barre de progression (rétention)
        img[0:12, :prog] = img[0:12, :prog] * 0.1 + np.array(acc, np.float32) * 0.9

    def anatomy_labels(self, img, info_, xy, lt, M):
        anchors = []
        for title, role, anchor in info_["muscles"]:
            ap = np.mean([xy[a] for a in anchor], axis=0)
            anchors.append((M @ np.array([ap[0], ap[1], 1.0]))[:2])
        # chaque côté a ses créneaux verticaux : jamais de chevauchement
        slots = {True: [], False: []}
        order = sorted(range(len(anchors)), key=lambda n: anchors[n][1])
        for n in order:
            left = anchors[n][0] > W / 2                          # étiquette du côté opposé à l'ancre
            want = float(np.clip(anchors[n][1], 500, 1380))
            for y in slots[left]:
                want = max(want, y + 140)
            slots[left].append(want)
            title, role, _ = info_["muscles"][n]
            t = lt - 0.55 - n * 0.32
            if t <= 0:
                continue
            spr = gfx.label_sprite(title, role, self.accent)
            w = spr.shape[1]
            lx = 40 + w / 2 if left else W - 40 - w / 2
            ly = min(want, 1420)
            edge = np.array([lx + (w / 2 if left else -w / 2), ly])
            ap = anchors[n]
            tip = ap + (edge - ap) * gfx.ease(t / 0.18)
            gfx.line(img, ap, tip, (255, 255, 255), 4)
            gfx.dot(img, ap, 10, self.accent)
            gfx.paste(img, spr, lx, ly, gfx.pop(t - 0.1, over=1.15))

    def render(self, base, out_path):
        """Décode base.mp4 par tronçons monotones, compose, et envoie les images à ffmpeg."""
        enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                                "-r", str(FPS), "-i", "-", "-vf", "noise=alls=5:allf=t,vignette=angle=PI/5",
                                "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-maxrate", "20M", "-bufsize", "40M",
                                "-pix_fmt", "yuv420p", str(out_path)], stdin=subprocess.PIPE)
        runs, cur = [], [0]
        for i in range(1, len(self.tl)):
            if self.tl[i]["src"] < self.tl[i - 1]["src"]:
                runs.append(cur)
                cur = []
            cur.append(i)
        runs.append(cur)
        k = 0
        for r in runs:
            start = int(self.tl[r[0]]["src"])
            frames = iter_frames(base, W, H, start=start / FPS if start else None)
            buf = {}
            idx = start - 1
            for i in r:
                f = self.tl[i]
                need = int(np.floor(f["src"])) + (1 if f["src"] % 1 > 1e-3 else 0)
                while idx < need:
                    nxt = next(frames, None)
                    if nxt is None:
                        break
                    idx += 1
                    buf[idx] = nxt
                    buf.pop(idx - 3, None)
                lo = min(int(np.floor(f["src"])), idx)
                a = buf.get(lo, buf[max(buf)])
                frac = f["src"] - lo
                if frac > 1e-3 and lo + 1 in buf:
                    rgb = cv2.addWeighted(a, 1 - frac, buf[lo + 1], frac, 0)
                else:
                    rgb = a
                img = rgb.astype(np.float32)
                self.scene_overlays(img, f, rgb)
                z, c = self.zoom_for(f)
                shake = self.shake_for(f)
                M = self.matrix(z, c, shake)
                if abs(z - 1) > 1e-3 or shake != (0, 0):
                    img = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
                self.screen_overlays(img, f, k, M)
                enc.stdin.write(np.clip(img, 0, 255).astype(np.uint8).tobytes())
                k += 1
                if k % 60 == 0:
                    print(f"\r  rendu {k}/{self.total} images", end="", flush=True)
        enc.stdin.close()
        enc.wait()
        print()


# --------------------------------------------------------------------------- 6. son

def build_audio(timeline, impacts, src_audio, music_path, out_wav, orig_gain=0.7, voice=(), insert=(0.0, 0.0),
                post=0.0, extra_fx=(), kit="reaction"):
    """Bande-son complète. `insert` = (instant, durée) d'un carton (intro) inséré dans le montage, `post` = durée
    de la carte de fin ajoutée à la fin ; les temps de `voice` et `extra_fx` sont ceux de la vidéo finale."""
    sr = sfx.SR
    spf = sr // FPS
    ins_at, ins_len = insert
    tmap = lambda t: t + ins_len if t >= ins_at - 1e-6 else t  # noqa: E731
    n = len(timeline) * spf + int(round((ins_len + post) * sr))
    dur = n / sr
    if music_path:
        mus = sfx.read_wav(music_path)
        reps = int(np.ceil(n / max(len(mus), 1)))
        mus = np.tile(mus, (reps, 1))[:n] if len(mus) else np.zeros((n, 2))
    elif kit == "reaction":
        mus = sfx.music_phonk(dur + 0.1)[:n]
    else:
        mus = sfx.music(dur + 0.1)[:n]
    duck = np.ones(n)
    orig = np.zeros((n, 2))
    fx = np.zeros((n, 2))

    def put(name, t, gain=1.0, **kw):
        s = sfx.LIB[name](**kw) * gain
        i = int(t * sr)
        if 0 <= i < n:
            seg = s[: n - i]
            fx[i: i + len(seg)] += seg

    for t, name, gain, kw in extra_fx:
        put(name, t, gain, **kw)
    prev = None
    for k, f in enumerate(timeline):
        t = tmap(k / FPS)
        i0 = int(round(t * sr))
        ph = f["phase"]
        if ph in ("freeze", "hook_freeze", "outro", "hit", "hook_hit"):
            duck[i0:i0 + spf] = 0.35
        if ph in ("normal", "jump", "post") and len(src_audio):
            a = int(f["src"] * spf)
            chunk = src_audio[a: a + spf]
            orig[i0: i0 + len(chunk)] = chunk
        if ph != (prev or {}).get("phase"):
            if ph in ("slow", "hook_slow"):
                put("low_whoosh" if kit == "reaction" else "whoosh", t, 0.8, d=0.5)
                if kit != "reaction":
                    put("riser", t, 0.5, d=max(SLOW_SRC / SLOW - 0.05, 0.3))
            if ph in ("freeze", "hook_freeze"):
                put("impact", t, 1.0)
                put("shutter", t, 0.6)
                if ph == "freeze":
                    m = impacts[f["imp"]]
                    for j in range(len(m["info"]["muscles"])):
                        put("tick", t + 0.55 + j * 0.32 + 0.1, 0.8)
                    put("tick", t + 0.85, 0.6, f=1400)
                    put("whoosh", t + freeze_len(m) - 0.3, 0.6, d=0.35)
            if ph in ("slow", "hook_slow") and kit == "reaction":   # mode fluide : montée inversée vers le contact
                from .fluide import PRE_SRC, SLOW_IN
                put("reverse_hit", t + PRE_SRC / SLOW_IN - 0.45, 0.7)
            if ph in ("hit", "hook_hit"):
                put("sub_boom" if kit == "reaction" else "impact", t, 1.0)
                put("shutter", t, 0.35)
            if ph == "jump":
                put("low_whoosh" if kit == "reaction" else "whoosh", max(t - 0.15, 0), 0.8, d=0.35)
            if ph == "outro":
                put("impact", t, 0.8)
                put("riser", max(t - 0.6, 0), 0.4, d=0.6)
        prev = f
    vox = np.zeros((n, 2))
    for t, a in voice:                           # voix off : la musique et le son d'origine passent dessous
        i = int(t * sr)
        if a is None or i >= n:
            continue
        seg = a[: n - i]
        vox[i: i + len(seg)] += seg
        duck[i: i + len(seg)] = np.minimum(duck[i: i + len(seg)], 0.22)
    duck = np.convolve(duck, np.ones(2400) / 2400, mode="same")
    if np.abs(vox).max() > 0:
        vox *= 0.8 / np.abs(vox).max()
        orig *= np.where(duck < 0.5, 0.3, 1.0)[:, None]
    mix = mus * 0.5 * duck[:, None] + orig * orig_gain + fx * 0.8 + vox * 1.6
    peak = np.abs(mix).max() or 1
    sfx.write_wav(out_wav, mix / peak * 0.9)


# --------------------------------------------------------------------------- 7. orchestration

def phase_starts(timeline):
    """Instant (s) du début de chaque phase : {('freeze', k): t, ('outro', -1): t, …}."""
    out = {}
    for i, f in enumerate(timeline):
        out.setdefault((f["phase"], f["imp"]), i / FPS)
    return out


def subtitles(segs, starts, impacts, out_base, work, burn, langs, windows=None, anchor="freeze"):
    """SRT par langue + fichier ASS pour l'incrustation. Renvoie (chemin ASS ou None, {langue: srt})."""
    from . import narration as nar
    from .talk import captions_ass
    t_of = {"hook": 0.0, "outro": starts.get(("outro", -1), 0.0)}
    for k in range(len(impacts)):
        t_of[k] = starts.get((anchor, k), 0.0) + 0.15
    fr_words, cues = [], {"fr": []}
    windows = windows or {}
    for sg in segs:
        t0 = t_of[sg["id"]]
        if sg["id"] in windows:                 # chaque réplique reste dans la fenêtre de son analyse
            sg["words"] = nar.fit_words(sg["words"], windows[sg["id"]])
            sg["dur"] = min(sg["dur"], windows[sg["id"]])
        ws = [{**w, "start": w["start"] + t0, "end": w["end"] + t0} for w in sg["words"]]
        fr_words += ws
        cues["fr"] += nar.cues_from_words(ws)
    other = [x for x in langs if x != "fr"]
    if other:
        from .ai import translate
        tr = translate([nar.plain(sg["fr"]) for sg in segs])
        if tr is None:
            print("   (pas d'identifiants Anthropic : sous-titres pt/en non traduits)")
        else:
            for lang in other:
                cues[lang] = []
                for sg, txt in zip(segs, tr[lang]):
                    t0 = t_of[sg["id"]]
                    cues[lang] += nar.cues_from_text(txt, t0, t0 + sg["dur"])
    srts = {}
    for lang, c in cues.items():
        if c:
            srts[lang] = f"{out_base}.{lang}.srt"
            nar.write_srt(c, srts[lang])
    ass = None
    if burn == "fr" and fr_words:
        ass = work / "sous_titres.ass"
        captions_ass(fr_words, ass, y=1640, max_words=3)
    elif burn in cues and cues[burn]:
        ass = work / "sous_titres.ass"
        captions_ass([{"text": txt, "start": a, "end": b} for a, b, txt in cues[burn]], ass, y=1640, max_words=1,
                     highlight=False)
    return ass, srts


def combat(src, out, workdir, music=None, handle=None, max_impacts=6, resolution="1080", ai=None, hook=True,
           orig_gain=0.7, accent=None, discipline="combat", voice_id=None, langs=("fr", "pt", "en"), burn="fr",
           extras=True, motion_design=True, framing="auto", tts="auto", style="fluide", kit="reaction",
           music_from=None):
    """style : "fluide" (analyse sur la vidéo en mouvement, sans pause) ou "analyse" (arrêts sur image commentés).
    kit : "reaction" (phonk 808, impacts sub) ou "classique". music_from : vidéo dont on reprend la bande-son
    comme musique (uniquement si tu en as les droits)."""
    from . import narration as nar
    from .anatomy import add_safety, capoeira_variant
    work = Path(workdir)
    work.mkdir(parents=True, exist_ok=True)
    base = work / "base.mp4"
    out_abs = Path(out).resolve()
    out_abs.parent.mkdir(parents=True, exist_ok=True)
    out_base = str(out_abs.with_suffix(""))
    # cache : relancer un montage sur la même vidéo (même cadrage) ne refait ni la normalisation ni le squelette
    people = 4 if discipline == "capoeira" else 2   # roda : on suit plusieurs personnes puis on garde les joueurs
    key = f"{Path(src).resolve()}|{Path(src).stat().st_size}|{Path(src).stat().st_mtime_ns}|{framing}|{people}"
    cache_ok = (work / "cache.key").exists() and (work / "cache.key").read_text() == key \
        and base.exists() and (work / "squelette.npy").exists()
    if cache_ok:
        print("1/6 normalisation + 2/6 squelette : repris du cache")
        tracks = np.load(work / "squelette.npy")
    else:
        print("1/6 normalisation 9:16 + étalonnage")
        normalize(str(src), base, framing)
        print("2/6 squelette (MediaPipe)")
        tracks = track(base, people=people)
        np.save(work / "squelette.npy", tracks)
        (work / "cache.key").write_text(key)
    n = tracks.shape[1]
    cuts = [int(round(c * FPS)) for c in scene_cuts(str(base))]
    print("3/6 détection des coups")
    impacts = detect_impacts(tracks, cuts, max_impacts, movers_only=discipline == "capoeira",
                             center_zone=0.42 if discipline == "capoeira" and framing == "cover" else None)
    for m in impacts:
        m["info"] = classify(tracks[m["track"]], m["frame"], m["eff"])
        if discipline == "capoeira":
            capoeira_variant(tracks[m["track"]], m["frame"], m["info"])
        add_safety(m["info"])
    if discipline == "capoeira":                 # variété : pas plus de 2 fois le même mouvement
        seen = {}
        for m in sorted(impacts, key=lambda m: -m["score"]):
            seen[m["info"]["nom"]] = seen.get(m["info"]["nom"], 0) + 1
            m["keep"] = seen[m["info"]["nom"]] <= 2
        impacts = [m for m in impacts if m.pop("keep")]
    if ai:
        from .ai import enrich
        enrich(impacts, base, provider=ai, discipline=discipline)
    for m in impacts:
        print(f"   t={m['frame'] / FPS:5.2f}s  {m['info']['nom']:<22} {m['info']['membre']:<14} vitesse {m['score']:.2f}")
    if not impacts:
        print("   aucun coup net détecté : montage dynamique sans analyse")

    # voix off : script, synthèse (ta voix clonée) et durées → l'arrêt sur image s'adapte à la voix
    fluid = style == "fluide"
    anchor = "slow" if fluid else "freeze"
    segs = nar.build_script(impacts, discipline, short=fluid)
    voice_id = voice_id or nar.default_voice()
    engine = nar.voice_segments(segs, voice_id, tts)
    has_voice = engine is not None
    print("   voix off : " + {"elevenlabs": f"ElevenLabs, voix {voice_id}", "kokoro": "voix test locale Kokoro (ff_siwis)",
                               None: "script seul (pas de clé ElevenLabs ni Kokoro)"}[engine])
    Path(f"{out_base}.voix.txt").write_text("\n\n".join(f"[{sg['id']}] {sg['fr']}" for sg in segs), encoding="utf-8")
    by_id = {sg["id"]: sg for sg in segs}
    for k, m in enumerate(impacts):
        if has_voice:
            m["voice_dur"] = by_id[k]["dur"]
    hook_freeze = max(HOOK_FREEZE, by_id["hook"]["dur"] - 1.1) if has_voice and "hook" in by_id else HOOK_FREEZE
    outro_len = max(1.8, by_id["outro"]["dur"] + 0.4) if has_voice else 1.8
    from . import motion
    use_motion = motion_design and motion.available() and bool(impacts)
    if motion_design and not use_motion:
        print("   motion design HyperFrames / Remotion indisponible (cd motion && npm install) : version sans")
    if use_motion:
        outro_len = 0.0                          # la carte de fin Remotion remplace l'outro intégré

    (work / "analyse.json").write_text(json.dumps(
        [{"t": m["frame"] / FPS, "score": m["score"], **{k: v for k, v in m["info"].items() if k in
          ("nom", "membre", "hook", "tip", "kind", "placement", "risque")},
          "muscles": [x[:2] for x in m["info"]["muscles"]]} for m in impacts], ensure_ascii=False, indent=1),
        encoding="utf-8")
    if fluid:
        from . import fluide
        timeline = fluide.build_timeline(n, impacts, hook=hook, outro_len=outro_len)
    else:
        timeline = build_timeline(n, impacts, hook=hook, hook_freeze=hook_freeze, outro_len=outro_len)
    starts = phase_starts(timeline)
    print(f"4/6 timeline : {len(timeline) / FPS:.1f} s ({len(impacts)} analyses)")
    print("5/6 rendu image par image")
    if fluid:
        renderer = type("FluidRenderer", (fluide.FluidMixin, Renderer), {})(tracks, impacts, timeline, handle,
                                                                              accent or gfx.GREEN)
    else:
        renderer = Renderer(tracks, impacts, timeline, handle, accent or gfx.GREEN)
    renderer.render(base, work / "video.mp4")
    print("6/6 motion design, son, sous-titres + export")
    first_main = next((i for i, f in enumerate(timeline) if not f["phase"].startswith("hook")), 0) / FPS
    ins_at, ins_len, post = first_main, 0.0, 0.0
    accent_hex = "#%02x%02x%02x" % tuple(accent or gfx.GREEN)
    if use_motion:
        top = max(range(len(impacts)), key=lambda j: impacts[j]["score"])
        tag = "CAPOEIRA • ANATOMIE • PLACEMENT" if discipline == "capoeira" else "COMBAT • ANATOMIE • PLACEMENT"
        try:
            motion.render_intro(work / "intro.mp4", impacts[top]["info"]["nom"], tag=tag, handle=handle or "",
                                accent=accent_hex)
            teaser = "PRÓXIMO : A ESQUIVA" if discipline == "capoeira" else "PARTIE 2 : LA DÉFENSE"
            motion.render_outro(work / "outro.mp4", handle=handle or "", teaser=teaser, accent=accent_hex)
            ins_len, post = motion.INTRO_DUR, motion.OUTRO_DUR
            print(f"   intro HyperFrames {ins_len} s après l'accroche, carte de fin Remotion {post} s")
        except (RuntimeError, OSError) as e:
            print(f"   motion design ignoré : {e}")
            use_motion = False
    tmap = lambda t: t + ins_len if t >= ins_at - 1e-6 else t  # noqa: E731
    main_end = len(timeline) / FPS + ins_len
    starts = {key: tmap(t) for key, t in starts.items()}
    if use_motion:
        starts[("outro", -1)] = main_end
    src_audio = sfx.read_wav(src) if info(str(src))["has_audio"] else np.zeros((0, 2))
    voice = []
    if has_voice:
        if hook and "hook" in by_id:
            voice.append((0.0, by_id["hook"]["audio"]))
        for k in range(len(impacts)):
            voice.append((starts.get((anchor, k), 0) + 0.15, by_id[k]["audio"]))
        voice.append((starts.get(("outro", -1), 0) + 0.1, by_id["outro"]["audio"]))
    extra = []
    if use_motion:                               # sons calés sur les animations de l'intro et de la carte de fin
        extra += [(ins_at, "riser", 0.5, {"d": 0.6}), (ins_at + 0.62, "impact", 1.0, {}),
                  (ins_at + 0.62, "shutter", 0.5, {}), (ins_at + 2.2, "whoosh", 0.7, {"d": 0.35}),
                  (main_end, "impact", 0.7, {}), (main_end + 1.0, "tick", 0.9, {"f": 2200}),
                  (main_end + 1.1, "tick", 0.7, {"f": 1500}), (main_end + 1.33, "tick", 0.6, {})]
    if music_from:                               # bande-son reprise d'une autre vidéo (droits requis pour publier)
        run(["ffmpeg", "-y", "-v", "error", "-i", str(Path(music_from).resolve()), "-vn", "-ac", "2", "-ar", 48000,
             "musique_reprise.wav"], cwd=work)
        music = str(work / "musique_reprise.wav")
    build_audio(timeline, impacts, src_audio, music, work / "audio.wav", orig_gain, voice, (ins_at, ins_len), post, extra,
                kit)
    if use_motion:                               # assemblage : accroche → intro → analyses → carte de fin
        norm = f"fps={FPS},scale={W}:{H},setsar=1,format=yuv420p"
        fc = (f"[0:v]trim=end={ins_at:.4f},setpts=PTS-STARTPTS,{norm}[a];[1:v]{norm}[b];"
              f"[0:v]trim=start={ins_at:.4f},setpts=PTS-STARTPTS,{norm}[c];[2:v]{norm}[d];"
              f"[a][b][c][d]concat=n=4:v=1:a=0[v]")
        run(["ffmpeg", "-y", "-v", "error", "-i", "video.mp4", "-i", "intro.mp4", "-i", "outro.mp4",
             "-filter_complex", fc, "-map", "[v]", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
             "-maxrate", "16M", "-bufsize", "32M", "video_motion.mp4"], cwd=work)
    video_in = "video_motion.mp4" if use_motion else "video.mp4"
    if not hook:
        segs = [sg for sg in segs if sg["id"] != "hook"]
    windows = {"hook": max(first_main - 0.1, 1.0), "outro": (post if use_motion else outro_len) - 0.1}
    for k, m in enumerate(impacts):
        if fluid:
            windows[k] = fluide.analysis_len(m.get("voice_dur", 0)) + 1.0
        else:
            windows[k] = freeze_len(m) - 0.25
    if not has_voice and burn != "none":
        print("   sans voix off : sous-titres écrits en .srt, pas incrustés (les étiquettes portent déjà l'info)")
        burn = "none"
    ass, srts = subtitles(segs, starts, impacts, out_base, work, burn, list(langs), windows, anchor)

    rw, rh = RESOLUTIONS[resolution]
    filters = []
    if ass:
        shutil.copytree(Path(__file__).parent / "fonts", work / "fonts", dirs_exist_ok=True)
        filters.append("ass=sous_titres.ass:fontsdir=fonts")
    if (rw, rh) != (W, H):
        filters.append(f"scale={rw}:{rh}:flags=lanczos,unsharp=5:5:0.4")
    # débit plafonné : le grain gonfle le fichier sans gain visible après recompression par les réseaux
    rate = {1080: "16M", 1440: "24M", 2160: "45M", 4320: "120M"}[rw]
    vf = ["-vf", ",".join(filters), "-c:v", "libx264", "-preset", "medium", "-crf", "17" if rw > W else "18",
          "-maxrate", rate, "-bufsize", str(int(rate[:-1]) * 2) + "M", "-pix_fmt", "yuv420p"] if filters else ["-c:v", "copy"]
    run(["ffmpeg", "-y", "-v", "error", "-i", video_in, "-i", "audio.wav", *vf,
         "-af", "loudnorm=I=-14:TP=-1:LRA=9", "-c:a", "aac", "-b:a", "192k", "-ar", 48000, "-shortest",
         "-movflags", "+faststart", "brut.mp4"], cwd=work)
    match_loudness(work / "brut.mp4", work / "final.mp4", -14)
    # pistes de sous-titres activables (YouTube / lecteurs) en plus de l'incrustation
    if srts:
        ins, maps, meta = [], [], []
        for j, (lang, path) in enumerate(srts.items()):
            ins += ["-i", path]
            maps += ["-map", str(j + 1)]
            meta += [f"-metadata:s:s:{j}", f"language={nar.LANG_ISO3.get(lang, lang)}"]
        run(["ffmpeg", "-y", "-v", "error", "-i", work / "final.mp4", *ins, "-map", "0", *maps, "-c", "copy",
             "-c:s", "mov_text", *meta, "-movflags", "+faststart", out_abs])
    else:
        shutil.copy(work / "final.mp4", out_abs)
    shutil.copy(work / "analyse.json", f"{out_base}.analyse.json")

    if extras:
        from . import seo, thumbs
        analyses = [{"t_out": starts.get((anchor, k), 0), "nom": m["info"]["nom"], "kind": m["info"]["kind"],
                     "muscles": m["info"]["muscles"]} for k, m in enumerate(impacts)]
        seo.write(seo.build(analyses, discipline, handle or ""), out_base)
        if impacts:
            top = max(range(len(impacts)), key=lambda j: impacts[j]["score"])
            frame = next(iter_frames(base, W, H, start=impacts[top]["frame"] / FPS))
            person = renderer.freeze_cache.get(top, {}).get("person")
            thumbs.make_thumbnails(frame, out_base, impacts[top]["info"]["nom"], mask=person, accent=accent or gfx.GREEN)
    return out_abs
