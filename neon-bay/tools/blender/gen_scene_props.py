"""Neon Bay - static set dressing for the beach, baile funk and prison-yard scenes.

    python3 tools/blender/gen_scene_props.py                     # every prop
    python3 tools/blender/gen_scene_props.py parasol dj_booth    # some of them

Writes models/prop_<id>.glb (+ .glb.js), each <= 3000 triangles, static (no armature):
    prop_lifeguard_tower  wooden lifeguard post on stilts: deck, hut, ramp, railings, flag
    prop_parasol          striped beach umbrella (16 panels, ribs, valance)
    prop_towel            beach towel with stripes, wrinkles and a rolled end
    prop_dj_booth         DJ booth: two turntables, mixer, laptop, emissive LED screen (texture)
    prop_speaker_stack    party wall of speakers (subs, mids, horns), neon edge strips
    prop_weights          prison-yard weight bench with rack, barbell and plates, two dumbbells
    prop_dumbbell         one dumbbell, origin at the grip (for the Workout clip, HandR / HandL)
    prop_rescue_tube      red rescue tube, origin at the strap end (to hang from HandL)
Origin on the ground at the centre, up +Y (glTF), metres; the "front" (deck ladder, DJ side
facing the crowd, speaker cones, bench foot end) faces +Z in glTF (= Blender -Y), like gen_props.py.
Materials are plain PBR colours with contract-like names (Wood, Paint, Fabric/Fabric2, Metal,
Screen and Neon are emissive); only the DJ screen carries a texture (equaliser bars).
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import bmesh  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402

import nb_common as nb  # noqa: E402
from gen_props import tube, lathe_obj, fix_normals, finish  # noqa: E402

V = Vector


def bx(name, size, loc, mat, bevel=0.0, seg=1):
    return nb.box(name, size, loc, mat, bevel=bevel, segments=seg)


def turn(o, c, rx=0.0, ry=0.0):
    """Rotate a mesh object's vertices (radians, about X then Y) around the point c."""
    from mathutils import Matrix
    R = Matrix.Rotation(ry, 3, "Y") @ Matrix.Rotation(rx, 3, "X")
    c = V(c)
    for v in o.data.vertices:
        v.co = R @ (v.co - c) + c
    return o


def cyl(name, r, depth, loc, mat, n=10, axis="Z", r2=None):
    return nb.cylinder(name, r, depth, loc, n, mat, axis, r2)


def beam(name, a, b, w, mat, sides=4):
    """Square-ish timber between two points (a 4-sided tube)."""
    return tube(name, [a, b], [w, w], sides, mat, cap_end=True, cap_start=True)


