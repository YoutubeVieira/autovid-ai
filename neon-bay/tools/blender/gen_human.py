"""Neon Bay - procedural skinned humans with animations (version 3).

    python3 tools/blender/gen_human.py          # human_m human_f human_m2 human_f2
    python3 tools/blender/gen_human.py f m2     # only human_f and human_m2

v3: finger bones (Thumb/Thumb2/Fingers/Fingers2 .L/.R under Hand), baked procedural textures
(nb_textures.py, UVs per part), hair locks in the geometry, stronger brows / lash lines / chin,
variants m2 (stocky, hoodie, cap = material Hat) and f2 (top + skirt = Pants, ponytail).

The body is sculpted with metaballs (ellipsoids / capsules / balls, some
negative ones for eye sockets, mouth and ears) in four separate families,
each polygonised at its own resolution then decimated to its own budget:
    body  (torso, arms, legs, shoes)     ~8 mm cells
    head  (skull, face, ears, neck)      ~4 mm cells
    hands (palm, 4 fingers, thumb)       ~3.5 mm cells, one family per hand
    hair  (cap offset from the scalp + volumes for the long female cut)
Clothes get real volume from bands built on the surface by ray casting
(shirt collar, sleeve hems, belt + buckle, trouser hems, shoe soles); these
bands also hide the seams between material regions. Eyebrows, eyes are
separate small meshes. Every element knows its bone and its material region,
so skin weights and material slots come from the same implicit field that
built the surface (smooth joints, no bone heat).

Contract (glTF, export_yup): up +Y, character faces +Z (Blender -Y), origin
between the feet on the ground (soles at y=0), A-pose bind, 1.80 m / 1.71 m.
Bones: Hips Spine Chest Neck Head UpperArm.L/R LowerArm.L/R Hand.L/R
       UpperLeg.L/R LowerLeg.L/R Foot.L/R  (three.js strips the dot: UpperArmL)
Materials: Skin Shirt Pants Shoes Hair Eyes (+ Lips, EyeWhite; Hat on human_m2 only)
Actions (24 fps): Idle Walk Run Aim AimRifle Crouch (loops), Punch, Death
(one-shot). Budget < 9000 triangles.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import bmesh  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector, Matrix, Quaternion  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402

import nb_common as nb  # noqa: E402
import nb_textures as nbt  # noqa: E402

FPS = 24
THRESH = 0.6
ORDER = ["Skin", "Shirt", "Pants", "Shoes", "Hair", "Eyes", "Lips", "EyeWhite", "Hat",
         # v4 accessories (never recoloured by the game): Gear = black plastic / cord, Metal = whistle,
         # chains, hoops (gold or silver), Lens = sunglasses, Trim = stripes / numbers / piping,
         # Sole = white sneaker soles and laces
         "Gear", "Metal", "Lens", "Trim", "Sole"]


def surf(s):
    """Surface radius / element radius for a metaball of stiffness s (threshold 0.6)."""
    return math.sqrt(1.0 - (THRESH / s) ** (1.0 / 3.0))


# --------------------------------------------------------------------------- body spec
# v4 outfits (new variants; human_m / f / m2 / f2 keep their v3 geometry):
#   top    : swim (one-piece swimsuit) | tank | crop | jersey (football) | jumpsuit
#   bottom : shorts (board shorts) | joggers | jumpsuit
#   feet   : flip (bare feet + flip-flops) | hightop (high-top sneakers, white Sole) | shoes
#   hair   : ponytail | bun (pulled back + top bun) | short | buzz
#   hat    : bucket | cap | None ;  extras: sunglasses (on the head), whistle, chain, earrings,
#            pocket, tattoo (texture on the arms), stripes (Trim stripes on the joggers), number
OUTFITS = {
    "human_f3": dict(H=1.70, top="swim", bottom="shorts", feet="flip", hair="ponytail", hat=None,
                     extras=("sunglasses", "whistle"), shorts_hem=0.70),
    "human_m3": dict(H=1.80, top="tank", bottom="shorts", feet="flip", hair="short", hat="bucket",
                     extras=("whistle",), shorts_hem=0.60, wf=1.04, lf=1.04),
    "human_f4": dict(H=1.68, top="crop", bottom="joggers", feet="hightop", hair="bun", hat=None,
                     extras=("chain", "earrings", "stripes")),
    "human_m4": dict(H=1.78, top="jersey", bottom="joggers", feet="hightop", hair="short", hat="cap",
                     extras=("chain", "stripes", "number")),
    "human_m5": dict(H=1.81, top="jumpsuit", bottom="jumpsuit", feet="shoes", hair="buzz", hat=None,
                     extras=("tattoo", "pocket"), wf=1.09, lf=1.10),
}


class Spec:
    def __init__(self, female, variant=""):
        self.female = f = female
        self.variant = variant
        self.stocky = st = (not f) and variant == "2"     # human_m2: shorter, broader, hoodie + cap
        self.dress = (f and variant == "2")               # human_f2: top + skirt, bare legs, ponytail
        self.name = ("human_f" if f else "human_m") + variant
        o = self.o = OUTFITS.get(self.name)                # v4 outfit (None for the v3 variants)
        self.v4 = o is not None
        self.top = o["top"] if o else ("hoodie" if st else "tee")
        self.bottom = o["bottom"] if o else ("skirt" if self.dress else "jeans")
        self.feet = o["feet"] if o else ("ballet" if self.dress else "shoes")
        self.hair = o["hair"] if o else ("ponytail" if self.dress else ("bob" if f else "short"))
        self.hat = o["hat"] if o else ("cap" if st else None)
        self.extras = set(o["extras"]) if o else set()
        self.pulled = self.hair in ("ponytail", "bun")     # hair pulled back (cap only + tie)
        self.H = o["H"] if o else (1.71 if f else (1.765 if st else 1.80))
        k = self.k = self.H / 1.80
        self.wf = (o or {}).get("wf", 1.12 if st else 1.0)    # torso width factor
        self.lf = (o or {}).get("lf", 1.10 if st else 1.0)    # limb girth factor
        sh = 0.166 if f else (0.197 if st else 0.186 * (1 + (self.wf - 1) * 0.6))  # shoulder joint half-width
        hip = 0.090 if f else (0.097 if st else 0.092 * (1 + (self.wf - 1) * 0.4))
        th = self.th = math.radians(24)         # arm A-pose angle from vertical (same for every variant:
        J = {}                                  # the weapon grip quaternions depend on it)
        J["hips"] = Vector((0, 0.0, 0.985 * k))
        J["spine"] = Vector((0, 0.0, 1.10 * k))
        J["chest"] = Vector((0, 0.005, 1.27 * k))
        J["neck"] = Vector((0, 0.02, 1.475 * k))
        J["head"] = Vector((0, 0.015, 1.598 * k))
        J["top"] = Vector((0, 0.0, 1.80 * k))
        ua, fa, ha = (0.300, 0.262, 0.190)
        for s, sx in (("L", 1), ("R", -1)):
            u = Vector((sx * math.sin(th), 0.0, -math.cos(th)))
            J["sho" + s] = Vector((sx * sh, 0.012, 1.445 * k))
            J["elb" + s] = J["sho" + s] + u * (ua * k) + Vector((0, 0.012, 0))
            J["wri" + s] = J["elb" + s] + u * (fa * k) + Vector((0, -0.012, 0))
            J["fin" + s] = J["wri" + s] + u * (ha * k)
            J["hip" + s] = Vector((sx * hip, 0.0, 0.935 * k))
            J["kne" + s] = Vector((sx * (hip + 0.005), -0.012, 0.505 * k))
            J["ank" + s] = Vector((sx * (hip + 0.010), 0.022, 0.082 * k))
            J["toe" + s] = Vector((sx * (hip + 0.024), -0.165 * k, 0.02))
        self.J = J
        self.hk = 0.955 if f else 1.0                     # head scale
        self.hc = Vector((0, 0.012, 1.695 * k + (1.0 - self.hk) * 0.105))  # cranium centre
        self.waist = (1.005 if f else 0.995) * k          # belt line (hoodie hem for the stocky variant)
        if st:
            self.waist = 0.925 * k
        self.hem = 0.118 * k                              # trouser hem (shoe top for the dress variant)
        if self.dress:
            self.hem = 0.088
        self.sleeve_t = 0.50 if f else 0.48               # sleeve hem along the upper arm
        self.long_sleeve = st                             # hoodie: sleeves down to the wrist
        self.skirt_hem = 0.585 * k                        # dress variant: skirt hem height
        self.sleeveless = self.top in ("swim", "tank")
        if self.top == "jersey":
            self.sleeve_t = 0.66                          # loose football shirt, long short sleeves
            self.waist = 0.93 * k                         # worn untucked: hem below the belt line
        elif self.top == "crop":
            self.sleeve_t = 0.40
        elif self.top == "jumpsuit":
            self.sleeve_t = 0.52
        if self.top == "crop":
            self.crop = self.waist + 0.085 * k            # crop-top hem (bare midriff down to the waist)
        if self.bottom == "shorts":
            self.shorts_hem = o["shorts_hem"] * k         # board shorts hem (bare legs below)
            self.waist = (0.985 if f else 0.975) * k
        if self.feet == "hightop":
            self.hem = 0.150 * k                          # high-top collar = jogger cuff
        elif self.feet == "flip":
            self.hem = -1.0                               # bare feet
        self.hand = {s: self._hand(s) for s in ("L", "R")}

    def _hand(self, s):
        """Hand frame and finger joints (rest pose). Also adds the finger joints to J."""
        J, f = self.J, self.female
        sx = 1 if s == "L" else -1
        a = 0.9 if f else (1.04 if self.stocky else 1.0)
        wri, fin = J["wri" + s], J["fin" + s]
        uh = (fin - wri).normalized()                 # along the hand
        th = Vector((0, -1, 0))                       # thumb side (forward in A-pose)
        th = (th - uh * th.dot(uh)).normalized()
        pn = uh.cross(th) * sx                        # palm normal (towards the body)
        if pn.x * sx > 0:
            pn = -pn

        def P(along, side, normal):
            return wri + uh * (along * a) + th * (side * a) + pn * (normal * a)
        fingers = []
        for side, length, rad in ((0.027, 0.076, 0.0086), (0.009, 0.084, 0.0090),
                                  (-0.009, 0.078, 0.0086), (-0.026, 0.063, 0.0078)):
            base = P(0.092, side, 0.0)
            d1 = (uh * math.cos(0.18) + pn * math.sin(0.18)).normalized()
            d2 = (uh * math.cos(0.42) + pn * math.sin(0.42)).normalized()
            mid = base + d1 * (length * 0.55 * a)
            tip = mid + d2 * (length * 0.42 * a)
            fingers.append((base, mid, tip, rad * a))
        t0 = P(0.022, 0.030, 0.006)
        dt = (uh * 0.55 + th * 0.75 + pn * 0.25).normalized()
        t1 = t0 + dt * (0.040 * a)
        dt2 = (uh * 0.85 + th * 0.35 + pn * 0.45).normalized()
        t2 = t1 + dt2 * (0.034 * a)
        avg = lambda i: sum((q[i] for q in fingers), Vector()) / 4
        J["fk" + s], J["fm" + s], J["ft" + s] = avg(0), avg(1), avg(2)
        J["tb" + s], J["tm" + s], J["tt" + s] = t0, t1, t2
        bend = uh.cross(pn).normalized()              # +angle curls the fingers into the palm
        tbend = dt.cross((pn - th * 0.6).normalized()).normalized()
        return dict(a=a, uh=uh, th=th, pn=pn, P=P, fingers=fingers, thumb=(t0, t1, t2), bend=bend,
                    tbend=tbend, tdir=dt)


# --------------------------------------------------------------------------- elements
class Fam:
    """A list of metaball elements: dict(t, co/p0/p1, semi, rot, r, s, neg, bone, reg)."""

    def __init__(self):
        self.E = []

    def ball(self, c, size, bone, reg, s=2.0, neg=False):
        self.E.append(dict(t="BALL", co=Vector(c), r=size / surf(s), s=s, neg=neg, bone=bone, reg=reg))

    def caps(self, p0, p1, size, bone, reg, s=2.0, neg=False):
        self.E.append(dict(t="CAPSULE", p0=Vector(p0), p1=Vector(p1), r=size / surf(s), s=s, neg=neg,
                           bone=bone, reg=reg))

    def ell(self, c, semi, bone, reg, axis=None, lateral=None, s=2.0, neg=False):
        """Ellipsoid; semi = (lateral, depth, along-axis) surface half sizes; axis = local Z."""
        z = Vector(axis).normalized() if axis else Vector((0, 0, 1))
        x = Vector(lateral) if lateral else Vector((1, 0, 0))
        if abs(x.normalized().dot(z)) > 0.99:
            x = Vector((0, 1, 0))
        x = (x - z * x.dot(z)).normalized()
        y = z.cross(x)
        rot = Matrix((x, y, z)).transposed()
        self.E.append(dict(t="ELLIPSOID", co=Vector(c), semi=Vector(semi), rot=rot, r=1.0 / surf(s), s=s,
                           neg=neg, bone=bone, reg=reg))


def fields(E, P):
    """(N, len(E)) array of each element's signed field contribution at points P (N, 3)."""
    P = np.asarray(P, dtype=np.float64)
    out = np.zeros((len(P), len(E)))
    for j, e in enumerate(E):
        if e["t"] == "BALL":
            q = ((P - np.array(e["co"])) ** 2).sum(1) / e["r"] ** 2
        elif e["t"] == "CAPSULE":
            a, b = np.array(e["p0"]), np.array(e["p1"])
            ab = b - a
            h = np.clip((P - a) @ ab / (ab @ ab), 0, 1)
            d = P - (a + h[:, None] * ab)
            q = (d ** 2).sum(1) / e["r"] ** 2
        else:
            rot = np.array(e["rot"])
            loc = (P - np.array(e["co"])) @ rot / np.array(e["semi"])
            q = (loc ** 2).sum(1) / e["r"] ** 2
        w = np.where(q < 1, e["s"] * np.clip(1 - q, 0, 1) ** 3, 0.0)
        out[:, j] = -w if e["neg"] else w
    return out


def metaball_mesh(name, E, resolution):
    mb = bpy.data.metaballs.new(name)
    mb.resolution = resolution
    mb.render_resolution = resolution
    mb.threshold = THRESH
    obj = nb.link(bpy.data.objects.new(name, mb))
    for d in E:
        t = d["t"]
        e = mb.elements.new(type=t)
        e.stiffness = d["s"]
        e.radius = d["r"]
        e.use_negative = d["neg"]
        if t == "BALL":
            e.co = d["co"]
        elif t == "CAPSULE":
            a, b = d["p0"], d["p1"]
            e.co = (a + b) / 2
            e.size_x = max((b - a).length / 2, 1e-4)
            e.rotation = Vector((1, 0, 0)).rotation_difference((b - a).normalized())
        else:
            e.co = d["co"]
            e.size_x, e.size_y, e.size_z = d["semi"]
            e.rotation = d["rot"].to_quaternion()
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    me = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
    bpy.data.objects.remove(obj)
    bpy.data.metaballs.remove(mb)
    return nb.link(bpy.data.objects.new(name, me))


def body_elements(sp):
    J, k, f = sp.J, sp.k, sp.female
    st, wf = sp.stocky, sp.wf
    B = Fam()
    # ---- torso (T-shirt / top: slightly loose volumes; hoodie: looser and longer)
    if not sp.sleeveless:
        B.caps((0, 0.022, 1.40 * k), (0, 0.022, 1.50 * k), 0.040 if f else (0.052 if st else 0.046), "Neck", "Shirt")
    if f:
        B.ell((0, 0.008, 1.335 * k), (0.135, 0.098, 0.145 * k), "Chest", "Shirt")
        B.caps((-0.11, 0.02, 1.425 * k), (0.11, 0.02, 1.425 * k), 0.050, "Chest", "Shirt")
        for sx in (1, -1):
            B.ell((sx * 0.058, -0.068, 1.292 * k), (0.060, 0.050, 0.056), "Chest", "Shirt")       # bust
            B.ell((sx * 0.07, 0.03, 1.465 * k), (0.05, 0.04, 0.03), "Chest", "Shirt")             # trapezius
        B.ell((0, 0.0, 1.165 * k), (0.112, 0.085, 0.115 * k), "Spine", "Shirt")                   # waist
        B.ell((0, 0.012, 0.985 * k), (0.170, 0.108, 0.112 * k), "Hips", "Pants")
        for sx in (1, -1):
            B.ell((sx * 0.072, 0.066, 0.925 * k), (0.084, 0.07, 0.09 * k), "Hips", "Pants")       # glutes
    else:
        B.ell((0, 0.008, 1.33 * k), (0.158 * wf, 0.110 * wf, 0.150 * k), "Chest", "Shirt")
        B.caps((-0.13 * wf, 0.02, 1.43 * k), (0.13 * wf, 0.02, 1.43 * k), 0.058 * wf, "Chest", "Shirt")
        for sx in (1, -1):
            B.ell((sx * 0.068 * wf, -0.058 * wf, 1.35 * k), (0.072 * wf, 0.045, 0.062), "Chest", "Shirt")   # pecs
            B.ell((sx * 0.085 * wf, 0.04, 1.30 * k), (0.072 * wf, 0.06, 0.12), "Chest", "Shirt")            # lats
            B.ell((sx * 0.078 * wf, 0.03, 1.47 * k), (0.06 * wf, 0.045, 0.034), "Chest", "Shirt")           # trapezius
        if st:   # belly + loose hoodie body down to the hips
            B.ell((0, -0.03, 1.13 * k), (0.150, 0.118, 0.13 * k), "Spine", "Shirt")
            B.ell((0, -0.045, 1.08 * k), (0.115, 0.075, 0.075 * k), "Spine", "Shirt")
            B.ell((0, 0.012, 0.975 * k), (0.172, 0.118, 0.095 * k), "Hips", "Shirt")
            # bunched hood lying on the shoulders behind the neck
            B.ell((0, 0.088, 1.475 * k), (0.090, 0.048, 0.060), "Chest", "Shirt", s=2.4)
            for sx in (1, -1):
                B.ell((sx * 0.072, 0.050, 1.468 * k), (0.034, 0.052, 0.048), "Chest", "Shirt", s=2.4)
            B.ell((0, 0.010, 0.94 * k), (0.160, 0.108, 0.09 * k), "Hips", "Pants")
            for sx in (1, -1):
                B.ell((sx * 0.07, 0.066, 0.90 * k), (0.082, 0.068, 0.085 * k), "Hips", "Pants")
        else:
            B.ell((0, -0.002, 1.16 * k), (0.136 * wf, 0.097 * wf, 0.12 * k), "Spine", "Shirt")
            B.ell((0, 0.010, 0.99 * k), (0.158 * wf, 0.105 * wf, 0.105 * k), "Hips", "Pants")
            for sx in (1, -1):
                B.ell((sx * 0.068, 0.064, 0.93 * k), (0.078, 0.064, 0.085 * k), "Hips", "Pants")
            if sp.top == "jersey":   # loose football shirt falling over the hips
                B.ell((0, 0.004, 1.04 * k), (0.160, 0.112, 0.11 * k), "Spine", "Shirt")
            if sp.top == "jumpsuit":  # baggy overall: fuller belly / back
                B.ell((0, 0.0, 1.10 * k), (0.150 * wf, 0.108 * wf, 0.10 * k), "Spine", "Shirt")
    # ---- arms
    a = 0.86 if f else (1.08 if st else 1.0)
    for s, sx in (("L", 1), ("R", -1)):
        sho, elb, wri = J["sho" + s], J["elb" + s], J["wri" + s]
        u = (elb - sho).normalized()
        L = (elb - sho).length
        B.ball(sho + Vector((sx * 0.006, 0, -0.012)), 0.058 * a, "UpperArm." + s, "Shirt")       # deltoid
        if sp.long_sleeve:    # loose hoodie sleeve, narrowing into the rib cuff
            B.caps(sho + u * 0.04, elb, 0.056 * a, "UpperArm." + s, "Shirt")
            B.ell(elb + (wri - elb) * 0.35, (0.050 * a, 0.047 * a, 0.12 * k), "LowerArm." + s, "Shirt",
                  axis=wri - elb)
            B.caps(elb + (wri - elb) * 0.5, wri - (wri - elb).normalized() * 0.03, 0.040 * a,
                   "LowerArm." + s, "Shirt")
            continue
        if sp.sleeveless:     # bare shoulder and upper arm (swimsuit, tank top)
            B.caps(sho + u * 0.03, sho + u * (L * 0.55), 0.046 * a * sp.lf, "UpperArm." + s, "Skin")
            B.ell(sho + u * (L * 0.50) + Vector((0, 0.004, 0)), (0.041 * a * sp.lf, 0.044 * a * sp.lf, 0.10 * k),
                  "UpperArm." + s, "Skin", axis=u)                                                 # biceps / triceps
        else:
            sl = 1.12 if sp.top in ("jersey", "jumpsuit") else 1.0                                # looser sleeves
            B.caps(sho + u * 0.04, sho + u * (L * sp.sleeve_t + 0.02), 0.054 * a * sl * (sp.lf if sp.v4 else 1),
                   "UpperArm." + s, "Shirt")
        B.caps(sho + u * (L * 0.45), elb, 0.041 * a * (sp.lf if sp.v4 else 1), "UpperArm." + s, "Skin")  # biceps
        la = sp.lf if sp.v4 else 1.0
        B.ell(elb + (wri - elb) * 0.30, (0.042 * a * la, 0.039 * a * la, 0.10 * k), "LowerArm." + s, "Skin",
              axis=wri - elb)
        B.caps(elb + (wri - elb) * 0.5, wri, 0.028 * a * la, "LowerArm." + s, "Skin")
    # ---- legs (straight trousers; bare legs under the skirt) and shoes
    lg = 0.94 if f else (1.08 if st else 1.0)
    for s, sx in (("L", 1), ("R", -1)):
        hip, kne, ank, toe = J["hip" + s], J["kne" + s], J["ank" + s], J["toe" + s]
        if sp.bottom == "shorts":
            # bare legs (athletic) + loose board shorts down to sp.shorts_hem
            g = 0.94 if f else 1.04 * sp.lf
            B.ball(hip + Vector((sx * 0.014, 0.0, -0.05)), 0.094 * (1.0 if f else 1.04), "UpperLeg." + s, "Pants")
            zt = (hip.z - sp.shorts_hem) / max(1e-3, hip.z - kne.z)
            B.ell(hip + (kne - hip) * (zt * 0.5) + Vector((sx * 0.006, 0, 0)),
                  (0.088 * g + 0.006, 0.090 * g + 0.006, (zt * 0.5 + 0.03) * (hip - kne).length), "UpperLeg." + s,
                  "Pants", axis=kne - hip)                                                         # loose leg
            B.ell(hip + (kne - hip) * 0.42, (0.076 * g, 0.078 * g, 0.21 * k), "UpperLeg." + s, "Skin", axis=kne - hip)
            B.ell(hip + (kne - hip) * 0.78, (0.057 * g, 0.059 * g, 0.10 * k), "UpperLeg." + s, "Skin", axis=kne - hip)
            B.ball(kne + Vector((0, -0.006, 0.012)), 0.047 * g, "UpperLeg." + s, "Skin")             # knee
            B.ell(kne + (ank - kne) * 0.28 + Vector((0, 0.016, 0)), (0.051 * g, 0.054 * g, 0.12 * k),
                  "LowerLeg." + s, "Skin", axis=ank - kne)                                         # calf
            B.caps(kne + (ank - kne) * 0.45, ank + Vector((0, 0, 0.03)), 0.031 * g, "LowerLeg." + s, "Skin")
        elif sp.dress:
            B.ball(hip + Vector((sx * 0.012, 0.0, -0.05)), 0.088, "UpperLeg." + s, "Pants")
            B.ell(hip + (kne - hip) * 0.40, (0.074, 0.076, 0.21 * k), "UpperLeg." + s, "Skin", axis=kne - hip)
            B.ell(hip + (kne - hip) * 0.78, (0.056, 0.058, 0.10 * k), "UpperLeg." + s, "Skin", axis=kne - hip)
            B.ball(kne + Vector((0, -0.006, 0.012)), 0.046, "UpperLeg." + s, "Skin")              # knee
            B.ell(kne + (ank - kne) * 0.28 + Vector((0, 0.016, 0)), (0.050, 0.052, 0.12 * k),
                  "LowerLeg." + s, "Skin", axis=ank - kne)                                         # calf
            B.caps(kne + (ank - kne) * 0.45, ank + Vector((0, 0, 0.03)), 0.030, "LowerLeg." + s, "Skin")
        else:
            lg2 = lg * {"jumpsuit": 1.07, "joggers": 1.04}.get(sp.bottom, 1.0)
            low = 0.88 if sp.bottom == "joggers" else 1.0          # joggers taper to the cuff
            B.ball(hip + Vector((sx * 0.012, 0.0, -0.05)), 0.090 * (1.04 if f else lg2), "UpperLeg." + s, "Pants")
            B.ell(hip + (kne - hip) * 0.42, (0.080 * lg2, 0.084 * lg2, 0.21 * k), "UpperLeg." + s, "Pants",
                  axis=kne - hip)
            B.ball(kne + Vector((0, -0.002, 0.02)), 0.054 * lg2, "UpperLeg." + s, "Pants")
            B.ell(kne + (ank - kne) * 0.30 + Vector((0, 0.012, 0)), (0.060 * lg2, 0.064 * lg2, 0.15 * k),
                  "LowerLeg." + s, "Pants", axis=ank - kne)
            B.caps(kne + (ank - kne) * 0.5, ank + Vector((0, 0, 0.045 + (0.03 if low < 1 else 0))),
                   0.052 * lg2 * low, "LowerLeg." + s, "Pants")
        if sp.feet == "flip":
            # bare foot: heel, sole, instep, ball of the foot and five toes (flip-flop built separately)
            g = 0.92 if f else 1.0
            B.ball(Vector((ank.x, 0.030, 0.040)), 0.036 * g, "Foot." + s, "Skin")
            B.ell(Vector((ank.x - sx * 0.004, -0.030, 0.040)), (0.036 * g, 0.075 * g, 0.026), "Foot." + s, "Skin",
                  axis=(0, -1, 0.25), lateral=(1, 0, 0))
            B.caps(Vector((ank.x, 0.0, ank.z - 0.012)), Vector((ank.x, -0.06, 0.035)), 0.026 * g, "Foot." + s, "Skin")
            B.ell(Vector((ank.x + sx * 0.004, toe.y + 0.060, 0.026)), (0.043 * g, 0.026 * g, 0.020), "Foot." + s,
                  "Skin", axis=(1, 0, 0), lateral=(0, 1, 0))                                     # ball of the foot
            for i, (dx, dy, r) in enumerate(((-0.026, 0.0, 0.0125), (-0.006, 0.010, 0.0092), (0.010, 0.016, 0.0086),
                                             (0.024, 0.024, 0.0080), (0.036, 0.034, 0.0074))):
                c = Vector((ank.x + sx * (dx * g + 0.002), toe.y + 0.028 + dy * g, 0.013))
                B.caps(c + Vector((0, 0.010, 0.003)), c, r * g, "Foot." + s, "Skin", s=3)
            continue
        if sp.feet == "hightop":
            # high-top sneaker: padded collar above the ankle, chunky toe box
            B.ell(Vector((ank.x, 0.018, 0.120 * k)), (0.050 * lg, 0.058, 0.050), "Foot." + s, "Shoes")
            B.ball(Vector((ank.x, 0.034, 0.070)), 0.052 * lg, "Foot." + s, "Shoes")
        # shoe: heel, instep, foot, toe box (low ballerina-like shoe for the dress variant)
        sl = 0.93 if sp.dress else (1.05 if sp.feet == "hightop" else 1.0)
        B.ball(Vector((ank.x, 0.032, 0.052 * sl)), 0.047 * lg * sl, "Foot." + s, "Shoes")
        B.ell(Vector((ank.x, -0.010, 0.068 * sl)), (0.044 * lg, 0.06, 0.035 * sl), "Foot." + s, "Shoes")
        B.ell(Vector((toe.x * 0.95 + ank.x * 0.05, -0.052 * k, 0.040)), (0.049 * lg, 0.037 * sl, 0.128 * k),
              "Foot." + s, "Shoes", axis=(0, -1, 0), lateral=(1, 0, 0))
        B.ell(Vector((toe.x, toe.y + 0.035, 0.030)), (0.045 * lg, 0.027, 0.05), "Foot." + s, "Shoes",
              axis=(0, -1, 0), lateral=(1, 0, 0))
    return B.E


