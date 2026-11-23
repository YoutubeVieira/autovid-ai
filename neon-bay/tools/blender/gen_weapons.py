"""Neon Bay - procedural firearms (original, generic designs: no real model, no brand).

    python3 tools/blender/gen_weapons.py               # every weapon
    python3 tools/blender/gen_weapons.py pistol rail   # some weapons

Outputs models/w_<id>.glb (+ .glb.js) for:
    pistol uzi shotgun rifle sniper rocket minigun lmg gl rail

Contract (glTF, export_yup): 1 unit = 1 m, barrel/muzzle towards +X, up +Y,
the right side of the weapon is +Z. Origin = centre of the main grip, where the
right hand closes (for the rocket launcher / minigun: the rear pistol grip).
Materials: Body (main colour, recoloured by the game for skins), Metal, Grip,
Glow (emissive: sight dots, LEDs, rail coils) on every weapon, Lens (optics) on
rifle, sniper, rocket, gl, rail. No animation. Budget < 2500 tris, < 120 KB.

Blender side (Z-up): X forward, Z up, Y = left side of the weapon. Shapes are
mostly side profiles (x, z) extruded across Y ("prism"), tubes along X and
lathes, with small chamfers so they catch the light from far away.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402,F401
import bmesh  # noqa: E402
from mathutils import Vector, Matrix  # noqa: E402

import nb_common as nb  # noqa: E402

M = {}


def mats(body=(0.075, 0.078, 0.085)):
    M["Body"] = nb.material("Body", body, metallic=0.15, roughness=0.45)
    M["Metal"] = nb.material("Metal", (0.30, 0.31, 0.33), metallic=0.9, roughness=0.32)
    M["Grip"] = nb.material("Grip", (0.045, 0.045, 0.048), roughness=0.85)
    M["Glow"] = nb.material("Glow", (0.25, 0.95, 1.0), emission=(0.25, 0.95, 1.0), strength=4.0, roughness=0.4)
    M["Lens"] = nb.material("Lens", (0.04, 0.09, 0.14), metallic=0.5, roughness=0.06)


# --------------------------------------------------------------------------- primitives
def _finish(obj, bevel, seg, angle):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ngons = [f for f in bm.faces if len(f.verts) > 4]
    if ngons:
        bmesh.ops.triangulate(bm, faces=ngons, quad_method="BEAUTY", ngon_method="BEAUTY")
    bm.to_mesh(obj.data)
    bm.free()
    if bevel > 0:
        nb.add_bevel(obj, bevel, seg, angle)
        nb.apply_modifiers(obj)
    return obj


def prism(pts, w, mat, y=0.0, bevel=0.0015, seg=1, angle=35):
    """Side profile [(x, z), ...] extruded across Y (thickness w, centred on y)."""
    n = len(pts)
    y0, y1 = y - w / 2, y + w / 2
    verts = [(x, y0, z) for x, z in pts] + [(x, y1, z) for x, z in pts]
    faces = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
    faces += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return _finish(nb.mesh_object("prism", verts, faces, [M[mat]]), bevel, seg, angle)


def top_prism(pts, h, mat, z=0.0, bevel=0.0015, seg=1, angle=35):
    """Top-view profile [(x, y), ...] extruded along Z (height h, centred on z)."""
    n = len(pts)
    verts = [(x, y, z - h / 2) for x, y in pts] + [(x, y, z + h / 2) for x, y in pts]
    faces = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
    faces += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return _finish(nb.mesh_object("tprism", verts, faces, [M[mat]]), bevel, seg, angle)


def box(x0, x1, z0, z1, w, mat, y=0.0, bevel=0.0015, seg=1):
    return prism([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], w, mat, y, bevel, seg)


def tube_x(r, x0, x1, mat, z=0.0, y=0.0, sides=12, r2=None, bevel=0.0, seg=1):
    """Cylinder along X from x0 to x1 (radius r at x0, r2 at x1)."""
    o = nb.cylinder("cyl", r, x1 - x0, ((x0 + x1) / 2, y, z), sides, M[mat], axis="X", r2=r2)
    return _finish(o, bevel, seg, 35)


def tube_z(r, z0, z1, mat, x=0.0, y=0.0, sides=10, r2=None, bevel=0.0):
    o = nb.cylinder("cyl", r, z1 - z0, (x, y, (z0 + z1) / 2), sides, M[mat], axis="Z", r2=r2)
    return _finish(o, bevel, 1, 35)


def tube_y(r, w, mat, x=0.0, z=0.0, y=0.0, sides=10, bevel=0.0):
    o = nb.cylinder("cyl", r, w, (x, y, z), sides, M[mat], axis="Y")
    return _finish(o, bevel, 1, 35)


def lathe_x(profile, mat, z=0.0, y=0.0, sides=12, cap_start=True, cap_end=True, bevel=0.0):
    """Revolve [(radius, x), ...] around an axis parallel to X."""
    v, f = nb.lathe(profile, sides, axis="X", cap_start=cap_start, cap_end=cap_end)
    v = [(a, b + y, c + z) for a, b, c in v]
    return _finish(nb.mesh_object("lathe", v, f, [M[mat]]), bevel, 1, 35)


def ring_x(r_in, r_out, x0, x1, mat, z=0.0, y=0.0, sides=12):
    """Thick ring (washer) along X."""
    prof = [(r_in, x0), (r_out, x0), (r_out, x1), (r_in, x1), (r_in, x0)]
    return lathe_x(prof, mat, z, y, sides, False, False)


def sphere(r, loc, mat, seg=8, rings=5, scale=(1, 1, 1)):
    return nb.uv_sphere("sph", r, loc, seg, rings, M[mat], scale)


def rot(obj, deg, axis="Y", pivot=(0, 0, 0)):
    """Rotate an object's mesh around a pivot (degrees, Blender axes)."""
    R = Matrix.Rotation(math.radians(deg), 4, axis)
    T = Matrix.Translation(Vector(pivot))
    obj.data.transform(T @ R @ T.inverted())
    return obj


