"""Neon Bay - procedural skinned humans with animations (version 2).

    python3 tools/blender/gen_human.py          # human_m + human_f
    python3 tools/blender/gen_human.py f        # only human_f

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
Materials: Skin Shirt Pants Shoes Hair Eyes (+ Lips, optional for the game)
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
ORDER = ["Skin", "Shirt", "Pants", "Shoes", "Hair", "Eyes", "Lips", "EyeWhite", "Hat"]


def surf(s):
    """Surface radius / element radius for a metaball of stiffness s (threshold 0.6)."""
    return math.sqrt(1.0 - (THRESH / s) ** (1.0 / 3.0))


# --------------------------------------------------------------------------- body spec
class Spec:
    def __init__(self, female, variant=""):
        self.female = f = female
        self.variant = variant
        self.stocky = st = (not f) and variant == "2"     # human_m2: shorter, broader, hoodie + cap
        self.dress = (f and variant == "2")               # human_f2: top + skirt, bare legs, ponytail
        self.name = ("human_f" if f else "human_m") + variant
        self.H = 1.71 if f else (1.765 if st else 1.80)
        k = self.k = self.H / 1.80
        self.wf = 1.12 if st else 1.0                     # torso width factor
        self.lf = 1.10 if st else 1.0                     # limb girth factor
        sh = 0.166 if f else (0.197 if st else 0.186)     # shoulder joint half-width
        hip = 0.090 if f else (0.097 if st else 0.092)
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
            B.ell((0, -0.002, 1.16 * k), (0.136, 0.097, 0.12 * k), "Spine", "Shirt")
            B.ell((0, 0.010, 0.99 * k), (0.158, 0.105, 0.105 * k), "Hips", "Pants")
            for sx in (1, -1):
                B.ell((sx * 0.068, 0.064, 0.93 * k), (0.078, 0.064, 0.085 * k), "Hips", "Pants")
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
        B.caps(sho + u * 0.04, sho + u * (L * sp.sleeve_t + 0.02), 0.054 * a, "UpperArm." + s, "Shirt")
        B.caps(sho + u * (L * 0.45), elb, 0.041 * a, "UpperArm." + s, "Skin")                    # biceps
        B.ell(elb + (wri - elb) * 0.30, (0.042 * a, 0.039 * a, 0.10 * k), "LowerArm." + s, "Skin",
              axis=wri - elb)
        B.caps(elb + (wri - elb) * 0.5, wri, 0.028 * a, "LowerArm." + s, "Skin")
    # ---- legs (straight trousers; bare legs under the skirt) and shoes
    lg = 0.94 if f else (1.08 if st else 1.0)
    for s, sx in (("L", 1), ("R", -1)):
        hip, kne, ank, toe = J["hip" + s], J["kne" + s], J["ank" + s], J["toe" + s]
        if sp.dress:
            B.ball(hip + Vector((sx * 0.012, 0.0, -0.05)), 0.088, "UpperLeg." + s, "Pants")
            B.ell(hip + (kne - hip) * 0.40, (0.074, 0.076, 0.21 * k), "UpperLeg." + s, "Skin", axis=kne - hip)
            B.ell(hip + (kne - hip) * 0.78, (0.056, 0.058, 0.10 * k), "UpperLeg." + s, "Skin", axis=kne - hip)
            B.ball(kne + Vector((0, -0.006, 0.012)), 0.046, "UpperLeg." + s, "Skin")              # knee
            B.ell(kne + (ank - kne) * 0.28 + Vector((0, 0.016, 0)), (0.050, 0.052, 0.12 * k),
                  "LowerLeg." + s, "Skin", axis=ank - kne)                                         # calf
            B.caps(kne + (ank - kne) * 0.45, ank + Vector((0, 0, 0.03)), 0.030, "LowerLeg." + s, "Skin")
        else:
            B.ball(hip + Vector((sx * 0.012, 0.0, -0.05)), 0.090 * (1.04 if f else lg), "UpperLeg." + s, "Pants")
            B.ell(hip + (kne - hip) * 0.42, (0.080 * lg, 0.084 * lg, 0.21 * k), "UpperLeg." + s, "Pants",
                  axis=kne - hip)
            B.ball(kne + Vector((0, -0.002, 0.02)), 0.054 * lg, "UpperLeg." + s, "Pants")
            B.ell(kne + (ank - kne) * 0.30 + Vector((0, 0.012, 0)), (0.060 * lg, 0.064 * lg, 0.15 * k),
                  "LowerLeg." + s, "Pants", axis=ank - kne)
            B.caps(kne + (ank - kne) * 0.5, ank + Vector((0, 0, 0.045)), 0.052 * lg, "LowerLeg." + s, "Pants")
        # shoe: heel, instep, foot, toe box (low ballerina-like shoe for the dress variant)
        sl = 0.93 if sp.dress else 1.0
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
    H.caps((0, 0.022, 1.47 * k), P(0, 0.006, -0.075), nr * 0.97, "Neck", "Skin")
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
    H.ell(P(0, -0.091, -0.024), (0.0058 * hk, 0.009 * hk, 0.026 * hk * nz), "Head", "Skin",
          axis=(0, -0.45, 1), s=6)
    H.ball(P(0, -0.1035 + (0.003 if f else 0), -0.049), 0.0078 * hk * nz, "Head", "Skin", s=6)
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
    H.ell(P(0, -0.074, -0.121), ((0.018 if f else 0.022) * hk, 0.017 * hk, 0.017 * hk), "Head", "Skin", s=3)
    H.ell(P(0, -0.060, -0.156), (0.026 * hk, 0.016 * hk, 0.009 * hk), "Head", "Skin", s=1.5, neg=True)
    for sx in (1, -1):   # jaw line: fuller mandible corner + hollow behind it
        H.ell(P(sx * 0.044, -0.010, -0.098), (0.010 * hk, 0.020 * hk, 0.016 * hk), "Head", "Skin", s=2.0)
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
    if sp.dress:
        return E.E                     # pulled-back hair: cap only (+ ponytail built separately)
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
    if sp.dress:                       # pulled back: strands converge to the ponytail tie
        T = Vector((0, 0.088, -0.005))
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
    NA, NR = 30, 8
    outer = []
    for r in range(NR):
        s = r / (NR - 1)
        z = zw + (zh - zw) * s
        ring = []
        for i in range(NA):
            az = 2 * math.pi * i / NA
            d = Vector((math.sin(az), -math.cos(az), 0))
            c = Vector((0, 0.010, z))
            hit = bvh_body.ray_cast(c + d * 0.4, -d, 0.4)
            rb = (hit[0] - c).length if (hit[0] is not None and s < 0.6) else 0.0
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
}


def build_human(female, variant=""):
    tex = nbt.textures(female)          # bakes in its own scene: before the scene reset
    nb.reset_scene()
    scene = bpy.context.scene
    scene.render.fps = FPS
    sp = Spec(female, variant)
    J, k, hk, hc = sp.J, sp.k, sp.hk, sp.hc
    st, dr = sp.stocky, sp.dress
    C = COLORS[sp.name]
    mats = {
        "Skin": tex_material("Skin", C["Skin"], 0.55, tex["skin_f" if female else "skin_m"]),
        "Shirt": tex_material("Shirt", C["Shirt"], 0.8, tex["jersey"], tex["jersey_n"], 0.55),
        "Pants": tex_material("Pants", C["Pants"], 0.85, tex["denim"], tex["denim_n"], 0.55),
        "Shoes": tex_material("Shoes", C["Shoes"], 0.5, tex["shoes"]),
        "Hair": nb.material("Hair", C["Hair"], roughness=0.6),
        "Eyes": nb.material("Eyes", (0.05, 0.035, 0.025), roughness=0.12),
        "Lips": nb.material("Lips", C["Lips"], roughness=0.4),
        "EyeWhite": nb.material("EyeWhite", (0.86, 0.83, 0.79), roughness=0.2),
        "Hat": (tex_material("Hat", C["Hat"], 0.75, tex["denim"], tex["denim_n"], 0.5) if st
                else nb.material("Hat", (0.5, 0.5, 0.5))),
    }

    body_E = body_elements(sp)
    head_E = head_elements(sp)
    hand_E = {s: hand_elements(sp, s) for s in ("L", "R")}
    weight_E = [e for e in body_E + head_E + hand_E["L"] + hand_E["R"] if not e["neg"]]

    # ------------------------------------------------ body family
    body = metaball_mesh("BodyMB", body_E, 0.0078)
    for m in ORDER:
        body.data.materials.append(mats[m])

    def body_rule(c, reg, bone):
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
    if st:
        budget = {"Shirt": 1650, "Pants": 900, "Shoes": 460, "Skin": 60}
    elif dr:
        budget = {"Shirt": 900, "Pants": 260, "Shoes": 420, "Skin": 1000}
    else:
        budget = {"Shirt": 1150, "Pants": 960, "Shoes": 460, "Skin": 380}
    for name, o in pieces.items():
        decimate(o, budget.get(name, 300))
        o["uv"] = {"Skin": "strip", "Shoes": "shoe"}.get(name, "box:" + name)

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
        if dr:
            off = 0.0042 + 0.0030 * top
            off *= 1.0 + 0.32 * rid
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
    decimate(head, 1800 if female else 1850, head_keep)
    decimate(hair_parts[0], 820 if dr else (560 if female else (520 if st else 980)))
    if vol is not None:
        decimate(vol, 900)
    head["uv"] = "face"

    # ------------------------------------------------ hands
    hands = []
    for s in ("L", "R"):
        h = metaball_mesh("Hand" + s + "MB", hand_E[s], 0.0032)
        set_material(h, mats, "Skin")
        decimate(h, 420)
        h["uv"] = "strip"
        hands.append(h)

    parts = list(pieces.values()) + [head] + hair_parts + hands
    bvh = bvh_of(parts)
    bvh_head = bvh_of([head])
    special = {}                                       # object name -> weight rule

    # ------------------------------------------------ clothing volume
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
        bvh_b = bvh_of(list(pieces.values()))
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
        th_b = 0.0030 if female else 0.0040
        for (pt, nt), (pb, nbm) in zip(top, bot):
            verts += [pt + nt * 0.0006, pb + nbm * 0.0006, pb + nbm * th_b * 0.8, pt + nt * th_b]
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

    # ------------------------------------------------ cap (m2) / ponytail (f2)
    if st:
        bvh_hh = bvh_of([head] + hair_parts)
        for o in make_cap(sp, bvh_hh, mats):
            o["uv"] = "box:Hat"
            special[o.name] = "head"
            parts.append(o)
        trim_under_cap(hair_parts[0], sp)
    if dr:
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
    neck_axis = np.array([0, 0.022])
    rule = np.array([""] * len(co), dtype=object)
    for name, a, b in ranges:
        rule[a:b] = name
    for i in range(len(co)):
        c = co[i]
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
        if W[i].sum() < 1e-6:                            # outside every element: nearest bone
            best, bd = "Hips", 9.0
            for name, h, t, _ in BONES:
                a, b = np.array(J[h]), np.array(J[t])
                ab = b - a
                hh = np.clip((c - a) @ ab / (ab @ ab), 0, 1)
                d = np.linalg.norm(c - (a + hh * ab))
                if d < bd:
                    best, bd = name, d
            W[i, bidx[best]] = 1.0
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
HAND_SUPPORT = (40, 62, 8, 12, 14)       # left hand under a handguard (AimRifle)
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
    arm_ik(p, "L", fore - hdL * (0.07 * k) + Vector((0, 0, -0.02)), Vector((0.45, 0.0, -1)),
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
    which = sys.argv[1:] or ["m", "f", "m2", "f2"]
    for w in which:
        p, t = build_human(w.startswith("f"), w[1:])
        print("[human] %s: %d tris" % (p, t))
