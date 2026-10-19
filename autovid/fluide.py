"""Mode « fluide » : l'analyse se fait sur la vidéo EN MOUVEMENT, sans arrêt sur image long.

Repris du modèle de référence (Gemini) : ralenti autour du coup, zoom précis sur le membre qui travaille,
membre colorié (pas de traits ni de ronds partout), petite flèche de trajectoire, étoile d'impact, titres courts
en deux lignes. Un seul rond, sur l'articulation qui compte, pendant la pause du contact.
"""
import cv2
import numpy as np

from . import gfx
from .effets import transition
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
SPIN_NAMES = ("MEIA-LUA", "ARMADA", "QUEIXADA", "MARTELO RODADO", "AÚ", "SPIN")


def contact_profile(tracks, m):
    """Ce que touche le coup et s'il y a rotation, pour choisir les bruits.
    cible : "corps" (l'extrémité arrive sur une autre personne), "sac" (arrêt net sans personne : sac, pao),
    "air" (le membre continue sa course)."""
    tr, f, e = tracks[m["track"]], m["frame"], m["eff"]
    s = np.array([1.0, 16 / 9])
    p = tr[:, e, :2] * s
    torso = torso_len(tr[f]) if np.isfinite(tr[f, 0, 0]) else 0.1
    torso = torso if np.isfinite(torso) and torso > 0 else 0.1
    v = np.r_[0, np.linalg.norm(np.diff(p, axis=0), axis=1)] / torso
    before = np.nanmax(v[max(f - 4, 0): f + 1]) if f > 0 else 0
    after = np.nanmean(v[f + 1: min(f + 4, len(v))]) if f + 1 < len(v) else before
    stop = bool(np.isfinite(before) and before > 0 and np.isfinite(after) and after < 0.35 * before)
    near = False
    for k in range(tracks.shape[0]):
        if k == m["track"] or not np.isfinite(tracks[k, f, 0, 0]):
            continue
        body = tracks[k, f, [0, 11, 12, L_HIP, R_HIP], :2] * s
        body = body[np.isfinite(body).all(axis=1)]
        if len(body) and np.isfinite(p[f]).all() and np.min(np.linalg.norm(body - p[f], axis=1)) < 0.6 * torso:
            near = True
    cible = "corps" if near else ("sac" if stop and m["info"]["kind"] in ("pied", "poing", "genou") else "air")
    # rotation : la ligne des hanches tourne de plus de ~75° entre le début du ralenti et le contact
    a, b = max(f - int(PRE_SRC * FPS), 0), f
    def hip_angle(i):
        d = (tr[i, R_HIP, :2] - tr[i, L_HIP, :2]) * s
        return np.arctan2(d[1], d[0]) if np.isfinite(d).all() else np.nan
    turn = abs((hip_angle(b) - hip_angle(a) + np.pi) % (2 * np.pi) - np.pi)
    rotation = bool(np.isfinite(turn) and turn > 1.3) or any(x in m["info"]["nom"] for x in SPIN_NAMES) \
        or m["info"]["kind"] == "au"
    return {"cible": cible, "rotation": rotation}


def slow_parts(t, curve=None):
    """Positions source du ralenti avant et après le contact `t` (image) : vitesse fixe, ou courbe CapCut."""
    if curve:
        from .effets import ramp
        return ramp(t - PRE_SRC * FPS, t, t + POST_SRC * FPS, curve)
    before = [t - PRE_SRC * FPS + j * SLOW_IN for j in range(int(PRE_SRC * FPS / SLOW_IN))]
    after = [t + j * SLOW_OUT for j in range(int(POST_SRC * FPS / SLOW_OUT))]
    return before, after


def analysis_len(voice_dur=0.0, curve=None):
    """Durée minimale d'une analyse (ralenti + contact + ralenti) : la voix doit pouvoir finir avant la suivante."""
    before, after = slow_parts(1000, curve)
    return max((len(before) + len(after)) / FPS + HIT, voice_dur + 0.3)


