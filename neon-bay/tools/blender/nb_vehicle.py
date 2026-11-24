"""Neon Bay - shared kit of the procedural vehicles (gen_cars.py v3, gen_army.py).

Blender side, Z-up: X = forward, Y = left, Z = up, origin on the ground at the centre of the
vehicle. glTF export (export_yup) -> forward +X, up +Y, left = -Z.

What lives here
  * textures      numpy-generated tiling / atlas PNGs (no bake, no download): tyre tread +
                  sidewall normal map, plastic grain normal map, canvas weave normal map,
                  headlamp / blinker atlas, tail-lamp LED pattern, rim + licence-plate atlas.
  * materials     vehicle_materials(): the contract names (Paint Glass Trim Tyre Rim LightFront
                  LightRear) + optional extras (Livery, SirenRed, SirenBlue, Canvas).
  * primitives    every part is a Blender object with ONE material slot and a UV layer;
                  parts are joined with nb.join at the end (box, cyl, lathe, tube, prisms,
                  loft of polygons, surface patches / ribbons projected on a body).
  * wheels        wheel(): tyre (lathe, tread in normal map) + rim (styles) + nuts + brake
                  disc, origin at the hub, axle = local Y in Blender (= local Z in glTF, the
                  game spins wheels with rotation.z). Callipers are NOT in the wheel (they must
                  not spin): brake_caliper() returns a part for the body.

UV conventions (the textured materials):
  Tyre       u around the tyre (TYRE_REPEAT tiles per turn), v across the profile (0..1)
  Trim       box projection, tile TILE["Trim"] metres (grain normal map)
  Canvas     box projection, tile TILE["Canvas"] (weave normal map)
  Rim        constant (0.25, 0.25) = plain metal; v in [0.75, 1] = licence plate (no text:
             blurred blocks that cannot be read)
  LightFront atlas: u < .5 headlamp (reflector bowls + DRL strip), u > .5 & v > .5 amber
             (blinkers), u > .5 & v < .5 plain white (reverse / fog lamps)
  LightRear  LED bars, box projection
"""
import math
import os
import tempfile

import bpy  # noqa: F401  (before bmesh / mathutils)
import bmesh
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

import nb_common as nb

TYRE_REPEAT = 6
TILE = {"Trim": 0.35, "Canvas": 0.6, "LightRear": 0.12, "Tyre": 0.3}
CONST_UV = {"Rim": (0.25, 0.25), "LightFront": (0.75, 0.25)}
PLATE_V = (0.76, 0.99)

_TEX = {}
_DIR = None


# =========================================================================== textures
def _rng(seed):
    return np.random.default_rng(seed)


def fnoise(n, m, sigma, seed):
    """Tileable smooth noise (n rows x m cols), FFT low-pass of white noise, range ~0..1."""
    w = _rng(seed).standard_normal((n, m))
    fy = np.fft.fftfreq(n)[:, None]
    fx = np.fft.fftfreq(m)[None, :]
    g = np.exp(-(fx * fx + fy * fy) * (sigma * sigma) * 2 * math.pi ** 2)
    r = np.real(np.fft.ifft2(np.fft.fft2(w) * g))
    r -= r.min()
    return r / max(r.max(), 1e-9)


