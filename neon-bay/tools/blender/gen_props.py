"""Neon Bay - procedural street props.

    python3 tools/blender/gen_props.py               # all props
    python3 tools/blender/gen_props.py palm lamp     # some props

Outputs models/<name>.glb (+ .glb.js): palm, lamp, hydrant, bench, traffic_light.
Origin at ground centre, up +Y (glTF), metres. Props that "face" somewhere
(lamp arm, bench seat, traffic light lenses) face +Z in glTF (= Blender -Y).
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402,F401
import bmesh  # noqa: E402
from mathutils import Vector, Matrix  # noqa: E402

import nb_common as nb  # noqa: E402


def tube(name, pts, radii, sides, mat, cap_end=True, cap_start=False):
    """Sweep a circle along a polyline (parallel-transport frames)."""
    verts, faces = [], []
    pts = [Vector(p) for p in pts]
    up = Vector((0, 0, 1))
    prev_n = None
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        n = prev_n if prev_n is not None else (up.cross(t) if abs(t.dot(up)) < 0.99 else Vector((1, 0, 0)).cross(t))
        n = (n - t * n.dot(t)).normalized()
        prev_n = n
        b = t.cross(n)
        for s in range(sides):
            a = 2 * math.pi * s / sides
            verts.append(tuple(p + (n * math.cos(a) + b * math.sin(a)) * radii[i]))
    for i in range(len(pts) - 1):
        for s in range(sides):
            s2 = (s + 1) % sides
            faces.append((i * sides + s, i * sides + s2, (i + 1) * sides + s2, (i + 1) * sides + s))
    if cap_end:
        o = (len(pts) - 1) * sides
        faces.append(tuple(o + s for s in range(sides)))
    if cap_start:
        faces.append(tuple(reversed(range(sides))))
    obj = nb.mesh_object(name, verts, faces, [mat])
    fix_normals(obj)
    return obj


def fix_normals(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()


def lathe_obj(name, profile, segments, mat, cap_start=True, cap_end=True, loc=(0, 0, 0)):
    v, f = nb.lathe(profile, segments, axis="Z", cap_start=cap_start, cap_end=cap_end)
    v = [(x + loc[0], y + loc[1], z + loc[2]) for x, y, z in v]
    obj = nb.mesh_object(name, v, f, [mat])
    fix_normals(obj)
    return obj


def finish(name, parts, smooth=40):
    obj = nb.join(parts, name)
    nb.auto_smooth(obj, smooth)
    return obj


# --------------------------------------------------------------------------- palm
def make_palm():
    rnd = random.Random(7)
    bark = nb.material("Trunk", (0.36, 0.27, 0.18), roughness=0.95)
    leaf = nb.material("Leaves", (0.13, 0.32, 0.08), roughness=0.7)
    leaf.use_backface_culling = False
    nut = nb.material("Coconut", (0.25, 0.17, 0.07), roughness=0.8)
    H = 6.2
    # gently curved trunk with ring bulges
    pts, radii = [], []
    n = 22
    for i in range(n + 1):
        t = i / n
        x = 0.55 * t * t
        z = H * t
        pts.append((x, 0, z))
        r = 0.2 - 0.075 * t
        radii.append(r * (1.12 if i % 2 == 0 and 0 < i < n else 1.0) + (0.06 if i == 0 else 0.0))
    trunk = tube("Palm", pts, radii, 8, bark, cap_end=True)
    top = Vector(pts[-1])
    parts = [trunk]
    # crown bulb
    parts.append(nb.uv_sphere("Crown", 0.2, top + Vector((0, 0, 0.05)), 8, 5, bark, (1, 1, 0.8)))
    # fronds: arched rachis (V-fold strip) + leaflet triangles
    fronds = 11
    for k in range(fronds):
        yaw = 2 * math.pi * k / fronds + rnd.uniform(-0.15, 0.15)
        pitch = rnd.uniform(0.15, 0.55)
        length = rnd.uniform(2.3, 2.9)
        seg = 8
        verts, faces = [], []
        rot = Matrix.Rotation(yaw, 3, "Z")
        spine = []
        for i in range(seg + 1):
            t = i / seg
            d = length * t
            z = math.sin(pitch) * d - 1.1 * (d / length) ** 2 * length * 0.45
            spine.append(Vector((d * math.cos(pitch), 0, z)))
        for i, p in enumerate(spine):
            t = i / seg
            w = 0.05 * (1 - t) + 0.01
            verts += [tuple(rot @ (p + Vector((0, -w, -0.02))) + top),
                      tuple(rot @ (p + Vector((0, 0, 0.02))) + top),
                      tuple(rot @ (p + Vector((0, w, -0.02))) + top)]
        for i in range(seg):
            a = i * 3
            faces += [(a, a + 3, a + 4, a + 1), (a + 1, a + 4, a + 5, a + 2)]
        for i in range(1, seg):
            t = i / seg
            ll = 0.75 * math.sin(math.pi * (0.15 + 0.85 * t)) + 0.12
            p0, p1 = spine[i], spine[i + 1]
            for side in (-1, 1):
                tip = p0 + (p1 - p0) * 1.6 + Vector((0, side * ll, -0.35 * ll))
                base = len(verts)
                verts += [tuple(rot @ p0 + top), tuple(rot @ (p0 + (p1 - p0) * 0.7) + top), tuple(rot @ tip + top)]
                faces.append((base, base + 1, base + 2) if side > 0 else (base, base + 2, base + 1))
        parts.append(nb.mesh_object("Frond", verts, faces, [leaf]))
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.4
        parts.append(nb.uv_sphere("Nut", 0.09, top + Vector((0.16 * math.cos(a), 0.16 * math.sin(a), -0.12)),
                                  8, 5, nut))
    return finish("Palm", parts, 60)


# --------------------------------------------------------------------------- street lamp
def make_lamp():
    metal = nb.material("Metal", (0.16, 0.17, 0.18), metallic=0.8, roughness=0.45)
    bulb = nb.material("Bulb", (1.0, 0.92, 0.75), emission=(1.0, 0.85, 0.6), strength=6.0)
    H = 6.0
    parts = [lathe_obj("Pole", [(0.0, 0.0), (0.2, 0.0), (0.2, 0.1), (0.16, 0.16), (0.11, 0.3), (0.09, 0.9),
                                (0.075, H - 0.2), (0.06, H)], 12, metal, cap_start=False, cap_end=True)]
    # curved arm towards -Y (glTF +Z)
    arm = []
    for i in range(9):
        t = i / 8
        a = t * math.pi / 2
        arm.append((0, -0.55 * (1 - math.cos(a)) - 0.9 * t * t, H - 0.25 + 0.55 * math.sin(a) * 0.6))
    parts.append(tube("Arm", arm, [0.05 - 0.015 * (i / 8) for i in range(9)], 8, metal, cap_end=True))
    end = Vector(arm[-1])
    head = nb.box("Head", (0.32, 0.62, 0.12), end + Vector((0, -0.18, -0.02)), metal, bevel=0.04, segments=2)
    parts.append(head)
    parts.append(nb.box("Bulb", (0.24, 0.48, 0.03), end + Vector((0, -0.18, -0.09)), bulb, bevel=0.01))
    return finish("Lamp", parts, 40)


# --------------------------------------------------------------------------- fire hydrant
def make_hydrant():
    paint = nb.material("HydrantPaint", (0.75, 0.08, 0.05), metallic=0.2, roughness=0.45)
    metal = nb.material("Metal", (0.55, 0.55, 0.52), metallic=0.9, roughness=0.35)
    body = lathe_obj("Body", [(0.0, 0.0), (0.17, 0.0), (0.17, 0.05), (0.13, 0.07), (0.12, 0.1), (0.12, 0.55),
                              (0.15, 0.57), (0.15, 0.62), (0.12, 0.64), (0.11, 0.7), (0.08, 0.78),
                              (0.03, 0.81), (0.0, 0.82)], 14, paint, cap_start=False, cap_end=False)
    parts = [body]
    parts.append(cylinder_axis("NozzleL", 0.05, 0.12, (0.15, 0, 0.42), "X", paint))
    parts.append(cylinder_axis("NozzleR", 0.05, 0.12, (-0.15, 0, 0.42), "X", paint))
    parts.append(cylinder_axis("NozzleF", 0.07, 0.12, (0, -0.15, 0.40), "Y", paint))
    parts.append(cylinder_axis("CapF", 0.075, 0.03, (0, -0.22, 0.40), "Y", metal, sides=6))
    parts.append(cylinder_axis("CapL", 0.055, 0.03, (0.22, 0, 0.42), "X", metal, sides=6))
    parts.append(cylinder_axis("CapR", 0.055, 0.03, (-0.22, 0, 0.42), "X", metal, sides=6))
    parts.append(cylinder_axis("Nut", 0.035, 0.05, (0, 0, 0.84), "Z", metal, sides=5))
    for k in range(6):
        a = 2 * math.pi * k / 6
        parts.append(cylinder_axis("Bolt", 0.015, 0.03, (0.15 * math.cos(a), 0.15 * math.sin(a), 0.065), "Z",
                                   metal, sides=6))
    return finish("Hydrant", parts, 40)


def cylinder_axis(name, r, depth, loc, axis, mat, sides=10):
    return nb.cylinder(name, r, depth, loc, sides, mat, axis)


# --------------------------------------------------------------------------- bench
def make_bench():
    wood = nb.material("Wood", (0.42, 0.25, 0.12), roughness=0.75)
    metal = nb.material("Metal", (0.08, 0.09, 0.09), metallic=0.7, roughness=0.5)
    L = 1.8
    parts = []
    # cast frames at both ends (seat faces -Y = glTF +Z)
    for x in (-0.75, 0.75):
        leg = [(x, -0.22, 0.0), (x, -0.2, 0.42), (x, 0.05, 0.44), (x, 0.2, 0.46), (x, 0.26, 0.9)]
        parts.append(tube("Frame", leg, [0.03] * len(leg), 6, metal, cap_end=True, cap_start=True))
        parts.append(tube("Leg", [(x, 0.18, 0.0), (x, 0.16, 0.45)], [0.028] * 2, 6, metal, True, True))
        parts.append(tube("Arm", [(x, -0.25, 0.62), (x, -0.05, 0.64), (x, 0.18, 0.62)], [0.025] * 3, 6, metal,
                          True, True))
        parts.append(tube("ArmPost", [(x, -0.2, 0.42), (x, -0.22, 0.62)], [0.022] * 2, 6, metal, True, True))
    # seat slats
    for i, y in enumerate((-0.17, -0.07, 0.03, 0.13)):
        parts.append(nb.box("Slat", (L, 0.085, 0.035), (0, y, 0.46 + i * 0.006), wood, bevel=0.008))
    # back slats, tilted
    for i in range(3):
        z = 0.58 + i * 0.11
        y = 0.2 + (z - 0.5) * 0.15
        s = nb.box("Back", (L, 0.03, 0.085), (0, 0, 0), wood, bevel=0.008)
        s.rotation_euler = (math.radians(-12), 0, 0)
        s.location = (0, y, z)
        parts.append(s)
    return finish("Bench", parts, 40)


# --------------------------------------------------------------------------- traffic light
def make_traffic_light():
    metal = nb.material("Metal", (0.12, 0.13, 0.13), metallic=0.7, roughness=0.5)
    housing = nb.material("Housing", (0.05, 0.05, 0.05), roughness=0.6)
    red = nb.material("LightRed", (0.9, 0.05, 0.03), emission=(1.0, 0.05, 0.02), strength=5.0)
    amber = nb.material("LightYellow", (0.9, 0.55, 0.02), emission=(1.0, 0.6, 0.02), strength=5.0)
    green = nb.material("LightGreen", (0.05, 0.8, 0.3), emission=(0.05, 1.0, 0.35), strength=5.0)
    H = 3.2
    parts = [lathe_obj("Pole", [(0.0, 0.0), (0.14, 0.0), (0.14, 0.08), (0.08, 0.14), (0.065, 0.3), (0.06, H),
                                (0.07, H + 0.02), (0.0, H + 0.05)], 10, metal, cap_start=False, cap_end=False)]
    hz = H + 0.0
    parts.append(nb.box("Housing", (0.34, 0.26, 0.95), (0, -0.16, hz - 0.15), housing, bevel=0.03, segments=2))
    parts.append(nb.box("Backplate", (0.5, 0.02, 1.1), (0, -0.02, hz - 0.15), housing))
    for i, mat in enumerate((red, amber, green)):
        z = hz + 0.15 - i * 0.3
        lens = nb.cylinder("Lens", 0.1, 0.02, (0, -0.295, z), 12, mat, "Y")
        parts.append(lens)
        # visor (half tube)
        verts, faces = [], []
        segs = 7
        for s in range(segs + 1):
            a = math.pi * s / segs
            for d in (0.0, 0.16):
                verts.append((0.13 * math.cos(a), -0.3 - d, z + 0.13 * math.sin(a)))
        for s in range(segs):
            a = s * 2
            faces.append((a, a + 2, a + 3, a + 1))
        v = nb.mesh_object("Visor", verts, faces, [housing])
        parts.append(v)
    housing.use_backface_culling = False
    # pedestrian button box
    parts.append(nb.box("Button", (0.1, 0.08, 0.16), (0, -0.09, 1.1), housing, bevel=0.01))
    return finish("TrafficLight", parts, 40)


PROPS = {"palm": make_palm, "lamp": make_lamp, "hydrant": make_hydrant, "bench": make_bench,
         "traffic_light": make_traffic_light}

if __name__ == "__main__":
    names = [a for a in sys.argv[1:] if a in PROPS] or list(PROPS)
    for n in names:
        nb.reset_scene()
        PROPS[n]()
        t = nb.scene_tris()
        nb.export_glb(n)
        print("[props] %s: %d tris" % (n, t))