def move(obj, d):
    obj.data.transform(Matrix.Translation(Vector(d)))
    return obj


def mirror_y(obj):
    """Copy of an object mirrored to the other side (y -> -y)."""
    me = obj.data.copy()
    me.transform(Matrix.Scale(-1, 4, Vector((0, 1, 0))))
    me.flip_normals()
    return nb.link(bpy.data.objects.new(obj.name + "_m", me))


def trigger_group(x, z, mat_guard="Body", w=0.010, size=1.0):
    """Trigger guard (U loop) + trigger blade, front of the guard at x, top at z."""
    s = size
    guard = prism([(x - 0.050 * s, z), (x - 0.046 * s, z - 0.032 * s), (x - 0.004 * s, z - 0.034 * s),
                   (x + 0.004 * s, z - 0.004 * s), (x + 0.004 * s, z), (x - 0.003 * s, z),
                   (x - 0.006 * s, z - 0.026 * s), (x - 0.040 * s, z - 0.025 * s), (x - 0.043 * s, z)],
                  w, mat_guard, bevel=0.001)
    trig = prism([(x - 0.028 * s, z), (x - 0.022 * s, z), (x - 0.024 * s, z - 0.014 * s),
                  (x - 0.030 * s, z - 0.022 * s), (x - 0.031 * s, z - 0.019 * s), (x - 0.028 * s, z - 0.012 * s)],
                 0.006, "Metal", bevel=0.0)
    return [guard, trig]


def pistol_grip(top_front, top_back, length, angle, w, mat="Grip", flare=0.004):
    """Slanted pistol grip: top edge from top_back to top_front (x, z), tilted back by angle."""
    a = math.radians(angle)
    d = Vector((-math.sin(a), -math.cos(a)))
    tf, tb = Vector(top_front), Vector(top_back)
    bf, bb = tf + d * length, tb + d * (length + 0.004)
    mid_f = tf + d * (length * 0.45) + Vector((0.004, 0))
    pts = [tuple(tb), tuple(tf), tuple(mid_f), tuple(bf), tuple(bb + Vector((-flare, 0))),
           tuple(tb + d * (length * 0.5) + Vector((-0.004, 0)))]
    centre = (tf + tb) / 2 + d * (length * 0.5)
    obj = prism(pts, w, mat, bevel=0.003, seg=2, angle=30)
    bbf = bb + Vector((-flare, 0))
    obj["bottom"] = (tuple(bf), tuple(bbf), tuple(d))
    return obj, (centre.x, centre.y)


def finish_weapon(name, parts, grip, smooth=32):
    obj = nb.join(parts, "W_" + name)
    obj.data.transform(Matrix.Translation(Vector((-grip[0], 0, -grip[1]))))
    nb.auto_smooth(obj, smooth)
    return obj


# --------------------------------------------------------------------------- weapons
def make_pistol():
    mats()
    p = []
    g, gc = pistol_grip((0.018, 0.032), (-0.030, 0.034), 0.100, 16, 0.030)
    p.append(g)
    bf, bb, d = (Vector(v) for v in g["bottom"])
    p.append(prism([tuple(bf - d * 0.003 + Vector((0.002, 0))), tuple(bb - d * 0.003 - Vector((0.002, 0))),
                    tuple(bb + d * 0.007 - Vector((0.002, 0))), tuple(bf + d * 0.007 + Vector((0.002, 0)))],
                   0.031, "Metal", bevel=0.002))                                       # magazine base
    p.append(prism([(-0.040, 0.030), (0.132, 0.030), (0.136, 0.036), (0.136, 0.048), (-0.044, 0.048),
                    (-0.050, 0.040)], 0.028, "Body", bevel=0.0015))                    # frame
    p.append(box(0.07, 0.132, 0.026, 0.031, 0.020, "Metal", bevel=0.0008))            # accessory rail
    p += trigger_group(0.062, 0.031, "Body", 0.012)
    # slide with a bevelled top and front
    p.append(prism([(-0.046, 0.047), (0.152, 0.047), (0.156, 0.056), (0.156, 0.072), (0.150, 0.079),
                    (-0.040, 0.079), (-0.046, 0.073)], 0.026, "Body", bevel=0.002, seg=2))
    for i in range(5):                                                                # serrations
        x = -0.036 + i * 0.006
        p.append(box(x, x + 0.0025, 0.052, 0.075, 0.0272, "Metal", bevel=0.0))
    p.append(box(0.040, 0.085, 0.064, 0.076, 0.004, "Metal", y=-0.0122, bevel=0.0))  # ejection port (right)
    p.append(tube_x(0.0068, 0.150, 0.1585, "Metal", z=0.064, sides=10))              # muzzle
    p.append(tube_x(0.0042, 0.156, 0.1588, "Grip", z=0.064, sides=8))                # bore
    p.append(box(0.140, 0.148, 0.079, 0.086, 0.004, "Metal", bevel=0.0))              # front sight
    p.append(sphere(0.0017, (0.144, -0.0021, 0.0835), "Glow", 6, 4))
    p.append(box(-0.040, -0.028, 0.079, 0.087, 0.020, "Metal", bevel=0.0))            # rear sight
    for sy in (0.0055, -0.0055):
        p.append(sphere(0.0016, (-0.0285, sy, 0.0835), "Glow", 6, 4))
    p.append(box(-0.054, -0.044, 0.050, 0.066, 0.010, "Metal", bevel=0.001))          # hammer
    p.append(box(-0.008, 0.012, 0.040, 0.046, 0.003, "Metal", y=0.0145, bevel=0.0))   # slide stop
    return finish_weapon("pistol", p, gc)


