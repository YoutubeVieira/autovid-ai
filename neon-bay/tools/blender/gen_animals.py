"""Neon Bay - procedural skinned + animated animals (dog, cat, gull, parrot, crab).

    python3 tools/blender/gen_animals.py              # every animal
    python3 tools/blender/gen_animals.py dog crab     # some of them

Writes models/animal_<id>.glb (+ .glb.js). Same toolkit as the humans (gen_human.py):
bodies are metaball families (each element carries its bone and its colour region), polygonised,
decimated to the budget, then faces get Fur / Fur2 from the dominant region of the implicit field
(irregular pelt markings for free); skin weights come from the same field (soft joints). Wings,
beaks, ears, legs of birds and crabs, eyes and noses are small meshes weighted rigidly (or by span
for the wings). Fur / feathers / chitin are baked procedural textures with normal maps
(nb_textures.animal_textures), box-projected at world scale.

Contract (glTF, export_yup): up +Y, the animal faces **+X** (like makeAnimal() in js/engine.js:
g.rotation.y = -heading), left side towards -Z, origin on the ground under the body, metres.
Materials: Fur (main coat, recolourable), Fur2 (second colour: chest / belly / muzzle / socks,
wings of the birds, crab underside), Eye (+ fixed: Nose, Beak, Feet, Tip, Claw where used).
Clips (24 fps, in place, no root motion): dog Idle Walk Run Sit; cat Idle Walk Sit;
gull / parrot Idle Fly; crab Idle Walk (sideways, along glTF +Z/-Z). Budget <= 4000 triangles.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import bmesh  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector, Matrix, Quaternion  # noqa: E402

import nb_common as nb  # noqa: E402
import nb_textures as nbt  # noqa: E402
import gen_human as gh  # noqa: E402  (metaballs, fields, decimation, textured materials)

FPS = 24
ORDER = ["Fur", "Fur2", "Eye", "Nose", "Beak", "Feet", "Tip", "Claw"]
V = Vector


def setmat(obj, mats, name):
    obj.data.materials.clear()
    for m in ORDER:
        obj.data.materials.append(mats[m])
    obj.data.polygons.foreach_set("material_index", [ORDER.index(name)] * len(obj.data.polygons))
    return obj


def make_mats(sp, tex):
    t = sp["tex"]
    C = sp["colors"]
    tm = lambda n, r: gh.tex_material(n, C[n], r, tex[t], tex[t + "_n"], sp.get("nstr", 0.8))
    return {
        "Fur": tm("Fur", 0.8), "Fur2": tm("Fur2", 0.8),
        "Eye": nb.material("Eye", C.get("Eye", (0.05, 0.03, 0.02)), roughness=0.08),
        "Nose": nb.material("Nose", C.get("Nose", (0.03, 0.025, 0.025)), roughness=0.35),
        "Beak": nb.material("Beak", C.get("Beak", (0.9, 0.7, 0.1)), roughness=0.4),
        "Feet": nb.material("Feet", C.get("Feet", (0.8, 0.55, 0.35)), roughness=0.6),
        "Tip": gh.tex_material("Tip", C.get("Tip", (0.05, 0.05, 0.06)), 0.7, tex[t], tex[t + "_n"], 0.8),
        "Claw": nb.material("Claw", C.get("Claw", (0.12, 0.1, 0.09)), roughness=0.4),
    }


# --------------------------------------------------------------------------- small meshes
def sphere(name, r, c, mats, mat, seg=10, rings=6, scale=(1, 1, 1)):
    return setmat(nb.uv_sphere(name, r, c, seg, rings, scale=scale), mats, mat)


def tube(name, pts, radii, sides, mats, mat, cap_end=True, cap_start=True):
    """Tapered tube (gen_human.tube) given the animal material `mat`."""
    hm = {n: mats["Fur"] for n in gh.ORDER}
    o = gh.tube(name, [V(p) for p in pts], radii, sides, hm, "Skin", cap_end=cap_end, cap_start=cap_start)
    return setmat(o, mats, mat)


def retube(obj, mats, mat):
    return setmat(obj, mats, mat)


def surface_out(E, p, d, r_embed=0.0):
    """Move p along d until it leaves the implicit surface of elements E, minus r_embed."""
    p = V(p)
    d = V(d).normalized()
    for _ in range(200):
        if gh.fields(E, [p]).sum() < gh.THRESH:
            break
        p = p + d * 0.001
    return p - d * r_embed


# --------------------------------------------------------------------------- generic build
class Animal:
    def __init__(self, name):
        self.name = name
        self.bones = []          # (name, head, tail, parent)
        self.E = gh.Fam()
        self.parts = []          # (obj, rule): rule = bone name (rigid) or callable(co) -> {bone: w}
        self.root = None

    def bone(self, name, head, tail, parent=None):
        self.bones.append((name, V(head), V(tail), parent))
        if parent is None:
            self.root = name
        return name

    def j(self, name):
        for n, h, t, _ in self.bones:
            if n == name:
                return h, t
        raise KeyError(name)


def classify(obj, E, rule=None):
    me = obj.data
    C = np.array([p.center for p in me.polygons])
    F = np.clip(gh.fields(E, C), 0, None)
    regs = sorted({e["reg"] for e in E})
    acc = np.stack([F[:, [j for j, e in enumerate(E) if e["reg"] == r]].sum(1) for r in regs], 1)
    idx = []
    for n, a in enumerate(acc.argmax(1)):
        reg = regs[a]
        if rule:
            reg = rule(V(C[n]), reg)
        idx.append(ORDER.index(reg))
    me.polygons.foreach_set("material_index", idx)


def uv_box(obj, tiles):
    me = obj.data
    uv = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
    for p in me.polygons:
        tile = tiles.get(ORDER[p.material_index], 0.1)
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


def build_armature(A):
    arm = bpy.data.armatures.new("Armature")
    obj = nb.link(bpy.data.objects.new("Armature", arm))
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    for name, h, t, parent in A.bones:
        b = arm.edit_bones.new(name)
        b.head, b.tail, b.roll = h, t, 0.0
        if parent:
            b.parent = arm.edit_bones[parent]
            b.use_connect = (arm.edit_bones[parent].tail - h).length < 1e-4
    bpy.ops.object.mode_set(mode="OBJECT")
    for pb in obj.pose.bones:
        pb.rotation_mode = "QUATERNION"
    return obj


def rot(v):
    """(rx, ry, rz) degrees about the armature axes (applied X, then Y, then Z) -> Matrix."""
    rx, ry, rz = v
    return (Matrix.Rotation(math.radians(rz), 3, "Z") @ Matrix.Rotation(math.radians(ry), 3, "Y")
            @ Matrix.Rotation(math.radians(rx), 3, "X"))


def make_actions(armobj, A, clips):
    ad = armobj.animation_data_create()
    for cname, frames, fn in clips:
        act = bpy.data.actions.new(cname)
        act.use_fake_user = True
        ad.action = act
        for f in range(0, frames + 1):
            pose = fn((f % frames) / frames)
            sc = pose.get("_scale", {})
            for pb in armobj.pose.bones:
                M = pb.bone.matrix_local.to_3x3()
                R = rot(pose.get(pb.name, (0, 0, 0)))
                pb.rotation_quaternion = (M.inverted() @ R @ M).to_quaternion()
                pb.keyframe_insert("rotation_quaternion", frame=f, group=pb.name)
                if pb.name == A.root:
                    pb.location = M.inverted() @ V(pose.get("_loc", (0, 0, 0)))
                    pb.keyframe_insert("location", frame=f, group=pb.name)
                if pb.name in A.scaled:
                    s = sc.get(pb.name, 1.0)
                    pb.scale = (s, s, s)
                    pb.keyframe_insert("scale", frame=f, group=pb.name)
        tr = ad.nla_tracks.new()
        tr.name = cname
        st = tr.strips.new(cname, 0, act)
        st.name = cname
        tr.mute = True
        ad.action = None
    for pb in armobj.pose.bones:
        pb.rotation_quaternion = Quaternion()
        pb.location = V()
        pb.scale = (1, 1, 1)


def finish(A, sp, mats, clips, res, body_budget, rule=None):
    E = A.E.E
    parts = []
    if E:
        body = gh.metaball_mesh(A.name + "MB", E, res)
        for v in body.data.vertices:          # flat soles
            if v.co.z < 0.002:
                v.co.z = 0.0
        gh.decimate(body, body_budget)
        setmat(body, mats, "Fur")
        classify(body, E, rule)
        parts.append((body, None))
    parts += A.parts
    print("[animal] %s parts: %s" % (A.name, ", ".join("%s=%d" % (o.name, nb.tri_count(o)) for o, _ in parts)))
    objs = [o for o, _ in parts]
    for o in objs:
        uv_box(o, sp["tiles"])
    ranges, off = [], 0
    for o, r in parts:
        n = len(o.data.vertices)
        ranges.append((r, off, off + n))
        off += n
    obj = nb.join(objs, "Body")
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    bm.to_mesh(obj.data)
    bm.free()
    nb.auto_smooth(obj, 60)
    armobj = build_armature(A)
    names = [b[0] for b in A.bones]
    groups = {n: obj.vertex_groups.new(name=n) for n in names}
    co = np.array([v.co for v in obj.data.vertices])
    wE = [e for e in E if not e["neg"]]
    F = np.clip(gh.fields(wE, co), 0, None) if wE else np.zeros((len(co), 0))
    bidx = {n: i for i, n in enumerate(names)}
    W = np.zeros((len(co), len(names)))
    for j, e in enumerate(wE):
        W[:, bidx[e["bone"]]] += F[:, j]
    for r, a, b in ranges:
        if r is None:
            continue
        for i in range(a, b):
            W[i] = 0
            if isinstance(r, str):
                W[i, bidx[r]] = 1.0
            else:
                for bn, w in r(V(co[i])).items():
                    W[i, bidx[bn]] += w
    for i in range(len(co)):
        if W[i].sum() < 1e-6:                  # outside every element: nearest bone
            best, bd = A.root, 9
            for n, h, t, _ in A.bones:
                hh, tt = np.array(h), np.array(t)
                ab = tt - hh
                q = np.clip((co[i] - hh) @ ab / max(1e-9, ab @ ab), 0, 1)
                d = np.linalg.norm(co[i] - (hh + q * ab))
                if d < bd:
                    best, bd = n, d
            W[i, bidx[best]] = 1.0
        order = np.argsort(-W[i])[:4]
        tot = W[i, order].sum()
        for jj in order:
            w = W[i, jj] / tot
            if w > 0.02:
                groups[names[jj]].add([i], float(w), "REPLACE")
    obj.parent = armobj
    m = obj.modifiers.new("Armature", "ARMATURE")
    m.object = armobj
    tris = nb.tri_count(obj)
    make_actions(armobj, A, clips)
    path = nb.export_glb(A.name, animations=True, texcoords=True)
    return path, tris


# --------------------------------------------------------------------------- quadrupeds
QUAD = {
    "dog": dict(s=1.0, bl=1.0, leg=1.0, g=1.0, hd=1.18, mz=1.0, ears="semi", tl=1.0, tail_up=0.35,
                tex="fur", tiles={"Fur": 0.11, "Fur2": 0.11}, res=0.0085, budget=3300,
                colors=dict(Fur=(0.42, 0.24, 0.10), Fur2=(0.93, 0.88, 0.80), Eye=(0.10, 0.05, 0.02),
                            Nose=(0.03, 0.025, 0.025), Claw=(0.10, 0.09, 0.08))),
    "cat": dict(s=0.50, bl=1.12, leg=0.92, g=0.92, hd=1.45, mz=0.35, ears="pointed", tl=1.75, tail_up=0.45,
                tex="fur", tiles={"Fur": 0.06, "Fur2": 0.06}, res=0.0042, budget=3300,
                colors=dict(Fur=(0.32, 0.30, 0.29), Fur2=(0.93, 0.91, 0.88), Eye=(0.55, 0.62, 0.12),
                            Nose=(0.75, 0.45, 0.45), Claw=(0.85, 0.82, 0.78))),
}


def build_quadruped(kind):
    q = QUAD[kind]
    s, bl, lg, g, hd, mz = q["s"], q["bl"], q["leg"], q["g"], q["hd"], q["mz"]
    tex = nbt.animal_textures()
    nb.reset_scene()
    bpy.context.scene.render.fps = FPS
    mats = make_mats(q, tex)
    A = Animal("animal_" + kind)
    A.scaled = set()

    def P(x, y, z):
        return V((x, y, z)) * s
    hl = 0.40 * lg                    # elbow-ish height of the body underside
    zb = hl + 0.12                    # body axis
    xr, xf = -0.27 * bl, 0.25 * bl
    # ---- bones
    A.bone("Hips", P(xr + 0.02, 0, zb + 0.02), P(xr + 0.20 * bl, 0, zb + 0.02))
    A.bone("Spine", P(xr + 0.20 * bl, 0, zb + 0.02), P(xf - 0.08 * bl, 0, zb + 0.03), "Hips")
    A.bone("Chest", P(xf - 0.08 * bl, 0, zb + 0.03), P(xf + 0.02, 0, zb + 0.07), "Spine")
    neck_top = P(xf + 0.09 * hd, 0, zb + 0.19 * hd)
    A.bone("Neck", P(xf + 0.02, 0, zb + 0.07), neck_top, "Chest")
    head_tip = neck_top + P(0.15 * hd, 0, -0.025 * hd)
    A.bone("Head", neck_top, head_tip, "Neck")
    hb = neck_top                                        # head base
    t0 = P(xr, 0, zb + 0.05)
    tdir = V((-1, 0, q["tail_up"])).normalized()
    tl = 0.13 * q["tl"] * s
    A.bone("Tail1", t0, t0 + tdir * tl, "Hips")
    t1 = t0 + tdir * tl
    tdir2 = V((-1, 0, q["tail_up"] * 1.3)).normalized()
    A.bone("Tail2", t1, t1 + tdir2 * tl, "Tail1")
    t2 = t1 + tdir2 * tl
    tdir3 = V((-1, 0, q["tail_up"] * (1.5 if kind == "cat" else 0.6))).normalized()
    A.bone("Tail3", t2, t2 + tdir3 * tl, "Tail2")
    for sd, sy in (("L", 1), ("R", -1)):
        y = 0.072 * g * sy
        A.bone("UpperArm." + sd, P(xf - 0.05, y, zb - 0.01), P(xf - 0.035, y, hl * 0.58), "Chest")
        A.bone("LowerArm." + sd, P(xf - 0.035, y, hl * 0.58), P(xf - 0.045, y, 0.055), "UpperArm." + sd)
        A.bone("Paw." + sd, P(xf - 0.045, y, 0.055), P(xf + 0.015, y, 0.014), "LowerArm." + sd)
        A.bone("Thigh." + sd, P(xr + 0.07, y * 1.05, zb - 0.01), P(xr + 0.14, y * 1.05, hl * 0.66), "Hips")
        A.bone("Shin." + sd, P(xr + 0.14, y * 1.05, hl * 0.66), P(xr + 0.02, y * 1.05, hl * 0.30), "Thigh." + sd)
        A.bone("Hock." + sd, P(xr + 0.02, y * 1.05, hl * 0.30), P(xr + 0.04, y * 1.05, 0.05), "Shin." + sd)
        A.bone("HPaw." + sd, P(xr + 0.04, y * 1.05, 0.05), P(xr + 0.10, y * 1.05, 0.014), "Hock." + sd)
    # ---- body elements (ell semi = (half width, half height, half length) with axis = +X)
    X, Y = (1, 0, 0), (0, 1, 0)
    E = A.E
    E.ell(P(xf - 0.07, 0, zb), (0.105 * g * s, 0.150 * s, 0.155 * s), "Chest", "Fur", axis=X, lateral=Y)
    E.ell(P(xf - 0.02, 0, zb - 0.085), (0.070 * g * s, 0.075 * s, 0.085 * s), "Chest", "Fur2", axis=X, lateral=Y)
    mid = (xr + xf) / 2 - 0.02
    E.ell(P(mid, 0, zb + 0.015), (0.083 * g * s, 0.105 * s, 0.20 * bl * s), "Spine", "Fur", axis=X, lateral=Y)
    E.ell(P(mid + 0.02, 0, zb - 0.075), (0.055 * g * s, 0.040 * s, 0.13 * bl * s), "Spine", "Fur2", axis=X,
          lateral=Y)
    E.ell(P(xr + 0.075, 0, zb + 0.015), (0.092 * g * s, 0.112 * s, 0.11 * s), "Hips", "Fur", axis=X, lateral=Y)
    # neck + throat
    E.caps(P(xf - 0.02, 0, zb + 0.05), hb + P(0.01, 0, -0.02), 0.068 * hd * s, "Neck", "Fur")
    E.caps(P(xf + 0.03, 0, zb - 0.01), hb + P(0.04 * hd, 0, -0.06 * hd), 0.045 * hd * s, "Neck", "Fur2")
    # head: skull, cheeks, brows, muzzle, jaw
    H = lambda x, y, z: hb + V((x, y, z)) * (hd * s)
    E.ell(H(0.050, 0, 0.030), (0.064 * hd * s, 0.066 * hd * s, 0.074 * hd * s), "Head", "Fur", axis=X, lateral=Y)
    for sy in (1, -1):
        E.ball(H(0.075, sy * 0.040, 0.000), 0.034 * hd * s, "Head", "Fur")
        E.ball(H(0.100, sy * 0.030, 0.050), 0.016 * hd * s, "Head", "Fur", s=2.5)                # brow
    mx = 0.105 + 0.055 * mz
    E.ell(H(mx, 0, -0.002), (0.034 * hd * s, 0.034 * hd * s, (0.030 + 0.048 * mz) * hd * s), "Head", "Fur2",
          axis=(1, 0, -0.15), lateral=Y)
    E.ell(H(mx - 0.01, 0, -0.030), (0.026 * hd * s, 0.016 * hd * s, (0.024 + 0.040 * mz) * hd * s), "Head", "Fur2",
          axis=(1, 0, -0.25), lateral=Y)                                                           # jaw
    # legs (Fur2 socks on the paws)
    for sd in ("L", "R"):
        for bn, r0, r1, reg in (("UpperArm", 0.050, 0.034, "Fur"), ("LowerArm", 0.030, 0.024, "Fur"),
                                ("Thigh", 0.062, 0.040, "Fur"), ("Shin", 0.036, 0.024, "Fur"),
                                ("Hock", 0.022, 0.020, "Fur")):
            h, t = A.j(bn + "." + sd)
            E.caps(h, h.lerp(t, 0.55), r0 * lg * s, bn + "." + sd, reg)
            E.caps(h.lerp(t, 0.45), t, r1 * lg * s, bn + "." + sd, reg)
        for bn in ("Paw", "HPaw"):
            h, t = A.j(bn + "." + sd)
            c = h.lerp(t, 0.6)
            E.ell(V((c.x, c.y, 0.022 * s)), (0.030 * lg * s, 0.022 * s, 0.040 * lg * s), bn + "." + sd, "Fur2",
                  axis=X, lateral=Y)
    # tail
    for i, bn in enumerate(("Tail1", "Tail2", "Tail3")):
        h, t = A.j(bn)
        r = (0.030 - 0.006 * i) * s if kind == "dog" else 0.021 * s
        E.caps(h, t, r, bn, "Fur" if (i < 2 or kind == "cat") else "Fur2")
    # ---- small meshes: eyes, nose, ears, claws
    for sy in (1, -1):
        c = H(0.098, sy * 0.036, 0.024)
        r = 0.0145 * hd * s if kind == "dog" else 0.0175 * hd * s
        p = surface_out(E.E, c, V((0.55, sy * 0.8, 0.15)), r * 0.55)
        A.parts.append((sphere("Eye", r, p, mats, "Eye", 10, 7), "Head"))
    tip = H(mx + 0.030 + 0.048 * mz, 0, 0.012)
    tip = surface_out(E.E, tip - V((0.03, 0, 0)) * s, V((1, 0, 0.25)), 0.006 * s)
    A.parts.append((sphere("Nose", 0.016 * hd * s, tip, mats, "Nose", 10, 6, scale=(0.8, 1.25, 0.8)), "Head"))
    for sd, sy in (("L", 1), ("R", -1)):
        base = H(0.030, sy * 0.050, 0.075)
        if q["ears"] == "pointed":
            up = V((0.05, sy * 0.35, 1)).normalized()
            L, W = 0.065 * hd * s, 0.040 * hd * s
        else:
            up = V((0.15, sy * 0.9, 0.55)).normalized()
            L, W = 0.095 * s, 0.062 * s
        A.bone("Ear." + sd, base, base + up * L, "Head")
        A.parts.append((ear_mesh(base, up, sy, L, W, mats, q["ears"] == "semi"), "Ear." + sd))
        for bn in ("Paw", "HPaw"):
            h, t = A.j(bn + "." + sd)
            for k in (-1, 0, 1):
                c = V((t.x + 0.012 * s, h.y + k * 0.012 * s, 0.010 * s))
                A.parts.append((retube(tube("Claw", [c, c + V((0.014, 0, -0.006)) * s], [0.0042 * s, 0.0012 * s], 4,
                                            mats, "Fur"), mats, "Claw"), bn + "." + sd))

    def rule(c, reg):
        return reg
    clips = quad_clips(A, kind)
    return finish(A, q, mats, clips, q["res"], q["budget"], rule)


def ear_mesh(base, up, sy, L, W, mats, floppy):
    """Ear flap: a cupped, slightly thick triangle; a floppy ear bends over at 60 %."""
    side = V((1, 0, 0)) - up * up.dot(V((1, 0, 0)))
    side.normalize()
    nrm = up.cross(side).normalized() * sy
    rows = []
    n = 5
    for i in range(n):
        t = i / (n - 1)
        w = W * (1 - t) ** 0.9 * 0.5 + 0.0015
        c = base + up * (L * t)
        if floppy and t > 0.5:
            c = c - nrm * (0.6 * L * (t - 0.5) ** 1.6) * 1.0 - V((0, 0, 0.5 * L * (t - 0.5) ** 1.4))
        cup = nrm * (0.25 * w)
        rows.append([c + side * w, c + cup * -1, c - side * w])
    th = 0.004
    verts = []
    for r in rows:
        verts += [p + nrm * th for p in r]
    for r in rows:
        verts += [p - nrm * th for p in r]
    m = 3 * n
    faces = []
    for i in range(n - 1):
        for j in range(2):
            a = 3 * i + j
            faces.append((a, a + 1, a + 4, a + 3))
            faces.append((m + a + 3, m + a + 4, m + a + 1, m + a))
    for i in range(n - 1):
        for j in (0, 2):
            a, b = 3 * i + j, 3 * (i + 1) + j
            faces.append((a, b, m + b, m + a) if j == 0 else (b, a, m + a, m + b))
    faces.append((0, m, m + 1, 1))
    faces.append((1, m + 1, m + 2, 2))
    o = nb.mesh_object("Ear", verts, faces)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(o.data)
    bm.free()
    return setmat(o, mats, "Fur")


def quad_clips(A, kind):
    cat = kind == "cat"

    def legs(p, t, amp, flex, phases, duty_shift=0.0):
        for (front, sd), ph in phases.items():
            c = 2 * math.pi * (t + ph)
            sw = math.sin(c)                 # +1: leg forward
            lift = max(0.0, math.cos(c + duty_shift))
            if front:
                p["UpperArm." + sd] = (0, -amp * sw, 0)
                p["LowerArm." + sd] = (0, flex * lift, 0)
                p["Paw." + sd] = (0, flex * 0.8 * lift - 6 * sw, 0)
            else:
                p["Thigh." + sd] = (0, -amp * sw, 0)
                p["Shin." + sd] = (0, -flex * 0.5 * lift, 0)
                p["Hock." + sd] = (0, flex * 0.9 * lift, 0)
                p["HPaw." + sd] = (0, flex * 0.3 * lift - 5 * sw, 0)

    def walk(t):
        ph = 2 * math.pi * t
        p = {"_loc": (0, 0, 0.006 * math.cos(4 * ph) * (0.5 if cat else 1))}
        p["Hips"] = (3 * math.sin(ph), 0, 2 * math.sin(ph))
        p["Chest"] = (-3 * math.sin(ph), 0, -2 * math.sin(ph))
        p["Neck"] = (0, -2 + 3 * math.cos(2 * ph), 0)
        p["Head"] = (0, 2 - 3 * math.cos(2 * ph), 0)
        legs(p, t, 24 if not cat else 22, 50, {(False, "L"): 0.0, (True, "L"): 0.25, (False, "R"): 0.5,
                                               (True, "R"): 0.75})
        p["Tail1"] = (0, -4, 14 * math.sin(ph * 2) * (0.4 if cat else 1))
        p["Tail2"] = (0, 0, 10 * math.sin(ph * 2 - 0.8) * (0.4 if cat else 1))
        p["Tail3"] = (0, 0, 8 * math.sin(ph * 2 - 1.6))
        return p

    def run(t):
        ph = 2 * math.pi * t
        p = {"_loc": (0, 0, 0.03 + 0.03 * math.sin(ph))}
        p["Spine"] = (0, 9 * math.sin(ph), 0)
        p["Chest"] = (0, 7 * math.sin(ph), 0)
        p["Hips"] = (0, -8 * math.sin(ph), 0)
        p["Neck"] = (0, -5 * math.sin(ph) + 8, 0)
        p["Head"] = (0, 5 * math.sin(ph) - 4, 0)
        legs(p, t, 42, 70, {(True, "L"): 0.0, (True, "R"): 0.08, (False, "L"): 0.5, (False, "R"): 0.58})
        p["Tail1"] = (0, -12 + 8 * math.sin(ph), 0)
        p["Tail2"] = (0, 6 * math.sin(ph - 1), 0)
        p["Ear.L"] = (0, 15 + 10 * math.sin(ph), 0)
        p["Ear.R"] = (0, 15 + 10 * math.sin(ph), 0)
        return p

    def idle(t):
        ph = 2 * math.pi * t
        b = math.sin(ph)
        p = {"_loc": (0, 0, 0.0015 * b)}
        p["Spine"] = (0, 0.8 * b, 0)
        p["Chest"] = (0, -0.8 * b, 0)
        look = 18 * math.sin(ph) if not cat else 12 * math.sin(ph)
        p["Neck"] = (0, -3, look * 0.4)
        p["Head"] = (6 * math.sin(2 * ph) * 0.3, 2, look * 0.6)
        wag = 22 if not cat else 8
        p["Tail1"] = (0, 0, wag * math.sin(4 * ph))
        p["Tail2"] = (0, 0, wag * 0.8 * math.sin(4 * ph - 0.7))
        p["Tail3"] = (0, 0, wag * 0.6 * math.sin(4 * ph - 1.4))
        tw = max(0.0, math.sin(6 * ph)) ** 8 * 18
        p["Ear.L"] = (tw, 0, 0)
        p["Ear.R"] = (-tw * 0.5, 0, 0)
        return p

    def sit(t):
        ph = 2 * math.pi * t
        b = math.sin(ph)
        sc = A.j("Hips")[0]
        hs = A.j("Thigh.L")[0]
        tilt = -38 if not cat else -42
        p = {}
        # pivot the body up around the hip joints, sink the rump to the ground
        drop = hs.z - (0.11 if not cat else 0.045)
        p["_loc"] = (0.02 * (1 if not cat else 0.5), 0, -drop + 0.0 * b)
        p["Hips"] = (0, tilt, 0)
        p["Spine"] = (0, -4 + 0.6 * b, 0)
        p["Chest"] = (0, -2 - 0.6 * b, 0)
        p["Neck"] = (0, 20, 6 * math.sin(ph))
        p["Head"] = (0, 22, 8 * math.sin(ph))
        for sd in ("L", "R"):
            p["UpperArm." + sd] = (0, -tilt + 6 + 4, 0)
            p["LowerArm." + sd] = (0, 0, 0)
            p["Paw." + sd] = (0, -2, 0)
            p["Thigh." + sd] = (0, -tilt - 80, 0)
            p["Shin." + sd] = (0, 130, 0)
            p["Hock." + sd] = (0, -100, 0)
            p["HPaw." + sd] = (0, 50, 0)
        p["Tail1"] = (0, 35, 18 * math.sin(2 * ph))
        p["Tail2"] = (0, 10, 10 * math.sin(2 * ph - 0.6))
        p["Tail3"] = (0, 0, 6 * math.sin(2 * ph - 1.2))
        return p
    clips = [("Idle", 48, idle), ("Walk", 24, walk)]
    if not cat:
        clips.append(("Run", 12, run))
    clips.append(("Sit", 48, sit))
    return clips


# --------------------------------------------------------------------------- birds
BIRD = {
    "bird": dict(s=1.0, span=0.46, chord=0.12, tail=0.075, beak=0.050, head=1.0, hook=False,
                 tex="feather", tiles={"Fur": 0.05, "Fur2": 0.05, "Tip": 0.05}, res=0.0045, budget=2300,
                 tip_zone=(0.72, 1.01), perch_tilt=-8, leg=0.13,
                 colors=dict(Fur=(0.95, 0.95, 0.93), Fur2=(0.55, 0.58, 0.63), Tip=(0.05, 0.05, 0.06),
                             Eye=(0.85, 0.75, 0.30), Beak=(0.95, 0.75, 0.10), Feet=(0.90, 0.62, 0.40))),
    "parrot": dict(s=1.0, span=0.42, chord=0.13, tail=0.36, beak=0.045, head=1.25, hook=True,
                   tex="feather", tiles={"Fur": 0.045, "Fur2": 0.045, "Tip": 0.045}, res=0.0045, budget=2300,
                   tip_zone=(0.0, 0.42), perch_tilt=-52, leg=0.07,
                   colors=dict(Fur=(0.85, 0.06, 0.05), Fur2=(0.05, 0.25, 0.80), Tip=(1.0, 0.80, 0.08),
                               Eye=(0.92, 0.88, 0.70), Beak=(0.88, 0.84, 0.75), Feet=(0.25, 0.25, 0.27))),
}


def build_bird(kind):
    q = BIRD[kind]
    s, hd = q["s"], q["head"]
    tex = nbt.animal_textures()
    nb.reset_scene()
    bpy.context.scene.render.fps = FPS
    mats = make_mats(q, tex)
    A = Animal("animal_" + kind)
    A.scaled = {"Wing2.L", "Wing2.R"}
    zb = q["leg"] + 0.09                      # body axis height (horizontal body in the rest pose)
    A.bone("Body", V((-0.10, 0, zb)), V((0.08, 0, zb)))
    hb = V((0.10, 0, zb + 0.07))
    A.bone("Neck", V((0.08, 0, zb)), hb, "Body")
    A.bone("Head", hb, hb + V((0.06 * hd, 0, 0)), "Neck")
    A.bone("Tail", V((-0.10, 0, zb + 0.01)), V((-0.10 - q["tail"], 0, zb + 0.01)), "Body")
    sho_y, wri_y, tip_y = 0.035, 0.035 + q["span"] * 0.42, 0.035 + q["span"]
    for sd, sy in (("L", 1), ("R", -1)):
        sho = V((0.045, sy * sho_y, zb + 0.035))
        wri = V((0.035, sy * wri_y, zb + 0.035))
        tip = V((-0.02, sy * tip_y, zb + 0.035))
        A.bone("Wing1." + sd, sho, wri, "Body")
        A.bone("Wing2." + sd, wri, tip, "Wing1." + sd)
        hip = V((-0.005, sy * 0.028, zb - 0.03))
        ank = V((0.0, sy * 0.032, 0.022))
        A.bone("Leg." + sd, hip, ank, "Body")
        A.bone("Foot." + sd, ank, ank + V((0.04, 0, -0.018)), "Leg." + sd)
    E = A.E
    X, Y = (1, 0, 0), (0, 1, 0)
    # body: breast (Fur), back mantle (Fur2 for the gull / Fur for the parrot), belly
    E.ell(V((0.0, 0, zb)), (0.052 * s, 0.058 * s, 0.115 * s), "Body", "Fur", axis=X, lateral=Y)
    E.ell(V((0.04, 0, zb - 0.01)), (0.048 * s, 0.055 * s, 0.06 * s), "Body", "Fur", axis=X, lateral=Y)
    E.ell(V((-0.02, 0, zb + 0.030)), (0.046 * s, 0.022 * s, 0.10 * s), "Body",
          "Fur2" if kind == "bird" else "Fur", axis=X, lateral=Y)
    E.ell(V((-0.11, 0, zb + 0.008)), (0.030 * s, 0.020 * s, 0.05 * s), "Tail", "Fur2" if kind == "bird" else "Fur",
          axis=X, lateral=Y)
    E.caps(V((0.07, 0, zb + 0.005)), hb + V((0.0, 0, -0.01)), 0.032 * s * (1.1 if kind == "parrot" else 1),
           "Neck", "Fur")
    E.ell(hb + V((0.020 * hd, 0, 0.008)), (0.033 * hd, 0.034 * hd, 0.040 * hd), "Head", "Fur", axis=X, lateral=Y)
    E.ball(hb + V((0.045 * hd, 0, -0.005)), 0.022 * hd, "Head", "Fur", s=2.4)
    # tail feathers: flat fan (Fur2 / parrot: long blue-red tail)
    tl = q["tail"]
    for i, (dy, ln) in enumerate(((0, 1.0), (0.012, 0.92), (-0.012, 0.92), (0.022, 0.8), (-0.022, 0.8))):
        h0 = V((-0.10, dy * 0.4, zb + 0.008))
        h1 = V((-0.10 - tl * ln, dy * (1.6 if kind == "bird" else 1.0), zb + 0.008 - 0.01 * ln))
        E.ell((h0 + h1) / 2, (0.016 * s, 0.0050 * s, tl * ln / 2), "Tail", "Fur" if (kind == "bird") else "Fur2",
              axis=h1 - h0, lateral=Y, s=3)
    # wings: span-skinned flat meshes
    for sd, sy in (("L", 1), ("R", -1)):
        A.parts.append(wing_mesh(A, q, sd, sy, mats))
        # legs + feet (rigid)
        hip, ank = A.j("Leg." + sd)
        A.parts.append((retube(tube("Leg", [hip + V((0, 0, -0.01)), ank], [0.0055, 0.0042], 6, mats, "Fur"),
                               mats, "Feet"), "Leg." + sd))
        toes = [V((0.045, 0.0, 0)), V((0.035, sy * 0.022, 0)), V((0.035, -sy * 0.020, 0)), V((-0.02, 0, 0))]
        if q["hook"]:                         # zygodactyl: two toes forward, two back
            toes = [V((0.032, sy * 0.012, 0)), V((0.030, -sy * 0.010, 0)), V((-0.026, sy * 0.012, 0)),
                    V((-0.024, -sy * 0.010, 0))]
        for tvec in toes:
            a = V((ank.x, ank.y, 0.006))
            A.parts.append((retube(tube("Toe", [a, a + tvec], [0.0040, 0.0022], 4, mats, "Fur"), mats, "Feet"),
                            "Foot." + sd))
        if kind == "bird":                    # webbing between the front toes
            a = V((ank.x, ank.y, 0.004))
            web = nb.mesh_object("Web", [a, a + toes[1], a + toes[0], a + toes[2]], [(0, 1, 2, 3), (3, 2, 1, 0)])
            A.parts.append((setmat(web, mats, "Feet"), "Foot." + sd))
    # beak
    A.parts.append((beak_mesh(hb, hd, q, mats), "Head"))
    for sy in (1, -1):
        c = hb + V((0.040 * hd, sy * 0.030 * hd, 0.012 * hd))
        r = 0.0075 * hd
        p = surface_out(E.E, c, V((0.2, sy, 0.1)), r * 0.5)
        A.parts.append((sphere("Eye", r, p, mats, "Eye", 8, 6), "Head"))
        if kind == "parrot":                  # white face patch of a macaw around the eye
            pf = surface_out(E.E, hb + V((0.046 * hd, sy * 0.024 * hd, 0.0)), V((0.3, sy, 0)), 0.006)
            A.parts.append((sphere("Face", 0.017 * hd, pf, mats, "Beak", 8, 6, scale=(1.2, 0.35, 0.9)), "Head"))
        if True:                              # pupil
            A.parts.append((sphere("Pupil", r * 0.5, p + V((0.1, sy, 0)).normalized() * r * 0.82, mats, "Nose",
                                   6, 4, scale=(1, 0.5, 1)), "Head"))
    clips = bird_clips(A, q, kind)
    return finish(A, q, mats, clips, q["res"], q["budget"])


def wing_mesh(A, q, sd, sy, mats):
    """Wing: thin cambered aerofoil from the shoulder to the tip, primaries notched at the tip.
    Material Fur2 (Tip in the tip zone); weights blend Body / Wing1 / Wing2 along the span."""
    sho, wri = A.j("Wing1." + sd)
    _, tip = A.j("Wing2." + sd)
    NS, NC = 14, 4
    span_w = (wri - sho).length / ((wri - sho).length + (tip - wri).length)
    top, bot = [], []
    for i in range(NS):
        u = i / (NS - 1)
        le = sho.lerp(wri, u / span_w) if u < span_w else wri.lerp(tip, (u - span_w) / (1 - span_w))
        chord = q["chord"] * (1.0 - 0.75 * u ** 1.6) + 0.012
        if u > 0.62:                           # primaries: alternate longer / shorter feathers
            chord *= 1.0 + (0.18 if i % 2 else -0.08)
        rt, rb = [], []
        for j in range(NC):
            c = j / (NC - 1)
            p = le + V((-chord * c, 0, 0))
            th = 0.010 * (1 - u * 0.7) * (1 - c) ** 1.5 + 0.0012
            camber = 0.006 * math.sin(math.pi * c) * (1 - u)
            rt.append(p + V((0, 0, camber + th)))
            rb.append(p + V((0, 0, camber - th * 0.4)))
        top.append(rt)
        bot.append(rb)
    verts = [p for r in top for p in r] + [p for r in bot for p in r]
    m = NS * NC
    faces, fm = [], []
    for i in range(NS - 1):
        for j in range(NC - 1):
            a = i * NC + j
            faces.append((a, a + NC, a + NC + 1, a + 1) if sy > 0 else (a, a + 1, a + NC + 1, a + NC))
            faces.append((m + a, m + a + 1, m + a + NC + 1, m + a + NC) if sy > 0 else
                         (m + a, m + a + NC, m + a + NC + 1, m + a + 1))
            u = (i + 0.5) / (NS - 1)
            z0, z1 = q["tip_zone"]
            mat = "Tip" if z0 <= u <= z1 else "Fur2"
            fm += [mat, mat]
        for j in (0, NC - 1):                  # leading / trailing edge strips
            a, b = i * NC + j, (i + 1) * NC + j
            faces.append((a, b, m + b, m + a))
            u = (i + 0.5) / (NS - 1)
            fm.append("Tip" if q["tip_zone"][0] <= u <= q["tip_zone"][1] else "Fur2")
    for i in (0, NS - 1):                      # root / tip caps
        for j in range(NC - 1):
            a = i * NC + j
            faces.append((a, a + 1, m + a + 1, m + a))
            fm.append("Fur2")
    o = nb.mesh_object("Wing", verts, faces)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(o.data)
    bm.free()
    setmat(o, mats, "Fur2")
    o.data.polygons.foreach_set("material_index", [ORDER.index(x) for x in fm])
    sw = span_w

    def w(c):
        u = (abs(c.y) - abs(sho.y)) / (abs(tip.y) - abs(sho.y))
        if u < 0.06:
            return {"Body": 0.5, "Wing1." + sd: 0.5}
        t = min(1.0, max(0.0, (u - (sw - 0.05)) / 0.10))
        return {"Wing1." + sd: 1 - t, "Wing2." + sd: t}
    return (o, w)


def beak_mesh(hb, hd, q, mats):
    """Gull: straight yellow bill with a hooked tip; parrot: big hooked upper mandible + lower."""
    base = hb + V((0.058 * hd, 0, -0.004 * hd))
    L = q["beak"] * hd
    pts, rad = [], []
    n = 7
    for i in range(n):
        t = i / (n - 1)
        if q["hook"]:
            ang = t * 2.0
            p = base + V((math.sin(ang) * L * 0.55, 0, (math.cos(ang) - 1) * L * 0.55 + 0.004))
            r = 0.021 * hd * (1 - t) ** 0.8 + 0.002
        else:
            p = base + V((L * t, 0, -0.002 - (0.006 * max(0, t - 0.8) / 0.2)))
            r = 0.010 * hd * (1 - t) ** 0.7 + 0.0015
        pts.append(p)
        rad.append(r)
    o = tube("Beak", pts, rad, 7, mats, "Fur")
    for v in o.data.vertices:                 # flatten sideways
        v.co.y = v.co.y * 0.72
    out = setmat(o, mats, "Beak")
    if q["hook"]:                             # lower mandible joined in (one object)
        lo = tube("BeakLow", [base + V((0, 0, -0.016 * hd)), base + V((0.026 * hd, 0, -0.022 * hd))],
                  [0.014 * hd, 0.004], 6, mats, "Fur")
        setmat(lo, mats, "Nose")
        out = nb.join([out, lo], "Beak")
    return out


def bird_clips(A, q, kind):
    tilt = q["perch_tilt"]

    def folded(p, b=0.0):
        for sd, sy in (("L", 1), ("R", -1)):
            p["Wing1." + sd] = (sy * -8, 8, sy * 96)        # back along the body, slightly down
            p["Wing2." + sd] = (sy * -4, -2, sy * 18 + sy * b)
        p["_scale"] = {"Wing2.L": 0.62, "Wing2.R": 0.62}

    def idle(t):
        ph = 2 * math.pi * t
        b = math.sin(ph)
        p = {"_loc": (0, 0, 0.001 * b)}
        p["Body"] = (0, tilt + 1.0 * b, 0)
        p["Tail"] = (0, -tilt * 0.6 + 2 * b, 0)
        look = 30 * (math.sin(ph) if kind == "bird" else math.sin(2 * ph) * 0.8)
        p["Neck"] = (0, -tilt * 0.55, 0)
        p["Head"] = (0, -tilt * 0.45 + 3 * math.sin(3 * ph), look)
        for sd in ("L", "R"):
            p["Leg." + sd] = (0, -tilt, 0)
            p["Foot." + sd] = (0, 0, 0)
        folded(p, 2 * b)
        if kind == "parrot":                  # perched upright: compensate the leg length change
            p["_loc"] = (0.03, 0, -0.012 + 0.001 * b)
        return p

    def fly(t):
        ph = 2 * math.pi * t
        f = math.sin(ph)
        p = {"_loc": (0, 0, 0.05 - 0.012 * f)}
        p["Body"] = (0, -4 + 2 * f, 0)
        p["Neck"] = (0, 6 - 2 * f, 0)
        p["Head"] = (0, -4, 0)
        p["Tail"] = (0, 2 * f, 0)
        for sd, sy in (("L", 1), ("R", -1)):
            p["Wing1." + sd] = (sy * (38 * f + 6), 6 * math.cos(ph), 0)
            p["Wing2." + sd] = (sy * (22 * math.sin(ph - 0.7) - 2), -6 * math.cos(ph), sy * -6 * max(0, -f))
            p["Leg." + sd] = (0, 70, 0)
            p["Foot." + sd] = (0, 40, 0)
        p["_scale"] = {"Wing2.L": 1.0, "Wing2.R": 1.0}
        return p
    return [("Idle", 48, idle), ("Fly", 12 if kind == "bird" else 10, fly)]


# --------------------------------------------------------------------------- crab
CRAB = dict(tex="shell", tiles={"Fur": 0.035, "Fur2": 0.035, "Tip": 0.035}, nstr=1.0,
            colors=dict(Fur=(0.80, 0.22, 0.08), Fur2=(0.96, 0.82, 0.62), Eye=(0.02, 0.02, 0.02),
                        Tip=(0.25, 0.10, 0.06), Claw=(0.30, 0.12, 0.06)))


def build_crab():
    q = CRAB
    tex = nbt.animal_textures()
    nb.reset_scene()
    bpy.context.scene.render.fps = FPS
    mats = make_mats(q, tex)
    A = Animal("animal_crab")
    A.scaled = set()
    zb = 0.045
    A.bone("Body", V((-0.03, 0, zb)), V((0.04, 0, zb)))
    # carapace: displaced uv sphere (front teeth, ridges), underside Fur2
    cara = nb.uv_sphere("Carapace", 1.0, (0, 0, 0), 20, 10)
    for v in cara.data.vertices:
        x, y, z = v.co
        a = math.atan2(y, x)
        teeth = 0.06 * max(0.0, math.cos(a)) ** 2 * max(0.0, math.sin(9 * a)) * (1 - abs(z))
        r = 1 + teeth
        zz = z if z > 0 else z * 0.55
        bump = 0.05 * math.sin(3 * x) * math.cos(4 * y) * max(0.0, z)
        v.co = V((x * 0.050 * r, y * 0.068 * r, zz * 0.026 + bump * 0.02 - 0.004 * abs(y / 1.0)))
        v.co.z += zb
    me = cara.data
    setmat(cara, mats, "Fur")
    me.polygons.foreach_set("material_index", [ORDER.index("Fur2" if p.center.z < zb - 0.006 else "Fur")
                                               for p in me.polygons])
    A.parts.append((cara, "Body"))
    # mouth plate
    # eyes on stalks
    for sd, sy in (("L", 1), ("R", -1)):
        b0 = V((0.040, sy * 0.016, zb + 0.012))
        b1 = b0 + V((0.006, sy * 0.004, 0.020))
        A.bone("Eye." + sd, b0, b1, "Body")
        A.parts.append((tube("Stalk", [b0, b1], [0.0028, 0.0022], 5, mats, "Fur2"), "Eye." + sd))
        A.parts.append((sphere("EyeBall", 0.0042, b1 + V((0, 0, 0.002)), mats, "Eye", 8, 5), "Eye." + sd))
        # claws: arm (2 segments) + palm + fixed finger + moving finger
        s0 = V((0.038, sy * 0.040, zb - 0.004))
        s1 = s0 + V((0.020, sy * 0.030, 0.004))
        s2 = s1 + V((0.032, sy * 0.004, 0.006))
        A.bone("Claw1." + sd, s0, s1, "Body")
        A.bone("Claw2." + sd, s1, s2, "Claw1." + sd)
        A.parts.append((tube("Arm", [s0, s1], [0.0065, 0.0060], 6, mats, "Fur"), "Claw1." + sd))
        palm = sphere("Palm", 1.0, (0, 0, 0), mats, "Fur", 10, 7)
        for v in palm.data.vertices:
            v.co = s1 + V((v.co.x * 0.022 + 0.018, v.co.y * 0.012, v.co.z * 0.014))
        A.parts.append((palm, "Claw2." + sd))
        f0 = s1 + V((0.036, -sy * 0.002, -0.003))
        A.parts.append((retube(tube("Finger", [f0, f0 + V((0.024, -sy * 0.006, -0.004))], [0.0060, 0.0012], 6, mats,
                                    "Fur"), mats, "Tip"), "Claw2." + sd))
        m0 = s1 + V((0.034, -sy * 0.002, 0.006))
        A.bone("Pincer." + sd, m0, m0 + V((0.022, -sy * 0.004, 0.002)), "Claw2." + sd)
        A.parts.append((retube(tube("Pincer", [m0, m0 + V((0.024, -sy * 0.005, 0.0))], [0.0052, 0.0011], 6, mats,
                                    "Fur"), mats, "Tip"), "Pincer." + sd))
        # four walking legs: coxa at the carapace rim, knee up and out, tip on the ground
        for i in range(4):
            a = math.radians(70 + 26 * i)      # from front-side to back-side
            hip = V((0.040 * math.cos(a) * 0.9, sy * 0.058 * math.sin(a), zb - 0.006))
            out = V((math.cos(a) * 0.35, sy * math.sin(a), 0)).normalized()
            knee = hip + out * 0.032 + V((0, 0, 0.016))
            toe = knee + out * 0.030 + V((0, 0, -knee.z + 0.002))
            A.bone("LegA%d.%s" % (i, sd), hip, knee, "Body")
            A.bone("LegB%d.%s" % (i, sd), knee, toe, "LegA%d.%s" % (i, sd))
            A.parts.append((tube("LegA", [hip, knee], [0.0050, 0.0042], 5, mats, "Fur"), "LegA%d.%s" % (i, sd)))
            A.parts.append((tube("LegB", [knee, knee.lerp(toe, 0.75), toe], [0.0040, 0.0030, 0.0008], 5, mats,
                                 "Fur"), "LegB%d.%s" % (i, sd)))

    def walk(t):
        """Sideways scuttle along +Y (glTF -Z): alternating tetrapod groups, body sway."""
        ph = 2 * math.pi * t
        p = {"_loc": (0, 0.004 * math.sin(2 * ph), 0.002 * abs(math.sin(2 * ph)))}
        p["Body"] = (3 * math.sin(2 * ph), 0, 2 * math.sin(ph))
        for sd, sy in (("L", 1), ("R", -1)):
            for i in range(4):
                grp = (i + (0 if sd == "L" else 1)) % 2
                c = 2 * ph + grp * math.pi
                lift = max(0.0, math.sin(c)) * 28
                reach = math.cos(c) * 14 * sy
                p["LegA%d.%s" % (i, sd)] = (sy * lift + reach, 0, 6 * math.cos(c) * (1 if i < 2 else -1))
                p["LegB%d.%s" % (i, sd)] = (-reach * 1.2 - sy * lift * 0.6, 0, 0)
            p["Claw1." + sd] = (sy * 6 * math.sin(2 * ph), 0, sy * 5)
            p["Pincer." + sd] = (0, -10, 0)
            p["Eye." + sd] = (sy * 8 * math.sin(ph), 0, 0)
        return p

    def idle(t):
        ph = 2 * math.pi * t
        p = {"_loc": (0, 0, 0.0008 * math.sin(ph))}
        snap = max(0.0, math.sin(4 * ph)) ** 3
        for sd, sy in (("L", 1), ("R", -1)):
            p["Claw1." + sd] = (sy * (10 + 8 * math.sin(ph)), -12 * math.sin(ph), 0)
            p["Claw2." + sd] = (0, -10 * math.sin(ph + 0.5), 0)
            p["Pincer." + sd] = (0, -28 * snap if sd == "L" else -20 * max(0, math.sin(4 * ph + 2)) ** 3, 0)
            p["Eye." + sd] = (sy * 10 * math.sin(2 * ph + (0 if sd == "L" else 1.3)), 0,
                              sy * 12 * math.sin(ph))
            for i in range(4):
                p["LegA%d.%s" % (i, sd)] = (sy * 3 * math.sin(ph + i), 0, 0)
        return p
    return finish(A, q, mats, [("Idle", 48, idle), ("Walk", 16, walk)], 0.005, 0)


BUILD = {"dog": lambda: build_quadruped("dog"), "cat": lambda: build_quadruped("cat"),
         "bird": lambda: build_bird("bird"), "parrot": lambda: build_bird("parrot"), "crab": build_crab}

if __name__ == "__main__":
    for k in (sys.argv[1:] or list(BUILD)):
        p, t = BUILD[k]()
        print("[animal] %s: %d tris" % (p, t))