# --------------------------------------------------------------------------- lifeguard tower
def make_lifeguard_tower():
    wood = nb.material("Wood", (0.62, 0.47, 0.32), roughness=0.85)
    dark = nb.material("WoodDark", (0.36, 0.25, 0.16), roughness=0.85)
    paint = nb.material("Paint", (0.10, 0.62, 0.66), roughness=0.6)
    white = nb.material("Trim", (0.93, 0.92, 0.88), roughness=0.6)
    roof = nb.material("Roof", (0.80, 0.10, 0.08), roughness=0.55)
    metal = nb.material("Metal", (0.7, 0.7, 0.72), metallic=1.0, roughness=0.35)
    flag = nb.material("Flag", (0.85, 0.08, 0.06), roughness=0.7)
    flag2 = nb.material("Flag2", (1.0, 0.82, 0.10), roughness=0.7)
    glass = nb.material("Glass", (0.25, 0.35, 0.42), metallic=0.3, roughness=0.08)
    P = []
    H = 1.70                           # deck height
    hw, hd = 1.05, 1.05                # deck half size
    for x in (-0.9, 0.9):
        for y in (-0.9, 0.9):
            P.append(cyl("Post", 0.075, H + 0.02, (x, y, (H + 0.02) / 2), wood, 8))
            P.append(cyl("Foot", 0.11, 0.12, (x, y, 0.06), dark, 8))
    for y in (-0.9, 0.9):              # X braces on the sides and back
        P.append(beam("Brace", V((-0.9, y, 0.25)), V((0.9, y, H - 0.15)), 0.035, dark))
        P.append(beam("Brace", V((0.9, y, 0.25)), V((-0.9, y, H - 0.15)), 0.035, dark))
    for x in (-0.9, 0.9):
        P.append(beam("Brace", V((x, -0.9, 0.25)), V((x, 0.9, H - 0.15)), 0.035, dark))
    P.append(beam("Brace", V((-0.9, 0.9, 0.25)), V((0.9, 0.9, H - 0.15)), 0.035, dark))
    # deck: joists + planks with gaps
    for y in (-0.9, 0.0, 0.9):
        P.append(bx("Joist", (2.2, 0.08, 0.12), (0, y, H - 0.06), dark))
    n = 13
    for i in range(n):
        y = -hd + (i + 0.5) * (2 * hd / n)
        P.append(bx("Plank", (2 * hw, 2 * hd / n - 0.018, 0.04), (0, y, H + 0.02), wood))
    # hut on the back two thirds of the deck
    hy0, hy1, hx = -0.25, 1.0, 0.95
    hh = 1.35
    z0 = H + 0.04
    P.append(bx("WallBack", (2 * hx, 0.06, hh), (0, hy1, z0 + hh / 2), paint))
    for sx in (-1, 1):
        P.append(bx("WallSide", (0.06, hy1 - hy0, hh), (sx * hx, (hy0 + hy1) / 2, z0 + hh / 2), paint))
        # side windows (frame + glass)
        P.append(bx("WinFrame", (0.07, 0.62, 0.45), (sx * (hx + 0.006), 0.42, z0 + 0.95), white))
        P.append(bx("WinGlass", (0.075, 0.52, 0.35), (sx * (hx + 0.008), 0.42, z0 + 0.95), glass))
    # front wall: low wall + wide open window + lintel
    P.append(bx("WallFront", (2 * hx, 0.06, 0.55), (0, hy0, z0 + 0.275), paint))
    P.append(bx("Lintel", (2 * hx, 0.07, 0.25), (0, hy0, z0 + hh - 0.125), paint))
    for x in (-hx + 0.05, 0, hx - 0.05):
        P.append(bx("Mullion", (0.07, 0.07, hh - 0.8), (x, hy0, z0 + 0.55 + (hh - 0.8) / 2), white))
    P.append(bx("Sill", (2 * hx + 0.08, 0.16, 0.04), (0, hy0 - 0.02, z0 + 0.57), white))
    # horizontal siding grooves on the walls (thin dark battens)
    for k in range(1, 5):
        z = z0 + k * hh / 5
        P.append(bx("Batten", (2 * hx + 0.01, 0.065, 0.012), (0, hy1 + 0.002, z), dark))
    # roof: two slopes + ridge, overhanging
    rz = z0 + hh
    for sy in (-1, 1):
        a = math.radians(18)
        L = 0.85
        cy = 0.375 + sy * L * math.cos(a) / 2
        c = (0, cy, rz + 0.20 - L * math.sin(a) / 2)
        P.append(turn(bx("Roof", (2 * hx + 0.35, L + 0.1, 0.05), c, roof), c, sy * a))
    P.append(cyl("Ridge", 0.045, 2 * hx + 0.38, (0, 0.375, rz + 0.22), white, 8, "X"))
    # front porch railing (three sides) on the open front part
    py = -hd + 0.05
    for x in (-hw + 0.04, -0.35, 0.35, hw - 0.04):
        if abs(x) < 0.4 and abs(x) > 0.3:
            continue
        P.append(bx("Baluster", (0.06, 0.06, 0.95), (x, py, H + 0.5), white))
    for z in (H + 0.5, H + 0.95):
        P.append(bx("Rail", (0.75, 0.07, 0.06), (-hw + 0.38, py, z), white))
        P.append(bx("Rail", (0.75, 0.07, 0.06), (hw - 0.38, py, z), white))
        for sx in (-1, 1):
            P.append(bx("Rail", (0.07, abs(hy0 - py), 0.06), (sx * (hw - 0.04), (py + hy0) / 2, z), white))
    for sx in (-1, 1):
        P.append(bx("Baluster", (0.06, 0.06, 0.95), (sx * (hw - 0.04), (py + hy0) / 2, H + 0.5), white))
    # ramp with cleats down to the sand (front, -Y)
    rl = 2.6
    ang = math.atan2(H, rl)
    ramp_c = V((0, -hd - rl / 2 + 0.05, H / 2))
    for sx in (-1, 1):
        P.append(beam("Stringer", V((sx * 0.33, -hd + 0.02, H + 0.02)), V((sx * 0.33, -hd - rl, 0.03)), 0.05, dark))
        P.append(beam("Handrail", V((sx * 0.37, -hd, H + 0.85)), V((sx * 0.37, -hd - rl + 0.2, 0.85)), 0.03, white,
                      6))
        for t in (0.35, 0.7):
            q = V((sx * 0.37, -hd - (rl - 0.2) * t, H + 0.85 - (H) * t))
            P.append(beam("RailPost", q, V((q.x, q.y, q.z - 0.85)), 0.025, white))
    P.append(turn(bx("RampDeck", (0.70, math.hypot(rl, H), 0.035), tuple(ramp_c), wood), ramp_c, ang))
    for i in range(9):
        t = (i + 0.5) / 9
        c = V((0, -hd - rl * t, H * (1 - t) + 0.04))
        P.append(turn(bx("Cleat", (0.66, 0.04, 0.03), tuple(c), dark), c, ang))
    # flag pole on the roof ridge + waving flag (two colour halves)
    top = V((hx - 0.15, 0.375, rz + 0.24))
    P.append(cyl("Pole", 0.022, 1.6, tuple(top + V((0, 0, 0.8))), metal, 8))
    P.append(nb.uv_sphere("PoleCap", 0.04, top + V((0, 0, 1.62)), 8, 5, metal))
    nu, nv = 10, 4
    verts, faces, fm = [], [], []
    for i in range(nu + 1):
        u = i / nu
        for j in range(nv + 1):
            vv = j / nv
            x = -0.03 - 0.85 * u
            z = top.z + 1.55 - 0.5 * vv - 0.04 * u
            y = top.y + 0.07 * math.sin(u * 2 * math.pi * 1.3) * u
            verts.append((top.x + x, y, z))
    for i in range(nu):
        for j in range(nv):
            a = i * (nv + 1) + j
            faces.append((a, a + nv + 1, a + nv + 2, a + 1))
            fm.append(0 if j < nv // 2 else 1)
    fl = nb.mesh_object("Flag", verts, faces, [flag, flag2], fm)
    flag.use_backface_culling = False
    flag2.use_backface_culling = False
    P.append(fl)
    # life ring on the railing + a board leaning on a post
    ring_c = V((hw - 0.38, py - 0.06, H + 0.62))
    pts = [ring_c + V((math.cos(a) * 0.22, 0, math.sin(a) * 0.22)) for a in
           (2 * math.pi * i / 14 for i in range(15))]
    P.append(tube("LifeRing", pts, [0.055] * 15, 6, flag, cap_end=False))
    return finish("LifeguardTower", P, 35)


# --------------------------------------------------------------------------- parasol
def make_parasol():
    fab = nb.material("Fabric", (0.95, 0.94, 0.90), roughness=0.8)
    fab2 = nb.material("Fabric2", (0.90, 0.20, 0.25), roughness=0.8)
    metal = nb.material("Metal", (0.85, 0.85, 0.86), metallic=1.0, roughness=0.3)
    wood = nb.material("Wood", (0.55, 0.40, 0.26), roughness=0.7)
    for m in (fab, fab2):
        m.use_backface_culling = False
    P = []
    H, R, N = 2.25, 1.05, 16
    P.append(cyl("Pole", 0.022, H, (0, 0, H / 2), wood, 10))
    P.append(cyl("Base", 0.06, 0.05, (0, 0, 0.025), metal, 10, r2=0.03))    # sand anchor collar
    P.append(cyl("Joint", 0.032, 0.08, (0, 0, 1.2), metal, 10))
    P.append(cyl("Runner", 0.035, 0.10, (0, 0, H - 0.45), metal, 10))
    # canopy: N panels, each a curved fan (rings), double-sided, stripe colours alternate
    rings = 5
    verts, faces, fm = [], [], []
    apex = V((0, 0, H + 0.05))
    for k in range(N):
        a0, a1 = 2 * math.pi * k / N, 2 * math.pi * (k + 1) / N
        base = len(verts)
        verts.append(tuple(apex))
        for r in range(1, rings + 1):
            t = r / rings
            for a in (a0, (a0 + a1) / 2, a1):
                sag = 0.035 * math.sin(math.pi * t) * (1 if a == (a0 + a1) / 2 else 0) * -1
                rr = R * t * (0.96 if a == (a0 + a1) / 2 else 1.0)
                z = apex.z - 0.42 * t ** 1.4 + sag
                verts.append((rr * math.cos(a), rr * math.sin(a), z))
        for r in range(rings):
            if r == 0:
                faces += [(base, base + 1, base + 2), (base, base + 2, base + 3)]
                fm += [k % 2] * 2
                continue
            a = base + 1 + (r - 1) * 3
            b = a + 3
            faces += [(a, b, b + 1, a + 1), (a + 1, b + 1, b + 2, a + 2)]
            fm += [k % 2] * 2
        # valance flap
        e0 = base + 1 + (rings - 1) * 3
        p0, p2 = V(verts[e0]), V(verts[e0 + 2])
        vb = len(verts)
        pm = (p0 + p2) / 2 * 0.985
        verts += [tuple(p0), tuple(p2), tuple(p2 - V((0, 0, 0.11))), tuple(pm - V((0, 0, 0.16))),
                  tuple(p0 - V((0, 0, 0.11)))]
        faces.append((vb, vb + 4, vb + 3, vb + 2, vb + 1))
        fm.append((k + 1) % 2)
    can = nb.mesh_object("Canopy", verts, faces, [fab, fab2], fm)
    fix_normals(can)
    P.append(can)
    # ribs + stretchers
    for k in range(N):
        a = 2 * math.pi * k / N
        d = V((math.cos(a), math.sin(a), 0))
        pts = [apex - V((0, 0, 0.02))] + [d * (R * t) + V((0, 0, apex.z - 0.42 * t ** 1.4 - 0.015)) for t in
                                          (0.35, 0.7, 1.0)]
        P.append(tube("Rib", pts, [0.006] * 4, 3, metal, cap_end=True))
        if k % 2 == 0:
            P.append(tube("Stretcher", [V((0, 0, H - 0.45)), d * (R * 0.45) + V((0, 0, apex.z - 0.42 * 0.33))],
                          [0.005, 0.005], 3, metal))
    P.append(nb.uv_sphere("Finial", 0.035, apex + V((0, 0, 0.04)), 8, 5, wood))
    return finish("Parasol", P, 50)


# --------------------------------------------------------------------------- towel
def make_towel():
    t1 = nb.material("Towel", (0.10, 0.55, 0.85), roughness=0.95)
    t2 = nb.material("Towel2", (0.98, 0.85, 0.20), roughness=0.95)
    rnd = random.Random(3)
    L, W, th = 1.6, 0.85, 0.006
    nx, ny = 24, 10
    verts, faces, fm = [], [], []

    def h(x, y):
        return (0.008 * math.sin(x * 7.0 + 0.6) * math.sin(y * 9.0) + 0.006 * math.sin(x * 13 + y * 5) +
                0.012 * max(0.0, math.sin(y * 4 + 1.0)) * math.exp(-((x - 0.3) / 0.25) ** 2))
    for i in range(nx + 1):
        for j in range(ny + 1):
            x = -L / 2 + L * i / nx
            y = -W / 2 + W * j / ny
            verts.append((x, y, th + h(x, y)))
    off = len(verts)
    for i in range(nx + 1):
        for j in range(ny + 1):
            x, y, z = verts[i * (ny + 1) + j]
            verts.append((x, y, z - th))
    for i in range(nx):
        stripe = 1 if (i // 2) % 3 == 1 or i in (1, nx - 2) else 0
        for j in range(ny):
            a = i * (ny + 1) + j
            faces.append((a, a + ny + 1, a + ny + 2, a + 1))
            faces.append((off + a + 1, off + a + ny + 2, off + a + ny + 1, off + a))
            fm += [stripe, stripe]
    for i in range(nx):                            # long edges
        for j in (0, ny):
            a, b = i * (ny + 1) + j, (i + 1) * (ny + 1) + j
            faces.append((a, off + a, off + b, b) if j == 0 else (b, off + b, off + a, a))
            fm.append(0)
    for i in (0, nx):
        for j in range(ny):
            a, b = i * (ny + 1) + j, i * (ny + 1) + j + 1
            faces.append((b, off + b, off + a, a) if i == 0 else (a, off + a, off + b, b))
            fm.append(0)
    tw = nb.mesh_object("Towel", verts, faces, [t1, t2], fm)
    fix_normals(tw)
    P = [tw]
    # rolled end (pillow) and fringe
    P.append(cyl("Roll", 0.07, W * 0.92, (L / 2 - 0.02, 0, 0.07), t2, 14, "Y"))
    P.append(cyl("RollIn", 0.035, W * 0.925, (L / 2 - 0.02, 0, 0.07), t1, 10, "Y"))
    for j in range(14):
        y = -W / 2 + 0.03 + (W - 0.06) * j / 13
        P.append(bx("Fringe", (0.05, 0.008, 0.003), (-L / 2 - 0.025, y + rnd.uniform(-0.004, 0.004), 0.003), t1))
    return finish("Towel", P, 50)


# --------------------------------------------------------------------------- DJ booth
def screen_texture(path):
    """Equaliser + neon grid frame for the booth LED screen (emissive colour map, 128 x 64)."""
    from PIL import Image
    w, h = 128, 64
    img = np.zeros((h, w, 3), np.float32)
    rng = np.random.RandomState(4)
    bars = 16
    for b in range(bars):
        hv = int(h * (0.25 + 0.7 * abs(math.sin(b * 0.7 + 0.3)) * rng.uniform(0.6, 1.0)))
        x0 = b * w // bars + 1
        for y in range(hv):
            t = y / h
            col = np.array([1.0, 0.1 + 0.8 * t, 0.9 - 0.8 * t]) if t < 0.75 else np.array([1.0, 0.95, 0.2])
            if y % 3 != 2:
                img[h - 1 - y, x0:x0 + w // bars - 2] = col
    img[:, ::8] *= 0.6
    img[0, :] = img[-1, :] = (0.1, 0.9, 1.0)
    Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8), "RGB").save(path, optimize=True)
    return path


def make_dj_booth():
    body = nb.material("Body", (0.05, 0.05, 0.06), roughness=0.5)
    metal = nb.material("Metal", (0.75, 0.75, 0.78), metallic=1.0, roughness=0.3)
    platter = nb.material("Platter", (0.10, 0.10, 0.11), roughness=0.35)
    vinyl = nb.material("Vinyl", (0.02, 0.02, 0.02), roughness=0.25)
    label = nb.material("Label", (0.95, 0.25, 0.55), roughness=0.5)
    neon = nb.material("Neon", (1.0, 0.1, 0.6), emission=(1.0, 0.1, 0.6), strength=6.0)
    neon2 = nb.material("Neon2", (0.1, 0.9, 1.0), emission=(0.1, 0.9, 1.0), strength=6.0)
    knob = nb.material("Knob", (0.85, 0.85, 0.85), roughness=0.4)
    screen = nb.material("Screen", (0.02, 0.02, 0.02), emission=(1, 1, 1), strength=3.0)
    import tempfile
    tex = screen_texture(os.path.join(tempfile.mkdtemp(prefix="nb_tex_"), "dj_screen.png"))
    nt = screen.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    it = nt.nodes.new("ShaderNodeTexImage")
    it.image = bpy.data.images.load(tex)
    nt.links.new(it.outputs["Color"], bsdf.inputs["Emission Color"])
    nt.links.new(it.outputs["Color"], bsdf.inputs["Base Color"])
    P = []
    W, D, H = 1.9, 0.75, 0.98
    P.append(bx("Desk", (W, D, 0.06), (0, 0, H - 0.03), body, 0.01))
    P.append(bx("Front", (W, 0.05, H - 0.06), (0, -D / 2 + 0.025, (H - 0.06) / 2), body, 0.01))
    for sx in (-1, 1):
        P.append(bx("Side", (0.05, D, H - 0.06), (sx * (W / 2 - 0.025), 0, (H - 0.06) / 2), body))
    # LED screen on the front (UV-mapped quad slightly proud of the panel)
    sw, sh = 1.5, 0.62
    z0 = 0.18
    scr = nb.mesh_object("Screen", [(-sw / 2, -D / 2 - 0.004, z0), (sw / 2, -D / 2 - 0.004, z0),
                                    (sw / 2, -D / 2 - 0.004, z0 + sh), (-sw / 2, -D / 2 - 0.004, z0 + sh)],
                         [(0, 1, 2, 3)], [screen])
    uv = scr.data.uv_layers.new(name="UVMap")
    for li, (a, b) in enumerate(((0, 0), (1, 0), (1, 1), (0, 1))):
        uv.data[li].uv = (a, b)
    P.append(scr)
    P.append(bx("Bezel", (sw + 0.06, 0.02, 0.03), (0, -D / 2 - 0.006, z0 - 0.015), metal))
    P.append(bx("Bezel", (sw + 0.06, 0.02, 0.03), (0, -D / 2 - 0.006, z0 + sh + 0.015), metal))
    # neon strips along the edges
    P.append(bx("NeonTop", (W, 0.02, 0.02), (0, -D / 2 - 0.01, H - 0.07), neon))
    P.append(bx("NeonLow", (W, 0.02, 0.02), (0, -D / 2 - 0.01, 0.07), neon2))
    for sx in (-1, 1):
        P.append(bx("NeonSide", (0.02, 0.02, H - 0.2), (sx * (W / 2 - 0.01), -D / 2 - 0.01, H / 2), neon2))
    # turntables
    for sx in (-1, 1):
        c = V((sx * 0.58, 0.02, H))
        P.append(bx("Deck", (0.46, 0.36, 0.08), (c.x, c.y, H + 0.04), body, 0.01))
        P.append(cyl("Platter", 0.150, 0.02, (c.x - sx * 0.03, c.y, H + 0.09), platter, 24))
        P.append(cyl("Vinyl", 0.145, 0.006, (c.x - sx * 0.03, c.y, H + 0.103), vinyl, 24))
        P.append(cyl("Label", 0.045, 0.008, (c.x - sx * 0.03, c.y, H + 0.104), label, 12))
        P.append(cyl("Spindle", 0.006, 0.03, (c.x - sx * 0.03, c.y, H + 0.11), metal, 6))
        arm_base = V((c.x + sx * 0.17, c.y + 0.12, H + 0.10))
        P.append(cyl("ArmBase", 0.025, 0.03, tuple(arm_base), metal, 10))
        P.append(tube("Tonearm", [arm_base + V((0, 0, 0.03)), arm_base + V((-sx * 0.04, -0.12, 0.03)),
                                  arm_base + V((-sx * 0.13, -0.19, 0.02))], [0.006] * 3, 5, metal))
        P.append(bx("Pitch", (0.03, 0.12, 0.012), (c.x + sx * 0.19, c.y - 0.08, H + 0.085), metal))
        P.append(cyl("StartBtn", 0.018, 0.01, (c.x - sx * 0.17, c.y - 0.14, H + 0.085), knob, 8))
    # mixer: body, knobs grid, faders
    P.append(bx("Mixer", (0.30, 0.36, 0.09), (0, 0.02, H + 0.045), body, 0.01))
    for i in range(4):
        for j in range(4):
            P.append(cyl("Knob", 0.012, 0.018, (-0.10 + i * 0.067, 0.16 - j * 0.055, H + 0.098), knob, 8))
    for i in range(4):
        P.append(bx("Fader", (0.012, 0.03, 0.016), (-0.10 + i * 0.067, -0.08 - 0.02 * (i % 2), H + 0.098), knob))
    P.append(bx("XFader", (0.04, 0.014, 0.016), (0.02, -0.135, H + 0.098), neon))
    # laptop on a stand behind the mixer
    P.append(bx("Stand", (0.28, 0.22, 0.10), (0, 0.27, H + 0.05), metal))
    lb = bx("LaptopBase", (0.34, 0.24, 0.018), (0, 0.25, H + 0.11), metal, 0.004)
    P.append(lb)
    c = (0, 0.38, H + 0.23)
    P.append(turn(bx("LaptopLid", (0.34, 0.012, 0.23), c, metal, 0.004), c, math.radians(-15)))
    return finish("DJBooth", P, 35)


# --------------------------------------------------------------------------- speaker stack
def make_speaker_stack():
    cab = nb.material("Cabinet", (0.06, 0.06, 0.07), roughness=0.8)
    cone = nb.material("Cone", (0.12, 0.12, 0.13), roughness=0.6)
    metal = nb.material("Metal", (0.65, 0.65, 0.68), metallic=1.0, roughness=0.3)
    grille = nb.material("Grille", (0.30, 0.30, 0.32), metallic=0.5, roughness=0.45)
    neon = nb.material("Neon", (0.2, 1.0, 0.3), emission=(0.2, 1.0, 0.3), strength=6.0)
    P = []

    def driver(c, r):
        prof = [(r, 0.0), (r * 0.92, -0.012), (r * 0.45, -0.07 * r / 0.2), (r * 0.18, -0.06 * r / 0.2),
                (r * 0.12, -0.035 * r / 0.2), (0.001, -0.02 * r / 0.2)]
        v, f = nb.lathe(prof, 16, axis="Y")
        v = [(x + c.x, -y + c.y, z + c.z) for x, y, z in v]
        o = nb.mesh_object("Cone", v, f, [cone])
        fix_normals(o)
        P.append(o)
        ring = [c + V((math.cos(a) * (r + 0.012), 0.002, math.sin(a) * (r + 0.012))) for a in
                (2 * math.pi * i / 16 for i in range(17))]
        P.append(tube("Surround", ring, [0.011] * 17, 4, metal, cap_end=False))

    def cabinet(x, z, w, h, d, kind):
        P.append(bx("Cab", (w, d, h), (x, 0, z + h / 2), cab, 0.012, 1))
        front = -d / 2 - 0.004
        for sx in (-1, 1):
            for sz in (0, 1):
                P.append(bx("Corner", (0.05, 0.05, 0.05), (x + sx * (w / 2 - 0.02), front + 0.02, z + 0.02 + sz *
                                                                     (h - 0.04)), metal))
        if kind == "sub":
            driver(V((x, front, z + h / 2)), min(w, h) * 0.40)
        elif kind == "mid":
            for k in (-1, 1):
                driver(V((x + k * w * 0.24, front, z + h * 0.45)), w * 0.19)
            P.append(bx("Port", (w * 0.6, 0.01, 0.03), (x, front, z + h * 0.85), grille))
        else:   # horn
            prof = [(0.0, 0.0)]
            hw_, hh_ = w * 0.42, h * 0.32
            fr = front - 0.012                     # horn mouth flange slightly proud of the baffle
            for sz in (-1, 1):                     # flange: top / bottom bars around the mouth
                P.append(bx("HornFlange", (2 * hw_ + 0.05, 0.02, 0.025), (x, fr, z + h / 2 + sz * (hh_ + 0.012)),
                            metal))
            v = [(x - hw_, fr, z + h / 2 - hh_), (x + hw_, fr, z + h / 2 - hh_),
                 (x + hw_, fr, z + h / 2 + hh_), (x - hw_, fr, z + h / 2 + hh_),
                 (x - 0.03, front + 0.10, z + h / 2 - 0.02), (x + 0.03, front + 0.10, z + h / 2 - 0.02),
                 (x + 0.03, front + 0.10, z + h / 2 + 0.02), (x - 0.03, front + 0.10, z + h / 2 + 0.02)]
            f = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7)]
            o = nb.mesh_object("Horn", v, f, [grille])
            bm = bmesh.new()
            bm.from_mesh(o.data)
            for fc in bm.faces:                    # the horn is seen from the inside: face the viewer
                if fc.calc_center_median().y > fr + 0.001 and fc.normal.y > 0.2:
                    fc.normal_flip()
            bm.to_mesh(o.data)
            bm.free()
            P.append(o)
            del prof
        # neon edge strip on the front bottom edge
        P.append(bx("Neon", (w - 0.08, 0.012, 0.012), (x, front - 0.004, z + 0.035), neon))
    for x in (-0.42, 0.42):
        cabinet(x, 0.0, 0.80, 0.80, 0.70, "sub")
        cabinet(x, 0.80, 0.80, 0.55, 0.60, "mid")
        cabinet(x, 1.35, 0.80, 0.38, 0.55, "horn")
    return finish("SpeakerStack", P, 35)