def make_uzi():
    mats()
    p = []
    g, gc = pistol_grip((0.020, 0.024), (-0.022, 0.024), 0.112, 6, 0.032)
    p.append(g)
    p.append(box(-0.022, 0.014, -0.150, 0.0, 0.022, "Metal", bevel=0.001))            # magazine in the grip
    rot(p[-1], -6, "Y", (0.0, 0, 0.024))
    move(p[-1], (0.004, 0, -0.03))
    p.append(box(-0.016, 0.016, -0.186, -0.176, 0.026, "Body", bevel=0.002))          # magazine base
    rot(p[-1], -6, "Y", (0.0, 0, 0.024))
    move(p[-1], (0.004, 0, 0.0))
    # receiver: long box, rounded top
    p.append(prism([(-0.150, 0.022), (0.170, 0.022), (0.180, 0.034), (0.180, 0.080), (0.170, 0.090),
                    (-0.140, 0.090), (-0.150, 0.080)], 0.040, "Body", bevel=0.003, seg=2))
    p.append(box(0.06, 0.15, 0.040, 0.075, 0.003, "Grip", y=0.0205, bevel=0.0))       # side panel L
    p.append(box(0.06, 0.15, 0.040, 0.075, 0.003, "Grip", y=-0.0205, bevel=0.0))      # side panel R
    p.append(tube_x(0.010, 0.175, 0.255, "Metal", z=0.056, sides=10))                 # barrel
    p.append(ring_x(0.006, 0.0135, 0.18, 0.205, "Metal", z=0.056, sides=10))          # barrel nut
    p.append(tube_x(0.0055, 0.253, 0.2555, "Grip", z=0.056, sides=8))
    p += trigger_group(0.058, 0.022, "Body", 0.012)
    p.append(tube_z(0.005, 0.090, 0.100, "Metal", x=-0.05, sides=8))                  # cocking knob
    p.append(sphere(0.007, (-0.05, 0, 0.102), "Metal", 8, 4))
    p.append(box(0.150, 0.165, 0.090, 0.104, 0.016, "Metal", bevel=0.001))            # front sight ears
    p.append(sphere(0.0018, (0.157, 0, 0.1), "Glow", 6, 4))
    p.append(box(-0.130, -0.118, 0.090, 0.100, 0.016, "Metal", bevel=0.001))          # rear sight
    # folded wire stock along the left side
    for dz in (0.034, 0.078):
        p.append(tube_x(0.004, -0.205, 0.10, "Metal", z=dz, y=0.025, sides=6))
    p.append(box(-0.213, -0.197, 0.028, 0.086, 0.026, "Metal", y=0.012, bevel=0.002)) # butt plate
    p.append(box(-0.163, -0.150, 0.028, 0.086, 0.046, "Metal", bevel=0.001))          # hinge block
    p.append(box(0.02, 0.05, 0.088, 0.093, 0.004, "Glow", y=-0.0165, bevel=0.0))      # LED (fire selector)
    return finish_weapon("uzi", p, gc)


def make_shotgun():
    mats((0.20, 0.13, 0.08))
    p = []
    # stock + wrist (Body), traditional shape; the grip is the narrow wrist
    p.append(prism([(-0.335, 0.045), (-0.335, -0.075), (-0.315, -0.080), (-0.130, -0.030), (-0.040, -0.010),
                    (0.000, 0.000), (0.010, 0.045), (-0.060, 0.050), (-0.150, 0.040)], 0.040, "Body",
                   bevel=0.004, seg=2, angle=30))
    p.append(box(-0.350, -0.334, -0.082, 0.048, 0.044, "Grip", bevel=0.004, seg=2))   # recoil pad
    p.append(prism([(-0.062, 0.030), (0.012, 0.030), (0.015, -0.025), (-0.020, -0.050), (-0.050, -0.040)],
                   0.036, "Grip", bevel=0.004, seg=2, angle=30))                      # wrist checkering
    # receiver
    p.append(prism([(0.000, 0.000), (0.215, 0.000), (0.215, 0.062), (0.200, 0.075), (0.020, 0.075),
                    (0.000, 0.060)], 0.038, "Metal", bevel=0.003, seg=2))
    p.append(box(0.07, 0.16, 0.035, 0.060, 0.004, "Body", y=-0.0192, bevel=0.0))      # ejection port
    p += trigger_group(0.075, 0.002, "Metal", 0.012)
    # barrel + magazine tube
    p.append(tube_x(0.0115, 0.200, 0.690, "Metal", z=0.055, sides=12))
    p.append(tube_x(0.0080, 0.684, 0.6915, "Grip", z=0.055, sides=10))
    p.append(tube_x(0.0110, 0.200, 0.600, "Metal", z=0.022, sides=12))
    p.append(tube_x(0.0125, 0.590, 0.612, "Metal", z=0.022, sides=12))                # mag cap
    p.append(box(0.585, 0.615, 0.030, 0.050, 0.010, "Metal", bevel=0.001))            # barrel clamp
    # pump forend with grooves
    p.append(lathe_x([(0.022, 0.30), (0.026, 0.31), (0.026, 0.48), (0.022, 0.49)], "Grip", z=0.026,
                     sides=12))
    for x in (0.34, 0.37, 0.40, 0.43):
        p.append(ring_x(0.0255, 0.0272, x, x + 0.008, "Body", z=0.026, sides=12))
    p.append(sphere(0.003, (0.675, 0, 0.069), "Glow", 6, 4))                          # bead sight
    p.append(box(0.20, 0.66, 0.066, 0.070, 0.008, "Metal", bevel=0.0))                # vent rib
    return finish_weapon("shotgun", p, (-0.03, -0.012))