def build_timeline(n_frames, impacts, hook=True, max_dead=2.5, outro_len=1.8, curve=None):
    out = []

    def add(src, phase, imp=-1, lt=0.0, pd=0.0):
        out.append({"src": float(min(max(src, 0), n_frames - 1)), "phase": phase, "imp": imp, "lt": lt, "pd": pd})

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
                add(s, "jump" if j < 7 else "normal", lt=j / FPS)
        else:
            for s in range(a, b):
                add(s, "normal")

    def analysis(k, m, prefix=""):
        t = m["frame"]
        before, after = slow_parts(t, curve)
        for j, s in enumerate(before):
            add(s, prefix + "slow", k, j / FPS, len(before) / FPS)
        for j in range(int(HIT * FPS)):
            add(t, prefix + "hit", k, j / FPS, HIT)
        for j, s in enumerate(after):
            add(s, prefix + "after", k, j / FPS, len(after) / FPS)
        return t + POST_SRC * FPS

    if hook and impacts:
        h = max(range(len(impacts)), key=lambda j: impacts[j]["score"])
        analysis(h, impacts[h], "hook_")
    cursor, need = 0, 0.0
    for k, m in enumerate(impacts):
        s0 = max(cursor, m["frame"] - PRE_SRC * FPS)
        normal(cursor, s0, first=(k == 0), need=need)
        cursor = analysis(k, m)
        spent = analysis_len(0, curve)
        need = max(0.0, m.get("voice_dur", 0) + 0.3 - spent)
    tail = min(n_frames, int(cursor + max(1.0, need + 0.4) * FPS)) if impacts else n_frames
    normal(int(cursor), tail)
    last = out[-1]["src"] if out else 0
    for j in range(int(outro_len * FPS)):
        add(last, "outro", -1, j / FPS)
    if hook and impacts:
        first_main = next(i for i, f in enumerate(out) if not f["phase"].startswith("hook"))
        for j in range(first_main, min(first_main + 7, len(out))):
            if out[j]["phase"] == "normal":
                out[j]["phase"], out[j]["lt"] = "jump", (j - first_main) / FPS
    return out


def _star(c, r_out, r_in, n=12, rot=0.0):
    a = np.linspace(0, 2 * np.pi, 2 * n, endpoint=False) + rot
    r = np.where(np.arange(2 * n) % 2 == 0, r_out, r_in)
    return np.stack([c[0] + r * np.cos(a), c[1] + r * np.sin(a)], axis=1).astype(np.int32)


def focus_part(info):
    """(os à tracer, point suivi par la flèche) : la partie précise du corps qui fait le mouvement."""
    from .anatomy import J
    sh, el, wr, hip, knee, ank, foot = J[info.get("side", "D")]
    kind = info["kind"]
    if kind in ("pied", "rasteira"):
        return [(hip, knee), (knee, ank), (ank, foot)], ank
    if kind == "genou":
        return [(hip, knee)], knee
    if kind == "esquive":
        return [(hip, knee), (knee, ank)], hip
    return [(sh, el), (el, wr)], wr            # poing, ginga, aú : le bras


