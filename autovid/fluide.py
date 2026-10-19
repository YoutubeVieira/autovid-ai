"""Mode « fluide » : l'analyse se fait sur la vidéo EN MOUVEMENT, sans arrêt sur image long.

Repris du modèle de référence (Gemini) : ralenti autour du coup, zoom précis sur le membre qui travaille,
traits de couleur sur les membres, trajectoire en arc, étoile d'impact, ellipse sous l'appui, flèches de
déplacement, titres courts en deux lignes.
"""
import cv2
import numpy as np

from . import gfx
from .media import FPS, H, W
from .pose import L_ANK, L_EL, L_HIP, L_KNEE, L_SH, L_WR, R_ANK, R_EL, R_HIP, R_KNEE, R_SH, R_WR, torso_len

SLOW_IN = 0.40         # vitesse du ralenti avant le contact
SLOW_OUT = 0.50        # vitesse juste après
PRE_SRC, POST_SRC = 0.7, 0.5   # durées (source) ralenties avant / après le contact
HIT = 0.25             # micro-arrêt sur le contact
MID = {L_WR: L_EL, R_WR: R_EL, L_ANK: L_KNEE, R_ANK: R_KNEE, L_KNEE: L_HIP, R_KNEE: R_HIP}
ROOT = {L_WR: L_SH, R_WR: R_SH, L_ANK: L_HIP, R_ANK: R_HIP, L_KNEE: L_HIP, R_KNEE: R_HIP}

CLE = {  # le mot-clé de la 2e ligne du titre
    "au": "MAINS AU SOL", "ginga": "BRAS QUI PROTÈGE", "esquive": "BASSIN BAS", "pied": "LA HANCHE TOURNE",
    "poing": "ROTATION DU BUSTE", "rasteira": "LE BON TIMING", "genou": "BASSIN EN AVANT",
}
BURST_KINDS = {"pied", "poing", "genou", "rasteira"}


def analysis_len(voice_dur=0.0):
    """Durée minimale d'une analyse (ralenti + contact + ralenti) : la voix doit pouvoir finir avant la suivante."""
    base = PRE_SRC / SLOW_IN + HIT + POST_SRC / SLOW_OUT
    return max(base, voice_dur + 0.3)


def build_timeline(n_frames, impacts, hook=True, max_dead=2.5, outro_len=1.8):
    out = []

    def add(src, phase, imp=-1, lt=0.0):
        out.append({"src": float(min(max(src, 0), n_frames - 1)), "phase": phase, "imp": imp, "lt": lt})

    def normal(a, b, first=False, need=0.0):
        """Plans à vitesse normale entre deux analyses ; les temps morts sont coupés, mais on garde `need`
        secondes pour que la voix de l'analyse précédente finisse."""
        a, b = int(a), int(b)
        if b <= a:
            return
        if first and b - a > 1.2 * FPS:
            a = b - int(1.2 * FPS)
        keep = max(int(max_dead * FPS), int(need * FPS) + int(0.8 * FPS))
        if b - a > keep:
            head = max(int(0.6 * FPS), int(need * FPS))
            tail = int(0.8 * FPS)
            for s in range(a, a + head):
                add(s, "normal")
            for j, s in enumerate(range(b - tail, b)):
                add(s, "jump" if j < 5 else "normal", lt=j / FPS)
        else:
            for s in range(a, b):
                add(s, "normal")

    def analysis(k, m, prefix=""):
        t = m["frame"]
        s0 = t - PRE_SRC * FPS
        for j in range(int(PRE_SRC * FPS / SLOW_IN)):
            add(s0 + j * SLOW_IN, prefix + "slow", k, j / FPS)
        for j in range(int(HIT * FPS)):
            add(t, prefix + "hit", k, j / FPS)
        for j in range(int(POST_SRC * FPS / SLOW_OUT)):
            add(t + j * SLOW_OUT, prefix + "after", k, j / FPS)
        return t + POST_SRC * FPS

    if hook and impacts:
        h = max(range(len(impacts)), key=lambda j: impacts[j]["score"])
        analysis(h, impacts[h], "hook_")
    cursor, need = 0, 0.0
    for k, m in enumerate(impacts):
        s0 = max(cursor, m["frame"] - PRE_SRC * FPS)
        normal(cursor, s0, first=(k == 0), need=need)
        cursor = analysis(k, m)
        spent = PRE_SRC / SLOW_IN + HIT + POST_SRC / SLOW_OUT
        need = max(0.0, m.get("voice_dur", 0) + 0.3 - spent)
    tail = min(n_frames, int(cursor + max(1.0, need + 0.4) * FPS)) if impacts else n_frames
    normal(int(cursor), tail)
    last = out[-1]["src"] if out else 0
    for j in range(int(outro_len * FPS)):
        add(last, "outro", -1, j / FPS)
    if hook and impacts:
        first_main = next(i for i, f in enumerate(out) if not f["phase"].startswith("hook"))
        for j in range(first_main, min(first_main + 5, len(out))):
            if out[j]["phase"] == "normal":
                out[j]["phase"], out[j]["lt"] = "jump", (j - first_main) / FPS
    return out