def make_rifle():
    mats()
    p = []
    g, gc = pistol_grip((0.002, 0.040), (-0.032, 0.040), 0.105, 18, 0.030)
    p.append(g)
    # lower + upper receiver
    p.append(prism([(-0.110, 0.040), (0.145, 0.040), (0.145, 0.078), (-0.110, 0.078)], 0.030, "Body",
                   bevel=0.002))
    p.append(prism([(0.060, 0.040), (0.120, 0.040), (0.118, 0.010), (0.062, 0.010)], 0.032, "Body",
                   bevel=0.002))                                                       # mag well
    p.append(prism([(-0.115, 0.078), (0.165, 0.078), (0.165, 0.112), (-0.115, 0.112)], 0.032, "Body",
                   bevel=0.003, seg=2))
    p.append(box(0.02, 0.10, 0.083, 0.102, 0.004, "Metal", y=-0.0162, bevel=0.0))     # ejection port
    p.append(box(-0.120, -0.090, 0.103, 0.114, 0.020, "Metal", bevel=0.001))          # charging handle
    p += trigger_group(0.045, 0.041, "Body", 0.012)
    # curved magazine
    p.append(prism([(0.064, 0.012), (0.116, 0.012), (0.124, -0.050), (0.142, -0.125), (0.098, -0.138),
                    (0.082, -0.060)], 0.024, "Metal", bevel=0.002))
    for i in range(3):
        x0 = 0.090 + i * 0.012
        p.append(box(x0, x0 + 0.004, -0.10 + i * 0.03, -0.02 + i * 0.03, 0.0255, "Body", bevel=0.0))
    # stock
    p.append(prism([(-0.115, 0.110), (-0.115, 0.050), (-0.240, 0.030), (-0.330, 0.020), (-0.335, 0.116),
                    (-0.240, 0.110)], 0.032, "Body", bevel=0.003, seg=2))
    p.append(prism([(-0.230, 0.095), (-0.150, 0.090), (-0.150, 0.065), (-0.230, 0.050)], 0.034, "Grip",
                   bevel=0.002))                                                       # stock window insert
    p.append(box(-0.350, -0.333, 0.016, 0.120, 0.036, "Grip", bevel=0.003, seg=2))    # butt pad
    # handguard (octagonal) with vents and glow strip
    p.append(lathe_x([(0.026, 0.165), (0.031, 0.17), (0.031, 0.41), (0.026, 0.418)], "Grip", z=0.086,
                     sides=8))
    for x in (0.21, 0.26, 0.31, 0.36):
        p.append(box(x, x + 0.025, 0.095, 0.104, 0.064, "Body", bevel=0.0))
    p.append(box(0.20, 0.38, 0.073, 0.077, 0.064, "Glow", bevel=0.0))
    p.append(box(-0.10, 0.40, 0.112, 0.120, 0.024, "Metal", bevel=0.001))             # top rail
    p.append(tube_x(0.0095, 0.41, 0.54, "Metal", z=0.086, sides=10))                  # barrel
    p.append(box(0.43, 0.45, 0.070, 0.135, 0.016, "Metal", bevel=0.001))              # front sight post
    p.append(lathe_x([(0.012, 0.535), (0.015, 0.54), (0.015, 0.582), (0.011, 0.585)], "Metal", z=0.086,
                     sides=8))                                                         # muzzle device
    p.append(tube_x(0.006, 0.583, 0.586, "Grip", z=0.086, sides=8))
    # red-dot sight
    p.append(box(0.000, 0.060, 0.120, 0.132, 0.026, "Metal", bevel=0.001))
    p.append(lathe_x([(0.017, 0.0), (0.020, 0.004), (0.020, 0.056), (0.017, 0.06)], "Body", z=0.152,
                     sides=12, cap_start=False, cap_end=False))
    p.append(tube_x(0.0172, 0.004, 0.006, "Lens", z=0.152, sides=12))
    p.append(tube_x(0.0172, 0.052, 0.054, "Lens", z=0.152, sides=12))
    p.append(sphere(0.0018, (0.03, 0, 0.152), "Glow", 6, 4))
    return finish_weapon("rifle", p, gc)


