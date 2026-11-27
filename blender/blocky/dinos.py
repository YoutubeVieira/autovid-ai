"""Dinosaures en blocs articules (T-Rex, Tricératops, Brachiosaure) + décor préhistorique, pour Blender (bpy).
Chaque dinosaure est une hiérarchie d'empties-pivots: on anime les rotations (marche, rugissement, regard)."""
import math
import random

import bpy
from mathutils import Matrix, Vector

import blocky as bk
import city
from city import H, _Static

P = city.PAL["primaires"]
BB = city.PAL["bois_brique"]


def _bevel(ob, w=0.04):
    m = ob.modifiers.new("Bevel", 'BEVEL')
    m.width, m.segments, m.limit_method = w, 2, 'ANGLE'


def pivot(col, name, parent=None, loc=(0, 0, 0)):
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = 0.2
    e.rotation_mode = 'XYZ'
    col.objects.link(e)
    if parent:
        e.parent = parent
    e.location = loc
    return e


def block(col, name, parent, center, size, material, rot=None, bevel=0.04):
    b = _Static(name)
    b.box(center, size, "hips", material, rot=rot)
    ob = b.finish(col)
    ob.parent = parent
    _bevel(ob, bevel)
    return ob


def emissive(name, rgb, strength):
    m = bk.mat(name, rgb, 0.4)
    bs = m.node_tree.nodes["Principled BSDF"]
    bs.inputs["Emission Color"].default_value = (*(c ** 2.2 for c in rgb), 1)
    bs.inputs["Emission Strength"].default_value = strength
    return m


def _eyes(col, head, sx_off=0.5, z=0.25, y=-0.3, s=0.2):
    """Deux jeux d'yeux commutables: 'normal' et 'scared' (grands, pupilles minuscules)."""
    WHT, BLK = bk.mat("white", (0.95, 0.95, 0.95)), bk.mat("face_black", (0.02, 0.02, 0.03), 0.3)
    sets = {"normal": [], "scared": []}
    for sx in (-1, 1):
        sets["normal"] += [block(col, "eye", head, (sx * sx_off, y, z), (s, 0.08, s), WHT, bevel=0.01),
                           block(col, "pupil", head, (sx * sx_off, y - 0.045, z), (s * 0.5, 0.05, s * 0.5), BLK, bevel=0.01)]
        sets["scared"] += [block(col, "eye", head, (sx * sx_off, y, z + 0.02), (s * 1.5, 0.08, s * 1.6), WHT, bevel=0.01),
                           block(col, "pupil", head, (sx * sx_off, y - 0.045, z), (s * 0.25, 0.05, s * 0.3), BLK, bevel=0.01)]
    for o in sets["scared"]:
        o.hide_render = o.hide_viewport = True
    return sets


def make_trex(col, name="TRex"):
    RED, ORG, WHT = bk.mat(f"{name}_r", H(P["rouge"]), 0.5), bk.mat(f"{name}_o", H(P["or"]), 0.5), bk.mat("tooth", (0.95, 0.93, 0.85), 0.4)
    root = pivot(col, name)
    hip = pivot(col, name + "_hip", root, (0, 0, 2.0))
    block(col, "body", hip, (0, 0, 0), (1.3, 2.4, 1.4), RED)
    block(col, "belly", hip, (0, -0.05, -0.62), (1.0, 2.2, 0.2), ORG)
    t1 = pivot(col, "t1", hip, (0, 1.2, 0.2)); block(col, "tail1", t1, (0, 0.8, 0), (0.9, 1.6, 0.9), RED)
    t2 = pivot(col, "t2", t1, (0, 1.6, 0)); block(col, "tail2", t2, (0, 0.9, 0), (0.6, 1.8, 0.6), RED)
    t3 = pivot(col, "t3", t2, (0, 1.8, 0)); block(col, "tail3", t3, (0, 0.8, 0), (0.35, 1.6, 0.35), RED)
    neck = pivot(col, "neck", hip, (0, -1.1, 0.5)); block(col, "neckb", neck, (0, -0.3, 0.3), (0.8, 0.9, 0.9), RED)
    head = pivot(col, "head", neck, (0, -0.6, 0.5)); block(col, "headb", head, (0, -0.55, 0.1), (0.95, 1.4, 0.85), RED)
    jaw = pivot(col, "jaw", head, (0, -0.1, -0.25)); block(col, "jawb", jaw, (0, -0.5, -0.05), (0.8, 1.1, 0.25), ORG)
    for k in range(4):
        for sx in (-1, 1):
            block(col, "tooth", jaw, (sx * 0.3, -0.25 - k * 0.22, 0.12), (0.07, 0.07, 0.14), WHT, bevel=0.01)
    eyes = _eyes(col, head, 0.5, 0.25, -0.45, 0.2)
    legs = {}
    for sx, side in ((-1, "R"), (1, "L")):
        th = pivot(col, "thigh" + side, hip, (sx * 0.7, 0, -0.5)); block(col, "thighb", th, (0, 0, -0.45), (0.55, 0.7, 1.0), RED)
        sh = pivot(col, "shin" + side, th, (0, 0, -0.95)); block(col, "shinb", sh, (0, -0.1, -0.42), (0.4, 0.5, 0.85), RED)
        block(col, "foot", sh, (0, -0.32, -0.9), (0.5, 0.9, 0.2), ORG)
        legs[side] = (th, sh)
        ar = pivot(col, "arm" + side, hip, (sx * 0.7, -1.0, 0.1)); block(col, "armb", ar, (0, -0.2, -0.2), (0.15, 0.15, 0.5), RED)
    return dict(root=root, hip=hip, head=head, jaw=jaw, neck=neck, tail=[t1, t2, t3], legs=legs, eyes=eyes, kind="trex", legsw=[("L", 1), ("R", -1)])


