"""Neon Bay - procedural cars, version 3 (detailed; original designs, no brand, no logo).

    python3 tools/blender/gen_cars.py                  # car_sedan car_sports car_suv car_van car_police
    python3 tools/blender/gen_cars.py sedan police     # some cars
    nice -n 5 python3 tools/blender/gen_cars.py        # when the machine is busy

Outputs models/car_<type>.glb (+ .glb.js base64 fallback).

Contract (unchanged since v2; js/engine.js makeCar3 / poseCar rely on it):
  * forward +X, up +Y (glTF), origin on the ground at the centre, ~4.4 m long (SUV 4.6, van 4.8)
  * materials Paint (recoloured by the game: every material whose name contains "paint"),
    Glass, Trim, Tyre, Rim, LightFront (emissive), LightRear (emissive): 7 materials (= draw
    calls) per car. car_police adds Livery (2nd colour of the two-tone livery, NOT recoloured),
    SirenRed, SirenBlue (emissive, on the separate Lightbar node).
  * wheels = separate nodes Wheel_FL, Wheel_FR, Wheel_RL, Wheel_RR, children of Body, origin
    at the hub, no rotation; the axle is the local Z axis (glTF), the game spins them with
    wheel.rotation.z -= v*dt/R. Their meshes are named mesh_Wheel_* so that the child meshes
    three.js creates do not match /^Wheel/ as well. Brake callipers belong to Body (they do
    not spin).
  * car_police: node Lightbar (child of Body, origin at the centre of its base on the roof);
    materials SirenRed (left half, +Z glTF... i.e. driver side) and SirenBlue (right half).

Budget: <= 9000 triangles and <= 700 KB per car (check_glb_three.js enforces it).

How the body is built: a loft of cross sections along X (14 points per half section:
underbody, sill, flared lower body, character line, shoulder, window seal, side glass,
roof rail, roof). Profiles (belt, roof, clear, width) are monotone cubic splines through the
keys of CARS; sections are dense around the wheel arches (cut in the profile, flared by
`flare`) and at every material boundary, rounded at both ends (`nose`). Material bands of the
loft give glass, pillars, window seals, underbody and the cladding. Details are separate
parts joined into Body: lamp patches conforming to the skin (ray-cast), panel gaps (thin
ribbons on the skin), grille with slats, intakes, plates, mirrors, handles, wipers, antenna,
exhausts, arch liners, callipers, and a visible cabin (tub, dashboard, steering wheel, seats)
behind the transparent Glass.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402,F401
import bmesh  # noqa: E402
from mathutils import Vector, Matrix  # noqa: E402

import nb_common as nb  # noqa: E402
import nb_vehicle as V  # noqa: E402

BUDGET = 9000

# x keys from rear (-L/2) to front (+L/2), heights in metres, width = half width.
CARS = {
    "sedan": dict(
        L=4.4, R=0.33, tyre_w=0.22, rim_r=0.235, wheel="alloy5", xf=1.36, xr=-1.34,
        paint=(0.06, 0.18, 0.55), flare=0.022,
        belt=[(-2.2, 0.80), (-2.06, 0.93), (-1.6, 0.965), (-1.25, 0.975), (0.95, 0.945), (1.6, 0.885),
              (1.98, 0.82), (2.2, 0.70)],
        roof=[(-2.2, 0.84), (-2.06, 0.97), (-1.6, 1.0), (-1.25, 1.02), (-0.9, 1.28), (-0.6, 1.41),
              (-0.1, 1.455), (0.25, 1.44), (0.6, 1.22), (0.97, 0.99), (1.6, 0.93), (1.98, 0.86), (2.2, 0.73)],
        clear=[(-2.2, 0.40), (-1.95, 0.29), (1.95, 0.29), (2.2, 0.38)],
        width=[(-2.2, 0.80), (-1.95, 0.875), (-1.3, 0.895), (0.0, 0.90), (1.4, 0.895), (1.9, 0.87), (2.2, 0.79)],
        gw=0.74, ws=0.97, rf=0.25, rr=-0.6, rw=-1.25, bpil=(-0.25, -0.13), side_glass=(-1.0, 0.97),
        doors=[0.93, -0.19, -1.02], hood=0.92, trunk=-1.3, nose=(0.2, 0.18),
        grille=dict(w=0.72, h=0.15, z=0.58, slats=4), intake=dict(w=1.2, h=0.12, z=0.40),
        exhaust="single", antenna="fin", spoiler=False, cabin=dict(rear_seat=True),
    ),
    "sports": dict(
        L=4.4, R=0.335, tyre_w=0.26, rim_r=0.25, wheel="sport", xf=1.38, xr=-1.32,
        paint=(0.75, 0.05, 0.04), flare=0.04,
        belt=[(-2.2, 0.62), (-2.02, 0.80), (-1.6, 0.85), (-1.1, 0.83), (-0.6, 0.79), (0.6, 0.765),
              (1.3, 0.79), (1.95, 0.665), (2.2, 0.52)],
        roof=[(-2.2, 0.66), (-2.02, 0.85), (-1.62, 0.895), (-1.2, 1.0), (-0.75, 1.14), (-0.3, 1.19),
              (-0.05, 1.185), (0.3, 1.0), (0.6, 0.80), (1.3, 0.83), (1.95, 0.70), (2.2, 0.555)],
        clear=[(-2.2, 0.27), (-1.9, 0.15), (1.9, 0.15), (2.2, 0.22)],
        width=[(-2.2, 0.82), (-1.9, 0.935), (-1.3, 0.965), (-0.6, 0.94), (0.2, 0.92), (1.35, 0.945), (1.9, 0.92),
               (2.2, 0.80)],
        gw=0.62, ws=0.6, rf=-0.05, rr=-0.75, rw=-1.62, bpil=None, side_glass=(-1.05, 0.6),
        doors=[0.88, -0.86], hood=0.56, trunk=-1.66, nose=(0.22, 0.2),
        grille=dict(w=0.56, h=0.09, z=0.42, slats=2), intake=dict(w=1.45, h=0.13, z=0.27),
        exhaust="twin", antenna="fin", spoiler=True, side_intake=True, cabin=dict(rear_seat=False),
    ),
    "suv": dict(
        L=4.6, R=0.38, tyre_w=0.25, rim_r=0.25, wheel="suv6", xf=1.45, xr=-1.42,
        paint=(0.15, 0.17, 0.16), flare=0.03, cladding=True,
        belt=[(-2.3, 1.0), (-2.2, 1.1), (-1.6, 1.11), (1.2, 1.10), (1.7, 1.065), (2.05, 1.01), (2.3, 0.88)],
        roof=[(-2.3, 1.04), (-2.22, 1.16), (-2.12, 1.66), (-1.98, 1.75), (-0.5, 1.785), (0.62, 1.775),
              (0.9, 1.48), (1.17, 1.18), (1.7, 1.11), (2.05, 1.05), (2.3, 0.92)],
        clear=[(-2.3, 0.52), (-2.1, 0.41), (2.1, 0.41), (2.3, 0.50)],
        width=[(-2.3, 0.88), (-2.15, 0.94), (0.0, 0.95), (2.05, 0.945), (2.3, 0.87)],
        gw=0.83, ws=1.17, rf=0.62, rr=-1.98, rw=-2.2, bpil=(-0.42, -0.31), side_glass=(-2.0, 1.17),
        cpil=(-1.42, -1.3),
        doors=[1.1, -0.37, -1.36], hood=1.12, trunk=None, tailgate=-2.24, nose=(0.15, 0.14),
        grille=dict(w=0.95, h=0.24, z=0.80, slats=5), intake=dict(w=1.1, h=0.12, z=0.55),
        exhaust="single", antenna="fin", spoiler=False, roof_rails=True, cabin=dict(rear_seat=True),
    ),
    "van": dict(
        L=4.8, R=0.34, tyre_w=0.23, rim_r=0.21, wheel="steel", xf=1.6, xr=-1.5,
        paint=(0.92, 0.92, 0.9), flare=0.012, cladding=True,
        belt=[(-2.4, 0.96), (-2.33, 1.06), (1.45, 1.06), (1.85, 1.04), (2.15, 0.99), (2.4, 0.86)],
        roof=[(-2.4, 1.86), (-2.34, 1.97), (-2.15, 2.02), (0.9, 2.02), (1.12, 1.98), (1.62, 1.25),
              (1.85, 1.15), (2.15, 1.09), (2.4, 0.90)],
        clear=[(-2.4, 0.42), (-2.2, 0.33), (2.2, 0.33), (2.4, 0.42)],
        width=[(-2.4, 0.93), (-2.25, 0.975), (1.6, 0.98), (2.2, 0.965), (2.4, 0.9)],
        gw=0.88, ws=1.62, rf=1.12, rr=None, rw=None, bpil=None, side_glass=(0.28, 1.62),
        doors=[1.58, 0.30, -0.95], hood=1.66, trunk=None, rear_doors=True, nose=(0.12, 0.12),
        grille=dict(w=1.0, h=0.2, z=0.74, slats=4), intake=dict(w=1.3, h=0.1, z=0.47),
        exhaust="single", antenna="whip", spoiler=False, cabin=dict(rear_seat=False, partition=True),
    ),
}
# police cruiser: sedan body, steel wheels, two-tone livery, light bar, push bar
CARS["police"] = dict(CARS["sedan"], paint=(0.93, 0.94, 0.97), wheel="steel", police=True, exhaust="single",
                      antenna="whip", flare=0.02)

N_HALF = 14     # points per half section (index 0 = bottom centre, 13 = roof centre)


# =========================================================================== profiles
def pchip(keys):
    """Monotone cubic interpolation (Fritsch-Carlson) through (x, y) keys."""
    xs = [k[0] for k in keys]
    ys = [k[1] for k in keys]
    n = len(xs)
    d = [(ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]) for i in range(n - 1)]
    m = [0.0] * n
    m[0], m[-1] = d[0], d[-1]
    for i in range(1, n - 1):
        if d[i - 1] * d[i] <= 0:
            m[i] = 0.0
        else:
            w1 = 2 * (xs[i + 1] - xs[i]) + (xs[i] - xs[i - 1])
            w2 = (xs[i + 1] - xs[i]) + 2 * (xs[i] - xs[i - 1])
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])

    def f(x):
        if x <= xs[0]:
            return ys[0]
        if x >= xs[-1]:
            return ys[-1]
        for i in range(n - 1):
            if x <= xs[i + 1]:
                h = xs[i + 1] - xs[i]
                t = (x - xs[i]) / h
                h00, h10 = 2 * t ** 3 - 3 * t ** 2 + 1, t ** 3 - 2 * t ** 2 + t
                h01, h11 = -2 * t ** 3 + 3 * t ** 2, t ** 3 - t ** 2
                return h00 * ys[i] + h10 * h * m[i] + h01 * ys[i + 1] + h11 * h * m[i + 1]
        return ys[-1]
    return f


class Car:
    def __init__(self, kind):
        self.kind = kind
        c = self.c = CARS[kind]
        self.belt = pchip(c["belt"])
        self.roof_ = pchip(c["roof"])
        self.clear = pchip(c["clear"])
        self.width = pchip(c["width"])
        self.L = c["L"]
        self.ra = c["R"] + 0.05            # wheel arch radius
        self.police = c.get("police", False)

    def roof(self, x):
        return max(self.roof_(x), self.belt(x) + 0.035)

    def bottom(self, x):
        b = self.clear(x)
        for wx in (self.c["xf"], self.c["xr"]):
            dx = x - wx
            if abs(dx) < self.ra:
                b = max(b, self.c["R"] + math.sqrt(self.ra ** 2 - dx * dx))
        return b

    def flare(self, x):
        f = 0.0
        for wx in (self.c["xf"], self.c["xr"]):
            t = abs(x - wx) / (self.ra + 0.28)
            if t < 1:
                f = max(f, self.c["flare"] * math.cos(t * math.pi / 2) ** 2)
        return f

    def half_section(self, x):
        """14 (y, z) points of the left half, bottom centre -> roof centre."""
        c = self.c
        b, c0 = self.bottom(x), self.clear(x)
        belt, roof, w = self.belt(x), self.roof(x), self.width(x)
        fl = self.flare(x)
        gw = c["gw"]
        H = belt - c0
        z_sill = max(b + 0.01, c0 + 0.085)
        z_low = max(b + 0.02, c0 + 0.42 * H)
        z_char = max(b + 0.03, c0 + 0.76 * H)
        g0 = belt + 0.03
        roof_e = g0 + 0.9 * (roof - g0)
        yg0, yg1 = 0.905 * w, gw * w
        pts = [
            (0.0, b),
            (0.76 * w, b),
            (0.93 * w + fl * 0.6, max(b, c0 + 0.02)),
            (0.968 * w + fl * 0.9, z_sill),
            (1.0 * w + fl, z_low),
            (1.0 * w + fl * 0.45, z_char),
            (0.987 * w, belt - 0.012),
            (0.958 * w, belt + 0.012),
            (yg0, g0),
            (yg0 + (yg1 - yg0) * 0.47 + 0.012, g0 + 0.5 * (roof_e - g0)),
            (yg1, roof_e),
            (yg1 * 0.94, roof_e + 0.55 * (roof - roof_e)),
            (yg1 * 0.6, roof - 0.01),
            (0.0, roof + 0.004),
        ]
        return pts

    def section_xs(self):
        c, L = self.c, self.L
        x0, x1 = -L / 2, L / 2
        xs = set()
        n = int(L / 0.2)
        for i in range(n + 1):
            xs.add(x0 + L * i / n)
        nf, nr = c["nose"]
        for t in (0.35, 0.65, 0.85, 0.96):
            xs.add(x1 - nf * (1 - t))
            xs.add(x0 + nr * (1 - t))
        for wx in (c["xf"], c["xr"]):
            for k in range(11):
                xs.add(wx + self.ra * math.cos(math.pi * k / 10))
            for f in (1.35, -1.35):
                xs.add(wx + f * self.ra)
        for k in ("ws", "rf", "rr", "rw"):
            if c.get(k) is not None:
                xs.add(c[k])
        for k in ("bpil", "side_glass", "cpil"):
            if c.get(k):
                xs.update(c[k])
        if self.police:
            xs.update((c["doors"][0], c["doors"][-1]))
        keep = sorted(x for x in xs if x0 - 1e-6 <= x <= x1 + 1e-6)
        must = set()
        for k in ("ws", "rf", "rr", "rw"):
            if c.get(k) is not None:
                must.add(round(c[k], 5))
        for k in ("bpil", "side_glass", "cpil"):
            if c.get(k):
                must.update(round(v, 5) for v in c[k])
        if self.police:
            must.update((round(c["doors"][0], 5), round(c["doors"][-1], 5)))
        out = [keep[0]]
        for x in keep[1:]:
            if x - out[-1] > 0.03:
                out.append(x)
            elif round(x, 5) in must:
                out[-1] = x
        out[-1] = x1
        return out

    def end_scale(self, x, pts):
        """Round both ends in plan and elevation."""
        nf, nr = self.c["nose"]
        x1, x0 = self.L / 2, -self.L / 2
        t = 0.0
        if x > x1 - nf:
            t = (x - (x1 - nf)) / nf
        elif x < x0 + nr:
            t = ((x0 + nr) - x) / nr
        if t <= 0:
            return pts
        k = 1 - math.sqrt(max(0.0, 1 - min(t, 1.0) ** 2))
        zc = 0.5 * (pts[0][1] + self.belt(x))
        sy, sz = 1 - 0.15 * k, 1 - 0.12 * k
        return [(y * sy, zc + (z - zc) * sz) for y, z in pts]


# =========================================================================== body loft
def band_material(car, k, xm):
    """Material of the loft band k (between half points k and k+1) at x = xm."""
    c = car.c

    def inside(r):
        return r is not None and r[0] - 1e-4 <= xm <= r[1] + 1e-4
    clad = c.get("cladding")
    if k in (0, 1):
        return "Trim"
    if k == 2:
        return "Trim" if clad else "Paint"
    if k == 3 and clad:
        return "Trim"
    if k == 7 and inside(c["side_glass"]):
        return "Trim"                                   # window seal
    if k in (8, 9) and inside(c["side_glass"]):
        if inside(c.get("bpil")) or inside(c.get("cpil")):
            return "Trim"
        return "Glass"
    if k in (11, 12):
        if c.get("rf") is not None and inside((c["rf"], c["ws"])):
            return "Glass"
        if c.get("rw") is not None and inside((c["rw"], c["rr"])):
            return "Glass"
    if car.police:
        d0, d1 = c["doors"][-1], c["doors"][0]
        if 2 <= k <= 9 and not (d0 - 1e-4 <= xm <= d1 + 1e-4):
            return "Livery"
        if k >= 10 and not (c["rw"] - 1e-4 <= xm <= c["ws"] + 1e-4):
            return "Livery"
    return "Paint"


def build_body(car):
    xs = car.section_xs()
    car.xs = xs
    H = N_HALF
    full = 2 * H - 2 + 2          # 0..13 left, then 12..1 right mirrored -> 26 points
    verts = []
    for x in xs:
        half = car.end_scale(x, car.half_section(x))
        ring = half + [(-y, z) for y, z in reversed(half[1:-1])]
        verts += [(x, y, z) for y, z in ring]
    N = len(half) + len(half) - 2
    names = ["Paint", "Glass", "Trim", "Livery"]
    mats = [V.MATS[n] for n in names if n in V.MATS]
    idx = {m.name: i for i, m in enumerate(mats)}
    faces, fm = [], []
    for i in range(len(xs) - 1):
        xm = 0.5 * (xs[i] + xs[i + 1])
        for k in range(N):
            a, b = i * N + k, i * N + (k + 1) % N
            cc, d = (i + 1) * N + (k + 1) % N, (i + 1) * N + k
            faces.append((a, b, cc, d))
            kk = k if k < H - 1 else (N - 1 - k)      # mirror band index
            fm.append(idx[band_material(car, kk, xm)])
    S = len(xs)
    faces.append(tuple(reversed(range(N))))
    fm.append(idx["Livery" if car.police else "Paint"])
    faces.append(tuple((S - 1) * N + k for k in range(N)))
    fm.append(idx["Livery" if car.police else "Paint"])
    body = nb.mesh_object("BodyShell", verts, faces, mats, fm)
    body["mat"] = "Paint"
    bm = bmesh.new()
    bm.from_mesh(body.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(body.data)
    bm.free()
    # smooth shading + crisp character lines
    me = body.data
    bm = bmesh.new()
    bm.from_mesh(me)
    sharp_k = {3, 5, 7, N - 3, N - 5, N - 7}
    lim = math.radians(42)
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        i0, i1 = (v.index for v in e.verts)
        if len(e.link_faces) != 2:
            e.smooth = False
            continue
        same = e.link_faces[0].material_index == e.link_faces[1].material_index
        sm = same and e.calc_face_angle(0.0) <= lim
        if i0 < S * N and i1 < S * N and i0 % N == i1 % N and i0 % N in sharp_k:
            sm = False
        if i0 // N == i1 // N and i0 // N in (0, S - 1):
            sm = False      # end caps
        e.smooth = sm
    bm.to_mesh(me)
    bm.free()
    me.update()
    return body


# =========================================================================== details
def headlamps(car, surf, parts):
    c = car.c
    x1 = car.L / 2
    xe = x1 - 0.02
    zb = car.belt(xe)
    w = car.width(xe - 0.1)
    z_hi, z_lo = zb - 0.035, zb - 0.13
    if car.kind == "van":
        z_hi, z_lo = zb - 0.03, zb - 0.17
    if car.kind == "suv":
        z_hi, z_lo = zb - 0.04, zb - 0.16
    y_in, y_out = 0.46 * w, 0.93 * w

    def g(a, b, sweep=0.03):
        y = y_in + (y_out - y_in) * a
        z = z_lo + (z_hi - z_lo) * b + sweep * a
        d = Vector((-1.0, -0.65 * a, 0.0)).normalized()
        return tuple(Vector((x1, y, z)) - d * 1.0), tuple(d)
    house = V.patch(surf, lambda a, b: g(-0.03 + a * 1.06, -0.12 + b * 1.24), 6, 2, 0.003, "Trim", name="LampHouse")
    lens = V.patch(surf, lambda a, b: g(a * 0.82, b), 5, 2, 0.008, "LightFront", uv_rect=(0.01, 0.0, 0.49, 1.0),
                   name="HeadLens", depth=0.006)
    blink = V.patch(surf, lambda a, b: g(0.84 + a * 0.16, b), 1, 2, 0.008, "LightFront", uv_rect=(0.55, 0.6, 0.95, 0.95),
                    name="Blinker", depth=0.006)
    for p in (house, lens, blink):
        if p:
            parts += [p, V.mirror_y(p)]
    # side repeater on the front fender (amber)
    xr = c["xf"] + car.ra + 0.12
    zr = car.belt(xr) - 0.07
    rep = V.patch(surf, lambda a, b: ((xr - 0.03 + 0.06 * a, 3, zr - 0.012 + 0.024 * b), (0, -1, 0)), 1, 1, 0.004,
                  "LightFront", uv_rect=(0.6, 0.6, 0.9, 0.9), name="Repeater", depth=0.004)
    if rep:
        parts += [rep, V.mirror_y(rep)]


def taillamps(car, surf, parts):
    c = car.c
    x0 = -car.L / 2
    xe = x0 + 0.02
    zb = car.belt(xe + 0.1)
    w = car.width(xe + 0.1)
    z_hi, z_lo = zb - 0.02, zb - 0.11
    y_in, y_out = 0.40 * w, 0.95 * w
    if car.kind in ("van", "suv"):
        z_hi, z_lo = zb + 0.32, zb - 0.12
        y_in, y_out = 0.80 * w, 0.97 * w

    def g(a, b):
        y = y_in + (y_out - y_in) * a
        z = z_lo + (z_hi - z_lo) * b
        d = Vector((1.0, -0.6 * a, 0.0)).normalized()
        return tuple(Vector((x0, y, z)) - d * 1.0), tuple(d)
    house = V.patch(surf, lambda a, b: g(-0.03 + a * 1.06, -0.1 + b * 1.2), 5, 2, 0.003, "Trim", name="TailHouse")
    vert = car.kind in ("van", "suv")
    if vert:      # vertical cluster: red top/bottom, amber + reverse in the middle
        red = V.patch(surf, lambda a, b: g(a, 0.55 + b * 0.45), 3, 2, 0.007, "LightRear", uv_rect=(0, 0, 1.5, 1.2),
                      name="TailRed", depth=0.005)
        amb = V.patch(surf, lambda a, b: g(a, 0.3 + b * 0.23), 2, 1, 0.007, "LightFront", uv_rect=(0.55, 0.6, 0.95, 0.95),
                      name="TailAmber", depth=0.005)
        rev = V.patch(surf, lambda a, b: g(a, b * 0.28), 2, 1, 0.007, "LightFront", uv_rect=(0.55, 0.05, 0.95, 0.45),
                      name="Reverse", depth=0.005)
    else:
        red = V.patch(surf, lambda a, b: g(0.38 + a * 0.62, b), 4, 2, 0.007, "LightRear", uv_rect=(0, 0, 2.5, 1.0),
                      name="TailRed", depth=0.005)
        amb = V.patch(surf, lambda a, b: g(0.19 + a * 0.18, b), 1, 2, 0.007, "LightFront", uv_rect=(0.55, 0.6, 0.95, 0.95),
                      name="TailAmber", depth=0.005)
        rev = V.patch(surf, lambda a, b: g(a * 0.18, b), 1, 2, 0.007, "LightFront", uv_rect=(0.55, 0.05, 0.95, 0.45),
                      name="Reverse", depth=0.005)
    for p in (house, red, amb, rev):
        if p:
            parts += [p, V.mirror_y(p)]


def grille_and_intakes(car, surf, parts):
    c = car.c
    x1 = car.L / 2
    g = c["grille"]
    # the nose cap is flat at x1: the grille sits proud of it
    gw, gh, gz = g["w"], g["h"], g["z"]
    xg = x1
    r = min(0.04, gh * 0.3)

    def rrect(w, h, r, n=3):
        pts = []
        for cx, cz, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180),
                           (w / 2 - r, -h / 2 + r, 270)):
            for k in range(n + 1):
                a = math.radians(a0 + 90 * k / n)
                pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))
        return pts
    outer = rrect(gw + 0.05, gh + 0.05, r + 0.02)
    inner = rrect(gw, gh, r)
    # frame = ring between outer and inner, extruded along X
    frame = ring_prism(outer, inner, xg - 0.005, xg + 0.035, gz, "Trim", name="GrilleFrame")
    parts.append(frame)
    parts.append(V.prism([(y, z + gz) for y, z in inner], xg + 0.001, xg + 0.004, "X", "Trim", name="GrilleBack"))
    n = g["slats"]
    for i in range(n):
        z = gz - gh / 2 + gh * (i + 0.5) / n
        parts.append(V.cbox((xg + 0.02, 0, z), (0.03, gw - 0.02, gh / n * 0.38), "Trim", bv=0.006,
                            rot=(0, math.radians(-12), 0), name="Slat"))
    for k in (-2, -1, 0, 1, 2):        # vertical bars
        parts.append(V.cbox((xg + 0.012, k * gw / 6, gz), (0.016, 0.012, gh - 0.01), "Trim", name="Bar"))
    # lower intake in the bumper (honeycomb normal map on the back plate) + fog lamps
    it = c["intake"]
    iw, ih, iz = it["w"], it["h"], it["z"]
    surf_x = []
    for y in (0.0, iw / 2 - 0.05):
        loc, _ = surf.front(y, iz, 1)
        if loc is not None:
            surf_x.append(loc.x)
    xi = min(surf_x) if surf_x else x1
    outer = rrect(iw + 0.04, ih + 0.04, 0.035)
    inner = rrect(iw, ih, 0.025)
    parts.append(ring_prism(outer, inner, xi - 0.01, xi + 0.03, iz, "Trim", name="IntakeFrame"))
    parts.append(V.prism([(y, z + iz) for y, z in inner], xi + 0.001, xi + 0.004, "X", "Trim", name="IntakeBack"))
    parts.append(V.cbox((xi + 0.02, 0, iz), (0.02, iw - 0.03, 0.018), "Trim", bv=0.005, name="IntakeBar"))
    for s in (1, -1):
        parts.append(V.cyl(0.035, 0.02, (xi + 0.012, s * (iw / 2 - 0.07), iz), "X", "LightFront", sides=10,
                           caps=(False, True), name="Fog"))
    # front lip / splitter
    zb = car.clear(x1) + 0.015
    loc, _ = surf.front(0, zb + 0.03, 1)
    xs_ = loc.x if loc is not None else x1 - 0.05
    lw = car.width(x1 - 0.1) * 1.65
    parts.append(V.prism([(xs_ + 0.03, zb - 0.01), (xs_ + 0.03, zb + 0.012), (xs_ - 0.35, zb + 0.02), (xs_ - 0.35, zb - 0.01)],
                         -lw / 2, lw / 2, "Y", "Trim", bv=0.004, name="Lip"))
    # front plate below the grille
    pz = (gz - gh / 2 + iz + ih / 2) / 2 if car.kind != "sports" else iz + ih / 2 + 0.07
    loc, _ = surf.front(0, pz, 1)
    xp = (loc.x if loc is not None else x1) + 0.006
    parts.append(plate((xp, 0, pz), 1))


def ring_prism(outer, inner, x0, x1, zc, mat, name="Ring"):
    """Flat ring (outer polygon minus inner polygon, same point count) extruded along X."""
    n = len(outer)
    verts = []
    for x in (x0, x1):
        verts += [(x, y, z + zc) for y, z in outer]
        verts += [(x, y, z + zc) for y, z in inner]
    faces = []
    o0, i0, o1, i1 = 0, n, 2 * n, 3 * n
    for k in range(n):
        k2 = (k + 1) % n
        faces.append((o1 + k, o1 + k2, i1 + k2, i1 + k))       # front face (x1)
        faces.append((o0 + k2, o0 + k, i0 + k, i0 + k2))       # back face
        faces.append((o0 + k, o0 + k2, o1 + k2, o1 + k))       # outer wall
        faces.append((i0 + k2, i0 + k, i1 + k, i1 + k2))       # inner wall
    o = V.part(name, verts, faces, mat)
    V.fix_normals(o)
    nb.auto_smooth(o, 35)
    return o


def plate(c, s):
    """Licence plate facing s*X (Rim material, plate region of the atlas: no readable text)."""
    w, h, t = 0.52, 0.115, 0.012
    x, y, z = c
    xf = x + s * t
    verts = [(x, -w / 2, z - h / 2), (x, w / 2, z - h / 2), (x, w / 2, z + h / 2), (x, -w / 2, z + h / 2),
             (xf, -w / 2, z - h / 2), (xf, w / 2, z - h / 2), (xf, w / 2, z + h / 2), (xf, -w / 2, z + h / 2)]
    v0, v1 = V.PLATE_V
    # front face: viewed from +s*X, u runs to the viewer's right
    if s > 0:
        front = (4, 5, 6, 7)
        fu = [(1, v0), (0, v0), (0, v1), (1, v1)]
    else:
        front = (7, 6, 5, 4)
        fu = [(0, v1), (1, v1), (1, v0), (0, v0)]
    faces = [front, (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    plain = [(0.25, 0.25)] * 4
    uvs = [fu, plain, plain, plain, plain]
    o = V.part("Plate", verts, faces, "Rim", uv=uvs)
    o.data.update()
    if o.data.polygons[0].normal.x * s < 0:
        o.data.flip_normals()
    nb.auto_smooth(o, 30)
    return o


def rear_details(car, surf, parts):
    c = car.c
    x0 = -car.L / 2
    w = car.width(x0 + 0.2)
    # rear plate
    zp = car.belt(x0 + 0.05) - 0.2 if car.kind not in ("van", "suv") else car.belt(x0 + 0.05) - 0.08
    loc, _ = surf.front(0, zp, -1)
    xp = (loc.x if loc is not None else x0) - 0.004
    parts.append(V.cbox((xp + 0.01, 0, zp), (0.02, 0.56, 0.15), "Trim", bv=0.006, name="PlateRecess"))
    parts.append(plate((xp - 0.002, 0, zp), -1))
    # diffuser / bumper lower
    zb = car.clear(x0) + 0.02
    loc, _ = surf.front(0, zb + 0.04, -1)
    xd = loc.x if loc is not None else x0 + 0.05
    dw = w * 1.5
    parts.append(V.prism([(xd - 0.025, zb - 0.01), (xd - 0.025, zb + 0.07), (xd + 0.3, zb + 0.02), (xd + 0.3, zb - 0.01)],
                         -dw / 2, dw / 2, "Y", "Trim", bv=0.004, name="Diffuser"))
    if car.kind == "sports":
        for k in (-2, -1, 0, 1, 2):
            parts.append(V.prism([(xd - 0.02, zb + 0.06), (xd + 0.22, zb + 0.02), (xd + 0.22, zb - 0.0), (xd - 0.02, zb - 0.0)],
                                 k * 0.16 - 0.006, k * 0.16 + 0.006, "Y", "Trim", name="Fin"))
    # exhausts
    ex = c["exhaust"]
    tips = [(-0.55 * w,)] if ex == "single" else [(0.55 * w,), (-0.55 * w,)]
    if ex == "twin":
        tips = [(0.62 * w,), (0.48 * w,), (-0.48 * w,), (-0.62 * w,)]
    for (y,) in tips:
        z = zb + 0.05
        r = 0.04 if ex == "single" else 0.034
        prof = [(r * 0.8, 0.0), (r * 0.8, 0.09), (r, 0.10), (r, 0.0)]
        o = V.lathe([(r * 0.82, 0.10), (r * 0.82, 0.0), (r, 0.0), (r, 0.12)], 12, (xd - 0.06, y, z),
                    "X", "Rim", name="Exhaust", fix=False, flip=True)
        parts.append(o)
        parts.append(V.cyl(r * 0.8, 0.01, (xd - 0.03, y, z), "X", "Trim", sides=12, caps=(True, False), name="ExhaustIn"))
        del prof
    # third brake light
    if c.get("rw") is not None and car.kind != "sports":
        xb = c["rw"] + 0.03
        zb3 = car.belt(xb) + 0.035
        loc, nrm = surf.top(xb, 0)
        parts.append(V.cbox((xb - 0.05, 0, zb3), (0.03, 0.4, 0.025), "LightRear", bv=0.004, name="Brake3"))
    elif car.kind in ("suv", "van"):
        xb = x0 + 0.08
        zb3 = car.roof(xb + 0.1) - 0.04
        loc, _ = surf.front(0, zb3, -1)
        if loc is not None:
            parts.append(V.cbox((loc.x - 0.008, 0, zb3), (0.02, 0.36, 0.03), "LightRear", bv=0.004, name="Brake3"))
    # spoiler
    if c.get("spoiler"):
        xs_ = x0 + 0.08
        zt = car.belt(xs_ + 0.1)
        sp = [(xs_ - 0.04, zt + 0.055), (xs_ + 0.22, zt + 0.025), (xs_ + 0.25, zt - 0.005), (xs_ + 0.0, zt - 0.005)]
        sw = car.width(xs_ + 0.1) * 0.85
        parts.append(V.prism(sp, -sw, sw, "Y", "Paint", bv=0.008, name="Spoiler"))


def mirrors(car, surf, parts):
    c = car.c
    xm = c["ws"] - 0.14
    zm = car.belt(xm) + 0.09
    loc, nrm = surf.side(xm, car.belt(xm) + 0.02, 1)
    if loc is None:
        return
    y0 = loc.y
    secs = []
    # housing: loft along Y of rounded sections (x, z)
    for t, sc in ((0.0, 0.55), (0.25, 0.92), (0.6, 1.0), (0.9, 0.85), (1.0, 0.55)):
        y = y0 + 0.07 + t * 0.17
        pts = []
        for k in range(8):
            a = 2 * math.pi * k / 8
            px = xm + (0.05 * math.cos(a) - (0.012 if math.cos(a) > 0 else 0.0)) * sc
            pz = zm + 0.055 * math.sin(a) * sc
            pts.append((px, pz))
        secs.append((y, pts))
    verts, faces = [], []
    for y, pts in secs:
        verts += [(px, y, pz) for px, pz in pts]
    S = len(secs)
    for i in range(S - 1):
        for k in range(8):
            k2 = (k + 1) % 8
            faces.append((i * 8 + k, i * 8 + k2, (i + 1) * 8 + k2, (i + 1) * 8 + k))
    faces.append(tuple(reversed(range(8))))
    faces.append(tuple((S - 1) * 8 + k for k in range(8)))
    hous = V.part("Mirror", verts, faces, "Livery" if car.police else "Paint")
    V.fix_normals(hous)
    nb.auto_smooth(hous, 50)
    glass = V.cbox((xm - 0.052, y0 + 0.165, zm), (0.006, 0.13, 0.075), "Rim", bv=0.006, name="MirrorGlass")
    arm = V.cbox((xm + 0.005, y0 + 0.04, zm - 0.04), (0.06, 0.11, 0.025), "Trim", bv=0.008, name="MirrorArm")
    for p in (hous, glass, arm):
        parts += [p, V.mirror_y(p)]


def handles_and_seams(car, surf, parts):
    c = car.c
    doors = c["doors"]
    zt = lambda x: car.belt(x) - 0.01  # noqa: E731
    gap = 0.0045
    # vertical door gaps
    for x in doors:
        rays = []
        z0 = car.bottom(x) + 0.03
        z1 = zt(x)
        if c.get("side_glass") and c["side_glass"][0] < x < c["side_glass"][1]:
            z1 = car.belt(x) + 0.008
        n = 7
        for k in range(n + 1):
            z = z0 + (z1 - z0) * k / n
            rays.append(((x - 0.02 * (z - z0), 3, z), (0, -1, 0)))
        s = V.seam(surf, rays, gap, 0.0012, "Trim", name="DoorGap")
        if s:
            parts += [s, V.mirror_y(s)]
    # door bottom line (along the sill) between the outer door gaps
    xa, xb = doors[-1], doors[0]
    rays = []
    for k in range(12):
        x = xb + (xa - xb) * k / 11
        rays.append(((x, 3, car.clear(x) + 0.1), (0, -1, 0)))
    s = V.seam(surf, rays, gap, 0.0012, "Trim", name="SillGap")
    if s:
        parts += [s, V.mirror_y(s)]
    # handles
    hx = []
    for i in range(len(doors) - 1):
        hx.append(doors[i] - 0.2 if not (car.kind == "van" and i == 1) else doors[i] - 0.25)
    if car.kind == "sports":
        hx = [doors[1] + 0.28]
    for x in hx:
        z = car.belt(x) - 0.075
        loc, nrm = surf.side(x, z, 1)
        if loc is None:
            continue
        h = V.cbox((x, loc.y + 0.008, z), (0.16, 0.022, 0.032), "Trim", bv=0.01, name="Handle")
        rec = V.patch(surf, lambda a, b: ((x - 0.09 + 0.18 * a, 3, z - 0.025 + 0.05 * b), (0, -1, 0)), 2, 1, 0.0015,
                      "Trim", name="HandleCup")
        for p in (h, rec):
            if p:
                parts += [p, V.mirror_y(p)]
    # hood seams: across the cowl + along each fender
    x1 = car.L / 2
    hx0 = c.get("hood")
    if hx0:
        wy = car.width(hx0) * 0.72
        rays = [((hx0 + 0.02 * abs(t), wy * t, 5), (0, 0, -1)) for t in [k / 6 - 1 for k in range(13)]]
        s = V.seam(surf, rays, gap, 0.0012, "Trim", name="HoodGap")
        if s:
            parts.append(s)
        rays = []
        for k in range(10):
            x = hx0 + (x1 - 0.12 - hx0) * k / 9
            rays.append(((x, car.width(x) * 0.72, 5), (0, 0, -1)))
        s = V.seam(surf, rays, gap, 0.0012, "Trim", name="HoodSide")
        if s:
            parts += [s, V.mirror_y(s)]
    tx = c.get("trunk")
    x0 = -car.L / 2
    if tx:
        wy = car.width(tx) * 0.74
        rays = [((tx, wy * t, 5), (0, 0, -1)) for t in [k / 6 - 1 for k in range(13)]]
        s = V.seam(surf, rays, gap, 0.0012, "Trim", name="TrunkGap")
        if s:
            parts.append(s)
        rays = []
        for k in range(8):
            x = tx + (x0 + 0.12 - tx) * k / 7
            rays.append(((x, car.width(x) * 0.74, 5), (0, 0, -1)))
        s = V.seam(surf, rays, gap, 0.0012, "Trim", name="TrunkSide")
        if s:
            parts += [s, V.mirror_y(s)]
    # bumper split lines (front + rear corners, from the arch up to the lamp)
    for wx, xend in ((c["xf"], x1), (c["xr"], x0)):
        sgn = 1 if xend > 0 else -1
        xb_ = wx + sgn * (car.ra + 0.02)
        rays = []
        z0 = car.bottom(xb_) + 0.01
        z1 = car.belt(xb_) - 0.13
        for k in range(5):
            z = z0 + (z1 - z0) * k / 4
            rays.append(((xb_ + sgn * 0.06 * k / 4, 3, z), (0, -1, 0)))
        s = V.seam(surf, rays, gap, 0.0012, "Trim", name="BumperGap")
        if s:
            parts += [s, V.mirror_y(s)]
    # van: sliding-door track + rear door split
    if c.get("rear_doors"):
        zr0, zr1 = car.clear(x0) + 0.12, car.roof(x0 + 0.06) - 0.05
        rays = [((x0 - 3, 0.0, zr0 + (zr1 - zr0) * k / 6), (1, 0, 0)) for k in range(7)]
        s = V.seam(surf, rays, gap * 1.4, 0.0015, "Trim", name="RearSplit")
        if s:
            parts.append(s)
        xt0, xt1 = doors[-1] - 0.1, doors[1] + 0.05
        rays = [((xt0 + (xt1 - xt0) * k / 6, 3, car.belt(0) + 0.04), (0, -1, 0)) for k in range(7)]
        s = V.seam(surf, rays, 0.018, 0.003, "Trim", name="SlideTrack")
        if s:
            parts += [s, V.mirror_y(s)]
    if c.get("tailgate"):
        z0, z1 = car.clear(x0) + 0.2, car.roof(x0 + 0.06) - 0.03
        for sgn in (1, -1):
            pass
        rays = [((x0 - 3, car.width(x0) * 0.82 * (k / 5 * 2 - 1), car.belt(x0) - 0.18), (1, 0, 0)) for k in range(6)]
        s = V.seam(surf, rays, gap, 0.0015, "Trim", name="TailgateGap")
        if s:
            parts.append(s)


def wipers_antenna_rails(car, surf, parts):
    c = car.c
    xw = c["ws"] - 0.02
    zw = car.belt(xw) + 0.035
    for y0, ang in ((0.05, 0.25), (-0.55, 0.18)):
        yl = 0.55
        cx, cy = xw - 0.02, y0 + yl / 2 * math.cos(ang)
        parts.append(V.cbox((cx, cy, zw + 0.012), (0.018, yl, 0.012), "Trim", rot=(0, 0, ang), name="Wiper"))
        parts.append(V.cbox((cx + 0.012, y0, zw), (0.04, 0.04, 0.02), "Trim", bv=0.006, name="WiperPivot"))
    # antenna
    if c.get("antenna") == "fin" and c.get("rr") is not None:
        xa = c["rr"] + 0.12
        za = car.roof(xa)
        fin = [(xa - 0.1, za - 0.01), (xa + 0.08, za - 0.01), (xa - 0.06, za + 0.06), (xa - 0.1, za + 0.055)]
        parts.append(V.prism(fin, -0.025, 0.025, "Y", "Paint", bv=0.01, seg=1, name="Fin"))
    else:
        xa = (c.get("rf") or 0.0) - 0.15 if car.kind != "van" else 0.7
        za = car.roof(xa)
        parts.append(V.cyl(0.004, 0.42, (xa, 0.35, za + 0.2), "Z", "Trim", sides=5, r2=0.0025, name="Whip"))
        parts.append(V.cyl(0.018, 0.02, (xa, 0.35, za + 0.0), "Z", "Trim", sides=8, name="WhipBase"))
    if c.get("roof_rails"):
        x0r, x1r = c["rr"] + 0.08, c["rf"] - 0.05
        for s in (1, -1):
            y = s * car.width(0) * c["gw"] * 0.86
            pts = []
            for k in range(7):
                x = x0r + (x1r - x0r) * k / 6
                pts.append((x, y, car.roof(x) + 0.055))
            parts.append(V.tube(pts, 0.016, "Trim", sides=6, name="Rail"))
            for x in (x0r + 0.05, x1r - 0.05):
                parts.append(V.cbox((x, y, car.roof(x) + 0.025), (0.08, 0.035, 0.05), "Trim", bv=0.008, name="RailFoot"))


def arch_liners(car, parts):
    """Black inner wall of each wheel arch (hides the hollow body and the other side)."""
    c = car.c
    for wx in (c["xf"], c["xr"]):
        ra = car.ra - 0.004
        y_in = car.width(wx) - c["tyre_w"] - 0.12
        n = 10
        verts, faces = [], []
        zc = c["R"]
        verts.append((wx, y_in, zc - 0.05))
        for k in range(n + 1):
            a = math.pi * k / n
            verts.append((wx + ra * math.cos(a), y_in, zc + ra * math.sin(a)))
        for k in range(n):
            faces.append((0, k + 2, k + 1))
        # outward (towards +Y) facing wall, seen from the left side through the arch
        o = V.part("Liner", verts, faces, "Trim")
        o.data.update()
        if o.data.polygons[0].normal.y < 0:
            o.data.flip_normals()
        nb.auto_smooth(o, 10)
        parts += [o, V.mirror_y(o)]


def calipers(car, parts):
    c = car.c
    mat = "Trim" if car.police else "Paint"
    track = car.width(0) - c["tyre_w"] / 2 - 0.04
    for wx in (c["xf"], c["xr"]):
        for s in (1, -1):
            y = s * (track + c["tyre_w"] / 2 * 0.05)
            parts.append(V.brake_caliper(wx, y, c["R"] * math.cos(math.pi / 18), c["rim_r"] - 0.04, s, mat))


def cabin(car, surf, parts):
    """Visible interior: tub (inward faces), dashboard, steering wheel, seats."""
    c = car.c
    ws = c["ws"]
    w = car.width(0)
    floor = car.clear(0) + 0.1
    xd = ws - 0.08
    xb = (c["rw"] + 0.1) if c.get("rw") is not None else ws - 1.9
    if car.kind == "van":
        xb = c["side_glass"][0] + 0.05
    if car.kind == "sports":
        xb = -0.95
    top = car.belt(0) - 0.03
    yi = w * 0.86
    # tub: inverted open box (floor, sides, front, back), faces pointing inwards
    vs = [(xb, -yi, floor), (xd, -yi, floor), (xd, yi, floor), (xb, yi, floor),
          (xb, -yi, top), (xd, -yi, top), (xd, yi, top), (xb, yi, top)]
    fs = [(0, 1, 2, 3), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    tub = V.part("Tub", vs, fs, "Trim")
    tub.data.update()
    if tub.data.polygons[0].normal.z < 0:
        tub.data.flip_normals()
    nb.auto_smooth(tub, 10)
    parts.append(tub)
    if c["cabin"].get("partition"):
        parts.append(V.cbox((xb + 0.02, 0, (floor + car.roof(xb)) / 2), (0.03, 2 * yi, car.roof(xb) - floor - 0.05), "Trim",
                            name="Partition"))
    # dashboard (side profile extruded across the car)
    zb = car.belt(xd)
    dash = [(xd + 0.04, zb - 0.02), (xd + 0.04, zb + 0.01), (xd - 0.16, zb + 0.06), (xd - 0.33, zb + 0.02),
            (xd - 0.36, zb - 0.12), (xd - 0.15, floor + 0.12)]
    parts.append(V.prism(dash, -yi, yi, "Y", "Trim", bv=0.02, name="Dash"))
    # centre console
    parts.append(V.prism([(xd - 0.3, zb - 0.1), (xd - 0.3, floor), (xd - 1.05, floor), (xd - 1.05, floor + 0.2),
                          (xd - 0.55, floor + 0.22)], -0.1, 0.1, "Y", "Trim", bv=0.015, name="Console"))
    # steering wheel on the left (+Y), facing the driver
    yd = 0.37 * w * 2 * 0.5 + 0.02
    sx, sz = xd - 0.45, zb + 0.0
    tilt = math.radians(62)
    ring = []
    rr = 0.18
    for k in range(14):
        a = 2 * math.pi * k / 14
        p = Vector((0, rr * math.cos(a), rr * math.sin(a)))
        p = Matrix.Rotation(-(math.pi / 2 - tilt), 3, "Y") @ p
        ring.append(tuple(Vector((sx, yd, sz)) + p))
    ring.append(ring[0])
    sw = V.tube(ring, 0.018, "Trim", sides=6, caps=False, name="SteeringWheel")
    parts.append(sw)
    nrm = Matrix.Rotation(-(math.pi / 2 - tilt), 3, "Y") @ Vector((1, 0, 0))
    hub = Vector((sx, yd, sz))
    for a in (0.0, math.pi, math.pi * 1.5):
        q = Matrix.Rotation(-(math.pi / 2 - tilt), 3, "Y") @ Vector((0, rr * math.cos(a), rr * math.sin(a)))
        parts.append(V.tube([tuple(hub), tuple(hub + q * 0.95)], 0.012, "Trim", sides=4, name="Spoke"))
    parts.append(V.tube([tuple(hub - nrm * 0.01), tuple(hub + nrm * 0.25)], 0.045, "Trim", sides=8, name="Column"))
    parts.append(V.cbox((xd - 0.3, yd, zb + 0.06), (0.12, 0.3, 0.06), "Trim", bv=0.015, name="Binnacle"))
    # seats
    def seat(xc, yc, width, rear=False):
        out = []
        zc = floor + 0.2
        out.append(V.cbox((xc, yc, zc), (0.5, width, 0.12), "Trim", bv=0.03, name="Cushion"))
        back_h = 0.55 if not rear else 0.5
        bx_ = xc - 0.27
        back_h = min(back_h, car.roof(bx_) - 0.32 - zc)
        bz = zc + 0.05 + back_h / 2
        out.append(V.cbox((bx_, yc, bz), (0.12, width, back_h), "Trim", bv=0.035, rot=(0, math.radians(-14), 0),
                          name="Back"))
        heads = [yc] if not rear else [yc - width * 0.3, yc + width * 0.3]
        hz = min(bz + back_h / 2 + 0.11, car.roof(bx_ - 0.07) - 0.16)
        for yh in heads:
            out.append(V.cbox((bx_ - 0.07, yh, hz), (0.09, 0.26, 0.16), "Trim", bv=0.03, name="Head"))
        return out
    xs1 = xd - 0.95
    if car.kind == "sports":
        xs1 = xd - 0.9
    for s in (1, -1):
        parts.extend(seat(xs1, s * 0.37 * w * 2 * 0.5 + s * 0.02, 0.48))
    if c["cabin"].get("rear_seat"):
        parts.extend(seat(xs1 - 0.78, 0.0, 2 * yi - 0.12, rear=True))


def police_kit(car, surf, parts):
    """Push bar, A-pillar spotlight, door emblem, rear cage; the light bar is a separate node."""
    c = car.c
    x1 = car.L / 2
    loc, _ = surf.front(0, 0.5, 1)
    xf = (loc.x if loc is not None else x1) + 0.09
    for s in (1, -1):
        y = s * 0.32
        pts = [(xf - 0.12, y, 0.33), (xf, y, 0.36), (xf + 0.02, y, 0.48), (xf + 0.02, y, 0.66), (xf - 0.12, y, 0.72)]
        parts.append(V.tube(pts, 0.022, "Trim", sides=8, name="PushBar"))
    parts.append(V.tube([(xf + 0.02, -0.34, 0.66), (xf + 0.02, 0.34, 0.66)], 0.02, "Trim", sides=8, name="PushBarTop"))
    parts.append(V.cbox((xf + 0.03, 0, 0.52), (0.03, 0.62, 0.12), "Trim", bv=0.01, name="PushPlate"))
    for s in (1, -1):
        parts.append(V.cyl(0.032, 0.02, (xf + 0.035, s * 0.24, 0.6), "X", "LightFront", sides=10, caps=(False, True),
                           name="PushLamp"))
    # spotlight at the left A pillar
    xs_ = c["ws"] - 0.12
    zs = car.belt(xs_) + 0.13
    loc, _ = surf.side(xs_, zs, 1)
    if loc is not None:
        parts.append(V.cyl(0.05, 0.11, (xs_ + 0.02, loc.y + 0.07, zs), "X", "Trim", sides=10, name="Spot"))
        parts.append(V.cyl(0.042, 0.01, (xs_ + 0.08, loc.y + 0.07, zs), "X", "LightFront", sides=10, name="SpotLens"))
        parts.append(V.cbox((xs_ + 0.0, loc.y + 0.03, zs), (0.03, 0.06, 0.03), "Trim", name="SpotArm"))
    # emblem on the front doors (generic 6-point star, no text)
    xe = (c["doors"][0] + c["doors"][1]) / 2
    ze = car.belt(xe) - 0.2
    loc, nrm = surf.side(xe, ze, 1)
    if loc is not None:
        verts, faces = [], []
        k = 0
        verts.append((xe, loc.y + 0.004, ze))
        for i in range(12):
            a = math.pi * i / 6
            r = 0.11 if i % 2 == 0 else 0.055
            verts.append((xe + r * math.cos(a), loc.y + 0.004, ze + r * math.sin(a)))
        for i in range(12):
            faces.append((0, 1 + i, 1 + (i + 1) % 12))
        star = V.part("Emblem", verts, faces, "Livery")
        star.data.update()
        if star.data.polygons[0].normal.y < 0:
            star.data.flip_normals()
        parts += [star, V.mirror_y(star)]
        del k
    # rear cage behind the front seats
    xb = c["bpil"][0] - 0.05
    zt = car.roof(xb) - 0.08
    z0 = car.belt(xb) - 0.25
    for k in range(-3, 4):
        parts.append(V.cbox((xb, k * 0.2, (zt + z0) / 2), (0.015, 0.015, zt - z0), "Trim", name="Cage"))
    parts.append(V.cbox((xb, 0, zt), (0.02, 1.3, 0.02), "Trim", name="CageTop"))


def lightbar(car):
    """Separate node 'Lightbar' (origin at the centre of its base, on the roof)."""
    x = (car.c["rf"] + car.c["rr"]) / 2 + 0.05
    zr = car.roof(x)
    parts = []
    L, D = 1.2, 0.26
    parts.append(V.cbox((0, 0, 0.035), (D, L, 0.05), "Trim", bv=0.015, name="LBBase"))
    for s in (1, -1):
        parts.append(V.cbox((0, s * 0.45, 0.0), (0.12, 0.05, 0.03), "Trim", name="LBFoot"))
    segs = [(0.42, "SirenRed"), (0.18, "SirenRed"), (0.0, "LightFront"), (-0.18, "SirenBlue"), (-0.42, "SirenBlue")]
    for y, m in segs:
        wseg = 0.22 if abs(y) > 0.3 else (0.17 if y != 0 else 0.12)
        parts.append(V.cbox((0, y, 0.095), (D - 0.03, wseg, 0.075), m, bv=0.02, seg=2, name="LBLens"))
        parts.append(V.cbox((0, y, 0.095), (0.012, wseg * 0.6, 0.06), "Rim", name="LBReflector"))
    for p in parts:
        V.uv_auto(p)
    lb = V.finish(parts, "Lightbar")
    lb.location = (x, 0, zr - 0.005)
    return lb


# =========================================================================== build
def build_car(kind):
    car = Car(kind)
    c = car.c
    nb.reset_scene()
    extras = []
    if car.police:
        extras = [("Livery", dict(color=(0.015, 0.03, 0.09), metallic=0.45, roughness=0.32)),
                  ("SirenRed", dict(color=(1.0, 0.05, 0.05), emission=(1.0, 0.04, 0.03), strength=6.0, roughness=0.3)),
                  ("SirenBlue", dict(color=(0.05, 0.2, 1.0), emission=(0.05, 0.25, 1.0), strength=6.0, roughness=0.3))]
    V.MATS.clear()
    V.MATS.update(V.vehicle_materials(c["paint"], extras=extras))
    shell = build_body(car)
    surf = V.Surface(shell)
    parts = [shell]
    headlamps(car, surf, parts)
    taillamps(car, surf, parts)
    grille_and_intakes(car, surf, parts)
    rear_details(car, surf, parts)
    mirrors(car, surf, parts)
    handles_and_seams(car, surf, parts)
    wipers_antenna_rails(car, surf, parts)
    arch_liners(car, parts)
    calipers(car, parts)
    cabin(car, surf, parts)
    if c.get("side_intake"):
        x = c["xr"] + car.ra + 0.16
        z = car.belt(x) - 0.16
        p = V.patch(surf, lambda a, b: ((x - 0.1 + 0.3 * a, 3, z - 0.07 + 0.11 * b + 0.04 * a), (0, -1, 0)), 3, 1, 0.002,
                    "Trim", name="SideIntake", depth=0.01)
        if p:
            parts += [p, V.mirror_y(p)]
    if car.police:
        police_kit(car, surf, parts)
    body = V.finish(parts, "Body")
    objs = [body]
    track = car.width(0) - c["tyre_w"] / 2 - 0.04
    zc = c["R"] * math.cos(math.pi / 18)          # tread vertex touches y = 0
    for nm, x, s in (("Wheel_FL", c["xf"], 1), ("Wheel_FR", c["xf"], -1),
                     ("Wheel_RL", c["xr"], 1), ("Wheel_RR", c["xr"], -1)):
        w = V.wheel(nm, c["R"], c["tyre_w"], c["rim_r"], (x, s * track, zc), s, style=c["wheel"])
        w.parent = body
        objs.append(w)
    if car.police:
        lb = lightbar(car)
        lb.parent = body
        objs.append(lb)
    tris = V.report("car_" + kind, objs, BUDGET)
    path = nb.export_glb("car_" + kind, texcoords=True)
    return path, tris


if __name__ == "__main__":
    kinds = [a for a in sys.argv[1:] if a in CARS] or list(CARS)
    for k in kinds:
        p, t = build_car(k)
        print("[cars] %s: %d tris -> %s (%.0f KB)" % (k, t, p, os.path.getsize(p) / 1024))