def make_sniper():
    mats((0.16, 0.18, 0.13))
    p = []
    g, gc = pistol_grip((0.004, 0.040), (-0.030, 0.040), 0.10, 20, 0.030)
    p.append(g)
    # chassis + long stock with thumbhole look and cheek riser
    p.append(prism([(-0.040, 0.040), (0.450, 0.040), (0.455, 0.055), (0.450, 0.074), (-0.120, 0.074),
                    (-0.150, 0.060)], 0.040, "Body", bevel=0.003, seg=2))
    p.append(prism([(-0.040, 0.044), (-0.150, 0.060), (-0.420, 0.070), (-0.420, -0.060), (-0.370, -0.062),
                    (-0.250, -0.020), (-0.120, 0.000), (-0.060, 0.000)], 0.038, "Body", bevel=0.004, seg=2,
                   angle=30))
    p.append(prism([(-0.140, 0.074), (-0.140, 0.100), (-0.360, 0.104), (-0.380, 0.080), (-0.380, 0.068)], 0.030,
                   "Grip", bevel=0.004, seg=2))                                        # cheek riser
    p.append(box(-0.436, -0.418, -0.064, 0.074, 0.042, "Grip", bevel=0.004, seg=2))   # butt pad
    p.append(box(-0.38, -0.34, -0.085, -0.050, 0.012, "Metal", bevel=0.001))          # monopod
    # receiver + bolt
    p.append(tube_x(0.021, -0.100, 0.150, "Metal", z=0.090, sides=12))
    p.append(tube_y(0.006, 0.045, "Metal", x=-0.070, z=0.092, y=-0.024, sides=8))     # bolt handle (right)
    p.append(sphere(0.011, (-0.074, -0.050, 0.086), "Metal", 8, 5))
    p.append(prism([(0.04, 0.040), (0.10, 0.040), (0.098, 0.004), (0.042, 0.004)], 0.030, "Metal",
                   bevel=0.002))                                                       # magazine
    p += trigger_group(0.040, 0.041, "Metal", 0.012)
    # barrel (fluted look: 8 sides), muzzle brake
    p.append(tube_x(0.0135, 0.15, 0.760, "Metal", z=0.090, sides=8, r2=0.0100))
    p.append(prism([(0.755, 0.075), (0.810, 0.075), (0.810, 0.105), (0.755, 0.105)], 0.030, "Metal",
                   bevel=0.003, seg=1))
    for x in (0.768, 0.785):
        p.append(box(x, x + 0.008, 0.079, 0.101, 0.0305, "Grip", bevel=0.0))
    # folded bipod under the fore-end
    for sy in (0.013, -0.013):
        p.append(tube_x(0.005, 0.20, 0.43, "Metal", z=0.030, y=sy, sides=6))
        p.append(sphere(0.007, (0.20, sy, 0.030), "Grip", 6, 4))
    p.append(box(0.42, 0.45, 0.022, 0.042, 0.040, "Metal", bevel=0.002))
    # scope: tube, objective bell, eyepiece, turrets, rings, lenses
    zs = 0.150
    p.append(lathe_x([(0.022, -0.120), (0.023, -0.112), (0.023, -0.075), (0.0155, -0.055), (0.0155, 0.180),
                      (0.029, 0.235), (0.029, 0.285), (0.026, 0.290)], "Body", z=zs, sides=14,
                     cap_start=False, cap_end=False))
    p.append(tube_x(0.021, -0.116, -0.114, "Lens", z=zs, sides=14))
    p.append(tube_x(0.027, 0.282, 0.284, "Lens", z=zs, sides=14))
    p.append(tube_z(0.011, zs, zs + 0.035, "Metal", x=0.06, sides=10))               # elevation turret
    p.append(tube_y(0.011, 0.070, "Metal", x=0.06, z=zs, sides=10))                   # windage / parallax
    p.append(ring_x(0.0156, 0.0175, 0.050, 0.070, "Glow", z=zs, sides=14))            # illumination ring
    for x in (-0.03, 0.15):
        p.append(box(x - 0.012, x + 0.012, 0.106, zs - 0.012, 0.024, "Metal", bevel=0.002))
        p.append(ring_x(0.0154, 0.0195, x - 0.011, x + 0.011, "Metal", z=zs, sides=14))
    return finish_weapon("sniper", p, gc)


def make_rocket():
    mats((0.20, 0.24, 0.15))
    p = []
    zc = 0.125
    p.append(lathe_x([(0.050, -0.505), (0.060, -0.50), (0.060, -0.47), (0.054, -0.45), (0.054, 0.44),
                      (0.064, 0.46), (0.064, 0.49)], "Body", z=zc, sides=16, cap_start=False, cap_end=False))
    p.append(lathe_x([(0.045, -0.495), (0.045, 0.48)], "Grip", z=zc, sides=16, cap_start=False,
                     cap_end=False))                                                   # inner wall
    p.append(ring_x(0.045, 0.0605, -0.505, -0.495, "Metal", z=zc, sides=16))
    for x in (-0.30, -0.02, 0.30):
        p.append(ring_x(0.053, 0.059, x, x + 0.03, "Metal", z=zc, sides=16))
    # warhead sticking out of the muzzle
    p.append(lathe_x([(0.044, 0.44), (0.044, 0.50), (0.040, 0.54), (0.026, 0.585), (0.010, 0.615),
                      (0.0, 0.62)], "Metal", z=zc, sides=12, cap_start=True, cap_end=False))
    p.append(sphere(0.006, (0.618, 0, zc), "Glow", 6, 4))
    # rear pistol grip (origin) + trigger housing
    g, gc = pistol_grip((0.010, 0.065), (-0.028, 0.065), 0.105, 14, 0.032)
    p.append(g)
    p.append(prism([(-0.050, 0.064), (0.070, 0.064), (0.070, 0.085), (-0.050, 0.085)], 0.040, "Body",
                   bevel=0.003, seg=2))
    p += trigger_group(0.050, 0.065, "Body", 0.012)
    # front grip
    p.append(tube_z(0.016, 0.0, 0.075, "Grip", x=0.27, sides=10, r2=0.018))
    p.append(box(0.245, 0.295, 0.068, 0.082, 0.040, "Body", bevel=0.003))
    # shoulder pad
    p.append(box(-0.22, -0.05, zc - 0.075, zc - 0.050, 0.060, "Grip", bevel=0.006, seg=2))
    # optical sight on the left side
    p.append(box(-0.04, 0.10, zc + 0.020, zc + 0.070, 0.026, "Body", y=0.080, bevel=0.004, seg=2))
    p.append(box(-0.02, 0.06, zc + 0.000, zc + 0.030, 0.035, "Metal", y=0.060, bevel=0.002))
    p.append(tube_x(0.014, 0.100, 0.103, "Lens", z=zc + 0.045, y=0.080, sides=10))
    p.append(tube_x(0.012, -0.043, -0.040, "Lens", z=zc + 0.045, y=0.080, sides=10))
    p.append(box(0.0, 0.05, zc + 0.070, zc + 0.074, 0.010, "Glow", y=0.080, bevel=0.0))
    # flip-up iron sights on top
    p.append(box(-0.25, -0.235, zc + 0.05, zc + 0.085, 0.022, "Metal", bevel=0.001))
    p.append(box(0.36, 0.375, zc + 0.05, zc + 0.09, 0.022, "Metal", bevel=0.001))
    return finish_weapon("rocket", p, gc)