def _star(c, r_out, r_in, n=12, rot=0.0):
    a = np.linspace(0, 2 * np.pi, 2 * n, endpoint=False) + rot
    r = np.where(np.arange(2 * n) % 2 == 0, r_out, r_in)
    return np.stack([c[0] + r * np.cos(a), c[1] + r * np.sin(a)], axis=1).astype(np.int32)


def _glow_strokes(img, segs, thick):
    """Traits épais lumineux : segs = [(p1, p2, couleur)] dans l'espace image."""
    pts = np.array([p for a, b, _ in segs for p in (a, b)])
    if not len(pts):
        return
    pad = thick * 3 + 30
    x0, y0 = np.maximum(pts.min(axis=0) - pad, 0).astype(int)
    x1, y1 = np.minimum(pts.max(axis=0) + pad, [W, H]).astype(int)
    if x1 - x0 < 8 or y1 - y0 < 8:
        return
    off = np.array([x0, y0])
    for col in {c for _, _, c in segs}:
        m = np.zeros((y1 - y0, x1 - x0), np.uint8)
        for a, b, c in segs:
            if c == col:
                cv2.line(m, tuple((a - off).astype(int)), tuple((b - off).astype(int)), 255, int(thick), cv2.LINE_AA)
        gfx.glow_fill(img[y0:y1, x0:x1], m.astype(np.float32) / 255, col, alpha=0.78, glow=0.7)