def head_elements(sp):
    k, f, hk = sp.k, sp.female, sp.hk
    hc = sp.hc
    H = Fam()

    def P(x, y, z):
        return hc + Vector((x, y, z)) * hk

    # neck: lower part follows the chest, upper part the neck bone
    nr = 0.047 if f else 0.054
    H.caps((0, 0.022, 1.39 * k), (0, 0.022, 1.47 * k), nr, "Chest", "Skin")
    H.caps((0, 0.022, 1.47 * k), P(0, 0.018, -0.088), nr * 0.95, "Neck", "Skin")
    # skull + face masses
    H.ell(P(0, 0, 0), (0.074 * hk, 0.093 * hk, 0.102 * hk), "Head", "Skin")                  # skull
    H.ell(P(0, -0.034, -0.058), (0.054 * hk, 0.052 * hk, 0.068 * hk), "Head", "Skin")          # face mass
    for sx in (1, -1):
        H.ell(P(sx * 0.024, -0.072, -0.052), (0.018 * hk, 0.014 * hk, 0.024 * hk), "Head", "Skin",
              s=2.0)                                                                           # maxilla / cheeks
    jaw = 0.043 if f else 0.047
    for sx in (1, -1):
        H.caps(P(sx * jaw, 0.006, -0.074), P(sx * 0.021, -0.066, -0.121), (0.0105 if f else 0.0135) * hk,
               "Head", "Skin", s=2.2 if f else 3)                                              # jaw line
        H.ell(P(sx * 0.045, -0.055, -0.032), (0.020 * hk, 0.018 * hk, 0.016 * hk), "Head", "Skin",
              s=2.0)                                                                           # cheekbone
        bw = 0.8 if f else 1.0
        H.ell(P(sx * 0.029, -0.083 - 0.002 * bw, 0.013), (0.025 * hk, (0.010 + 0.004 * bw) * hk,
              (0.008 + 0.002 * bw) * hk), "Head", "Skin", axis=(sx * 0.28, 0, 1), s=3.4)   # brow ridge (marked)
        H.ell(P(sx * 0.031, -0.088, -0.007), (0.0155 * hk, 0.012 * hk, 0.0100 * hk), "Head", "Skin",
              s=4.4, neg=True)                                                                 # eye socket
        H.ell(P(sx * 0.050, -0.072, 0.004), (0.010 * hk, 0.008 * hk, 0.012 * hk), "Head", "Skin",
              s=2.5)                                                                           # orbit rim
        # ear: shell + inner hollow + lobe
        H.ell(P(sx * 0.077, 0.010, -0.018), (0.009 * hk, 0.019 * hk, 0.031 * hk), "Head", "Skin",
              axis=(0, 0.25, 1), lateral=(1, 0, 0), s=5)
        H.ell(P(sx * 0.084, 0.006, -0.020), (0.006 * hk, 0.010 * hk, 0.017 * hk), "Head", "Skin",
              axis=(0, 0.25, 1), lateral=(1, 0, 0), s=5, neg=True)
        H.ell(P(sx * 0.073, 0.012, -0.046), (0.007 * hk, 0.010 * hk, 0.010 * hk), "Head", "Skin", s=5)
    H.ell(P(0, -0.086, 0.012), (0.014 * hk, 0.009 * hk, 0.011 * hk), "Head", "Skin", s=3)        # glabella
    # nose: bridge, tip, wings, nostrils
    nz = 0.9 if f else 1.0
    H.ell(P(0, -0.0935, -0.025), (0.0060 * hk, 0.0095 * hk, 0.027 * hk * nz), "Head", "Skin",
          axis=(0, -0.50, 1), s=6)
    H.ball(P(0, -0.1065 + (0.003 if f else 0), -0.049), 0.0080 * hk * nz, "Head", "Skin", s=6)
    for sx in (1, -1):
        H.ell(P(sx * 0.0105, -0.094, -0.054), (0.0060 * hk, 0.0070 * hk, 0.0060 * hk), "Head", "Skin", s=6)
        H.ell(P(sx * 0.0075, -0.099, -0.059), (0.003, 0.0035, 0.0022), "Head", "Skin", s=5, neg=True)
    # mouth: muzzle, lips, slit
    H.ell(P(0, -0.070, -0.088), (0.027 * hk, 0.0140 * hk, 0.024 * hk), "Head", "Skin", s=2.5)
    lip = 1.2 if f else 1.0
    H.ell(P(0, -0.0855, -0.0835), (0.019 * hk, 0.0065 * hk * lip, 0.0058 * hk * lip), "Head", "Skin", s=5)
    H.ell(P(0, -0.0840, -0.0952), (0.017 * hk, 0.0072 * hk * lip, 0.0064 * hk * lip), "Head", "Skin", s=5)
    H.caps(P(-0.020, -0.094, -0.0889), P(0.020, -0.094, -0.0889), 0.0016, "Head", "Skin", s=6, neg=True)
    # chin, with a defined underside: a negative volume under the jaw separates the chin from
    # the neck (the overhang casts the chin shadow seen from above / 3/4)
    H.ell(P(0, -0.077, -0.122), ((0.018 if f else 0.022) * hk, 0.017 * hk, 0.018 * hk), "Head", "Skin", s=3)
    H.ell(P(0, -0.034, -0.116), ((0.036 if f else 0.042) * hk, 0.042 * hk, 0.011 * hk), "Head", "Skin",
          s=3.0)                                                                           # jaw floor
    H.ell(P(0, -0.050, -0.152), (0.030 * hk, 0.022 * hk, 0.010 * hk), "Head", "Skin", s=1.6, neg=True)
    return H.E


def hand_elements(sp, s):
    hd = sp.hand[s]
    a, uh, th, pn, P = hd["a"], hd["uh"], hd["th"], hd["pn"], hd["P"]
    E = Fam()
    hb = "Hand." + s
    E.caps(P(-0.05, 0, 0), P(0.005, 0, 0), 0.027 * a, "LowerArm." + s, "Skin")              # wrist
    E.ell(P(0.012, 0, 0), (0.026 * a, 0.019 * a, 0.022 * a), hb, "Skin", axis=uh, lateral=th, s=3)
    E.ell(P(0.052, 0.002, 0.0), (0.039 * a, 0.0135 * a, 0.045 * a), hb, "Skin", axis=uh, lateral=th, s=3)
    E.ell(P(0.035, 0.024, 0.009), (0.016 * a, 0.012 * a, 0.026 * a), hb, "Skin",
          axis=uh + th * 0.6, lateral=pn, s=3)                                                   # thenar pad
    E.ell(P(0.078, 0.0, -0.004), (0.036 * a, 0.0075 * a, 0.010 * a), hb, "Skin",
          axis=th, lateral=uh, s=3)                                                              # knuckle ridge
    # four fingers: proximal phalanx on Fingers, middle + distal on Fingers2
    for base, mid, tip, rad in hd["fingers"]:
        E.caps(base, mid, rad, "Fingers." + s, "Skin", s=4)
        E.caps(mid, tip, rad * 0.88, "Fingers2." + s, "Skin", s=4)
    # thumb: separated from the index, pointing forward/down
    t0, t1, t2 = hd["thumb"]
    E.caps(t0, t1, 0.0115 * a, "Thumb." + s, "Skin", s=4)
    E.caps(t1, t2, 0.0098 * a, "Thumb2." + s, "Skin", s=4)
    return E.E


def hair_volume_elements(sp):
    """Extra hair masses (metaballs) on top of the scalp cap."""
    hk = sp.hk
    hc = sp.hc

    def P(x, y, z):
        return hc + Vector((x, y, z)) * hk

    E = Fam()
    if sp.hair == "bun":               # top bun (afro puff) on the pulled-back cap
        E.ell(P(0, 0.030, 0.112), (0.056, 0.054, 0.044), "Head", "Hair", s=2.2)
        E.ell(P(0, 0.034, 0.130), (0.044, 0.044, 0.028), "Head", "Hair", s=2.2)
        return E.E
    if sp.hair != "bob":
        return E.E                     # pulled-back / short hair: cap only (+ ponytail built separately)
    if sp.female:
        E.ell(P(0, 0.016, 0.010), (0.086, 0.102, 0.108), "Head", "Hair")                  # crown volume
        E.ell(P(0, 0.040, -0.085), (0.086, 0.074, 0.112), "Head", "Hair")                 # back
        E.ell(P(0, 0.052, -0.172), (0.078, 0.048, 0.078), "Head", "Hair")                 # to the shoulders
        for sx in (1, -1):
            E.ell(P(sx * 0.080, 0.012, -0.075), (0.022, 0.050, 0.100), "Head", "Hair")    # side curtains
            E.ell(P(sx * 0.074, 0.022, -0.168), (0.020, 0.044, 0.064), "Head", "Hair")
            E.ell(P(sx * 0.046, -0.072, 0.050), (0.040, 0.024, 0.024), "Head", "Hair",
                  axis=(sx * 0.6, 0, 1))                                                    # fringe sweep
        for i in range(7):                                                                  # tips
            a = math.radians(-70 + i * 140 / 6)
            E.ell(P(0.074 * math.sin(a), 0.045 + 0.028 * math.cos(a), -0.232 - 0.012 * (i % 2)),
                  (0.022, 0.020, 0.036), "Head", "Hair", s=3)
        # keep the face clear: a negative volume carves a smooth opening (closed surface)
        E.ell(P(0, -0.105, -0.062), (0.060, 0.065, 0.088), "Head", "Hair", neg=True)
    return E.E


# --------------------------------------------------------------------------- mesh utilities
def classify(obj, E, rule, boost=None):
    """Assign material indices from the dominant region of the field, refined by rule()."""
    me = obj.data
    C = np.array([p.center for p in me.polygons])
    F = fields(E, C)
    pos = np.clip(F, 0, None)
    regs = [e["reg"] for e in E]
    bones = [e["bone"] for e in E]
    reg_names = sorted(set(regs))
    reg_acc = np.stack([pos[:, [j for j, r in enumerate(regs) if r == rn]].sum(1) * (boost or {}).get(rn, 1.0)
                        for rn in reg_names], 1)
    bone_names = sorted(set(bones))
    bone_acc = np.stack([pos[:, [j for j, b in enumerate(bones) if b == bn]].sum(1) for bn in bone_names], 1)
    ri = reg_acc.argmax(1)
    bi = bone_acc.argmax(1)
    idx = []
    for n, p in enumerate(me.polygons):
        reg = rule(Vector(C[n]), reg_names[ri[n]], bone_names[bi[n]])
        idx.append(ORDER.index(reg))
    me.polygons.foreach_set("material_index", idx)


def decimate(obj, target, keep=None, triangulate=True):
    """Collapse-decimate to ~target triangles. keep(co) -> 0..1 preserves areas (1 = keep most)."""
    tris = nb.tri_count(obj)
    if tris > target:
        m = obj.modifiers.new("Decimate", "DECIMATE")
        m.decimate_type = "COLLAPSE"
        m.ratio = target / tris
        m.use_collapse_triangulate = True
        if keep is not None:
            vg = obj.vertex_groups.new(name="Keep")
            for v in obj.data.vertices:
                w = keep(v.co)
                if w > 0:
                    vg.add([v.index], min(1.0, w), "REPLACE")
            m.vertex_group = "Keep"
            m.vertex_group_factor = 1.0
            m.invert_vertex_group = True
        nb.apply_modifiers(obj)
        obj.vertex_groups.clear()
        if keep is not None and nb.tri_count(obj) > target * 1.06:
            return decimate(obj, target, None, triangulate)   # protected areas over budget: plain pass
    if triangulate:
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bm.to_mesh(obj.data)
        bm.free()
    return obj


def split_by_material(obj, mats):
    """Separate faces by material into new objects (seams become open boundaries)."""
    out = {}
    me = obj.data
    for mi in sorted({p.material_index for p in me.polygons}):
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index != mi], context="FACES")
        name = ORDER[mi]
        o = nb.bm_to_object(obj.name + "_" + name, bm, [mats[m] for m in ORDER])
        out[name] = o
    bpy.data.objects.remove(obj)
    return out


def set_material(obj, mats, name):
    obj.data.materials.clear()
    for m in ORDER:
        obj.data.materials.append(mats[m])
    obj.data.polygons.foreach_set("material_index", [ORDER.index(name)] * len(obj.data.polygons))
    return obj


def bvh_of(objs):
    bm = bmesh.new()
    for o in objs:
        me = o.data.copy()
        me.transform(o.matrix_world)
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    tree = BVHTree.FromBMesh(bm)
    bm.free()
    return tree


def band(name, bvh, center, axis, ref, n, r_cast, height, thick, mat, mats, embed=0.002, flare=0.0,
         shift=None, closed_inner=False):
    """Thick band hugging a surface: rays cast towards the axis in the plane (center, axis)."""
    axis = Vector(axis).normalized()
    ref = Vector(ref)
    ref = (ref - axis * ref.dot(axis)).normalized()
    side = axis.cross(ref)
    pts, dirs = [], []
    last = r_cast * 0.5
    for i in range(n):
        a = 2 * math.pi * i / n
        d = ref * math.cos(a) + side * math.sin(a)
        c = Vector(center) + (axis * shift(a) if shift else Vector())
        hit = bvh.ray_cast(c + d * r_cast, -d, r_cast)
        if hit[0] is not None:
            last = (hit[0] - c).dot(d)
        pts.append(c + d * last)
        dirs.append(d)
    verts, faces = [], []
    for p, d in zip(pts, dirs):
        verts += [p + d * (-embed) - axis * height / 2, p + d * (thick + flare) - axis * height / 2,
                  p + d * thick + axis * height / 2, p + d * (-embed) + axis * height / 2]
    for i in range(n):
        j = (i + 1) % n
        a, b = 4 * i, 4 * j
        faces += [(a, b, b + 1, a + 1), (a + 1, b + 1, b + 2, a + 2), (a + 2, b + 2, b + 3, a + 3)]
        if closed_inner:
            faces.append((a + 3, b + 3, b, a))
    obj = nb.mesh_object(name, verts, faces)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # recalc may flip an open band inwards: force normals to point away from the axis
    bm.faces.ensure_lookup_table()
    for fc in bm.faces:
        c = fc.calc_center_median() - Vector(center)
        radial = c - axis * c.dot(axis)
        if fc.normal.dot(radial) < -1e-6 and abs(fc.normal.dot(axis)) < 0.7:
            fc.normal_flip()
    bm.to_mesh(obj.data)
    bm.free()
    set_material(obj, mats, mat)
    return obj, pts, dirs


def slab_from_outline(name, outline, z0, z1, mats, mat):
    n = len(outline)
    verts = [(p.x, p.y, z0) for p in outline] + [(p.x, p.y, z1) for p in outline]
    faces = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
    faces += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    obj = nb.mesh_object(name, verts, faces)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    bm.to_mesh(obj.data)
    bm.free()
    set_material(obj, mats, mat)
    return obj


def add_hair_volume(vol, head_E, hc, hk, female, mats):
    """Remove the hair-volume faces buried in the head or hanging in front of the face."""
    bm = bmesh.new()
    bm.from_mesh(vol.data)
    co = np.array([v.co for v in bm.verts])
    inside = fields(head_E, co).sum(1) > THRESH + 0.05
    bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if all(inside[v.index] for v in f.verts)], context="FACES")
    bm.to_mesh(vol.data)
    bm.free()
    set_material(vol, mats, "Hair")


def band_from_points(name, pts, dirs, axes, height, thick, mat, mats, embed=0.002, flare=0.0, lift=0.0,
                     closed=True):
    """Thick band through surface points pts (outward dirs, per-point band axis)."""
    n = len(pts)
    verts, faces = [], []
    for p, d, ax in zip(pts, dirs, axes):
        b = p + ax * lift
        verts += [b + d * (-embed) - ax * height / 2, b + d * (thick + flare) - ax * height / 2,
                  b + d * thick + ax * height / 2, b + d * (-embed) + ax * height / 2]
    for i in range(n if closed else n - 1):
        j = (i + 1) % n
        a, b = 4 * i, 4 * j
        faces += [(a, b, b + 1, a + 1), (a + 1, b + 1, b + 2, a + 2), (a + 2, b + 2, b + 3, a + 3)]
    obj = nb.mesh_object(name, verts, faces)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    cen = sum(pts, Vector()) / n
    for fc in bm.faces:
        fc.normal_update()
        c = fc.calc_center_median() - cen
        i = min(range(n), key=lambda q: (pts[q] - fc.calc_center_median()).length)
        ax = axes[i]
        radial = c - ax * c.dot(ax)
        if abs(fc.normal.dot(ax)) < 0.7 and fc.normal.dot(radial) < 0:
            fc.normal_flip()
    bm.to_mesh(obj.data)
    bm.free()
    set_material(obj, mats, mat)
    return obj