def make_minigun():
    mats((0.12, 0.12, 0.13))
    p = []
    zc = 0.105
    # 6 barrels around the axis
    for i in range(6):
        a = 2 * math.pi * i / 6 + math.pi / 6
        y, z = 0.026 * math.cos(a), zc + 0.026 * math.sin(a)
        p.append(tube_x(0.0085, 0.16, 0.88, "Metal", z=z, y=y, sides=7))
        p.append(tube_x(0.0045, 0.879, 0.882, "Grip", z=z, y=y, sides=6))
    p.append(tube_x(0.009, 0.16, 0.86, "Grip", z=zc, sides=8))                        # central spindle
    for x, r in ((0.46, 0.042), (0.84, 0.040)):
        p.append(lathe_x([(r - 0.004, x), (r, x + 0.004), (r, x + 0.020), (r - 0.004, x + 0.024)], "Metal",
                         z=zc, sides=12))                                              # barrel clamps
    # rotor housing + motor body
    p.append(lathe_x([(0.050, 0.06), (0.056, 0.07), (0.056, 0.16), (0.046, 0.175)], "Body", z=zc, sides=14))
    p.append(prism([(-0.090, 0.060), (0.075, 0.060), (0.075, 0.160), (-0.060, 0.160), (-0.090, 0.135)], 0.090,
                   "Body", bevel=0.006, seg=2))
    p.append(lathe_x([(0.030, -0.13), (0.036, -0.12), (0.036, -0.08), (0.030, -0.07)], "Metal", z=0.115,
                     sides=10))                                                        # motor cap
    for i in range(3):
        p.append(box(-0.05 + i * 0.03, -0.035 + i * 0.03, 0.075, 0.145, 0.0915, "Grip", bevel=0.0))  # vents
    for i in range(3):
        p.append(sphere(0.004, (0.04 + i * 0.012, -0.046, 0.145), "Glow", 6, 4))      # status LEDs (right)
    # rear grip (origin) + trigger, top carry handle, front handle
    g, gc = pistol_grip((0.010, 0.062), (-0.026, 0.062), 0.10, 12, 0.032)
    p.append(g)
    p += trigger_group(0.045, 0.062, "Body", 0.012)
    p.append(prism([(-0.060, 0.160), (-0.050, 0.215), (0.090, 0.215), (0.100, 0.160), (0.080, 0.160),
                    (0.074, 0.198), (-0.034, 0.198), (-0.040, 0.160)], 0.024, "Grip", bevel=0.003))
    p.append(tube_z(0.015, -0.01, zc - 0.04, "Grip", x=0.30, sides=10))
    p.append(box(0.285, 0.315, zc - 0.045, zc - 0.022, 0.032, "Metal", bevel=0.002))
    # ammo box + feed chute
    p.append(box(0.08, 0.22, -0.11, 0.00, 0.075, "Body", y=0.0, bevel=0.005, seg=2))
    p.append(box(0.10, 0.20, -0.005, 0.004, 0.06, "Metal", bevel=0.001))
    p.append(prism([(0.150, 0.000), (0.175, 0.000), (0.120, 0.065), (0.095, 0.065)], 0.040, "Metal",
                   bevel=0.002))
    return finish_weapon("minigun", p, gc)


