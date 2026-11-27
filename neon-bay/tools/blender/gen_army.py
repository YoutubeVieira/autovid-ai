"""Neon Bay - procedural military vehicles (original, generic designs: no real vehicle copied,
no real insignia; stencil numbers are invented).

    python3 tools/blender/gen_army.py                 # army_jeep army_truck army_apc
    python3 tools/blender/gen_army.py jeep apc        # some vehicles
    nice -n 5 python3 tools/blender/gen_army.py       # when the machine is busy

Outputs models/army_<id>.glb (+ .glb.js). Same contract as the cars (gen_cars.py), so the
game can drive them like cars:
  * forward +X, up +Y (glTF), origin on the ground at the centre, 1 unit = 1 m
  * materials Paint (matte olive; the game recolours every material whose name contains
    "paint", so pass an olive colour or skip the recolouring), Glass, Trim (black / dark
    steel, also the stencil numbers), Tyre, Rim (olive-drab steel wheels), LightFront,
    LightRear; army_truck adds Canvas (tarp, bench cushions)
  * every road wheel is a separate node named Wheel_* (child of Body, origin at the hub,
    axle = local Z in glTF, spin with rotation.z -= v*dt/R), meshes named mesh_Wheel_*:
      army_jeep   Wheel_FL Wheel_FR Wheel_RL Wheel_RR                        R = 0.38 m
      army_truck  Wheel_FL Wheel_FR | Wheel_ML Wheel_MR (middle axle) | Wheel_RL Wheel_RR   R = 0.55 m
      army_apc    Wheel_FL Wheel_FR | Wheel_F2L Wheel_F2R (2nd axle) | Wheel_R2L Wheel_R2R
                  (3rd axle) | Wheel_RL Wheel_RR (4th, rearmost)            R = 0.55 m
    The spare wheels (jeep, truck) are part of Body and are NOT named Wheel_*.
  * army_apc: node Turret (child of Body, origin on the turret ring axis at the hull roof;
    turn with rotation.y in glTF) and node Gun (child of Turret, origin on the trunnion
    axis; elevate with rotation.z, + = barrel up), barrel along +X.
Budget: <= 12000 triangles and <= 900 KB per vehicle.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402,F401
from mathutils import Vector, Matrix  # noqa: E402

import nb_common as nb  # noqa: E402
import nb_vehicle as V  # noqa: E402

BUDGET = 12000
OLIVE = (0.115, 0.135, 0.06)


def mats(canvas=False):
    extras = [("Canvas", dict(color=(0.16, 0.16, 0.085), roughness=0.95))] if canvas else []
    V.MATS.clear()
    V.MATS.update(V.vehicle_materials(OLIVE, paint_metal=0.0, paint_rough=0.78, rim=(0.09, 0.1, 0.05),
                                      rim_metal=0.25, rim_rough=0.7, extras=extras))


def mir(parts, objs):
    """Append objs and their left/right mirror copies."""
    for o in objs:
        if o is not None:
            parts += [o, V.mirror_y(o)]


def arc(cx, cz, r, a0, a1, n):
    return [(cx + r * math.cos(a0 + (a1 - a0) * k / n), cz + r * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n + 1)]


def spare(c, R, w, rim_r, axis="X", style="army", segs=16):
    """Spare wheel joined into the body (named SpareTyre: not animated)."""
    o = V.wheel("SpareTyre", R, w, rim_r, (0, 0, 0), 1, style=style, segs=segs, disc=False, beadlock=8, hub_nuts=6)
    rot = Matrix.Rotation(math.pi / 2, 4, "Z") if axis == "X" else (
        Matrix.Rotation(math.pi / 2, 4, "X") if axis == "Z" else Matrix.Identity(4))
    o.data.transform(Matrix.Translation(Vector(c)) @ rot)
    o.location = (0, 0, 0)
    return o


def stencil_side(parts, text, x0, z0, y, h):
    """Same text on both sides, readable from each side (not mirrored)."""
    parts.append(V.stencil(text, (x0 + len(text) * h * 0.5 * 1.45, y, z0), (-1, 0, 0), (0, 0, 1), h, "Trim"))
    parts.append(V.stencil(text, (x0, -y, z0), (1, 0, 0), (0, 0, 1), h, "Trim"))


def headlamp(parts, c, r, guard=True):
    """Round headlamp facing +X with a dark bezel and a wire guard (left, mirrored)."""
    x, y, z = c
    objs = [V.cyl(r + 0.018, 0.06, (x - 0.02, y, z), "X", "Trim", sides=12, name="LampBody"),
            V.cyl(r, 0.012, (x + 0.012, y, z), "X", "LightFront", sides=12, caps=(False, True), name="Lamp")]
    if guard:
        for k in (-1, 0, 1):
            objs.append(V.cbox((x + 0.05, y + k * r * 0.55, z), (0.01, 0.01, 2 * r + 0.02), "Trim", name="Guard"))
        objs.append(V.tube([(x + 0.05, y + r * math.cos(t), z + r * math.sin(t)) for t in
                            [math.pi * k / 6 for k in range(7)]], 0.006, "Trim", sides=4, name="GuardArc"))
    mir(parts, objs)


def wz(R, segs):
    """Hub height so that the lowest tread vertex touches the ground."""
    return R if segs % 4 == 0 else R * math.cos(math.pi / segs)


def wheels(body, spec, R, w, rim_r, segs=16, beadlock=8):
    out = []
    for nm, x, y in spec:
        s = 1 if y > 0 else -1
        o = V.wheel(nm, R, w, rim_r, (x, y, wz(R, segs)), s, style="army",
                    segs=segs, disc=False, beadlock=beadlock, hub_nuts=6 if R > 0.45 else 5)
        o.parent = body
        out.append(o)
    return out


def axle(parts, x, y, z, r=0.055, diff=True):
    parts.append(V.cyl(r, 2 * y, (x, 0, z), "Y", "Trim", sides=8, name="Axle"))
    if diff:
        parts.append(V.lathe([(0.001, -0.17), (0.12, -0.12), (0.15, 0.0), (0.12, 0.12), (0.001, 0.17)], 10, (x, 0, z), "X",
                             "Trim", name="Diff"))


# =========================================================================== jeep
def make_jeep():
    mats()
    p = []
    R, TW, RIM = 0.38, 0.25, 0.2
    xf, xr, tr = 1.15, -1.05, 0.72
    zc = wz(R, 16)
    # chassis, axles, springs
    for s in (1, -1):
        p.append(V.box(-1.6, 1.88, s * 0.42 - 0.04, s * 0.42 + 0.04, 0.28, 0.42, "Trim", name="Rail"))
        for x in (xf, xr):
            p.append(V.box(x - 0.42, x + 0.42, s * 0.47 - 0.03, s * 0.47 + 0.03, zc + 0.06, zc + 0.12, "Trim", name="Leaf"))
    for x in (xf, xr):
        axle(p, x, tr - 0.1, zc)
    # floor + rear wheel housings
    p.append(V.box(-1.62, 0.56, -0.58, 0.58, 0.44, 0.5, "Paint", name="Floor"))
    for s in (1, -1):
        p.append(V.box(xr - 0.46, xr + 0.46, min(s * 0.56, s * 0.76), max(s * 0.56, s * 0.76), 0.5, 0.86, "Paint",
                       bv=0.01, name="WheelHouse"))
    # tub side walls with the rear wheel arch notch
    prof = [(-1.62, 0.4)] + arc(xr, zc, 0.47, math.pi, 0.0, 10) + [(0.58, 0.4), (0.58, 1.0), (-1.62, 1.0)]
    prof[1] = (prof[1][0], 0.4)
    prof[-3] = (prof[-3][0], 0.4)
    side = V.prism(prof, 0.74, 0.78, "Y", "Paint", bv=0.008, name="Side")
    mir(p, [side])
    mir(p, [V.cyl(0.03, 2.2, (-0.52, 0.765, 1.0), "X", "Paint", sides=8, name="TopRail")])
    p.append(V.box(-1.66, -1.6, -0.78, 0.78, 0.4, 1.0, "Paint", bv=0.01, name="RearWall"))
    p.append(V.box(0.52, 0.6, -0.76, 0.76, 0.44, 1.04, "Paint", bv=0.01, name="Cowl"))
    # hood (between the fenders), hinge, latches
    hood = V.loft([(0.6, [(-0.56, 0.6), (0.56, 0.6), (0.6, 0.99), (0.52, 1.045), (-0.52, 1.045), (-0.6, 0.99)]),
                   (1.74, [(-0.56, 0.6), (0.56, 0.6), (0.6, 0.95), (0.52, 1.0), (-0.52, 1.0), (-0.6, 0.95)])],
                  "Paint", bv=0.012, name="Hood")
    p.append(hood)
    p.append(V.cyl(0.012, 1.1, (0.63, 0, 1.048), "Y", "Trim", sides=6, name="Hinge"))
    mir(p, [V.cbox((1.2, 0.605, 0.92), (0.07, 0.02, 0.05), "Trim", name="Latch")])
    # grille panel with slots + headlamps
    p.append(V.box(1.72, 1.77, -0.6, 0.6, 0.48, 0.98, "Paint", bv=0.01, name="Grille"))
    for k in range(7):
        y = -0.27 + 0.09 * k
        p.append(V.box(1.77, 1.775, y - 0.018, y + 0.018, 0.58, 0.9, "Trim", name="Slot"))
    headlamp(p, (1.79, 0.46, 0.8), 0.075)
    # front fenders (flat, sloped nose) + inner wings
    fend = [(0.6, 0.86), (1.6, 0.86), (1.92, 0.62), (1.92, 0.58), (1.6, 0.82), (0.6, 0.82)]
    mir(p, [V.prism(fend, 0.58, 0.88, "Y", "Paint", bv=0.006, name="Fender"),
            V.box(0.6, 1.72, 0.56, 0.6, 0.52, 0.86, "Paint", name="Wing"),
            V.cbox((1.9, 0.8, 0.66), (0.06, 0.06, 0.04), "LightFront", name="Marker"),
            V.cbox((0.9, 0.86, 0.84), (0.05, 0.05, 0.05), "LightFront", name="Blackout")])
    # front bumper, tow hooks, rear bumperettes, tail lamps
    p.append(V.box(1.86, 2.0, -0.88, 0.88, 0.42, 0.56, "Paint", bv=0.012, name="Bumper"))
    for s in (1, -1):
        p.append(V.tube([(1.98, s * 0.55, 0.47), (2.06, s * 0.55, 0.47), (2.08, s * 0.55, 0.53), (2.0, s * 0.55, 0.56)],
                        0.016, "Trim", sides=6, name="Hook"))
    p.append(V.stencil("4-17", (2.001, 0.82, 0.455), (0, -1, 0), (0, 0, 1), 0.07, "Trim"))
    mir(p, [V.box(-1.78, -1.66, 0.56, 0.78, 0.42, 0.52, "Paint", bv=0.01, name="RearBumper"),
            V.box(-1.68, -1.66, 0.6, 0.72, 0.72, 0.86, "Trim", name="TailHouse"),
            V.box(-1.69, -1.68, 0.62, 0.7, 0.8, 0.85, "LightRear", name="Tail"),
            V.box(-1.69, -1.68, 0.62, 0.7, 0.74, 0.78, "LightFront", name="TailWhite")])
    # windshield frame (tilted) with two panes
    tilt = math.radians(-12)
    rotw = Matrix.Translation(Vector((0.6, 0, 1.03))) @ Matrix.Rotation(tilt, 4, "Y")
    frame = [(0, 0.72, 0), (0, 0.72, 0.46), (0, 0.66, 0.5), (0, -0.66, 0.5), (0, -0.72, 0.46), (0, -0.72, 0)]
    fr = V.tube([tuple(rotw @ Vector(q)) for q in frame], 0.022, "Paint", sides=6, name="WsFrame")
    p.append(fr)
    post = V.cbox((0, 0, 0.25), (0.03, 0.04, 0.48), "Paint", name="WsPost")
    post.data.transform(rotw)
    p.append(post)
    for s in (1, -1):
        g = V.cbox((0, s * 0.355, 0.25), (0.008, 0.64, 0.42), "Glass", name="WsGlass")
        g.data.transform(rotw)
        p.append(g)
        wpr = V.cbox((0.02, s * 0.3, 0.47), (0.012, 0.4, 0.012), "Trim", name="Wiper")
        wpr.data.transform(rotw)
        p.append(wpr)
    mir(p, [V.cyl(0.05, 0.012, (0.55, 0.83, 1.32), "Y", "Rim", sides=10, name="Mirror"),
            V.tube([(0.57, 0.72, 1.2), (0.56, 0.8, 1.3)], 0.008, "Trim", sides=4, name="MirrorArm")])
    # dashboard, steering wheel, seats
    p.append(V.box(0.36, 0.56, -0.72, 0.72, 0.8, 0.98, "Paint", bv=0.02, name="Dash"))
    mir(p, [V.cyl(0.03, 0.01, (0.355, 0.15, 0.9), "X", "Trim", sides=8, name="Gauge")])
    hub = Vector((0.12, 0.36, 1.05))
    rot = Matrix.Rotation(math.radians(-35), 3, "Y")
    ring = [tuple(hub + rot @ Vector((0, 0.19 * math.cos(2 * math.pi * k / 12), 0.19 * math.sin(2 * math.pi * k / 12))))
            for k in range(13)]
    p.append(V.tube(ring, 0.016, "Trim", sides=5, caps=False, name="SteerWheel"))
    p.append(V.tube([tuple(hub), (0.45, 0.36, 0.86)], 0.03, "Trim", sides=6, name="Column"))
    for a in (0, math.pi):
        p.append(V.tube([tuple(hub), tuple(hub + rot @ Vector((0, 0.18 * math.cos(a), 0.0)))], 0.01, "Trim", sides=4,
                        name="Spoke"))

    def seat(x, y, wdt):
        return [V.cbox((x, y, 0.62), (0.46, wdt, 0.1), "Trim", bv=0.025, name="Cushion"),
                V.cbox((x - 0.26, y, 0.9), (0.08, wdt, 0.5), "Trim", bv=0.025, rot=(0, math.radians(-12), 0), name="Back"),
                V.box(x - 0.18, x + 0.18, y - 0.18, y + 0.18, 0.5, 0.57, "Paint", name="SeatBox")]
    for s in (1, -1):
        p += seat(0.02, s * 0.36, 0.44)
    p += seat(-1.18, 0.0, 1.0)
    # roll bars
    for x in (-0.38, -1.52):
        hoop = [(x, 0.7, 1.0), (x, 0.7, 1.7), (x, 0.66, 1.8), (x, 0.6, 1.82), (x, -0.6, 1.82), (x, -0.66, 1.8),
                (x, -0.7, 1.7), (x, -0.7, 1.0)]
        p.append(V.tube(hoop, 0.03, "Paint", sides=8, name="Hoop"))
    mir(p, [V.tube([(-0.38, 0.64, 1.805), (-1.52, 0.64, 1.805)], 0.026, "Paint", sides=8, name="RollTop"),
            V.tube([(-0.38, 0.68, 1.75), (0.5, 0.68, 1.47)], 0.024, "Paint", sides=8, name="RollFront")])
    p.append(V.tube([(-1.52, 0.68, 1.06), (-1.52, -0.6, 1.79)], 0.024, "Paint", sides=8, name="Brace"))
    # rear: spare wheel, jerrycan in its bracket, antenna
    p.append(spare((-1.83, 0.25, 0.76), R, TW, RIM, "X"))
    p.append(V.box(-1.72, -1.66, 0.12, 0.38, 0.62, 0.9, "Trim", name="SpareMount"))
    can = [V.box(-1.86, -1.69, -0.66, -0.3, 0.48, 0.96, "Rim", bv=0.02, name="Jerrycan")]
    for d in (1, -1):    # embossed X on the can's rear face
        can.append(V.cbox((-1.865, -0.48, 0.72), (0.012, 0.03, 0.5), "Rim", rot=(math.radians(32 * d), 0, 0), name="CanX"))
    can.append(V.tube([(-1.78, -0.6, 0.96), (-1.78, -0.6, 1.0), (-1.78, -0.42, 1.0), (-1.78, -0.42, 0.96)], 0.01,
                      "Rim", sides=4, caps=False, name="CanHandle"))
    can.append(V.cyl(0.022, 0.05, (-1.78, -0.36, 0.98), "Z", "Rim", sides=6, name="CanSpout"))
    can.append(V.box(-1.88, -1.66, -0.68, -0.28, 0.46, 0.49, "Trim", name="CanTray"))
    can.append(V.box(-1.9, -1.88, -0.68, -0.28, 0.46, 0.62, "Trim", name="CanStrap"))
    p += can
    p.append(V.cyl(0.006, 1.7, (-1.56, -0.8, 1.85), "Z", "Trim", sides=5, r2=0.003, name="Antenna"))
    p.append(V.cyl(0.03, 0.1, (-1.56, -0.8, 1.0), "Z", "Trim", sides=8, name="AntennaBase"))
    p.append(V.box(-1.6, -1.52, -0.84, -0.78, 0.95, 1.02, "Trim", name="AntennaBracket"))
    # shovel on the left side
    p.append(V.cyl(0.018, 0.8, (-0.05, 0.81, 0.72), "X", "Trim", sides=6, name="ShovelHandle"))
    p.append(V.tube([(0.35, 0.81, 0.72), (0.43, 0.81, 0.72), (0.47, 0.81, 0.75), (0.47, 0.81, 0.69)], 0.012, "Trim",
                    sides=4, name="ShovelGrip"))
    p.append(V.prism([(-0.45, 0.66), (-0.7, 0.62), (-0.76, 0.72), (-0.7, 0.82), (-0.45, 0.78)], 0.8, 0.815, "Y", "Rim",
                     name="ShovelBlade"))
    for x in (-0.3, 0.25):
        p.append(V.box(x - 0.03, x + 0.03, 0.78, 0.83, 0.68, 0.76, "Trim", name="ShovelClip"))
    # exhaust along the right side
    p.append(V.tube([(0.6, -0.5, 0.36), (-1.0, -0.62, 0.36), (-1.7, -0.62, 0.36)], 0.03, "Trim", sides=6, name="Exhaust"))
    # stencils (invented numbers)
    stencil_side(p, "47-208", 0.0, 0.86, 0.781, 0.09)
    p.append(V.stencil("208", (1.45, -0.18, 1.0 + 0.026), (0, 1, 0), (-1, 0, 0), 0.16, "Trim", normal_off=0.004))
    p.append(V.stencil("3-19", (-1.661 - 0.0, 0.56, 0.6), (0, -1, 0), (0, 0, 1), 0.06, "Trim"))
    body = V.finish(p, "Body")
    ws = wheels(body, [("Wheel_FL", xf, tr), ("Wheel_FR", xf, -tr), ("Wheel_RL", xr, tr), ("Wheel_RR", xr, -tr)],
                R, TW, RIM, segs=16, beadlock=8)
    return [body] + ws


# =========================================================================== truck
def make_truck():
    mats(canvas=True)
    p = []
    R, TW, RIM = 0.55, 0.38, 0.3
    xf, xm, xr, tr = 2.55, -1.15, -2.55, 0.97
    zc = wz(R, 16)
    # chassis, axles, springs, tanks
    for s in (1, -1):
        p.append(V.box(-3.5, 3.45, s * 0.46 - 0.05, s * 0.46 + 0.05, 0.74, 0.98, "Trim", name="Rail"))
        for x in (xf, xm, xr):
            p.append(V.box(x - 0.6, x + 0.6, s * 0.5 - 0.04, s * 0.5 + 0.04, zc + 0.08, zc + 0.18, "Trim", name="Leaf"))
    for x in (xf, xm, xr):
        axle(p, x, tr - 0.12, zc, r=0.075)
    for k in range(-3, 3):
        p.append(V.box(-3.4 + k * 0.0 + (k + 3) * 1.15, -3.32 + (k + 3) * 1.15, -0.46, 0.46, 0.8, 0.9, "Trim",
                       name="CrossMember"))
    mir(p, [V.cyl(0.24, 0.9, (0.55, 0.78, 0.92), "X", "Paint", sides=12, name="FuelTank"),
            V.box(0.3, 0.38, 0.55, 0.85, 0.7, 1.12, "Trim", name="TankStrap"),
            V.box(0.72, 0.8, 0.55, 0.85, 0.7, 1.12, "Trim", name="TankStrap2")])
    # cab
    cab = V.box(1.0, 2.15, -1.12, 1.12, 1.0, 2.72, "Paint", bv=0.06, seg=2, name="Cab")
    p.append(cab)
    for s in (1, -1):    # windows on dark backing
        p.append(V.box(2.15, 2.16, min(s * 0.06, s * 1.0), max(s * 0.06, s * 1.0), 2.02, 2.6, "Trim", name="WsBack"))
        p.append(V.box(2.16, 2.175, min(s * 0.08, s * 0.98), max(s * 0.08, s * 0.98), 2.04, 2.58, "Glass", name="Ws"))
        p.append(V.box(2.15, 2.19, min(s * 0.4, s * 0.45), max(s * 0.4, s * 0.45), 2.62, 2.64, "Trim", name="WiperP"))
        p.append(V.cbox((2.18, s * 0.5, 2.3), (0.015, 0.015, 0.5), "Trim", rot=(math.radians(20 * s), 0, 0), name="Wiper"))
    mir(p, [V.box(1.25, 2.0, 1.12, 1.125, 1.95, 2.55, "Trim", name="SideWinBack"),
            V.box(1.27, 1.98, 1.125, 1.135, 1.97, 2.53, "Glass", name="SideWin"),
            V.box(1.18, 1.2, 1.12, 1.13, 1.1, 2.6, "Trim", name="DoorGapR"),
            V.box(2.05, 2.07, 1.12, 1.13, 1.1, 2.6, "Trim", name="DoorGapF"),
            V.box(1.2, 2.06, 1.12, 1.13, 1.1, 1.12, "Trim", name="DoorGapB"),
            V.box(1.35, 1.55, 1.12, 1.15, 1.75, 1.79, "Trim", bv=0.006, name="Handle"),
            V.box(1.3, 1.9, 0.95, 1.15, 0.72, 0.76, "Trim", name="Step"),
            V.box(1.3, 1.34, 0.95, 1.15, 0.72, 1.0, "Trim", name="StepHanger"),
            V.box(2.15, 2.25, 1.0, 1.06, 2.2, 2.26, "Trim", name="MirrorArm"),
            V.box(2.2, 2.24, 1.2, 1.38, 1.95, 2.35, "Trim", bv=0.01, name="MirrorBody"),
            V.box(2.245, 2.25, 1.22, 1.36, 1.97, 2.33, "Rim", name="MirrorGlass"),
            V.tube([(2.2, 1.06, 2.23), (2.22, 1.25, 2.23)], 0.012, "Trim", sides=4, name="MirrorBar"),
            V.cbox((2.12, 0.95, 2.74), (0.06, 0.08, 0.04), "LightFront", name="RoofMarker")])
    p.append(V.cyl(0.32, 0.06, (1.55, -0.35, 2.74), "Z", "Trim", sides=14, name="HatchRing"))
    p.append(V.cyl(0.28, 0.05, (1.55, -0.35, 2.78), "Z", "Paint", sides=14, name="Hatch"))
    # snorkel (right front corner) and exhaust stack (left rear corner)
    p.append(V.tube([(2.0, -1.1, 1.4), (2.08, -1.2, 1.5), (2.08, -1.2, 2.9), (2.15, -1.2, 3.0)], 0.07, "Trim", sides=8,
                    name="Snorkel"))
    p.append(V.cyl(0.1, 0.12, (2.2, -1.2, 3.0), "X", "Trim", sides=8, name="SnorkelCap"))
    p.append(V.tube([(1.0, 1.05, 1.0), (0.92, 1.18, 1.1), (0.92, 1.18, 2.95)], 0.06, "Trim", sides=8, name="Stack"))
    p.append(V.cyl(0.09, 0.9, (0.92, 1.18, 2.3), "Z", "Rim", sides=10, caps=(False, False), name="HeatShield"))
    # hood, fenders, grille, brush guard, headlamps, bumper
    hood = V.loft([(2.15, [(-0.66, 1.0), (0.66, 1.0), (0.7, 1.72), (0.6, 1.8), (-0.6, 1.8), (-0.7, 1.72)]),
                   (3.42, [(-0.66, 1.0), (0.66, 1.0), (0.7, 1.62), (0.6, 1.7), (-0.6, 1.7), (-0.7, 1.62)])],
                  "Paint", bv=0.02, name="Hood")
    p.append(hood)
    mir(p, [V.box(2.6, 3.3, 0.7, 0.71, 1.25, 1.55, "Trim", name="Louver") for _ in range(1)])
    for k in range(5):
        x = 2.55 + k * 0.15
        p.append(V.box(x, x + 0.08, 0.705, 0.715, 1.3, 1.52, "Trim", name="Vent"))
        p.append(V.box(x, x + 0.08, -0.715, -0.705, 1.3, 1.52, "Trim", name="Vent"))
    fend = [(1.95, 1.3), (3.05, 1.3), (3.48, 1.02), (3.48, 0.95), (3.03, 1.24), (1.95, 1.24)]
    mir(p, [V.prism(fend, 0.62, 1.22, "Y", "Paint", bv=0.01, name="Fender"),
            V.box(1.92, 1.97, 0.62, 1.22, 0.86, 1.3, "Paint", name="Mudguard"),
            V.box(2.15, 3.42, 0.62, 0.68, 1.0, 1.3, "Paint", name="InnerWing")])
    p.append(V.box(3.42, 3.47, -0.62, 0.62, 0.98, 1.68, "Paint", bv=0.01, name="Grille"))
    for k in range(6):
        z = 1.07 + k * 0.1
        p.append(V.box(3.47, 3.49, -0.56, 0.56, z, z + 0.04, "Trim", name="GrilleBar"))
    for s in (1, -1):
        p.append(V.tube([(3.47, s * 0.6, 1.0), (3.65, s * 0.6, 1.05), (3.65, s * 0.6, 1.72), (3.45, s * 0.6, 1.75)], 0.03,
                        "Trim", sides=6, name="Guard"))
    for z in (1.4, 1.72):
        p.append(V.tube([(3.65, -0.6, z), (3.65, 0.6, z)], 0.025, "Trim", sides=6, name="GuardBar"))
    headlamp(p, (3.46, 0.9, 1.13), 0.09)
    mir(p, [V.cbox((3.3, 1.1, 1.24), (0.08, 0.08, 0.05), "LightFront", name="Blinker")])
    p.append(V.box(3.45, 3.62, -1.2, 1.2, 0.74, 0.98, "Paint", bv=0.015, name="Bumper"))
    for s in (1, -1):
        p.append(V.tube([(3.6, s * 0.75, 0.82), (3.72, s * 0.75, 0.82), (3.74, s * 0.75, 0.92), (3.6, s * 0.75, 0.94)],
                        0.025, "Trim", sides=6, name="Shackle"))
    p.append(V.stencil("72-415", (3.621, 0.55, 0.8), (0, -1, 0), (0, 0, 1), 0.1, "Trim"))
    # behind the cab: spare wheel + tool box
    p.append(spare((0.82, 0.0, 1.95), R, TW, RIM, "X"))
    p.append(V.box(0.95, 1.0, -0.3, 0.3, 1.0, 2.5, "Trim", name="SpareCarrier"))
    p.append(V.box(0.2, 0.75, -1.15, -0.5, 1.0, 1.25, "Paint", bv=0.01, name="ToolBox"))
    # cargo bed: floor, boards with stakes, tailgate
    p.append(V.box(-3.55, 0.85, -1.2, 1.2, 1.2, 1.32, "Paint", bv=0.01, name="BedFloor"))
    mir(p, [V.box(-3.55, 0.85, 1.16, 1.2, 1.32, 1.92, "Paint", bv=0.006, name="Board")])
    p.append(V.box(0.8, 0.85, -1.2, 1.2, 1.32, 1.92, "Paint", name="FrontBoard"))
    for k in range(8):
        x = -3.45 + k * 0.6
        mir(p, [V.box(x, x + 0.06, 1.2, 1.23, 1.22, 1.92, "Paint", name="Stake")])
    p.append(V.box(-3.6, -3.55, -1.2, 1.2, 1.22, 1.9, "Paint", bv=0.008, name="Tailgate"))
    for z in (1.42, 1.72):
        p.append(V.box(-3.62, -3.6, -1.1, 1.1, z, z + 0.04, "Paint", name="GateRib"))
    p.append(V.stencil("72-415", (-3.621, 0.42, 1.52), (0, -1, 0), (0, 0, 1), 0.12, "Trim"))
    mir(p, [V.cyl(0.035, 0.1, (-3.6, 1.0, 1.25), "Y", "Trim", sides=6, name="Hinge")])
    # benches inside (visible through the open rear)
    mir(p, [V.box(-3.3, 0.6, 0.72, 1.12, 1.62, 1.7, "Canvas", bv=0.01, name="Bench"),
            V.box(-3.3, 0.6, 0.8, 1.05, 1.32, 1.62, "Paint", name="BenchBox")])
    # tarp over 6 hoops (sagging between hoops), inner lining, rolled rear flap
    hoops = [-3.47 + k * (0.82 + 3.47) / 5 for k in range(6)]

    def tsec(sag):
        half = [(1.22 - sag * 0.4, 1.9), (1.22 - sag * 0.5, 2.62), (1.12 - sag * 0.6, 2.88), (0.75 - sag * 0.3, 3.02),
                (0.0, 3.06 - sag)]
        return half + [(-y, z) for y, z in reversed(half[:-1])]
    secs = []
    for i, x in enumerate(hoops):
        secs.append((x, tsec(0.0)))
        if i < len(hoops) - 1:
            secs.append(((x + hoops[i + 1]) / 2, tsec(0.035)))
    # open section: build without caps, then close the front
    nn = len(secs[0][1])
    verts, faces = [], []
    for x, pts in secs:
        verts += [(x, y, z) for y, z in pts]
    for i in range(len(secs) - 1):
        for k in range(nn - 1):
            faces.append((i * nn + k, i * nn + k + 1, (i + 1) * nn + k + 1, (i + 1) * nn + k))
    outer = V.part("Tarp", verts, faces, "Canvas")
    outer.data.update()
    if outer.data.polygons[nn // 2].normal.z < 0:
        outer.data.flip_normals()
    nb.auto_smooth(outer, 50)
    inner = V.part("TarpIn", [(x, y * 0.985, 1.9 + (z - 1.9) * 0.985) for x, y, z in verts], faces, "Canvas")
    inner.data.update()
    if inner.data.polygons[nn // 2].normal.z > 0:
        inner.data.flip_normals()
    nb.auto_smooth(inner, 50)
    p += [outer, inner]
    front = [(y, z) for y, z in tsec(0.0)]
    p.append(V.prism(front, 0.8, 0.83, "X", "Canvas", name="TarpFront"))
    top = [(y, z) for y, z in tsec(0.0) if z >= 2.55]
    top = [(top[0][0], 2.55)] + top + [(top[-1][0], 2.55)]
    p.append(V.prism(top, -3.48, -3.46, "X", "Canvas", name="RearFlap"))
    p.append(V.cyl(0.08, 2.3, (-3.5, 0, 2.52), "Y", "Canvas", sides=10, name="Roll"))
    for x in hoops:
        rib = [(x, y * 1.006, 1.9 + (z - 1.9) * 1.006) for y, z in tsec(0.0)]
        p.append(V.tube(rib, 0.018, "Canvas", sides=5, caps=False, name="Rib"))
        mir(p, [V.box(x - 0.02, x + 0.02, 1.2, 1.235, 1.6, 1.98, "Trim", name="Strap")])
    # rear lights, mud flaps, rear fenders
    mir(p, [V.box(-3.6, -3.55, 0.8, 1.15, 0.92, 1.08, "Trim", name="TailHouse"),
            V.box(-3.61, -3.6, 0.82, 0.95, 0.95, 1.05, "LightRear", name="Tail"),
            V.box(-3.61, -3.6, 0.98, 1.12, 0.95, 1.05, "LightFront", name="TailAmber"),
            V.box(-3.3, -3.27, 0.76, 1.2, 0.35, 1.15, "Trim", name="MudFlap"),
            V.box(-3.3, -0.4, 0.76, 1.2, 1.12, 1.17, "Paint", bv=0.006, name="RearFender")])
    stencil_side(p, "72-415", -1.0, 1.45, 1.201, 0.13)
    body = V.finish(p, "Body")
    ws = wheels(body, [("Wheel_FL", xf, tr), ("Wheel_FR", xf, -tr), ("Wheel_ML", xm, tr), ("Wheel_MR", xm, -tr),
                       ("Wheel_RL", xr, tr), ("Wheel_RR", xr, -tr)], R, TW, RIM, segs=16, beadlock=8)
    return [body] + ws


# =========================================================================== APC
def apc_hull_section(x):
    """Half section (y, z) of the hull: V-shaped belly, inner side between the wheels,
    sponson over the wheels, sloped upper plates."""
    return [(0.0, 0.42), (0.55, 0.47), (0.82, 0.72), (0.84, 1.18), (1.34, 1.24), (1.38, 1.56), (1.06, 1.95), (0.0, 1.98)]


def make_apc():
    mats()
    p = []
    R, TW, RIM = 0.55, 0.36, 0.29
    xs = [2.15, 0.85, -0.75, -2.05]
    tr = 1.1
    zc = wz(R, 14)
    # hull: faceted loft (glacis at the front, sloped rear), bevelled plates
    def sec(x, sc_y=1.0, dz_top=0.0, dz_bot=0.0, low=0.0):
        h = apc_hull_section(x)
        out = []
        for i, (y, z) in enumerate(h):
            zz = z + (dz_top if i >= 5 else 0.0) + (dz_bot if i <= 2 else 0.0)
            if i in (3, 4) and low:
                zz += low
            out.append((y * sc_y, zz))
        return out + [(-y, z) for y, z in reversed(out[1:-1])]
    def full(half):
        return half + [(-y, z) for y, z in reversed(half[1:-1])]
    glacis = full([(0.0, 0.5), (0.55, 0.55), (0.8, 0.78), (0.82, 1.15), (1.28, 1.2), (1.32, 1.42), (1.0, 1.58),
                   (0.0, 1.6)])
    nose = full([(0.0, 0.74), (0.5, 0.77), (0.7, 0.88), (0.72, 0.98), (1.0, 1.03), (1.05, 1.18), (0.85, 1.33),
                 (0.0, 1.36)])
    sections = [(-3.3, sec(0, 0.93, -0.12, 0.2)), (-3.05, sec(0)), (2.7, sec(0)), (3.25, glacis), (3.5, nose)]
    hull = V.loft(sections, "Paint", bv=0.025, name="Hull", smooth=25, angle=25)
    p.append(hull)
    # bolt-on armour plates (bevelled) on the sponson sides, with bolts
    for i, (x0, x1) in enumerate(((-2.9, -1.45), (-1.4, 0.15), (0.2, 1.65), (1.7, 2.6))):
        plate = V.box(x0, x1, 1.375, 1.42, 1.28, 1.52, "Paint", bv=0.02, name="Applique")
        objs = [plate]
        for xb in (x0 + 0.08, x1 - 0.08):
            for zb in (1.33, 1.47):
                objs.append(V.cyl(0.015, 0.015, (xb, 1.425, zb), "Y", "Trim", sides=6, name="Bolt"))
        mir(p, objs)
    # glacis: driver hatch + vision blocks, headlamps with guards, splash vane, tow hooks
    p.append(V.cyl(0.3, 0.05, (2.45, 0.45, 1.97), "Z", "Paint", sides=12, bv=0.01, name="DriverHatch"))
    p.append(V.cyl(0.34, 0.03, (2.45, 0.45, 1.955), "Z", "Trim", sides=12, name="HatchRing"))
    p.append(V.box(2.3, 2.38, 0.38, 0.52, 2.0, 2.06, "Trim", name="HatchHinge"))
    for k in (-1, 0, 1):
        yv = 0.45 + k * 0.2
        p.append(V.cbox((2.82, yv, 1.86), (0.12, 0.14, 0.07), "Trim", rot=(0, math.radians(-25), 0), name="Periscope"))
        p.append(V.cbox((2.885, yv, 1.85), (0.012, 0.11, 0.045), "Glass", rot=(0, math.radians(-25), 0), name="Vision"))
    p.append(V.prism([(3.2, 1.55), (3.38, 1.48), (3.4, 1.52), (3.24, 1.62)], -1.0, 1.0, "Y", "Paint", bv=0.008,
                     name="SplashVane"))
    headlamp(p, (3.42, 0.78, 1.2), 0.07)
    mir(p, [V.cbox((3.3, 1.05, 1.42), (0.06, 0.08, 0.05), "LightFront", name="Blinker"),
            V.tube([(3.45, 0.6, 0.72), (3.6, 0.6, 0.72), (3.62, 0.6, 0.82), (3.47, 0.6, 0.84)], 0.03, "Trim", sides=6,
                   name="TowHook")])
    p.append(V.stencil("5-306", (3.5, 0.3, 0.84), (0, -1, 0), (0, 0, 1), 0.1, "Trim", normal_off=0.004))
    # roof: engine grille (front right), rear crew hatches, antennas, storage boxes
    for k in range(6):
        x = 1.55 + k * 0.13
        p.append(V.box(x, x + 0.07, -1.0, -0.35, 1.97, 2.01, "Trim", name="EngineGrille"))
    p.append(V.box(1.5, 2.33, -1.04, -0.31, 1.955, 1.975, "Paint", name="GrilleFrame"))
    for s in (1, -1):
        p.append(V.box(-2.9, -1.9, min(s * 0.12, s * 0.75), max(s * 0.12, s * 0.75), 1.97, 2.03, "Paint", bv=0.012,
                       name="RoofHatch"))
        p.append(V.box(-2.4, -2.3, min(s * 0.15, s * 0.7), max(s * 0.15, s * 0.7), 2.03, 2.05, "Trim", name="HatchHandle"))
    mir(p, [V.cyl(0.035, 0.1, (-2.95, 1.0, 2.02), "Z", "Trim", sides=8, name="AntBase"),
            V.cyl(0.007, 2.0, (-2.95, 1.0, 3.05), "Z", "Trim", sides=5, r2=0.003, name="Antenna"),
            V.box(-1.6, -0.6, 1.0, 1.32, 1.88, 2.1, "Paint", bv=0.015, name="StowBox"),
            V.box(-1.2, -1.0, 1.32, 1.34, 1.95, 2.02, "Trim", name="StowLatch")])
    # rear: door with seams, handle, tail lights, exhaust grille on the left side
    p.append(V.box(-3.33, -3.3, -0.55, 0.55, 0.7, 1.75, "Paint", bv=0.01, name="RearDoor"))
    p.append(V.box(-3.345, -3.33, -0.08, 0.08, 1.2, 1.3, "Trim", name="DoorHandle"))
    for s in (1, -1):
        p.append(V.box(-3.34, -3.33, s * 0.56 - 0.01, s * 0.56 + 0.01, 0.7, 1.75, "Trim", name="DoorSeam"))
    p.append(V.box(-3.34, -3.33, -0.56, 0.56, 1.75, 1.77, "Trim", name="DoorSeamTop"))
    p.append(V.box(-3.36, -3.33, -0.07, 0.07, 1.45, 1.6, "Glass", name="DoorVision"))
    mir(p, [V.box(-3.32, -3.28, 0.8, 1.05, 1.42, 1.58, "Trim", name="TailHouse"),
            V.box(-3.33, -3.32, 0.83, 0.94, 1.45, 1.55, "LightRear", name="Tail"),
            V.box(-3.33, -3.32, 0.95, 1.02, 1.45, 1.55, "LightFront", name="TailAmber")])
    p.append(V.stencil("5-306", (-3.36, 0.3, 0.85), (0, -1, 0), (0, 0, 1), 0.1, "Trim", normal_off=0.0))
    for k in range(5):
        p.append(V.box(1.6 + k * 0.12, 1.66 + k * 0.12, 1.42, 1.44, 1.3, 1.5, "Trim", name="ExhaustSlot"))
    stencil_side(p, "5-306", -0.9, 1.6, 1.36, 0.16)
    # wheel-station hubs (suspension arms) between the hull and the wheels
    for x in xs:
        mir(p, [V.box(x - 0.08, x + 0.08, 0.8, 0.95, zc - 0.07, zc + 0.07, "Trim", name="Arm"),
                V.cyl(0.08, 0.5, (x, 1.05, 1.0), "Z", "Trim", sides=8, name="Damper")])
    body = V.finish(p, "Body")
    out = [body]
    names = [("Wheel_FL", "Wheel_FR"), ("Wheel_F2L", "Wheel_F2R"), ("Wheel_R2L", "Wheel_R2R"), ("Wheel_RL", "Wheel_RR")]
    spec = []
    for x, (nl, nr) in zip(xs, names):
        spec += [(nl, x, tr), (nr, x, -tr)]
    out += wheels(body, spec, R, TW, RIM, segs=14, beadlock=0)
    # turret (separate node) + gun (child node)
    tp = []
    ring_z = 1.98
    tz = 0.0
    def tsec_(sc, z):
        pts = [(0.95, 0.55), (0.35, 0.82), (-0.75, 0.82), (-1.05, 0.5), (-1.05, -0.5), (-0.75, -0.82), (0.35, -0.82),
               (0.95, -0.55)]
        return [(x * sc, y * sc, z) for x, y in pts]
    lo, hi = tsec_(1.0, tz + 0.05), tsec_(0.82, tz + 0.55)
    verts = lo + hi
    n = len(lo)
    faces = [tuple(reversed(range(n))), tuple(n + i for i in range(n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    tb = V.part("TurretBody", verts, faces, "Paint")
    V.fix_normals(tb)
    V.bevel(tb, 0.025)
    nb.auto_smooth(tb, 25)
    tp.append(tb)
    tp.append(V.cyl(0.85, 0.06, (0, 0, tz + 0.03), "Z", "Trim", sides=16, name="TurretRing"))
    tp.append(V.cyl(0.28, 0.05, (-0.35, 0.3, tz + 0.58), "Z", "Paint", sides=12, bv=0.01, name="CmdHatch"))
    tp.append(V.cyl(0.32, 0.04, (-0.35, 0.3, tz + 0.56), "Z", "Trim", sides=12, name="CmdRing"))
    for k in range(5):
        a = 2 * math.pi * k / 5
        tp.append(V.box(-0.35 + 0.33 * math.cos(a) - 0.04, -0.35 + 0.33 * math.cos(a) + 0.04, 0.3 + 0.33 * math.sin(a) - 0.04,
                        0.3 + 0.33 * math.sin(a) + 0.04, tz + 0.55, tz + 0.64, "Trim", name="CmdPeri"))
    tp.append(V.box(0.15, 0.4, -0.45, -0.2, tz + 0.55, tz + 0.72, "Trim", bv=0.01, name="Sight"))
    tp.append(V.box(0.4, 0.405, -0.43, -0.22, tz + 0.58, tz + 0.69, "Glass", name="SightGlass"))
    for s in (1, -1):    # smoke dischargers: 4 tubes per side, angled forward/out
        for k in range(4):
            c = Vector((0.55 - k * 0.11, s * 0.78, tz + 0.42))
            tube = V.cyl(0.04, 0.22, (0, 0, 0), "X", "Trim", sides=8, caps=(True, False), name="Smoke")
            tube.data.transform(Matrix.Translation(c) @ Matrix.Rotation(math.radians(20 * s), 4, "Z") @
                                Matrix.Rotation(math.radians(-25), 4, "Y"))
            tp.append(tube)
        tp.append(V.box(0.15, 0.62, s * 0.78 - 0.07, s * 0.78 + 0.07, tz + 0.3, tz + 0.36, "Trim", name="SmokeRack"))
    tp.append(V.box(-1.25, -1.0, -0.6, 0.6, tz + 0.1, tz + 0.45, "Paint", bv=0.015, name="Bustle"))
    for k in range(4):
        tp.append(V.box(-1.27, -1.25, -0.55 + k * 0.36, -0.53 + k * 0.36, tz + 0.12, tz + 0.43, "Trim", name="BustleRail"))
    tp.append(V.stencil("31", (0.3, 0.83, tz + 0.15), (-1, 0, 0), (0, 0, 1), 0.2, "Trim", normal_off=0.0))
    tp.append(V.stencil("31", (0.0, -0.83, tz + 0.15), (1, 0, 0), (0, 0, 1), 0.2, "Trim", normal_off=0.0))
    for o in tp:
        V.uv_auto(o)
    turret = V.finish(tp, "Turret")
    turret.location = (0.3, 0, ring_z)
    turret.parent = body
    # gun: mantlet + barrel + muzzle brake + coax MG; origin on the trunnion axis
    gp = []
    gp.append(V.box(-0.12, 0.22, -0.3, 0.3, -0.16, 0.16, "Paint", bv=0.03, name="Mantlet"))
    gp.append(V.lathe([(0.075, 0.2), (0.075, 0.5), (0.055, 0.6), (0.052, 1.9), (0.0001, 1.9)], 12, (0, 0, 0), "X",
                      "Trim", name="Barrel", fix=True))
    gp.append(V.cyl(0.07, 0.3, (1.15, 0, 0), "X", "Trim", sides=12, name="Evacuator"))
    gp.append(V.cyl(0.08, 0.18, (1.97, 0, 0), "X", "Trim", sides=12, name="Muzzle"))
    for s in (1, -1):
        gp.append(V.box(1.93, 2.0, s * 0.06, s * 0.085, -0.035, 0.035, "Trim", name="MuzzlePort") if s > 0 else
                  V.box(1.93, 2.0, -0.085, -0.06, -0.035, 0.035, "Trim", name="MuzzlePort"))
    gp.append(V.cyl(0.02, 0.5, (0.42, -0.2, 0.0), "X", "Trim", sides=6, name="Coax"))
    for o in gp:
        V.uv_auto(o)
    gun = V.finish(gp, "Gun")
    gun.location = (0.95, 0, 0.3)
    gun.parent = turret
    out += [turret, gun]
    return out


VEHICLES = {"jeep": make_jeep, "truck": make_truck, "apc": make_apc}


def build(kind):
    nb.reset_scene()
    objs = VEHICLES[kind]()
    tris = V.report("army_" + kind, objs, BUDGET)
    path = nb.export_glb("army_" + kind, texcoords=True)
    return path, tris


if __name__ == "__main__":
    for k in [a for a in sys.argv[1:] if a in VEHICLES] or list(VEHICLES):
        p, t = build(k)
        print("[army] %s: %d tris -> %s (%.0f KB)" % (k, t, p, os.path.getsize(p) / 1024))