def make_lips(bvh_head, hc, hk, female, mats):
    """Upper and lower lip: tapered tubes laid on the mouth surface (half embedded)."""
    out = []
    lipf = 1.2 if female else 1.0
    for name, zc, half, rv0, bend in (("LipUp", -0.0836, 0.0205, 0.0040, -0.0022),
                                      ("LipLow", -0.0948, 0.0185, 0.0048, 0.0020)):
        n = 9
        rings = []
        for i in range(n):
            u = -1 + 2 * i / (n - 1)
            x = u * half * hk
            z = hc.z + (zc + bend * u * u) * hk
            hit = bvh_head.ray_cast(Vector((x, -0.5, z)), Vector((0, 1, 0)))
            if hit[0] is None:
                continue
            p, nrm = hit[0], hit[1].normalized()
            up = Vector((0, 0, 1))
            up = (up - nrm * up.dot(nrm)).normalized()
            taper = math.sqrt(max(0.0, 1 - u * u))
            rv = rv0 * hk * lipf * taper + 0.0006
            rd = 0.0029 * hk * lipf * taper + 0.0005
            c = p + nrm * (rd * 0.2)
            rings.append([c + nrm * math.cos(a) * rd + up * math.sin(a) * rv
                          for a in (2 * math.pi * j / 8 for j in range(8))])
        verts = [v for r in rings for v in r]
        faces = []
        for i in range(len(rings) - 1):
            for j in range(8):
                j2 = (j + 1) % 8
                faces.append((i * 8 + j, (i + 1) * 8 + j, (i + 1) * 8 + j2, i * 8 + j2))
        o = nb.mesh_object(name, verts, faces)
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.faces.ensure_lookup_table()
        # make sure normals point away from the tube axis
        f0 = bm.faces[0]
        ring0 = rings[0]
        cen = sum(ring0, Vector()) / 8
        if f0.normal.dot(f0.calc_center_median() - (sum(rings[1], Vector()) / 8 + cen) / 2) < 0:
            for fc in bm.faces:
                fc.normal_flip()
        bm.to_mesh(o.data)
        bm.free()
        out.append(set_material(o, mats, "Lips"))
    return out


def neckline(bvh_head, body_E, k, n=20):
    """Points where the neck (head family) leaves the shirt (body family), all around."""
    pts, dirs = [], []
    zs = np.arange(1.36 * k, 1.58 * k, 0.002)
    for i in range(n):
        a = 2 * math.pi * i / n
        d = Vector((math.sin(a), -math.cos(a), 0))
        hits = []
        for z in zs:
            c = Vector((0, 0.022, z))
            h = bvh_head.ray_cast(c + d * 0.15, -d, 0.15)
            hits.append(h[0] + d * 0.0015 if h[0] is not None else c)
        inside = fields(body_E, np.array(hits)).sum(1) > THRESH
        top = max([j for j in range(len(zs)) if inside[j]] or [0])
        pts.append(hits[top] - d * 0.0015)
        dirs.append(d)
    return pts, dirs


# --------------------------------------------------------------------------- extra geometry (v3)
def fix_normals_out(obj, center_fn):
    """Recalculate normals, then flip faces whose normal points towards center_fn(face centre)."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for fc in bm.faces:
        c = fc.calc_center_median()
        if fc.normal.dot(c - center_fn(c)) < 0:
            fc.normal_flip()
    bm.to_mesh(obj.data)
    bm.free()


def tube(name, pts, radii, sides, mats, mat, cap_end=True, cap_start=False, up=None):
    """Tapered tube along a polyline (parallel-transported frames)."""
    n = len(pts)
    tang = []
    for i in range(n):
        a, b = pts[max(0, i - 1)], pts[min(n - 1, i + 1)]
        tang.append((b - a).normalized())
    ref = Vector(up) if up is not None else Vector((0, 0, 1))
    if abs(ref.dot(tang[0])) > 0.9:
        ref = Vector((1, 0, 0))
    nrm = (ref - tang[0] * ref.dot(tang[0])).normalized()
    verts, faces = [], []
    for i in range(n):
        if i:
            nrm = (nrm - tang[i] * nrm.dot(tang[i])).normalized()
        bi = tang[i].cross(nrm)
        for j in range(sides):
            a = 2 * math.pi * j / sides
            verts.append(pts[i] + (nrm * math.cos(a) + bi * math.sin(a)) * radii[i])
    for i in range(n - 1):
        for j in range(sides):
            j2 = (j + 1) % sides
            faces.append((i * sides + j, i * sides + j2, (i + 1) * sides + j2, (i + 1) * sides + j))
    if cap_end:
        verts.append(pts[-1] + tang[-1] * radii[-1] * 0.8)
        e = len(verts) - 1
        faces += [((n - 1) * sides + j, (n - 1) * sides + (j + 1) % sides, e) for j in range(sides)]
    if cap_start:
        verts.append(pts[0] - tang[0] * radii[0] * 0.8)
        e = len(verts) - 1
        faces += [((j + 1) % sides, j, e) for j in range(sides)]
    obj = nb.mesh_object(name, verts, faces)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.faces.ensure_lookup_table()
    f0 = bm.faces[0]
    if f0.normal.dot(f0.calc_center_median() - (pts[0] + pts[1]) / 2) < 0:
        for fc in bm.faces:
            fc.normal_flip()
    bm.to_mesh(obj.data)
    bm.free()
    return set_material(obj, mats, mat)


def lash_line(eye_c, r, sx, hk, mats):
    """Dark upper lash / eyelid line around the top of the eye (reads at distance)."""
    pts, rad = [], []
    n = 7
    for i in range(n):
        a = math.radians(18 + 144 * i / (n - 1))
        x = -math.cos(a) * sx
        pts.append(eye_c + Vector((x * r * 1.0, -r * 0.62 - 0.0004, math.sin(a) * r * 0.80 + 0.0007)))
        rad.append(0.0011 * hk * (0.55 + 0.45 * math.sin(math.pi * i / (n - 1))))
    return tube("Lash", pts, rad, 4, mats, "Eyes", cap_end=True, cap_start=True)


def strand_ridge(sp, d):
    """Hair lock pattern in [-1, 1] at head-local point d (mèches: ridges along the strand flow)."""
    if sp.pulled:                      # pulled back: strands converge to the ponytail / bun tie
        T = Vector((0, 0.088, -0.005)) if sp.hair == "ponytail" else Vector((0, 0.035, 0.098))
        F = Vector((0, -0.095, 0.030))
        A = (T - F).normalized()
        U = Vector((0, 0, 1))
        U = (U - A * U.dot(A)).normalized()
        q = d - T
        q = q - A * q.dot(A)
        phi = math.atan2(q.x, q.dot(U))
        return math.cos(22 * phi)
    if sp.female:                      # bob: locks fall from the crown
        q = d - Vector((0, 0.01, 0.08))
        phi = math.atan2(q.x, -q.y)
        return math.cos(26 * phi + 9 * q.length)
    q = d - Vector((0, 0.045, 0.088))  # short cut: combed out from the crown, slight swirl
    phi = math.atan2(q.x, -q.y)
    return math.cos(17 * phi + 14 * q.length)


def cap_frame(sp):
    """Rim plane of the baseball cap (stocky variant): point, normal (up-ish), front point."""
    hc, hk = sp.hc, sp.hk
    front = hc + Vector((0, -0.080, 0.036)) * hk
    back = hc + Vector((0, 0.098, -0.028)) * hk
    n = (back - front).cross(Vector((1, 0, 0))).normalized()
    if n.z < 0:
        n = -n
    return front, back, n


def make_cap(sp, bvh, mats):
    """Six-panel cap: crown hugging head + hair, button, curved visor. Material Hat."""
    hc, hk = sp.hc, sp.hk
    front, back, n = cap_frame(sp)
    C = (front + back) / 2 + n * 0.0           # centre on the rim plane
    X = Vector((1, 0, 0))
    Yp = n.cross(X).normalized()               # in-plane, points backwards
    if Yp.y < 0:
        Yp = -Yp
    NA, NE = 24, 6
    rings = []
    for e in range(NE):
        el = (e / NE) * 0.5 * math.pi * 0.96
        ring = []
        for i in range(NA):
            az = 2 * math.pi * i / NA
            d = (X * math.sin(az) - Yp * math.cos(az)) * math.cos(el) + n * math.sin(el)
            o = C + n * 0.004
            hit = bvh.ray_cast(o + d * 0.3, -d, 0.3)
            p = hit[0] if hit[0] is not None else o + d * 0.1
            puff = 0.0045 + 0.005 * math.sin(math.pi * e / NE) + 0.002 * (e / NE)
            ring.append(p + d * puff)
        rings.append(ring)
    top = C + n * 0.004
    hit = bvh.ray_cast(top + n * 0.3, -n, 0.3)
    top = (hit[0] if hit[0] is not None else top + n * 0.1) + n * 0.011
    verts = [v for r in rings for v in r] + [top]
    faces = []
    for e in range(NE - 1):
        for i in range(NA):
            i2 = (i + 1) % NA
            faces.append((e * NA + i, e * NA + i2, (e + 1) * NA + i2, (e + 1) * NA + i))
    ti = len(verts) - 1
    faces += [((NE - 1) * NA + i, (NE - 1) * NA + (i + 1) % NA, ti) for i in range(NA)]
    # inner lip: the rim turns in so the edge has thickness
    base = len(verts)
    for i in range(NA):
        p = rings[0][i]
        verts.append(p - (p - C).normalized() * 0.005 + n * 0.006)
    for i in range(NA):
        i2 = (i + 1) % NA
        faces.append((base + i, base + i2, i2, i))
    crown = nb.mesh_object("CapCrown", verts, faces)
    fix_normals_out(crown, lambda c: C + n * 0.02)
    set_material(crown, mats, "Hat")
    out = [crown]
    out.append(set_material(nb.uv_sphere("CapButton", 0.0065 * hk, top + n * 0.001, 8, 4, scale=(1, 1, 0.5)),
                            mats, "Hat"))
    # visor: from the front rim, forward and slightly down, curved sideways
    nv, nl = 11, 4
    fwd = -Yp
    top_s, bot_s = [], []
    for i in range(nv):
        u = -1 + 2 * i / (nv - 1)
        az = u * math.radians(72)
        d = X * math.sin(az) - Yp * math.cos(az)
        root = C + d * 0.0
        hit = bvh.ray_cast(C + n * 0.004 + d * 0.3, -d, 0.3)
        root = (hit[0] if hit[0] is not None else C + d * 0.09) + d * 0.004
        L = 0.072 * hk * math.sqrt(max(0.0, 1 - (u * 0.92) ** 2)) + 0.006
        rowt, rowb = [], []
        for j in range(nl):
            s = j / (nl - 1)
            p = root + (d * 0.35 + fwd * 0.65).normalized() * (L * s) - n * (0.010 * s * s + 0.004 * s)
            p = p - n * (0.010 * (u * u) * s)                       # sides curve down
            rowt.append(p + n * 0.0025)
            rowb.append(p - n * 0.0025)
        top_s.append(rowt)
        bot_s.append(rowb)
    verts, faces = [], []
    for i in range(nv):
        verts += top_s[i] + bot_s[i]
    W = 2 * nl
    for i in range(nv - 1):
        a, b = i * W, (i + 1) * W
        for j in range(nl - 1):
            faces.append((a + j, b + j, b + j + 1, a + j + 1))                       # top
            faces.append((a + nl + j + 1, b + nl + j + 1, b + nl + j, a + nl + j))   # bottom
        faces.append((a + nl - 1, b + nl - 1, b + W - 1, a + W - 1))                 # front edge
        faces.append((a + nl, b + nl, b, a))                                         # root edge
    faces.append(tuple(list(range(nl)) + list(range(W - 1, nl - 1, -1))))           # side ends
    e = (nv - 1) * W
    faces.append(tuple([e + q for q in list(range(nl)) + list(range(W - 1, nl - 1, -1))][::-1]))
    visor = nb.mesh_object("CapVisor", verts, faces)
    bm = bmesh.new()
    bm.from_mesh(visor.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(visor.data)
    bm.free()
    out.append(set_material(visor, mats, "Hat"))
    return out


def trim_under_cap(obj, sp, margin=0.006):
    """Remove the hair faces hidden inside the cap."""
    front, back, n = cap_frame(sp)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if (f.calc_center_median() - front).dot(n) > margin],
                     context="FACES")
    bm.to_mesh(obj.data)
    bm.free()


def make_pocket(sp, bvh, mats):
    """Kangaroo pocket on the hoodie front: thin patch laid on the belly by ray casting."""
    k = sp.k
    nx, nz = 9, 5
    z0, z1 = sp.waist + 0.035 * k, sp.waist + 0.175 * k
    grid = []
    for j in range(nz):
        t = j / (nz - 1)
        z = z0 + (z1 - z0) * t
        half = 0.125 - 0.040 * t                       # trapezoid: slanted hand openings
        row = []
        for i in range(nx):
            x = -half + 2 * half * i / (nx - 1)
            hit = bvh.ray_cast(Vector((x, -0.5, z)), Vector((0, 1, 0)))
            p, nn = (hit[0], hit[1]) if hit[0] is not None else (Vector((x, -0.12, z)), Vector((0, -1, 0)))
            row.append((p, nn))
        grid.append(row)
    verts, faces = [], []
    for row in grid:
        for p, nn in row:
            verts.append(p + nn * 0.0045)
    off = len(verts)
    for row in grid:
        for p, nn in row:
            verts.append(p - nn * 0.002)
    for j in range(nz - 1):
        for i in range(nx - 1):
            a = j * nx + i
            faces.append((a, a + 1, a + nx + 1, a + nx))
    ring = [i for i in range(nx)] + [j * nx + nx - 1 for j in range(1, nz)] + \
        [(nz - 1) * nx + i for i in range(nx - 2, -1, -1)] + [j * nx for j in range(nz - 2, 0, -1)]
    for q in range(len(ring)):
        a, b = ring[q], ring[(q + 1) % len(ring)]
        faces.append((b, a, a + off, b + off))
    obj = nb.mesh_object("Pocket", verts, faces)
    fix_normals_out(obj, lambda c: Vector((0, 0.05, c.z)))
    return set_material(obj, mats, "Shirt")


def make_skirt(sp, bvh_body, mats):
    """Skirt (material Pants) from the waist to above the knee: hugs the hips, flares, soft folds.
    Outer + inner shell joined by a hem rim."""
    k = sp.k
    zw, zh = sp.waist + 0.012, sp.skirt_hem
    NA, NR = 24, 7
    outer = []
    for r in range(NR):
        s = r / (NR - 1)
        z = zw + (zh - zw) * s
        ring = []
        for i in range(NA):
            az = 2 * math.pi * i / NA
            d = Vector((math.sin(az), -math.cos(az), 0))
            c = Vector((0, 0.010, z))
            hit = bvh_body.ray_cast(c + d * 0.26, -d, 0.26)      # torso only (arms hang further out)
            rb = (hit[0] - c).length if (hit[0] is not None and s < 0.6) else 0.0
            rb = min(rb, 0.21)
            flare = Vector((0.205 * math.sin(az), -0.170 * math.cos(az) - 0.012, 0)).length
            rr = max(rb + 0.006 + 0.012 * s, (rb + 0.006) * (1 - s) + flare * s if rb else flare)
            rr *= 1.0 + (0.045 * s ** 1.4) * math.sin(9 * az + 0.6)          # folds
            ring.append(c + d * rr)
        outer.append(ring)
    verts = [v for r in outer for v in r]
    off = len(verts)
    c0 = Vector((0, 0.010, 0))
    for r in outer:
        for v in r:
            d = Vector((v.x - c0.x, v.y - c0.y, 0)).normalized()
            verts.append(v - d * 0.004)
    faces = []
    for r in range(NR - 1):
        for i in range(NA):
            i2 = (i + 1) % NA
            a, b = r * NA + i, r * NA + i2
            faces.append((a, b, b + NA, a + NA))
            faces.append((off + a + NA, off + b + NA, off + b, off + a))
    last = (NR - 1) * NA
    for i in range(NA):
        i2 = (i + 1) % NA
        faces.append((last + i, last + i2, off + last + i2, off + last + i))
    obj = nb.mesh_object("Skirt", verts, faces)
    return set_material(obj, mats, "Pants")


def make_ponytail(sp, bvh_avoid, mats):
    """Ponytail of a few twisted tapered locks (geometry), tie at the back of the head."""
    hc, hk = sp.hc, sp.hk

    def P(x, y, z):
        return hc + Vector((x, y, z)) * hk
    ctrl = [P(0, 0.084, -0.004), P(0, 0.118, -0.030), P(0, 0.136, -0.085), P(0, 0.136, -0.150),
            P(0, 0.124, -0.208), P(0, 0.112, -0.250)]
    # smooth centre curve (Catmull-Rom), pushed away from the body when needed
    cen = []
    for i in range(len(ctrl) - 1):
        p0, p1 = ctrl[max(0, i - 1)], ctrl[i]
        p2, p3 = ctrl[i + 1], ctrl[min(len(ctrl) - 1, i + 2)]
        for t in (0.0, 0.5):
            t2, t3 = t * t, t * t * t
            cen.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 +
                              (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    cen.append(ctrl[-1])
    for i, c in enumerate(cen):
        hit = bvh_avoid.find_nearest(c)
        if hit[0] is not None and i > 1:
            d = c - hit[0]
            if d.dot(hit[1]) < 0.030:
                cen[i] = hit[0] + hit[1] * 0.030
    n = len(cen)
    out = []
    locks = 6
    for L in range(locks):
        a0 = 2 * math.pi * L / locks
        pts, rad = [], []
        for i, c in enumerate(cen):
            s = i / (n - 1)
            tang = (cen[min(n - 1, i + 1)] - cen[max(0, i - 1)]).normalized()
            side = tang.cross(Vector((1, 0, 0))).normalized()
            xax = Vector((1, 0, 0))
            bundle = (0.010 + 0.014 * math.sin(math.pi * min(1.0, s * 1.3))) * hk * (1 - 0.6 * s ** 2)
            a = a0 + 1.1 * s
            spread = 1.0 + 0.25 * s * (L % 2)
            pts.append(c + (xax * math.cos(a) + side * math.sin(a)) * bundle * spread)
            rad.append(((0.0105 if L % 2 else 0.0090) * (1 - 0.82 * s ** 1.3) + 0.0012) * hk)
        out.append(tube("Lock", pts, rad, 5, mats, "Hair", cap_end=True))
    # tie (scrunchie, material Shirt so it matches the top)
    t0, t1 = cen[0], cen[1]
    ax = (t1 - t0).normalized()
    u = ax.cross(Vector((1, 0, 0))).normalized()
    v = ax.cross(u)
    c = t0 + ax * 0.008
    ring = [c + (u * math.cos(2 * math.pi * i / 10) + v * math.sin(2 * math.pi * i / 10)) * 0.017 * hk
            for i in range(11)]
    out.append(tube("Tie", ring, [0.0055 * hk] * 11, 5, mats, "Shirt", cap_end=False))
    return out


def make_drawstrings(sp, npts, mats):
    out = []
    k = sp.k
    for sx in (1, -1):
        p0 = min(npts, key=lambda p: (p.x - sx * 0.032) ** 2 + (p.y + 0.2) ** 2 * 0.05)
        p0 = p0 + Vector((0, -0.010, -0.008))
        pts = [p0 + Vector((sx * 0.004 * t, -0.012 * t, -0.15 * k * t)) for t in (0, 0.25, 0.5, 0.75, 1.0)]
        out.append(tube("String", pts, [0.0032] * 4 + [0.0045], 5, mats, "Shirt", cap_end=True))
    return out


# --------------------------------------------------------------------------- v4 outfit geometry
def close_normals(obj):
    """Consistent outward normals for a closed (or nearly closed) small mesh."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()


def ribbon(name, pts, nrms, width, thick, mats, mat, closed=False, embed=0.0015, widths=None, bottom=True):
    """Flat ribbon lying on a surface along pts (surface normals nrms): piping, stripes, digits,
    plackets. Box section (width x thick), capped when open, so normals can be recomputed."""
    n = len(pts)
    verts, faces = [], []
    for i in range(n):
        if closed:
            t = pts[(i + 1) % n] - pts[i - 1]
        else:
            t = pts[min(n - 1, i + 1)] - pts[max(0, i - 1)]
        nn = nrms[i].normalized()
        a = t.cross(nn).normalized()
        w = (widths[i] if widths else width) / 2
        p = pts[i]
        verts += [p + a * w + nn * thick, p - a * w + nn * thick, p - a * w - nn * embed, p + a * w - nn * embed]
    for i in range(n if closed else n - 1):
        j = (i + 1) % n
        A, B = 4 * i, 4 * j
        for q in range(4 if bottom else 3):
            q2 = (q + 1) % 4
            faces.append((A + q, A + q2, B + q2, B + q))
    if not closed:
        faces.append((3, 2, 1, 0))
        e = 4 * (n - 1)
        faces.append((e, e + 1, e + 2, e + 3))
    o = nb.mesh_object(name, verts, faces)
    close_normals(o)
    # recalc on a thin ribbon can still pick the inward side: top face must follow the normal
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.faces.ensure_lookup_table()
    f0 = bm.faces[0]
    if f0.normal.dot(nrms[0]) < 0:
        for fc in bm.faces:
            fc.normal_flip()
    bm.to_mesh(o.data)
    bm.free()
    return set_material(o, mats, mat)


def project(bvh, p, d=None, reach=0.3, off=0.0):
    """Surface point + normal: ray from p - d*reach towards d (d None: nearest point)."""
    if d is None:
        hit = bvh.find_nearest(p)
        if hit[0] is None:
            return None, None
        return hit[0] + hit[1] * off, hit[1]
    d = Vector(d).normalized()
    hit = bvh.ray_cast(p - d * reach, d, reach * 2)
    if hit[0] is None:
        return None, None
    return hit[0] + hit[1] * off, hit[1]