def make_lmg():
    mats((0.10, 0.11, 0.10))
    p = []
    g, gc = pistol_grip((0.004, 0.035), (-0.030, 0.035), 0.105, 18, 0.032)
    p.append(g)
    # receiver + feed cover
    p.append(prism([(-0.105, 0.035), (0.200, 0.035), (0.200, 0.115), (-0.105, 0.115)], 0.046, "Body",
                   bevel=0.003, seg=2))
    p.append(prism([(-0.060, 0.115), (0.140, 0.115), (0.140, 0.128), (-0.050, 0.135)], 0.042, "Body",
                   bevel=0.003))
    p.append(tube_y(0.006, 0.050, "Metal", x=0.135, z=0.122, sides=8))               # cover hinge
    p.append(box(0.02, 0.12, 0.08, 0.10, 0.004, "Metal", y=-0.0232, bevel=0.0))       # ejection port
    p += trigger_group(0.040, 0.036, "Body", 0.012)
    # skeleton stock
    p.append(prism([(-0.105, 0.110), (-0.105, 0.050), (-0.360, 0.035), (-0.370, 0.115)], 0.034, "Body",
                   bevel=0.003, seg=2))
    p.append(prism([(-0.180, 0.095), (-0.300, 0.098), (-0.300, 0.060), (-0.180, 0.068)], 0.036, "Grip",
                   bevel=0.0))
    p.append(box(-0.384, -0.366, 0.028, 0.122, 0.040, "Grip", bevel=0.003, seg=2))
    # box magazine on the left + belt
    p.append(box(0.030, 0.150, -0.080, 0.030, 0.060, "Body", y=0.040, bevel=0.005, seg=2))
    p.append(box(0.040, 0.140, -0.072, 0.022, 0.004, "Glow", y=0.0715, bevel=0.0))   # round counter strip
    for i in range(4):
        x = 0.06 + i * 0.016
        p.append(tube_y(0.0055, 0.030, "Metal", x=x, z=0.040, y=0.012, sides=6))
    # handguard + heavy barrel with perforated shroud, carry handle
    p.append(prism([(0.200, 0.040), (0.380, 0.045), (0.380, 0.080), (0.200, 0.080)], 0.048, "Grip",
                   bevel=0.004, seg=2))
    p.append(tube_x(0.024, 0.200, 0.470, "Metal", z=0.092, sides=10))
    for x in (0.25, 0.29, 0.33, 0.37, 0.41):
        p.append(box(x, x + 0.018, 0.084, 0.100, 0.0495, "Grip", bevel=0.0))
    p.append(tube_x(0.012, 0.470, 0.640, "Metal", z=0.092, sides=10))
    p.append(lathe_x([(0.014, 0.630), (0.017, 0.635), (0.017, 0.672), (0.013, 0.676)], "Metal", z=0.092,
                     sides=8))
    p.append(tube_x(0.007, 0.674, 0.677, "Grip", z=0.092, sides=8))
    p.append(prism([(0.40, 0.112), (0.40, 0.150), (0.52, 0.150), (0.52, 0.112), (0.505, 0.112), (0.50, 0.138),
                    (0.42, 0.138), (0.415, 0.112)], 0.018, "Metal", bevel=0.002))  # carry handle
    for sy in (0.012, -0.012):                                                         # folded bipod
        p.append(tube_x(0.005, 0.46, 0.63, "Metal", z=0.066, y=sy, sides=6))
    p.append(box(0.62, 0.64, 0.060, 0.104, 0.034, "Metal", bevel=0.002))              # front sight block
    p.append(box(-0.09, -0.07, 0.135, 0.150, 0.024, "Metal", bevel=0.001))            # rear sight
    p.append(sphere(0.002, (-0.08, 0, 0.148), "Glow", 6, 4))
    return finish_weapon("lmg", p, gc)


def make_gl():
    mats((0.13, 0.15, 0.12))
    p = []
    g, gc = pistol_grip((0.004, 0.040), (-0.030, 0.040), 0.10, 16, 0.032)
    p.append(g)
    zc = 0.110
    # frame
    p.append(prism([(-0.060, 0.040), (0.050, 0.040), (0.050, 0.065), (0.220, 0.065), (0.220, 0.165),
                    (0.050, 0.165), (0.050, 0.150), (-0.060, 0.120)], 0.034, "Body", bevel=0.003, seg=2))
    p += trigger_group(0.040, 0.041, "Body", 0.012)
    # revolver drum (12 sides) with chamber caps
    p.append(lathe_x([(0.012, 0.055), (0.058, 0.055), (0.062, 0.062), (0.062, 0.205), (0.058, 0.212),
                      (0.012, 0.212)], "Body", z=zc, sides=12, cap_start=True, cap_end=True))
    for i in range(6):
        a = 2 * math.pi * i / 6
        y, z = 0.038 * math.cos(a), zc + 0.038 * math.sin(a)
        p.append(tube_x(0.016, 0.2105, 0.216, "Metal", z=z, y=y, sides=8))
    for i in range(6):                                                                 # drum flutes
        a = 2 * math.pi * (i + 0.5) / 6
        y, z = 0.060 * math.cos(a), zc + 0.060 * math.sin(a)
        p.append(tube_x(0.007, 0.08, 0.19, "Grip", z=z, y=y, sides=6))
    # fat barrel + muzzle
    p.append(tube_x(0.027, 0.215, 0.440, "Metal", z=zc + 0.012, sides=12))
    p.append(ring_x(0.021, 0.031, 0.425, 0.452, "Metal", z=zc + 0.012, sides=12))
    p.append(tube_x(0.021, 0.444, 0.446, "Grip", z=zc + 0.012, sides=12))
    p.append(box(0.215, 0.43, zc + 0.036, zc + 0.052, 0.020, "Body", bevel=0.002))    # top strap / rail
    # vertical foregrip
    p.append(tube_z(0.015, zc - 0.10, zc - 0.015, "Grip", x=0.33, sides=10))
    p.append(box(0.31, 0.35, zc - 0.03, zc - 0.012, 0.030, "Body", bevel=0.002))
    # folding tubular stock (Body) + pad
    for dz in (0.055, 0.115):
        p.append(tube_x(0.007, -0.300, -0.055, "Body", z=dz, sides=8))
    p.append(box(-0.318, -0.296, 0.030, 0.135, 0.040, "Grip", bevel=0.004, seg=2))
    p.append(box(-0.075, -0.050, 0.045, 0.125, 0.030, "Metal", bevel=0.002))          # hinge
    # reflex sight
    p.append(box(0.07, 0.15, zc + 0.054, zc + 0.062, 0.026, "Metal", bevel=0.001))
    p.append(prism([(0.08, zc + 0.062), (0.14, zc + 0.062), (0.14, zc + 0.100), (0.08, zc + 0.090)], 0.004,
                   "Lens", y=0.0, bevel=0.0))
    p.append(box(0.135, 0.145, zc + 0.062, zc + 0.104, 0.030, "Body", bevel=0.001))
    p.append(sphere(0.0025, (0.11, 0, zc + 0.080), "Glow", 6, 4))
    return finish_weapon("gl", p, gc)