def make_trice(col, name="Trice"):
    BLU, BRN, WHT = bk.mat(f"{name}_b", H(P["bleu_ciel"]), 0.5), bk.mat(f"{name}_f", H(BB["brun"]), 0.5), bk.mat("horn", (0.95, 0.92, 0.82), 0.4)
    root = pivot(col, name)
    hip = pivot(col, name + "_hip", root, (0, 0, 1.15))
    block(col, "body", hip, (0, 0, 0), (1.5, 2.4, 1.2), BLU)
    t1 = pivot(col, "t1", hip, (0, 1.2, 0.1)); block(col, "tail1", t1, (0, 0.7, 0), (0.6, 1.4, 0.5), BLU)
    head = pivot(col, "head", hip, (0, -1.2, 0.1))
    block(col, "headb", head, (0, -0.55, 0), (0.85, 1.1, 0.8), BLU)
    block(col, "frill", head, (0, 0.1, 0.35), (1.7, 0.18, 1.5), BRN)
    for sx in (-1, 1):
        block(col, "horn", head, (sx * 0.28, -1.0, 0.35), (0.13, 1.0, 0.13), WHT, rot=Matrix.Rotation(-0.35, 3, 'X'), bevel=0.01)
    block(col, "nose", head, (0, -1.0, -0.05), (0.18, 0.35, 0.2), WHT, bevel=0.01)
    jaw = pivot(col, "jaw", head, (0, -0.1, -0.3)); block(col, "jawb", jaw, (0, -0.5, -0.05), (0.6, 0.9, 0.18), BRN)
    eyes = _eyes(col, head, 0.42, 0.18, -0.5, 0.17)
    legs = {}
    for sx, sy, k in ((-1, -0.8, "FR"), (1, -0.8, "FL"), (-1, 0.8, "BR"), (1, 0.8, "BL")):
        th = pivot(col, "leg" + k, hip, (sx * 0.65, sy, -0.5)); block(col, "legb", th, (0, 0, -0.4), (0.45, 0.5, 0.9), BLU)
        block(col, "foot", th, (0, -0.05, -0.85), (0.5, 0.6, 0.15), BRN)
        legs[k] = (th, None)
    return dict(root=root, hip=hip, head=head, jaw=jaw, neck=None, tail=[t1], legs=legs, eyes=eyes, kind="trice",
                legsw=[("FL", 1), ("BR", 1), ("FR", -1), ("BL", -1)])