def boundary_loops(obj, zmin=-9.0):
    """Ordered boundary loops (vertex coordinates) of an open mesh piece."""
    me = obj.data
    adj = {}
    bm = bmesh.new()
    bm.from_mesh(me)
    for e in bm.edges:
        if e.is_boundary:
            a, b = e.verts[0].index, e.verts[1].index
            adj.setdefault(a, []).append(b)
            adj.setdefault(b, []).append(a)
    co = {v.index: v.co.copy() for v in bm.verts}
    bm.free()
    seen, loops = set(), []
    for start in adj:
        if start in seen:
            continue
        loop, prev, cur = [start], None, start
        seen.add(start)
        while True:
            nxt = [q for q in adj[cur] if q != prev and q not in seen]
            if not nxt:
                break
            prev, cur = cur, nxt[0]
            seen.add(cur)
            loop.append(cur)
        if len(loop) > 12:
            pts = [co[i] for i in loop]
            if sum(p.z for p in pts) / len(pts) > zmin:
                loops.append(pts)
    return loops


def resample_loop(pts, step):
    n = len(pts)
    L = [0.0]
    for i in range(n):
        L.append(L[-1] + (pts[(i + 1) % n] - pts[i]).length)
    total = L[-1]
    m = max(12, int(total / step))
    out, j = [], 0
    for q in range(m):
        s = total * q / m
        while L[j + 1] < s:
            j += 1
        t = (s - L[j]) / max(1e-9, L[j + 1] - L[j])
        out.append(pts[j].lerp(pts[(j + 1) % n], t))
    return out


def snap_boundary(obj, curves, reach=0.03):
    """Move the boundary vertices of a piece onto the nearest smooth seam curve (closed polylines).
    Both pieces of a seam share the same boundary positions, so they stay watertight."""
    if not curves:
        return
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    A = np.concatenate(curves)
    B = np.concatenate([np.roll(c, -1, 0) for c in curves])
    AB = B - A
    L2 = np.maximum((AB ** 2).sum(1), 1e-12)
    for v in bm.verts:
        if not v.is_boundary:
            continue
        p = np.array(v.co)
        t = np.clip(((p - A) * AB).sum(1) / L2, 0, 1)
        Q = A + AB * t[:, None]
        d = ((Q - p) ** 2).sum(1)
        i = int(d.argmin())
        if d[i] < reach * reach:
            v.co = Vector(Q[i])
    bm.to_mesh(me)
    bm.free()
    me.update()


def seam_piping(name, piece, bvh, mats, mat, zmin, width=0.013, thick=0.0032):
    """Hide the stair-stepped material seams of a garment piece (swimsuit / tank top cut-outs):
    each boundary loop is resampled, smoothed, projected back on the body and turned into a
    piping ribbon that straddles the seam."""
    out = []
    for li, loop in enumerate(boundary_loops(piece, zmin)):
        pts = resample_loop(loop, 0.026)
        for _ in range(1):          # the seam is already snapped onto a smooth curve: barely smooth
            pts = [pts[i] * 0.5 + (pts[i - 1] + pts[(i + 1) % len(pts)]) * 0.25 for i in range(len(pts))]
        P, N = [], []
        for p in pts:
            q, nn = project(bvh, p)
            if q is not None:
                P.append(q)
                N.append(nn)
        if len(P) > 8:
            o = ribbon("%s%d" % (name, li), P, N, width, thick, mats, mat, closed=True, embed=0.003, bottom=False)
            o["uv"] = "box:" + mat if mat in TILE else ""
            out.append(o)
    return out


def torso_bare(sp, c):
    """True where a swimsuit / tank top leaves the skin bare (neckline, armholes, shoulders)."""
    x, z = abs(c.x), c.z / sp.k
    if sp.top == "swim":
        z_ap, xi, xo, nf, nbk = 1.330, 0.050, 0.094, 1.378, 1.405
    else:   # tank
        z_ap, xi, xo, nf, nbk = 1.318, 0.066, 0.122, 1.392, 1.425
    if z < z_ap:
        return False
    s = min(1.0, (z - z_ap) / 0.080)
    xo_z = xo + (0.25 - xo) * (1 - s) ** 2.2                  # armhole curve up to the strap
    if x > xo_z:
        return True
    if x < xi:
        tb = min(1.0, max(0.0, (c.y + 0.02) / 0.09))
        nz = nf + (nbk - nf) * tb * tb * (3 - 2 * tb)       # front scoop rising smoothly to the back
        return z > nz + 0.045 * (x / xi) ** 2.5                # scooped neckline rising to the straps
    return False


def hat_frame(sp):
    """Rim plane of the hat: front point, back point, normal (up-ish)."""
    if sp.hat != "bucket":
        return cap_frame(sp)
    hc, hk = sp.hc, sp.hk
    front = hc + Vector((0, -0.084, 0.034)) * hk
    back = hc + Vector((0, 0.100, -0.008)) * hk
    n = (back - front).cross(Vector((1, 0, 0))).normalized()
    if n.z < 0:
        n = -n
    return front, back, n


def make_bucket(sp, bvh, mats):
    """Bucket hat (bob): soft crown clearing head + hair, flat top, sloping brim. Material Hat."""
    hk = sp.hk
    front, back, n = hat_frame(sp)
    C = (front + back) / 2
    X = Vector((1, 0, 0))
    Yp = n.cross(X).normalized()
    if Yp.y < 0:
        Yp = -Yp
    NA, NE = 24, 5
    rim = []
    for i in range(NA):
        az = 2 * math.pi * i / NA
        d = X * math.sin(az) - Yp * math.cos(az)
        hit = bvh.ray_cast(C + d * 0.3, -d, 0.3)
        r = ((hit[0] - C).length if hit[0] is not None else 0.09) + 0.007
        rim.append((d, r))
    H = 0.0
    hit = bvh.ray_cast(C + n * 0.3, -n, 0.3)
    if hit[0] is not None:
        H = (hit[0] - C).dot(n)
    H = max(H + 0.008, 0.080 * hk)
    rings = []
    for e in range(NE):
        h = H * e / (NE - 1) * 0.94
        ring = []
        for d, r in rim:
            taper = 1.0 - 0.22 * (e / (NE - 1)) ** 1.4
            p = C + n * h + d * r * taper
            hit = bvh.ray_cast(C + n * h + d * 0.3, -d, 0.3)
            if hit[0] is not None:
                rr = (hit[0] - (C + n * h)).length + 0.006
                if rr > r * taper:
                    p = C + n * h + d * rr
            ring.append(p)
        rings.append(ring)
    top = C + n * H
    verts = [v for r in rings for v in r]
    # flat-ish top: one extra inner ring then the centre
    last = rings[-1]
    verts += [top + (p - top) * 0.55 + n * 0.004 for p in last] + [top + n * 0.006]
    faces = []
    for e in range(NE - 1):
        for i in range(NA):
            i2 = (i + 1) % NA
            faces.append((e * NA + i, e * NA + i2, (e + 1) * NA + i2, (e + 1) * NA + i))
    b0 = NE * NA
    for i in range(NA):
        i2 = (i + 1) % NA
        faces.append(((NE - 1) * NA + i, (NE - 1) * NA + i2, b0 + i2, b0 + i))
    ci = len(verts) - 1
    faces += [(b0 + i, b0 + (i + 1) % NA, ci) for i in range(NA)]
    crown = nb.mesh_object("HatCrown", verts, faces)
    fix_normals_out(crown, lambda c: C + n * (H * 0.4))
    # brim: two shells (top / bottom) joined at the rolled edge and at the crown
    NB = 3
    verts, faces = [], []
    for i, (d, r) in enumerate(rim):
        p0 = rings[0][i]
        for j in range(NB):
            s = j / (NB - 1)
            out = d * (0.050 * hk * s) - n * (0.024 * s ** 1.2)
            verts.append(p0 + out + n * 0.0022)
        for j in range(NB):
            s = j / (NB - 1)
            out = d * (0.050 * hk * s) - n * (0.024 * s ** 1.2)
            verts.append(p0 + out - n * 0.0022)
    W = 2 * NB
    for i in range(NA):
        a, b = i * W, ((i + 1) % NA) * W
        for j in range(NB - 1):
            faces.append((a + j, b + j, b + j + 1, a + j + 1))
            faces.append((a + NB + j + 1, b + NB + j + 1, b + NB + j, a + NB + j))
        faces.append((a + NB - 1, b + NB - 1, b + W - 1, a + W - 1))
        faces.append((a + NB, b + NB, b, a))
    brim = nb.mesh_object("HatBrim", verts, faces)
    close_normals(brim)
    return [set_material(crown, mats, "Hat"), set_material(brim, mats, "Hat")]


def trim_under_hat(obj, sp, margin=0.006):
    front, back, n = hat_frame(sp)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if (f.calc_center_median() - front).dot(n) > margin],
                     context="FACES")
    bm.to_mesh(obj.data)
    bm.free()