def make_rail():
    mats((0.82, 0.84, 0.88))
    p = []
    g, gc = pistol_grip((0.004, 0.035), (-0.030, 0.035), 0.105, 16, 0.032)
    p.append(g)
    zc = 0.100
    # core body: sculpted side profile, wider in the middle
    p.append(prism([(-0.110, 0.035), (0.260, 0.035), (0.300, 0.065), (0.300, 0.140), (0.250, 0.160),
                    (-0.060, 0.160), (-0.110, 0.130)], 0.060, "Body", bevel=0.006, seg=2))
    p.append(box(-0.05, 0.22, 0.06, 0.135, 0.004, "Grip", y=0.031, bevel=0.0))        # side panels
    p.append(box(-0.05, 0.22, 0.06, 0.135, 0.004, "Grip", y=-0.031, bevel=0.0))
    p.append(box(-0.04, 0.21, 0.094, 0.100, 0.0045, "Glow", y=0.0322, bevel=0.0))     # side glow lines
    p.append(box(-0.04, 0.21, 0.094, 0.100, 0.0045, "Glow", y=-0.0322, bevel=0.0))
    p += trigger_group(0.040, 0.036, "Body", 0.012)
    # stock: open frame
    p.append(prism([(-0.110, 0.150), (-0.110, 0.045), (-0.360, 0.040), (-0.380, 0.060), (-0.380, 0.140),
                    (-0.350, 0.150), (-0.300, 0.150), (-0.300, 0.075), (-0.150, 0.080), (-0.150, 0.150)],
                   0.036, "Body", bevel=0.004, seg=2))
    p.append(box(-0.392, -0.376, 0.036, 0.152, 0.040, "Grip", bevel=0.004, seg=2))
    # twin rails with an energy channel and coils
    for dz in (-0.028, 0.028):
        p.append(prism([(0.290, zc + dz - 0.010), (0.610, zc + dz - 0.007), (0.625, zc + dz),
                        (0.610, zc + dz + 0.007), (0.290, zc + dz + 0.010)], 0.022, "Metal", bevel=0.002))
    p.append(box(0.295, 0.600, zc - 0.006, zc + 0.006, 0.006, "Glow", bevel=0.0))
    for x in (0.34, 0.43, 0.52):
        p.append(lathe_x([(0.040, x), (0.046, x + 0.006), (0.046, x + 0.020), (0.040, x + 0.026)], "Glow",
                         z=zc, sides=12, cap_start=False, cap_end=False))
        p.append(lathe_x([(0.039, x - 0.003), (0.039, x + 0.029)], "Body", z=zc, sides=12, cap_start=False,
                         cap_end=False))
    # capacitor cells under the barrel
    for sy in (0.016, -0.016):
        p.append(tube_x(0.012, 0.29, 0.48, "Body", z=0.045, y=sy, sides=8))
        p.append(tube_x(0.008, 0.48, 0.49, "Glow", z=0.045, y=sy, sides=8))
    # scope
    zs = 0.195
    p.append(box(0.02, 0.18, 0.158, 0.175, 0.024, "Metal", bevel=0.002))
    p.append(lathe_x([(0.020, -0.03), (0.022, -0.02), (0.016, 0.02), (0.016, 0.17), (0.024, 0.21),
                      (0.022, 0.22)], "Body", z=zs, sides=12, cap_start=False, cap_end=False))
    p.append(tube_x(0.019, -0.027, -0.025, "Lens", z=zs, sides=12))
    p.append(tube_x(0.021, 0.212, 0.214, "Lens", z=zs, sides=12))
    p.append(ring_x(0.0162, 0.018, 0.08, 0.095, "Glow", z=zs, sides=12))
    return finish_weapon("rail", p, gc)


WEAPONS = {
    "pistol": make_pistol, "uzi": make_uzi, "shotgun": make_shotgun, "rifle": make_rifle,
    "sniper": make_sniper, "rocket": make_rocket, "minigun": make_minigun, "lmg": make_lmg,
    "gl": make_gl, "rail": make_rail,
}


def build(name):
    nb.reset_scene()
    obj = WEAPONS[name]()
    used = {obj.data.materials[p.material_index].name for p in obj.data.polygons}
    lo = [min(v.co[i] for v in obj.data.vertices) for i in range(3)]
    hi = [max(v.co[i] for v in obj.data.vertices) for i in range(3)]
    print("[weapon] %s: %d tris, length %.3f m (x %.3f..%.3f), height %.3f, width %.3f, mats %s" % (
        name, nb.tri_count(obj), hi[0] - lo[0], lo[0], hi[0], hi[2] - lo[2], hi[1] - lo[1], sorted(used)))
    return nb.export_glb("w_" + name)


if __name__ == "__main__":
    for n in sys.argv[1:] or list(WEAPONS):
        build(n)