# --------------------------------------------------------------------------- weights
def plate(c, r, w, mat, axis="X"):
    prof = [(0.016, -w / 2), (r * 0.92, -w / 2), (r, -w / 2 + 0.006), (r, w / 2 - 0.006), (r * 0.92, w / 2),
            (0.016, w / 2)]
    v, f = nb.lathe(prof, 16, axis="X", cap_start=False, cap_end=False)
    v = [(x + c.x, y + c.y, z + c.z) for x, y, z in v]
    o = nb.mesh_object("Plate", v, f, [mat])
    fix_normals(o)
    return o


def dumbbell_parts(c, steel, rubber, axis_y=False):
    """Hex-ish dumbbell along X centred on c (grip at c)."""
    P = [cyl("Grip", 0.016, 0.14, tuple(c), steel, 8, "X")]
    for sx in (-1, 1):
        for k, (r, w) in enumerate(((0.065, 0.035), (0.058, 0.03))):
            P.append(plate(c + V((sx * (0.087 + k * 0.033), 0, 0)), r, w, rubber))
        P.append(cyl("Collar", 0.022, 0.016, tuple(c + V((sx * 0.062, 0, 0))), steel, 8, "X"))
    return P


def make_weights():
    steel = nb.material("Metal", (0.62, 0.63, 0.66), metallic=1.0, roughness=0.35)
    frame = nb.material("Frame", (0.12, 0.12, 0.13), metallic=0.6, roughness=0.5)
    pad = nb.material("Pad", (0.08, 0.08, 0.09), roughness=0.6)
    rubber = nb.material("Rubber", (0.05, 0.05, 0.05), roughness=0.8)
    paint = nb.material("Paint", (0.75, 0.12, 0.08), roughness=0.6)
    P = []
    # bench: pad + backrest along Y (foot end towards -Y = glTF +Z)
    P.append(bx("Seat", (0.30, 0.42, 0.07), (0, -0.40, 0.45), pad, 0.02, 2))
    P.append(bx("Back", (0.30, 0.80, 0.07), (0, 0.22, 0.45), pad, 0.02, 2))
    for y in (-0.55, 0.55):
        P.append(beam("Leg", V((0, y, 0.0)), V((0, y, 0.40)), 0.03, frame))
        P.append(beam("Foot", V((-0.24, y, 0.025)), V((0.24, y, 0.025)), 0.03, frame))
    P.append(beam("Spine", V((0, -0.58, 0.39)), V((0, 0.58, 0.39)), 0.035, frame))
    # rack uprights at the head end + J hooks
    for sx in (-1, 1):
        x = sx * 0.55
        P.append(beam("Upright", V((x, 0.62, 0.0)), V((x, 0.62, 1.15)), 0.035, paint))
        P.append(beam("Base", V((x, 0.40, 0.03)), V((x, 0.85, 0.03)), 0.035, paint))
        P.append(beam("Hook", V((x, 0.62, 0.95)), V((x, 0.55, 0.95)), 0.02, steel))
        P.append(beam("HookLip", V((x, 0.55, 0.95)), V((x, 0.55, 1.0)), 0.015, steel))
    P.append(beam("Cross", V((-0.55, 0.62, 0.15)), V((0.55, 0.62, 0.15)), 0.03, paint))
    # barbell on the hooks
    P.append(cyl("Bar", 0.014, 1.9, (0, 0.56, 0.99), steel, 8, "X"))
    for sx in (-1, 1):
        P.append(cyl("Sleeve", 0.025, 0.36, (sx * 0.78, 0.56, 0.99), steel, 8, "X"))
        P.append(plate(V((sx * 0.66, 0.56, 0.99)), 0.225, 0.05, rubber))
        P.append(plate(V((sx * 0.72, 0.56, 0.99)), 0.16, 0.04, rubber))
        P.append(cyl("Clip", 0.032, 0.02, (sx * 0.765, 0.56, 0.99), steel, 8, "X"))
    # two dumbbells on the ground + a plate leaning on the rack
    for k, x in enumerate((-0.35, 0.35)):
        P += dumbbell_parts(V((x, -0.85, 0.065)), steel, rubber)
    P.append(turn(plate(V((0.72, 0.0, 0.23)), 0.225, 0.05, rubber), (0.72, 0.0, 0.0), 0.0, math.radians(-12)))
    return finish("Weights", P, 40)