def make_sunglasses(sp, bvh_hh, mats):
    """Sunglasses pushed up on the head: two wrap lenses (Lens), frame + temples (Gear)."""
    hc, hk = sp.hc, sp.hk
    w = Vector((0, -0.50, 0.866))
    hit = bvh_hh.ray_cast(hc + w * 0.3, -w, 0.3)
    B = (hit[0] if hit[0] is not None else hc + w * 0.11) + w * 0.010
    X = Vector((1, 0, 0))
    v = w.cross(X).normalized()                     # lens "up" = towards the back of the head
    out = []
    rims = []
    for sx in (1, -1):
        c = B + X * (sx * 0.034 * hk)
        ring = []
        for i in range(14):
            a = 2 * math.pi * i / 14
            lx, ly = math.cos(a) * 0.027 * hk, math.sin(a) * 0.019 * hk
            ly *= 1.0 + 0.18 * (lx * sx > 0) * (abs(lx) / 0.027)        # wider at the outer side
            q = c + X * lx + v * (ly - 0.002 * hk)
            h = bvh_hh.ray_cast(q + w * 0.06, -w, 0.12)
            if h[0] is not None:
                gap = (q - h[0]).dot(w) - 0.009
                if gap > 0:
                    q = q - w * gap * 0.75
            ring.append(q)
        rims.append(ring)
        cen = sum(ring, Vector()) / len(ring) + w * 0.0015
        verts = ring + [p - w * 0.0018 for p in ring] + [cen, cen - w * 0.0034]
        m = len(ring)
        faces = [(i, (i + 1) % m, 2 * m) for i in range(m)]
        faces += [(m + (i + 1) % m, m + i, 2 * m + 1) for i in range(m)]
        faces += [((i + 1) % m, i, m + i, m + (i + 1) % m) for i in range(m)]
        lens = nb.mesh_object("Lens", verts, faces)
        close_normals(lens)
        out.append(set_material(lens, mats, "Lens"))
        out.append(tube("Frame", ring[::2] + [ring[0]], [0.0017] * (m // 2 + 1), 4, mats, "Gear", cap_end=False))
        # temple: from the outer hinge back along the side of the head, above the ear
        hinge = ring[0]
        tp = [hinge]
        for y, z in ((0.000, 0.046), (0.032, 0.030), (0.064, 0.014), (0.090, 0.000)):
            o = hc + Vector((sx * 0.20, y, z)) * hk
            h = bvh_hh.ray_cast(o, Vector((-sx, 0, 0)), 0.3)
            if h[0] is not None:
                tp.append(h[0] + Vector((sx * 0.004, 0, 0)))
        out.append(tube("Temple", tp, [0.0018] * len(tp), 4, mats, "Gear", cap_end=True, cap_start=True))
    br = [rims[0][7], (rims[0][7] + rims[1][7]) / 2 + w * 0.002, rims[1][7]]
    out.append(tube("Bridge", br, [0.0018] * 3, 4, mats, "Gear", cap_end=False))
    return out


def neck_ring(npts, ndirs, out, drop):
    return [p + d * out - Vector((0, 0, drop)) for p, d in zip(npts, ndirs)]


def make_whistle(sp, bvh, npts, ndirs, mats):
    """Lifeguard whistle on a lanyard: cord around the base of the neck, V down to the whistle."""
    k = sp.k
    ring = neck_ring(npts, ndirs, 0.005, 0.006)
    zc = (1.355 if sp.female else 1.325) * k
    W, Wn = project(bvh, Vector((0, -0.3, zc)), (0, 1, 0), 0.3, 0.0)
    if W is None:
        W, Wn = Vector((0, -0.12, zc)), Vector((0, -1, 0))
    # ring points sorted around the neck, starting at the front (index 0 = front centre)
    n = len(ring)
    iL, iR = 2, n - 2
    pts = []
    for t in (0.2, 0.4, 0.6, 0.8):
        a = ring[iR].lerp(W, t)
        q, nn = project(bvh, a + Vector((0, -0.25, 0)), (0, 1, 0), 0.3)
        pts.append((q + nn * 0.004) if q is not None else a)
    cord = [ring[i] for i in range(iL, iR + 1)] + pts[::1] + [W + Wn * 0.006]
    pts2 = []
    for t in (0.8, 0.6, 0.4, 0.2):
        a = ring[iL].lerp(W, t)
        q, nn = project(bvh, a + Vector((0, -0.25, 0)), (0, 1, 0), 0.3)
        pts2.append((q + nn * 0.004) if q is not None else a)
    cord = cord + pts2 + [ring[iL]]
    out = [tube("Lanyard", cord, [0.0026] * len(cord), 3, mats, "Gear", cap_end=False)]
    # whistle body hanging along the chest
    down = Vector((0, 0, -1))
    ax = (down - Wn * down.dot(Wn)).normalized()
    c0 = W + Wn * 0.011
    body = tube("Whistle", [c0 - ax * 0.002, c0 + ax * 0.030], [0.0095, 0.0095], 8, mats, "Metal",
                cap_end=True, cap_start=True)
    mouth = tube("WhistleTip", [c0 + ax * 0.028, c0 + ax * 0.046], [0.0055, 0.0045], 6, mats, "Metal",
                 cap_end=True, cap_start=True)
    loop = tube("WhistleRing", [c0 - ax * 0.002, W + Wn * 0.006], [0.0020, 0.0020], 4, mats, "Metal")
    return out + [body, mouth, loop]


def make_chain(sp, bvh, npts, ndirs, mats):
    """Chunky gold chain (bead-modulated tube) hanging on the chest, with a round pendant."""
    k = sp.k
    n = len(npts)
    ring = neck_ring(npts, ndirs, 0.007, 0.012)
    zb = sum(p.z for p in ring) / n
    depth = (0.105 if sp.female else 0.135) * k
    pts, rad = [], []
    m = 28
    for q in range(m):
        a = 2 * math.pi * q / m                     # 0 = front centre
        f = q * n / m
        i0 = int(f) % n
        p = ring[i0].lerp(ring[(i0 + 1) % n], f - int(f))
        drop = depth * ((1 + math.cos(a)) / 2) ** 1.6
        target = Vector((p.x, p.y, p.z - drop))
        d = Vector((p.x, p.y - 0.022, 0)).normalized()
        if drop > 0.004:          # short rays from just outside: never catch the shoulders
            qh, nn = project(bvh, target + d * 0.035, -d, 0.05)
            if qh is not None:
                target = qh + nn * 0.0055
        pts.append(target)
        rad.append(0.0046 if q % 2 else 0.0030)
    pts.append(pts[0])
    rad.append(rad[0])
    out = [tube("Chain", pts, rad, 4, mats, "Metal", cap_end=False)]
    p0 = pts[0]
    qh, nn = project(bvh, p0 + Vector((0, -0.25, -0.018)), (0, 1, 0), 0.3)
    if qh is not None:
        c = qh + nn * 0.006
        out.append(tube("Pendant", [c - nn * 0.0015, c + nn * 0.0025], [0.0125, 0.0125], 10, mats, "Metal",
                        cap_end=True, cap_start=True))
    return out


def make_earrings(sp, mats):
    hc, hk = sp.hc, sp.hk
    out = []
    for sx in (1, -1):
        lobe = hc + Vector((sx * 0.076, 0.012, -0.050)) * hk
        c = lobe + Vector((sx * 0.002, 0, -0.012))
        ring = [c + Vector((0, math.cos(a) * 0.013, math.sin(a) * 0.013)) for a in
                (2 * math.pi * i / 10 for i in range(11))]
        out.append(tube("Hoop", ring, [0.0017] * 11, 3, mats, "Metal", cap_end=False))
    return out


def patch(name, bvh, x0, x1, z0, z1, mats, mat, front=True, lift=0.0042, nx=5, nz=4):
    """Thin patch laid on the body by ray casting (pockets)."""
    sgn = -1 if front else 1
    grid = []
    for j in range(nz):
        z = z0 + (z1 - z0) * j / (nz - 1)
        row = []
        for i in range(nx):
            x = x0 + (x1 - x0) * i / (nx - 1)
            q, nn = project(bvh, Vector((x, sgn * 0.5, z)), (0, -sgn, 0), 0.5, 0.0)
            row.append((q, nn) if q is not None else (Vector((x, sgn * 0.12, z)), Vector((0, sgn, 0))))
        grid.append(row)
    verts = [p + nn * lift for row in grid for p, nn in row] + [p - nn * 0.002 for row in grid for p, nn in row]
    off = nx * nz
    faces = []
    for j in range(nz - 1):
        for i in range(nx - 1):
            a = j * nx + i
            faces.append((a, a + 1, a + nx + 1, a + nx))
    ring = [i for i in range(nx)] + [j * nx + nx - 1 for j in range(1, nz)] + \
        [(nz - 1) * nx + i for i in range(nx - 2, -1, -1)] + [j * nx for j in range(nz - 2, 0, -1)]
    for q in range(len(ring)):
        a, b = ring[q], ring[(q + 1) % len(ring)]
        faces.append((b, a, a + off, b + off))
    obj = nb.mesh_object(name, verts, faces)
    fix_normals_out(obj, lambda c: Vector((0, -sgn * 0.05 + 0.01, c.z)))
    return set_material(obj, mats, mat)


def surface_line(bvh, starts, d, off=0.0):
    """Project each start point along d onto the surface; returns points, normals."""
    P, N = [], []
    for s in starts:
        q, nn = project(bvh, s, d, 0.35, off)
        if q is not None:
            P.append(q)
            N.append(nn)
    return P, N


def make_stripes(sp, bvh, mats):
    """Side stripes of the joggers (Trim), hip to cuff, on the outer side of each leg."""
    J, k = sp.J, sp.k
    out = []
    for s, sx in (("L", 1), ("R", -1)):
        hip, kne, ank = J["hip" + s], J["kne" + s], J["ank" + s]
        starts = []
        z0, z1 = sp.waist - 0.03, sp.hem + 0.05
        for i in range(14):
            z = z0 + (z1 - z0) * i / 13
            if z > kne.z:
                c = hip.lerp(kne, (hip.z - z) / (hip.z - kne.z))
            else:
                c = kne.lerp(ank, (kne.z - z) / (kne.z - ank.z))
            starts.append(Vector((c.x + sx * 0.3, c.y + 0.004, z)))
        P, N = surface_line(bvh, starts, (-sx, 0, 0))
        if len(P) > 3:
            o = ribbon("Stripe" + s, P, N, 0.020, 0.0022, mats, "Trim")
            out.append(o)
    return out


SEG7 = {"1": "bc", "0": "abcdef"}


def make_number(sp, bvh, mats, text="10"):
    """Football shirt number on the back (7-segment style digits, Trim)."""
    k = sp.k
    hgt, wid, bw = 0.17 * k, 0.085, 0.024
    zc = 1.255 * k
    out = []
    xs = [0.058, -0.048] if len(text) == 2 else [0.0]
    for ch, x in zip(text, xs):
        segs = {"a": ((-1, 1), (1, 1)), "b": ((1, 1), (1, 0)), "c": ((1, 0), (1, -1)), "d": ((1, -1), (-1, -1)),
                "e": ((-1, -1), (-1, 0)), "f": ((-1, 0), (-1, 1))}
        for sg in SEG7[ch]:
            (u0, v0), (u1, v1) = segs[sg]
            if ch == "1":
                u0 = u1 = 0.0
            starts = []
            for t in (0.0, 0.25, 0.5, 0.75, 1.0):
                u, v = u0 + (u1 - u0) * t, v0 + (v1 - v0) * t
                starts.append(Vector((x - u * (wid - bw) / 2, 0.3, zc + v * (hgt - bw) / 2)))
            P, N = surface_line(bvh, starts, (0, -1, 0))
            if len(P) >= 2:
                ext = (P[-1] - P[0]).normalized() * (bw / 2)
                P[0], P[-1] = P[0] - ext, P[-1] + ext
                out.append(ribbon("Digit", P, N, bw, 0.0020, mats, "Trim"))
    return out


def make_flipflops(sp, bvh, mats):
    """Flip-flops under the bare feet: sole slab (Shoes) + Y strap from the toe post."""
    J = sp.J
    out = []
    g = 0.92 if sp.female else 1.0
    for s, sx in (("L", 1), ("R", -1)):
        ank, toe = J["ank" + s], J["toe" + s]
        outline = []
        cx, cy = ank.x * 0.97 + toe.x * 0.03, (ank.y + 0.04 + toe.y) / 2
        for i in range(24):
            a = 2 * math.pi * i / 24
            d = Vector((math.cos(a) * 0.55, math.sin(a), 0)).normalized()
            c = Vector((cx, cy, 0.008))
            rc = 1.0 / math.hypot(d.x / 0.075, d.y / 0.19)
            hit = bvh.ray_cast(c + d * rc, -d, rc)
            p = hit[0] if hit[0] is not None else c + d * 0.05
            p = Vector((p.x, p.y, 0)) + d * (0.009 + 0.006 * max(0.0, -d.y))
            outline.append(p)
        sole = slab_from_outline("FlipSole" + s, outline, 0.0, 0.016, mats, "Shoes")
        sole["uv"] = "sole"
        out.append(sole)
        post = Vector((ank.x + sx * (-0.016 * g), toe.y + 0.052 * g, 0.016))
        for side in (-1, 1):                    # medial / lateral strap
            end = Vector((ank.x + sx * side * 0.040 * g, -0.025, 0.018))
            pts = [post]
            for t in (0.25, 0.5, 0.75):
                q = post.lerp(end, t)
                h = bvh.ray_cast(Vector((q.x, q.y, 0.11)), Vector((0, 0, -1)), 0.11)
                z = h[0].z + 0.0035 if h[0] is not None else 0.04
                pts.append(Vector((q.x, q.y, max(z, 0.02))))
            h = bvh.ray_cast(Vector((end.x + sx * side * 0.1, end.y, 0.024)), Vector((-sx * side, 0, 0)), 0.2)
            pts.append((h[0] + Vector((sx * side * 0.003, 0, 0))) if h[0] is not None else end)
            pts.append(Vector((pts[-1].x, pts[-1].y, 0.012)))
            out.append(tube("Strap", pts, [0.0044] * len(pts), 4, mats, "Shoes", cap_end=True, cap_start=True))
    return out


def make_laces(sp, bvh, mats):
    """High-top laces: small bars across the instep (Sole material, white)."""
    J = sp.J
    out = []
    for s in ("L", "R"):
        ank = J["ank" + s]
        for i in range(5):
            y = -0.010 - 0.017 * i
            h = bvh.ray_cast(Vector((ank.x, y, 0.20)), Vector((0, 0, -1)), 0.2)
            if h[0] is None or h[0].z > 0.16:
                continue
            p = h[0] + h[1] * 0.003
            o = set_material(nb.box("Lace", (0.030, 0.0055, 0.004), p), mats, "Sole")
            out.append(o)
    return out


def lash_cards(eye_c, r, sx, hk, mats, female):
    """Upper eyelash card: a thin curved wedge flicking out of the upper lid (Hair material)."""
    n = 8
    root, tip = [], []
    L = (0.0042 if female else 0.0032) * hk
    for i in range(n):
        a = math.radians(14 + 152 * i / (n - 1))
        x = -math.cos(a) * sx
        p = eye_c + Vector((x * r * 1.0, -r * 0.60 - 0.0006, math.sin(a) * r * 0.82 + 0.0005))
        out = Vector((x * 0.35, -1.0, 0.75)).normalized()
        f = 0.55 + 0.45 * math.sin(math.pi * (0.25 + 0.75 * i / (n - 1)))    # longer at the outer corner
        root.append(p)
        tip.append(p + out * L * f + Vector((0, 0, L * 0.35 * f)))
    verts = []
    for p, t in zip(root, tip):
        verts += [p + Vector((0, 0, 0.00045)), t, p - Vector((0, 0, 0.00045))]
    faces = []
    for i in range(n - 1):
        a, b = 3 * i, 3 * (i + 1)
        faces += [(a, b, b + 1, a + 1), (a + 1, b + 1, b + 2, a + 2), (a + 2, b + 2, b, a)]
    faces += [(0, 1, 2), (3 * (n - 1) + 2, 3 * (n - 1) + 1, 3 * (n - 1))]
    o = nb.mesh_object("LashCard", verts, faces)
    close_normals(o)
    return set_material(o, mats, "Hair")


def bvh_side(objs, sx):
    """BVH of the faces of objs on one side (sign of x) — e.g. one leg of the shorts."""
    bm = bmesh.new()
    for o in objs:
        me = o.data.copy()
        me.transform(o.matrix_world)
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_center_median().x * sx <= 0], context="FACES")
    tree = BVHTree.FromBMesh(bm)
    bm.free()
    return tree


def clothes_v4(sp, pieces, parts, bvh, bvh_head, body_E, mats, special, seam_src):
    """Volume / trims of the v4 outfits (bands on the seams, piping, accessories)."""
    J, k = sp.J, sp.k
    out = []

    def add(o, uv="", rule=None):
        o["uv"] = uv
        if rule:
            special[o.name] = rule
        out.append(o)
        return o
    Z = Vector((0, 0, 1))
    npts, ndirs = neckline(bvh_head, body_E, k)
    # ---- tops
    if sp.sleeveless and seam_src is not None:
        for o in seam_piping("Piping", seam_src, bvh, mats, "Shirt", sp.waist + 0.05,
                             width=0.011 if sp.top == "swim" else 0.014):
            add(o, "box:Shirt")
        bpy.data.objects.remove(seam_src)
    if sp.top in ("crop", "jersey", "jumpsuit"):
        ch, thick, mat = {"crop": (0.014, 0.0048, "Shirt"), "jersey": (0.020, 0.0060, "Trim"),
                          "jumpsuit": (0.030, 0.0065, "Shirt")}[sp.top]
        add(band_from_points("Collar", npts, ndirs, [Z] * len(npts), ch, thick, mat, mats, embed=0.004,
                             flare=0.005, lift=ch * 0.2), "box:Shirt" if mat == "Shirt" else "")
        for s in ("L", "R"):
            sho, elb = J["sho" + s], J["elb" + s]
            u = (elb - sho).normalized()
            c = sho + (elb - sho) * sp.sleeve_t
            if sp.top == "jumpsuit":      # rolled-up sleeve
                o, _, _ = band("Sleeve" + s, bvh, c, u, Vector((0, -1, 0)), 14, 0.10, 0.034, 0.0075, "Shirt", mats,
                               flare=0.002)
            else:
                o, _, _ = band("Sleeve" + s, bvh, c, u, Vector((0, -1, 0)), 14, 0.10, 0.022, 0.0045,
                               "Trim" if sp.top == "jersey" else "Shirt", mats, flare=0.002)
            add(o, "box:Shirt" if sp.top != "jersey" else "")
    if sp.top == "crop":
        o, _, _ = band("CropHem", bvh, Vector((0, 0.008, sp.crop)), Z, Vector((0, -1, 0)), 26, 0.30, 0.022, 0.005,
                       "Shirt", mats, embed=0.003)
        add(o, "box:Shirt")
    if sp.top == "jersey":
        o, _, _ = band("JerseyHem", bvh, Vector((0, 0.008, sp.waist)), Z, Vector((0, -1, 0)), 26, 0.32, 0.026,
                       0.0055, "Shirt", mats, embed=0.003, flare=0.003)
        add(o, "box:Shirt")
        if "number" in sp.extras:
            for o in make_number(sp, bvh, mats):
                add(o)
    if sp.top == "jumpsuit":
        # front placket from the collar to the waist, zip on top; chest pocket
        zt = min(p.z for p in npts[:3] + npts[-2:]) - 0.006
        starts = [Vector((0, -0.3, zt + (sp.waist + 0.03 - zt) * i / 9)) for i in range(10)]
        P, N = surface_line(bvh, starts, (0, 1, 0))
        if len(P) > 3:
            add(ribbon("Placket", P, N, 0.032, 0.0022, mats, "Shirt"), "box:Shirt")
            add(ribbon("Zip", [p + n * 0.0022 for p, n in zip(P, N)], N, 0.0065, 0.0016, mats, "Gear"))
        if "pocket" in sp.extras:
            add(patch("Pocket", bvh, 0.040, 0.118, 1.290 * k, 1.385 * k, mats, "Shirt"), "box:Shirt")
            # pocket flap
            add(patch("Flap", bvh, 0.037, 0.121, 1.362 * k, 1.392 * k, mats, "Shirt", lift=0.0068, nz=2),
                "box:Shirt")
    # ---- bottoms
    if sp.bottom == "shorts" or (sp.bottom == "joggers" and sp.top != "jersey") or sp.top == "jumpsuit":
        hgt = 0.026 if sp.top == "jumpsuit" else 0.036
        o, bpts, bdirs = band("Waistband", bvh, Vector((0, 0.008, sp.waist)), Z, Vector((0, -1, 0)), 26, 0.28,
                              hgt, 0.0062, "Pants", mats, embed=0.003)
        add(o, "box:Pants")
        if sp.top != "jumpsuit":      # drawstrings hanging from the front of the waistband
            f0 = bpts[0] + bdirs[0] * 0.0075
            for sx in (1, -1):
                q = f0 + Vector((sx * 0.011, 0, -0.006))
                pts = [q + Vector((sx * 0.003 * t, -0.006 * t, -0.11 * k * t)) for t in (0, 0.3, 0.6, 1.0)]
                add(tube("Cord", pts, [0.0028, 0.0028, 0.0028, 0.004], 5, mats, "Trim", cap_end=True,
                         cap_start=True), rule="legs")
    if sp.bottom == "shorts":
        for s, sx in (("L", 1), ("R", -1)):
            hip, kne = J["hip" + s], J["kne" + s]
            z = sp.shorts_hem
            c = hip.lerp(kne, (hip.z - z) / (hip.z - kne.z))
            axis = (hip - kne).normalized()
            o, _, _ = band("ShortsHem" + s, bvh_side([pieces["Pants"]], sx), c, axis, Vector((0, -1, 0)), 16, 0.16,
                           0.024, 0.0048, "Pants", mats, embed=0.004, flare=0.004)
            add(o, "box:Pants")
    if sp.bottom == "joggers":
        for s in ("L", "R"):
            ank = J["ank" + s]
            o, _, _ = band("Cuff" + s, bvh, Vector((ank.x, ank.y - 0.006, sp.hem + 0.006)), Z, Vector((0, -1, 0)),
                           14, 0.10, 0.042, 0.0068, "Pants", mats, embed=0.004, flare=0.002)
            add(o, "box:Pants")
        if "stripes" in sp.extras:
            for o in make_stripes(sp, bvh_of([pieces["Pants"]]), mats):
                add(o, rule="legs")
    if sp.bottom == "jumpsuit":
        for s in ("L", "R"):
            ank = J["ank" + s]
            o, _, _ = band("Hem" + s, bvh, Vector((ank.x, ank.y - 0.008, sp.hem)), Z, Vector((0, -1, 0)), 14, 0.09,
                           0.026, 0.005, "Pants", mats, embed=0.003, flare=0.004)
            add(o, "box:Pants")
    # ---- feet
    if sp.feet == "flip":
        for o in make_flipflops(sp, bvh, mats):
            add(o, o.get("uv", "shoe"))
    else:
        for s in ("L", "R"):
            ank, toe = J["ank" + s], J["toe" + s]
            outline = []
            cx, cy = ank.x * 0.97 + toe.x * 0.03, (ank.y + 0.06 + toe.y) / 2
            for i in range(22):
                a = 2 * math.pi * i / 22
                d = Vector((math.cos(a) * 0.55, math.sin(a), 0)).normalized()
                c = Vector((cx, cy, 0.016))
                rc = 1.0 / math.hypot(d.x / 0.075, d.y / 0.19)
                hit = bvh.ray_cast(c + d * rc, -d, rc)
                p = hit[0] if hit[0] is not None else c + d * 0.05
                outline.append(p + d * (0.0045 if sp.feet == "hightop" else 0.0035))
            if sp.feet == "hightop":
                add(slab_from_outline("Sole" + s, outline, 0.0, 0.032, mats, "Sole"))
            else:
                add(slab_from_outline("Sole" + s, outline, 0.0, 0.024, mats, "Shoes"), "sole")
        if sp.feet == "hightop":
            for o in make_laces(sp, bvh, mats):
                add(o)
    # ---- neck accessories
    if "whistle" in sp.extras:
        for o in make_whistle(sp, bvh, npts, ndirs, mats):
            add(o, rule="chest")
    if "chain" in sp.extras:
        for o in make_chain(sp, bvh, npts, ndirs, mats):
            add(o, rule="chest")
    return out


# --------------------------------------------------------------------------- textures / UVs (v3)
def tex_material(name, color, roughness, img, normal=None, nstrength=1.0):
    """Principled material whose base colour is image x colour (glTF baseColorTexture x factor)."""
    mat = nb.material(name, color, roughness=roughness)
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    it = nt.nodes.new("ShaderNodeTexImage")
    it.image = bpy.data.images.load(img, check_existing=True)
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs[0].default_value = 1.0
    nt.links.new(it.outputs["Color"], mix.inputs[6])
    mix.inputs[7].default_value = tuple(color) + (1.0,)
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    if normal:
        nimg = bpy.data.images.load(normal, check_existing=True)
        nimg.colorspace_settings.name = "Non-Color"
        ni = nt.nodes.new("ShaderNodeTexImage")
        ni.image = nimg
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = nstrength
        nt.links.new(ni.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def _uv(obj):
    me = obj.data
    return me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")


def uv_box(obj, tile):
    """Box projection at world scale (tiling fabric textures)."""
    me = obj.data
    uv = _uv(obj)
    for p in me.polygons:
        nx, ny, nz = (abs(c) for c in p.normal)
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            if nz >= nx and nz >= ny:
                a, b = co.x, co.y
            elif nx >= ny:
                a, b = co.y, co.z
            else:
                a, b = co.x, co.z
            uv.data[li].uv = (a / tile, b / tile)


def uv_face(obj, sp):
    """Front projection of the head into the face area of the skin texture (u .25-1)."""
    me = obj.data
    uv = _uv(obj)
    for li, lp in enumerate(me.loops):
        d = (me.vertices[lp.vertex_index].co - sp.hc) / sp.hk
        u, v = nbt.face_uv(d.x, d.z)
        uv.data[li].uv = (min(0.995, max(0.255, u)), min(0.995, max(0.005, v)))


def uv_strip(obj, u0=0.01, u1=0.24, axis="y"):
    """Plain skin: planar projection normalised into the body strip of the skin texture."""
    me = obj.data
    uv = _uv(obj)
    co = np.array([v.co for v in me.vertices])
    if not len(co):
        return
    i0, i1 = (0, 2) if axis == "y" else (1, 2)
    lo, hi = co.min(0), co.max(0)
    span = np.maximum(hi - lo, 1e-6)
    for li, lp in enumerate(me.loops):
        c = co[lp.vertex_index]
        a = (c[i0] - lo[i0]) / span[i0]
        b = (c[i1] - lo[i1]) / span[i1]
        uv.data[li].uv = (u0 + (u1 - u0) * a, 0.01 + 0.98 * b)


def uv_shoe(obj):
    """Shoe uppers / belt pieces: side projection normalised into the leather band (v .32-.98)."""
    me = obj.data
    uv = _uv(obj)
    co = np.array([v.co for v in me.vertices])
    if not len(co):
        return
    lo, hi = co.min(0), co.max(0)
    span = np.maximum(hi - lo, 1e-6)
    for li, lp in enumerate(me.loops):
        c = co[lp.vertex_index]
        uv.data[li].uv = ((c[1] - lo[1]) / span[1] + 0.5 * (c[0] - lo[0]) / span[0],
                          0.32 + 0.66 * (c[2] - lo[2]) / span[2])


def uv_ring(obj, center, z0, z1, v0, v1, reps):
    """Cylindrical mapping around a vertical axis (soles, belt): u wraps reps times."""
    me = obj.data
    uv = _uv(obj)
    for p in me.polygons:
        us = []
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            us.append((math.atan2(co.y - center.y, co.x - center.x) / (2 * math.pi)) % 1.0)
        if max(us) - min(us) > 0.5:
            us = [x + 1.0 if x < 0.5 else x for x in us]
        for li, u in zip(p.loop_indices, us):
            co = me.vertices[me.loops[li].vertex_index].co
            t = min(1.0, max(0.0, (co.z - z0) / max(1e-6, z1 - z0)))
            if abs(p.normal.z) > 0.7:
                t = 0.5
            uv.data[li].uv = (u * reps, v0 + (v1 - v0) * t)


TILE = {"Shirt": 0.05, "Pants": 0.06, "Hat": 0.055}
ARM_U = {1: (0.060, 0.152), -1: (0.156, 0.248)}       # armcyl: u range of the left / right arm


def arm_coords(sp, c):
    """(side, s, phi) of a point of the arm: s 0 = elbow .. 1 = wrist, -1 .. 0 = shoulder .. elbow."""
    side = 1 if c.x >= 0 else -1
    sd = "L" if side > 0 else "R"
    sho, elb, wri = sp.J["sho" + sd], sp.J["elb" + sd], sp.J["wri" + sd]
    fa = wri - elb
    s = (c - elb).dot(fa) / fa.length_squared
    ax = fa.normalized()
    if s < 0:
        ua = sho - elb
        s = -(c - elb).dot(ua) / ua.length_squared
        ax = -ua.normalized()
    ref = Vector((0, -1, 0))
    ref = (ref - ax * ref.dot(ax)).normalized()
    b = ax.cross(ref)
    r = c - elb
    return side, s, math.atan2(r.dot(b), r.dot(ref))


def uv_armcyl(obj, sp):
    """Cylindrical UVs around each arm (forearm + upper arm) into the body strip: tattoos wrap."""
    me = obj.data
    uv = _uv(obj)
    for p in me.polygons:
        vals = []
        for li in p.loop_indices:
            side, s, phi = arm_coords(sp, me.vertices[me.loops[li].vertex_index].co)
            u0, u1 = ARM_U[side]
            vals.append((u0, u1, (phi + math.pi) / (2 * math.pi), 0.5 - 0.48 * max(-1.0, min(1.0, s))))
        fr = [q[2] for q in vals]
        if max(fr) - min(fr) > 0.5:
            fr = [f + 1.0 if f < 0.5 else f for f in fr]
        for li, (u0, u1, _, v), f in zip(p.loop_indices, vals, fr):
            uv.data[li].uv = (u0 + (u1 - u0) * min(1.0, f), v)


def arm_uv_inverse(u, v):
    for side, (u0, u1) in ARM_U.items():
        if u0 <= u <= u1:
            return side, (0.5 - v) / 0.48, (u - u0) / (u1 - u0) * 2 * math.pi - math.pi
    return None


def assign_uvs(parts, sp):
    for o in parts:
        mode = o.get("uv", "")
        if mode == "face":
            uv_face(o, sp)
        elif mode == "strip":
            uv_strip(o)
        elif mode == "shoe":
            uv_shoe(o)
        elif mode == "sole":
            c = sum((v.co for v in o.data.vertices), Vector()) / max(1, len(o.data.vertices))
            uv_ring(o, c, 0.0, 0.024, 0.02, 0.25, 6)
        elif mode == "belt":
            uv_ring(o, Vector((0, 0.008, 0)), sp.waist - 0.02, sp.waist + 0.02, 0.40, 0.90, 9)
        elif mode.startswith("box:"):
            uv_box(o, TILE[mode[4:]])
        elif mode.startswith("iris:"):
            ex, ez, ri = (float(x) for x in mode[5:].split(","))
            uv = _uv(o)
            for li, lp in enumerate(o.data.loops):
                c = o.data.vertices[lp.vertex_index].co
                uv.data[li].uv = (0.5 + (c.x - ex) / (2 * ri), 0.5 + (c.z - ez) / (2 * ri))
        elif mode == "strip0":
            uv_strip(o, 0.005, 0.055)
        elif mode == "armcyl":
            uv_armcyl(o, sp)
        else:
            _uv(o)



# --------------------------------------------------------------------------- build
COLORS = {   # default glTF colours (the game overrides Skin Shirt Pants Shoes Hair through material.color)
    "human_m": dict(Skin=(0.80, 0.56, 0.43), Shirt=(0.13, 0.30, 0.55), Pants=(0.12, 0.14, 0.20),
                    Shoes=(0.09, 0.07, 0.06), Hair=(0.09, 0.06, 0.04), Lips=(0.62, 0.34, 0.30)),
    "human_f": dict(Skin=(0.86, 0.64, 0.52), Shirt=(0.62, 0.12, 0.28), Pants=(0.20, 0.23, 0.33),
                    Shoes=(0.09, 0.07, 0.06), Hair=(0.25, 0.13, 0.06), Lips=(0.66, 0.28, 0.30)),
    "human_m2": dict(Skin=(0.56, 0.37, 0.26), Shirt=(0.30, 0.32, 0.31), Pants=(0.15, 0.21, 0.34),
                     Shoes=(0.80, 0.80, 0.78), Hair=(0.04, 0.03, 0.025), Lips=(0.45, 0.25, 0.21),
                     Hat=(0.55, 0.09, 0.08)),
    "human_f2": dict(Skin=(0.66, 0.45, 0.33), Shirt=(0.86, 0.80, 0.66), Pants=(0.10, 0.12, 0.24),
                     Shoes=(0.12, 0.08, 0.07), Hair=(0.05, 0.035, 0.025), Lips=(0.58, 0.26, 0.27)),
    # v4
    "human_f3": dict(Skin=(0.78, 0.55, 0.40), Shirt=(0.78, 0.04, 0.04), Pants=(0.06, 0.10, 0.26),
                     Shoes=(0.95, 0.70, 0.08), Hair=(0.34, 0.20, 0.09), Lips=(0.66, 0.30, 0.30),
                     Gear=(0.02, 0.02, 0.025), Metal=(0.82, 0.82, 0.84), Lens=(0.02, 0.025, 0.04),
                     Trim=(0.92, 0.92, 0.90), Eyes=(0.30, 0.42, 0.22)),
    "human_m3": dict(Skin=(0.60, 0.38, 0.25), Shirt=(0.80, 0.05, 0.05), Pants=(0.98, 0.64, 0.08),
                     Shoes=(0.06, 0.06, 0.07), Hair=(0.07, 0.045, 0.03), Lips=(0.48, 0.27, 0.22),
                     Hat=(0.93, 0.92, 0.86), Gear=(0.75, 0.04, 0.04), Metal=(0.82, 0.82, 0.84),
                     Trim=(0.92, 0.92, 0.90), Eyes=(0.28, 0.17, 0.08)),
    "human_f4": dict(Skin=(0.42, 0.26, 0.17), Shirt=(1.00, 0.10, 0.52), Pants=(0.05, 0.05, 0.07),
                     Shoes=(0.94, 0.94, 0.95), Hair=(0.03, 0.02, 0.018), Lips=(0.36, 0.17, 0.15),
                     Metal=(1.00, 0.74, 0.28), Trim=(0.35, 1.00, 0.10), Sole=(0.96, 0.96, 0.96),
                     Eyes=(0.22, 0.12, 0.05)),
    "human_m4": dict(Skin=(0.52, 0.33, 0.22), Shirt=(1.00, 0.84, 0.04), Pants=(0.04, 0.14, 0.45),
                     Shoes=(0.07, 0.07, 0.09), Hair=(0.03, 0.02, 0.018), Lips=(0.42, 0.22, 0.18),
                     Hat=(0.02, 0.50, 0.24), Metal=(1.00, 0.74, 0.28), Trim=(0.02, 0.50, 0.24),
                     Sole=(0.96, 0.96, 0.96), Eyes=(0.20, 0.11, 0.05)),
    "human_m5": dict(Skin=(0.74, 0.52, 0.38), Shirt=(1.00, 0.36, 0.04), Pants=(1.00, 0.36, 0.04),
                     Shoes=(0.90, 0.90, 0.88), Hair=(0.07, 0.05, 0.04), Lips=(0.60, 0.33, 0.28),
                     Gear=(0.12, 0.12, 0.13), Eyes=(0.25, 0.30, 0.34)),
}
# v4 fabric maps per slot: (texture, normal map, tile in metres)
FABRIC = {
    "swim": ("jersey", 0.022), "tank": ("mesh", 0.030), "crop": ("jersey", 0.045), "jersey": ("mesh", 0.034),
    "jumpsuit": ("denim", 0.075), "shorts": ("ripstop", 0.05), "joggers": ("jersey", 0.065),
}


def build_human(female, variant=""):
    tex = dict(nbt.textures(female))    # bakes in its own scene: before the scene reset
    if Spec(female, variant).v4:
        tex.update(nbt.textures_v4())
    nb.reset_scene()
    scene = bpy.context.scene
    scene.render.fps = FPS
    sp = Spec(female, variant)
    J, k, hk, hc = sp.J, sp.k, sp.hk, sp.hc
    st, dr = sp.stocky, sp.dress
    C = COLORS[sp.name]
    if sp.v4:
        top, bot = FABRIC[sp.top], FABRIC[sp.bottom]
        TILE["Shirt"], TILE["Pants"] = top[1], bot[1]
    else:
        top, bot = ("jersey", 0.05), ("denim", 0.06)
        TILE["Shirt"], TILE["Pants"] = 0.05, 0.06
    hat_tex = "denim" if not sp.v4 else {"bucket": bot[0], "cap": top[0]}.get(sp.hat, "denim")
    skin_png = tex["skin_f" if female else "skin_m"]
    if "tattoo" in sp.extras:
        skin_png = nbt.tattoo_skin(skin_png, "skin_" + sp.name[6:], arm_uv_inverse)
    mats = {
        "Skin": tex_material("Skin", C["Skin"], 0.55, skin_png),
        "Shirt": tex_material("Shirt", C["Shirt"], 0.45 if sp.top == "swim" else 0.8, tex[top[0]],
                              tex[top[0] + "_n"], 0.55),
        "Pants": tex_material("Pants", C["Pants"], 0.85, tex[bot[0]], tex[bot[0] + "_n"], 0.55),
        "Shoes": tex_material("Shoes", C["Shoes"], 0.5, tex["shoes"]),
        "Hair": nb.material("Hair", C["Hair"], roughness=0.6),
        "Eyes": (tex_material("Eyes", C["Eyes"], 0.12, tex["iris"]) if sp.v4
                 else nb.material("Eyes", (0.05, 0.035, 0.025), roughness=0.12)),
        "Lips": nb.material("Lips", C["Lips"], roughness=0.4),
        "EyeWhite": nb.material("EyeWhite", (0.86, 0.83, 0.79), roughness=0.2),
        "Hat": (tex_material("Hat", C["Hat"], 0.75, tex[hat_tex], tex[hat_tex + "_n"], 0.5) if sp.hat
                else nb.material("Hat", (0.5, 0.5, 0.5))),
        "Gear": nb.material("Gear", C.get("Gear", (0.03, 0.03, 0.035)), roughness=0.45),
        "Metal": nb.material("Metal", C.get("Metal", (0.8, 0.8, 0.82)), metallic=1.0, roughness=0.25),
        "Lens": nb.material("Lens", C.get("Lens", (0.02, 0.025, 0.04)), metallic=0.6, roughness=0.08),
        "Trim": nb.material("Trim", C.get("Trim", (0.9, 0.9, 0.9)), roughness=0.6),
        "Sole": nb.material("Sole", C.get("Sole", (0.95, 0.95, 0.95)), roughness=0.7),
    }

    body_E = body_elements(sp)
    head_E = head_elements(sp)
    hand_E = {s: hand_elements(sp, s) for s in ("L", "R")}
    weight_E = [e for e in body_E + head_E + hand_E["L"] + hand_E["R"] if not e["neg"]]

    # ------------------------------------------------ body family
    body = metaball_mesh("BodyMB", body_E, 0.0078)
    for m in ORDER:
        body.data.materials.append(mats[m])

    def body_rule_v4(c, reg, bone):
        if bone in ("Hips", "Spine", "Chest", "Neck"):
            if c.z <= sp.waist:
                return "Pants"
            if sp.top == "crop" and c.z < sp.crop:
                return "Skin"
            if sp.sleeveless and torso_bare(sp, c):
                return "Skin"
            return "Shirt"
        if bone.startswith("UpperArm"):
            if sp.sleeveless:
                return "Skin"
            sd = bone[-1]
            sho, elb = J["sho" + sd], J["elb" + sd]
            t = (c - sho).dot(elb - sho) / (elb - sho).length_squared
            return "Shirt" if t < sp.sleeve_t else "Skin"
        if bone.startswith("LowerArm"):
            return "Skin"
        if sp.feet == "flip" and bone.startswith("Foot"):
            return "Skin"
        if sp.bottom == "shorts":
            return "Pants" if c.z > sp.shorts_hem else "Skin"
        if (c.z < sp.hem or bone.startswith("Foot")) and c.z < sp.hem + 0.01:
            return "Shoes"
        return "Pants"

    def body_rule(c, reg, bone):
        if sp.v4:
            return body_rule_v4(c, reg, bone)
        if bone in ("Hips", "Spine", "Chest", "Neck") and reg in ("Shirt", "Pants", "Skin"):
            reg = "Shirt" if c.z > sp.waist else "Pants"
        elif bone.startswith("UpperArm"):
            sd = bone[-1]
            sho, elb = J["sho" + sd], J["elb" + sd]
            t = (c - sho).dot(elb - sho) / (elb - sho).length_squared
            reg = "Shirt" if (t < sp.sleeve_t or sp.long_sleeve) else "Skin"
        elif bone.startswith("LowerArm"):
            reg = "Shirt" if sp.long_sleeve else "Skin"
        elif bone.startswith(("UpperLeg", "LowerLeg", "Foot")):
            if (c.z < sp.hem or bone.startswith("Foot")) and c.z < sp.hem + 0.01:
                reg = "Shoes"
            elif dr:
                reg = "Pants" if c.z > 0.80 * k else "Skin"      # shorts under the skirt, bare legs
            else:
                reg = "Pants"
        return reg
    classify(body, body_E, body_rule)
    for v in body.data.vertices:          # flat shoe bottoms
        if v.co.z < 0.006:
            v.co.z = 0.0
    pieces = split_by_material(body, mats)
    seam_src = None
    if sp.sleeveless:              # snap the stair-stepped cut-out seams onto smooth curves
        curves = []
        for lp in boundary_loops(pieces["Shirt"], sp.waist + 0.05):
            c = resample_loop(lp, 0.006)
            for _ in range(16):
                c = [c[i] * 0.5 + (c[i - 1] + c[(i + 1) % len(c)]) * 0.25 for i in range(len(c))]
            curves.append(np.array(c))
        for nm in ("Shirt", "Skin"):
            snap_boundary(pieces[nm], curves)
    if sp.sleeveless:              # garment cut-outs: keep the dense boundary for the piping
        seam_src = pieces["Shirt"].copy()
        seam_src.data = pieces["Shirt"].data.copy()
        nb.link(seam_src)
    if sp.v4:
        budget = {"swim": {"Shirt": 700, "Pants": 520, "Skin": 1150},
                  "tank": {"Shirt": 820, "Pants": 600, "Skin": 1330},
                  "crop": {"Shirt": 720, "Pants": 760, "Shoes": 440, "Skin": 640},
                  "jersey": {"Shirt": 1150, "Pants": 800, "Shoes": 480, "Skin": 460},
                  "jumpsuit": {"Shirt": 1150, "Pants": 1060, "Shoes": 460, "Skin": 480}}[sp.top]
    elif st:
        budget = {"Shirt": 1650, "Pants": 900, "Shoes": 460, "Skin": 60}
    elif dr:
        budget = {"Shirt": 880, "Pants": 240, "Shoes": 400, "Skin": 880}
    else:
        budget = {"Shirt": 1150, "Pants": 960, "Shoes": 460, "Skin": 380}
    for name, o in pieces.items():
        keep = None
        if sp.sleeveless and name in ("Shirt", "Skin"):
            # protect the garment cut-out edges (otherwise the decimated seam shows red teeth)
            from mathutils.kdtree import KDTree
            bl = [p_ for lp_ in boundary_loops(o, sp.waist + 0.05) for p_ in lp_]
            if bl:
                kd = KDTree(len(bl))
                for i_, p_ in enumerate(bl):
                    kd.insert(p_, i_)
                kd.balance()
                keep = lambda c, kd=kd: 1.0 if kd.find(c)[2] < 0.010 else 0.0
        decimate(o, budget.get(name, 300), keep)
        o["uv"] = {"Skin": "armcyl" if "tattoo" in sp.extras else "strip", "Shoes": "shoe"}.get(name, "box:" + name)

    # ------------------------------------------------ head family
    head = metaball_mesh("HeadMB", head_E, 0.0038)
    set_material(head, mats, "Skin")

    def head_rule(c, reg, bone):
        return "Lips" if reg == "Lips" else "Skin"
    classify(head, head_E, head_rule, boost={"Lips": 4.0})

    def scalp(c):
        """Hairline: True when a point of the head lies under the hair."""
        d = (c - hc) / hk
        if d.length > 0.17 or d.z < -0.16:
            return False
        t = max(0.0, min(1.0, (d.y + 0.09) / 0.19))     # 0 = forehead, 1 = back of the head
        if female:
            zc = 0.036 - 0.150 * t ** 1.2 + 0.010 * min(1.0, (d.x / 0.05) ** 2) * (1 - t)
        else:
            zc = 0.044 - 0.148 * t ** 1.3 + 0.016 * min(1.0, (d.x / 0.05) ** 2) * (1 - t)
        temple = abs(d.x) > (0.050 if female else 0.046) and d.y < -0.035 and d.z < (0.020 if female else 0.032)
        ear = abs(d.x) > 0.062 and -0.022 < d.y < 0.040 and -0.07 < d.z < 0.010
        burn = abs(d.x) > 0.058 and -0.036 < d.y < -0.010 and d.z > (-0.030 if female else -0.026)
        return (d.z > zc and not temple and not ear) or (burn and not ear)

    # hair cap: copy of the dense scalp faces pushed out along the normals,
    # tapering to zero at the hairline so it blends into the skin; the offset is modulated
    # by strand_ridge() so the hair shows locks (mèches) in the geometry
    me = head.data
    bm = bmesh.new()
    bm.from_mesh(me)
    capbm = bmesh.new()
    vmap = {}
    for f_ in bm.faces:
        if not scalp(f_.calc_center_median()):
            continue
        vs = []
        for v in f_.verts:
            if v.index not in vmap:
                vmap[v.index] = (capbm.verts.new(v.co), v.normal.copy())
            vs.append(vmap[v.index][0])
        try:
            capbm.faces.new(vs)
        except ValueError:
            pass
    bm.free()
    bvh_dense = BVHTree.FromObject(head, bpy.context.evaluated_depsgraph_get())
    bnd = [v for v in capbm.verts if v.is_boundary]
    for _ in range(8):
        new = {}
        for v in bnd:
            nb_ = [e.other_vert(v) for e in v.link_edges if e.is_boundary]
            if len(nb_) == 2:
                new[v] = v.co * 0.4 + (nb_[0].co + nb_[1].co) * 0.3
        for v, c in new.items():
            hit = bvh_dense.find_nearest(c)
            v.co = hit[0] if hit[0] is not None else c
    ring = {v: 0 for v in capbm.verts if v.is_boundary}
    frontier = list(ring)
    lvl = 0
    while frontier and lvl < 9:
        lvl += 1
        nxt = []
        for v in frontier:
            for e in v.link_edges:
                o = e.other_vert(v)
                if o not in ring:
                    ring[o] = lvl
                    nxt.append(o)
        frontier = nxt
    nrm = {cv: n for cv, n in vmap.values()}
    for v in capbm.verts:
        d = (v.co - hc) / hk
        top = max(0.0, min(1.0, (d.z + 0.02) / 0.10))
        rid = strand_ridge(sp, d)
        if sp.pulled:
            off = 0.0042 + 0.0030 * top
            off *= 1.0 + 0.32 * rid
        elif sp.hair == "buzz":            # shaved / buzz cut: a thin even shell
            off = 0.0036 + 0.0008 * top
        elif female:
            off = 0.008 + 0.006 * top
            off *= 1.0 + 0.22 * rid
        else:
            side = max(0.0, min(1.0, (abs(d.x) - 0.045) / 0.03))
            off = 0.0055 + 0.013 * top * (1 - 0.6 * side)
            off *= 1.0 + 0.30 * rid * (0.4 + 0.6 * top) + 0.10 * math.sin(d.x * 95 + 1.3) * math.sin(d.y * 60 + d.z * 40)
        r = ring.get(v, 9)
        v.co = v.co + nrm[v] * off * (0.10 + 0.90 * smooth(r / 7.0))
    hair_parts = [nb.bm_to_object("HairCap", capbm)]
    set_material(hair_parts[0], mats, "Hair")

    # hair volumes (bob): separate metaball family, faces buried in the head removed, locks carved
    hv = hair_volume_elements(sp)
    vol = metaball_mesh("HairMB", hv, 0.0050) if hv else None
    if vol is not None:
        add_hair_volume(vol, head_E, hc, hk, female, mats)
        vol.data.update()
        for v in vol.data.vertices:
            d = (v.co - hc) / hk
            if sp.hair == "bun":                                   # tight curls on the puff
                cur = math.sin(d.x * 260 + 1.1) * math.sin(d.y * 240 + 0.4) * math.sin(d.z * 250 + 2.0)
                v.co = v.co + v.normal * (0.0028 * cur)
                continue
            fall = max(0.0, min(1.0, (0.06 - d.z) / 0.10))         # locks deepen towards the tips
            v.co = v.co + v.normal * (0.0032 * strand_ridge(sp, d) * (0.4 + 0.6 * fall))
        hair_parts.append(vol)

    def head_keep(c):
        d = (c - hc) / hk
        if d.y < -0.035 and -0.15 < d.z < 0.03 and abs(d.x) < 0.07:
            return 0.55                                  # face
        if abs(d.x) > 0.062 and -0.08 < d.z < 0.02:
            return 0.35                                  # ears
        if scalp(c):
            return 0.0
        return 0.1
    decimate(head, (1740 if female else 1800) if sp.v4 else (1800 if female else 1850), head_keep)
    decimate(hair_parts[0], (680 if sp.v4 else 820) if sp.pulled else (560 if female else (
        520 if sp.hat else (640 if sp.hair == "buzz" else 980))))
    if vol is not None:
        decimate(vol, 440 if sp.hair == "bun" else 900)
    head["uv"] = "face"

    # ------------------------------------------------ hands
    hands = []
    for s in ("L", "R"):
        h = metaball_mesh("Hand" + s + "MB", hand_E[s], 0.0032)
        set_material(h, mats, "Skin")
        decimate(h, 380 if sp.v4 else 420)
        h["uv"] = "strip0" if "tattoo" in sp.extras else "strip"
        hands.append(h)

    parts = list(pieces.values()) + [head] + hair_parts + hands
    bvh = bvh_of(parts)
    bvh_head = bvh_of([head])
    special = {}                                       # object name -> weight rule

    # ------------------------------------------------ clothing volume
    if sp.v4:
        parts += clothes_v4(sp, pieces, parts, bvh, bvh_head, body_E, mats, special, seam_src)
    else:
        # shirt collar on the neckline (where the neck leaves the shirt), standing a little
        npts, ndirs = neckline(bvh_head, body_E, k)
        ch = 0.016 if female else (0.030 if st else 0.024)
        collar = band_from_points("Collar", npts, ndirs, [Vector((0, 0, 1))] * len(npts), ch,
                                  0.0085 if st else 0.0055, "Shirt", mats, embed=0.004, flare=0.005, lift=ch * 0.2)
        collar["uv"] = "box:Shirt"
        parts.append(collar)
        if st:
            for o in make_drawstrings(sp, npts, mats):
                o["uv"] = "box:Shirt"
                parts.append(o)
            pk = make_pocket(sp, bvh, mats)
            pk["uv"] = "box:Shirt"
            parts.append(pk)
        # sleeve hems (rib cuffs at the wrist for the hoodie)
        for s in ("L", "R"):
            sho, elb, wri = J["sho" + s], J["elb" + s], J["wri" + s]
            if sp.long_sleeve:
                u = (wri - elb).normalized()
                o, _, _ = band("Cuff" + s, bvh, wri - u * 0.040, u, Vector((0, -1, 0)), 14, 0.09, 0.040, 0.004,
                               "Shirt", mats, embed=0.003)
            else:
                u = (elb - sho).normalized()
                c = sho + (elb - sho) * sp.sleeve_t
                o, _, _ = band("Sleeve" + s, bvh, c, u, Vector((0, -1, 0)), 14, 0.075, 0.022, 0.0045, "Shirt", mats,
                               flare=0.002)
            o["uv"] = "box:Shirt"
            parts.append(o)
        if st:
            # hoodie rib hem instead of the belt
            o, _, _ = band("HoodHem", bvh, Vector((0, 0.008, sp.waist)), Vector((0, 0, 1)), Vector((0, -1, 0)),
                           26, 0.30, 0.050, 0.006, "Shirt", mats, embed=0.004)
            o["uv"] = "box:Shirt"
            parts.append(o)
        elif dr:
            bvh_b = bvh_of([o for n_, o in pieces.items() if n_ in ("Pants", "Shirt")])
            sk = make_skirt(sp, bvh_b, mats)
            sk["uv"] = "box:Pants"
            special[sk.name] = "skirt"
            parts.append(sk)
            o, _, _ = band("Waistband", bvh, Vector((0, 0.008, sp.waist)), Vector((0, 0, 1)), Vector((0, -1, 0)),
                           26, 0.26, 0.030, 0.0065, "Pants", mats, embed=0.003)
            o["uv"] = "box:Pants"
            parts.append(o)
        else:
            # belt + buckle
            belt, bpts, bdirs = band("Belt", bvh, Vector((0, 0.008, sp.waist)), Vector((0, 0, 1)),
                                     Vector((0, -1, 0)), 24, 0.26, 0.036 if not female else 0.03, 0.006, "Shoes", mats,
                                     embed=0.003)
            belt["uv"] = "belt"
            parts.append(belt)
            front = bpts[0] + bdirs[0] * 0.006
            bk = set_material(nb.box("Buckle", (0.05, 0.010, 0.040 if not female else 0.034),
                                     (front.x, front.y - 0.003, sp.waist)), mats, "Shoes")
            bk["uv"] = "shoe"
            parts.append(bk)
            for x in (-0.06, 0.06, -0.12, 0.12):                       # belt loops
                hit = bvh.ray_cast(Vector((x, -0.4, sp.waist)), Vector((0, 1, 0)))
                if hit[0] is not None:
                    lp = set_material(nb.box("Loop", (0.012, 0.010, 0.05), hit[0] + Vector((0, -0.006, 0))),
                                      mats, "Pants")
                    lp["uv"] = "box:Pants"
                    parts.append(lp)
        # trouser hems (shoe collar for the bare-legged variant) and shoe soles
        for s in ("L", "R"):
            ank, toe = J["ank" + s], J["toe" + s]
            if dr:
                o, _, _ = band("ShoeTop" + s, bvh, Vector((ank.x, ank.y - 0.004, sp.hem)), Vector((0, 0.35, 1)),
                               Vector((0, -1, 0)), 14, 0.09, 0.012, 0.0035, "Shoes", mats, embed=0.003, flare=0.001)
                o["uv"] = "shoe"
            else:
                o, _, _ = band("Hem" + s, bvh, Vector((ank.x, ank.y - 0.008, sp.hem)), Vector((0, 0, 1)),
                               Vector((0, -1, 0)), 14, 0.09, 0.026, 0.005, "Pants", mats, embed=0.003, flare=0.004)
                o["uv"] = "box:Pants"
            parts.append(o)
            outline = []
            cx, cy = ank.x * 0.97 + toe.x * 0.03, (ank.y + 0.06 + toe.y) / 2
            for i in range(22):
                a = 2 * math.pi * i / 22
                d = Vector((math.cos(a) * 0.55, math.sin(a), 0)).normalized()
                c = Vector((cx, cy, 0.014))
                rc = 1.0 / math.hypot(d.x / 0.075, d.y / 0.19)        # start inside an ellipse around the foot
                hit = bvh.ray_cast(c + d * rc, -d, rc)
                p = hit[0] if hit[0] is not None else c + d * 0.05
                outline.append(p + d * 0.0035)
            sole = slab_from_outline("Sole" + s, outline, 0.0, 0.018 if dr else 0.024, mats, "Shoes")
            sole["uv"] = "sole"
            parts.append(sole)

    # ------------------------------------------------ eyes, lash lines and eyebrows
    for sx in (1, -1):
        ex, ez = sx * 0.031 * hk, hc.z - 0.007 * hk
        hit = bvh_head.ray_cast(Vector((ex, -0.5, ez)), Vector((0, 1, 0)))
        r = 0.0118 * hk
        cy = (hit[0].y if hit[0] is not None else hc.y - 0.08) - 0.0015 + r
        eye = nb.uv_sphere("Eye", r, (ex, cy, ez), 10, 6)
        parts.append(set_material(eye, mats, "EyeWhite"))
        if sp.v4:   # textured iris (planar UV), lash line + lash card in the Hair colour
            ri = 0.0060 * hk
            iris = nb.uv_sphere("Iris", ri, (ex, cy - r + 0.0013, ez), 10, 5, scale=(1, 0.42, 1))
            iris["uv"] = "iris:%f,%f,%f" % (ex, ez, ri)
            parts.append(set_material(iris, mats, "Eyes"))
            ll = lash_line(Vector((ex, cy, ez)), r, sx, hk, mats)
            parts.append(set_material(ll, mats, "Hair"))
            parts.append(lash_cards(Vector((ex, cy, ez)), r, sx, hk, mats, female))
        else:
            iris = nb.uv_sphere("Iris", 0.0058 * hk, (ex, cy - r + 0.0012, ez), 8, 4, scale=(1, 0.45, 1))
            parts.append(set_material(iris, mats, "Eyes"))
            parts.append(lash_line(Vector((ex, cy, ez)), r, sx, hk, mats))
        # eyebrow: tapered slab following the brow surface (thicker than v2: reads from 10 m)
        n = 7
        top, bot = [], []
        for i in range(n):
            u = i / (n - 1)
            x = sx * (0.010 + 0.044 * u) * hk
            z = hc.z + (0.0165 + 0.0065 * math.sin(math.pi * u * 0.9) - 0.0065 * u) * hk
            w = (0.0050 - 0.0024 * u) * hk * (0.78 if female else 1.0)
            hu = bvh_head.ray_cast(Vector((x, -0.5, z + w)), Vector((0, 1, 0)))
            hd = bvh_head.ray_cast(Vector((x, -0.5, z - w)), Vector((0, 1, 0)))
            if hu[0] is None or hd[0] is None:
                continue
            top.append((hu[0], hu[1]))
            bot.append((hd[0], hd[1]))
        verts, faces = [], []
        th_b = 0.0024 if female else 0.0031
        for i, ((pt, nt), (pb, nbm)) in enumerate(zip(top, bot)):
            tb = th_b * (0.55 + 0.45 * math.sin(math.pi * (0.15 + 0.85 * i / max(1, len(top) - 1))))
            verts += [pt + nt * 0.0006, pb + nbm * 0.0006, pb + nbm * tb * 0.8, pt + nt * tb]
        for i in range(len(top) - 1):
            a, b = 4 * i, 4 * (i + 1)
            faces += [(a + 3, a + 2, b + 2, b + 3), (a, a + 3, b + 3, b), (a + 2, a + 1, b + 1, b + 2)]
        m = len(top) - 1
        faces += [(0, 1, 2, 3), (4 * m + 3, 4 * m + 2, 4 * m + 1, 4 * m)]
        brow = nb.mesh_object("Brow", verts, faces)
        bmb = bmesh.new()
        bmb.from_mesh(brow.data)
        bmesh.ops.recalc_face_normals(bmb, faces=bmb.faces)
        bmb.to_mesh(brow.data)
        bmb.free()
        parts.append(set_material(brow, mats, "Hair"))

    # ------------------------------------------------ hats / ponytail / bun tie / head accessories
    if sp.hat:
        bvh_hh = bvh_of([head] + hair_parts)
        for o in (make_cap(sp, bvh_hh, mats) if sp.hat == "cap" else make_bucket(sp, bvh_hh, mats)):
            o["uv"] = "box:Hat"
            special[o.name] = "head"
            parts.append(o)
        trim_under_hat(hair_parts[0], sp)
    if "sunglasses" in sp.extras:
        bvh_hh = bvh_of([head] + hair_parts)
        for o in make_sunglasses(sp, bvh_hh, mats):
            special[o.name] = "head"
            parts.append(o)
    if "earrings" in sp.extras:
        for o in make_earrings(sp, mats):
            special[o.name] = "head"
            parts.append(o)
    if sp.hair == "bun":                     # scrunchie at the base of the bun
        c = hc + Vector((0, 0.030, 0.097)) * hk
        ring = [c + Vector((math.cos(a) * 0.050, math.sin(a) * 0.048, 0)) * hk
                for a in (2 * math.pi * i / 14 for i in range(15))]
        o = tube("Tie", ring, [0.0065 * hk] * 15, 4, mats, "Trim", cap_end=False)
        special[o.name] = "head"
        parts.append(o)
    if sp.hair == "ponytail":
        bvh_av = bvh_of([head] + list(pieces.values()))
        for o in make_ponytail(sp, bvh_av, mats):
            if o.name.startswith("Tie"):
                special[o.name] = "head"
                o["uv"] = "box:Shirt"
            parts.append(o)

    print("[human] parts:", ", ".join("%s=%d" % (o.name, nb.tri_count(o)) for o in parts))
    parts += make_lips(bvh_head, hc, hk, female, mats)
    assign_uvs(parts, sp)
    # vertex ranges of the parts that need special skin weights (join keeps the vertex order)
    ranges, off = [], 0
    for o in parts:
        nv = len(o.data.vertices)
        if o.name in special:
            ranges.append((special[o.name], off, off + nv))
        off += nv
    body = nb.join(parts, "Body")
    bm = bmesh.new()
    bm.from_mesh(body.data)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    bm.to_mesh(body.data)
    bm.free()
    nb.auto_smooth(body, 75)

    # ------------------------------------------------ skin weights
    armobj = build_armature(sp)
    bone_names = [b[0] for b in BONES]
    groups = {n: body.vertex_groups.new(name=n) for n in bone_names}
    me = body.data
    co = np.array([v.co for v in me.vertices])
    vmat = np.zeros(len(co), dtype=int)
    for p in me.polygons:
        for vi in p.vertices:
            vmat[vi] = p.material_index
    F = np.clip(fields(weight_E, co), 0, None)
    wb = [e["bone"] for e in weight_E]
    bidx = {n: i for i, n in enumerate(bone_names)}
    W = np.zeros((len(co), len(bone_names)))
    for j, b in enumerate(wb):
        W[:, bidx[b]] += F[:, j]
    hair_i, eyes_i, shirt_i = ORDER.index("Hair"), ORDER.index("Eyes"), ORDER.index("Shirt")
    white_i, hat_i = ORDER.index("EyeWhite"), ORDER.index("Hat")
    pants_i, shoes_i = ORDER.index("Pants"), ORDER.index("Shoes")
    trim_i, sole_i = ORDER.index("Trim"), ORDER.index("Sole")
    arm_bones = [b for b in bone_names if b.startswith(("UpperArm", "LowerArm", "Hand", "Thumb", "Fingers"))]
    neck_axis = np.array([0, 0.022])
    rule = np.array([""] * len(co), dtype=object)
    for name, a, b in ranges:
        rule[a:b] = name
    for i in range(len(co)):
        c = co[i]
        if rule[i] == "chest":                           # chain / lanyard / whistle
            keep = [bidx[b] for b in ("Chest", "Neck", "Spine")]
            sub = W[i, keep].copy()
            W[i] = 0
            W[i, keep] = sub
            if W[i].sum() < 1e-6:
                W[i, bidx["Chest"]] = 1.0
            continue
        if rule[i] == "legs":                            # jogger stripes, cords: never the arms
            for b in arm_bones:
                W[i, bidx[b]] = 0
        if rule[i] == "skirt":
            # hips near the waist, more and more the leg of its side towards the hem
            s = min(1.0, max(0.0, (sp.waist - c[2]) / (sp.waist - sp.skirt_hem)))
            legs = 0.78 * s ** 1.2
            wl = min(1.0, max(0.0, 0.5 + c[0] / 0.12))
            W[i] = 0
            W[i, bidx["Hips"]] = 1 - legs
            W[i, bidx["UpperLeg.L"]] = legs * wl
            W[i, bidx["UpperLeg.R"]] = legs * (1 - wl)
        elif vmat[i] in (hair_i, eyes_i, white_i, hat_i) or rule[i] == "head":
            W[i] = 0
            z = c[2]
            zh = J["head"].z
            if z > zh - 0.005 or not female or rule[i] == "head":
                W[i, bidx["Head"]] = 1.0
            elif z > zh - 0.085 * k:
                t = (zh - 0.005 - z) / (0.08 * k)
                W[i, bidx["Head"]] = 1 - t
                W[i, bidx["Neck"]] = t
            else:
                t = min(1.0, (zh - 0.085 * k - z) / (0.07 * k))
                W[i, bidx["Neck"]] = 1 - t
                W[i, bidx["Chest"]] = t
        elif vmat[i] == shirt_i and c[2] > 1.40 * k and np.hypot(*(c[:2] - neck_axis)) < (0.10 if st else 0.085):
            for b in bone_names:                         # collar / hood: chest / neck only
                if b not in ("Neck", "Chest", "Spine"):
                    W[i, bidx[b]] = 0
            if W[i].sum() < 1e-6:
                W[i, bidx["Chest"]] = 1.0
        elif vmat[i] in (pants_i, shoes_i):              # trousers / skirt / belt never follow the arms
            for b in arm_bones:
                W[i, bidx[b]] = 0
        if W[i].sum() < 1e-6:                            # outside every element: nearest bone
            best, bd = "Hips", 9.0
            no_arms = vmat[i] in (pants_i, shoes_i, trim_i, sole_i) or rule[i] == "legs"
            for name, h, t, _ in BONES:
                if no_arms and name in arm_bones:        # waistbands / soles never follow the hands
                    continue
                a, b = np.array(J[h]), np.array(J[t])
                ab = b - a
                hh = np.clip((c - a) @ ab / (ab @ ab), 0, 1)
                d = np.linalg.norm(c - (a + hh * ab))
                if d < bd:
                    best, bd = name, d
            W[i, bidx[best]] = 1.0
    # v4: the torso is skinned by height (Hips -> Spine -> Chest) instead of by the dominant
    # field: shirt and trousers share the same weights at the waist, so hip sways / body waves
    # (Dance, Dance2, Sit) no longer open a gap between the top and the waistband.
    tb = [bidx["Hips"], bidx["Spine"], bidx["Chest"]]
    zA, zB, zC = sp.waist - 0.05 * k, 1.13 * k, 1.31 * k
    for i in range(len(co)):
        c = co[i]
        tot = W[i].sum()
        tor = W[i, tb].sum()
        if tot < 1e-9 or tor < 0.55 * tot or abs(c[0]) > 0.24 or not (zA - 0.08 < c[2] < zC + 0.02):
            continue
        if rule[i] in ("skirt", "head", "chest") or vmat[i] in (hair_i, eyes_i, white_i, hat_i):
            continue
        z = c[2]
        if z <= zA:
            wh, ws, wc = 1.0, 0.0, 0.0
        elif z <= zB:
            t = smooth((z - zA) / (zB - zA))
            wh, ws, wc = 1 - t, t, 0.0
        else:
            t = smooth((z - zB) / (zC - zB))
            wh, ws, wc = 0.0, 1 - t, t
        if z < zA:                                       # below the waist: legs keep their share
            continue
        W[i, tb] = np.array([wh, ws, wc]) * tor
    for i in range(len(co)):
        order = np.argsort(-W[i])[:4]
        tot = W[i, order].sum()
        for j in order:
            w = W[i, j] / tot
            if w > 0.02:
                groups[bone_names[j]].add([i], float(w), "REPLACE")
    body.parent = armobj
    mod = body.modifiers.new("Armature", "ARMATURE")
    mod.object = armobj
    tris = nb.tri_count(body)
    make_actions(armobj, sp)
    path = nb.export_glb(sp.name, animations=True, texcoords=True)
    return path, tris


# --------------------------------------------------------------------------- armature
BONES = [
    ("Hips", "hips", "spine", None),
    ("Spine", "spine", "chest", "Hips"),
    ("Chest", "chest", "neck", "Spine"),
    ("Neck", "neck", "head", "Chest"),
    ("Head", "head", "top", "Neck"),
]
for _s in ("L", "R"):
    BONES += [
        ("UpperArm." + _s, "sho" + _s, "elb" + _s, "Chest"),
        ("LowerArm." + _s, "elb" + _s, "wri" + _s, "UpperArm." + _s),
        ("Hand." + _s, "wri" + _s, "fin" + _s, "LowerArm." + _s),
        ("Thumb." + _s, "tb" + _s, "tm" + _s, "Hand." + _s),
        ("Thumb2." + _s, "tm" + _s, "tt" + _s, "Thumb." + _s),
        ("Fingers." + _s, "fk" + _s, "fm" + _s, "Hand." + _s),
        ("Fingers2." + _s, "fm" + _s, "ft" + _s, "Fingers." + _s),
        ("UpperLeg." + _s, "hip" + _s, "kne" + _s, "Hips"),
        ("LowerLeg." + _s, "kne" + _s, "ank" + _s, "UpperLeg." + _s),
        ("Foot." + _s, "ank" + _s, "toe" + _s, "LowerLeg." + _s),
    ]


def build_armature(sp):
    arm = bpy.data.armatures.new("Armature")
    obj = nb.link(bpy.data.objects.new("Armature", arm))
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    for name, h, t, parent in BONES:
        b = arm.edit_bones.new(name)
        b.head = sp.J[h]
        b.tail = sp.J[t]
        b.roll = 0.0
        if parent:
            b.parent = arm.edit_bones[parent]
            b.use_connect = (arm.edit_bones[parent].tail - b.head).length < 1e-4
    bpy.ops.object.mode_set(mode="OBJECT")
    for pb in obj.pose.bones:
        pb.rotation_mode = "QUATERNION"
    return obj


# --------------------------------------------------------------------------- pose maths
# A pose is a dict bone -> (pitch, out, yaw) in degrees, expressed in armature axes
# and relative to the parent (pitch about X: negative = forward for a hanging limb,
# positive = bend the knee; out about Y; yaw about Z), or directly a 3x3 Matrix
# (same convention, produced by the IK helpers). '_loc' = armature-space hips offset.
class Rig:
    def __init__(self, armobj, sp):
        self.sp = sp
        self.parent = {n: p for n, _, _, p in BONES}
        self.head = {n: sp.J[h].copy() for n, h, _, _ in BONES}
        self.tail = {n: sp.J[t].copy() for n, _, t, _ in BONES}
        self.M = {pb.name: pb.bone.matrix_local.to_3x3() for pb in armobj.pose.bones}


RIG = None


def rmat(v):
    if isinstance(v, Matrix):
        return v
    p, o, y = v
    return (Matrix.Rotation(math.radians(y), 3, "Z") @ Matrix.Rotation(math.radians(p), 3, "X")
            @ Matrix.Rotation(math.radians(o), 3, "Y"))


def fk(pose):
    G, Hd = {}, {}
    for name, _, _, parent in BONES:
        R = rmat(pose.get(name, (0, 0, 0)))
        if parent is None:
            G[name] = R
            Hd[name] = RIG.head[name] + Vector(pose.get("_loc", (0, 0, 0)))
        else:
            G[name] = G[parent] @ R
            Hd[name] = Hd[parent] + G[parent] @ (RIG.head[name] - RIG.head[parent])
    return G, Hd


def frame(a, b):
    a = a.normalized()
    b = (b - a * b.dot(a)).normalized()
    return Matrix((a, b, a.cross(b))).transposed()


def ik(pose, upper, lower, target, pole, hinge):
    """Two-bone IK: sets pose[upper], pose[lower] so the end of `lower` reaches target.
    hinge = rest bend axis (knee: +X, elbow: -X). Returns the world delta of `lower`."""
    G, Hd = fk(pose)
    Gp = G[RIG.parent[upper]]
    S = Hd[upper]
    S0, E0, W0 = RIG.head[upper], RIG.head[lower], RIG.tail[lower]
    L1, L2 = (E0 - S0).length, (W0 - E0).length
    D = Vector(target) - S
    d = max(abs(L1 - L2) + 1e-3, min(D.length, (L1 + L2) * 0.9995))
    dd = D.normalized()
    pp = Vector(pole) - dd * Vector(pole).dot(dd)
    pp.normalize()
    a = (L1 * L1 + d * d - L2 * L2) / (2 * d)
    h = math.sqrt(max(0.0, L1 * L1 - a * a))
    E = S + dd * a + pp * h
    T = S + dd * d
    u1, u2 = (E - S).normalized(), (T - E).normalized()
    n = pp.cross(dd).normalized()
    if Vector(hinge).x < 0:
        n = -n
    u10, u20 = (E0 - S0).normalized(), (W0 - E0).normalized()
    n0 = Vector(hinge)
    Gu = frame(u1, n) @ frame(u10, n0).transposed()
    Gl = frame(u2, n) @ frame(u20, n0).transposed()
    pose[upper] = Gp.transposed() @ Gu
    pose[lower] = Gu.transposed() @ Gl
    return Gl


def orient_end(pose, end, Gl, Gwant):
    pose[end] = Gl.transposed() @ Gwant


def hand_world(side, direction, thumb):
    """World delta that points Hand.<side> along `direction` with the thumb towards `thumb`."""
    h0 = (RIG.tail["Hand." + side] - RIG.head["Hand." + side]).normalized()
    t0 = Vector((0, -1, 0))
    return frame(Vector(direction), Vector(thumb)) @ frame(h0, t0).transposed()


def foot_target(side, y, theta, x=None, lift=0.0, yaw=0.0):
    """Ankle position for a foot whose flat reference sits at y (forward = -y) and is pitched
    by theta degrees (negative = toes up, pivot on the heel; positive = heel up, on the ball)."""
    sp = RIG.sp
    ank = sp.J["ank" + side]
    k = sp.k
    az = ank.z
    if x is None:
        x = ank.x
    flat = Vector((x, y, az + lift))
    r = Vector((0, 0.05 * k, -az)) if theta < 0 else Vector((0, -0.125 * k, -az))
    R = Matrix.Rotation(math.radians(theta), 3, "X")
    pos = flat + r + R @ (-r)
    G = Matrix.Rotation(math.radians(yaw), 3, "Z") @ R
    return pos, G


def leg_ik(p, side, y, theta, x=None, lift=0.0, yaw=0.0, pole=None):
    pos, Gf = foot_target(side, y, theta, x, lift, yaw)
    sx = 1 if side == "L" else -1
    Gl = ik(p, "UpperLeg." + side, "LowerLeg." + side, pos, pole or Vector((sx * 0.12, -1, 0)),
            Vector((1, 0, 0)))
    orient_end(p, "Foot." + side, Gl, Gf)


def arm_ik(p, side, wrist, pole, hand_dir=None, thumb=None):
    Gl = ik(p, "UpperArm." + side, "LowerArm." + side, wrist, pole, Vector((-1, 0, 0)))
    if hand_dir is not None:
        orient_end(p, "Hand." + side, Gl, hand_world(side, hand_dir, thumb))


def pose_quat(pb, v):
    M = pb.bone.matrix_local.to_3x3()
    return (M.inverted() @ rmat(v) @ M).to_quaternion()


def key_pose(armobj, frame_, pose):
    for pb in armobj.pose.bones:
        pb.rotation_quaternion = pose_quat(pb, pose.get(pb.name, (0, 0, 0)))
        pb.keyframe_insert("rotation_quaternion", frame=frame_, group=pb.name)
        if pb.name == "Hips":
            M = pb.bone.matrix_local.to_3x3()
            pb.location = M.inverted() @ Vector(pose.get("_loc", (0, 0, 0)))
            pb.keyframe_insert("location", frame=frame_, group=pb.name)


def legs(pose, side, hip, knee, foot_world=0.0, out=0.0):
    pose["UpperLeg." + side] = (hip, out, 0)
    pose["LowerLeg." + side] = (knee, 0, 0)
    pose["Foot." + side] = (foot_world - hip - knee, 0, 0)


ARM_DOWN = 18  # degrees from the A-pose towards the body


def arms(pose, side, swing, elbow, down=ARM_DOWN, yaw=0.0, hand=0.0):
    sx = 1 if side == "L" else -1
    pose["UpperArm." + side] = (swing, sx * down, sx * yaw)
    pose["LowerArm." + side] = (-elbow, 0, 0)
    pose["Hand." + side] = (hand, 0, 0)


def fingers(p, side, f1, f2, t1=0.0, t2=0.0, opp=0.0):
    """Finger pose (degrees): f1 knuckles, f2 middle joints (+ = curl into the palm), t1 / t2 thumb
    base / tip flexion towards the palm, opp = thumb rotation about the hand axis (opposition)."""
    hd = RIG.sp.hand[side]
    sx = 1 if side == "L" else -1
    p["Fingers." + side] = Matrix.Rotation(math.radians(f1), 3, hd["bend"])
    p["Fingers2." + side] = Matrix.Rotation(math.radians(f2), 3, hd["bend"])
    p["Thumb." + side] = (Matrix.Rotation(math.radians(opp * sx), 3, hd["uh"]) @
                          Matrix.Rotation(math.radians(t1), 3, hd["tbend"]))
    p["Thumb2." + side] = Matrix.Rotation(math.radians(t2), 3, hd["tbend"])


HAND_RELAXED = (16, 20, 4, 10, 0)        # every clip except Aim / AimRifle / Punch
HAND_GRIP = (62, 92, 22, 30, -10)        # right hand closed on a pistol grip (Aim, AimRifle)
HAND_SUPPORT = (28, 44, 6, 10, 10)       # left hand under a handguard (AimRifle)
HAND_FIST = (88, 104, 34, 40, 22)        # Punch


def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def hermite(a, b, s, ma=0.0, mb=0.0):
    s2, s3 = s * s, s * s * s
    return (2 * s3 - 3 * s2 + 1) * a + (s3 - 2 * s2 + s) * ma + (-2 * s3 + 3 * s2) * b + (s3 - s2) * mb


def catmull(keys, s):
    """keys: [(s_i, (values...)), ...] sorted, s in [keys[0].s, keys[-1].s]."""
    for i in range(len(keys) - 1):
        if s <= keys[i + 1][0] or i == len(keys) - 2:
            break
    s0, v0 = keys[i]
    s1, v1 = keys[i + 1]
    vm = keys[i - 1][1] if i > 0 else tuple(2 * a - b for a, b in zip(v0, v1))
    vp = keys[i + 2][1] if i + 2 < len(keys) else tuple(2 * b - a for a, b in zip(v0, v1))
    u = (s - s0) / max(1e-6, s1 - s0)
    out = []
    for a, b, c, d in zip(vm, v0, v1, vp):
        out.append(0.5 * ((2 * b) + (-a + c) * u + (2 * a - 5 * b + 4 * c - d) * u * u
                          + (-a + 3 * b - 3 * c + d) * u * u * u))
    return out


# --------------------------------------------------------------------------- clips
def idle_pose(t):
    ph = 2 * math.pi * t
    b = math.sin(ph)
    p = {"_loc": (0.004 * math.sin(ph + 0.6), 0, -0.006 + 0.003 * b)}
    p["Hips"] = (0, -1.0 * math.sin(ph + 0.6), 0)
    p["Spine"] = (1.0 + 0.6 * b, 0, 0)
    p["Chest"] = (-1.0 - 1.2 * b, 0, 0)
    p["Neck"] = (2, 0, 0)
    p["Head"] = (-1 + 0.8 * b, 0, 2.5 * math.sin(ph))
    arms(p, "L", 2 + 1.5 * b, 10 + 2 * b)
    arms(p, "R", 2 - 1.5 * b, 10 - 2 * b)
    leg_ik(p, "L", 0.0, 0.0, x=RIG.sp.J["ankL"].x + 0.008, yaw=8)
    leg_ik(p, "R", 0.02, 0.0, x=RIG.sp.J["ankR"].x - 0.008, yaw=-10)
    return p


def gait(t, duty, y_contact, y_off, th_contact, th_flat_in, th_flat_out, th_off, swing_fn):
    """Foot state (y, theta, lift) for phase t of one leg: stance [0, duty), swing [duty, 1)."""
    if t < duty:
        s = t / duty
        y = y_contact + (y_off - y_contact) * s
        if s < th_flat_in:
            th = th_contact * (1 - smooth(s / th_flat_in))
        elif s < th_flat_out:
            th = 0.0
        else:
            th = th_off * smooth((s - th_flat_out) / (1 - th_flat_out)) ** 1.3
        return y, th, 0.0
    return swing_fn((t - duty) / (1 - duty))


WALK = dict(duty=0.6, yc=-0.25, yo=0.33, thc=-14.0, thi=0.16, tho=0.55, tho_end=38.0)


def walk_pose(t):
    sp = RIG.sp
    k = sp.k
    w = WALK
    yc, yo = w["yc"] * k, w["yo"] * k
    p = {}
    ph = 2 * math.pi * t
    p["_loc"] = (0.016 * math.sin(ph), 0.0, -0.012 * k - 0.009 * math.cos(2 * ph))
    p["Hips"] = (2, -2.5 * math.sin(ph), -5 * math.cos(ph))
    p["Spine"] = (3, 1.5 * math.sin(ph), 3 * math.cos(ph))
    p["Chest"] = (1 - 0.6 * math.cos(2 * ph), 1.0 * math.sin(ph), 3.5 * math.cos(ph))
    p["Neck"] = (1, 0, -0.8 * math.cos(ph))
    p["Head"] = (-3 + 1.2 * math.cos(2 * ph), 0, -0.8 * math.cos(ph))

    def swing(s):
        y = hermite(yo, yc, smooth(s), 0, 0)
        th = hermite(w["tho_end"], w["thc"], s, -40, 10)
        lift = 0.075 * k * math.sin(math.pi * min(1.0, s * 1.15)) ** 1.2
        return y, th, lift
    for side, o in (("L", 0.0), ("R", 0.5)):
        sx = 1 if side == "L" else -1
        tt = (t + o) % 1.0
        y, th, lift = gait(tt, w["duty"], yc, yo, w["thc"], w["thi"], w["tho"], w["tho_end"], swing)
        leg_ik(p, side, y, th, x=sx * 0.088 * k, lift=lift, yaw=sx * 6)
        a = 2 * math.pi * ((t + o - 0.04) % 1.0)
        fwd = -math.cos(a)                      # +1 when this arm swings forward (opposite leg)
        arms(p, side, -17 * fwd + 3, 14 + 14 * max(0.0, fwd) + 4 * math.sin(a), down=ARM_DOWN + 1,
             yaw=-4 * max(0.0, fwd), hand=-4)
    return p


RUN = dict(duty=0.36, yc=-0.20, yo=0.38)


def run_pose(t):
    sp = RIG.sp
    k = sp.k
    p = {}
    ph = 2 * math.pi * t
    p["_loc"] = (0.01 * math.sin(ph), 0.0, -0.062 * k - 0.024 * math.cos(4 * math.pi * (t - 0.17)))
    p["Hips"] = (7, -2 * math.sin(ph), -8 * math.cos(ph))
    p["Spine"] = (5, 1.5 * math.sin(ph), 5 * math.cos(ph))
    p["Chest"] = (3, 0, 5 * math.cos(ph))
    p["Neck"] = (-4, 0, -1 * math.cos(ph))
    p["Head"] = (-6, 0, -1 * math.cos(ph))
    yc, yo = RUN["yc"] * k, RUN["yo"] * k

    def swing(s):
        keys = [(0.0, (yo + 0.0, 50.0, 0.0)), (0.25, (0.44 * k, 38.0, 0.22 * k)), (0.52, (0.10 * k, 8.0, 0.30 * k)),
                (0.80, (-0.24 * k, -14.0, 0.13 * k)), (1.0, (yc, -6.0, 0.0))]
        y, th, lift = catmull(keys, s)
        return y, th, max(0.0, lift)
    for side, o in (("L", 0.0), ("R", 0.5)):
        sx = 1 if side == "L" else -1
        tt = (t + o) % 1.0
        y, th, lift = gait(tt, RUN["duty"], yc, yo, -6.0, 0.2, 0.42, 50.0, swing)
        leg_ik(p, side, y, th, x=sx * 0.075 * k, lift=lift, yaw=sx * 4)
        a = 2 * math.pi * ((t + o - 0.03) % 1.0)
        fwd = -math.cos(a)
        arms(p, side, -26 * fwd + 14, 80 + 14 * fwd, down=ARM_DOWN - 4, yaw=-12, hand=-8)
    return p


def guard(p, twist=0.0):
    arms(p, "L", -40, 98, down=12, yaw=-16, hand=-10)
    arms(p, "R", -32, 106, down=12, yaw=-18, hand=-10)
    legs(p, "L", -16, 16, 0, out=-3)
    legs(p, "R", 10, 12, 0, out=3)
    p["_loc"] = (0, 0, -0.03)
    p["Hips"] = (0, 0, twist * 0.4 - 10)
    p["Spine"] = (5, 0, twist * 0.3)
    p["Chest"] = (3, 0, twist * 0.3)
    p["Head"] = (-6, 0, 8 - twist * 0.6)
    return p


def punch_pose(t):
    # 0 guard -> .25 wind-up -> .42 full extension (right jab-cross) -> 1 back to guard
    p = _punch_pose(t)
    for sd in ("L", "R"):
        fingers(p, sd, *HAND_FIST)
    return p


def _punch_pose(t):
    p = guard({})
    if t < 0.25:
        k = t / 0.25
        p = guard({}, twist=-10 * k)
    elif t < 0.42:
        k = smooth((t - 0.25) / 0.17)
        p = guard({}, twist=-10 + 42 * k)
        arms(p, "R", -32 - 56 * k, 106 * (1 - k) + 4 * k, down=12 + 4 * k, yaw=-18 - 4 * k, hand=-10 + 10 * k)
        arms(p, "L", -40 + 6 * k, 98 + 14 * k, down=12, yaw=-16, hand=-10)
    else:
        k = smooth((t - 0.42) / 0.58)
        p = guard({}, twist=32 * (1 - k))
        arms(p, "R", -88 + 56 * k, 4 + 102 * k, down=16 - 4 * k, yaw=-22 + 4 * k, hand=0 - 10 * k)
        arms(p, "L", -34 - 6 * k, 112 - 14 * k, down=12, yaw=-16, hand=-10)
    return p


def death_pose(t):
    """Hit, knees buckle, fall on the back, settle."""
    keys = [0.0, 0.12, 0.3, 0.55, 0.66, 0.75, 1.0]

    def at(vals):
        for i in range(len(keys) - 1):
            if t <= keys[i + 1]:
                k = smooth((t - keys[i]) / (keys[i + 1] - keys[i]))
                return vals[i] + (vals[i + 1] - vals[i]) * k
        return vals[-1]
    p = {}
    hip_pitch = at([0, 6, -25, -86, -91, -89, -90])
    drop = at([0, -0.05, -0.32, -0.78, -0.86, -0.84, -0.855])
    back = at([0, 0.03, 0.16, 0.34, 0.4, 0.4, 0.4])
    p["_loc"] = (0, back, drop * RIG.sp.k)
    p["Hips"] = (hip_pitch, 0, at([0, 4, 8, 6, 5, 5, 5]))
    p["Spine"] = (at([0, 14, 4, -4, 0, 0, 0]), 0, 0)
    p["Chest"] = (at([0, 10, -2, -6, 2, 1, 0]), 0, 0)
    p["Neck"] = (at([0, -18, -10, 6, -4, -2, 0]), 0, 0)
    p["Head"] = (at([0, -20, -8, 10, -6, -4, -4]), 0, at([0, 0, 10, 20, 28, 30, 30]))
    kl = at([4, 40, 70, 30, 20, 22, 25])
    legs(p, "L", at([-2, -20, -40, -6, 0, -4, -8]), kl, 0, out=at([0, -2, -5, -10, -12, -12, -12]))
    legs(p, "R", at([2, -10, -25, 4, 6, 4, 2]), at([3, 30, 50, 15, 8, 10, 10]), 0, out=at([0, 2, 5, 8, 9, 9, 9]))
    arms(p, "L", at([2, -40, -70, -20, 4, 6, 8]), at([10, 50, 30, 15, 8, 10, 12]),
         down=at([ARM_DOWN, 10, -20, -45, -55, -52, -50]))
    arms(p, "R", at([2, -30, -80, -30, 2, 4, 6]), at([10, 60, 40, 20, 12, 14, 15]),
         down=at([ARM_DOWN, 5, -25, -40, -48, -46, -45]))
    return p


def aim_pose(t):
    """One-handed aim: right arm straight forward at shoulder height (pistol)."""
    sp = RIG.sp
    k = sp.k
    ph = 2 * math.pi * t
    b = math.sin(ph)
    p = {"_loc": (0.003 * math.sin(ph + 0.5), 0.0, -0.016 * k + 0.002 * b)}
    p["Hips"] = (0, 0, 12)
    p["Spine"] = (2 + 0.4 * b, 0, 3)
    p["Chest"] = (-1 - 0.8 * b, 0, 5)
    p["Neck"] = (0, 0, -9)
    p["Head"] = (-2 + 0.5 * b, -2, -11)
    leg_ik(p, "L", -0.07 * k, 0.0, x=0.13 * k, yaw=14, pole=Vector((0.25, -1, 0)))
    leg_ik(p, "R", 0.07 * k, 0.0, x=-0.10 * k, yaw=-8, pole=Vector((-0.1, -1, 0)))
    arms(p, "L", 6 + 1.0 * b, 14 + 1.5 * b, down=ARM_DOWN - 2)
    G, Hd = fk(p)
    S = Hd["UpperArm.R"]
    reach = (RIG.head["Hand.R"] - RIG.head["UpperArm.R"]).length
    wrist = S + Vector((0.06 * k, -reach * 0.985, 0.012 + 0.003 * b))
    arm_ik(p, "R", wrist, Vector((-0.4, 0.2, -1)), Vector((0.02, -1, -0.04)), Vector((0.12, 0, 1)))
    fingers(p, "R", *HAND_GRIP)
    return p


def aim_rifle_pose(t):
    """Two-handed aim: stock in the right shoulder pocket, left hand under the handguard."""
    sp = RIG.sp
    k = sp.k
    ph = 2 * math.pi * t
    b = math.sin(ph)
    p = {"_loc": (0.003 * math.sin(ph + 0.5), 0.012, -0.03 * k + 0.002 * b)}
    p["Hips"] = (2, 0, -28)
    p["Spine"] = (4 + 0.4 * b, 0, 4)
    p["Chest"] = (2 - 0.6 * b, 0, 2)
    p["Neck"] = (6, 0, 10)
    p["Head"] = (6 + 0.4 * b, -7, 11)
    leg_ik(p, "L", -0.17 * k, 0.0, x=0.06 * k, yaw=-8, pole=Vector((0.2, -1, 0)))
    leg_ik(p, "R", 0.13 * k, 0.0, x=-0.17 * k, yaw=-48, pole=Vector((-0.5, -1, 0)))
    G, Hd = fk(p)
    S = Hd["UpperArm.R"]
    fwd = Vector((0, -1, 0))
    up = Vector((0, 0, 1))
    butt = S + Vector((0.075 * k, -0.06 * k, -0.005)) + up * (0.002 * b)   # shoulder pocket
    grip = butt + fwd * (0.30 * k) - up * 0.085
    fore = butt + fwd * (0.58 * k) - up * 0.045 + Vector((0.008, 0, 0))
    hdR = Vector((0.12, -0.55, -0.82)).normalized()
    hdL = Vector((-0.30, -0.90, 0.05)).normalized()
    arm_ik(p, "R", grip - hdR * (0.075 * k) + Vector((-0.012, 0, 0)), Vector((-0.6, 0.15, -0.8)),
           hdR, Vector((0.35, -0.8, 0.3)))
    arm_ik(p, "L", fore - hdL * (0.07 * k) + Vector((0, 0, -0.004)), Vector((0.45, 0.0, -1)),
           hdL, Vector((-0.1, -0.35, 1)))
    fingers(p, "R", *HAND_GRIP)
    fingers(p, "L", *HAND_SUPPORT)
    return p


def crouch_pose(t):
    """Low crouch: left foot flat in front, right knee close to the ground on the toes."""
    sp = RIG.sp
    k = sp.k
    ph = 2 * math.pi * t
    b = math.sin(ph)
    p = {"_loc": (0.0, 0.07, -0.47 * k + 0.004 * b)}
    p["Hips"] = (22, 0, -6)
    p["Spine"] = (8 + 1.2 * b, 0, 2)
    p["Chest"] = (3 - 1.5 * b, 0, 2)
    p["Neck"] = (-14, 0, 1)
    p["Head"] = (-16 + 0.8 * b, 0, 1)
    leg_ik(p, "L", -0.26 * k, 0.0, x=0.13 * k, yaw=10, pole=Vector((0.25, -1, 0.1)))
    leg_ik(p, "R", 0.36 * k, 72.0, x=-0.11 * k, yaw=-6, pole=Vector((-0.05, -0.25, -1)))
    arms(p, "L", -26 + 1.5 * b, 52, down=ARM_DOWN + 2, yaw=6, hand=-10)
    arms(p, "R", -12 + 1.5 * b, 46, down=ARM_DOWN + 2, yaw=4, hand=-10)
    return p


HAND_LOOSE_FIST = (55, 70, 18, 20, 10)   # dancing
HAND_OPEN = (6, 8, 0, 4, 0)              # waving hands


def dance_pose(t):
    """Baile funk groove (2 s, 4 beats at 120 bpm): knees bounce down on every beat, hips sway
    side to side (2 sways), chest counter-rotates, fists pump forward/up in alternation."""
    sp = RIG.sp
    k = sp.k
    ph = 2 * math.pi * t
    beat = 0.5 + 0.5 * math.cos(4 * ph)                   # 1 on the beat (down)
    sway = math.sin(2 * ph)
    p = {"_loc": (0.045 * sway, 0.01, -0.055 * k - 0.040 * k * beat)}
    p["Hips"] = (6 + 4 * beat, 9 * sway, 10 * math.sin(ph))
    p["Spine"] = (4 - 3 * beat, -5 * sway, -4 * math.sin(ph))
    p["Chest"] = (2 + 3 * beat, -5 * sway, -6 * math.sin(ph))
    p["Neck"] = (-2, 2 * sway, 0)
    p["Head"] = (-4 + 7 * beat, 3 * sway, 4 * math.sin(ph))
    leg_ik(p, "L", -0.02 * k, 0.0, x=0.165 * k, yaw=16, pole=Vector((0.45, -1, 0)))
    leg_ik(p, "R", 0.02 * k, 0.0, x=-0.165 * k, yaw=-16, pole=Vector((-0.45, -1, 0)))
    for side, o in (("L", 0.0), ("R", 0.5)):
        pump = 0.5 + 0.5 * math.cos(2 * ph * 2 + o * 2 * math.pi)          # one pump per second
        arms(p, side, -38 - 42 * pump, 95 - 35 * pump, down=8 - 6 * pump, yaw=-14 - 8 * pump, hand=-10 + 12 * pump)
        fingers(p, side, *HAND_LOOSE_FIST)
    return p


def dance2_pose(t):
    """Second groove (2 s): body wave (spine / chest / neck in cascade), weight shifting from one
    foot to the other with the heel lifting, both hands up waving over the head."""
    sp = RIG.sp
    k = sp.k
    ph = 2 * math.pi * t
    sway = math.sin(ph)
    beat = 0.5 + 0.5 * math.cos(4 * ph)
    p = {"_loc": (0.060 * sway, 0.0, -0.035 * k - 0.025 * k * beat)}
    p["Hips"] = (4 + 5 * math.sin(2 * ph), 7 * sway, -6 * sway)
    p["Spine"] = (5 * math.sin(2 * ph - 0.9), -4 * sway, 3 * sway)
    p["Chest"] = (5 * math.sin(2 * ph - 1.8), -4 * sway, 4 * sway)
    p["Neck"] = (4 * math.sin(2 * ph - 2.7), 0, 0)
    p["Head"] = (5 * math.sin(2 * ph - 3.6), 4 * sway, -5 * sway)
    # the unloaded foot lifts its heel
    liftL = max(0.0, -sway) ** 1.5 * 34
    liftR = max(0.0, sway) ** 1.5 * 34
    leg_ik(p, "L", -0.01 * k, liftL, x=0.150 * k, yaw=12, pole=Vector((0.35, -1, 0)))
    leg_ik(p, "R", 0.01 * k, liftR, x=-0.150 * k, yaw=-12, pole=Vector((-0.35, -1, 0)))
    for side, o in (("L", 0.0), ("R", math.pi)):
        sx = 1 if side == "L" else -1
        w = math.sin(2 * ph + o)
        p["UpperArm." + side] = (-25 + 8 * w, sx * (-128 + 14 * w), sx * 10)
        p["LowerArm." + side] = (-(28 + 22 * (0.5 + 0.5 * w)), 0, 0)
        p["Hand." + side] = (10 * w, 0, sx * 12 * w)
        fingers(p, side, *HAND_OPEN)
    return p


def sit_pose(t):
    """Seated on a bench / step (seat ~0.46 m): thighs level, feet flat, forearms on the thighs.
    Loops (2 s) with a slow breath."""
    sp = RIG.sp
    k = sp.k
    ph = 2 * math.pi * t
    b = math.sin(ph)
    hipz = 0.50 * k                                   # hip joints just above a 0.46 m seat
    p = {"_loc": (0.0, 0.06 * k, hipz - sp.J["hipL"].z)}
    p["Hips"] = (-4, 0, 0)
    p["Spine"] = (10 + 0.8 * b, 0, 0)
    p["Chest"] = (6 - 1.0 * b, 0, 0)
    p["Neck"] = (-6, 0, 0)
    p["Head"] = (-6 + 0.6 * b, 0, 3 * math.sin(ph))
    leg_ik(p, "L", -0.36 * k, 0.0, x=0.14 * k, yaw=8, pole=Vector((0.15, -1, 0.3)))
    leg_ik(p, "R", -0.37 * k, 0.0, x=-0.14 * k, yaw=-8, pole=Vector((-0.15, -1, 0.3)))
    G, Hd = fk(p)
    for side in ("L", "R"):
        sx = 1 if side == "L" else -1
        knee = Hd["LowerLeg." + side]
        hipj = Hd["UpperLeg." + side]
        on = hipj.lerp(knee, 0.62) + Vector((sx * 0.012, 0, 0.085 * k + 0.002 * b))
        arm_ik(p, side, on, Vector((sx * 0.7, 0.5, -0.2)), Vector((-sx * 0.15, -1, -0.35)),
               Vector((-sx * 1, -0.1, 0.2)))
    return p


def workout_pose(t):
    """Alternating hammer curls (2 s): left arm in the first second, right in the second;
    upper arms tight on the ribs, fists closed (prop_weights dumbbell can go in the hand)."""
    sp = RIG.sp
    k = sp.k
    ph = 2 * math.pi * t
    p = {"_loc": (0.0, 0.0, -0.012 * k)}
    p["Hips"] = (2, 0, 0)
    p["Spine"] = (2, 0, 0)
    p["Chest"] = (-2 - 1.5 * math.sin(2 * ph), 0, 0)
    p["Neck"] = (2, 0, 0)
    p["Head"] = (2, 0, 0)
    leg_ik(p, "L", 0.0, 0.0, x=0.13 * k, yaw=10)
    leg_ik(p, "R", 0.0, 0.0, x=-0.13 * k, yaw=-10)
    for side, t0 in (("L", 0.0), ("R", 0.5)):
        q = ((t - t0) % 1.0) * 2.0                    # 0..2 ; curl while q < 1
        c = math.sin(math.pi * q) ** 2 if q < 1 else 0.0
        arms(p, side, -6 - 14 * c, 12 + 118 * c, down=ARM_DOWN + 5, yaw=-6, hand=-6 + 18 * c)
        fingers(p, side, *HAND_GRIP)
    p["Spine"] = (2 + 2 * math.sin(4 * ph), 0, 0)
    return p


ACTIONS = [
    # name, frames, pose fn, loop
    ("Idle", 48, idle_pose, True),
    ("Walk", 24, walk_pose, True),
    ("Run", 16, run_pose, True),
    ("Punch", 16, punch_pose, False),
    ("Death", 36, death_pose, False),
    ("Aim", 48, aim_pose, True),
    ("AimRifle", 48, aim_rifle_pose, True),
    ("Crouch", 48, crouch_pose, True),
    # v4 clips (every human): Dance / Dance2 loops for the baile funk scenes, Sit and Workout (prison yard)
    ("Dance", 48, dance_pose, True),
    ("Dance2", 48, dance2_pose, True),
    ("Sit", 48, sit_pose, True),
    ("Workout", 48, workout_pose, True),
]


def make_actions(armobj, sp):
    global RIG
    RIG = Rig(armobj, sp)
    ad = armobj.animation_data_create()
    for name, frames, fn, loop in ACTIONS:
        act = bpy.data.actions.new(name)
        act.use_fake_user = True
        ad.action = act
        step = 2 if (frames > 20 and name not in ("Walk",)) else 1
        fr = list(range(0, frames + 1, step))
        if fr[-1] != frames:
            fr.append(frames)
        for f_ in fr:
            t = f_ / frames
            pose = fn(0.0 if (loop and f_ == frames) else t)
            for sd in ("L", "R"):
                if "Fingers." + sd not in pose:
                    fingers(pose, sd, *HAND_RELAXED)
            key_pose(armobj, f_, pose)
        track = ad.nla_tracks.new()
        track.name = name
        strip = track.strips.new(name, 0, act)
        strip.name = name
        track.mute = True
        ad.action = None
    # reset the pose to rest so the bind pose is exported cleanly
    for pb in armobj.pose.bones:
        pb.rotation_quaternion = Quaternion()
        pb.location = Vector()


if __name__ == "__main__":
    which = sys.argv[1:] or ["m", "f", "m2", "f2", "f3", "m3", "f4", "m4", "m5"]
    for w in which:
        p, t = build_human(w.startswith("f"), w[1:])
        print("[human] %s: %d tris" % (p, t))