class FluidMixin:
    """À combiner avec combat.Renderer : remplace zoom, tremblement et habillage."""

    def live(self, m, src, span=2):
        """Pose lissée autour de l'image source (moyenne sur ±span images) : suivi stable du membre."""
        tr = self.tracks[m["track"]]
        i = int(round(src))
        win = tr[max(i - span, 0): i + span + 1, :, :2]
        xy = np.nanmean(win, axis=0) * np.array([W, H])
        vis = tr[min(i, len(tr) - 1), :, 2]
        return xy, vis

    def limb_focus(self, m, src):
        """Centre et zoom pour cadrer le membre qui travaille (extrémité + articulation intermédiaire)."""
        xy, _ = self.live(m, src)
        e = m["eff"]
        eff, mid, root = xy[e], xy[MID.get(e, e)], xy[ROOT.get(e, e)]
        if not (np.isfinite(eff).all() and np.isfinite(mid).all()):
            return 1.0, None
        c = eff * 0.45 + mid * 0.35 + (root if np.isfinite(root).all() else mid) * 0.2
        span = np.linalg.norm(eff - root) if np.isfinite(root).all() else np.linalg.norm(eff - mid) * 2
        z = float(np.clip(0.42 * H / max(span, 40), 1.35, 2.4))
        return z, c

    def zoom_for(self, f):
        ph, lt, imp = f["phase"], f["lt"], f["imp"]
        if imp < 0:
            if ph == "jump":
                return 1 + 0.12 * (1 - gfx.ease(lt / 0.2)), None
            return 1.0, None
        m = self.impacts[imp]
        zt, c = self.limb_focus(m, f["src"] if not ph.endswith("hit") else m["frame"])
        base = ph.replace("hook_", "")
        if base == "slow":
            z = 1 + (zt - 1) * gfx.ease(lt / (PRE_SRC / SLOW_IN * 0.8))
        elif base == "hit":
            z = zt * (1 + 0.06 * gfx.ease(lt / HIT))
        elif base == "after":
            z = zt * 1.06 - (zt * 1.06 - 1) * gfx.ease(lt / (POST_SRC / SLOW_OUT))
        else:
            z = 1.0
        return z, c

    def shake_for(self, f):
        if f["phase"].endswith("hit") and f["lt"] < 0.15:
            amp = 14 * (1 - f["lt"] / 0.15)
            return tuple(self.rng.uniform(-amp, amp, 2))
        return (0, 0)

    def scene_overlays(self, img, f, frame_rgb):
        ph, lt, imp = f["phase"], f["lt"], f["imp"]
        base = ph.replace("hook_", "")
        if imp < 0 or base not in ("slow", "hit", "after"):
            return
        m = self.impacts[imp]
        info_ = m["info"]
        src = m["frame"] if base == "hit" else f["src"]
        xy, vis = self.live(m, src)
        if not np.isfinite(xy[[L_HIP, R_HIP, L_SH, R_SH]]).all():
            return
        torso = torso_len(np.concatenate([xy / np.array([W, H]), vis[:, None]], axis=1)) * W
        thick = max(int(torso * 0.11), 7)
        fade = 1.0 if base != "after" else 1 - gfx.ease((lt - 0.4) / 0.6)
        if fade <= 0.02:
            return
        ok = lambda j: np.isfinite(xy[j]).all() and vis[j] > 0.2  # noqa: E731

        # 1. traits de couleur : appui en orange, chaîne qui travaille dans la couleur d'accent
        segs = [(xy[a], xy[b], gfx.ORANGE) for a, b in info_["support"] if ok(a) and ok(b)]
        segs += [(xy[a], xy[b], self.accent) for a, b in info_["chain"] if ok(a) and ok(b)]
        if fade < 1:
            over = img.copy()
            _glow_strokes(over, segs, thick)
            cv2.addWeighted(over, fade, img, 1 - fade, 0, dst=img)
        else:
            _glow_strokes(img, segs, thick)
        for j in info_["joints"]:
            if ok(j):
                gfx.ring(img, xy[j], thick * 1.3, (255, 255, 255), 3)

        # 2. ellipse sous le pied d'appui (pivot)
        sup = [j for bone in info_["support"] for j in bone if j in (L_ANK, R_ANK)]
        foot = xy[sup[0]] if sup and ok(sup[0]) else None
        if foot is not None:
            pulse = 1 + 0.08 * np.sin(lt * 10)
            ax = (int(torso * 0.55 * pulse), int(torso * 0.17 * pulse))
            cv2.ellipse(img, tuple((foot + [0, torso * 0.08]).astype(int)), ax, 0, 0, 360, (0, 0, 0), 9, cv2.LINE_AA)
            cv2.ellipse(img, tuple((foot + [0, torso * 0.08]).astype(int)), ax, 0, 0, 360, gfx.YELLOW, 5, cv2.LINE_AA)

        e = info_["effector"]
        if info_["kind"] in BURST_KINDS:
            # 3. trajectoire de l'extrémité en arc, avec pointe de flèche
            if base in ("slow", "hit"):
                pts = []
                for d in np.arange(0, 16, 1.5):
                    p, _ = self.live(m, max(src - d, 0), span=1)
                    if np.isfinite(p[e]).all() and (not np.isfinite(xy[e]).all() or
                                                    np.linalg.norm(p[e] - xy[e]) < torso * 3):
                        pts.append(p[e])
                if len(pts) >= 3:
                    pts = np.array(pts[::-1])
                    over = np.zeros_like(img)
                    for n in range(len(pts) - 1):
                        w = 3 + int(thick * 0.9 * (n + 1) / len(pts))
                        cv2.line(over, tuple(pts[n].astype(int)), tuple(pts[n + 1].astype(int)), self.accent, w, cv2.LINE_AA)
                    d = pts[-1] - pts[-2]
                    if np.linalg.norm(d) > 1:
                        d = d / np.linalg.norm(d)
                        nrm = np.array([-d[1], d[0]])
                        tip = pts[-1] + d * thick * 1.6
                        tri = np.array([tip, pts[-1] + nrm * thick, pts[-1] - nrm * thick]).astype(np.int32)
                        cv2.fillPoly(over, [tri], self.accent, cv2.LINE_AA)
                    glow = cv2.GaussianBlur(over, (0, 0), 9)
                    mask = (over.max(axis=2, keepdims=True) > 0).astype(np.float32)
                    img[:] = np.clip(img * (1 - mask * 0.85) + over * 0.85 + glow * 0.8, 0, 255)
            # 4. étoile d'impact au contact
            if base == "hit" or (base == "after" and lt < 0.25):
                t = lt if base == "hit" else HIT + lt
                if ok(e):
                    r = torso * (0.35 + 0.65 * gfx.ease(t / 0.15))
                    a = 1 - gfx.ease((t - 0.25) / 0.25)
                    over = img.copy()
                    cv2.fillPoly(over, [_star(xy[e], r, r * 0.42, 12, t * 2)], self.accent, cv2.LINE_AA)
                    cv2.fillPoly(over, [_star(xy[e], r * 0.55, r * 0.25, 12, t * 2 + 0.2)], (255, 255, 255), cv2.LINE_AA)
                    cv2.addWeighted(over, 0.9 * a, img, 1 - 0.9 * a, 0, dst=img)
        else:
            # 5. mouvement du corps (aú, esquiva, ginga) : flèche jaune courbe et lisse sur le trajet du bassin
            cur = (xy[L_HIP] + xy[R_HIP]) / 2
            pts = []
            for d in np.arange(0, 26, 2):
                p, _ = self.live(m, max(src - d, 0), span=4)
                hip = (p[L_HIP] + p[R_HIP]) / 2
                if np.isfinite(hip).all() and np.linalg.norm(hip - cur) < torso * 2.2:   # écarte les sauts de suivi
                    pts.append(hip)
            if len(pts) >= 4:
                pts = np.array(pts[::-1])
                a0, a2 = pts[0], pts[-1]
                a1 = pts[len(pts) // 2] * 2 - (a0 + a2) / 2           # point de contrôle : la courbe passe par le milieu
                if np.linalg.norm(a2 - a0) > torso * 0.35:
                    u = np.linspace(0, 1, 24)[:, None]
                    curve = ((1 - u) ** 2 * a0 + 2 * (1 - u) * u * a1 + u ** 2 * a2).astype(np.int32)
                    w = thick // 2 + 3
                    cv2.polylines(img, [curve], False, (0, 0, 0), w + 5, cv2.LINE_AA)
                    cv2.polylines(img, [curve], False, gfx.YELLOW, w, cv2.LINE_AA)
                    d = (curve[-1] - curve[-3]).astype(float)
                    if np.linalg.norm(d) > 1:
                        d /= np.linalg.norm(d)
                        nrm = np.array([-d[1], d[0]])
                        tri = np.array([curve[-1] + d * thick * 1.7, curve[-1] + nrm * thick * 1.1,
                                        curve[-1] - nrm * thick * 1.1]).astype(np.int32)
                        cv2.fillPoly(img, [tri], (0, 0, 0), cv2.LINE_AA)
                        cv2.fillPoly(img, [(tri * 0.92 + tri.mean(axis=0) * 0.08).astype(np.int32)], gfx.YELLOW, cv2.LINE_AA)

    def screen_overlays(self, img, f, k, M):
        ph, lt, imp = f["phase"], f["lt"], f["imp"]
        base = ph.replace("hook_", "")
        acc = self.accent
        if (base == "hit" and lt < 0.1) or (ph == "jump" and lt < 0.1):
            a = (1 - lt / 0.1) * 0.6
            img[:] = img * (1 - a) + 255 * a
            img[:, 8:, 0] = img[:, :-8, 0].copy()
            img[:, :-8, 2] = img[:, 8:, 2].copy()
        if imp >= 0:
            m = self.impacts[imp]
            info_ = m["info"]
            if ph.startswith("hook_"):
                l1, l2 = info_["hook"]
                gfx.paste(img, gfx.text_sprite(l1, 96, gfx.WHITE, stroke=8), W / 2, 330,
                          gfx.pop(lt) if base == "slow" else 1)
                if base != "slow":
                    gfx.paste(img, gfx.text_sprite(l2, 78, gfx.YELLOW, stroke=7), W / 2, 445,
                              gfx.pop(lt if base == "hit" else 1))
            elif base in ("slow", "hit", "after"):
                t_all = lt + {"slow": 0, "hit": PRE_SRC / SLOW_IN, "after": PRE_SRC / SLOW_IN + HIT}[base]
                out = 1 - gfx.ease((t_all - 2.4) / 0.25)
                if out > 0.02:
                    gfx.paste(img, gfx.text_sprite(info_["nom"], 124, gfx.WHITE, stroke=9), W / 2, 330,
                              gfx.pop(t_all), out)
                    gfx.paste(img, gfx.text_sprite(CLE.get(info_["kind"], info_["membre"]), 70, gfx.YELLOW, stroke=7),
                              W / 2, 448, gfx.pop(t_all - 0.12), out)
                gfx.paste(img, gfx.text_sprite("RALENTI", 34, gfx.WHITE, stroke=4, shadow=4), W / 2, 150, 1, 0.75)
                if base == "after" and info_.get("risque"):
                    gfx.paste(img, gfx.text_sprite("ATTENTION : " + info_["risque"][0], 46, gfx.RED, stroke=5, shadow=6,
                                                   max_w=980), W / 2, 1480, gfx.pop(lt - 0.05))
                    musc = " • ".join(x[0] for x in info_["muscles"])
                    gfx.paste(img, gfx.text_sprite(musc, 38, acc, stroke=4, shadow=4, max_w=980), W / 2, 1548,
                              gfx.pop(lt - 0.15))
        if ph == "outro":
            img *= 1 - 0.55 * gfx.ease(lt / 0.3)
            gfx.paste(img, gfx.text_sprite("ABONNE-TOI", 130, gfx.WHITE), W / 2, 760, gfx.pop(lt - 0.1))
        if self.handle:
            gfx.paste(img, gfx.text_sprite(self.handle, 40, gfx.WHITE, stroke=3, shadow=4), W / 2, 1745, 1, 0.55)
        prog = int(W * (k + 1) / self.total)
        img[0:12, :prog] = img[0:12, :prog] * 0.1 + np.array(acc, np.float32) * 0.9
