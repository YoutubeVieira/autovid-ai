"""Neon Bay - procedural cars.

    python3 tools/blender/gen_cars.py            # all cars
    python3 tools/blender/gen_cars.py sedan suv  # some cars

Outputs models/car_<type>.glb (+ .glb.js base64 fallback).
Contract: forward +X, up +Y (glTF), origin at ground centre, ~4.4 m long.
Materials: Paint, Glass, Tyre, Rim, LightFront, LightRear, Trim.
Wheels: separate objects Wheel_FL / Wheel_FR / Wheel_RL / Wheel_RR, origin at hub.

Body = loft of 12-point cross sections along X (profiles below), subdivided once
(applied), auto-smoothed. Glass / pillars / underbody are material bands of the
loft, so the greenhouse follows the body exactly.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402,F401
import bmesh  # noqa: E402
from mathutils import Vector, Matrix  # noqa: E402

import nb_common as nb  # noqa: E402

# x keys run from rear (-L/2) to front (+L/2), heights in metres.
CARS = {
    "sedan": dict(
        L=4.4, R=0.33, tyre_w=0.22, xf=1.36, xr=-1.34, paint=(0.06, 0.18, 0.55),
        belt=[(-2.2, 0.80), (-2.05, 0.93), (-1.2, 0.96), (0.95, 0.93), (1.95, 0.82), (2.2, 0.68)],
        roof=[(-2.2, 0.84), (-2.05, 0.975), (-1.22, 1.0), (-0.62, 1.42), (0.28, 1.45), (0.97, 0.985),
              (1.95, 0.865), (2.2, 0.72)],
        clear=[(-2.2, 0.42), (-1.95, 0.30), (1.95, 0.30), (2.2, 0.40)],
        width=[(-2.2, 0.80), (-1.9, 0.89), (1.85, 0.90), (2.2, 0.79)],
        gw=0.74, rw=-1.22, rr=-0.62, rf=0.28, ws=0.97, bpil=(-0.24, -0.12), side_glass=(-0.95, 0.97),
    ),
    "sports": dict(
        L=4.4, R=0.33, tyre_w=0.26, xf=1.38, xr=-1.32, paint=(0.75, 0.05, 0.04),
        belt=[(-2.2, 0.66), (-2.0, 0.84), (-1.32, 0.88), (-0.6, 0.81), (0.6, 0.79), (1.38, 0.84),
              (1.95, 0.70), (2.2, 0.55)],
        roof=[(-2.2, 0.70), (-2.0, 0.885), (-1.6, 0.93), (-0.72, 1.17), (-0.05, 1.2), (0.6, 0.835),
              (1.38, 0.88), (1.95, 0.74), (2.2, 0.58)],
        clear=[(-2.2, 0.30), (-1.9, 0.16), (1.9, 0.16), (2.2, 0.26)],
        width=[(-2.2, 0.84), (-1.9, 0.94), (-1.32, 0.97), (0.0, 0.93), (1.38, 0.96), (2.2, 0.82)],
        gw=0.62, rw=-1.6, rr=-0.72, rf=-0.05, ws=0.6, bpil=None, side_glass=(-1.0, 0.6),
    ),
    "suv": dict(
        L=4.6, R=0.38, tyre_w=0.25, xf=1.45, xr=-1.42, paint=(0.15, 0.17, 0.16),
        belt=[(-2.3, 1.0), (-2.2, 1.1), (1.2, 1.1), (2.05, 1.01), (2.3, 0.88)],
        roof=[(-2.3, 1.04), (-2.22, 1.17), (-1.98, 1.76), (0.62, 1.78), (1.17, 1.19), (2.05, 1.06),
              (2.3, 0.92)],
        clear=[(-2.3, 0.52), (-2.1, 0.40), (2.1, 0.40), (2.3, 0.50)],
        width=[(-2.3, 0.88), (-2.15, 0.95), (2.05, 0.95), (2.3, 0.88)],
        gw=0.83, rw=-2.22, rr=-1.98, rf=0.62, ws=1.17, bpil=(-0.42, -0.30), side_glass=(-2.0, 1.17),
    ),
    "van": dict(
        L=4.8, R=0.34, tyre_w=0.23, xf=1.6, xr=-1.5, paint=(0.92, 0.92, 0.9),
        belt=[(-2.4, 0.96), (-2.32, 1.06), (1.45, 1.06), (2.15, 0.99), (2.4, 0.86)],
        roof=[(-2.4, 1.85), (-2.32, 1.97), (-2.1, 2.02), (1.0, 2.02), (1.62, 1.24), (2.15, 1.1),
              (2.4, 0.9)],
        clear=[(-2.4, 0.42), (-2.2, 0.33), (2.2, 0.33), (2.4, 0.42)],
        width=[(-2.4, 0.92), (-2.25, 0.98), (2.2, 0.98), (2.4, 0.9)],
        gw=0.86, rw=None, rr=None, rf=1.0, ws=1.62, bpil=None, side_glass=(0.25, 1.62),
    ),
}


def pl(keys, x):
    """Piecewise-linear interpolation through (x, y) keys."""
    if x <= keys[0][0]:
        return keys[0][1]
    for (x0, y0), (x1, y1) in zip(keys, keys[1:]):
        if x <= x1:
            t = (x - x0) / (x1 - x0)
            t = t * t * (3 - 2 * t) * 0.5 + t * 0.5  # slight ease
            return y0 + (y1 - y0) * t
    return keys[-1][1]


def bottom(c, x):
    b = pl(c["clear"], x)
    ra = c["R"] + 0.045
    for wx in (c["xf"], c["xr"]):
        dx = x - wx
        if abs(dx) < ra:
            b = max(b, c["R"] + math.sqrt(ra * ra - dx * dx) * 0.98)
    return b


def section_points(c, x):
    """12-point closed cross-section (lateral y, height z)."""
    b = bottom(c, x)
    belt = pl(c["belt"], x)
    roof = max(pl(c["roof"], x), belt + 0.04)
    w = pl(c["width"], x)
    shoulder = belt + 0.035
    roof_e = shoulder + 0.86 * (roof - shoulder)
    side = [
        (0.84 * w, b),
        (w, b + 0.3 * (belt - b)),
        (0.975 * w, belt),
        (0.88 * w, shoulder),
        (w * c["gw"], roof_e),
    ]
    pts = [(0.0, b)] + side + [(0.0, roof + 0.012)] + [(-y, z) for y, z in reversed(side)]
    return pts


def build_body(c, mats):
    L = c["L"]
    x0, x1 = -L / 2, L / 2
    xs = {x0, x0 + 0.13, x1, x1 - 0.13}
    ra = c["R"] + 0.045
    for wx in (c["xf"], c["xr"]):
        for f in (-1.0, -0.62, 0.0, 0.62, 1.0):
            xs.add(wx + f * ra)
    for k in ("rw", "rr", "rf", "ws"):
        if c[k] is not None:
            xs.add(c[k])
    if c["bpil"]:
        xs.update(c["bpil"])
    xs.update(c["side_glass"])
    for k in [kx for kx, _ in c["roof"]]:
        xs.add(k)
    xs = sorted(xs)
    # merge sections closer than 6 cm
    merged = [xs[0]]
    for x in xs[1:]:
        if x - merged[-1] > 0.06:
            merged.append(x)
        elif x == xs[-1]:
            merged[-1] = x
    xs = merged

    verts, faces, fmat = [], [], []
    N = 12
    for i, x in enumerate(xs):
        pts = section_points(c, x)
        if i in (0, len(xs) - 1):  # rounded bumper ends
            zc = sum(z for _, z in pts) / len(pts)
            pts = [(y * 0.9, zc + (z - zc) * 0.93) for y, z in pts]
        for y, z in pts:
            verts.append((x, y, z))

    def inside(x, lo, hi):
        return lo is not None and hi is not None and lo - 1e-4 <= x <= hi + 1e-4

    PAINT, GLASS, TRIM = 0, 1, 2
    for i in range(len(xs) - 1):
        xm = 0.5 * (xs[i] + xs[i + 1])
        for k in range(N):
            a, b_ = i * N + k, i * N + (k + 1) % N
            cc, d = (i + 1) * N + (k + 1) % N, (i + 1) * N + k
            faces.append((a, d, cc, b_))
            band = k
            m = PAINT
            if band in (0, N - 1):
                m = TRIM  # underbody
            elif band in (4, 7):  # side window band
                if inside(xm, *c["side_glass"]):
                    m = GLASS
                    if c["bpil"] and inside(xm, *c["bpil"]):
                        m = TRIM
            elif band in (5, 6):  # roof / screens
                if inside(xm, c["rf"], c["ws"]) or inside(xm, c["rw"], c["rr"]):
                    m = GLASS
            fmat.append(m)
    # end caps
    faces.append(tuple(range(N)))
    fmat.append(PAINT)
    last = (len(xs) - 1) * N
    faces.append(tuple(last + k for k in reversed(range(N))))
    fmat.append(PAINT)

    body = nb.mesh_object("Body", verts, faces, mats, fmat)
    # make normals consistent (outside) + edge creases for crisp character lines
    bm = bmesh.new()
    bm.from_mesh(body.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    crease = bm.edges.layers.float.get("crease_edge") or bm.edges.layers.float.new("crease_edge")
    S = len(xs)
    for e in bm.edges:
        i0, i1 = sorted(v.index for v in e.verts)
        k0, k1 = i0 % N, i1 % N
        val = 0.0
        if len(e.link_faces) == 2 and e.link_faces[0].material_index != e.link_faces[1].material_index:
            val = 0.75  # window / underbody outlines
        elif k0 == k1 and k0 in (3, N - 3):
            val = 0.55  # belt line
        elif k0 == k1 and k0 in (1, N - 1):
            val = 0.35  # rocker
        if i0 // N == i1 // N and i0 // N in (0, S - 1):
            val = max(val, 0.45)  # bumper faces
        e[crease] = val
    bm.to_mesh(body.data)
    bm.free()
    nb.add_subsurf(body, 1)
    nb.apply_modifiers(body)
    nb.auto_smooth(body, 50)
    return body


def wheel(name, c, loc, side, mats):
    """Tyre (lathe) + rim (lathe + 5 spokes), origin at the hub. side=+1 left (+Y)."""
    R, tw = c["R"], c["tyre_w"]
    rr = R * 0.66
    h = tw / 2
    tyre = [(rr, -h * 0.82), (R - 0.045, -h), (R - 0.008, -h * 0.86), (R, -h * 0.55),
            (R, h * 0.55), (R - 0.008, h * 0.86), (R - 0.045, h), (rr, h * 0.82)]
    rim = [(rr + 0.006, h * 0.86), (rr - 0.018, h * 0.76), (rr - 0.02, h * 0.1),
           (0.075, h * 0.1), (0.06, h * 0.7), (0.0, h * 0.78)]
    verts, faces, fm = [], [], []

    def add(vs, fs, m):
        o = len(verts)
        verts.extend(vs)
        for f in fs:
            faces.append(tuple(o + i for i in f))
            fm.append(m)

    v, f = nb.lathe(tyre, 14, axis="Y")
    add(v, f, 0)
    v, f = nb.lathe(rim, 12, axis="Y")
    add(v, f, 1)
    # spokes
    for s in range(5):
        a = 2 * math.pi * s / 5 + 0.3
        rot = Matrix.Rotation(a, 3, "Y")
        r0, r1, sw, st = 0.05, rr - 0.015, 0.032, 0.03
        yc = h * 0.52
        corners = []
        for rx in (r0, r1):
            for dy in (-st / 2, st / 2):
                for dz in (-sw / 2, sw / 2):
                    width = dz * (1.0 if rx == r0 else 0.7)
                    corners.append(rot @ Vector((rx, yc + dy, width)))
        bx = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (1, 5, 7, 3), (0, 2, 6, 4)]
        add([tuple(p) for p in corners], bx, 1)
    if side < 0:  # mirror for the right side, keep winding outward
        verts = [(x, -y, z) for x, y, z in verts]
        faces = [tuple(reversed(f)) for f in faces]
    obj = nb.mesh_object(name, verts, faces, mats, fm)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    nb.auto_smooth(obj, 45)
    obj.location = loc
    return obj


def surface_x(body, y, z, front=True):
    """Ray-cast along X to find the body skin at (y, z)."""
    origin = Vector((10 if front else -10, y, z))
    d = Vector((-1 if front else 1, 0, 0))
    ok, loc, nrm, _ = body.ray_cast(origin, d)
    return loc.x if ok else None


def surface_y(body, x, z):
    ok, loc, _, _ = body.ray_cast(Vector((x, 10, z)), Vector((0, -1, 0)))
    return loc.y if ok else None


def detail_box(name, size, loc, mat, bevel=0.012):
    o = nb.box(name, size, loc, mat, bevel=bevel, segments=1)
    nb.auto_smooth(o, 40)
    return o


def build_car(kind):
    c = CARS[kind]
    nb.reset_scene()
    M = {
        "Paint": nb.material("Paint", c["paint"], metallic=0.55, roughness=0.32),
        "Glass": nb.material("Glass", (0.02, 0.035, 0.05), metallic=0.4, roughness=0.06),
        "Trim": nb.material("Trim", (0.035, 0.035, 0.04), roughness=0.6),
        "Tyre": nb.material("Tyre", (0.025, 0.025, 0.025), roughness=0.92),
        "Rim": nb.material("Rim", (0.72, 0.73, 0.75), metallic=1.0, roughness=0.28),
        "LightFront": nb.material("LightFront", (1.0, 0.97, 0.88), emission=(1.0, 0.95, 0.82), strength=4.0),
        "LightRear": nb.material("LightRear", (0.6, 0.02, 0.02), emission=(1.0, 0.05, 0.03), strength=3.0),
    }
    body = build_body(c, [M["Paint"], M["Glass"], M["Trim"]])
    parts = [body]
    W = pl(c["width"], 0)
    xf_end, xr_end = c["L"] / 2, -c["L"] / 2

    # head / tail lights, grille, bumpers, mirrors, handles (ray-cast onto the skin)
    zf = pl(c["belt"], xf_end - 0.1) - 0.07
    zr = pl(c["belt"], xr_end + 0.1) - 0.07
    for s in (1, -1):
        y = s * (pl(c["width"], xf_end - 0.1) - 0.2)
        x = surface_x(body, y, zf, True)
        if x is not None:
            parts.append(detail_box("HeadLight", (0.12, 0.3, 0.085), (x - 0.03, y, zf), M["LightFront"], 0.02))
        y = s * (pl(c["width"], xr_end + 0.1) - 0.17)
        x = surface_x(body, y, zr, False)
        if x is not None:
            parts.append(detail_box("TailLight", (0.1, 0.34, 0.085), (x + 0.03, y, zr), M["LightRear"], 0.02))
        # mirror
        xm = c["ws"] - 0.12 if c["ws"] else 0.8
        zm = pl(c["belt"], xm) + 0.07
        ym = surface_y(body, xm, zm)
        if ym is not None:
            parts.append(detail_box("Mirror", (0.09, 0.2, 0.12), (xm - 0.05, s * (ym + 0.08), zm + 0.02), M["Paint"], 0.03))
        # door handles
        for hx in (c["side_glass"][1] - 0.45, c["side_glass"][1] - 1.35):
            if hx < c["side_glass"][0] - 0.3:
                continue
            hz = pl(c["belt"], hx) - 0.09
            hy = surface_y(body, hx, hz)
            if hy is not None:
                parts.append(detail_box("Handle", (0.14, 0.03, 0.025), (hx, s * (hy + 0.004), hz), M["Trim"], 0.0))
    # grille + lower bumper strips
    zg = zf - 0.13
    x = surface_x(body, 0, zg, True)
    if x is not None:
        parts.append(detail_box("Grille", (0.08, 0.95 * W, 0.12), (x - 0.02, 0, zg), M["Trim"], 0.015))
    zb = pl(c["clear"], xf_end) + 0.06
    x = surface_x(body, 0, zb, True)
    if x is not None:
        parts.append(detail_box("BumperF", (0.1, 1.55 * W, 0.08), (x - 0.02, 0, zb), M["Trim"], 0.02))
    zb = pl(c["clear"], xr_end) + 0.08
    x = surface_x(body, 0, zb, False)
    if x is not None:
        parts.append(detail_box("BumperR", (0.1, 1.55 * W, 0.09), (x + 0.02, 0, zb), M["Trim"], 0.02))
    # licence plate (trim) at the rear
    zp = zr - 0.12
    x = surface_x(body, 0, zp, False)
    if x is not None:
        parts.append(detail_box("Plate", (0.04, 0.42, 0.1), (x + 0.005, 0, zp), M["Trim"], 0.0))

    body = nb.join(parts, "Body")

    track = W - c["tyre_w"] / 2 - 0.04
    wheel_mats = [M["Tyre"], M["Rim"]]
    for nm, x, s in (("Wheel_FL", c["xf"], 1), ("Wheel_FR", c["xf"], -1),
                     ("Wheel_RL", c["xr"], 1), ("Wheel_RR", c["xr"], -1)):
        w = wheel(nm, c, (x, s * track, c["R"] * math.cos(math.pi / 14)), s, wheel_mats)  # tread touches y=0
        w.parent = body
    tris = nb.scene_tris()
    path = nb.export_glb("car_" + kind)
    return path, tris


if __name__ == "__main__":
    kinds = [a for a in sys.argv[1:] if a in CARS] or list(CARS)
    for k in kinds:
        p, t = build_car(k)
        print("[cars] %s: %d tris" % (k, t))
