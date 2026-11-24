"""Neon Bay - procedural firearms, version 3 ("showcase" detail; original, generic designs:
no real model reproduced, no brand, no marking).

    python3 tools/blender/gen_weapons.py               # every weapon
    python3 tools/blender/gen_weapons.py pistol rail   # some weapons
    nice -n 5 python3 ...                              # when the machine is busy

Outputs models/w_<id>.glb (+ .glb.js) for:
    pistol uzi shotgun rifle sniper rocket minigun lmg gl rail

Contract (glTF, export_yup): 1 unit = 1 m, barrel/muzzle towards +X, up +Y, the right side
of the weapon is +Z. Origin = centre of the main grip, where the right hand closes (for the
rocket launcher / minigun: the rear pistol grip). The overall lengths and the grip centres
are the ones of version 2 (same make_* layouts), so setHeroGun / the studio need no change.
One mesh, no animation. Budgets: pistol <= 4000 tris, rifles <= 9000, heavy weapons
(rocket, minigun, lmg, gl) <= 12000, every file <= 600 KB.

Materials (names are the contract; the game recolours every material whose name contains
"body" with the weapon skin, and treats names containing "metal" as metal):
    Body       main finish (Cerakote / anodised), recoloured for skins; fine grain normal map
    Metal      blued / parkerised steel (barrels, slides inner parts, pins, rails); brushed map
    MetalEdge  worn bare steel on the chamfers of steel parts (edge wear, catches the light)
    Polymer    matte textured polymer (frames, stocks, magazines); stipple colour + normal map
    Grip       rubber with diamond checkering (normal map)
    Glow       emissive: tritium dots, red-dot reticles, LEDs, rail coils (small accents)
    Lens       tinted, faintly emissive coated glass (optics) on rifle, sniper, rocket, gl, rail

Textures (nb_textures.weapon_textures, 256 px, tiling) are box-projected at world scale
(WEAPON_TILE), so UVs are exported; Phong quality levels simply ignore the maps.

Blender side (Z-up): X forward, Z up, Y = left side of the weapon (right side = -Y).
Building blocks: side profiles extruded across Y (prism), sections extruded along X (xsec),
lathes / tubes / rings along X, boolean cuts (EXACT solver, applied without bpy.ops) for
serrations, ports, vents and lightening cuts, then a Bevel modifier whose new faces can get
the MetalEdge material. Detail kits: picatinny(), screw(), pin_y(), sling_loop(),
trigger_group(), pistol_grip(), muzzle_brake(), slotted_handguard(), red_dot(), scope().
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402,F401
import bmesh  # noqa: E402
from mathutils import Vector, Matrix  # noqa: E402

import nb_common as nb  # noqa: E402
import nb_textures as nbt  # noqa: E402

M = {}
TEX = {}
WEAPON_TILE = {"Body": 0.06, "Polymer": 0.05, "Grip": 0.032, "Metal": 0.10, "MetalEdge": 0.10}
BUDGET = {"pistol": 4000, "uzi": 9000, "shotgun": 9000, "rifle": 9000, "sniper": 9000, "rail": 9000,
          "rocket": 12000, "minigun": 12000, "lmg": 12000, "gl": 12000}


# --------------------------------------------------------------------------- materials
def tex_mat(name, color, metallic, roughness, img=None, normal=None, nstrength=1.0, **kw):
    mat = nb.material(name, color, metallic=metallic, roughness=roughness, **kw)
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    if img:
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


def mats(body=(0.075, 0.078, 0.085), body_metal=0.3, body_rough=0.48, glow=(0.25, 0.95, 1.0)):
    t = TEX
    M["Body"] = tex_mat("Body", body, body_metal, body_rough, normal=t["poly_n"], nstrength=0.25)
    M["Metal"] = tex_mat("Metal", (0.105, 0.11, 0.118), 0.95, 0.36, img=t["steel"])
    M["MetalEdge"] = tex_mat("MetalEdge", (0.50, 0.50, 0.52), 1.0, 0.26, img=t["steel"])
    M["Polymer"] = tex_mat("Polymer", (0.046, 0.047, 0.05), 0.0, 0.78, img=t["poly"], normal=t["poly_n"])
    M["Grip"] = tex_mat("Grip", (0.034, 0.034, 0.037), 0.0, 0.9, normal=t["checker_n"], nstrength=0.9)
    M["Glow"] = nb.material("Glow", glow, emission=glow, strength=4.0, roughness=0.4)
    M["Lens"] = nb.material("Lens", (0.02, 0.05, 0.075), metallic=0.4, roughness=0.04,
                            emission=(0.10, 0.24, 0.36), strength=0.55)


# --------------------------------------------------------------------------- primitives
def _clean(obj, tri=True):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if tri:
        ngons = [f for f in bm.faces if len(f.verts) > 4]
        if ngons:
            bmesh.ops.triangulate(bm, faces=ngons, quad_method="BEAUTY", ngon_method="BEAUTY")
    bm.to_mesh(obj.data)
    bm.free()


def bevel(obj, width, seg=1, angle=35, edge=None):
    """Chamfer the sharp edges; edge=True gives the new faces the MetalEdge material."""
    if width <= 0:
        return obj
    m = nb.add_bevel(obj, width, seg, angle)
    m.miter_outer = "MITER_ARC" if seg > 1 else "MITER_SHARP"
    if edge:
        if M["MetalEdge"].name not in [mm.name for mm in obj.data.materials]:
            obj.data.materials.append(M["MetalEdge"])
        m.material = [mm.name for mm in obj.data.materials].index("MetalEdge")
    nb.apply_modifiers(obj)
    return obj


def _edge_default(mat, edge):
    return (mat == "Metal") if edge is None else edge


def _finish(obj, bv, seg, angle, edge, mat):
    _clean(obj, tri=False)
    return bevel(obj, bv, seg, angle, _edge_default(mat, edge))


def prism(pts, w, mat, y=0.0, bv=0.0015, seg=1, angle=35, edge=None):
    """Side profile [(x, z), ...] extruded across Y (thickness w, centred on y)."""
    n = len(pts)
    y0, y1 = y - w / 2, y + w / 2
    verts = [(x, y0, z) for x, z in pts] + [(x, y1, z) for x, z in pts]
    faces = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
    faces += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return _finish(nb.mesh_object("prism", verts, faces, [M[mat]]), bv, seg, angle, edge, mat)


def top_prism(pts, h, mat, z=0.0, bv=0.0015, seg=1, angle=35, edge=None):
    """Top-view profile [(x, y), ...] extruded along Z (height h, centred on z)."""
    n = len(pts)
    verts = [(x, y, z - h / 2) for x, y in pts] + [(x, y, z + h / 2) for x, y in pts]
    faces = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
    faces += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return _finish(nb.mesh_object("tprism", verts, faces, [M[mat]]), bv, seg, angle, edge, mat)


def xsec(sec, x0, x1, mat, bv=0.0012, seg=1, angle=35, edge=None, scale1=1.0, dz1=0.0):
    """Cross-section [(y, z), ...] extruded along X from x0 to x1 (optionally tapered)."""
    n = len(sec)
    verts = [(x0, y, z) for y, z in sec] + [(x1, y * scale1, z * scale1 + dz1) for y, z in sec]
    faces = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
    faces += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return _finish(nb.mesh_object("xsec", verts, faces, [M[mat]]), bv, seg, angle, edge, mat)


def box(x0, x1, z0, z1, w, mat, y=0.0, bv=0.0012, seg=1, edge=None):
    return prism([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], w, mat, y, bv, seg, edge=edge)


def rbox(x0, x1, y0, y1, z0, z1, mat, bv=0.0012, seg=1, edge=None):
    """Axis-aligned box from extents (all three axes)."""
    return box(x0, x1, z0, z1, y1 - y0, mat, (y0 + y1) / 2, bv, seg, edge)


def tube_x(r, x0, x1, mat, z=0.0, y=0.0, sides=12, r2=None, bv=0.0, seg=1, edge=None, rot0=0.0):
    o = nb.cylinder("cyl", r, x1 - x0, ((x0 + x1) / 2, y, z), sides, M[mat], axis="X", r2=r2)
    if rot0:
        rot(o, rot0, "X", ((x0 + x1) / 2, y, z))
    return _finish(o, bv, seg, 35, edge, mat)


def tube_z(r, z0, z1, mat, x=0.0, y=0.0, sides=10, r2=None, bv=0.0, edge=None):
    o = nb.cylinder("cyl", r, z1 - z0, (x, y, (z0 + z1) / 2), sides, M[mat], axis="Z", r2=r2)
    return _finish(o, bv, 1, 35, edge, mat)


def tube_y(r, w, mat, x=0.0, z=0.0, y=0.0, sides=10, bv=0.0, edge=None):
    o = nb.cylinder("cyl", r, w, (x, y, z), sides, M[mat], axis="Y")
    return _finish(o, bv, 1, 35, edge, mat)


def lathe_x(profile, mat, z=0.0, y=0.0, sides=12, cap_start=True, cap_end=True, bv=0.0, seg=1,
            edge=None, rot0=0.0):
    """Revolve [(radius, x), ...] around an axis parallel to X (rot0: phase, degrees)."""
    v, f = nb.lathe(profile, sides, axis="X", cap_start=cap_start, cap_end=cap_end)
    if rot0:
        c, s = math.cos(math.radians(rot0)), math.sin(math.radians(rot0))
        v = [(a, b * c - d * s, b * s + d * c) for a, b, d in v]
    v = [(a, b + y, d + z) for a, b, d in v]
    return _finish(nb.mesh_object("lathe", v, f, [M[mat]]), bv, seg, 35, edge, mat)


def ring_x(r_in, r_out, x0, x1, mat, z=0.0, y=0.0, sides=12, bv=0.0, edge=None, rot0=0.0):
    """Thick ring (washer / hollow tube) along X."""
    prof = [(r_in, x0), (r_out, x0), (r_out, x1), (r_in, x1), (r_in, x0)]
    return lathe_x(prof, mat, z, y, sides, False, False, bv=bv, edge=edge, rot0=rot0)


def sphere(r, loc, mat, seg=8, rings=5, scale=(1, 1, 1)):
    return nb.uv_sphere("sph", r, loc, seg, rings, M[mat], scale)


def torus_y(R, r, loc, mat, seg=12, rseg=6):
    """Ring lying in the XZ plane (axis Y): sling loops, hammer rings."""
    prof = [(R + r * math.cos(2 * math.pi * i / rseg), r * math.sin(2 * math.pi * i / rseg))
            for i in range(rseg + 1)]
    v, f = nb.lathe(prof, seg, axis="Y")
    v = [(a + loc[0], b + loc[1], c + loc[2]) for a, b, c in v]
    o = nb.mesh_object("torus", v, f, [M[mat]])
    _clean(o, tri=False)
    return o


def rot(obj, deg, axis="Y", pivot=(0, 0, 0)):
    """Rotate an object's mesh around a pivot (degrees, Blender axes)."""
    R = Matrix.Rotation(math.radians(deg), 4, axis)
    T = Matrix.Translation(Vector(pivot))
    obj.data.transform(T @ R @ T.inverted())
    return obj


def move(obj, d):
    obj.data.transform(Matrix.Translation(Vector(d)))
    return obj