def make_brachio(col, name="Brachio"):
    GRN, TAN = bk.mat(f"{name}_g", H(P["vert"]), 0.5), bk.mat(f"{name}_t", H(city.PAL["pierre_sable"]["creme"]), 0.5)
    root = pivot(col, name)
    hip = pivot(col, name + "_hip", root, (0, 0, 3.0))
    block(col, "body", hip, (0, 0, 0), (1.8, 3.0, 1.7), GRN)
    block(col, "belly", hip, (0, 0, -0.78), (1.4, 2.6, 0.2), TAN)
    t1 = pivot(col, "t1", hip, (0, 1.5, 0.2)); block(col, "tail1", t1, (0, 0.9, 0), (0.9, 1.8, 0.8), GRN)
    t2 = pivot(col, "t2", t1, (0, 1.8, 0)); block(col, "tail2", t2, (0, 0.9, 0), (0.5, 1.8, 0.45), GRN)
    n1 = pivot(col, "n1", hip, (0, -1.4, 0.6)); block(col, "neck1", n1, (0, -0.2, 0.9), (0.6, 0.7, 1.9), GRN, rot=None)
    n2 = pivot(col, "n2", n1, (0, -0.1, 1.9)); block(col, "neck2", n2, (0, -0.1, 0.9), (0.5, 0.6, 1.9), GRN)
    n3 = pivot(col, "n3", n2, (0, -0.1, 1.85)); block(col, "neck3", n3, (0, -0.1, 0.7), (0.45, 0.55, 1.5), GRN)
    head = pivot(col, "head", n3, (0, -0.1, 1.4)); block(col, "headb", head, (0, -0.3, 0.1), (0.55, 0.9, 0.5), GRN)
    jaw = pivot(col, "jaw", head, (0, -0.1, -0.1)); block(col, "jawb", jaw, (0, -0.3, -0.02), (0.4, 0.6, 0.1), TAN)
    eyes = _eyes(col, head, 0.3, 0.2, -0.3, 0.14)
    legs = {}
    for sx, sy, k in ((-1, -1.0, "FR"), (1, -1.0, "FL"), (-1, 1.0, "BR"), (1, 1.0, "BL")):
        th = pivot(col, "leg" + k, hip, (sx * 0.75, sy, -0.7)); block(col, "legb", th, (0, 0, -0.9), (0.65, 0.7, 1.9), GRN)
        block(col, "foot", th, (0, -0.05, -1.9), (0.7, 0.9, 0.2), TAN)
        legs[k] = (th, None)
    return dict(root=root, hip=hip, head=head, jaw=jaw, neck=n1, neckchain=[n1, n2, n3], tail=[t1, t2], legs=legs, eyes=eyes, kind="brachio",
                legsw=[("FL", 1), ("BR", 1), ("FR", -1), ("BL", -1)])


# ------------------------------------------------------------------ animation
def key(ob, prop, frame):
    ob.keyframe_insert(prop, frame=frame)


def place(d, f, loc=None, yaw=None, scale=None):
    r = d["root"]
    if loc is not None:
        r.location = loc
        key(r, "location", f)
    if yaw is not None:
        r.rotation_euler = (0, 0, math.radians(yaw))
        key(r, "rotation_euler", f)
    if scale is not None:
        r.scale = (scale,) * 3
        key(r, "scale", f)


def walk(d, f0, f1, p0, p1, cycle=28, amp=0.45, step=4):
    """Marche lineaire p0 -> p1 (le dino regarde vers -Y par defaut: yaw calcule)."""
    dv = Vector(p1) - Vector(p0)
    yaw = math.degrees(math.atan2(dv.x, -dv.y)) if dv.length > 1e-6 else 0
    bob = {"trex": 0.12, "trice": 0.06, "brachio": 0.1}[d["kind"]]
    for f in range(f0, f1 + 1, step):
        t = (f - f0) / max(1, f1 - f0)
        loc = Vector(p0).lerp(Vector(p1), t)
        ph = (f - f0) / cycle * 2 * math.pi
        place(d, f, (loc.x, loc.y, loc.z + abs(math.sin(ph)) * bob), yaw)
        for side, sgn in d["legsw"]:
            th, sh = d["legs"][side]
            th.rotation_euler = (sgn * amp * math.sin(ph), 0, 0)
            key(th, "rotation_euler", f)
            if sh is not None:
                sh.rotation_euler = (max(0, -sgn * math.sin(ph)) * 0.6, 0, 0)
                key(sh, "rotation_euler", f)
        for i, tp in enumerate(d["tail"]):
            tp.rotation_euler = (0, 0, 0.12 * math.sin(ph - i * 0.8))
            key(tp, "rotation_euler", f)


def pose(ob, f, rx=None, ry=None, rz=None):
    r = ob.rotation_euler
    ob.rotation_euler = (r.x if rx is None else rx, r.y if ry is None else ry, r.z if rz is None else rz)
    key(ob, "rotation_euler", f)


def roar(d, f0, dur=22):
    pose(d["head"], f0, rx=0); pose(d["jaw"], f0, rx=0)
    pose(d["head"], f0 + 5, rx=-0.5); pose(d["jaw"], f0 + 5, rx=0.65)
    pose(d["head"], f0 + dur - 4, rx=-0.45); pose(d["jaw"], f0 + dur - 4, rx=0.55)
    pose(d["head"], f0 + dur, rx=0); pose(d["jaw"], f0 + dur, rx=0)