def _curve_arrow(img, pts, color, thick, min_len=0.0):
    """Flèche courbe lisse (Bézier passant par le milieu du trajet), contour noir pour la lisibilité."""
    a0, a2 = pts[0], pts[-1]
    if np.linalg.norm(a2 - a0) <= min_len:
        return
    a1 = pts[len(pts) // 2] * 2 - (a0 + a2) / 2
    u = np.linspace(0, 1, 24)[:, None]
    curve = ((1 - u) ** 2 * a0 + 2 * (1 - u) * u * a1 + u ** 2 * a2).astype(np.int32)
    w = thick // 2 + 3
    cv2.polylines(img, [curve], False, (0, 0, 0), w + 5, cv2.LINE_AA)
    cv2.polylines(img, [curve], False, color, w, cv2.LINE_AA)
    d = (curve[-1] - curve[-3]).astype(float)
    if np.linalg.norm(d) > 1:
        d /= np.linalg.norm(d)
        nrm = np.array([-d[1], d[0]])
        tri = np.array([curve[-1] + d * thick * 1.7, curve[-1] + nrm * thick * 1.1,
                        curve[-1] - nrm * thick * 1.1]).astype(np.int32)
        cv2.fillPoly(img, [tri], (0, 0, 0), cv2.LINE_AA)
        cv2.fillPoly(img, [(tri * 0.92 + tri.mean(axis=0) * 0.08).astype(np.int32)], color, cv2.LINE_AA)


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
        z = float(np.clip(0.42 * H / max(span, 40), 1.35, getattr(self, "max_zoom", 2.4)))
        return z, c

    def zoom_for(self, f):
        ph, lt, imp = f["phase"], f["lt"], f["imp"]
        if imp < 0:
            if ph == "jump":
                return 1 + 0.12 * (1 - gfx.ease(lt / 0.2)), None
            return 1.0, None
        m = self.impacts[imp]
        if not m["info"].get("fx", {}).get("zoom", True):
            return 1.0, None
        zt, c = self.limb_focus(m, f["src"] if not ph.endswith("hit") else m["frame"])
        base = ph.replace("hook_", "")
        pd = f.get("pd") or {"slow": PRE_SRC / SLOW_IN, "hit": HIT, "after": POST_SRC / SLOW_OUT}.get(base, 1.0)
        if base == "slow":
            z = 1 + (zt - 1) * gfx.ease(lt / (pd * 0.8))
        elif base == "hit":
            z = zt * (1 + 0.06 * gfx.ease(lt / HIT))
        elif base == "after":
            z = zt * 1.06 - (zt * 1.06 - 1) * gfx.ease(lt / pd)
        else:
            z = 1.0
        return z, c

    def shake_for(self, f):
        if f["phase"].endswith("hit") and f["lt"] < 0.15:
            amp = 14 * (1 - f["lt"] / 0.15)
            return tuple(self.rng.uniform(-amp, amp, 2))
        return (0, 0)

    def limb_mask(self, m, src, frame_rgb, xy, bones, torso):
        """Masque 0–1 du membre : silhouette MediaPipe ∩ capsule autour des os. Sans silhouette exploitable
        (personne trop petite, flou), bande douce autour des os. Renvoie (masque, boîte) ou (None, None)."""
        if not bones:
            return None, None
        pts = np.array([p for a, b in bones for p in (xy[a], xy[b])])
        pad = torso * 0.45 + 20
        x0, y0 = np.maximum(pts.min(axis=0) - pad, 0).astype(int)
        x1, y1 = np.minimum(pts.max(axis=0) + pad, [W, H]).astype(int)
        if x1 - x0 < 8 or y1 - y0 < 8:
            return None, None
        off = np.array([x0, y0])
        cap = np.zeros((y1 - y0, x1 - x0), np.uint8)
        for a, b in bones:
            cv2.line(cap, tuple((xy[a] - off).astype(int)), tuple((xy[b] - off).astype(int)), 255,
                     max(int(torso * 0.42), 9), cv2.LINE_AA)
        cap = cap.astype(np.float32) / 255
        person = self.person_mask(m, src, frame_rgb)
        if person is not None:
            limb = cap * person[y0:y1, x0:x1]
            if limb.sum() > 0.15 * cap.sum():      # assez de silhouette dans la capsule : on suit le vrai membre
                cap = cv2.GaussianBlur(limb, (0, 0), 1.5)
                return self._full(cap, x0, y0), (x0, y0, x1, y1)
        thin = np.zeros_like(cap)
        for a, b in bones:
            cv2.line(thin, tuple((xy[a] - off).astype(int)), tuple((xy[b] - off).astype(int)), 1.0,
                     max(int(torso * 0.2), 7), cv2.LINE_AA)
        return self._full(cv2.GaussianBlur(thin, (0, 0), max(torso * 0.05, 2)), x0, y0), (x0, y0, x1, y1)

    @staticmethod
    def _full(part, x0, y0):
        full = np.zeros((H, W), np.float32)
        full[y0:y0 + part.shape[0], x0:x0 + part.shape[1]] = part
        return full

    def person_mask(self, m, src, frame_rgb):
        """Silhouette (pleine résolution) de la personne suivie, mise en cache par image source."""
        from .pose import segment
        cache = self.__dict__.setdefault("_masks", {})
        key = (m["track"], int(round(src)))
        if key not in cache:
            cache[key] = None
            try:
                poses, masks = segment(cv2.resize(frame_rgb, (W // 2, H // 2)))
            except Exception:                    # MediaPipe absent ou image illisible : repli sur la bande douce
                poses, masks = [], []
            ref = self.tracks[m["track"], min(key[1], self.tracks.shape[1] - 1), [L_HIP, R_HIP, L_SH, R_SH], :2]
            best = None
            for p, mk in zip(poses, masks):
                d = np.nanmean(np.linalg.norm(p[[L_HIP, R_HIP, L_SH, R_SH], :2] - ref, axis=1))
                if np.isfinite(d) and d < 0.08 and (best is None or d < best[0]):
                    best = (d, mk)
            if best is not None:
                cache[key] = cv2.resize(best[1], (W, H))
            if len(cache) > 64:
                cache.pop(next(iter(cache)))
        return cache[key]

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

        # Une seule partie du corps, coloriée (pas de trait) : la jambe qui frappe, ou le bras qui protège / porte.
        bones, target = focus_part(info_)
        fx = info_.get("fx", {})
        on = lambda name: fx.get(name, True)  # noqa: E731  (effets cochés / décochés dans la plateforme)
        mask, box = (self.limb_mask(m, src, frame_rgb, xy, [(a, b) for a, b in bones if ok(a) and ok(b)], torso)
                     if on("couleur") else (None, None))
        if mask is not None:
            gfx.glow_fill(img, mask, self.accent, alpha=0.55 * fade, glow=0.35 * fade, box=box)

        # un seul rond, sur l'articulation qui compte, seulement pendant la pause du contact
        pause = base == "hit" or (base == "after" and lt < 0.35)
        if pause and ok(target) and on("rond"):
            a = 1.0 if base == "hit" else 1 - lt / 0.35
            r = torso * 0.28 * (1 + 0.15 * gfx.ease(min(lt / 0.12, 1)) if base == "hit" else 1.15)
            if info_["kind"] == "au":           # aú : l'ellipse d'appui sous la main remplace le rond
                ax = (int(torso * 0.42), int(torso * 0.13))
                c = tuple((xy[target] + [0, torso * 0.06]).astype(int))
                over = img.copy()
                cv2.ellipse(over, c, ax, 0, 0, 360, (0, 0, 0), 9, cv2.LINE_AA)
                cv2.ellipse(over, c, ax, 0, 0, 360, gfx.YELLOW, 5, cv2.LINE_AA)
            else:
                over = img.copy()
                gfx.ring(over, xy[target], r, gfx.YELLOW, 5)
            cv2.addWeighted(over, a, img, 1 - a, 0, dst=img)

        # une flèche courbe et lisse qui suit l'extrémité de cette partie
        if on("fleche") and (base in ("slow", "hit") or (base == "after" and lt < 0.3)):
            pts = []
            if ok(target):                           # trajet récent et CONTINU : on s'arrête au premier saut de suivi
                prev = xy[target]
                for d in np.arange(0, 16, 2):
                    p, _ = self.live(m, max(src - d, 0), span=3)
                    q = p[target]
                    if not np.isfinite(q).all() or np.linalg.norm(q - prev) > torso * 0.6:
                        break
                    pts.append(q)
                    prev = q
            if len(pts) >= 4:
                _curve_arrow(img, np.array(pts[::-1]), gfx.YELLOW, max(int(thick * 0.6), 5), min_len=torso * 0.3)

        # étoile d'impact au contact (coups seulement)
        if on("etoile") and info_["kind"] in BURST_KINDS and (base == "hit" or (base == "after" and lt < 0.25)):
            t = lt if base == "hit" else HIT + lt
            e = info_["effector"]
            if ok(e):
                r = torso * (0.35 + 0.65 * gfx.ease(t / 0.15))
                a = 1 - gfx.ease((t - 0.25) / 0.25)
                over = img.copy()
                cv2.fillPoly(over, [_star(xy[e], r, r * 0.42, 12, t * 2)], self.accent, cv2.LINE_AA)
                cv2.fillPoly(over, [_star(xy[e], r * 0.55, r * 0.25, 12, t * 2 + 0.2)], (255, 255, 255), cv2.LINE_AA)
                cv2.addWeighted(over, 0.9 * a, img, 1 - 0.9 * a, 0, dst=img)

    def screen_overlays(self, img, f, k, M):
        ph, lt, imp = f["phase"], f["lt"], f["imp"]
        base = ph.replace("hook_", "")
        acc = self.accent
        if base == "hit" and lt < 0.1:
            transition(img, "flash", lt, self.rng, 0.1)
        if ph == "jump":                         # transition de coupe choisie (CapCut : flash, zoom, whip, glitch)
            kind = getattr(self, "transition", "flash")
            if kind == "mix":
                kind = ("zoom", "whip", "glitch", "flash")[int(f["src"]) % 4]
            transition(img, kind, lt, self.rng, 0.1 if kind == "flash" else 0.2)
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
                pre = self.slow_len.get(imp, PRE_SRC / SLOW_IN) if hasattr(self, "slow_len") else PRE_SRC / SLOW_IN
                t_all = lt + {"slow": 0, "hit": pre, "after": pre + HIT}[base]
                out = 1 - gfx.ease((t_all - 2.4) / 0.25)
                if out > 0.02:
                    gfx.paste(img, gfx.text_sprite(info_["nom"], 124, gfx.WHITE, stroke=9), W / 2, 330,
                              gfx.pop(t_all), out)
                    gfx.paste(img, gfx.text_sprite(info_.get("cle") or CLE.get(info_["kind"], info_["membre"]), 70, gfx.YELLOW, stroke=7),
                              W / 2, 448, gfx.pop(t_all - 0.12), out)
                gfx.paste(img, gfx.text_sprite("RALENTI", 34, gfx.WHITE, stroke=4, shadow=4), W / 2, 150, 1, 0.75)
                if base == "after" and info_.get("risque") and info_.get("fx", {}).get("risque", True):
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