def normal_from_height(h, strength):
    """glTF / OpenGL tangent normal map (+Y = +v). h: rows = v from top (v = 1) to bottom."""
    hv = h[::-1]
    dx = (np.roll(hv, -1, 1) - np.roll(hv, 1, 1)) * 0.5
    dy = (np.roll(hv, -1, 0) - np.roll(hv, 1, 0)) * 0.5
    n = np.stack([-dx * strength, -dy * strength, np.ones_like(hv)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return (n * 0.5 + 0.5)[::-1]


def _save(name, arr, mode="RGB", levels=None):
    from PIL import Image
    a = np.clip(arr, 0, 1)
    if levels:
        a = np.round(a * (levels - 1)) / (levels - 1)
    a8 = (a * 255 + 0.5).astype(np.uint8)
    if mode == "L" and a8.ndim == 3:
        a8 = a8[:, :, 0]
    p = os.path.join(_DIR, name + ".png")
    Image.fromarray(a8, mode).save(p, optimize=True, compress_level=9)
    return p


def _uv_grid(n, m):
    """u (cols, 0..1) and v (rows, 1 at top .. 0 at bottom) pixel-centre grids."""
    u = (np.arange(m) + 0.5) / m
    v = 1.0 - (np.arange(n) + 0.5) / n
    return np.meshgrid(u, v)


def _sstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def _tyre_height():
    n = 256
    u, v = _uv_grid(n, n)
    d = np.abs(v - 0.5)
    h = np.zeros_like(u)
    # tread (|d| < .16): blocks between 2 circumferential grooves + slanted sipes
    tread = d < 0.16
    g1 = np.exp(-((d - 0.06) / 0.012) ** 2)
    sip = np.abs(((u * 8 + (v - 0.5) * 2.2 * np.sign(v - 0.5)) % 1.0) - 0.5)
    sip_g = _sstep(0.06, 0.03, sip) * (d > 0.075)
    hb = 1.0 - np.clip(g1 * 1.2 + sip_g * 0.9, 0, 1)
    h = np.where(tread, hb, h)
    # shoulder blocks
    sh = (d >= 0.16) & (d < 0.23)
    lat = _sstep(0.10, 0.05, np.abs(((u * 8 + 0.5) % 1.0) - 0.5))
    h = np.where(sh, 0.85 - lat * 0.8 - (d - 0.16) * 3.0, h)
    # sidewall: two ridges, a raised plain band (no lettering), fine serration near the rim
    sw = d >= 0.23
    rid = np.exp(-((d - 0.27) / 0.008) ** 2) * 0.5 + np.exp(-((d - 0.44) / 0.006) ** 2) * 0.4
    band = _sstep(0.325, 0.335, d) * _sstep(0.385, 0.375, d) * (0.18 + 0.1 * _sstep(0.2, 0.3, np.abs(((u * 2) % 1) - 0.5)))
    ser = (d > 0.46) * (np.abs(((u * 96) % 1.0) - 0.5) < 0.2) * 0.25
    h = np.where(sw, 0.3 + rid + band + ser, h)
    return h


def _plate_rgb(rgb, u, v, v0, v1):
    """Licence plate design inside v in [v0, v1] (full u width): no readable text."""
    inside = (v >= v0) & (v <= v1)
    pu = u
    pv = (v - v0) / (v1 - v0)
    base = np.stack([np.full_like(u, 0.93), np.full_like(u, 0.93), np.full_like(u, 0.88)], -1)
    border = ((pu < 0.025) | (pu > 0.975) | (pv < 0.09) | (pv > 0.91)) & ~((pu < 0.012) | (pu > 0.988) | (pv < 0.03) | (pv > 0.97))
    col = base.copy()
    col[border] = (0.12, 0.12, 0.14)
    strip = (pu > 0.03) & (pu < 0.1) & (pv > 0.12) & (pv < 0.88)
    col[strip] = (0.12, 0.42, 0.33)                      # fictional green region band
    dot = ((pu - 0.065) * 4.0) ** 2 + (pv - 0.62) ** 2 < 0.018
    col[dot & strip] = (0.9, 0.9, 0.85)
    # pseudo characters: blurred random bars (illegible by design)
    r = _rng(7)
    ink = np.zeros_like(u)
    for k in range(7):
        cx = 0.17 + k * 0.115 + (0.03 if k > 2 else 0.0)
        for _ in range(3):
            if r.random() < 0.5:
                x0, x1 = cx + r.uniform(-0.035, 0.0), cx + r.uniform(0.005, 0.04)
                y0, y1 = 0.22 + r.uniform(0, 0.1), 0.62 + r.uniform(0, 0.15)
            else:
                x0, x1 = cx - 0.035, cx + 0.035
                yy = r.uniform(0.25, 0.7)
                y0, y1 = yy, yy + 0.09
            ink += ((pu > x0) & (pu < x1) & (pv > y0) & (pv < y1)).astype(float)
    ink = np.clip(ink, 0, 1)
    # blur (separable box, a few passes) so nothing is readable
    for _ in range(3):
        ink = (np.roll(ink, 1, 1) + ink + np.roll(ink, -1, 1)) / 3
        ink = (np.roll(ink, 1, 0) + ink + np.roll(ink, -1, 0)) / 3
    ink *= 0.85
    col = col * (1 - ink[..., None]) + np.array([0.1, 0.1, 0.12]) * ink[..., None]
    rgb[inside] = col[inside]


def vehicle_textures():
    """Generate (once per process) the vehicle maps; returns {name: png path}."""
    global _DIR
    if _TEX:
        return dict(_TEX)
    _DIR = tempfile.mkdtemp(prefix="nb_veh_")
    # tyre normal map
    _TEX["tyre_n"] = _save("tyre_n", normal_from_height(_tyre_height(), 5.0), levels=64)
    # plastic grain (trim)
    g = fnoise(128, 128, 1.2, 3) * 0.7 + fnoise(128, 128, 4.0, 4) * 0.3
    _TEX["trim_n"] = _save("trim_n", normal_from_height(g, 1.6), levels=32)
    # canvas weave
    u, v = _uv_grid(128, 128)
    wv = np.sin(u * 2 * math.pi * 32) * np.sign(np.sin(v * 2 * math.pi * 16)) * 0.5 + \
        np.sin(v * 2 * math.pi * 32) * np.sign(np.sin(u * 2 * math.pi * 16 + 1.0)) * 0.5
    wv = wv * 0.5 + fnoise(128, 128, 3.0, 9) * 1.2
    _TEX["canvas_n"] = _save("canvas_n", normal_from_height(wv, 1.4), levels=32)
    # headlamp / blinker atlas
    n = 256
    u, v = _uv_grid(n, n)
    rgb = np.ones((n, n, 3))
    hl = u < 0.5
    base = 0.62 + 0.12 * v                                    # reflector housing
    lamp = np.stack([base * 0.92, base * 0.96, base], -1)
    for cx in (0.13, 0.35):
        r = np.hypot((u - cx) * 1.0, (v - 0.58) * 0.5)
        bowl = _sstep(0.11, 0.02, r)
        ring = np.exp(-((r - 0.075) / 0.008) ** 2)
        core = _sstep(0.05, 0.035, r)
        val = np.clip(base + bowl * 0.25 - ring * 0.35 + core * 0.6, 0, 1)
        m = r < 0.11
        for c, k in enumerate((0.97, 0.99, 1.0)):
            lamp[..., c] = np.where(m, val * k, lamp[..., c])
    drl = (v > 0.12) & (v < 0.22) & (u > 0.03) & (u < 0.47)
    lamp[drl] = (1.0, 1.0, 1.0)
    edge = (v < 0.05) | (v > 0.95) | (u < 0.012) | (u > 0.488)
    lamp[edge] = (0.3, 0.3, 0.32)
    rgb[hl] = lamp[hl]
    amb = (u >= 0.5) & (v >= 0.5)
    lines = 0.88 + 0.12 * (np.abs(((v * 24) % 1.0) - 0.5) > 0.12)
    rgb[amb] = np.stack([lines, lines * 0.52, lines * 0.08], -1)[amb]
    wh = (u >= 0.5) & (v < 0.5)
    facet = 0.9 + 0.1 * (np.abs(((u * 16) % 1.0) - 0.5) > 0.1) * (np.abs(((v * 16) % 1.0) - 0.5) > 0.1)
    rgb[wh] = np.stack([facet] * 3, -1)[wh]
    _TEX["lightf"] = _save("lightf", rgb, levels=64)
    # tail lamp LED bars (grey, x red factor)
    u, v = _uv_grid(64, 64)
    bars = 0.55 + 0.45 * _sstep(0.32, 0.22, np.abs(((v * 4) % 1.0) - 0.5))
    cells = 0.9 + 0.1 * (np.abs(((u * 8) % 1.0) - 0.5) > 0.06)
    _TEX["lightr"] = _save("lightr", bars * cells, mode="L", levels=32)
    # rim + plate atlas
    u, v = _uv_grid(256, 256)
    rgb = np.ones((256, 256, 3)) * (0.95 + 0.05 * fnoise(256, 256, 1.5, 11))[..., None]
    _plate_rgb(rgb, u, v, *PLATE_V)
    _TEX["rim"] = _save("rim", rgb, levels=64)
    return dict(_TEX)


# =========================================================================== materials
def _img(path, data=False):
    im = bpy.data.images.load(path, check_existing=True)
    if data:
        im.colorspace_settings.name = "Non-Color"
    return im


def tex_mat(name, color, metallic=0.0, roughness=0.5, img=None, normal=None, nstrength=1.0,
            emission=None, strength=0.0, emit_img=False, alpha=1.0):
    """Principled material with an optional base texture (x color, i.e. baseColorFactor),
    tangent normal map and emissive texture (the same image x emission colour)."""
    mat = nb.material(name, color, metallic=metallic, roughness=roughness, emission=emission,
                      strength=strength, alpha=alpha)
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    if img:
        it = nt.nodes.new("ShaderNodeTexImage")
        it.image = _img(img)
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs[0].default_value = 1.0
        nt.links.new(it.outputs["Color"], mix.inputs[6])
        mix.inputs[7].default_value = tuple(color) + (1.0,)
        nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
        if emit_img and emission is not None:
            mix2 = nt.nodes.new("ShaderNodeMix")
            mix2.data_type = "RGBA"
            mix2.blend_type = "MULTIPLY"
            mix2.inputs[0].default_value = 1.0
            nt.links.new(it.outputs["Color"], mix2.inputs[6])
            mix2.inputs[7].default_value = tuple(emission) + (1.0,)
            nt.links.new(mix2.outputs[2], bsdf.inputs["Emission Color"])
    if normal:
        ni = nt.nodes.new("ShaderNodeTexImage")
        ni.image = _img(normal, data=True)
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = nstrength
        nt.links.new(ni.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def vehicle_materials(paint, paint_metal=0.55, paint_rough=0.3, rim=(0.78, 0.79, 0.81),
                      rim_metal=0.9, rim_rough=0.3, trim=(0.035, 0.036, 0.04), glass_alpha=0.42,
                      extras=()):
    """Contract materials of every vehicle (+ extras: 'Livery', 'SirenRed', 'SirenBlue',
    'Canvas', each given as (name, kwargs))."""
    t = vehicle_textures()
    M = {
        "Paint": nb.material("Paint", paint, metallic=paint_metal, roughness=paint_rough),
        "Glass": nb.material("Glass", (0.025, 0.04, 0.055), metallic=0.3, roughness=0.05, alpha=glass_alpha),
        "Trim": tex_mat("Trim", trim, 0.0, 0.62, normal=t["trim_n"], nstrength=0.5),
        "Tyre": tex_mat("Tyre", (0.03, 0.03, 0.032), 0.0, 0.9, normal=t["tyre_n"], nstrength=1.0),
        "Rim": tex_mat("Rim", rim, rim_metal, rim_rough, img=t["rim"]),
        "LightFront": tex_mat("LightFront", (1.0, 0.97, 0.92), 0.0, 0.2, img=t["lightf"],
                              emission=(1.0, 0.96, 0.88), strength=3.0, emit_img=True),
        "LightRear": tex_mat("LightRear", (0.75, 0.03, 0.03), 0.0, 0.25, img=t["lightr"],
                             emission=(1.0, 0.06, 0.04), strength=2.5, emit_img=True),
    }
    for name, kw in extras:
        if name == "Canvas":
            kw = dict(kw)
            M[name] = tex_mat(name, kw.pop("color"), normal=t["canvas_n"], nstrength=0.8, **kw)
        else:
            kw = dict(kw)
            M[name] = nb.material(name, kw.pop("color"), **kw)
    return M


# =========================================================================== parts
MATS = {}          # name -> material of the vehicle being built (set by the generators)


def part(name, verts, faces, mat, uv=None, smooth=None):
    """Mesh object with one material. uv: None (auto, see uv_auto), (u, v) constant, or a
    list of per-face lists of (u, v)."""
    obj = nb.mesh_object(name, verts, faces, [MATS[mat]])
    obj["mat"] = mat
    if uv is not None:
        lay = obj.data.uv_layers.new(name="UVMap")
        if isinstance(uv, tuple):
            for d in lay.data:
                d.uv = uv
        else:
            for p, fu in zip(obj.data.polygons, uv):
                for li, uvv in zip(p.loop_indices, fu):
                    lay.data[li].uv = uvv
    if smooth is not None:
        nb.auto_smooth(obj, smooth)
    return obj


def obj_part(obj, mat):
    obj["mat"] = mat
    if not obj.data.materials:
        obj.data.materials.append(MATS[mat])
    return obj


def uv_auto(obj):
    """Fill the UV layer if missing: box projection (tiling maps) or a constant."""
    me = obj.data
    if me.uv_layers.get("UVMap"):
        return
    lay = me.uv_layers.new(name="UVMap")
    names = [m.name for m in me.materials]
    for p in me.polygons:
        mn = names[p.material_index] if names else ""
        if mn in TILE:
            t = TILE[mn]
            nx, ny, nz = (abs(c) for c in p.normal)
            for li in p.loop_indices:
                co = me.vertices[me.loops[li].vertex_index].co
                if nz >= nx and nz >= ny:
                    a, b = co.x, co.y
                elif nx >= ny:
                    a, b = co.y, co.z
                else:
                    a, b = co.x, co.z
                lay.data[li].uv = (a / t, b / t)
        else:
            c = CONST_UV.get(mn, (0.5, 0.5))
            for li in p.loop_indices:
                lay.data[li].uv = c


def fix_normals(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    return obj


def bevel(obj, width, seg=1, angle=35):
    if width > 0:
        m = nb.add_bevel(obj, width, seg, angle)
        m.miter_outer = "MITER_ARC" if seg > 1 else "MITER_SHARP"
        nb.apply_modifiers(obj)
    return obj


def box(x0, x1, y0, y1, z0, z1, mat, bv=0.0, seg=1, name="Box", smooth=35):
    o = nb.box(name, (x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), MATS[mat])
    obj_part(o, mat)
    bevel(o, bv, seg)
    nb.auto_smooth(o, smooth)
    return o


def cbox(c, size, mat, bv=0.0, seg=1, rot=None, name="Box", smooth=35):
    """Box of size (sx, sy, sz) centred on c, optional rotation (Euler XYZ radians, about c)."""
    o = box(-size[0] / 2, size[0] / 2, -size[1] / 2, size[1] / 2, -size[2] / 2, size[2] / 2, mat, bv, seg, name, smooth)
    m = Matrix.Translation(Vector(c))
    if rot:
        from mathutils import Euler
        m = m @ Euler(rot, "XYZ").to_matrix().to_4x4()
    o.data.transform(m)
    return o


def cyl(r, length, c, axis, mat, sides=12, r2=None, caps=(True, True), name="Cyl", smooth=40, bv=0.0):
    """Cylinder / cone centred on c along 'X' | 'Y' | 'Z' (r -> r2 from - to + end)."""
    r2 = r if r2 is None else r2
    prof = [(r, -length / 2), (r2, length / 2)]
    verts, faces = nb.lathe(prof, sides, axis="Z", cap_start=caps[0], cap_end=caps[1])
    o = part(name, verts, faces, mat)
    fix_normals(o)
    rotm = {"X": Matrix.Rotation(math.pi / 2, 4, "Y"), "Y": Matrix.Rotation(-math.pi / 2, 4, "X"),
            "Z": Matrix.Identity(4)}[axis]
    o.data.transform(Matrix.Translation(Vector(c)) @ rotm)
    bevel(o, bv)
    nb.auto_smooth(o, smooth)
    return o


def lathe(profile, sides, c, axis, mat, caps=(False, False), name="Lathe", smooth=40, fix=True, phase=0.0,
          flip=False):
    """Revolve [(r, h)] around axis through c. axis 'Y' = +h along +Y. Without fix, a profile
    going up in h faces the axis (inside of a barrel); flip=True for discs / caps whose
    profile runs from a large to a small radius and must face +h."""
    verts, faces = nb.lathe(profile, sides, axis="Z", cap_start=caps[0], cap_end=caps[1])
    if flip:
        faces = [tuple(reversed(f)) for f in faces]
    if phase:
        verts = [tuple(Matrix.Rotation(phase, 3, "Z") @ Vector(v)) for v in verts]
    o = part(name, verts, faces, mat)
    if fix:
        fix_normals(o)
    rotm = {"X": Matrix.Rotation(math.pi / 2, 4, "Y"), "Y": Matrix.Rotation(-math.pi / 2, 4, "X"),
            "Z": Matrix.Identity(4)}[axis]
    o.data.transform(Matrix.Translation(Vector(c)) @ rotm)
    nb.auto_smooth(o, smooth)
    return o


def tube(pts, r, mat, sides=8, caps=True, name="Tube", smooth=50):
    """Swept circle along a polyline (parallel-transport frames)."""
    P = [Vector(p) for p in pts]
    n = len(P)
    tans = []
    for i in range(n):
        a = P[max(i - 1, 0)]
        b = P[min(i + 1, n - 1)]
        tans.append((b - a).normalized())
    up = Vector((0, 0, 1)) if abs(tans[0].z) < 0.9 else Vector((1, 0, 0))
    nrm = tans[0].cross(up).normalized()
    verts, faces = [], []
    radii = r if isinstance(r, (list, tuple)) else [r] * n
    for i in range(n):
        t = tans[i]
        nrm = (nrm - t * nrm.dot(t)).normalized()
        bi = t.cross(nrm)
        # keep the section size constant through bends
        k = 1.0
        if 0 < i < n - 1:
            d0 = (P[i] - P[i - 1]).normalized()
            d1 = (P[i + 1] - P[i]).normalized()
            k = 1.0 / max(0.5, math.sqrt((1 + d0.dot(d1)) / 2))
        for s in range(sides):
            a = 2 * math.pi * s / sides
            off = nrm * math.cos(a) + bi * math.sin(a)
            # stretch only in the bend plane
            if k != 1.0:
                bend = (P[i + 1] - P[i]).normalized() - (P[i] - P[i - 1]).normalized()
                if bend.length > 1e-6:
                    bend = (bend - t * bend.dot(t)).normalized()
                    off = off + bend * off.dot(bend) * (k - 1)
            verts.append(tuple(P[i] + off * radii[i]))
    for i in range(n - 1):
        for s in range(sides):
            s2 = (s + 1) % sides
            faces.append((i * sides + s, i * sides + s2, (i + 1) * sides + s2, (i + 1) * sides + s))
    if caps:
        faces.append(tuple(reversed(range(sides))))
        faces.append(tuple((n - 1) * sides + s for s in range(sides)))
    o = part(name, verts, faces, mat)
    fix_normals(o)
    nb.auto_smooth(o, smooth)
    return o


def prism(pts, a0, a1, axis, mat, bv=0.0, seg=1, name="Prism", smooth=35, angle=35):
    """Polygon extruded along an axis. axis 'Y': pts are (x, z), from y=a0 to a1;
    'X': pts are (y, z); 'Z': pts are (x, y)."""
    n = len(pts)
    verts = []
    for a in (a0, a1):
        for p, q in pts:
            if axis == "Y":
                verts.append((p, a, q))
            elif axis == "X":
                verts.append((a, p, q))
            else:
                verts.append((p, q, a))
    faces = [tuple(range(n)), tuple(n + i for i in reversed(range(n)))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    o = part(name, verts, faces, mat)
    fix_normals(o)
    if bv:
        m = nb.add_bevel(o, bv, seg, angle)
        m.miter_outer = "MITER_ARC" if seg > 1 else "MITER_SHARP"
        nb.apply_modifiers(o)
    nb.auto_smooth(o, smooth)
    return o


def loft(sections, mat, caps=True, bv=0.0, seg=1, name="Loft", smooth=35, angle=35):
    """sections: [(x, [(y, z), ...]), ...] with the same point count (closed polygons)."""
    n = len(sections[0][1])
    verts, faces = [], []
    for x, pts in sections:
        verts += [(x, y, z) for y, z in pts]
    S = len(sections)
    for i in range(S - 1):
        for k in range(n):
            k2 = (k + 1) % n
            faces.append((i * n + k, i * n + k2, (i + 1) * n + k2, (i + 1) * n + k))
    if caps:
        faces.append(tuple(reversed(range(n))))
        faces.append(tuple((S - 1) * n + k for k in range(n)))
    o = part(name, verts, faces, mat)
    fix_normals(o)
    if bv:
        m = nb.add_bevel(o, bv, seg, angle)
        m.miter_outer = "MITER_ARC" if seg > 1 else "MITER_SHARP"
        nb.apply_modifiers(o)
    nb.auto_smooth(o, smooth)
    return o


def mirror_y(obj, name=None):
    """Copy of obj mirrored across the XZ plane (left <-> right), winding fixed."""
    me = obj.data.copy()
    me.transform(Matrix.Scale(-1, 4, Vector((0, 1, 0))))
    me.flip_normals()
    o = nb.link(bpy.data.objects.new(name or obj.name + "_R", me))
    for k in obj.keys():
        o[k] = obj[k]
    return o


# --------------------------------------------------------------------------- surface tools
class Surface:
    """BVH of a body mesh for ray-casting details onto it (object at the origin)."""

    def __init__(self, obj):
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bm.transform(obj.matrix_world)
        self.bvh = BVHTree.FromBMesh(bm)
        bm.free()

    def hit(self, origin, direction):
        loc, nrm, idx, dist = self.bvh.ray_cast(Vector(origin), Vector(direction).normalized())
        return (loc, nrm) if loc is not None else (None, None)

    def side(self, x, z, s=1, start=3.0):
        """Point on the left (s=+1) / right (s=-1) side at (x, z), casting towards the centre."""
        return self.hit((x, s * start, z), (0, -s, 0))

    def front(self, y, z, s=1, start=8.0):
        """Point on the front (s=+1) / rear (s=-1) at (y, z)."""
        return self.hit((s * start, y, z), (-s, 0, 0))

    def top(self, x, y, start=5.0):
        return self.hit((x, y, start), (0, 0, -1))


def patch(surf, grid_fn, nu, nv, offset, mat, uv_rect=(0, 0, 1, 1), name="Patch", depth=0.0,
          smooth=60, uv_flip_u=False):
    """Surface patch conforming to a body: grid_fn(a, b) -> (origin, direction) of a ray for
    a, b in [0, 1]; the hit points are pushed out by `offset` along the normal. depth > 0
    adds a skirt going back into the body (closes the edge). UV: rect (u0, v0, u1, v1)."""
    pts = []
    for j in range(nv + 1):
        row = []
        for i in range(nu + 1):
            a, b = i / nu, j / nv
            o, d = grid_fn(a, b)
            loc, nrm = surf.hit(o, d)
            if loc is None:
                return None
            if nrm.dot(Vector(d)) > 0:
                nrm = -nrm
            row.append((loc + nrm * offset, nrm))
        pts.append(row)
    verts, faces, uvs = [], [], []
    u0, v0, u1, v1 = uv_rect

    def uvat(i, j):
        a = i / nu
        if uv_flip_u:
            a = 1 - a
        return (u0 + (u1 - u0) * a, v0 + (v1 - v0) * j / nv)
    for j in range(nv + 1):
        for i in range(nu + 1):
            verts.append(tuple(pts[j][i][0]))
    W = nu + 1
    for j in range(nv):
        for i in range(nu):
            f = (j * W + i, j * W + i + 1, (j + 1) * W + i + 1, (j + 1) * W + i)
            faces.append(f)
            uvs.append([uvat(i, j), uvat(i + 1, j), uvat(i + 1, j + 1), uvat(i, j + 1)])
    if depth > 0:
        ring = [(i, 0) for i in range(nu)] + [(nu, j) for j in range(nv)] + \
               [(i, nv) for i in range(nu, 0, -1)] + [(0, j) for j in range(nv, 0, -1)]
        base = len(verts)
        for (i, j) in ring:
            p, nrm = pts[j][i]
            verts.append(tuple(p - nrm * (offset + depth)))
        R = len(ring)
        for k in range(R):
            i0, j0 = ring[k]
            i1, j1 = ring[(k + 1) % R]
            faces.append((j0 * W + i0, base + k, base + (k + 1) % R, j1 * W + i1))
            uvs.append([uvat(i0, j0)] * 4)
    o = part(name, verts, faces, mat, uv=uvs)
    # orient outwards: compare with the first ray direction
    me = o.data
    me.update()
    o0, d0 = grid_fn(0.5, 0.5)
    if me.polygons and me.polygons[(nv // 2) * nu + nu // 2].normal.dot(Vector(d0)) > 0:
        me.flip_normals()
    nb.auto_smooth(o, smooth)
    return o


def ribbon(points, normals, width, mat, name="Ribbon"):
    """Flat strip through points (offset already applied), lying on the surface (normals)."""
    verts, faces = [], []
    n = len(points)
    for i in range(n):
        p, nr = Vector(points[i]), Vector(normals[i])
        t = (Vector(points[min(i + 1, n - 1)]) - Vector(points[max(i - 1, 0)])).normalized()
        b = nr.cross(t).normalized() * width / 2
        verts += [tuple(p - b), tuple(p + b)]
    for i in range(n - 1):
        faces.append((2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2))
    o = part(name, verts, faces, mat)
    me = o.data
    me.update()
    if me.polygons and me.polygons[0].normal.dot(Vector(normals[0])) < 0:
        me.flip_normals()
    nb.auto_smooth(o, 60)
    return o


def seam(surf, ray_list, width, offset, mat, name="Seam"):
    """Panel gap line: rays [(origin, dir)] -> ribbon slightly above the skin."""
    pts, nrs = [], []
    for o, d in ray_list:
        loc, nrm = surf.hit(o, d)
        if loc is None:
            continue
        if nrm.dot(Vector(d)) > 0:
            nrm = -nrm
        pts.append(loc + nrm * offset)
        nrs.append(nrm)
    if len(pts) < 2:
        return None
    return ribbon(pts, nrs, width, mat, name)


# --------------------------------------------------------------------------- digits
# 7-segment stencil digits (gaps between segments = stencil bridges): a, b, c, d, e, f, g
_SEG = {"0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd",
        "6": "afgedc", "7": "abc", "8": "abcdefg", "9": "abcdfg", "-": "g"}


def stencil(text, origin, right, up, height, mat, normal_off=0.003, name="Stencil"):
    """Flat stencil digits as quads (origin = lower-left of the first glyph, in the plane
    spanned by the unit vectors right / up, facing right x up)."""
    o, R, U = Vector(origin), Vector(right).normalized(), Vector(up).normalized()
    N = R.cross(U).normalized()
    o = o + N * normal_off
    w, t, gap = height * 0.5, height * 0.13, height * 0.05
    seg = {"a": ((gap, height - t), (w - gap, height)), "g": ((gap, height / 2 - t / 2), (w - gap, height / 2 + t / 2)),
           "d": ((gap, 0), (w - gap, t)), "f": ((0, height / 2 + gap), (t, height - gap)),
           "b": ((w - t, height / 2 + gap), (w, height - gap)), "e": ((0, gap), (t, height / 2 - gap)),
           "c": ((w - t, gap), (w, height / 2 - gap))}
    verts, faces = [], []
    x = 0.0
    for ch in text:
        if ch == " ":
            x += w * 0.8
            continue
        for s in _SEG.get(ch, ""):
            (a0, b0), (a1, b1) = seg[s]
            k = len(verts)
            for aa, bb in ((a0, b0), (a1, b0), (a1, b1), (a0, b1)):
                verts.append(tuple(o + R * (x + aa) + U * bb))
            faces.append((k, k + 1, k + 2, k + 3))
        x += w * 1.45
    if not verts:
        return None
    return part(name, verts, faces, mat)


# =========================================================================== wheels
def wheel(name, R, width, rim_r, loc, side, style="alloy5", segs=18, disc=True, nuts=5,
          tyre_mat="Tyre", rim_mat="Rim", disc_mat="Rim", hub_mat="Rim"):
    """Tyre + rim + nuts (+ brake disc), origin at the hub, outer face towards side*Y.
    style: alloy5 | sport | suv6 | steel | army."""
    h = width / 2
    parts = []
    # ---- tyre (UV: u around, v across)
    bulge = 0.012 if style != "army" else 0.03
    prof = [(rim_r + 0.006, -h * 0.78), (rim_r + (R - rim_r) * 0.45, -h - bulge), (R - 0.035, -h * 0.97),
            (R - 0.010, -h * 0.84), (R, -h * 0.62), (R, h * 0.62), (R - 0.010, h * 0.84),
            (R - 0.035, h * 0.97), (rim_r + (R - rim_r) * 0.45, h + bulge), (rim_r + 0.006, h * 0.78)]
    vs = [0.0, 0.12, 0.23, 0.30, 0.36, 0.64, 0.70, 0.77, 0.88, 1.0]
    np_ = len(prof)
    verts, faces, uvs = [], [], []
    for s in range(segs):
        a = 2 * math.pi * s / segs
        for r, y in prof:
            verts.append((r * math.cos(a), y, r * math.sin(a)))
    for s in range(segs):
        s2 = (s + 1) % segs
        ua, ub = TYRE_REPEAT * s / segs, TYRE_REPEAT * (s + 1) / segs
        for i in range(np_ - 1):
            faces.append((s * np_ + i, s * np_ + i + 1, s2 * np_ + i + 1, s2 * np_ + i))
            uvs.append([(ua, vs[i]), (ua, vs[i + 1]), (ub, vs[i + 1]), (ub, vs[i])])
    t = part(name + "_tyre", verts, faces, tyre_mat, uv=uvs)
    parts.append(t)
    # ---- rim barrel (lathe; outer face at +y)
    lip = rim_r + 0.008
    barrel = [(rim_r - 0.012, -h * 0.80), (rim_r + 0.004, -h * 0.80), (rim_r - 0.004, -h * 0.70),
              (rim_r - 0.022, -h * 0.55), (rim_r - 0.022, h * 0.62), (rim_r - 0.006, h * 0.74),
              (lip, h * 0.80), (rim_r - 0.004, h * 0.88)]
    if style == "army":
        barrel = [(rim_r - 0.01, -h * 0.80), (rim_r + 0.006, -h * 0.80), (rim_r - 0.02, -h * 0.6),
                  (rim_r - 0.02, h * 0.6), (rim_r + 0.006, h * 0.80), (rim_r - 0.01, h * 0.84)]
    parts.append(lathe(barrel, segs, (0, 0, 0), "Y", rim_mat, name=name + "_barrel", fix=False, smooth=50))
    face_y = h * 0.52
    # ---- disc / centre
    if style in ("steel", "army"):
        # pressed steel disc with vent holes (as dark recesses) + hub cap
        dish = [(rim_r - 0.022, face_y - 0.02), (rim_r * 0.72, face_y + 0.01), (rim_r * 0.45, face_y + 0.03),
                (0.09 if style == "army" else 0.075, face_y + 0.04)]
        parts.append(lathe(dish, segs, (0, 0, 0), "Y", rim_mat, name=name + "_dish", fix=False, smooth=40, flip=True))
        if style == "army":
            hub = [(0.10, face_y + 0.04), (0.085, face_y + 0.10), (0.06, face_y + 0.11), (0.0, face_y + 0.11)]
        else:
            hub = [(0.075, face_y + 0.04), (0.07, face_y + 0.06), (0.04, face_y + 0.075), (0.0, face_y + 0.078)]
        parts.append(lathe(hub, 12, (0, 0, 0), "Y", hub_mat, name=name + "_hub", fix=False, smooth=40, flip=True))
        holes = 6 if style == "steel" else 0
        for k in range(holes):
            a = 2 * math.pi * (k + 0.5) / holes
            rr = rim_r * 0.6
            c = (rr * math.cos(a), face_y + 0.024, rr * math.sin(a))
            parts.append(cyl(0.03, 0.012, c, "Y", "Trim", sides=8, caps=(False, True), name=name + "_hole"))
        if style == "army":   # bead-lock ring bolts + 8 hub bolts
            for k in range(12):
                a = 2 * math.pi * k / 12
                rr = rim_r - 0.012
                parts.append(cyl(0.011, 0.02, (rr * math.cos(a), h * 0.82, rr * math.sin(a)), "Y", hub_mat, sides=6,
                                 caps=(False, True), name=name + "_bolt"))
            nr = 0.078
            for k in range(8):
                a = 2 * math.pi * k / 8
                parts.append(cyl(0.012, 0.03, (nr * math.cos(a), face_y + 0.06, nr * math.sin(a)), "Y", hub_mat,
                                 sides=6, caps=(False, True), name=name + "_nut"))
            nuts = 0
    else:
        hubr = 0.072
        hub = [(hubr + 0.006, face_y - 0.01), (hubr, face_y + 0.025), (0.04, face_y + 0.035), (0.0, face_y + 0.035)]
        parts.append(lathe(hub, 12, (0, 0, 0), "Y", hub_mat, name=name + "_hub", fix=False, smooth=40, flip=True))
        n_sp, twin, sw0, sw1 = {"alloy5": (5, True, 0.036, 0.024), "sport": (10, False, 0.024, 0.016),
                                "suv6": (6, False, 0.05, 0.036)}[style]
        offs = (-0.11, 0.11) if twin else (0.0,)
        for k in range(n_sp):
            for off in offs:
                a = 2 * math.pi * k / n_sp + off + 0.3
                rot = Matrix.Rotation(a, 3, "Y")
                r0, r1 = hubr - 0.004, rim_r - 0.016
                st = 0.022
                cs = []
                for rx, wd, yy in ((r0, sw0, face_y + 0.02), (r1, sw1, h * 0.70)):
                    for dy in (-st / 2, st / 2):
                        for dz in (-wd / 2, wd / 2):
                            dz2 = dz + (-off * rx * 0.5 if twin else 0.0)
                            cs.append(tuple(rot @ Vector((rx, yy + dy, dz2))))
                bx = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (1, 5, 7, 3), (0, 2, 6, 4)]
                sp = part(name + "_spoke", cs, bx, rim_mat)
                fix_normals(sp)
                nb.auto_smooth(sp, 40)
                parts.append(sp)
    # ---- lug nuts
    for k in range(nuts):
        a = 2 * math.pi * k / nuts
        rr = 0.05
        parts.append(cyl(0.011, 0.022, (rr * math.cos(a), face_y + 0.035, rr * math.sin(a)), "Y", hub_mat,
                         sides=6, caps=(False, True), name=name + "_nut", smooth=20))
    # ---- brake disc (spins with the wheel; the calliper is a body part)
    if disc:
        dr = rim_r - 0.045
        dprof = [(0.085, h * 0.05), (dr, h * 0.05), (dr, -h * 0.25), (0.085, -h * 0.25)]
        parts.append(lathe(dprof, 14, (0, 0, 0), "Y", disc_mat, caps=(False, False), name=name + "_disc", fix=False,
                           smooth=30))
    for p in parts:
        uv_auto(p)
    obj = nb.join(parts, name)
    if side < 0:
        obj.data.transform(Matrix.Scale(-1, 4, Vector((0, 1, 0))))
        obj.data.flip_normals()
    nb.auto_smooth(obj, 40)
    obj.data.name = "mesh_" + name          # three.js names child meshes after the mesh:
    obj.location = loc                      # keep them from matching /^Wheel/ too
    return obj


def brake_caliper(x, y_face, z, R_disc, side, mat, h=0.06):
    """Calliper block hugging the top-rear of the disc (body part: does not spin)."""
    a = math.radians(125)
    cx, cz = x + math.cos(a) * R_disc * 0.82, z + math.sin(a) * R_disc * 0.82
    o = cbox((cx, y_face, cz), (0.11, h, 0.065), mat, bv=0.012, rot=(0, -(a - math.pi / 2), 0), name="Caliper")
    return o


# =========================================================================== finishing
def finish(parts, name="Body", smooth=None):
    parts = [p for p in parts if p is not None]
    for p in parts:
        uv_auto(p)
    obj = nb.join(parts, name)
    if smooth:
        nb.auto_smooth(obj, smooth)
    obj.data.name = "mesh_" + name
    return obj


def report(label, objs, budget):
    tris = sum(nb.tri_count(o) for o in objs)
    mats = sorted({m.name for o in objs for m in o.data.materials})
    print("[vehicle] %s: %d tris (budget %d), %d materials %s" % (label, tris, budget, len(mats), mats))
    return tris