def look_up(d, f0, f1, amount=-0.55):
    pose(d["head"], f0, rx=0)
    pose(d["head"], f1, rx=amount)
    if d.get("neckchain"):
        for n in d["neckchain"]:
            pose(n, f0, rx=0); pose(n, f1, rx=amount * 0.3)


def set_eyes(d, f, which):
    for k, objs in d["eyes"].items():
        for o in objs:
            o.hide_render = o.hide_viewport = (k != which)
            o.keyframe_insert("hide_render", frame=f)
            o.keyframe_insert("hide_viewport", frame=f)


# ------------------------------------------------------------------ decor
def tree_fern(col, loc, scale=1.0, seed=0):
    rnd = random.Random(seed)
    TR, LF = bk.mat("trunk", H(BB["brun"]), 0.7), bk.mat("fern", H(P["vert"]), 0.6)
    root = pivot(col, "tree", None, loc)
    root.scale = (scale,) * 3
    block(col, "trunk", root, (0, 0, 1.3), (0.4, 0.4, 2.6), TR, bevel=0.03)
    for k in range(7):
        a = k / 7 * 2 * math.pi
        block(col, "leaf", root, (math.cos(a) * 0.9, math.sin(a) * 0.9, 2.7 + rnd.uniform(-0.1, 0.1)), (1.7, 0.35, 0.12), LF,
              rot=Matrix.Rotation(a, 3, 'Z'), bevel=0.02)
    return root


def build_world(col, seed=4):
    rnd = random.Random(seed)
    G, D = bk.mat("pgrass", (0.16, 0.42, 0.12), 0.9), bk.mat("pdirt", (0.50, 0.33, 0.17), 0.9)
    ROCK, LAVA = bk.mat("prock", (0.30, 0.27, 0.26), 0.9), emissive("lava", (1.0, 0.35, 0.05), 9.0)
    SMOKE = bk.mat("smoke", (0.25, 0.24, 0.26), 0.9)
    st = _Static("PWorld")
    st.box((0, 40, -0.5), (300, 300, 1.0), "hips", G)
    st.box((0, 24, 0.02), (14, 70, 0.1), "hips", D)
    ob = st.finish(col)
    # montagnes et volcan
    for i, (x, y, r, h) in enumerate([(-60, 110, 22, 30), (-25, 125, 26, 36), (30, 120, 24, 28), (70, 105, 22, 24)]):
        b = _Static(f"mont{i}")
        b.cyl((x, y, h / 2), r, r * 0.18, h, "hips", ROCK, seg=5)
        b.finish(col)
    vb = _Static("volcan")
    vb.cyl((0, 150, 21), 38, 7, 42, "hips", ROCK, seg=6)
    vb.cyl((0, 150, 42), 7.4, 6.4, 1.2, "hips", LAVA, seg=6)
    vb.finish(col)
    for k in range(6):                                     # fumee
        sb = _Static(f"fumee{k}")
        sb.sphere((rnd.uniform(-3, 3), 150 + rnd.uniform(-2, 2), 46 + k * 4.5), 3.2 + k * 0.7, "hips", SMOKE)
        sb.finish(col)
    for k in range(40):                                    # fougeres
        tree_fern(col, (rnd.choice([-1, 1]) * rnd.uniform(10, 45), rnd.uniform(10, 95), 0), rnd.uniform(0.9, 1.7), k)
    for k in range(18):                                    # rochers
        b = _Static(f"roc{k}")
        b.box((rnd.choice([-1, 1]) * rnd.uniform(8, 40), rnd.uniform(5, 80), 0.5), (rnd.uniform(0.8, 2.2),) * 3, "hips", ROCK)
        b.finish(col)


def build_sky(scene):
    world = bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.sky_type = 'MULTIPLE_SCATTERING'
    sky.sun_elevation = math.radians(42)
    sky.sun_rotation = math.radians(200)
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = 'RGBA'
    mix.inputs[7].default_value = (0.20, 0.05, 0.02, 1)       # fond d'apocalypse: braise sombre
    bg = nt.nodes.new("ShaderNodeBackground")
    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(sky.outputs["Color"], mix.inputs[6])
    nt.links.new(mix.outputs[2], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    bg.inputs["Strength"].default_value = 0.3
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 20))
    sun = bpy.context.active_object
    sun.data.energy = 2.6
    sun.data.color = (1.0, 0.95, 0.85)
    sun.rotation_euler = (math.radians(48), 0, math.radians(30))
    return sky, mix, bg, sun