def cutter(x0, x1, y0, y1, z0, z1):
    o = nb.box("cut", (x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    return o


def cutter_prism(pts, y0, y1):
    n = len(pts)
    verts = [(x, y0, z) for x, z in pts] + [(x, y1, z) for x, z in pts]
    faces = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
    faces += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    o = nb.mesh_object("cutp", verts, faces)
    _clean(o, tri=False)
    return o


def cutter_cyl(r, axis, loc, length, sides=12):
    o = nb.cylinder("cutc", r, length, loc, sides, None, axis=axis)
    return o


def slot_cutter(x0, x1, z, h, y0, y1, sides=8):
    """Rounded slot (stadium) through Y: x0..x1 long, h high, centred at z (a slot taller
    than long gets its round ends at the top and bottom instead)."""
    L = x1 - x0
    pts = []
    if L >= h:
        r = h / 2
        for i in range(sides + 1):
            a = -math.pi / 2 + math.pi * i / sides
            pts.append((x1 - r + r * math.cos(a), z + r * math.sin(a)))
        for i in range(sides + 1):
            a = math.pi / 2 + math.pi * i / sides
            pts.append((x0 + r + r * math.cos(a), z + r * math.sin(a)))
    else:
        r, xc = L / 2, (x0 + x1) / 2
        for i in range(sides + 1):
            a = math.pi * i / sides
            pts.append((xc + r * math.cos(a), z + h / 2 - r + r * math.sin(a)))
        for i in range(sides + 1):
            a = math.pi + math.pi * i / sides
            pts.append((xc + r * math.cos(a), z - h / 2 + r + r * math.sin(a)))
    clean = []
    for q in pts:
        if not clean or abs(clean[-1][0] - q[0]) + abs(clean[-1][1] - q[1]) > 1e-7:
            clean.append(q)
    if abs(clean[0][0] - clean[-1][0]) + abs(clean[0][1] - clean[-1][1]) < 1e-7:
        clean.pop()
    return cutter_prism(clean, y0, y1)


def cut(obj, cutters, bv=0.0, seg=1, angle=35, edge=None, mat=None, pre=None):
    """Boolean difference (EXACT) of all cutters, then optional bevel. pre=(width, seg):
    bevel the outer shape before cutting instead (much lighter: the cut edges stay sharp)."""
    if mat is None:
        mat = obj.data.materials[0].name if obj.data.materials else ""
    if pre:
        bevel(obj, pre[0], pre[1], angle, _edge_default(mat, edge))
    if cutters:
        tool = nb.join(cutters, "cutters") if len(cutters) > 1 else cutters[0]
        for mm in obj.data.materials:
            tool.data.materials.append(mm)
        mod = obj.modifiers.new("cut", "BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.solver = "EXACT"
        mod.object = tool
        mod.material_mode = "INDEX"
        mod.use_self = len(cutters) > 1          # cutters may overlap each other
        nb.apply_modifiers(obj)
        me = tool.data
        bpy.data.objects.remove(tool)
        bpy.data.meshes.remove(me)
        _clean(obj, tri=False)
    return bevel(obj, bv, seg, angle, _edge_default(mat, edge))


# --------------------------------------------------------------------------- detail kits
def picatinny(x0, x1, z, mat="Metal", w=0.021, pitch=0.0100, y=0.0, base_h=0.0035, tooth_h=0.0030):
    """Accessory rail on top of z (or below if tooth_h < 0): dovetail base + regular teeth."""
    s = 1 if tooth_h > 0 else -1
    th = abs(tooth_h)
    hw, bw = w / 2, w / 2 - 0.0025
    base = xsec([(y - bw, z), (y + bw, z), (y + bw, z + s * base_h), (y - bw, z + s * base_h)],
                x0, x1, mat, bv=0.0006, edge=False)
    out = [base]
    zt0 = z + s * base_h
    sec = [(y - bw, zt0), (y + bw, zt0), (y + hw, zt0 + s * th * 0.45), (y + hw - 0.0018, zt0 + s * th),
           (y - hw + 0.0018, zt0 + s * th), (y - hw, zt0 + s * th * 0.45)]
    n = int((x1 - x0 - 0.002) / pitch)
    off = x0 + (x1 - x0 - n * pitch) / 2
    tw = pitch * 0.47
    for i in range(n):
        xa = off + i * pitch + (pitch - tw) / 2
        out.append(xsec(sec, xa, xa + tw, mat, bv=0.0, edge=False))
    return out


def screw(x, z, y_face, r=0.0028, side=1, mat="Metal", h=0.0012, sides=10):
    """Socket-head screw on a side face at y=y_face, facing +Y (side=1) or -Y (side=-1)."""
    head = tube_y(r, h, mat, x=x, z=z, y=y_face + side * h / 2, sides=min(sides, 8), bv=0.0)
    sock = tube_y(r * 0.45, h * 0.4, "Polymer", x=x, z=z, y=y_face + side * (h + 0.0001), sides=6)
    return [head, sock]


def screw_z(x, y, z_face, r=0.0026, mat="Metal", h=0.0012, sides=10):
    head = tube_z(r, z_face, z_face + h, mat, x=x, y=y, sides=min(sides, 8), bv=0.0)
    sock = tube_z(r * 0.45, z_face + h - 0.0003, z_face + h + 0.0002, "Polymer", x=x, y=y, sides=6)
    return [head, sock]


def pin_y(x, z, w, r=0.0016, mat="Metal"):
    """Cross pin visible on both sides."""
    return tube_y(r, w + 0.0012, mat, x=x, z=z, sides=8, edge=False)


def sling_loop(x, z, y=0.0, R=0.0065, r=0.0014, axis="Y", mat="Metal"):
    """Sling ring + its mount block: ring in the XZ plane (axis Y) or the XY plane (axis Z)."""
    o = torus_y(R, r, (0, 0, 0), mat, 12, 5)
    if axis == "Z":
        rot(o, 90, "X")
    move(o, (x, y, z))
    return o


def knurl_ring(r, x0, x1, mat, z=0.0, y=0.0, teeth=16, depth=0.0008):
    """Knurled knob along X: star-shaped section (alternating radius)."""
    sec = []
    for i in range(teeth * 2):
        a = 2 * math.pi * i / (teeth * 2)
        rr = r if i % 2 == 0 else r - depth
        sec.append((y + rr * math.cos(a), z + rr * math.sin(a)))
    return xsec(sec, x0, x1, mat, bv=0.0, edge=False)


def knurl_z(r, z0, z1, mat, x=0.0, y=0.0, teeth=16, depth=0.0008):
    """Knurled knob along Z (turret caps)."""
    pts = []
    for i in range(teeth * 2):
        a = 2 * math.pi * i / (teeth * 2)
        rr = r if i % 2 == 0 else r - depth
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    return top_prism(pts, z1 - z0, mat, z=(z0 + z1) / 2, bv=0.0)


def knurl_y(r, w, mat, x=0.0, z=0.0, y=0.0, teeth=16, depth=0.0008):
    o = knurl_z(r, -w / 2, w / 2, mat, teeth=teeth, depth=depth)
    rot(o, 90, "X")
    return move(o, (x, y, z))


def trigger_group(x, z, mat_guard="Polymer", w=0.011, size=1.0, square=True):
    """Trigger guard (U loop, squared front with a finger ridge) + curved trigger with a
    safety blade; front of the guard at x, top at z."""
    s = size
    if square:
        outer = [(x - 0.052 * s, z), (x - 0.049 * s, z - 0.030 * s), (x - 0.040 * s, z - 0.036 * s),
                 (x - 0.002 * s, z - 0.036 * s), (x + 0.006 * s, z - 0.030 * s), (x + 0.007 * s, z - 0.020 * s),
                 (x + 0.004 * s, z)]
        inner = [(x - 0.004 * s, z), (x - 0.002 * s, z - 0.022 * s), (x - 0.006 * s, z - 0.027 * s),
                 (x - 0.038 * s, z - 0.027 * s), (x - 0.042 * s, z - 0.023 * s), (x - 0.044 * s, z)]
    else:
        outer = [(x - 0.050 * s, z), (x - 0.046 * s, z - 0.032 * s), (x - 0.004 * s, z - 0.034 * s),
                 (x + 0.004 * s, z - 0.004 * s), (x + 0.004 * s, z)]
        inner = [(x - 0.003 * s, z), (x - 0.006 * s, z - 0.026 * s), (x - 0.040 * s, z - 0.025 * s),
                 (x - 0.043 * s, z)]
    guard = prism(outer + inner, w, mat_guard, bv=0.0014, seg=1, edge=mat_guard == "Metal")
    # curved trigger blade: arc of points, thicker at the top
    blade = []
    for i in range(6):
        t = i / 5
        a = math.radians(-10 + 60 * t)
        blade.append((x - 0.024 * s - 0.016 * s * math.sin(a) * 0.6 + 0.004 * s * t, z - 0.022 * s * t))
    back = [(px - (0.0068 - 0.0022 * (j / 5)) * s, pz) for j, (px, pz) in enumerate(blade)]
    trig = prism(blade + back[::-1], 0.0058, "Metal", bv=0.0008, seg=1, edge=True)
    safety = prism([(x - 0.0255 * s, z - 0.003 * s), (x - 0.0235 * s, z - 0.003 * s),
                    (x - 0.0262 * s, z - 0.016 * s), (x - 0.0278 * s, z - 0.015 * s)], 0.0022, "Polymer", bv=0.0)
    pin = pin_y(x - 0.030 * s, z + 0.004 * s, w + 0.002, 0.0013)
    return [guard, trig, safety, pin]


def pistol_grip(top_front, top_back, length, angle, w, mat="Polymer", flare=0.004, beaver=0.010,
                panel=True, grooves=True):
    """Slanted pistol grip, same centre as v2: top edge from top_back to top_front (x, z),
    tilted back by angle. Front strap with finger grooves, palm swell, beavertail, flared
    base; checkered rubber side panels (Grip). Returns (parts, centre (x, z), info)."""
    a = math.radians(angle)
    d = Vector((-math.sin(a), -math.cos(a)))
    nrm = Vector((math.cos(a), -math.sin(a)))          # towards the front, perpendicular to d
    tf, tb = Vector(top_front), Vector(top_back)
    bf, bb = tf + d * length, tb + d * (length + 0.004)
    centre = (tf + tb) / 2 + d * (length * 0.5)
    front = []
    for i in range(1, 16):
        t = i / 16
        bump = 0.0
        if grooves:
            tt = max(0.0, (t - 0.16) / 0.80)
            bump = 0.0032 * abs(math.sin(min(tt, 1.0) * math.pi * 3.0))
        front.append(tf + d * (length * t) + nrm * (0.003 * math.sin(t * math.pi) + bump))
    back = []
    for i in range(10, 0, -1):
        t = i / 11
        swell = 0.004 * math.sin(t * math.pi) ** 1.5
        back.append(tb + d * ((length + 0.004) * t) - nrm * swell)
    bbf = bb + Vector((-flare, 0))
    pts = [tb, tf] + front + [bf + nrm * 0.002, bf + d * 0.002 + nrm * 0.001, bbf + d * 0.002, bbf] + back
    pts = [tuple(p) for p in pts]
    parts = [prism(pts, w, mat, bv=0.0028, seg=2, angle=40)]
    if panel:
        inset = []
        for i in range(0, 9):
            t = 0.12 + 0.78 * i / 8
            inset.append(tf + d * (length * t) - nrm * 0.0055)
        for i in range(8, -1, -1):
            t = 0.12 + 0.78 * i / 8
            inset.append(tb + d * ((length + 0.004) * t) + nrm * 0.0040)
        pan = [tuple(p) for p in inset]
        parts.append(prism(pan, w + 0.0016, "Grip", bv=0.0008, seg=1, angle=30))
    info = {"bottom": (tuple(bf), tuple(bbf), tuple(d)), "d": d, "nrm": nrm, "tf": tf, "tb": tb}
    return parts, (centre.x, centre.y), info


def muzzle_brake(x0, x1, r, z, mat="Metal", ports=3, sides=16, y=0.0, top_ports=True):
    """Cylindrical brake with side ports (through cuts), crown and bore."""
    body = lathe_x([(r * 0.82, x0), (r, x0 + 0.003), (r, x1 - 0.003), (r * 0.86, x1)], mat, z=z, y=y,
                   sides=sides)
    cs = []
    L = x1 - x0
    pw = L * 0.6 / ports
    for i in range(ports):
        xa = x0 + L * 0.18 + i * (L * 0.72 / ports)
        cs.append(slot_cutter(xa, xa + pw, z, r * 1.05, y - r * 2, y + r * 2, 4))
        if top_ports and i < ports - 1:
            cs.append(cutter(xa + pw * 0.2, xa + pw * 0.8, y - r * 0.25, y + r * 0.25, z + r * 0.4, z + r * 1.5))
    body = cut(body, cs, bv=0.0006, edge=True, mat=mat)
    bore = tube_x(r * 0.42, x1 - 0.0015, x1 + 0.0004, "Polymer", z=z, y=y, sides=10)
    return [body, bore]


def slotted_handguard(x0, x1, r, z, mat="Body", slots=4, sides=8, rows=(0.0,), slot_h=0.009, y=0.0,
                      inner=0.8, bottom_slots=True):
    """Hollow polygonal handguard (rotated so a flat is on top) with through slots on the
    sides (and the bottom): the barrel shows through."""
    o = ring_x(r * inner, r, x0, x1, mat, z=z, y=y, sides=sides, rot0=180.0 / sides)
    cs = []
    L = x1 - x0
    sl = L / (slots * 1.6 + 0.6)
    for dz in rows:
        for i in range(slots):
            xa = x0 + sl * (0.6 + i * 1.6)
            cs.append(slot_cutter(xa, xa + sl, z + dz, slot_h, y - r * 1.2, y + r * 1.2, 3))
    if bottom_slots:
        for i in range(slots - 1):
            xa = x0 + sl * (1.4 + i * 1.6)
            c = slot_cutter(xa, xa + sl, 0.0, slot_h * 0.9, -r * 0.4, r * 0.4, 3)
            rot(c, 90, "X")
            move(c, (0, y, z - r))
            cs.append(c)
    return cut(o, cs, edge=False, mat=mat, pre=(0.0009, 1))


def red_dot(x0, x1, zb, mat="Body", r=0.017, y=0.0):
    """Tube reflex sight on a mount: base + clamp screws, housing, tinted lenses, reticle,
    turret caps."""
    L = x1 - x0
    zc = zb + 0.012 + r
    p = []
    p.append(rbox(x0 + 0.004, x1 - 0.004, y - 0.011, y + 0.011, zb, zb + 0.008, "Metal", bv=0.0008))
    p.append(prism([(x0 + 0.010, zb + 0.007), (x1 - 0.010, zb + 0.007), (x1 - 0.016, zc - r * 0.6),
                    (x0 + 0.016, zc - r * 0.6)], 0.014, "Metal", y=y, bv=0.0008))
    p += screw(x0 + 0.010, zb + 0.004, y - 0.011, 0.0022, -1)
    p += screw(x1 - 0.010, zb + 0.004, y - 0.011, 0.0022, -1)
    p.append(lathe_x([(r - 0.002, x0), (r + 0.0015, x0 + 0.002), (r + 0.0015, x0 + L * 0.18), (r, x0 + L * 0.22),
                      (r, x1 - L * 0.22), (r + 0.002, x1 - L * 0.16), (r + 0.002, x1 - 0.002), (r - 0.0015, x1),
                      (r - 0.0022, x1), (r - 0.0022, x0)], mat, z=zc, y=y, sides=14, cap_start=False,
                     cap_end=False, edge=False))
    p.append(tube_x(r - 0.0022, x0 + 0.0015, x0 + 0.0025, "Lens", z=zc, y=y, sides=14))
    p.append(tube_x(r - 0.0022, x1 - 0.0035, x1 - 0.0025, "Lens", z=zc, y=y, sides=14))
    p.append(sphere(0.0014, (x0 + L * 0.55, y, zc), "Glow", 6, 4))
    # turret caps: elevation on top, windage on the right
    xm = x0 + L * 0.5
    p.append(knurl_z(0.0062, zc + r - 0.002, zc + r + 0.0062, "Metal", x=xm, y=y, teeth=12, depth=0.0006))
    p.append(knurl_y(0.0062, 0.0082, "Metal", x=xm, z=zc, y=y - r - 0.002, teeth=12, depth=0.0006))
    return p, zc


def scope(x0, x1, zc, r_tube=0.0155, r_obj=0.029, r_eye=0.022, mat="Body", y=0.0, glow_ring=True,
          sides=16, sunshade=0.0):
    """Riflescope: eyepiece with focus ring, tube, turret saddle with knurled turrets and a
    parallax knob, objective bell, sunshade, tinted lenses, illumination ring."""
    L = x1 - x0
    xe1 = x0 + L * 0.17
    xs0, xs1 = x0 + L * 0.40, x0 + L * 0.58
    xo0 = x1 - L * 0.22 - sunshade
    prof = [(r_eye - 0.002, x0), (r_eye, x0 + 0.004), (r_eye, xe1 - 0.012), (r_eye - 0.0015, xe1 - 0.008),
            (r_eye - 0.0015, xe1), (r_tube + 0.002, xe1 + 0.018), (r_tube, xe1 + 0.026),
            (r_tube, xo0), (r_obj, xo0 + L * 0.13), (r_obj, x1 - 0.004 - sunshade), (r_obj - 0.0015, x1 - sunshade)]
    if sunshade:
        prof += [(r_obj - 0.0008, x1 - sunshade + 0.002), (r_obj - 0.0008, x1)]
    prof += [(r_obj - 0.0035, x1), (r_obj - 0.0035, x1 - sunshade - 0.004)]
    p = [lathe_x(prof, mat, z=zc, y=y, sides=sides, cap_start=False, cap_end=False, edge=False)]
    p.append(tube_x(r_eye - 0.0028, x0 + 0.003, x0 + 0.004, "Lens", z=zc, y=y, sides=sides))
    p.append(tube_x(r_eye - 0.002, x0, x0 + 0.003, "Polymer", z=zc, y=y, sides=sides))
    p.append(knurl_ring(r_eye + 0.0006, x0 + 0.010, xe1 - 0.014, "Polymer", z=zc, y=y, teeth=20, depth=0.0009))
    p.append(tube_x(r_obj - 0.0035, x1 - sunshade - 0.006, x1 - sunshade - 0.005, "Lens", z=zc, y=y, sides=sides))
    # turret saddle
    p.append(lathe_x([(r_tube + 0.002, xs0), (r_tube + 0.0045, xs0 + 0.006), (r_tube + 0.0045, xs1 - 0.006),
                      (r_tube + 0.002, xs1)], mat, z=zc, y=y, sides=sides, edge=False))
    xm = (xs0 + xs1) / 2
    tr = (xs1 - xs0) * 0.33
    p.append(tube_z(tr, zc + r_tube, zc + r_tube + 0.012, mat, x=xm, y=y, sides=16, bv=0.0005, edge=True))
    p.append(knurl_z(tr + 0.001, zc + r_tube + 0.012, zc + r_tube + 0.022, "Metal", x=xm, y=y, teeth=18))
    p.append(tube_z(tr * 0.6, zc + r_tube + 0.022, zc + r_tube + 0.024, "MetalEdge", x=xm, y=y, sides=12))
    # windage on the right (-Y)
    p.append(knurl_y(tr + 0.001, 0.010, "Metal", x=xm, z=zc, y=y - r_tube - 0.012, teeth=18))
    p.append(tube_y(tr, 0.012, mat, x=xm, z=zc, y=y - r_tube - 0.003, sides=16))
    # parallax / illumination knob on the left (+Y)
    p.append(tube_y(tr * 0.85, 0.010, mat, x=xm, z=zc, y=y + r_tube + 0.003, sides=16))
    p.append(knurl_y(tr * 0.95, 0.008, "Metal", x=xm, z=zc, y=y + r_tube + 0.011, teeth=16))
    if glow_ring:
        p.append(ring_x(r_tube + 0.0045, r_tube + 0.0052, xs0 + 0.004, xs0 + 0.0065, "Glow", z=zc, y=y,
                        sides=sides))
    return p


def ring_mount(x, zc, zb, r, w=0.016, y=0.0, mat="Metal"):
    """Scope ring (split clamp with 2 screws per side) on a base clamped to a rail."""
    p = [ring_x(r, r + 0.0042, x - w / 2, x + w / 2, mat, z=zc, y=y, sides=16)]
    p.append(prism([(x - w / 2, zb), (x + w / 2, zb), (x + w / 2 - 0.002, zc - r * 0.5),
                    (x - w / 2 + 0.002, zc - r * 0.5)], r * 1.2, mat, y=y, bv=0.0008))
    p.append(rbox(x - w / 2 - 0.002, x + w / 2 + 0.002, y - 0.0125, y + 0.0125, zb - 0.002, zb + 0.004, mat, bv=0.0007))
    p.append(rbox(x - w * 0.35, x + w * 0.35, y - r - 0.0055, y - r - 0.0015, zc - 0.003, zc + 0.003, mat, bv=0.0004))
    for dx in (-w * 0.22, w * 0.22):
        p += screw(x + dx, zc + r * 0.55, y - r - 0.0030, 0.0016, -1, h=0.0010, sides=8)
        p += screw(x + dx, zc - r * 0.55, y - r - 0.0030, 0.0016, -1, h=0.0010, sides=8)
    p += screw(x, zb + 0.001, y - 0.0125, 0.0022, -1)
    return p


def finish_weapon(name, parts, grip, smooth=32):
    parts = [o for o in parts if o is not None]
    if os.environ.get("NB_DEBUG"):
        big = sorted(((nb.tri_count(o), i, o.data.materials[0].name if o.data.materials else "") for i, o in
                      enumerate(parts)), reverse=True)[:14]
        print("[weapon] heaviest parts (tris, index, material):", big)
    obj = nb.join(parts, "W_" + name)
    obj.data.transform(Matrix.Translation(Vector((-grip[0], 0, -grip[1]))))
    nb.auto_smooth(obj, smooth)
    uv_box(obj)
    return obj


def uv_box(obj):
    """Box projection at world scale, tile size per material (tiling maps)."""
    me = obj.data
    uv = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
    names = [m.name for m in me.materials]
    for p in me.polygons:
        tile = WEAPON_TILE.get(names[p.material_index], 0.1)
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


# --------------------------------------------------------------------------- weapons
def make_pistol():
    """Compact striker-less service pistol: polymer frame with an accessory rail, steel slide
    (Body finish) with front/rear cuts, optic cover plate, exposed ring hammer."""
    mats()
    p = []
    g, gc, gi = pistol_grip((0.018, 0.032), (-0.030, 0.034), 0.100, 16, 0.029, beaver=0.016)
    p += g
    bf, bb, d = (Vector(v) for v in gi["bottom"])
    nrm = gi["nrm"]
    # magazine: base plate with a finger lip + the mag body showing in the well
    p.append(prism([tuple(bf - d * 0.002 + nrm * 0.004), tuple(bb - d * 0.002 - nrm * 0.006),
                    tuple(bb + d * 0.0075 - nrm * 0.006), tuple(bf + d * 0.0075 + nrm * 0.006),
                    tuple(bf + d * 0.0040 + nrm * 0.0075)], 0.0305, "Polymer", bv=0.0018, seg=2))
    p.append(prism([tuple(bf - d * 0.004 + nrm * 0.001), tuple(bb - d * 0.004 - nrm * 0.001),
                    tuple(bb + d * 0.001 - nrm * 0.001), tuple(bf + d * 0.001 + nrm * 0.001)],
                   0.0255, "Metal", bv=0.0006))
    # frame / dust cover with an accessory rail underneath
    frame = prism([(-0.040, 0.030), (0.020, 0.030), (0.034, 0.024), (0.134, 0.024), (0.138, 0.030),
                   (0.138, 0.048), (-0.044, 0.048), (-0.054, 0.046), (-0.056, 0.042), (-0.046, 0.034)],
                  0.0275, "Polymer", bv=0.0016, seg=2)
    rcs = []
    for i in range(3):
        x = 0.083 + i * 0.016
        rcs.append(cutter(x, x + 0.0055, -0.02, 0.02, 0.020, 0.0275))
    p.append(cut(frame, rcs, mat="Polymer"))
    p += trigger_group(0.066, 0.031, "Polymer", 0.0115, square=True)
    # slide
    hw, c = 0.01275, 0.0032
    slide = xsec([(-hw, 0.0475), (hw, 0.0475), (hw, 0.0785 - c), (hw - c * 0.8, 0.0785), (-hw + c * 0.8, 0.0785),
                  (-hw, 0.0785 - c)], -0.046, 0.157, "Body", bv=0.0)
    slide = cut(slide, [cutter_prism([(0.150, 0.090), (0.160, 0.090), (0.160, 0.040), (0.157, 0.040),
                                      (0.157, 0.071)], -0.02, 0.02),
                        cutter_prism([(-0.050, 0.090), (-0.038, 0.090), (-0.038, 0.0785), (-0.046, 0.072),
                                      (-0.050, 0.072)], -0.02, 0.02)])
    bevel(slide, 0.0010, 1, 30, True)
    cs = []
    for i in range(8):                                                # rear serrations (both sides)
        x = -0.041 + i * 0.0044
        for sy in (1, -1):
            cs.append(cutter_prism([(x, 0.0505), (x + 0.0021, 0.0505), (x + 0.0031, 0.0755), (x + 0.0010, 0.0755)],
                                   sy * 0.0118, sy * 0.016))
    for i in range(4):                                                # front serrations
        x = 0.116 + i * 0.0046
        for sy in (1, -1):
            cs.append(cutter_prism([(x, 0.0505), (x + 0.0021, 0.0505), (x + 0.0031, 0.0730), (x + 0.0010, 0.0730)],
                                   sy * 0.0118, sy * 0.016))
    cs.append(cutter(0.044, 0.088, -0.020, 0.0025, 0.0645, 0.090))     # ejection port (right + top)
    cs.append(cutter(0.093, 0.145, -0.004, 0.004, 0.0765, 0.090))      # top lightening slot
    p.append(cut(slide, cs, mat="Body"))
    # barrel hood + chamber in the port, extractor, barrel crown, guide rod
    p.append(rbox(0.042, 0.090, -0.0095, 0.0065, 0.060, 0.0772, "Metal", bv=0.0008))
    p.append(rbox(0.050, 0.086, -0.0098, -0.0040, 0.0705, 0.0745, "Polymer", bv=0.0))  # chamber opening
    p.append(rbox(0.095, 0.143, -0.0035, 0.0035, 0.066, 0.0768, "Metal", bv=0.0005))   # barrel under slot
    p.append(rbox(0.088, 0.108, -0.0138, -0.0122, 0.0665, 0.0715, "Metal", bv=0.0004))  # extractor
    p.append(lathe_x([(0.0060, 0.1555), (0.0067, 0.1560), (0.0067, 0.1585), (0.0052, 0.1592)], "Metal",
                     z=0.064, sides=14))
    p.append(tube_x(0.0040, 0.1585, 0.1596, "Polymer", z=0.064, sides=10))
    p.append(tube_x(0.0042, 0.1500, 0.1575, "Metal", z=0.0525, sides=10, bv=0.0004, edge=True))
    # sights: front post (tritium dot), rear notch (two dots), both dovetailed
    p.append(prism([(0.136, 0.0785), (0.148, 0.0785), (0.146, 0.0855), (0.139, 0.0855)], 0.0034, "Metal",
                   bv=0.0004))
    p.append(tube_x(0.0012, 0.1455, 0.1462, "Glow", z=0.0835, sides=8))
    rear = prism([(-0.036, 0.0785), (-0.022, 0.0785), (-0.024, 0.0872), (-0.034, 0.0872)], 0.019, "Metal",
                 bv=0.0)
    p.append(cut(rear, [cutter(-0.040, -0.018, -0.0021, 0.0021, 0.0835, 0.090)], bv=0.0005, edge=True))
    for sy in (0.0055, -0.0055):
        p.append(tube_x(0.0011, -0.0222, -0.0215, "Glow", z=0.0838, y=sy, sides=8))
    # optic cover plate with 2 screws
    p.append(rbox(-0.018, 0.022, -0.0085, 0.0085, 0.0785, 0.0805, "Metal", bv=0.0005))
    p += screw_z(-0.012, 0.0, 0.0805, 0.0016, h=0.0006, sides=8)
    p += screw_z(0.016, 0.0, 0.0805, 0.0016, h=0.0006, sides=8)
    # ring hammer
    ham = prism([(-0.047, 0.049), (-0.043, 0.050), (-0.046, 0.066), (-0.052, 0.0745), (-0.060, 0.0745),
                 (-0.0625, 0.069), (-0.058, 0.064), (-0.054, 0.049)], 0.0080, "Metal", bv=0.0)
    p.append(cut(ham, [cutter_cyl(0.0026, "Y", (-0.0560, 0, 0.0690), 0.02, 12)], bv=0.0005, edge=True))
    p.append(pin_y(-0.049, 0.053, 0.0275, 0.0016))
    # controls (left side +Y): slide stop with a serrated pad, takedown lever, mag release
    ss = prism([(-0.010, 0.0445), (0.030, 0.0445), (0.034, 0.0475), (0.012, 0.0490), (0.000, 0.0525),
                (-0.010, 0.0515)], 0.0022, "Metal", y=0.0150, bv=0.0005)
    p.append(ss)
    for i in range(4):
        p.append(rbox(-0.008 + i * 0.0025, -0.007 + i * 0.0025, 0.0158, 0.0166, 0.0465, 0.0510, "Metal", bv=0.0))
    p.append(tube_y(0.0028, 0.0014, "Metal", x=0.030, z=0.0405, y=0.0145, sides=10, bv=0.0003, edge=True))
    p.append(rbox(0.035, 0.044, 0.0137, 0.0157, 0.0405, 0.0435, "Metal", bv=0.0004))     # takedown lever
    p.append(rbox(0.008, 0.015, 0.0135, 0.0165, 0.0195, 0.0275, "Metal", bv=0.0005))     # mag release
    for x, z in ((0.004, 0.038), (0.050, 0.040), (-0.030, 0.042)):
        p.append(pin_y(x, z, 0.0275, 0.0013))
    # grip panel screws + lanyard loop
    for t in (0.30, 0.78):
        c = Vector((0.018, 0.032)) * 0.5 + Vector((-0.030, 0.034)) * 0.5 + d * (0.100 * t)
        p += screw(c.x, c.y, 0.0153, 0.0019, 1, h=0.0008, sides=8)
        p += screw(c.x, c.y, -0.0153, 0.0019, -1, h=0.0008, sides=8)
    p.append(sling_loop(bb.x + 0.004, bb.y - 0.010, 0.0, R=0.0045, r=0.0010, axis="Y"))
    return finish_weapon("pistol", p, gc)


def gpts(tc, d, nrm, ta):
    """Points in a grip frame: tc + d * t + nrm * a for (t, a) in ta (a > 0 = towards the front)."""
    tc, d, nrm = Vector(tc), Vector(d), Vector(nrm)
    return [tuple(tc + d * t + nrm * a) for t, a in ta]


def chamfer_sec(hw, z0, z1, ct, cb=0.0, y=0.0):
    """Box cross-section (y, z) with chamfered top (ct) and bottom (cb) corners."""
    sec = [(y - hw + cb, z0), (y + hw - cb, z0), (y + hw, z0 + cb), (y + hw, z1 - ct), (y + hw - ct, z1),
           (y - hw + ct, z1), (y - hw, z1 - ct), (y - hw, z0 + cb)]
    out = []
    for q in sec:                          # drop duplicates when a chamfer is 0
        if not out or (abs(out[-1][0] - q[0]) > 1e-7 or abs(out[-1][1] - q[1]) > 1e-7):
            out.append(q)
    if abs(out[0][0] - out[-1][0]) < 1e-7 and abs(out[0][1] - out[-1][1]) < 1e-7:
        out.pop()
    return out


def fluted_x(r, x0, x1, mat, z=0.0, y=0.0, flutes=6, depth=0.18, r2=None):
    """Fluted barrel: lands and flat-bottomed flutes, optional taper to r2."""
    sec = []
    for i in range(flutes):
        a0 = 2 * math.pi * i / flutes
        for k, (da, rr) in enumerate(((0.0, 1.0), (0.42, 1.0), (0.52, 1 - depth), (0.88, 1 - depth),
                                      (0.98, 1.0))):
            if k == 4:
                continue
            a = a0 + da * 2 * math.pi / flutes
            sec.append((rr * r * math.cos(a), rr * r * math.sin(a)))
    o = xsec([(a, b) for a, b in sec], x0, x1, mat, bv=0.0, scale1=(r2 / r if r2 else 1.0))
    move(o, (0, y, z))
    return o


def flip_sight(x, z, mat="Metal", front=False, w=0.016, h=0.016, y=0.0):
    """Flip-up sight standing on a rail: base clamp + leaf (aperture or protected post)."""
    p = [rbox(x - 0.012, x + 0.012, y - w / 2, y + w / 2, z, z + 0.006, mat, bv=0.0007)]
    leaf = prism([(x - 0.006, z + 0.005), (x + 0.006, z + 0.005), (x + 0.004, z + h), (x - 0.004, z + h)],
                 w * 0.8, mat, y=y, bv=0.0)
    if front:
        leaf = cut(leaf, [cutter(x - 0.01, x + 0.01, y - w * 0.22, y + w * 0.22, z + h * 0.45, z + h + 0.01)],
                   bv=0.0005, edge=True)
        p.append(leaf)
        p.append(rbox(x - 0.0012, x + 0.0012, y - 0.0012, y + 0.0012, z + h * 0.4, z + h * 0.92, mat, bv=0.0))
        p.append(sphere(0.0012, (x, y, z + h * 0.9), "Glow", 6, 4))
    else:
        leaf = cut(leaf, [cutter_cyl(0.0022, "X", (x, y, z + h * 0.72), 0.03, 10)], bv=0.0005, edge=True)
        p.append(leaf)
    p += screw(x, z + 0.003, y - w / 2, 0.0016, -1, h=0.0008, sides=8)
    return p


def make_uzi():
    """Compact PDW-style SMG: magazine in the grip, chamfered receiver with a full-length rail,
    slotted barrel shroud, ported compensator, side charger, collapsed rod stock."""
    mats()
    p = []
    tf, tb = Vector((0.020, 0.024)), Vector((-0.022, 0.024))
    g, gc, gi = pistol_grip(tuple(tf), tuple(tb), 0.112, 6, 0.032, grooves=False)
    p += g
    d, nrm = gi["d"], gi["nrm"]
    tc = (tf + tb) / 2
    # magazine sticking out of the grip: ribbed body + base plate
    p.append(prism(gpts(tc, d, nrm, [(0.095, -0.015), (0.095, 0.0135), (0.172, 0.0145), (0.172, -0.016)]),
                   0.0245, "Polymer", bv=0.0012))
    for t in (0.125, 0.145):
        p.append(prism(gpts(tc, d, nrm, [(t, -0.0158), (t, 0.0143), (t + 0.006, 0.0145), (t + 0.006, -0.016)]),
                       0.0262, "Polymer", bv=0.0007))
    p.append(prism(gpts(tc, d, nrm, [(0.170, -0.019), (0.170, 0.018), (0.182, 0.019), (0.184, 0.0), (0.182, -0.020)]),
                   0.029, "Polymer", bv=0.0016, seg=2))
    # receiver
    rec = xsec(chamfer_sec(0.020, 0.022, 0.090, 0.006, 0.003), -0.150, 0.105, "Body", bv=0.0)
    rec = cut(rec, [cutter(0.020, 0.072, -0.03, -0.012, 0.056, 0.080),            # ejection port (right)
                    slot_cutter(-0.105, 0.002, 0.069, 0.006, 0.014, 0.03, 6)],      # charging slot (left)
              pre=(0.0012, 1), edge=False)
    p.append(rec)
    p.append(rbox(0.018, 0.074, -0.0125, 0.010, 0.058, 0.078, "Metal", bv=0.0006))   # bolt in the port
    p.append(rbox(0.030, 0.064, -0.0128, -0.010, 0.0625, 0.066, "MetalEdge", bv=0.0))  # bolt face groove
    p.append(rbox(-0.152, -0.142, -0.016, 0.016, 0.030, 0.084, "Metal", bv=0.0012))  # end cap
    for sy in (1, -1):                                                                # side ribs + screws
        p.append(rbox(-0.135, 0.000, sy * 0.0200 - 0.0012, sy * 0.0200 + 0.0012, 0.036, 0.042, "Body", bv=0.0005))
        for x in (-0.125, -0.020, 0.090):
            p += screw(x, 0.030, sy * 0.020, 0.0021, sy, h=0.0008, sides=8)
    p += picatinny(-0.138, 0.100, 0.090)
    # barrel shroud, barrel, thread, compensator
    p.append(slotted_handguard(0.105, 0.186, 0.026, 0.056, "Body", slots=3, sides=8, slot_h=0.010))
    p.append(ring_x(0.0085, 0.0235, 0.184, 0.190, "Metal", z=0.056, sides=16, bv=0.0005, edge=True))
    p.append(tube_x(0.0085, 0.100, 0.236, "Metal", z=0.056, sides=14))
    for i in range(5):
        x = 0.2245 + i * 0.0022
        p.append(ring_x(0.0084, 0.0093, x, x + 0.0012, "Metal", z=0.056, sides=14))
    p += muzzle_brake(0.236, 0.262, 0.0125, 0.056, ports=2, sides=16)
    # sights
    p += flip_sight(-0.118, 0.0965, front=False, w=0.018, h=0.014)
    p.append(rbox(0.162, 0.184, -0.007, 0.007, 0.0805, 0.088, "Metal", bv=0.0006))
    for sy in (1, -1):
        p.append(prism([(0.165, 0.087), (0.182, 0.087), (0.180, 0.102), (0.170, 0.102)], 0.0022, "Metal",
                       y=sy * 0.0058, bv=0.0004))
    p.append(rbox(0.1745, 0.1765, -0.0011, 0.0011, 0.087, 0.0985, "Metal", bv=0.0))
    p.append(sphere(0.0013, (0.1755, 0, 0.0985), "Glow", 6, 4))
    # lower: trigger housing, trigger group, selector + LED, mag release
    p.append(prism([(-0.034, 0.024), (0.080, 0.024), (0.080, 0.013), (0.068, 0.010), (-0.020, 0.010)], 0.034,
                   "Polymer", bv=0.0014, seg=2))
    p += trigger_group(0.058, 0.012, "Polymer", 0.012)
    p.append(tube_y(0.0042, 0.0016, "Metal", x=-0.012, z=0.034, y=0.0208, sides=12, bv=0.0003, edge=True))
    p.append(prism([(-0.013, 0.0325), (-0.002, 0.039), (0.0005, 0.0365), (-0.011, 0.031)], 0.0018, "Metal",
                   y=0.0222, bv=0.0))
    p.append(rbox(0.025, 0.048, -0.0212, -0.0198, 0.0835, 0.0865, "Glow", bv=0.0))
    p.append(rbox(0.006, 0.014, 0.0158, 0.0175, 0.010, 0.020, "Metal", bv=0.0004))
    # charging handle knob (left)
    p.append(tube_y(0.0034, 0.010, "Metal", x=-0.050, z=0.069, y=0.023, sides=10))
    p.append(knurl_y(0.0058, 0.008, "Metal", x=-0.050, z=0.069, y=0.031, teeth=12, depth=0.0006))
    # collapsed rod stock: two rods through guides, butt plate with rubber pad, sling loop
    for sy in (1, -1):
        p.append(tube_x(0.0042, -0.200, 0.010, "Metal", z=0.040, y=sy * 0.0245, sides=10))
        p.append(rbox(-0.012, 0.012, sy * 0.0205, sy * 0.0295, 0.033, 0.047, "Body", bv=0.0007))
        p.append(rbox(-0.148, -0.130, sy * 0.0195, sy * 0.0295, 0.032, 0.048, "Metal", bv=0.0008))
    plate = prism([(-0.204, 0.026), (-0.192, 0.026), (-0.192, 0.088), (-0.204, 0.094)], 0.058, "Polymer",
                  bv=0.0015, seg=2)
    p.append(cut(plate, [slot_cutter(-0.21, -0.18, 0.062, 0.016, -0.018, 0.018, 6)]))
    p.append(prism([(-0.2125, 0.024), (-0.2035, 0.026), (-0.2035, 0.094), (-0.2125, 0.096)], 0.052, "Grip",
                   bv=0.002, seg=2))
    p.append(sling_loop(-0.196, 0.030, 0.034, R=0.0055, axis="Z"))
    p.append(sling_loop(0.150, 0.026, 0.0, R=0.005))
    return finish_weapon("uzi", p, gc)


def make_shotgun():
    """Pump shotgun: steel receiver with a short rail and a ghost-ring sight, vent-ribbed barrel,
    magazine tube with a sling cap, grooved pump on action bars, side saddle with shells,
    sporting stock (Body colour) with a checkered wrist, ventilated recoil pad."""
    mats((0.20, 0.13, 0.08), body_metal=0.0, body_rough=0.55)
    p = []
    stock = prism([(-0.335, 0.045), (-0.335, -0.075), (-0.315, -0.080), (-0.130, -0.030), (-0.060, -0.018),
                   (-0.040, -0.010), (0.000, 0.000), (0.010, 0.045), (-0.060, 0.050), (-0.150, 0.042),
                   (-0.250, 0.046)], 0.040, "Body", bv=0.0035, seg=2, angle=30)
    p.append(stock)
    p.append(prism([(-0.300, 0.0455), (-0.170, 0.0425), (-0.150, 0.0405), (-0.170, 0.050), (-0.290, 0.052)],
                   0.030, "Body", bv=0.003, seg=2))                                   # comb
    # recoil pad: rubber with spacer line and vent slots
    pad = prism([(-0.352, -0.083), (-0.336, -0.080), (-0.336, 0.047), (-0.350, 0.050), (-0.354, -0.017)],
                0.044, "Grip", bv=0.0035, seg=2)
    p.append(cut(pad, [slot_cutter(-0.36, -0.34, z, 0.006, -0.012, 0.012, 4) for z in (-0.050, -0.020, 0.010)]))
    p.append(prism([(-0.3375, -0.080), (-0.3345, -0.080), (-0.3345, 0.047), (-0.3375, 0.047)], 0.0425, "Polymer",
                   bv=0.0))
    # checkered wrist panels
    for sy in (1, -1):
        p.append(prism([(-0.075, 0.030), (0.000, 0.030), (0.004, 0.002), (-0.040, -0.006), (-0.085, -0.010)],
                       0.004, "Grip", y=sy * 0.0185, bv=0.0008))
    p += screw(-0.200, -0.040, -0.020, 0.0035, -1)
    p.append(sling_loop(-0.280, -0.068, 0.0, R=0.0075, r=0.0016))
    p.append(tube_z(0.004, -0.065, -0.058, "Metal", x=-0.280, sides=8))
    # receiver: steel, ejection port with bolt, loading port below, pins, short rail + ghost ring
    rec = xsec(chamfer_sec(0.019, 0.000, 0.075, 0.008, 0.002), 0.000, 0.215, "Metal", bv=0.0)
    rec = cut(rec, [cutter_prism([(0.000, 0.090), (0.008, 0.090), (0.008, 0.000), (0.000, 0.000)], -0.03, 0.03),
                    cutter(0.080, 0.160, -0.03, -0.010, 0.032, 0.062),
                    cutter(0.090, 0.180, -0.012, 0.012, -0.01, 0.006)],
              pre=(0.0014, 1), edge=True)
    p.append(rec)
    p.append(prism([(-0.004, 0.000), (0.012, 0.000), (0.012, 0.072), (0.003, 0.068)], 0.034, "Metal",
                   bv=0.0012))
    p.append(rbox(0.078, 0.160, -0.0145, 0.010, 0.036, 0.058, "Metal", bv=0.0005))
    p.append(rbox(0.090, 0.150, -0.0150, -0.0130, 0.042, 0.050, "MetalEdge", bv=0.0))
    p.append(rbox(0.088, 0.182, -0.009, 0.009, 0.002, 0.004, "Polymer", bv=0.0))    # loading port shadow
    for x, z in ((0.030, 0.012), (0.060, 0.012)):
        p.append(pin_y(x, z, 0.038, 0.0017))
    p += picatinny(0.040, 0.205, 0.075, w=0.020)
    p.append(rbox(0.020, 0.040, -0.009, 0.009, 0.075, 0.080, "Metal", bv=0.0006))
    for sy in (1, -1):
        p.append(prism([(0.022, 0.079), (0.038, 0.079), (0.034, 0.098), (0.026, 0.098)], 0.0035, "Metal",
                       y=sy * 0.0075, bv=0.0004))
    ghost = prism([(0.0265, 0.080), (0.0335, 0.080), (0.0335, 0.103), (0.0265, 0.103)], 0.0085, "Metal", bv=0.0)
    p.append(cut(ghost, [cutter_cyl(0.0024, "X", (0.03, 0, 0.096), 0.02, 12)], bv=0.0004, edge=True))
    # controls: safety button, slide release, trigger group
    p.append(tube_y(0.0035, 0.044, "Metal", x=0.015, z=0.010, sides=10, bv=0.0004, edge=True))
    p.append(rbox(0.030, 0.042, -0.0215, -0.0185, -0.004, 0.0, "Metal", bv=0.0004))
    p += trigger_group(0.078, 0.002, "Metal", 0.012, square=False)
    # side saddle (left) with 4 shells: brass bases + hulls
    p.append(rbox(0.040, 0.150, 0.0195, 0.0225, 0.010, 0.064, "Polymer", bv=0.0008))
    p += screw(0.050, 0.020, 0.0225, 0.0022, 1, h=0.0008)
    p += screw(0.140, 0.020, 0.0225, 0.0022, 1, h=0.0008)
    for i in range(4):
        x = 0.060 + i * 0.0225
        p.append(lathe_x([(0.0, 0.001), (0.0108, 0.001), (0.0108, 0.0035), (0.0098, 0.004), (0.0098, 0.0115)],
                         "MetalEdge", sides=12))
        rot(p[-1], 90, "Y", (0, 0, 0))
        move(p[-1], (x, 0.0325, 0.074))
        p.append(tube_z(0.0098, 0.008, 0.0635, "Body", x=x, y=0.0325, sides=12))
        p.append(rbox(x - 0.0108, x + 0.0108, 0.0225, 0.0435, 0.026, 0.032, "Polymer", bv=0.0005))
    # barrel + vent rib + bead, magazine tube + cap with sling loop, barrel clamp
    p.append(tube_x(0.0115, 0.200, 0.690, "Metal", z=0.055, sides=16))
    p.append(lathe_x([(0.0115, 0.680), (0.0122, 0.684), (0.0122, 0.692), (0.0105, 0.6935)], "Metal", z=0.055,
                     sides=16, bv=0.0, edge=True))
    p.append(tube_x(0.0078, 0.6915, 0.6940, "Polymer", z=0.055, sides=12))
    p.append(rbox(0.205, 0.680, -0.0042, 0.0042, 0.0705, 0.0735, "Metal", bv=0.0005))
    for i in range(16):
        x = 0.215 + i * 0.0295
        p.append(rbox(x, x + 0.006, -0.0025, 0.0025, 0.064, 0.071, "Metal", bv=0.0))
    p.append(tube_z(0.0022, 0.0735, 0.0775, "Metal", x=0.676, sides=8))
    p.append(sphere(0.0026, (0.676, 0, 0.078), "Glow", 8, 5))
    p.append(tube_x(0.0110, 0.200, 0.596, "Metal", z=0.022, sides=16))
    p.append(lathe_x([(0.0105, 0.594), (0.0128, 0.598), (0.0128, 0.614), (0.0090, 0.620)], "Metal", z=0.022,
                     sides=16, edge=True))
    p.append(knurl_ring(0.0131, 0.600, 0.611, "Metal", z=0.022, teeth=16, depth=0.0007))
    p.append(sling_loop(0.6235, 0.022, 0.0, R=0.0055))
    clamp = prism([(0.560, 0.010), (0.585, 0.010), (0.585, 0.068), (0.560, 0.068)], 0.026, "Metal", bv=0.0)
    p.append(cut(clamp, [cutter_cyl(0.0115, "X", (0.57, 0, 0.055), 0.05, 16),
                         cutter_cyl(0.0110, "X", (0.57, 0, 0.022), 0.05, 16)], bv=0.0008, edge=True))
    p += screw(0.5725, 0.0385, -0.013, 0.0028, -1)
    # pump: grooved polymer forend on two action bars
    pump = lathe_x([(0.021, 0.300), (0.0262, 0.306), (0.0262, 0.484), (0.021, 0.490)], "Polymer", z=0.027,
                   sides=16, bv=0.0)
    pc = []
    for i in range(7):
        x = 0.322 + i * 0.022
        pc.append(ring_cutter(0.0242, 0.04, x, x + 0.0075, z=0.027))
    p.append(cut(pump, pc, edge=False))
    for sy in (1, -1):
        p.append(rbox(0.150, 0.302, sy * 0.0125 - 0.0012, sy * 0.0125 + 0.0012, 0.012, 0.018, "Metal", bv=0.0))
    return finish_weapon("shotgun", p, (-0.03, -0.012))


def ring_cutter(r_in, r_out, x0, x1, z=0.0, y=0.0, sides=16):
    """Annular cutter (grooves around tubes)."""
    prof = [(r_in, x0), (r_out, x0), (r_out, x1), (r_in, x1)]
    v, f = nb.lathe(prof + [prof[0]], sides, axis="X")
    v = [(a, b + y, c + z) for a, b, c in v]
    o = nb.mesh_object("ringcut", v, f)
    _clean(o, tri=False)
    return o


def curved_mag(x_top0, x_top1, z_top, n=6, length=0.150, curve=0.035, w=0.024, mat="Polymer", ribs=True):
    """Curved box magazine hanging from (x_top0..x_top1, z_top): spine bent forward."""
    p = []
    front, back = [], []
    for i in range(n + 1):
        t = i / n
        dx = curve * t * t + 0.008 * t
        z = z_top - length * t
        wid = (x_top1 - x_top0) * (1 + 0.08 * t)
        back.append((x_top0 + dx, z))
        front.append((x_top0 + dx + wid, z))
    body = prism(front + back[::-1], w, mat, bv=0.0012)
    p.append(body)
    if ribs:
        for i in range(1, n):
            if i % 2:
                continue
            t0 = i / n
            fx, fz = front[i]
            bx, bz = back[i]
            p.append(prism([(bx - 0.0008, bz), (fx + 0.0008, fz), (fx + 0.0008, fz - 0.005), (bx - 0.0008, bz - 0.005)],
                           w + 0.0016, mat, bv=0.0005))
    fx, fz = front[-1]
    bx, bz = back[-1]
    p.append(prism([(bx - 0.003, bz + 0.002), (fx + 0.003, fz + 0.002), (fx + 0.004, fz - 0.008),
                    (bx - 0.004, bz - 0.008)], w + 0.004, mat, bv=0.0016, seg=2))
    return p


def make_rifle():
    """Assault rifle: monolithic upper with a continuous rail, side charger, slotted octagonal
    free-float handguard, ported brake, curved ribbed magazine, adjustable skeleton stock on a
    buffer tube, tube red-dot sight and folded flip-up irons."""
    mats()
    p = []
    g, gc, gi = pistol_grip((0.002, 0.040), (-0.032, 0.040), 0.105, 18, 0.030)
    p += g
    # lower receiver with mag well, integrated guard
    low = prism([(-0.110, 0.040), (-0.004, 0.040), (0.004, 0.034), (0.058, 0.034), (0.062, 0.006),
                 (0.122, 0.006), (0.126, 0.034), (0.145, 0.040), (0.145, 0.078), (-0.110, 0.078)], 0.030, "Body",
                bv=0.0016, seg=1)
    p.append(cut(low, [cutter(0.066, 0.118, -0.0125, 0.0125, 0.0, 0.034)]))
    p += trigger_group(0.048, 0.041, "Body", 0.012)
    for x, z in ((-0.020, 0.048), (0.030, 0.050), (0.135, 0.068), (-0.100, 0.068)):
        p.append(pin_y(x, z, 0.030, 0.0018))
    p.append(prism([(-0.004, 0.051), (0.010, 0.058), (0.012, 0.055), (0.000, 0.047)], 0.002, "Metal", y=0.0165,
                   bv=0.0))                                                                 # selector
    p.append(tube_y(0.0045, 0.0015, "Metal", x=-0.002, z=0.052, y=0.0158, sides=12, bv=0.0003, edge=True))
    p.append(tube_y(0.0035, 0.004, "Metal", x=0.050, z=0.044, y=-0.0165, sides=10, bv=0.0004, edge=True))
    p.append(prism([(0.072, 0.040), (0.084, 0.040), (0.082, 0.048), (0.074, 0.050)], 0.0022, "Metal", y=0.0162,
                   bv=0.0))                                                                 # bolt catch
    # upper receiver: chamfered section, ejection port with bolt carrier, brass deflector
    up = xsec(chamfer_sec(0.016, 0.078, 0.112, 0.004, 0.0), -0.115, 0.165, "Body", bv=0.0)
    up = cut(up, [cutter(0.020, 0.090, -0.03, -0.010, 0.084, 0.103),
                  slot_cutter(-0.080, 0.030, 0.097, 0.0055, 0.010, 0.03, 6)], pre=(0.0012, 1))
    p.append(up)
    p.append(rbox(0.018, 0.092, -0.0128, 0.008, 0.083, 0.104, "Metal", bv=0.0006))
    p.append(rbox(0.030, 0.062, -0.0132, -0.0125, 0.090, 0.097, "MetalEdge", bv=0.0))
    p.append(prism([(-0.004, 0.098), (0.016, 0.098), (0.016, 0.108), (0.004, 0.110)], 0.006, "Body",
                   y=-0.018, bv=0.0008))                                                    # deflector
    p.append(tube_y(0.0030, 0.010, "Metal", x=0.010, z=0.097, y=0.020, sides=10))       # side charger
    p.append(prism([(0.002, 0.092), (0.020, 0.092), (0.022, 0.102), (0.004, 0.102)], 0.008, "Metal", y=0.027,
                   bv=0.0008))
    p += picatinny(-0.108, 0.405, 0.112)
    # handguard + screws, gas block, barrel, brake
    p.append(slotted_handguard(0.165, 0.418, 0.031, 0.086, "Body", slots=6, sides=8, slot_h=0.0105,
                               rows=(0.0,)))
    for x in (0.180, 0.400):
        for sy in (1, -1):
            p += screw(x, 0.075, sy * 0.0287, 0.0020, sy, h=0.0008, sides=8)
    p.append(ring_x(0.0095, 0.024, 0.160, 0.170, "Metal", z=0.086, sides=16, bv=0.0005, edge=True))
    p.append(tube_x(0.0095, 0.165, 0.545, "Metal", z=0.086, sides=14))
    p.append(rbox(0.430, 0.452, -0.011, 0.011, 0.074, 0.100, "Metal", bv=0.0012))
    p.append(tube_x(0.0045, 0.380, 0.430, "Metal", z=0.0965, sides=8))
    p += screw(0.441, 0.096, -0.011, 0.0018, -1, h=0.0008, sides=8)
    p += muzzle_brake(0.535, 0.586, 0.0145, 0.086, ports=3, sides=16)
    # irons folded flat on the rail ends
    p.append(rbox(-0.100, -0.078, -0.008, 0.008, 0.1185, 0.1255, "Metal", bv=0.0006))
    p.append(rbox(-0.098, -0.080, -0.006, 0.006, 0.1255, 0.1295, "Metal", bv=0.0005))
    p.append(rbox(0.372, 0.398, -0.008, 0.008, 0.1185, 0.1255, "Metal", bv=0.0006))
    p.append(rbox(0.374, 0.396, -0.006, 0.006, 0.1255, 0.1295, "Metal", bv=0.0005))
    p.append(sphere(0.0013, (0.394, 0, 0.1300), "Glow", 6, 4))
    # magazine
    p += curved_mag(0.066, 0.116, 0.010, length=0.135, curve=0.030, w=0.024)
    # buffer tube + adjustable skeleton stock + pad
    p.append(tube_x(0.0150, -0.300, -0.110, "Metal", z=0.092, sides=16))
    p.append(ring_x(0.0150, 0.0175, -0.122, -0.112, "Metal", z=0.092, sides=16, bv=0.0004, edge=True))
    stk = prism([(-0.200, 0.110), (-0.200, 0.070), (-0.240, 0.040), (-0.330, 0.020), (-0.336, 0.020),
                 (-0.336, 0.118), (-0.250, 0.118)], 0.030, "Polymer", bv=0.0022, seg=2)
    p.append(cut(stk, [cutter_prism([(-0.236, 0.062), (-0.300, 0.034), (-0.316, 0.034), (-0.316, 0.072), (-0.250, 0.072)],
                                    -0.03, 0.03)]))
    p.append(prism([(-0.290, 0.118), (-0.215, 0.116), (-0.205, 0.124), (-0.290, 0.128)], 0.026, "Polymer",
                   bv=0.002, seg=2))                                                       # cheek rest
    pad = prism([(-0.351, 0.016), (-0.336, 0.016), (-0.336, 0.122), (-0.351, 0.122)], 0.036, "Grip", bv=0.003, seg=2)
    p.append(pad)
    p.append(tube_y(0.0028, 0.034, "Metal", x=-0.215, z=0.080, sides=10))                # lock lever pin
    p.append(sling_loop(-0.326, 0.028, 0.0, R=0.006))
    p.append(ring_x(0.0035, 0.0062, -0.127, -0.119, "Metal", z=0.072, y=0.016, sides=10))  # QD cup
    # red dot
    rd, _ = red_dot(0.000, 0.062, 0.1185, "Body", r=0.0175)
    p += rd
    return finish_weapon("rifle", p, gc)


def make_sniper():
    """Bolt-action precision rifle on a chassis: slotted fore-end, folding stock with an
    adjustable cheek riser and butt pad, round receiver with exposed bolt and tactical knob,
    fluted tapered barrel, big two-port brake, long scope on rings, folded bipod."""
    mats((0.16, 0.18, 0.13), body_metal=0.25)
    p = []
    g, gc, gi = pistol_grip((0.004, 0.040), (-0.030, 0.040), 0.10, 20, 0.030)
    p += g
    # chassis + fore-end with slots and a bottom rail
    ch = prism([(-0.040, 0.040), (0.180, 0.040), (0.200, 0.030), (0.450, 0.030), (0.456, 0.050), (0.450, 0.074),
                (-0.120, 0.074), (-0.150, 0.060)], 0.044, "Body", bv=0.0, seg=1)
    cs = [slot_cutter(0.215 + i * 0.040, 0.240 + i * 0.040, 0.052, 0.009, -0.03, 0.03, 3) for i in range(6)]
    cs.append(cutter(0.035, 0.105, -0.0155, 0.0155, 0.030, 0.050))                  # mag well
    p.append(cut(ch, cs, pre=(0.0016, 1)))
    for x in (0.150, 0.300):
        for sy in (1, -1):
            p += screw(x, 0.064, sy * 0.022, 0.0024, sy, h=0.0009)
    # folding stock: hinge, skeleton frame, cheek riser with knobs, pad with spacers, monopod
    p.append(rbox(-0.160, -0.138, -0.020, 0.020, 0.038, 0.076, "Metal", bv=0.0014))
    p.append(tube_z(0.0045, 0.030, 0.084, "Metal", x=-0.149, y=-0.014, sides=10))
    stk = prism([(-0.160, 0.074), (-0.160, 0.040), (-0.250, 0.010), (-0.400, -0.055), (-0.420, -0.060),
                 (-0.420, 0.074)], 0.036, "Body", bv=0.0)
    stk = cut(stk, [cutter_prism([(-0.200, 0.058), (-0.250, 0.030), (-0.380, -0.030), (-0.395, -0.030),
                                  (-0.395, 0.058)], -0.03, 0.03)], pre=(0.0018, 1))
    p.append(stk)
    p.append(prism([(-0.150, 0.074), (-0.150, 0.098), (-0.170, 0.104), (-0.370, 0.106), (-0.388, 0.090),
                    (-0.388, 0.074)], 0.030, "Polymer", bv=0.003, seg=2))               # cheek riser
    for x in (-0.200, -0.330):
        p.append(tube_z(0.0035, 0.074, 0.080, "Metal", x=x, sides=8))
        p.append(knurl_y(0.0068, 0.008, "Metal", x=x, z=0.084, y=0.021, teeth=12, depth=0.0006))
    p.append(prism([(-0.428, -0.064), (-0.420, -0.064), (-0.420, 0.076), (-0.428, 0.076)], 0.040, "Polymer", bv=0.001))
    p.append(prism([(-0.444, -0.066), (-0.428, -0.066), (-0.428, 0.078), (-0.442, 0.080), (-0.446, 0.006)],
                   0.042, "Grip", bv=0.0035, seg=2))
    p.append(tube_z(0.0050, -0.085, -0.030, "Metal", x=-0.360, sides=10))
    p.append(knurl_z(0.0095, -0.064, -0.052, "Metal", x=-0.360, teeth=14))
    p.append(tube_z(0.0090, -0.094, -0.085, "Grip", x=-0.360, sides=12, bv=0.001))
    p.append(ring_x(0.004, 0.0068, -0.300, -0.292, "Metal", z=-0.012, y=0.019, sides=10))
    p.append(sling_loop(-0.405, -0.052, 0.0, R=0.0065))
    # receiver + bolt
    p.append(cut(tube_x(0.021, -0.100, 0.150, "Metal", z=0.090, sides=16),
                        [cutter(0.000, 0.075, -0.03, -0.004, 0.090, 0.12)], pre=(0.0010, 1), edge=True))
    p.append(tube_x(0.0155, -0.020, 0.080, "MetalEdge", z=0.091, sides=14))            # bolt body in the port
    for i in range(3):
        x = 0.006 + i * 0.022
        p.append(rbox(x, x + 0.009, -0.0157, -0.0150, 0.087, 0.095, "Metal", bv=0.0))
    p.append(lathe_x([(0.012, -0.135), (0.017, -0.130), (0.019, -0.112), (0.021, -0.100)], "Metal", z=0.090,
                     sides=16, edge=True))                                                  # bolt shroud
    p.append(tube_y(0.0050, 0.040, "Metal", x=-0.070, z=0.092, y=-0.040, sides=10))
    rot(p[-1], 12, "X", (-0.070, -0.020, 0.092))
    p.append(knurl_z(0.0105, -0.010, 0.010, "Metal", teeth=14, depth=0.0008))
    rot(p[-1], 90, "X")
    rot(p[-1], 12, "X")
    move(p[-1], (-0.070, -0.060, 0.084))
    p += picatinny(-0.110, 0.168, 0.111, w=0.021)
    p.append(rbox(-0.105, 0.160, -0.010, 0.010, 0.104, 0.112, "Metal", bv=0.0008))
    # magazine + trigger
    p.append(prism([(0.040, 0.034), (0.100, 0.034), (0.098, 0.004), (0.042, 0.004)], 0.030, "Polymer", bv=0.0014))
    p.append(prism([(0.038, 0.006), (0.104, 0.006), (0.104, -0.002), (0.038, -0.002)], 0.033, "Polymer",
                   bv=0.0016, seg=2))
    p += trigger_group(0.040, 0.041, "Metal", 0.012, square=False)
    # barrel: fluted, tapered; brake
    p.append(tube_x(0.0150, 0.150, 0.190, "Metal", z=0.090, sides=16))
    p.append(fluted_x(0.0140, 0.190, 0.740, "Metal", z=0.090, flutes=6, r2=0.0105))
    p.append(tube_x(0.0105, 0.740, 0.760, "Metal", z=0.090, sides=14))
    brk = prism([(0.755, 0.074), (0.810, 0.074), (0.810, 0.106), (0.755, 0.106)], 0.032, "Metal", bv=0.0)
    brk = cut(brk, [cutter(0.768, 0.780, -0.03, 0.03, 0.078, 0.102), cutter(0.788, 0.800, -0.03, 0.03, 0.078, 0.102),
                    cutter(0.770, 0.778, -0.006, 0.006, 0.096, 0.12), cutter(0.790, 0.798, -0.006, 0.006, 0.096, 0.12)],
              bv=0.0010, edge=True)
    p.append(brk)
    p.append(tube_x(0.0060, 0.809, 0.8105, "Polymer", z=0.090, sides=10))
    # bipod folded under the fore-end
    p.append(rbox(0.418, 0.448, -0.016, 0.016, 0.012, 0.0315, "Metal", bv=0.0012))
    p.append(tube_y(0.0045, 0.036, "Metal", x=0.425, z=0.020, sides=10))
    for sy in (0.012, -0.012):
        p.append(tube_x(0.0055, 0.250, 0.430, "Metal", z=0.016, y=sy, sides=10))
        p.append(tube_x(0.0042, 0.215, 0.255, "Metal", z=0.016, y=sy, sides=10))
        p.append(ring_x(0.0055, 0.0070, 0.300, 0.312, "Metal", z=0.016, y=sy, sides=10))
        p.append(sphere(0.0072, (0.212, sy, 0.016), "Grip", 8, 5))
    # scope + rings
    zs = 0.150
    p += scope(-0.130, 0.290, zs, r_tube=0.0155, r_obj=0.029, r_eye=0.0225, mat="Body", sunshade=0.0, sides=14)
    for x in (-0.030, 0.150):
        p += ring_mount(x, zs, 0.115, 0.0155)
    return finish_weapon("sniper", p, gc)


def make_rocket():
    """Reusable shoulder launcher: tube with a ribbed heat-shield sleeve, rubber muzzle bumper,
    flared rear venturi, ogive warhead with fuze, grip/trigger housing, front grip, left side
    optic with rubber eyecup, top rail with flip sights, shoulder pad, clamps and sling loops."""
    mats((0.20, 0.24, 0.15), body_metal=0.1, body_rough=0.55)
    p = []
    zc = 0.125
    S = 24
    p.append(lathe_x([(0.0545, -0.470), (0.0545, 0.440)], "Body", z=zc, sides=S, cap_start=False, cap_end=False))
    p.append(lathe_x([(0.047, -0.505), (0.047, 0.488)], "Polymer", z=zc, sides=S, cap_start=False, cap_end=False))
    # rear venturi (flared, steel) + reinforcement rings
    p.append(lathe_x([(0.0545, -0.470), (0.058, -0.474), (0.058, -0.486), (0.064, -0.500), (0.066, -0.507),
                      (0.0615, -0.508), (0.050, -0.494), (0.047, -0.490)], "Metal", z=zc, sides=S, cap_start=False,
                     cap_end=False, edge=True))
    for x in (-0.440, -0.300):
        p.append(ring_x(0.054, 0.0585, x, x + 0.016, "Metal", z=zc, sides=S, bv=0.0006, edge=True))
    # heat shield sleeve with ribs and vent holes
    hs = ring_x(0.0545, 0.0600, -0.250, 0.080, "Polymer", z=zc, sides=S)
    hc = []
    for i in range(6):
        x = -0.225 + i * 0.052
        for a in (90, 270):
            c = slot_cutter(x, x + 0.030, 0.0, 0.010, -0.0, 0.08, 3)
            rot(c, a, "X")
            move(c, (0, 0, zc))
            hc.append(c)
    p.append(cut(hs, hc, edge=False, mat="Polymer"))
    for x in (-0.255, 0.080):
        p.append(ring_x(0.0545, 0.0625, x, x + 0.010, "Metal", z=zc, sides=S, bv=0.0006, edge=True))
    # muzzle: flared end + rubber bumper
    p.append(lathe_x([(0.0545, 0.440), (0.060, 0.452), (0.064, 0.470), (0.064, 0.488), (0.047, 0.488)], "Body",
                     z=zc, sides=S, cap_start=False, cap_end=False))
    p.append(ring_x(0.0560, 0.0670, 0.470, 0.492, "Grip", z=zc, sides=S, bv=0.002))
    # warhead: tube adapter, body with a band, ogive and fuze tip
    p.append(lathe_x([(0.044, 0.440), (0.044, 0.505), (0.046, 0.508), (0.046, 0.520), (0.042, 0.528),
                      (0.038, 0.548), (0.030, 0.572), (0.020, 0.594), (0.012, 0.606), (0.0075, 0.612)],
                     "Metal", z=zc, sides=S, cap_start=True, cap_end=False))
    p.append(ring_x(0.0438, 0.0458, 0.488, 0.498, "MetalEdge", z=zc, sides=S))
    p.append(lathe_x([(0.0075, 0.612), (0.0065, 0.616), (0.0, 0.619)], "Glow", z=zc, sides=12, cap_start=False))
    # trigger housing + grip + guard
    g, gc, gi = pistol_grip((0.010, 0.065), (-0.028, 0.065), 0.105, 14, 0.032)
    p += g
    p.append(prism([(-0.052, 0.064), (0.074, 0.064), (0.074, 0.072), (0.060, 0.082), (-0.040, 0.082),
                    (-0.052, 0.074)], 0.040, "Body", bv=0.0018, seg=2))
    p.append(rbox(-0.046, 0.068, -0.018, 0.018, 0.080, 0.086, "Metal", bv=0.0008))
    p += trigger_group(0.052, 0.065, "Body", 0.012)
    p.append(tube_y(0.004, 0.044, "Metal", x=0.000, z=0.074, sides=10, bv=0.0004, edge=True))  # safety
    for x in (-0.040, 0.062):
        p += screw(x, 0.073, -0.020, 0.0022, -1)
    # clamps holding the housing / front grip on the tube
    for x in (-0.020, 0.040, 0.250, 0.300):
        p.append(ring_x(0.0605 if -0.25 < x < 0.08 else 0.0545, 0.064, x - 0.006, x + 0.006, "Metal", z=zc,
                        sides=S, bv=0.0005, edge=True))
    # front grip
    p.append(rbox(0.240, 0.310, -0.018, 0.018, 0.064, 0.074, "Body", bv=0.0014))
    fg = lathe_x([(0.0, 0.0), (0.0175, 0.0), (0.0185, 0.012), (0.0165, 0.040), (0.0175, 0.068), (0.0150, 0.075)],
                 "Grip", sides=14, bv=0.0)
    rot(fg, -90, "Y")
    move(fg, (0.275, 0, -0.002))
    p.append(fg)
    # shoulder pad under the rear
    p.append(prism([(-0.240, zc - 0.058), (-0.050, zc - 0.058), (-0.060, zc - 0.078), (-0.230, zc - 0.082)],
                   0.054, "Grip", bv=0.004, seg=2))
    # top rail + flip sights
    p.append(rbox(-0.270, 0.400, -0.010, 0.010, zc + 0.053, zc + 0.059, "Metal", bv=0.0008))
    p += picatinny(-0.260, -0.200, zc + 0.059)
    p += picatinny(0.340, 0.390, zc + 0.059)
    p += flip_sight(-0.230, zc + 0.065, front=False, w=0.018, h=0.024)
    p += flip_sight(0.365, zc + 0.065, front=True, w=0.018, h=0.026)
    # optic on the left side: arm, body, objective / eyepiece lenses, rubber eyecup, knobs, LED
    yo, zo = 0.086, zc + 0.045
    p.append(rbox(-0.030, 0.050, 0.050, 0.072, zc + 0.000, zc + 0.026, "Metal", bv=0.0012))
    ob = xsec(chamfer_sec(0.016, zo - 0.024, zo + 0.024, 0.006, 0.006, y=yo), -0.050, 0.095, "Body", bv=0.0014)
    p.append(ob)
    p.append(lathe_x([(0.017, 0.095), (0.020, 0.100), (0.020, 0.118), (0.0185, 0.120), (0.0165, 0.120),
                      (0.0165, 0.100)], "Body", z=zo, y=yo, sides=18, cap_start=False, cap_end=False))
    p.append(tube_x(0.0165, 0.112, 0.113, "Lens", z=zo, y=yo, sides=18))
    p.append(lathe_x([(0.013, -0.050), (0.016, -0.060), (0.018, -0.075), (0.0155, -0.078), (0.011, -0.066),
                      (0.0105, -0.050)], "Grip", z=zo, y=yo, sides=16, cap_start=False, cap_end=False, bv=0.0))
    p.append(tube_x(0.0105, -0.060, -0.059, "Lens", z=zo, y=yo, sides=14))
    p.append(knurl_z(0.0075, zo + 0.024, zo + 0.034, "Metal", x=0.020, y=yo, teeth=14))
    p.append(knurl_y(0.0075, 0.010, "Metal", x=0.020, z=zo, y=yo + 0.021, teeth=14))
    p.append(rbox(0.050, 0.070, yo - 0.003, yo + 0.003, zo + 0.0235, zo + 0.0255, "Glow", bv=0.0))
    # sling loops
    p.append(sling_loop(-0.400, zc - 0.060, 0.0, R=0.008, r=0.0018))
    p.append(sling_loop(0.400, zc - 0.060, 0.0, R=0.008, r=0.0018))
    p.append(rbox(-0.408, -0.392, -0.006, 0.006, zc - 0.058, zc - 0.052, "Metal", bv=0.0006))
    p.append(rbox(0.392, 0.408, -0.006, 0.006, zc - 0.058, zc - 0.052, "Metal", bv=0.0006))
    return finish_weapon("rocket", p, gc)


def make_minigun():
    """Hand-held rotary gun: six barrels in a cluster with crowns, two perforated clamps,
    fluted rotor, finned motor, vented housing with status LEDs, carry handle, front handle,
    ammo box with lid and latch, articulated feed chute."""
    mats((0.12, 0.12, 0.13))
    p = []
    zc = 0.105
    for i in range(6):
        a = 2 * math.pi * i / 6 + math.pi / 6
        y, z = 0.026 * math.cos(a), zc + 0.026 * math.sin(a)
        p.append(tube_x(0.0085, 0.16, 0.876, "Metal", z=z, y=y, sides=10))
        p.append(lathe_x([(0.0085, 0.872), (0.0095, 0.874), (0.0095, 0.882), (0.0080, 0.884)], "Metal", z=z, y=y,
                         sides=10, edge=True))
        p.append(tube_x(0.0046, 0.8825, 0.8845, "Polymer", z=z, y=y, sides=8))
    p.append(tube_x(0.009, 0.16, 0.86, "Polymer", z=zc, sides=10))
    for x, r in ((0.46, 0.0415), (0.83, 0.0400)):
        cl = lathe_x([(r - 0.004, x), (r, x + 0.004), (r, x + 0.020), (r - 0.004, x + 0.024)], "Metal", z=zc, sides=18)
        cs = []
        for i in range(6):
            a = 2 * math.pi * i / 6 + math.pi / 6 + math.pi / 6
            cs.append(cutter_cyl(0.0050, "X", (x + 0.012, 0.031 * math.cos(a), zc + 0.031 * math.sin(a)), 0.05, 8))
        p.append(cut(cl, cs, edge=True, mat="Metal"))
    # rotor: fluted drum
    rot_ = lathe_x([(0.048, 0.050), (0.054, 0.056), (0.054, 0.165), (0.044, 0.176)], "Metal", z=zc, sides=18)
    rc = []
    for i in range(6):
        a = 2 * math.pi * i / 6
        c = cutter(0.068, 0.155, -0.006, 0.006, 0.048, 0.07)
        rot(c, math.degrees(a), "X", (0, 0, 0))
        move(c, (0, 0, zc))
        rc.append(c)
    p.append(cut(rot_, rc, edge=True, mat="Metal"))
    # housing (Body) with vents, motor with fins, end cap with screws
    hs = prism([(-0.090, 0.060), (0.072, 0.060), (0.072, 0.160), (-0.060, 0.160), (-0.090, 0.135)], 0.090, "Body",
               bv=0.0)
    vc = [slot_cutter(-0.055 + i * 0.024, -0.040 + i * 0.024, 0.118, 0.034, -0.05, -0.036, 6) for i in range(4)]
    vc += [slot_cutter(-0.055 + i * 0.024, -0.040 + i * 0.024, 0.118, 0.034, 0.036, 0.05, 6) for i in range(4)]
    p.append(cut(hs, vc, pre=(0.004, 2)))
    for i in range(4):
        x = -0.0475 + i * 0.024
        p.append(rbox(x - 0.006, x + 0.006, -0.040, 0.040, 0.102, 0.134, "Polymer", bv=0.0))
    p.append(tube_x(0.032, -0.140, -0.088, "Metal", z=0.112, sides=20))
    for i in range(6):
        x = -0.136 + i * 0.008
        p.append(ring_x(0.031, 0.040, x, x + 0.004, "Metal", z=0.112, sides=20, bv=0.0004, edge=True))
    p.append(lathe_x([(0.030, -0.150), (0.033, -0.146), (0.033, -0.140)], "Metal", z=0.112, sides=20, edge=True))
    for i in range(4):
        a = 2 * math.pi * i / 4 + math.pi / 4
        p.append(tube_x(0.0028, -0.152, -0.148, "MetalEdge", z=0.112 + 0.022 * math.sin(a), y=0.022 * math.cos(a),
                        sides=8))
    for i in range(3):
        p.append(sphere(0.0035, (0.030 + i * 0.012, -0.0455, 0.148), "Glow", 8, 5))
    for x in (-0.075, 0.060):
        for sy in (1, -1):
            p += screw(x, 0.070, sy * 0.045, 0.0026, sy)
            p += screw(x, 0.150, sy * 0.045, 0.0026, sy)
    # rear grip + trigger
    g, gc, gi = pistol_grip((0.010, 0.062), (-0.026, 0.062), 0.10, 12, 0.032)
    p += g
    p += trigger_group(0.045, 0.062, "Body", 0.012)
    # carry handle with rubber sleeve
    p.append(prism([(-0.060, 0.160), (-0.052, 0.208), (0.088, 0.208), (0.098, 0.160), (0.082, 0.160),
                    (0.075, 0.194), (-0.036, 0.194), (-0.042, 0.160)], 0.022, "Metal", bv=0.0018, seg=2))
    p.append(tube_x(0.0115, -0.030, 0.068, "Grip", z=0.204, sides=14, bv=0.001))
    # front handle on a clamp
    p.append(ring_x(0.0545, 0.060, 0.290, 0.312, "Metal", z=zc, sides=24, bv=0.0006, edge=True))
    p.append(tube_z(0.015, -0.020, zc - 0.052, "Grip", x=0.301, sides=14, bv=0.0012))
    p.append(tube_z(0.0165, -0.026, -0.018, "Metal", x=0.301, sides=14, bv=0.0008))
    p.append(rbox(0.288, 0.314, -0.016, 0.016, zc - 0.062, zc - 0.050, "Metal", bv=0.0012))
    # ammo box + lid + latch + handle
    p.append(rbox(0.080, 0.220, -0.040, 0.040, -0.115, -0.006, "Body", bv=0.004, seg=2))
    for x in (0.105, 0.150, 0.195):
        p.append(rbox(x - 0.004, x + 0.004, -0.0415, 0.0415, -0.108, -0.016, "Body", bv=0.0010))
    p.append(rbox(0.078, 0.222, -0.042, 0.042, -0.008, 0.002, "Metal", bv=0.0018))
    p.append(rbox(0.140, 0.160, -0.0445, -0.0405, -0.030, -0.004, "Metal", bv=0.0008))
    p.append(prism([(0.115, 0.002), (0.120, 0.012), (0.180, 0.012), (0.185, 0.002), (0.178, 0.002), (0.175, 0.008),
                    (0.125, 0.008), (0.122, 0.002)], 0.010, "Metal", y=0.030, bv=0.0008))
    # feed chute: articulated links from the box to the housing
    pts = [(0.165, 0.003), (0.150, 0.025), (0.135, 0.042), (0.115, 0.055), (0.092, 0.062)]
    for (x0, z0), (x1, z1) in zip(pts[:-1], pts[1:]):
        ang = math.degrees(math.atan2(z1 - z0, x1 - x0))
        ln = math.hypot(x1 - x0, z1 - z0)
        seg_ = rbox(-ln * 0.5 - 0.002, ln * 0.5 + 0.002, -0.017, 0.017, -0.009, 0.009, "Metal", bv=0.0012)
        rot(seg_, -ang, "Y")
        move(seg_, ((x0 + x1) / 2, 0, (z0 + z1) / 2))
        p.append(seg_)
        p.append(tube_y(0.0045, 0.037, "MetalEdge", x=x1, z=z1, sides=8))
    return finish_weapon("minigun", p, gc)


def make_lmg():
    """Belt-fed light machine gun: receiver with feed cover (latch, rail, rear sight), ammo box
    with a round counter, belt with links and cartridges, perforated barrel shroud, heavy barrel
    with folding carry handle and flash hider, folded bipod, skeleton stock."""
    mats((0.10, 0.11, 0.10))
    p = []
    g, gc, gi = pistol_grip((0.004, 0.035), (-0.030, 0.035), 0.105, 18, 0.032)
    p += g
    rec = xsec(chamfer_sec(0.023, 0.035, 0.115, 0.004, 0.003), -0.105, 0.200, "Body", bv=0.0)
    rec = cut(rec, [cutter(0.020, 0.120, -0.03, -0.018, 0.074, 0.100),
                    slot_cutter(-0.060, 0.110, 0.088, 0.007, -0.03, -0.018, 6)], pre=(0.0014, 1))
    p.append(rec)
    p.append(rbox(0.018, 0.122, -0.020, 0.010, 0.073, 0.101, "Metal", bv=0.0006))
    p.append(rbox(0.030, 0.100, -0.0205, -0.0195, 0.082, 0.088, "MetalEdge", bv=0.0))
    p.append(prism([(0.040, 0.081), (0.054, 0.081), (0.056, 0.095), (0.040, 0.095)], 0.010, "Metal", y=-0.028,
                   bv=0.0008))                                                              # charging handle
    for sy in (1, -1):
        for x in (-0.090, 0.050, 0.180):
            p += screw(x, 0.045, sy * 0.023, 0.0024, sy, h=0.0009)
    p += trigger_group(0.040, 0.036, "Body", 0.012)
    # feed cover with hinge, latch, rail, rear sight
    p.append(prism([(-0.062, 0.115), (0.140, 0.115), (0.140, 0.129), (-0.050, 0.136), (-0.062, 0.130)], 0.044,
                   "Body", bv=0.0016, seg=1))
    p.append(tube_y(0.0055, 0.052, "Metal", x=0.136, z=0.122, sides=12))
    p.append(rbox(-0.074, -0.060, -0.010, 0.010, 0.112, 0.132, "Metal", bv=0.0012))
    p += picatinny(-0.045, 0.130, 0.1335, w=0.020)
    p += flip_sight(-0.030, 0.1395, front=False, w=0.018, h=0.016)
    # stock
    stk = prism([(-0.105, 0.110), (-0.105, 0.050), (-0.360, 0.035), (-0.370, 0.115)], 0.034, "Polymer", bv=0.0)
    p.append(cut(stk, [cutter_prism([(-0.140, 0.098), (-0.330, 0.103), (-0.330, 0.052), (-0.140, 0.064)],
                                    -0.03, 0.03)], pre=(0.0022, 2)))
    p.append(tube_x(0.010, -0.330, -0.110, "Metal", z=0.081, sides=14))
    p.append(prism([(-0.386, 0.026), (-0.369, 0.030), (-0.369, 0.118), (-0.386, 0.124)], 0.042, "Grip", bv=0.003,
                   seg=2))
    p.append(sling_loop(-0.360, 0.036, 0.0, R=0.0065))
    # ammo box on the left + belt into the feed tray
    p.append(rbox(0.030, 0.150, 0.012, 0.072, -0.080, 0.030, "Polymer", bv=0.004, seg=2))
    for x in (0.055, 0.090, 0.125):
        p.append(rbox(x - 0.003, x + 0.003, 0.011, 0.073, -0.074, 0.024, "Polymer", bv=0.0008))
    p.append(rbox(0.040, 0.140, 0.0715, 0.0735, -0.068, -0.058, "Glow", bv=0.0))
    p.append(rbox(0.082, 0.098, 0.072, 0.076, -0.020, 0.004, "Metal", bv=0.0007))
    for i in range(5):
        x = 0.052 + i * 0.0165
        p.append(tube_y(0.0050, 0.026, "MetalEdge", x=x, z=0.040, y=0.034, sides=8))
        p.append(lathe_x([(0.0050, 0.0), (0.0050, 0.004), (0.0036, 0.009), (0.0, 0.012)], "MetalEdge", sides=8))
        rot(p[-1], 90, "Z")
        move(p[-1], (x, 0.047, 0.040))
        p.append(rbox(x - 0.006, x + 0.006, 0.020, 0.048, 0.033, 0.037, "Metal", bv=0.0))
    # handguard, perforated shroud, barrel, gas tube, flash hider
    p.append(prism([(0.200, 0.038), (0.380, 0.044), (0.380, 0.082), (0.200, 0.082)], 0.050, "Polymer", bv=0.0035,
                   seg=2))
    sh = ring_x(0.0200, 0.0245, 0.200, 0.470, "Metal", z=0.094, sides=16)
    hc = []
    for i in range(3):
        for j in range(2):
            x = 0.392 + i * 0.026 + j * 0.013
            hc.append(cutter_cyl(0.0050, "Y", (x, 0, 0.094 + (0.006 if j else -0.006)), 0.08, 8))
    p.append(cut(sh, hc, edge=True, mat="Metal"))
    p.append(tube_x(0.0135, 0.200, 0.640, "Metal", z=0.094, sides=14))
    p.append(tube_x(0.0055, 0.380, 0.560, "Metal", z=0.066, sides=10))
    p.append(rbox(0.548, 0.572, -0.010, 0.010, 0.060, 0.090, "Metal", bv=0.0012))
    fh = lathe_x([(0.0140, 0.628), (0.0172, 0.634), (0.0172, 0.676), (0.0150, 0.679)], "Metal", z=0.094, sides=16)
    fc = []
    for i in range(4):
        c = cutter(0.650, 0.690, -0.0022, 0.0022, 0.0, 0.03)
        rot(c, 45 + 90 * i, "X")
        move(c, (0, 0, 0.094))
        fc.append(c)
    p.append(cut(fh, fc, bv=0.0005, edge=True, mat="Metal"))
    p.append(tube_x(0.0080, 0.677, 0.6795, "Polymer", z=0.094, sides=12))
    # carry handle (folded), bipod, front sight
    p.append(rbox(0.430, 0.470, -0.012, 0.012, 0.112, 0.122, "Metal", bv=0.0012))
    p.append(prism([(0.400, 0.120), (0.400, 0.146), (0.520, 0.146), (0.520, 0.120), (0.505, 0.120), (0.500, 0.136),
                    (0.420, 0.136), (0.415, 0.120)], 0.018, "Metal", bv=0.0016))
    p.append(tube_x(0.0085, 0.420, 0.500, "Grip", z=0.142, sides=12))
    p.append(rbox(0.600, 0.625, -0.016, 0.016, 0.066, 0.084, "Metal", bv=0.0012))
    for sy in (0.013, -0.013):
        p.append(tube_x(0.0055, 0.455, 0.612, "Metal", z=0.066, y=sy, sides=10))
        p.append(tube_x(0.0042, 0.430, 0.460, "Metal", z=0.066, y=sy, sides=10))
        p.append(sphere(0.0070, (0.428, sy, 0.066), "Grip", 8, 5))
    p.append(rbox(0.620, 0.642, -0.017, 0.017, 0.080, 0.108, "Metal", bv=0.0014))
    p.append(prism([(0.626, 0.108), (0.638, 0.108), (0.636, 0.124), (0.628, 0.124)], 0.0035, "Metal", bv=0.0004))
    for sy in (1, -1):
        p.append(prism([(0.622, 0.106), (0.640, 0.106), (0.637, 0.126), (0.625, 0.126)], 0.0025, "Metal",
                       y=sy * 0.0085, bv=0.0004))
    p.append(sphere(0.0018, (0.632, 0, 0.1245), "Glow", 6, 4))
    return finish_weapon("lmg", p, gc)


def make_gl():
    """Revolving 6-shot grenade launcher: fluted drum with front/rear plates and chamber
    mouths, spring housing cap, top strap rail with a reflex sight, short barrel with front
    ring and ladder sight, vertical foregrip, folding tubular stock."""
    mats((0.13, 0.15, 0.12))
    p = []
    g, gc, gi = pistol_grip((0.004, 0.040), (-0.030, 0.040), 0.10, 16, 0.032)
    p += g
    zc = 0.110
    fr = prism([(-0.062, 0.040), (0.050, 0.040), (0.050, 0.060), (0.222, 0.060), (0.222, 0.168), (0.050, 0.168),
                (0.050, 0.150), (-0.062, 0.122)], 0.036, "Body", bv=0.0)
    p.append(cut(fr, [cutter(0.054, 0.214, -0.05, 0.05, 0.064, 0.164)], pre=(0.0020, 2)))
    p += trigger_group(0.040, 0.041, "Body", 0.012)
    for x, z in ((-0.040, 0.100), (0.020, 0.052), (-0.010, 0.120)):
        p += screw(x, z, 0.018, 0.0024, 1)
        p += screw(x, z, -0.018, 0.0024, -1)
    # drum: 12-sided body with flutes, plates, chamber mouths, axle cap
    drum = lathe_x([(0.012, 0.058), (0.058, 0.058), (0.062, 0.064), (0.062, 0.204), (0.058, 0.210), (0.012, 0.210)],
                   "Body", z=zc, sides=24)
    dcs = []
    for i in range(6):
        a = 2 * math.pi * (i + 0.5) / 6
        c = slot_cutter(0.075, 0.195, 0.0, 0.014, -0.006, 0.006, 6)
        rot(c, 90, "X")
        move(c, (0, 0, 0.062))
        rot(c, math.degrees(a) - 90, "X", (0, 0, 0))
        move(c, (0, 0, zc))
        dcs.append(c)
    p.append(cut(drum, dcs, bv=0.0008, edge=True, mat="Body"))
    for x0 in (0.0565, 0.208):
        p.append(ring_x(0.012, 0.0605, x0, x0 + 0.004, "Metal", z=zc, sides=24, bv=0.0004, edge=True))
    for i in range(6):
        a = 2 * math.pi * i / 6
        y, z = 0.036 * math.cos(a), zc + 0.036 * math.sin(a)
        p.append(ring_x(0.0150, 0.0175, 0.211, 0.2155, "Metal", z=z, y=y, sides=14))
        p.append(tube_x(0.0150, 0.2105, 0.2115, "Polymer", z=z, y=y, sides=14))
    p.append(lathe_x([(0.010, 0.212), (0.012, 0.215), (0.012, 0.222), (0.009, 0.226)], "Metal", z=zc, sides=14,
                     edge=True))
    p.append(lathe_x([(0.016, 0.040), (0.020, 0.046), (0.020, 0.058)], "Metal", z=zc, sides=16, edge=True))
    # barrel + front ring + ladder sight
    p.append(tube_x(0.027, 0.222, 0.430, "Metal", z=zc + 0.012, sides=20))
    p.append(lathe_x([(0.027, 0.424), (0.031, 0.428), (0.031, 0.450), (0.028, 0.453), (0.022, 0.453),
                      (0.022, 0.440)], "Metal", z=zc + 0.012, sides=20, cap_start=False, cap_end=False, edge=True))
    p.append(tube_x(0.022, 0.4505, 0.4515, "Polymer", z=zc + 0.012, sides=16))
    for x in (0.300, 0.360):
        p.append(ring_x(0.027, 0.0295, x, x + 0.006, "Metal", z=zc + 0.012, sides=20))
    p.append(rbox(0.222, 0.436, -0.010, 0.010, zc + 0.036, zc + 0.054, "Body", bv=0.0014))
    p += picatinny(0.060, 0.430, zc + 0.054, w=0.020)
    p.append(rbox(0.050, 0.222, -0.012, 0.012, zc + 0.050, zc + 0.058, "Body", bv=0.0012))
    ladder = prism([(0.395, zc + 0.062), (0.420, zc + 0.062), (0.418, zc + 0.068), (0.398, zc + 0.068)], 0.020,
                   "Metal", bv=0.0006)
    p.append(ladder)
    # vertical foregrip on the barrel
    p.append(rbox(0.310, 0.352, -0.014, 0.014, zc - 0.022, zc - 0.012, "Metal", bv=0.0012))
    fg = lathe_x([(0.0, 0.0), (0.0165, 0.0), (0.0175, 0.010), (0.0155, 0.045), (0.0165, 0.078), (0.0140, 0.085)],
                 "Grip", sides=14)
    rot(fg, -90, "Y")
    move(fg, (0.331, 0, zc - 0.105))
    p.append(fg)
    # folding stock: two tubes, hinge, plate, butt pad
    p.append(rbox(-0.078, -0.054, -0.018, 0.018, 0.044, 0.126, "Metal", bv=0.0016))
    p.append(tube_z(0.0045, 0.040, 0.130, "Metal", x=-0.066, y=-0.0, sides=10))
    for dz in (0.055, 0.115):
        p.append(tube_x(0.0072, -0.300, -0.075, "Body", z=dz, sides=12))
    p.append(rbox(-0.300, -0.288, -0.016, 0.016, 0.044, 0.126, "Polymer", bv=0.0014))
    p.append(prism([(-0.320, 0.028), (-0.300, 0.032), (-0.300, 0.138), (-0.318, 0.142)], 0.040, "Grip", bv=0.003,
                   seg=2))
    p.append(rbox(-0.250, -0.200, -0.006, 0.006, 0.060, 0.110, "Polymer", bv=0.0012))
    p.append(sling_loop(-0.285, 0.040, 0.0, R=0.0060))
    p.append(sling_loop(0.226, 0.060, 0.0, R=0.0060))
    # reflex sight: base, window frame, tinted glass, reticle
    zs = zc + 0.0605
    p.append(rbox(0.074, 0.152, -0.013, 0.013, zs, zs + 0.008, "Metal", bv=0.0008))
    fr2 = prism([(0.120, zs + 0.006), (0.150, zs + 0.006), (0.150, zs + 0.046), (0.120, zs + 0.040)], 0.030, "Body",
                bv=0.0)
    p.append(cut(fr2, [cutter(0.110, 0.160, -0.0115, 0.0115, zs + 0.010, zs + 0.040)], pre=(0.0010, 1)))
    p.append(prism([(0.133, zs + 0.0095), (0.137, zs + 0.0095), (0.137, zs + 0.041), (0.133, zs + 0.040)], 0.023,
                   "Lens", bv=0.0))
    p.append(rbox(0.080, 0.118, -0.011, 0.011, zs + 0.006, zs + 0.016, "Body", bv=0.0012))
    p.append(sphere(0.0018, (0.122, 0, zs + 0.025), "Glow", 6, 4))
    p += screw(0.090, zs + 0.004, -0.013, 0.0018, -1, h=0.0008)
    return finish_weapon("gl", p, gc)


def make_rail():
    """Pulse rifle (futuristic): sculpted white shell with panel cuts, twin vented rails with an
    energy channel, segmented glowing coils, capacitor cells with caps, cooling fins, status
    display, skeleton stock, scope with an illuminated ring."""
    mats((0.82, 0.84, 0.88), body_metal=0.05, body_rough=0.35)
    p = []
    g, gc, gi = pistol_grip((0.004, 0.035), (-0.030, 0.035), 0.105, 16, 0.032)
    p += g
    zc = 0.100
    core = prism([(-0.110, 0.035), (0.260, 0.035), (0.300, 0.065), (0.300, 0.140), (0.250, 0.160),
                  (-0.060, 0.160), (-0.110, 0.130)], 0.060, "Body", bv=0.0)
    cc = [cutter(-0.040, 0.215, -0.04, -0.0285, 0.062, 0.134), cutter(-0.040, 0.215, 0.0285, 0.04, 0.062, 0.134)]
    cc += [cutter(0.226 + i * 0.012, 0.232 + i * 0.012, -0.04, 0.04, 0.068, 0.132) for i in range(4)]
    p.append(cut(core, cc, pre=(0.005, 2)))
    for sy in (1, -1):
        p.append(rbox(-0.036, 0.211, sy * 0.0288 - 0.0012, sy * 0.0288 + 0.0012, 0.066, 0.130, "Polymer", bv=0.0006))
        p.append(rbox(-0.030, 0.205, sy * 0.0302 - 0.0007, sy * 0.0302 + 0.0007, 0.094, 0.100, "Glow", bv=0.0))
        for x in (-0.025, 0.200):
            for z in (0.072, 0.124):
                p += screw(x, z, sy * 0.030, 0.0022, sy, h=0.0008, sides=8)
    p.append(rbox(0.040, 0.100, -0.0312, -0.0298, 0.108, 0.124, "Lens", bv=0.0))           # status display
    for i in range(4):
        p.append(rbox(0.046 + i * 0.013, 0.054 + i * 0.013, -0.0316, -0.0310, 0.112, 0.112 + 0.003 * (i + 1),
                      "Glow", bv=0.0))
    p += trigger_group(0.040, 0.036, "Body", 0.012)
    # stock: open frame + pad
    stk = prism([(-0.110, 0.150), (-0.110, 0.045), (-0.360, 0.040), (-0.380, 0.060), (-0.380, 0.140),
                 (-0.350, 0.150)], 0.036, "Body", bv=0.0)
    p.append(cut(stk, [cutter_prism([(-0.150, 0.135), (-0.150, 0.080), (-0.300, 0.075), (-0.330, 0.090),
                                     (-0.330, 0.135)], -0.03, 0.03)], pre=(0.004, 2)))
    p.append(rbox(-0.392, -0.376, -0.020, 0.020, 0.036, 0.152, "Grip", bv=0.004, seg=2))
    p.append(rbox(-0.300, -0.170, -0.0185, 0.0185, 0.090, 0.098, "Glow", bv=0.0))
    # twin vented rails + energy channel
    for dz in (-0.028, 0.028):
        r_ = prism([(0.290, zc + dz - 0.010), (0.610, zc + dz - 0.007), (0.625, zc + dz),
                    (0.610, zc + dz + 0.007), (0.290, zc + dz + 0.010)], 0.022, "Metal", bv=0.0)
        rcs = [slot_cutter(0.320 + i * 0.045, 0.345 + i * 0.045, zc + dz, 0.0055, -0.02, 0.02, 4) for i in range(6)]
        p.append(cut(r_, rcs, pre=(0.0016, 1)))
    p.append(rbox(0.295, 0.600, -0.003, 0.003, zc - 0.006, zc + 0.006, "Glow", bv=0.0))
    # coils: glowing rings segmented by housings
    for x in (0.34, 0.43, 0.52):
        p.append(lathe_x([(0.040, x), (0.046, x + 0.006), (0.046, x + 0.020), (0.040, x + 0.026)], "Glow",
                         z=zc, sides=16, cap_start=False, cap_end=False))
        p.append(lathe_x([(0.039, x - 0.004), (0.039, x + 0.030)], "Body", z=zc, sides=16, cap_start=False,
                         cap_end=False))
        for k in (0, 1):
            xx = x - 0.005 + k * 0.031
            p.append(ring_x(0.039, 0.049, xx, xx + 0.004, "Metal", z=zc, sides=16))
        for i in range(4):
            a = math.pi / 4 + i * math.pi / 2
            fin = rbox(x + 0.010, x + 0.016, -0.003, 0.003, 0.0, 0.0050, "Metal", bv=0.0)
            rot(fin, math.degrees(a) - 90, "X")
            p.append(move(fin, (0, 0.046 * math.cos(a), zc + 0.046 * math.sin(a))))
    # capacitor cells
    for sy in (0.016, -0.016):
        p.append(tube_x(0.012, 0.29, 0.478, "Body", z=0.045, y=sy, sides=14))
        p.append(tube_x(0.008, 0.478, 0.490, "Glow", z=0.045, y=sy, sides=12))
        p.append(lathe_x([(0.0125, 0.474), (0.0135, 0.478), (0.0135, 0.484), (0.0090, 0.486)], "Metal", z=0.045,
                         y=sy, sides=14, cap_start=False, cap_end=False, edge=True))
        for x in (0.330, 0.400):
            p.append(ring_x(0.0118, 0.0135, x, x + 0.006, "Metal", z=0.045, y=sy, sides=14))
    p.append(rbox(0.292, 0.470, -0.006, 0.006, 0.052, 0.072, "Metal", bv=0.0008))
    # scope on a rail
    zs = 0.195
    p += picatinny(0.000, 0.200, 0.160, w=0.020)
    for x in (0.040, 0.150):
        p += ring_mount(x, zs, 0.1665, 0.016)
    p += scope(-0.030, 0.220, zs, r_tube=0.016, r_obj=0.0235, r_eye=0.020, mat="Body")
    return finish_weapon("rail", p, gc)



WEAPONS = {
    "pistol": make_pistol, "uzi": make_uzi, "shotgun": make_shotgun, "rifle": make_rifle,
    "sniper": make_sniper, "rocket": make_rocket, "minigun": make_minigun, "lmg": make_lmg,
    "gl": make_gl, "rail": make_rail,
}


def build(name):
    TEX.update(nbt.weapon_textures())           # bakes in its own scene: before the reset
    nb.reset_scene()
    obj = WEAPONS[name]()
    used = {obj.data.materials[p.material_index].name for p in obj.data.polygons}
    lo = [min(v.co[i] for v in obj.data.vertices) for i in range(3)]
    hi = [max(v.co[i] for v in obj.data.vertices) for i in range(3)]
    tris = nb.tri_count(obj)
    print("[weapon] %s: %d tris (budget %d), length %.3f m (x %.3f..%.3f), height %.3f (z %.3f..%.3f), "
          "width %.3f, mats %s" % (name, tris, BUDGET[name], hi[0] - lo[0], lo[0], hi[0], hi[2] - lo[2],
                                   lo[2], hi[2], hi[1] - lo[1], sorted(used)))
    return nb.export_glb("w_" + name, texcoords=True)


if __name__ == "__main__":
    for n in sys.argv[1:] or list(WEAPONS):
        build(n)