def make_dumbbell():
    steel = nb.material("Metal", (0.62, 0.63, 0.66), metallic=1.0, roughness=0.35)
    rubber = nb.material("Rubber", (0.05, 0.05, 0.05), roughness=0.8)
    return finish("Dumbbell", dumbbell_parts(V((0, 0, 0)), steel, rubber), 40)


# --------------------------------------------------------------------------- rescue tube
def make_rescue_tube():
    red = nb.material("Foam", (0.90, 0.06, 0.05), roughness=0.55)
    strap = nb.material("Strap", (0.95, 0.80, 0.10), roughness=0.7)
    metal = nb.material("Metal", (0.75, 0.75, 0.78), metallic=1.0, roughness=0.3)
    P = []
    # foam body along +X starting 0.42 m from the strap end (origin)
    L, r = 1.0, 0.075
    x0 = 0.42
    pts = [V((x0 + L * t, 0, 0)) for t in (0.0, 0.02, 0.06, 0.5, 0.94, 0.98, 1.0)]
    rad = [0.02, 0.055, r, r, r, 0.055, 0.02]
    body = tube("Tube", pts, rad, 12, red, cap_end=True, cap_start=True)
    for v in body.data.vertices:              # flattened section (rescue tube profile)
        v.co.y *= 0.62
    P.append(body)
    for t in (0.33, 0.5, 0.67):               # moulded grooves (darker rings)
        ring = [V((x0 + L * t, math.cos(a) * r * 0.64, math.sin(a) * r * 1.01)) for a in
                (2 * math.pi * i / 12 for i in range(13))]
        P.append(tube("Groove", ring, [0.006] * 13, 4, strap, cap_end=False))
    # clip + hook at the ends, short lanyard to a hand loop at the origin
    P.append(tube("Clip", [V((x0 + L + 0.01, 0, 0)), V((x0 + L + 0.06, 0, 0.0)), V((x0 + L + 0.06, 0, -0.03))],
                  [0.007] * 3, 5, metal))
    P.append(tube("Ring", [V((x0 - 0.01, 0, 0)), V((x0 - 0.05, 0, 0))], [0.008, 0.008], 6, metal))
    line = [V((x0 - 0.05, 0, 0)), V((0.30, 0.0, -0.04)), V((0.16, 0, -0.03)), V((0.05, 0, 0))]
    P.append(tube("Line", line, [0.009] * 4, 4, strap))
    loop = [V((0.05 + 0.05 * math.cos(a) - 0.05, 0.0, 0.045 * math.sin(a))) for a in
            (2 * math.pi * i / 10 for i in range(11))]
    P.append(tube("Loop", loop, [0.010] * 11, 4, strap, cap_end=False))
    return finish("RescueTube", P, 50)


PROPS = {"lifeguard_tower": make_lifeguard_tower, "parasol": make_parasol, "towel": make_towel,
         "dj_booth": make_dj_booth, "speaker_stack": make_speaker_stack, "weights": make_weights,
         "dumbbell": make_dumbbell, "rescue_tube": make_rescue_tube}
TEXTURED = {"dj_booth"}
HANDHELD = {"dumbbell", "rescue_tube"}

if __name__ == "__main__":
    for n in [a for a in sys.argv[1:] if a in PROPS] or list(PROPS):
        nb.reset_scene()
        PROPS[n]()
        t = nb.scene_tris()
        if n not in HANDHELD:                  # ground props: nothing below the ground plane
            for o in bpy.context.scene.objects:
                if o.type == "MESH":
                    for v in o.data.vertices:
                        if v.co.z < 0:
                            v.co.z = 0.0
        nb.export_glb("prop_" + n, texcoords=n in TEXTURED)
        print("[props] prop_%s: %d tris" % (n, t))
