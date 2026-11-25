"""Neon Bay - landmarks of the city (invented monuments) and sports equipment.

    python3 tools/blender/gen_landmarks.py                  # every model below
    python3 tools/blender/gen_landmarks.py lm_statue court  # some models (id or short name)
    python3 tools/blender/gen_landmarks.py --sheet          # preview sheets only (from models/*.glb)
    python3 tools/blender/gen_landmarks.py --sheet lm_statue
    NB_BACKFACE=1 python3 tools/blender/gen_landmarks.py --sheet   # back faces drawn red (normal check)

Models (models/<id>.glb + .glb.js), all original designs, no real names, no brands:

  lm_statue          "Statue of Light": draped neoclassical woman raising a torch (flame =
                     emissive `Glow`), 5-ray crown, tablet engraved "NB", verdigris patina, on a
                     square granite pedestal standing on a 7-point star fort, on a small rocky
                     islet with a wooden pier.  Real scale 1:1, 1 unit = 1 m: water level y=0,
                     torch flame tip ~88.5 m.  Islet ~88 m across (pier included).
  lm_palace          "Presidential palace": white neoclassical central block + two wings,
                     Ionic portico (6 columns) with pediment, windows with pediments, roof
                     balustrade, hipped roof, flag mast with an invented flag (neon blue, pink
                     star), lawn with paths, entrance gate + front railing, fountain.
                     Real scale: building 88 m wide, lawn 110 x 80 m, flag top ~30 m.
  prop_basket_hoop   portable basketball hoop (rim 3.05 m), diamond net in thin geometry
  prop_basket_court  basketball court floor 28 x 15 m (+2 m run-off), lines in the texture
  prop_soccer_goal   7.32 x 2.44 m goal with a strand net
  prop_soccer_field  90 x 56 m pitch (+3 m run-off), mowing stripes and lines in the texture
  prop_boxing_ring   6.1 m ring: 4 posts, 4 ropes, canvas mat, colored corner pads, steps,
                     lighting truss on 4 towers with 8 spotlights (`Glow` lenses)
  prop_ball_basket   basketball (r 0.12 m), pebbled rubber normal map + seams in geometry
  prop_ball_soccer   football (r 0.11 m), 32 puffy panels (truncated icosahedron)
  prop_stadium_stand stand module 10 m wide (x -5..5, tiles side by side along X),
                     12 rows of colored seats, faces +Z (glTF) = the field

Conventions: Blender Z-up, exported with export_yup (glTF +Y up), metres, origin on the ground
(water level for the statue) at the centre of the footprint. "Front" faces glTF +Z
(= Blender -Y): palace facade, hoop rim, goal mouth, stand seats.

Materials: PBR, clear names (Stone, Marble, Patina, Metal, Glow, Grass, Wood, Rope, Canvas...).
Avoid names containing "paint", "glass", "rim", "trim", "metal", "tyre" unless that is meant:
the game's glbMat() changes metalness/roughness of those (Metal -> shiny metal, Glass -> glossy).
Tileable textures are baked procedurally in Cycles (nb_textures helpers, 256 px) and are light
neutral greys multiplied by the material colour, like the humans / weapons. The court, pitch
textures (512 px) are full-colour "printed" maps (baseColorFactor = white). UVs: box projection
at world scale (TILE per material), planar for the court / pitch tops.
Parts that use no texture are exported in a separate mesh without UVs (smaller files).
Every part is a closed solid or an explicitly outward-oriented surface; materials are exported
single-sided (back-face culling on), like the game's Phong materials.
"""
import math
import os
import random
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402,F401
import bmesh  # noqa: E402
from mathutils import Vector, Matrix, Quaternion  # noqa: E402
import numpy as np  # noqa: E402

import nb_common as nb  # noqa: E402
import nb_textures as nbt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PREVIEWS = os.path.join(HERE, "previews")
TEX = {}
M = {}
# world size of one texture tile, metres (box projection)
TILE = {"Marble": 4.0, "Stone": 3.0, "Patina": 6.0, "Grass": 4.0, "Rock": 5.0, "Concrete": 2.5,
        "Canvas": 1.2, "Rubber": 0.05, "Wood": 1.5, "Hedge": 2.0}
BUDGET = {"lm_statue": 15000, "lm_palace": 15000, "prop_basket_hoop": 4000, "prop_basket_court": 4000,
          "prop_soccer_goal": 4000, "prop_soccer_field": 4000, "prop_boxing_ring": 8000,
          "prop_ball_basket": 4000, "prop_ball_soccer": 4000, "prop_stadium_stand": 8000}
UP = Vector((0, 0, 1))


# =========================================================================== textures
def _floor(a):
    return nbt.X._math("FLOOR", a)


def _hash(a, b):
    return nbt.frac(nbt.sin(a * 12.9898 + b * 78.233) * 43758.5453)


def _marble(u, v):
    vec, w = nbt.torus(u, v, 1.0, 1.0, 3.0)
    n = nbt.noise(vec, w, scale=1.3, detail=5, rough=0.6, distortion=0.4)
    vec2, w2 = nbt.torus(u, v, 2.5, 2.5, 8.0)
    n2 = nbt.noise(vec2, w2, scale=1.5, detail=3)
    vein = 1.0 - nbt.smoothstep(0.0, 0.10, nbt.fabs(nbt.sin((u + v + n * 1.6) * (2 * math.pi * 2))))
    vein2 = 1.0 - nbt.smoothstep(0.0, 0.05, nbt.fabs(nbt.sin((u * 2.0 - v + n2 * 1.2) * (2 * math.pi * 3))))
    return [0.95 - vein * 0.13 - vein2 * 0.06 + (n2 - 0.5) * 0.05]


def _stone_parts(u, v):
    rows, cols = 6, 3                       # tile 3 m: blocks 1 m x 0.5 m, running bond
    r = v * rows
    rf, ri = nbt.frac(r), _floor(r)
    off = nbt.frac(ri * 0.5)
    c = u * cols + off
    cf = c - _floor(c)
    cid = nbt.frac(_floor(c) * (1.0 / cols)) * cols      # block id wraps with the tile
    dy = nbt.vmin(rf, 1.0 - rf) * (1.0 / rows)
    dx = nbt.vmin(cf, 1.0 - cf) * (1.0 / cols)
    d = nbt.vmin(dx, dy)
    return d, _hash(cid + 1.0, ri + 3.0)


def _stone_h(u, v):
    d, _ = _stone_parts(u, v)
    return nbt.smoothstep(0.002, 0.010, d)


def _stone(u, v):
    d, hsh = _stone_parts(u, v)
    vec, w = nbt.torus(u, v, 2.0, 2.0, 5.0)
    fine = nbt.noise(vec, w, scale=2.0, detail=4, rough=0.6) - 0.5
    mortar = 1.0 - nbt.smoothstep(0.002, 0.006, d)
    return [0.88 + (hsh - 0.5) * 0.10 + fine * 0.08 - mortar * 0.28]


def _patina(u, v):
    vec, w = nbt.torus(u, v, 3.0, 0.45, 1.0)          # vertical rain streaks
    streak = nbt.noise(vec, w, scale=1.6, detail=3)
    vec2, w2 = nbt.torus(u, v, 1.4, 1.4, 5.0)
    mott = nbt.noise(vec2, w2, scale=2.0, detail=4, rough=0.6)
    vec3, w3 = nbt.torus(u, v, 6.0, 6.0, 9.0)
    fine = nbt.noise(vec3, w3, scale=2.0, detail=2)
    return [0.86 + (mott - 0.5) * 0.22 - nbt.smoothstep(0.52, 0.72, streak) * 0.14 + (fine - 0.5) * 0.06]


def _grass(u, v):
    vec, w = nbt.torus(u, v, 9.0, 9.0, 2.0)
    fine = nbt.noise(vec, w, scale=2.0, detail=2)
    vec2, w2 = nbt.torus(u, v, 1.2, 1.2, 6.0)
    patch = nbt.noise(vec2, w2, scale=1.5, detail=3)
    return [0.84 + (fine - 0.5) * 0.30 + (patch - 0.5) * 0.22]


def _concrete(u, v):
    vec, w = nbt.torus(u, v, 1.5, 1.5, 4.0)
    mott = nbt.noise(vec, w, scale=1.8, detail=4, rough=0.6)
    vec2, w2 = nbt.torus(u, v, 3.0, 3.0, 12.0)
    pits = nbt.voronoi(vec2, w2, scale=6.0)
    return [0.88 + (mott - 0.5) * 0.16 - (1.0 - nbt.smoothstep(0.0, 0.08, pits)) * 0.12]


def _canvas_h(u, v):
    n = 32                                  # 8 px threads: exact pixel period on 256
    a = nbt.sin(u * (2 * math.pi * n))
    b = nbt.sin(v * (2 * math.pi * n))
    return 0.5 + a * b * 0.35 + nbt.fabs(a) * 0.15


def _canvas(u, v):
    vec, w = nbt.torus(u, v, 1.2, 1.2, 2.0)
    mott = nbt.noise(vec, w, scale=1.5, detail=3) - 0.5
    return [0.88 + (_canvas_h(u, v) - 0.5) * 0.12 + mott * 0.08]


def _pebble_h(u, v):
    vec, w = nbt.torus(u, v, 2.0, 2.0, 7.0)
    return nbt.smoothstep(0.0, 0.45, nbt.voronoi(vec, w, scale=9.0, randomness=0.8))


def _wood(u, v):
    """Grey plank grain: 48 plank rows along v, grain streaks along u (court base)."""
    rows = 48
    rf = nbt.frac(v * rows)
    ri = _floor(v * rows)
    vec, w = nbt.torus(u, v, 0.8, 24.0, 3.0)
    grain = nbt.noise(vec, w, scale=1.5, detail=4, rough=0.6)
    seam = 1.0 - nbt.smoothstep(0.0, 0.08, nbt.vmin(rf, 1.0 - rf))
    return [0.86 + (_hash(ri, 5.0) - 0.5) * 0.12 + (grain - 0.5) * 0.16 - seam * 0.18]


def _turf(u, v):
    vec, w = nbt.torus(u, v, 14.0, 14.0, 2.0)
    fine = nbt.noise(vec, w, scale=2.0, detail=2)
    vec2, w2 = nbt.torus(u, v, 2.0, 2.0, 8.0)
    patch = nbt.noise(vec2, w2, scale=1.4, detail=3)
    return [0.86 + (fine - 0.5) * 0.22 + (patch - 0.5) * 0.16]


def _court_rgb(base):
    """Composite the basketball court (32 x 19 m map, court 28 x 15) over the baked grain."""
    N = 1024
    g = np.kron(base[:, :, 0], np.ones((2, 2)))           # 512 -> 1024
    Lt, Wt = 32.0, 19.0
    j = (np.arange(N) + 0.5) / N
    X_, Y_ = np.meshgrid((j - 0.5) * Lt, (0.5 - j) * Wt)   # row 0 = top = +y
    L, W, hw = 14.0, 7.5, 0.045
    inside = (np.abs(X_) <= L) & (np.abs(Y_) <= W)
    wood = np.array([0.80, 0.55, 0.32])
    border = np.array([0.10, 0.14, 0.34])
    pink = np.array([0.86, 0.20, 0.52])
    col = np.where(inside[..., None], wood, border)
    ax = np.abs(X_)
    bx = L - 1.575                                        # basket centre from the court centre
    key = (ax >= L - 5.8) & (np.abs(Y_) <= 2.45)
    col = np.where(key[..., None], pink, col)
    col = np.where((np.hypot(X_, Y_) <= 1.8)[..., None], pink, col)
    col = col * g[..., None]
    lines = np.zeros((N, N), bool)
    lines |= inside & ((np.abs(ax - L) < hw) | (np.abs(np.abs(Y_) - W) < hw))     # boundary
    lines |= (np.abs(X_) < hw) & (np.abs(Y_) <= W)                                 # centre line
    lines |= np.abs(np.hypot(X_, Y_) - 1.8) < hw                                   # centre circle
    kx = L - 5.8
    lines |= (np.abs(ax - kx) < hw) & (np.abs(Y_) <= 2.45 + hw)                     # free-throw line
    lines |= (np.abs(np.abs(Y_) - 2.45) < hw) & (ax >= kx) & (ax <= L)              # key sides
    dft = np.hypot(ax - kx, Y_)
    lines |= (np.abs(dft - 1.8) < hw) & (ax <= kx)                                  # free-throw circle
    d3 = np.hypot(ax - bx, Y_)
    arc = (np.abs(d3 - 6.75) < hw) & (np.abs(Y_) <= 6.6) & (ax <= bx)
    lines |= arc | ((np.abs(np.abs(Y_) - 6.6) < hw) & (ax >= bx) & (ax <= L))       # three-point line
    lines |= (np.abs(d3 - 1.25) < hw) & (ax <= bx)                                  # no-charge arc
    col = np.where(lines[..., None], np.array([0.97, 0.97, 0.95]), col)
    return col.reshape(512, 2, 512, 2, 3).mean(axis=(1, 3))


def _pitch_rgb(base):
    """Football pitch 90 x 56 m (+3 m run-off): mowing stripes + lines."""
    N = 1024
    g = np.kron(base[:, :, 0], np.ones((2, 2)))
    Lt, Wt = 96.0, 62.0
    j = (np.arange(N) + 0.5) / N
    X_, Y_ = np.meshgrid((j - 0.5) * Lt, (0.5 - j) * Wt)
    L, W, hw = 45.0, 28.0, 0.13
    stripe = (np.floor((X_ + L) / 7.5).astype(int) % 2 == 0)
    dark, light = np.array([0.16, 0.42, 0.13]), np.array([0.22, 0.52, 0.17])
    col = np.where(stripe[..., None], light, dark) * g[..., None]
    ax, ay = np.abs(X_), np.abs(Y_)
    inside = (ax <= L + hw) & (ay <= W + hw)
    lines = np.zeros((N, N), bool)
    lines |= inside & ((np.abs(ax - L) < hw) | (np.abs(ay - W) < hw))
    lines |= (np.abs(X_) < hw) & (ay <= W)
    r = np.hypot(X_, Y_)
    lines |= np.abs(r - 9.15) < hw
    lines |= r < 0.25
    pa, pw = 16.5, 20.15
    lines |= (np.abs(ax - (L - pa)) < hw) & (ay <= pw)
    lines |= (np.abs(ay - pw) < hw) & (ax >= L - pa) & (ax <= L)
    ga, gw = 5.5, 9.16
    lines |= (np.abs(ax - (L - ga)) < hw) & (ay <= gw)
    lines |= (np.abs(ay - gw) < hw) & (ax >= L - ga) & (ax <= L)
    dsp = np.hypot(ax - (L - 11.0), Y_)
    lines |= dsp < 0.22
    lines |= (np.abs(dsp - 9.15) < hw) & (ax < L - pa)
    dc = np.hypot(ax - L, ay - W)
    lines |= (np.abs(dc - 1.0) < hw) & (ax <= L) & (ay <= W)
    col = np.where(lines[..., None], np.array([0.95, 0.96, 0.93]), col)
    return col.reshape(512, 2, 512, 2, 3).mean(axis=(1, 3))


def bake_textures(names):
    """Bake (cached per process) the needed textures; must run before the scene is built
    (each bake resets the scene). Returns nothing, fills TEX[name] = png path."""
    if nbt._DIR is None:
        nbt._DIR = tempfile.mkdtemp(prefix="nb_lm_")
    keep = nbt.SIZE
    try:
        for n in names:
            if n in TEX:
                continue
            if n in ("court", "pitch"):
                nbt.SIZE = 512
                base = nbt._bake(n, _wood if n == "court" else _turf, 1)
                rgb = _court_rgb(base) if n == "court" else _pitch_rgb(base)
                TEX[n] = nbt._save(n, rgb, levels=48, mode="RGB")
                continue
            nbt.SIZE = 256
            if n == "stone_n":
                h = nbt._bake("stone_h", lambda u, v: [_stone_h(u, v)], 1)[:, :, 0]
                TEX[n] = nbt._save(n, nbt._normal_from_height(h, 6.0), levels=24, mode="RGB")
            elif n == "canvas_n":
                h = nbt._fold(nbt._bake("canvas_h", lambda u, v: [_canvas_h(u, v)], 1)[:, :, 0], 8, 8)
                TEX[n] = nbt._save(n, nbt._normal_from_height(h, 2.0), levels=48, mode="RGB")
            elif n == "pebble_n":
                h = nbt._blur(nbt._bake("pebble_h", lambda u, v: [_pebble_h(u, v)], 1)[:, :, 0])
                TEX[n] = nbt._save(n, nbt._normal_from_height(h, 5.0), levels=24, mode="RGB")
            else:
                fn = {"marble": _marble, "stone": _stone, "patina": _patina, "grass": _grass,
                      "concrete": _concrete, "canvas": _canvas}[n]
                TEX[n] = nbt._save(n, nbt._bake(n, fn, 1), levels=40)
    finally:
        nbt.SIZE = keep


# =========================================================================== materials
def mat(name, color, metallic=0.0, roughness=0.6, img=None, normal=None, nstrength=1.0, double=False, **kw):
    """Principled material (nb.material) + optional baked maps. Colour maps are multiplied
    by `color` (exported as baseColorFactor x baseColorTexture)."""
    if name in M:
        return M[name]
    m = nb.material(name, color, metallic=metallic, roughness=roughness, **kw)
    m.use_backface_culling = not double
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    if img:
        it = nt.nodes.new("ShaderNodeTexImage")
        it.image = bpy.data.images.load(TEX[img], check_existing=True)
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs[0].default_value = 1.0
        nt.links.new(it.outputs["Color"], mix.inputs[6])
        mix.inputs[7].default_value = tuple(color) + (1.0,)
        nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    if normal:
        nimg = bpy.data.images.load(TEX[normal], check_existing=True)
        nimg.colorspace_settings.name = "Non-Color"
        ni = nt.nodes.new("ShaderNodeTexImage")
        ni.image = nimg
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = nstrength
        nt.links.new(ni.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    m["nb_textured"] = bool(img or normal)
    M[name] = m
    return m


# =========================================================================== geometry helpers
def fix_normals(obj):
    """Merge doubles + recompute outward normals (closed solids only)."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    return obj


def smooth(obj, angle=35.0):
    nb.auto_smooth(obj, angle)
    return obj


def solid(name, verts, faces, m, angle=35.0):
    """Closed mesh: normals recomputed outward, auto-smoothed."""
    o = nb.mesh_object(name, verts, faces, [m])
    fix_normals(o)
    return smooth(o, angle)


def surf(name, verts, faces, m, angle=35.0):
    """Open surface: faces must already be counter-clockwise seen from the visible side."""
    o = nb.mesh_object(name, verts, faces, [m])
    return smooth(o, angle)


def box(size, loc, m, rot_z=0.0, angle=35.0):
    sx, sy, sz = (s / 2 for s in size)
    c, s = math.cos(rot_z), math.sin(rot_z)
    v = []
    for z in (-sz, sz):
        for x, y in ((-sx, -sy), (sx, -sy), (sx, sy), (-sx, sy)):
            v.append((loc[0] + x * c - y * s, loc[1] + x * s + y * c, loc[2] + z))
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return surf("Box", v, f, m, angle)


def bbox(x0, x1, y0, y1, z0, z1, m):
    return box((x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), m)


def frustum(x0, x1, y0, y1, z0, z1, ix0, ix1, iy0, iy1, m, bottom=True):
    """Box whose top rectangle is (ix0..ix1, iy0..iy1): hipped roofs, tapered blocks."""
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (ix0, iy0, z1), (ix1, iy0, z1), (ix1, iy1, z1), (ix0, iy1, z1)]
    f = [(4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    if bottom:
        f.append((0, 3, 2, 1))
    return surf("Frustum", v, f, m)


def extrude(poly, axis, a0, a1, m, angle=35.0, name="Prism"):
    """Extrude a 2D polygon (closed, any winding, may be concave) along an axis.
    axis 'X': poly in (y, z); 'Y': (x, z); 'Z': (x, y)."""
    n = len(poly)
    verts = []
    for a in (a0, a1):
        for p, q in poly:
            verts.append((a, p, q) if axis == "X" else (p, a, q) if axis == "Y" else (p, q, a))
    faces = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    return solid(name, verts, faces, m, angle)


def rev(profile, segs, m, loc=(0, 0, 0), cap0=False, cap1=False, angle=40.0, rfun=None, phase=0.0,
        scale=(1.0, 1.0)):
    """Surface of revolution around Z, outward normals. profile = [(r, z)] from bottom to top;
    rfun(r, z, theta) -> r lets the radius vary with the angle (flutes, folds)."""
    v, f = [], []
    n = len(profile)
    for s in range(segs):
        a = 2 * math.pi * s / segs + phase
        for r, z in profile:
            rr = rfun(r, z, a) if rfun else r
            v.append((loc[0] + rr * math.cos(a) * scale[0], loc[1] + rr * math.sin(a) * scale[1], loc[2] + z))
    for s in range(segs):
        s2 = (s + 1) % segs
        for i in range(n - 1):
            f.append((s * n + i, s2 * n + i, s2 * n + i + 1, s * n + i + 1))
    if cap0:
        f.append(tuple(s * n for s in reversed(range(segs))))
    if cap1:
        f.append(tuple(s * n + n - 1 for s in range(segs)))
    return surf("Rev", v, f, m, angle)


def frame_of(t):
    t = Vector(t).normalized()
    ref = UP if abs(t.dot(UP)) < 0.95 else Vector((1, 0, 0))
    n = ref.cross(t).normalized()
    b = t.cross(n)
    return t, n, b


def strand(p0, p1, r, m, sides=3, r1=None, cap=False, angle=89.0):
    """Thin tube between two points (outward normals; open ends unless cap)."""
    p0, p1 = Vector(p0), Vector(p1)
    t, n, b = frame_of(p1 - p0)
    v, f = [], []
    for p, rr in ((p0, r), (p1, r if r1 is None else r1)):
        for s in range(sides):
            a = 2 * math.pi * s / sides
            v.append(tuple(p + (n * math.cos(a) + b * math.sin(a)) * rr))
    for s in range(sides):
        s2 = (s + 1) % sides
        f.append((s, s2, sides + s2, sides + s))
    if cap:
        f.append(tuple(reversed(range(sides))))
        f.append(tuple(sides + s for s in range(sides)))
    return surf("Strand", v, f, m, angle)


def path_tube(pts, r, m, sides=6, closed=False, angle=89.0, radii=None):
    """Tube swept along a polyline (parallel transport), outward normals, open ends."""
    pts = [Vector(p) for p in pts]
    N = len(pts)
    v, f = [], []
    prev = None
    for i, p in enumerate(pts):
        if closed:
            t = (pts[(i + 1) % N] - pts[(i - 1) % N]).normalized()
        else:
            t = (pts[min(i + 1, N - 1)] - pts[max(i - 1, 0)]).normalized()
        if prev is None:
            _, n, _ = frame_of(t)
        else:
            n = (prev - t * prev.dot(t)).normalized()
        prev = n
        b = t.cross(n)
        rr = radii[i] if radii else r
        for s in range(sides):
            a = 2 * math.pi * s / sides
            v.append(tuple(p + (n * math.cos(a) + b * math.sin(a)) * rr))
    rng = N if closed else N - 1
    for i in range(rng):
        i2 = (i + 1) % N
        for s in range(sides):
            s2 = (s + 1) % sides
            f.append((i * sides + s, i * sides + s2, i2 * sides + s2, i2 * sides + s))
    return surf("Tube", v, f, m, angle)


def sphere(r, loc, m, seg=10, rings=6, scale=(1, 1, 1), angle=89.0):
    o = nb.uv_sphere("Sphere", r, loc, seg, rings, m, scale)
    return smooth(fix_normals(o), angle)


def xform(obj, mtx):
    obj.data.transform(mtx)
    obj.data.update()
    return obj


def star_poly(n, r_out, r_in, rot=math.pi / 2):
    return [((r_out if k % 2 == 0 else r_in) * math.cos(rot + math.pi * k / n),
             (r_out if k % 2 == 0 else r_in) * math.sin(rot + math.pi * k / n)) for k in range(2 * n)]


def decimate(obj, target):
    tris = nb.tri_count(obj)
    if tris > target:
        md = obj.modifiers.new("Decimate", "DECIMATE")
        md.decimate_type = "COLLAPSE"
        md.ratio = target / tris
        md.use_collapse_triangulate = True
        nb.apply_modifiers(obj)
    return obj


# =========================================================================== UVs / finishing
def uv_box(obj):
    me = obj.data
    uv = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
    names = [m.name for m in me.materials]
    for p in me.polygons:
        tile = TILE.get(names[p.material_index], 2.0)
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


def uv_planar(obj, matname, L, W):
    """Top faces of `matname`: u = x / L + .5, v = y / W + .5 (printed court / pitch maps)."""
    me = obj.data
    uv = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
    names = [m.name for m in me.materials]
    for p in me.polygons:
        if names[p.material_index] != matname:
            continue
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = (co.x / L + 0.5, co.y / W + 0.5)


def finish(name, parts, planar=None):
    """Join parts into <Name>_Tex (textured materials, with UVs) and <Name> (the rest, no UVs).
    Smoothing flags set per part survive the join. Returns the objects."""
    parts = [p for p in parts if p is not None]
    tex, plain = [], []
    for p in parts:
        ms = p.data.materials
        is_tex = any(m.get("nb_textured") for m in ms) if ms else False
        (tex if is_tex else plain).append(p)
    out = []
    if plain:
        o = nb.join(plain, name)
        for l in list(o.data.uv_layers):
            o.data.uv_layers.remove(l)
        out.append(o)
    if tex:
        o = nb.join(tex, name + "_Tex")
        uv_box(o)
        if planar:
            uv_planar(o, *planar)
        out.append(o)
    return out


# =========================================================================== lm_statue
S_FIG = 20.0          # figure units (a 1.8 m tall human-like figure) -> metres
Z_FEET = 39.3         # top of the statue plinth


def mb_elements(E, resolution, name):
    """Metaball family -> mesh. Elements: (kind, data...) with *visible* radii/semi-axes
    (surface of an isolated element, threshold .6, stiffness 2 -> radius x 0.575)."""
    k = 1 / 0.575
    mb = bpy.data.metaballs.new(name)
    mb.resolution = resolution
    mb.render_resolution = resolution
    mb.threshold = 0.6
    obj = nb.link(bpy.data.objects.new(name, mb))
    for e in E:
        kind = e[0]
        neg = kind.startswith("-")
        kind = kind.lstrip("-")
        if kind == "ball":
            el = mb.elements.new(type="BALL")
            el.co, el.radius = e[1], e[2] * k
        elif kind == "caps":
            a, b, r = Vector(e[1]), Vector(e[2]), e[3]
            el = mb.elements.new(type="CAPSULE")
            el.co = (a + b) / 2
            el.radius = r * k
            el.size_x = max((b - a).length / 2, 1e-4)
            el.rotation = Vector((1, 0, 0)).rotation_difference((b - a).normalized())
        else:   # ell: centre, semi-axes, optional rotation (Euler deg)
            el = mb.elements.new(type="ELLIPSOID")
            el.co = e[1]
            el.radius = k
            el.size_x, el.size_y, el.size_z = e[2]
            if len(e) > 3:
                from mathutils import Euler
                el.rotation = Euler([math.radians(a) for a in e[3]]).to_quaternion()
        el.stiffness = 2.0
        el.use_negative = neg
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    me = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
    bpy.data.objects.remove(obj)
    bpy.data.metaballs.remove(mb)
    return nb.link(bpy.data.objects.new(name, me))


def statue_body_elements():
    """Upper body, arms, head (figure units, Z up, facing -Y; the figure's right is -X)."""
    E = [
        # torso under the drapery
        ("ell", (0, 0.01, 0.98), (0.150, 0.125, 0.14)),
        ("ell", (0, 0.01, 1.10), (0.140, 0.110, 0.11)),
        ("ell", (0, 0.0, 1.31), (0.165, 0.110, 0.15)),
        ("ball", (0.07, -0.075, 1.31), 0.062), ("ball", (-0.07, -0.075, 1.31), 0.062),
        ("caps", (-0.165, 0.005, 1.425), (0.165, 0.005, 1.425), 0.062),
        # neck + head (rounder face, small straight nose, full chin; hair bun at the nape)
        ("caps", (0, 0.01, 1.45), (0, 0.0, 1.555), 0.044),
        ("ell", (0, 0.0, 1.648), (0.080, 0.090, 0.104)),
        ("ell", (0, -0.030, 1.598), (0.064, 0.060, 0.058)),
        ("ball", (0.042, -0.058, 1.616), 0.030), ("ball", (-0.042, -0.058, 1.616), 0.030),
        ("ball", (0, -0.070, 1.562), 0.026),
        ("caps", (0, -0.088, 1.668), (0, -0.098, 1.628), 0.014),
        ("caps", (-0.042, -0.072, 1.676), (0.042, -0.072, 1.676), 0.017),
        ("-ball", (0.030, -0.092, 1.654), 0.014), ("-ball", (-0.030, -0.092, 1.654), 0.014),
        ("caps", (-0.018, -0.083, 1.593), (0.018, -0.083, 1.593), 0.010),       # lips
        ("ell", (0, 0.020, 1.678), (0.092, 0.098, 0.088)),                     # hair mass
        ("ball", (0.0, 0.098, 1.598), 0.048), ("ball", (0.0, 0.085, 1.640), 0.040),   # bun
        ("caps", (0.080, 0.0, 1.62), (0.076, 0.03, 1.56), 0.022),             # hair over the ears
        ("caps", (-0.080, 0.0, 1.62), (-0.076, 0.03, 1.56), 0.022),
        # raised right arm (bare forearm, heavy sleeve falling back from the upper arm)
        ("caps", (-0.175, 0.0, 1.43), (-0.235, 0.02, 1.72), 0.050),
        ("caps", (-0.235, 0.02, 1.72), (-0.232, 0.0, 1.975), 0.038),
        ("ball", (-0.232, -0.002, 2.005), 0.040),
        ("caps", (-0.19, 0.03, 1.44), (-0.262, 0.05, 1.68), 0.072),
        ("ball", (-0.27, 0.07, 1.60), 0.058),
        ("ball", (-0.255, 0.065, 1.50), 0.060),
        # left arm: upper arm down, forearm forward holding the tablet against the hip
        ("caps", (0.175, 0.0, 1.42), (0.235, 0.025, 1.17), 0.050),
        ("caps", (0.235, 0.025, 1.17), (0.205, -0.115, 1.235), 0.040),
        ("ball", (0.19, -0.135, 1.25), 0.038),
        ("caps", (0.19, 0.02, 1.42), (0.25, 0.04, 1.22), 0.062),                # sleeve
        # drapery: mantle over the left shoulder, crossing to the right hip, back panel
        ("caps", (0.15, -0.065, 1.44), (-0.13, -0.115, 1.02), 0.048),
        ("caps", (0.17, -0.10, 1.22), (-0.16, -0.125, 0.90), 0.044),
        ("caps", (0.16, -0.09, 1.07), (-0.10, -0.135, 0.80), 0.036),
        ("ell", (0, 0.085, 1.22), (0.17, 0.06, 0.26)),
        ("ell", (0.0, 0.11, 0.95), (0.16, 0.06, 0.20)),
    ]
    return E


def robe_radius(z, a):
    """Lower robe radius in figure units, with vertical folds deeper towards the hem."""
    prof = [(0.0, 0.250), (0.10, 0.243), (0.40, 0.222), (0.70, 0.192), (0.90, 0.168), (1.05, 0.152),
            (1.13, 0.142)]
    for (z0, r0), (z1, r1) in zip(prof, prof[1:]):
        if z <= z1:
            r = r0 + (r1 - r0) * (z - z0) / (z1 - z0)
            break
    else:
        r = prof[-1][1]
    depth = 0.10 * (1.0 - min(1.0, z / 1.15)) ** 0.7 + 0.015
    tw = a + 0.35 * z
    fold = 0.55 * math.sin(9 * tw + 0.8 * math.sin(3 * tw)) + 0.30 * math.sin(16 * tw + 1.3) \
        + 0.15 * math.sin(23 * a + 2.1)
    # left knee (figure's left = +X) pushing the cloth forward
    da = math.atan2(math.sin(a - math.radians(-62)), math.cos(a - math.radians(-62)))
    knee = 0.035 * math.exp(-(da / 0.45) ** 2) * math.exp(-((z - 0.50) / 0.16) ** 2)
    return r * (1.0 + depth * fold) + knee


def statue_robe(m, segs=44, rings=13):
    zs = [0.0, 0.03, 0.08, 0.16, 0.26, 0.38, 0.50, 0.62, 0.74, 0.86, 0.96, 1.05, 1.13][:rings]
    v, f = [], []
    for z in zs:
        for s in range(segs):
            a = 2 * math.pi * s / segs
            r = robe_radius(z, a)
            # hem lifted at the front (feet show), cloth trailing a little at the back
            front = max(0.0, -math.sin(a))
            zz = z if z > 0.2 else z + (0.055 * front ** 3) * (1 - z / 0.2)
            yoff = 0.03 * (1 - min(1.0, z / 0.9))
            v.append((r * math.cos(a), r * math.sin(a) * 0.86 + yoff, zz))
    for i in range(len(zs) - 1):
        for s in range(segs):
            s2 = (s + 1) % segs
            f.append((i * segs + s, i * segs + s2, (i + 1) * segs + s2, (i + 1) * segs + s))
    f.append(tuple(reversed(range(segs))))
    return surf("Robe", v, f, m, 60.0)


def tablet(mp, mdark):
    """Tablet held against the left hip, engraved 'NB' (letters = dark inset strokes)."""
    parts = []
    w, h, t = 0.15, 0.27, 0.035
    parts.append(box((w, t, h), (0, 0, 0), mp))
    parts.append(box((w + 0.012, t + 0.01, 0.016), (0, 0, h / 2 - 0.004), mp))    # top moulding
    sw, lh, d = 0.011, 0.075, -t / 2 - 0.0015

    def stroke(x0, z0, x1, z1):
        L = math.hypot(x1 - x0, z1 - z0)
        o = box((sw, 0.006, L + sw * 0.6), ((x0 + x1) / 2, d, (z0 + z1) / 2), mdark)
        xform(o, Matrix.Translation(Vector(((x0 + x1) / 2, d, (z0 + z1) / 2))) @
              Matrix.Rotation(-math.atan2(x1 - x0, z1 - z0), 4, "Y") @
              Matrix.Translation(-Vector(((x0 + x1) / 2, d, (z0 + z1) / 2))))
        return o
    z0, z1 = 0.0, lh
    # N
    parts += [stroke(-0.055, z0, -0.055, z1), stroke(-0.055, z1, -0.012, z0), stroke(-0.012, z0, -0.012, z1)]
    # B: stem + two bowls (polyline strokes)
    parts.append(stroke(0.012, z0, 0.012, z1))
    for zc, rr in ((z1 - 0.019, 0.019), (z0 + 0.021, 0.021)):
        pts = [(0.012, zc + rr)] + [(0.035 + rr * 0.9 * math.sin(math.pi * k / 4), zc + rr * math.cos(math.pi * k / 4))
                                    for k in range(1, 4)] + [(0.012, zc - rr)]
        pts[0] = (0.022, zc + rr)
        pts[-1] = (0.022, zc - rr)
        for (a0, b0), (a1, b1) in zip(pts, pts[1:]):
            parts.append(stroke(a0, b0, a1, b1))
    # roman-like date line below (dots), different from any real inscription
    for k in range(4):
        parts.append(box((0.012, 0.006, 0.012), (-0.045 + k * 0.03, d, -0.06), mdark))
    obj = nb.join(parts, "Tablet")
    smooth(obj, 30)
    return obj


def make_statue():
    bake_textures(["patina", "stone", "stone_n", "grass", "concrete"])
    nb.reset_scene()
    M.clear()
    patina = mat("Patina", (0.36, 0.62, 0.52), 0.25, 0.55, img="patina")
    pdark = mat("PatinaDark", (0.10, 0.22, 0.19), 0.2, 0.7)
    glow = mat("Glow", (1.0, 0.72, 0.25), emission=(1.0, 0.62, 0.18), strength=8.0, roughness=0.4)
    gold = mat("Gold", (0.92, 0.70, 0.32), 1.0, 0.3)
    stone = mat("Stone", (0.80, 0.76, 0.70), 0.0, 0.8, img="stone", normal="stone_n", nstrength=0.8)
    grass = mat("Grass", (0.24, 0.42, 0.16), 0.0, 0.9, img="grass")
    rock = mat("Rock", (0.42, 0.40, 0.38), 0.0, 0.95, img="concrete")
    wood = mat("Wood", (0.36, 0.25, 0.16), 0.0, 0.8)
    shadow = mat("Shadow", (0.03, 0.035, 0.04), 0.0, 0.9)
    parts = []
    rnd = random.Random(11)

    # ---------------- islet (water level z = 0, plateau z = 2.5)
    segs = 48
    rings = [(0.0, 2.5, "g"), (25.0, 2.5, "g"), (25.6, 2.53, "p"), (28.4, 2.53, "p"), (29.0, 2.5, "g"),
             (32.0, 2.45, "g"), (34.0, 2.1, "r"), (37.0, 1.1, "r"), (40.0, -0.1, "r"), (43.0, -1.6, "r")]
    v, f, fm = [], [], []
    for (r, z, _) in rings:
        for s in range(segs):
            a = 2 * math.pi * s / segs
            k = 1.0 if r < 30 else 1.0 + 0.05 * math.sin(3 * a + 1.0) + 0.035 * math.sin(7 * a + 0.3) \
                + 0.02 * math.sin(13 * a)
            v.append((r * k * math.cos(a), r * k * math.sin(a), z))
    for i in range(len(rings) - 1):
        kind = rings[i + 1][2] if rings[i][2] != "p" or rings[i + 1][2] == "p" else "g"
        if rings[i][2] == "p" and rings[i + 1][2] == "p":
            kind = "p"
        elif rings[i + 1][2] == "r" or rings[i][2] == "r":
            kind = "r"
        else:
            kind = "g" if not (rings[i][2] == "g" and rings[i + 1][2] == "p") else "g"
        for s in range(segs):
            s2 = (s + 1) % segs
            f.append((i * segs + s, i * segs + s2, (i + 1) * segs + s2, (i + 1) * segs + s))
            fm.append({"g": 0, "p": 1, "r": 2}[kind])
    isl = nb.mesh_object("Islet", v, f, [grass, stone, rock], fm)
    parts.append(smooth(isl, 30))
    # boulders along the shore
    for k in range(18):
        a = 2 * math.pi * k / 18 + rnd.uniform(-0.1, 0.1)
        r = rnd.uniform(37.5, 40.5)
        sz = rnd.uniform(1.2, 2.4)
        parts.append(sphere(sz, (r * math.cos(a), r * math.sin(a), 0.2), rock, 6, 4,
                            (1.0, rnd.uniform(0.7, 1.0), 0.55), angle=40))
    # wooden pier towards the front (-Y = glTF +Z)
    parts.append(bbox(-2.0, 2.0, -50.0, -36.0, 1.2, 1.55, wood))
    for y in (-49.0, -45.0, -41.0):
        for x in (-1.7, 1.7):
            parts.append(strand((x, y, -1.5), (x, y, 1.25), 0.18, wood, sides=6, cap=False))
    for x in (-1.9, 1.9):
        parts.append(bbox(x - 0.07, x + 0.07, -50.0, -37.0, 1.55, 2.5, wood))

    # ---------------- 7-point star fort (z 2.5 -> 10.5), battered walls + coping
    star = star_poly(7, 23.5, 15.0, rot=-math.pi / 2)
    zb, zt = 2.5, 10.5
    v = [(x, y, zb) for x, y in star] + [(x * 0.965, y * 0.965, zt) for x, y in star]
    n = len(star)
    f = [tuple(range(2 * n - 1, n - 1, -1))[::-1]]
    f = [tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        f.append((i, j, n + j, n + i))
    parts.append(solid("Fort", v, f, stone, 20))
    cop = [(x * 0.985, y * 0.985) for x, y in star]
    parts.append(extrude(cop, "Z", zt - 0.05, zt + 0.55, stone, 20))
    inner = [(x * 0.90, y * 0.90) for x, y in star]
    parts.append(extrude(inner, "Z", zt + 0.5, zt + 0.62, stone, 20))
    # gate in the front point (dark recess + stone frame)
    gx, gy = star[0]
    parts.append(bbox(-1.8, 1.8, gy * 0.965 - 0.9, gy * 0.965 + 0.6, zb, zb + 4.2, stone))
    parts.append(bbox(-1.2, 1.2, gy * 0.965 - 0.95, gy * 0.965 - 0.85, zb, zb + 3.4, shadow))

    # ---------------- pedestal (granite blocks), z 10.5 -> 39.3
    def sq(half, z0, z1, m=stone):
        return bbox(-half, half, -half, half, z0, z1, m)
    parts += [sq(10.2, 10.5, 11.3), sq(9.4, 11.3, 12.5), sq(8.0, 12.5, 20.0), sq(8.5, 20.0, 20.9),
              sq(7.0, 20.9, 33.0), sq(7.7, 33.0, 34.2), sq(6.6, 34.2, 37.5), sq(7.2, 37.5, 38.3),
              sq(5.6, 38.3, 39.3)]
    for sx in (-1, 1):                     # corner pilasters (lower + upper shafts)
        for sy in (-1, 1):
            parts.append(bbox(sx * 8.25 - 0.9, sx * 8.25 + 0.9, sy * 8.25 - 0.9, sy * 8.25 + 0.9, 12.5, 20.0, stone))
            parts.append(bbox(sx * 7.2 - 0.75, sx * 7.2 + 0.75, sy * 7.2 - 0.75, sy * 7.2 + 0.75, 20.9, 33.0, stone))
    for k in range(4):                     # per face: loggia opening, pediment, star relief, attic slits
        R = Matrix.Rotation(k * math.pi / 2, 4, "Z")
        fp = []
        fp.append(bbox(-2.0, 2.0, -7.45, -7.0, 24.0, 30.4, stone))      # frame
        fp.append(bbox(-1.4, 1.4, -7.5, -7.4, 24.4, 29.8, shadow))     # opening
        fp.append(extrude([(-2.5, 30.4), (2.5, 30.4), (0.0, 32.0)], "Y", -7.55, -7.0, stone))
        fp.append(bbox(-2.3, 2.3, -7.6, -7.0, 23.6, 24.0, stone))       # sill
        fp.append(extrude(star_poly(5, 1.9, 0.8), "Y", -8.25, -8.0, stone, name="Star"))
        xform(fp[-1], Matrix.Translation((0, 0, 16.0)) @ Matrix.Rotation(math.pi / 2, 4, "X")
              @ Matrix.Translation((0, 8.125, 0)) @ Matrix.Rotation(-math.pi / 2, 4, "X")
              @ Matrix.Translation((0, 0, 0)))
        for x in (-3.6, 0.0, 3.6):
            fp.append(bbox(x - 0.45, x + 0.45, -6.65, -6.55, 35.0, 36.8, shadow))
        for o in fp:
            xform(o, R)
        parts += fp

    # ---------------- the figure
    fig = []
    body = mb_elements(statue_body_elements(), 0.011, "StatueMB")
    decimate(body, 6200)
    body.data.materials.append(patina)
    smooth(body, 70)
    fig.append(body)
    fig.append(statue_robe(patina))
    for x, y, sz in ((0.085, -0.235, (0.045, 0.072, 0.034)), (-0.075, -0.200, (0.042, 0.060, 0.030))):
        fig.append(sphere(1.0, (x, y, 0.028), patina, 10, 6, sz, 60))         # toes under the hem
    fig.append(rev([(0.27, -0.02), (0.27, 0.0)], 32, patina, cap1=True))    # bronze base slab
    # crown: band + 5 rays fanned over the front half
    fig.append(rev([(0.090, 1.684), (0.100, 1.692), (0.101, 1.712), (0.094, 1.728)], 20, patina,
                   loc=(0, 0.004, 0), angle=50, scale=(1.0, 1.08)))
    for k in range(5):
        a = math.radians(-90 + (k - 2) * 38)
        d = Vector((math.cos(a), math.sin(a) * 1.08, 0.0))
        tilt = math.radians(28 - abs(k - 2) * 4)
        dirv = (d * math.cos(tilt) + UP * math.sin(tilt)).normalized()
        base = Vector((0, 0.004, 1.708)) + d * 0.096
        side = UP.cross(d).normalized()
        upv = dirv.cross(side).normalized()
        L = 0.20 if k == 2 else 0.17
        tip = base + dirv * L
        w = 0.022
        vv = [tuple(base + side * w + upv * w * 0.5), tuple(base - side * w + upv * w * 0.5),
              tuple(base - side * w - upv * w * 0.5), tuple(base + side * w - upv * w * 0.5), tuple(tip)]
        fig.append(solid("Ray", vv, [(0, 1, 2, 3), (0, 4, 1), (1, 4, 2), (2, 4, 3), (3, 4, 0)], patina, 20))
    # torch in the raised right hand
    hx, hy = -0.232, -0.002
    fig.append(rev([(0.020, 1.96), (0.022, 2.08), (0.030, 2.10), (0.026, 2.12)], 10, patina, loc=(hx, hy, 0)))
    fig.append(rev([(0.026, 2.115), (0.050, 2.15), (0.064, 2.19), (0.070, 2.205), (0.062, 2.215)], 16,
                   patina, loc=(hx, hy, 0), cap1=True))
    fig.append(rev([(0.064, 2.21), (0.066, 2.222), (0.0, 2.226)], 16, gold, loc=(hx, hy, 0)))

    def flame_r(r, z, a):
        return r * (1.0 + 0.22 * math.sin(5 * a + (z - 2.2) * 30.0))
    fig.append(rev([(0.055, 2.215), (0.060, 2.25), (0.052, 2.30), (0.036, 2.35), (0.018, 2.40), (0.0, 2.44)],
                   15, glow, loc=(hx, hy, 0), rfun=flame_r, angle=70, cap0=True))
    tb = tablet(patina, pdark)
    xform(tb, Matrix.Translation((0.245, -0.075, 1.19)) @ Matrix.Rotation(math.radians(-22), 4, "Z")
          @ Matrix.Rotation(math.radians(-10), 4, "X"))
    fig.append(tb)
    for o in fig:
        xform(o, Matrix.Translation((0, 0, Z_FEET)) @ Matrix.Scale(S_FIG, 4))
    parts += fig
    return finish("Statue", parts)


# =========================================================================== lm_palace
def window(o, n, s, z, w, h, mglass, mframe, ped=None, fd=0.16, fw=0.22):
    """Window on a facade: o = point on the wall (z=0), n = outward normal, s = offset along
    the facade, z = sill-centre height. Frame ring (closed solid) + recessed glass + mullions +
    head: None, 'tri' (triangular pediment) or 'flat' (cornice lintel)."""
    n = Vector(n)
    t = UP.cross(n)
    c = Vector(o) + t * s

    def P(a, b, d):
        return tuple(c + t * a + n * d + UP * (z + b))
    parts = []
    W2, H2 = w / 2 + fw, h / 2 + fw
    w2, h2 = w / 2, h / 2
    rect = lambda x, y, d: [P(-x, -y, d), P(x, -y, d), P(x, y, d), P(-x, y, d)]
    v = rect(W2, H2, fd) + rect(w2, h2, fd) + rect(w2, h2, 0.0) + rect(W2, H2, 0.0)
    f = []
    for i in range(4):
        j = (i + 1) % 4
        f.append((i, j, 4 + j, 4 + i))           # front ring
        f.append((4 + i, 4 + j, 8 + j, 8 + i))   # reveal
        f.append((12 + j, 12 + i, i, j))         # outer side
        f.append((8 + i, 8 + j, 12 + j, 12 + i))  # back
    parts.append(solid("WinFrame", v, f, mframe, 30))
    parts.append(surf("WinGlass", [P(-w2, -h2, 0.02), P(w2, -h2, 0.02), P(w2, h2, 0.02), P(-w2, h2, 0.02)],
                      [(0, 1, 2, 3)], mglass))
    mw = 0.05
    parts.append(surf("Mull", [P(-mw, -h2, 0.04), P(mw, -h2, 0.04), P(mw, h2, 0.04), P(-mw, h2, 0.04),
                               P(-w2, h2 * 0.25 - mw, 0.04), P(w2, h2 * 0.25 - mw, 0.04),
                               P(w2, h2 * 0.25 + mw, 0.04), P(-w2, h2 * 0.25 + mw, 0.04)],
                      [(0, 1, 2, 3), (4, 5, 6, 7)], mframe))
    if ped == "tri":
        b0, ph = H2 + 0.12, 0.85
        tri = [(-W2 - 0.25, b0), (W2 + 0.25, b0), (0.0, b0 + ph)]
        v = [P(a, b, 0.0) for a, b in tri] + [P(a, b, fd + 0.12) for a, b in tri]
        parts.append(solid("Ped", v, [(0, 1, 2), (3, 4, 5), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)], mframe, 30))
        v = rect(W2 + 0.25, 0.07, 0.0) + rect(W2 + 0.25, 0.07, fd + 0.14)
        v = [tuple(Vector(p) + UP * (H2 + 0.06)) for p in v]
        parts.append(solid("Lintel", v, [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6),
                                         (3, 0, 4, 7)], mframe, 30))
    elif ped == "flat":
        v = rect(W2 + 0.2, 0.14, 0.0) + rect(W2 + 0.2, 0.14, fd + 0.12)
        v = [tuple(Vector(p) + UP * (H2 + 0.14)) for p in v]
        parts.append(solid("Lintel", v, [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6),
                                         (3, 0, 4, 7)], mframe, 30))
    return parts


def balustrade(p0, p1, z, m, spacing=0.7, sides=4, h=1.05):
    """Rail + plinth + vase balusters between two points (horizontal)."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    L = d.length
    ang = math.atan2(d.y, d.x)
    mid = (p0 + p1) / 2
    parts = [box((L, 0.42, 0.14), (mid.x, mid.y, z + 0.07), m, ang),
             box((L, 0.46, 0.14), (mid.x, mid.y, z + h - 0.07), m, ang)]
    n = max(1, int(L / spacing))
    prof = [(0.07, z + 0.14), (0.13, z + 0.42), (0.065, z + 0.78), (0.09, z + h - 0.14)]
    for i in range(n):
        p = p0 + d * ((i + 0.5) / n)
        parts.append(rev(prof, sides, m, loc=(p.x, p.y, 0), phase=math.pi / 4 + ang, angle=89))
    return parts


def ionic_column(x, y, z0, z1, D, m):
    parts = []
    H = z1 - z0
    parts.append(bbox(x - D * 0.68, x + D * 0.68, y - D * 0.68, y + D * 0.68, z0, z0 + 0.18, m))
    parts.append(rev([(D * 0.64, z0 + 0.18), (D * 0.62, z0 + 0.30), (D * 0.54, z0 + 0.36), (D * 0.58, z0 + 0.46),
                      (D * 0.52, z0 + 0.52)], 12, m, loc=(x, y, 0), angle=60))
    sh0, sh1 = z0 + 0.52, z1 - 0.62

    def flute(r, z, a):
        return r * (0.955 + 0.045 * abs(math.cos(a * 8)))
    parts.append(rev([(D * 0.5, sh0), (D * 0.5, sh0 + (sh1 - sh0) * 0.33), (D * 0.47, sh0 + (sh1 - sh0) * 0.7),
                      (D * 0.43, sh1)], 16, m, loc=(x, y, 0), rfun=flute, angle=60))
    parts.append(rev([(D * 0.43, sh1), (D * 0.50, sh1 + 0.10), (D * 0.52, sh1 + 0.22)], 12, m,
                     loc=(x, y, 0), angle=60))
    parts.append(bbox(x - D * 0.62, x + D * 0.62, y - D * 0.62, y + D * 0.62, z1 - 0.16, z1, m))
    # volute bolsters running front-back, spirals on the front face
    zc = z1 - 0.34
    for sx in (-1, 1):
        cx = x + sx * D * 0.48
        parts.append(strand((cx, y + D * 0.5, zc), (cx, y - D * 0.5, zc), D * 0.21, m, sides=10, cap=True, angle=60))
        pts = []
        for k in range(10):
            a = k * 0.75
            rr = D * 0.20 * (1 - k / 11)
            pts.append((cx + sx * rr * math.cos(a), y - D * 0.5 - 0.03, zc + rr * math.sin(a)))
        parts.append(path_tube(pts, D * 0.028, m, sides=3))
    return parts


def make_palace():
    bake_textures(["marble", "stone", "stone_n", "grass"])
    nb.reset_scene()
    M.clear()
    marble = mat("Marble", (0.93, 0.92, 0.89), 0.0, 0.45, img="marble")
    stone = mat("Stone", (0.70, 0.68, 0.64), 0.0, 0.8, img="stone", normal="stone_n", nstrength=0.7)
    glass = mat("Glass", (0.05, 0.08, 0.12), 0.3, 0.1)
    roof = mat("Roof", (0.30, 0.32, 0.35), 0.4, 0.55)
    grass = mat("Grass", (0.22, 0.45, 0.15), 0.0, 0.9, img="grass")
    path = mat("Path", (0.72, 0.68, 0.60), 0.0, 0.9)
    hedge = mat("Hedge", (0.10, 0.25, 0.09), 0.0, 0.9)
    iron = mat("Metal", (0.05, 0.05, 0.055), 0.8, 0.45)
    gold = mat("Gold", (0.92, 0.72, 0.30), 1.0, 0.3)
    water = mat("Water", (0.12, 0.35, 0.50), 0.0, 0.05)
    wood = mat("Wood", (0.25, 0.14, 0.08), 0.0, 0.6)
    flag = mat("Flag", (0.0, 0.45, 1.0), 0.0, 0.7, emission=(0.0, 0.35, 1.0), strength=0.6)
    fstar = mat("FlagStar", (1.0, 0.25, 0.70), 0.0, 0.6, emission=(1.0, 0.2, 0.65), strength=1.5)
    glow = mat("Glow", (1.0, 0.85, 0.6), emission=(1.0, 0.8, 0.5), strength=5.0)
    P = []

    # ---------------- grounds: lawn slab, paths, hedges
    P.append(bbox(-55, 55, -40, 40, -0.3, 0.0, grass))
    P.append(bbox(-3.0, 3.0, -40, -13.0, 0.0, 0.04, path))                  # main drive
    P.append(rev([(9.0, 0.0), (9.0, 0.04), (12.5, 0.04), (12.5, 0.0)], 32, path, loc=(0, -26.5, 0), angle=30))
    P.append(bbox(-46, 46, -2.0, -1.0, 0.0, 0.04, path))                    # walk along the facade
    for sx in (-1, 1):
        P.append(bbox(sx * 53.0 - 0.6, sx * 53.0 + 0.6, -37, 38.0, 0.0, 1.4, hedge))
    P.append(bbox(-53.6, 53.6, 38.0, 39.2, 0.0, 1.4, hedge))

    # ---------------- central block (x +-20, y -1..21) and wings (x 20..44, y 1..17)
    def block(x0, x1, y0, y1, ztop, corn):
        q = [bbox(x0 - 0.3, x1 + 0.3, y0 - 0.3, y1 + 0.3, 0.0, 2.0, stone),        # rusticated plinth
             bbox(x0, x1, y0, y1, 2.0, ztop, marble),
             bbox(x0 - 0.35, x1 + 0.35, y0 - 0.35, y1 + 0.35, ztop, ztop + 0.6, marble),   # architrave/frieze
             bbox(x0 - 0.75, x1 + 0.75, y0 - 0.75, y1 + 0.75, ztop + 0.6, ztop + corn, marble)]  # cornice
        q.append(bbox(x0 - 0.2, x1 + 0.2, y0 - 0.2, y1 + 0.2, 6.0, 6.35, marble))      # string course
        return q
    P += block(-20, 20, -1, 21, 14.0, 1.2)
    for sx in (-1, 1):
        x0, x1 = (20, 44) if sx > 0 else (-44, -20)
        P += block(x0, x1, 1, 17, 10.0, 1.0)
    # hipped roof + chimneys
    P.append(frustum(-19, 19, 0, 20, 15.2, 18.6, -11, 11, 8.5, 11.5, roof, bottom=False))
    for x in (-14, 14):
        for y in (3.5, 16.5):
            P.append(bbox(x - 0.6, x + 0.6, y - 1.0, y + 1.0, 15.0, 19.4, marble))
            P.append(bbox(x - 0.75, x + 0.75, y - 1.15, y + 1.15, 19.4, 19.7, marble))
    for sx in (-1, 1):
        x0, x1 = (21, 43) if sx > 0 else (-43, -21)
        P.append(bbox(x0, x1, 2, 16, 11.0, 11.6, roof))
    # pilasters on the facades
    for x in (-20, -11.4, 11.4, 20):
        for y, dy in ((-1, -0.25), (21, 0.25)):
            P.append(bbox(x - 0.4, x + 0.4, min(y, y + dy), max(y, y + dy), 2.0, 14.0, marble))
    for sx in (-1, 1):
        for x in (21.0, 43.6):
            for y, dy in ((1, -0.22), (17, 0.22)):
                xx = sx * x
                P.append(bbox(xx - 0.35, xx + 0.35, min(y, y + dy), max(y, y + dy), 2.0, 10.0, marble))

    # ---------------- windows (66) with pediments on the upper floor
    F, B = Vector((0, -1, 0)), Vector((0, 1, 0))
    for xs in (-17.5, -13.5, 13.5, 17.5, -5.25, 5.25):
        P += window((0, -1, 0), F, xs, 4.6, 1.7, 2.7, glass, marble, "flat")
        P += window((0, 21, 0), B, -xs, 4.6, 1.7, 2.7, glass, marble, "flat")
    for xs in (-17.5, -13.5, 13.5, 17.5, -5.25, 0.0, 5.25):
        P += window((0, -1, 0), F, xs, 10.0, 1.7, 3.0, glass, marble, "tri" if xs in (-13.5, 13.5, 0.0) else "flat")
        P += window((0, 21, 0), B, -xs, 10.0, 1.7, 3.0, glass, marble, "tri" if xs in (-15.75, 15.75) else "flat")
    for sx in (-1, 1):
        for xs in (23.5, 28.5, 33.5, 38.5):
            for z, hh, ped in ((4.2, 2.3, "flat"), (8.1, 2.3, "tri")):
                P += window((0, 1, 0), F, sx * xs, z, 1.5, hh, glass, marble, ped)
                P += window((0, 17, 0), B, -sx * xs, z, 1.5, hh, glass, marble, ped)
        nrm = Vector((sx, 0, 0))
        for ys in (6.0, 12.0):
            for z, hh, ped in ((4.2, 2.3, "flat"), (8.1, 2.3, "tri")):
                P += window((sx * 44, 0, 0), nrm, ys * (1 if sx > 0 else -1) - (0 if sx > 0 else 0), z, 1.5, hh,
                            glass, marble, ped)
    # doors (front, under the portico, and back)
    for y, nrm in ((-1, F), (21, B)):
        P += window((0, y, 0), nrm, 0.0, 4.0, 2.2, 4.0, wood, marble, "tri", fw=0.3)

    # ---------------- balustrades on the roofs
    zb = 15.2
    P += balustrade((-20.4, -1.4), (20.4, -1.4), zb, marble, 0.72)
    P += balustrade((-20.4, 21.4), (20.4, 21.4), zb, marble, 0.72)
    for sx in (-1, 1):
        P += balustrade((sx * 20.4, -1.4), (sx * 20.4, 21.4), zb, marble, 0.72)
        xa, xb = (20.4, 44.4) if sx > 0 else (-44.4, -20.4)
        P += balustrade((xa, 0.6), (xb, 0.6), 11.0, marble, 0.95, sides=3)
        P += balustrade((xa, 17.4), (xb, 17.4), 11.0, marble, 0.95, sides=3)
        P += balustrade((sx * 44.4, 0.6), (sx * 44.4, 17.4), 11.0, marble, 0.95, sides=3)
        for y in (0.6, 17.4):              # dies (pedestals) with urns at the corners
            P.append(bbox(sx * 44.4 - 0.4, sx * 44.4 + 0.4, y - 0.4, y + 0.4, 11.0, 12.3, marble))
            P.append(sphere(0.35, (sx * 44.4, y, 12.65), marble, 8, 5, angle=60))
    for x in (-20.4, 20.4):
        for y in (-1.4, 21.4):
            P.append(bbox(x - 0.45, x + 0.45, y - 0.45, y + 0.45, zb, zb + 1.3, marble))
            P.append(sphere(0.38, (x, y, zb + 1.7), marble, 8, 5, angle=60))

    # ---------------- portico: podium, steps, 6 Ionic columns, entablature, pediment
    P.append(bbox(-11.5, 11.5, -9.0, -1.0, 0.0, 2.0, stone))
    for k in range(8):
        P.append(bbox(-7.5, 7.5, -13.5 + k * 0.56, -9.0, 0.0, (k + 1) * 0.25, stone))
    for sx in (-1, 1):
        P.append(bbox(sx * 7.5 - (0.8 if sx > 0 else 0) + (0 if sx > 0 else -0.0), sx * 7.5 + (0 if sx > 0 else 0.8)
                      if False else sx * 8.3, -13.6, -9.0, 0.0, 2.3, stone) if False else
                 bbox(min(sx * 7.5, sx * 8.4), max(sx * 7.5, sx * 8.4), -13.6, -9.0, 0.0, 2.3, stone))
    for x in (-8.75, -5.25, -1.75, 1.75, 5.25, 8.75):
        P += ionic_column(x, -7.6, 2.0, 14.0, 1.25, marble)
        P.append(bbox(x - 0.55, x + 0.55, -1.25, -1.0, 2.0, 14.0, marble))          # responding pilaster
    P.append(bbox(-10.6, 10.6, -8.5, -1.0, 14.0, 15.2, marble))                     # entablature
    P.append(bbox(-11.0, 11.0, -8.9, -1.0, 15.2, 15.6, marble))                     # cornice
    tri = [(-11.2, 15.6), (11.2, 15.6), (0.0, 19.6)]
    P.append(extrude(tri, "Y", -8.9, -1.0, marble))
    P.append(extrude([(-11.6, 15.5), (11.6, 15.5), (0.0, 20.0), ], "Y", -9.15, -8.85, marble))
    P.append(extrude([(-9.8, 15.85), (9.8, 15.85), (0.0, 18.95)], "Y", -9.3, -9.1, marble))   # tympanum
    med = strand((0, -9.45, 17.1), (0, -9.25, 17.1), 1.0, marble, sides=16, cap=True, angle=40)
    P.append(med)
    P.append(extrude(star_poly(5, 0.75, 0.3), "Y", -9.62, -9.4, gold, name="Star"))
    xform(P[-1], Matrix.Translation((0, 0, 17.1)) @ Matrix.Rotation(0, 4, "Y"))
    # star polygon is in (x, z) because axis 'Y' -> (x, z): centred at origin -> moved up

    # ---------------- flag mast on the roof + invented flag (neon blue, pink star)
    P.append(rev([(0.16, 18.4), (0.12, 19.0), (0.09, 29.0), (0.07, 29.6)], 8, iron, angle=60))
    P.append(sphere(0.22, (0, 0, 29.8), gold, 8, 5))
    fw, fh, nx, nz = 4.6, 3.0, 10, 4
    z_top = 29.4

    def wave(x):
        return 0.28 * math.sin(x * 1.35) * (x / fw) ** 0.8

    v, f = [], []
    for side in (-1, 1):
        for i in range(nx + 1):
            x = 0.12 + fw * i / nx
            for j in range(nz + 1):
                v.append((x, wave(x) + side * 0.02, z_top - fh + fh * j / nz - 0.05 * (x / fw) ** 2))
    off = (nx + 1) * (nz + 1)
    for i in range(nx):
        for j in range(nz):
            a, b, c, d = i * (nz + 1) + j, (i + 1) * (nz + 1) + j, (i + 1) * (nz + 1) + j + 1, i * (nz + 1) + j + 1
            f.append((a, d, c, b))
            f.append((off + a, off + b, off + c, off + d))
    for i in range(nx):        # bottom / top / free edges
        a, b = i * (nz + 1), (i + 1) * (nz + 1)
        f.append((a, b, off + b, off + a))
        a, b = i * (nz + 1) + nz, (i + 1) * (nz + 1) + nz
        f.append((b, a, off + a, off + b))
    for j in range(nz):
        a, b = nx * (nz + 1) + j, nx * (nz + 1) + j + 1
        f.append((a, b, off + b, off + a))
        a, b = j, j + 1
        f.append((b, a, off + a, off + b))
    P.append(solid("Flag", v, f, flag, 60))
    cx, cz = 0.12 + fw * 0.5, z_top - fh * 0.5
    sp = star_poly(5, 0.85, 0.34)
    v = []
    for side in (-1, 1):
        for x, z in sp:
            xx = cx + x
            v.append((xx, wave(xx) + side * 0.045, cz + z - 0.05 * (xx / fw) ** 2))
    n = len(sp)
    f = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
    for i in range(n):
        j = (i + 1) % n
        f.append((i, j, n + j, n + i))
    P.append(solid("FlagStar", v, f, fstar, 20))

    # ---------------- front railing + entrance gate (y = -40)
    yf = -39.6
    for xa, xb in ((-54.5, -5.2), (5.2, 54.5)):
        P.append(bbox(xa, xb, yf - 0.3, yf + 0.3, 0.0, 0.6, stone))
        P.append(box((xb - xa, 0.06, 0.08), ((xa + xb) / 2, yf, 0.75), iron))
        P.append(box((xb - xa, 0.06, 0.08), ((xa + xb) / 2, yf, 2.25), iron))
        nbar = int((xb - xa) / 0.5)
        for i in range(nbar):
            x = xa + (i + 0.5) * (xb - xa) / nbar
            P.append(strand((x, yf, 0.6), (x, yf, 2.45), 0.022, iron, sides=3, r1=0.0))
        for x in np.arange(xa + 5.0, xb - 1.0, 7.0):
            P.append(bbox(x - 0.35, x + 0.35, yf - 0.35, yf + 0.35, 0.0, 2.6, stone))
    for sx in (-1, 1):                    # gate piers with lanterns
        x = sx * 4.6
        P.append(bbox(x - 0.6, x + 0.6, yf - 0.6, yf + 0.6, 0.0, 3.4, stone))
        P.append(bbox(x - 0.75, x + 0.75, yf - 0.75, yf + 0.75, 3.4, 3.7, stone))
        P.append(rev([(0.12, 3.7), (0.25, 3.9), (0.25, 4.5), (0.12, 4.75), (0.0, 4.9)], 8, iron, loc=(x, yf, 0)))
        P.append(rev([(0.20, 3.95), (0.20, 4.45)], 8, glow, loc=(x, yf, 0), angle=60))
    # gate leaves (closed), a raised arch of bars in the middle
    for i in range(16):
        x = -3.8 + (i + 0.5) * 7.6 / 16
        top = 2.7 + 0.8 * math.cos(x / 4.0 * math.pi / 2)
        P.append(strand((x, yf, 0.1), (x, yf, top), 0.03, iron, sides=3))
        P.append(sphere(0.06, (x, yf, top + 0.03), gold, 6, 4))
    for z in (0.3, 1.2, 2.4):
        P.append(box((7.6, 0.08, 0.1), (0, yf, z), iron))

    # ---------------- fountain on the front lawn
    fy = -26.5
    P.append(rev([(6.0, 0.0), (6.2, 0.0), (6.2, 0.55), (5.85, 0.65), (5.6, 0.62), (5.6, 0.3)], 32, marble,
                 loc=(0, fy, 0), angle=50))
    P.append(rev([(5.62, 0.42)], 32, water, loc=(0, fy, 0), cap1=True) if False else
             surf("Pool", [(5.62 * math.cos(2 * math.pi * s / 32), fy + 5.62 * math.sin(2 * math.pi * s / 32), 0.42)
                           for s in range(32)], [tuple(range(32))], water))
    P.append(rev([(0.9, 0.4), (0.6, 0.8), (0.45, 2.0), (0.6, 2.2), (2.2, 2.45), (2.3, 2.65), (2.0, 2.7)], 16,
                 marble, loc=(0, fy, 0), angle=50))
    P.append(surf("Pool2", [(2.05 * math.cos(2 * math.pi * s / 16), fy + 2.05 * math.sin(2 * math.pi * s / 16), 2.62)
                            for s in range(16)], [tuple(range(16))], water))
    P.append(rev([(0.3, 2.6), (0.22, 3.4), (0.45, 3.65), (0.5, 3.8), (0.0, 3.9)], 10, marble, loc=(0, fy, 0)))
    P.append(rev([(0.12, 3.85), (0.09, 5.0), (0.25, 5.3), (0.0, 5.6)], 8, water, loc=(0, fy, 0), angle=60))
    return finish("Palace", P)


# =========================================================================== sport props
def make_basket_hoop():
    nb.reset_scene()
    M.clear()
    steel = mat("Metal", (0.10, 0.11, 0.12), 0.8, 0.4)
    pad = mat("Padding", (0.05, 0.20, 0.55), 0.0, 0.7)
    board = mat("Board", (0.92, 0.93, 0.95), 0.0, 0.25)
    lines = mat("Lines", (0.85, 0.10, 0.08), 0.0, 0.5)
    hoop = mat("HoopRed", (0.95, 0.32, 0.05), 0.6, 0.35)
    rope = mat("Rope", (0.95, 0.95, 0.93), 0.0, 0.9)
    P = []
    # weighted base (behind, +Y) with a padded front
    P.append(bbox(-0.6, 0.6, 0.35, 2.15, 0.0, 0.45, pad))
    P.append(bbox(-0.62, 0.62, 2.15, 2.25, 0.0, 0.5, steel))
    for x in (-0.6, 0.6):
        P.append(sphere(0.12, (x, 2.15, 0.12), steel, 8, 5))          # wheels
    # pole (square tube) raked forward, then the arm to the board
    P.append(strand((0, 1.5, 0.45), (0, 1.15, 3.35), 0.10, steel, sides=4, cap=True, angle=30))
    P.append(strand((0, 0.75, 0.45), (0, 1.25, 1.6), 0.04, steel, sides=6, cap=True))           # brace
    P.append(bbox(-0.12, 0.12, 0.0, 1.2, 3.25, 3.45, steel))
    P.append(bbox(-0.12, 0.12, 0.0, 1.0, 2.95, 3.05, steel))
    P.append(strand((0, 1.1, 3.0), (0, 0.15, 3.35), 0.035, steel, sides=6, cap=True))
    P.append(strand((0.0, 1.05, 2.3), (0, 1.12, 0.8), 0.13, pad, sides=8, cap=True, angle=50))   # pole pad
    # backboard 1.8 x 1.05, bottom at 2.90; lines = thin strips proud of the front face
    yb = -0.04
    P.append(bbox(-0.9, 0.9, yb - 0.03, yb + 0.03, 2.90, 3.95, board))
    P.append(bbox(-0.92, 0.92, yb - 0.02, yb + 0.05, 2.88, 2.92, steel))
    P.append(bbox(-0.92, 0.92, yb - 0.02, yb + 0.05, 3.93, 3.97, steel))
    for x in (-0.91, 0.91):
        P.append(bbox(x - 0.02, x + 0.02, yb - 0.02, yb + 0.05, 2.88, 3.97, steel))
    yl = yb - 0.035
    for (x0, x1, z0, z1) in ((-0.295, 0.295, 3.03, 3.08), (-0.295, 0.295, 3.43, 3.48),
                             (-0.295, -0.245, 3.03, 3.48), (0.245, 0.295, 3.03, 3.48),
                             (-0.85, 0.85, 2.95, 3.0), (-0.85, 0.85, 3.85, 3.9),
                             (-0.85, -0.8, 2.95, 3.9), (0.8, 0.85, 2.95, 3.9)):
        P.append(bbox(x0, x1, yl - 0.006, yl + 0.006, z0, z1, lines))
    # rim (r 0.23 at 3.05) + bracket + net
    R, rr, cy, zr = 0.23, 0.011, -0.07 - 0.15 - 0.23, 3.05
    ring = [(R * math.cos(2 * math.pi * k / 20), cy + R * math.sin(2 * math.pi * k / 20), zr) for k in range(20)]
    P.append(path_tube(ring, rr, hoop, sides=5, closed=True))
    P.append(bbox(-0.12, 0.12, cy + R - 0.02, yb - 0.03, zr - 0.02, zr + 0.01, hoop))
    P.append(extrude([(cy + R - 0.02, zr - 0.01), (yb - 0.03, zr - 0.01), (yb - 0.03, zr - 0.16)], "X", -0.06, 0.06, hoop))
    N, rows, Ln, rb = 12, 4, 0.42, 0.15
    pts = []
    for k in range(rows + 1):
        t = k / rows
        r = R * (1 - t) + rb * t - 0.012 * math.sin(math.pi * t)
        z = zr - Ln * t
        pts.append([Vector((r * math.cos(2 * math.pi * (i + 0.5 * k) / N),
                            cy + r * math.sin(2 * math.pi * (i + 0.5 * k) / N), z)) for i in range(N)])
    for k in range(rows):
        for i in range(N):
            a = pts[k][i]
            P.append(strand(a, pts[k + 1][i], 0.0045, rope))
            P.append(strand(a, pts[k + 1][(i - 1) % N], 0.0045, rope))
    for i in range(N):
        P.append(path_tube([pts[rows][i], pts[rows][(i + 1) % N]], 0.0045, rope, sides=3))
    return finish("BasketHoop", P)


def make_basket_court():
    bake_textures(["court"])
    nb.reset_scene()
    M.clear()
    floor = mat("CourtFloor", (1.0, 1.0, 1.0), 0.0, 0.45, img="court")
    edge = mat("Concrete", (0.35, 0.36, 0.38), 0.0, 0.9)
    L, W = 32.0, 19.0
    top = bbox(-L / 2, L / 2, -W / 2, W / 2, 0.0, 0.06, floor)
    # keep only the top face in the printed material, sides in Concrete
    me = top.data
    me.materials.append(edge)
    for p in me.polygons:
        p.material_index = 0 if p.normal.z > 0.5 else 1
    plinth = bbox(-L / 2 - 0.15, L / 2 + 0.15, -W / 2 - 0.15, W / 2 + 0.15, -0.02, 0.03, edge)
    return finish("BasketCourt", [top, plinth], planar=("CourtFloor", L, W))


def make_soccer_goal():
    nb.reset_scene()
    M.clear()
    white = mat("GoalPost", (0.95, 0.95, 0.95), 0.3, 0.35)
    steel = mat("Metal", (0.45, 0.47, 0.5), 0.8, 0.4)
    rope = mat("Rope", (0.92, 0.92, 0.90), 0.0, 0.9)
    P = []
    hw, H, dt, db = 3.66, 2.44, 0.8, 2.0
    r = 0.06
    for sx in (-1, 1):
        P.append(strand((sx * (hw + r), 0, 0), (sx * (hw + r), 0, H + r), r, white, sides=10, angle=60))
    P.append(strand((-hw - 2 * r, 0, H + r), (hw + 2 * r, 0, H + r), r, white, sides=10, cap=True, angle=60))
    # support frame (thin steel): top bars back, sloping struts, ground frame
    for sx in (-1, 1):
        x = sx * (hw + r)
        P.append(strand((x, 0.0, H + r), (x, dt, H + r), 0.025, steel, sides=6, cap=True))
        P.append(strand((x, dt, H + r), (x, db, 0.02), 0.025, steel, sides=6, cap=True))
        P.append(strand((x, 0.0, 0.025), (x, db, 0.025), 0.025, steel, sides=6, cap=True))
    P.append(strand((-hw - r, dt, H + r), (hw + r, dt, H + r), 0.025, steel, sides=6, cap=True))
    P.append(strand((-hw - r, db, 0.025), (hw + r, db, 0.025), 0.025, steel, sides=6, cap=True))
    # net: strands over top + back panel, and side panels
    rn, sp = 0.006, 0.30
    nx = int(2 * hw / sp)
    for i in range(nx + 1):
        x = -hw + 2 * hw * i / nx
        path = [(x, 0.02, H + r - 0.04), (x, dt * 0.5, H + r - 0.10), (x, dt, H + r - 0.03),
                (x, dt + (db - dt) * 0.5 + 0.10, H * 0.5), (x, db, 0.03)]
        for a, b in zip(path, path[1:]):
            P.append(strand(a, b, rn, rope))

    def net_point(s):           # s in [0, 1] along the top + back profile
        Lt = dt
        Lb = math.hypot(db - dt, H)
        d = s * (Lt + Lb)
        if d <= Lt:
            return Vector((0, d, H + r - 0.06))
        u = (d - Lt) / Lb
        return Vector((0, dt + (db - dt) * u, (H + r - 0.04) * (1 - u) + 0.03))
    for k in range(1, 12):
        p = net_point(k / 12)
        P.append(strand((-hw, p.y, p.z), (0.0, p.y + 0.06, p.z - 0.03), rn, rope))
        P.append(strand((0.0, p.y + 0.06, p.z - 0.03), (hw, p.y, p.z), rn, rope))
    for sx in (-1, 1):
        x = sx * hw
        for zl in np.arange(0.3, H, sp):
            ymax = dt + (db - dt) * (1 - zl / H)
            P.append(strand((x, 0.03, zl), (x + sx * 0.05, ymax, zl), rn, rope))
        for yl in np.arange(0.3, db, sp):
            ztop = H if yl <= dt else H * (1 - (yl - dt) / (db - dt))
            P.append(strand((x, yl, 0.03), (x + sx * 0.05, yl, ztop - 0.04), rn, rope))
    obj = finish("SoccerGoal", P)
    for o in obj:                                   # centre the footprint on the origin (depth 0..2 m)
        xform(o, Matrix.Translation((0, -db / 2, 0)))
    return obj


def make_soccer_field():
    bake_textures(["pitch"])
    nb.reset_scene()
    M.clear()
    turf = mat("Pitch", (1.0, 1.0, 1.0), 0.0, 0.9, img="pitch")
    edge = mat("Concrete", (0.32, 0.33, 0.35), 0.0, 0.9)
    L, W = 96.0, 62.0
    top = bbox(-L / 2, L / 2, -W / 2, W / 2, 0.0, 0.05, turf)
    top.data.materials.append(edge)
    for p in top.data.polygons:
        p.material_index = 0 if p.normal.z > 0.5 else 1
    return finish("SoccerField", [top], planar=("Pitch", L, W))


def make_boxing_ring():
    bake_textures(["canvas", "canvas_n"])
    nb.reset_scene()
    M.clear()
    canvas = mat("Canvas", (0.10, 0.28, 0.75), 0.0, 0.85, img="canvas", normal="canvas_n", nstrength=0.6)
    skirt = mat("Skirt", (0.04, 0.04, 0.06), 0.0, 0.7)
    band = mat("Glow", (1.0, 0.2, 0.6), emission=(1.0, 0.15, 0.55), strength=2.5)
    steel = mat("Metal", (0.12, 0.12, 0.13), 0.8, 0.4)
    red = mat("CornerRed", (0.80, 0.06, 0.06), 0.0, 0.6)
    blue = mat("CornerBlue", (0.05, 0.18, 0.75), 0.0, 0.6)
    white = mat("CornerWhite", (0.92, 0.92, 0.92), 0.0, 0.6)
    rope = mat("Rope", (0.95, 0.95, 0.95), 0.0, 0.6)
    lens = mat("Lens", (1.0, 0.95, 0.85), emission=(1.0, 0.95, 0.85), strength=6.0)
    P = []
    A, h, post = 3.65, 1.1, 3.05
    P.append(bbox(-A, A, -A, A, 0.0, h - 0.06, skirt))
    P.append(bbox(-A - 0.02, A + 0.02, -A - 0.02, A + 0.02, h - 0.34, h - 0.24, band))   # neon band
    P.append(bbox(-A, A, -A, A, h - 0.06, h, canvas))
    P.append(box((2 * A + 0.1, 0.1, 0.1), (0, -A, h - 0.03), canvas))
    P.append(box((2 * A + 0.1, 0.1, 0.1), (0, A, h - 0.03), canvas))
    P.append(box((0.1, 2 * A + 0.1, 0.1), (-A, 0, h - 0.03), canvas))
    P.append(box((0.1, 2 * A + 0.1, 0.1), (A, 0, h - 0.03), canvas))
    corners = [(-1, -1, red), (1, 1, blue), (1, -1, white), (-1, 1, white)]
    zr = [h + 0.46, h + 0.76, h + 1.07, h + 1.37]
    for sx, sy, cm in corners:
        x, y = sx * post, sy * post
        P.append(strand((x, y, h), (x, y, h + 1.55), 0.07, steel, sides=8, cap=True, angle=60))
        pad = box((0.26, 0.26, 1.15), (x - sx * 0.1, y - sy * 0.1, h + 0.92), cm, rot_z=math.pi / 4)
        P.append(pad)
    # ropes (slight sag) + spacer straps
    for z in zr:
        for (x0, y0), (x1, y1) in (((-post, -post), (post, -post)), ((post, -post), (post, post)),
                                   ((post, post), (-post, post)), ((-post, post), (-post, -post))):
            pts = []
            for k in range(5):
                t = k / 4
                pts.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, z - 0.04 * math.sin(math.pi * t)))
            P.append(path_tube(pts, 0.025, rope, sides=6))
    for sgn in (-1, 1):
        for xs in (-1.0, 1.0):
            for side in range(4):
                c = post * sgn
                if side < 2:
                    p0, p1 = (xs, c, zr[0] - 0.05), (xs, c, zr[-1] + 0.05)
                else:
                    p0, p1 = (c, xs, zr[0] - 0.05), (c, xs, zr[-1] + 0.05)
                if side % 2 == 0:
                    P.append(strand(p0, p1, 0.035, blue if sgn > 0 else red, sides=4, cap=True, angle=30))
    # steps at the red and blue corners
    for sx, cm in ((-1, red), (1, blue)):
        for k in range(3):
            d = 0.9 - k * 0.3
            P.append(box((1.0, d, (k + 1) * 0.33), (sx * (A - 0.9), sx * (A + d / 2), (k + 1) * 0.165), steel,
                         rot_z=0.0))
    # lighting rig: 4 lattice towers + square truss at 7 m, 8 spotlights aimed at the ring
    T, Z = 5.6, 7.0
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * T, sy * T
            q = 0.2
            cs = [(cx - q, cy - q), (cx + q, cy - q), (cx + q, cy + q), (cx - q, cy + q)]
            P.append(bbox(cx - 0.4, cx + 0.4, cy - 0.4, cy + 0.4, 0.0, 0.1, steel))
            for (x, y) in cs:
                P.append(strand((x, y, 0.1), (x, y, Z + 0.3), 0.025, steel, sides=4))
            for k in range(7):
                z0, z1 = 0.1 + k, 0.1 + k + 1.0
                for i in range(4):
                    a, b = cs[i], cs[(i + 1) % 4]
                    if k % 2:
                        a, b = b, a
                    P.append(strand((a[0], a[1], z0), (b[0], b[1], min(z1, Z + 0.3)), 0.015, steel, sides=3))
    for i in range(4):
        ang = i * math.pi / 2
        Rm = Matrix.Rotation(ang, 4, "Z")
        q = []
        for (dy, dz) in ((-0.2, 0.2), (0.2, 0.2), (0.0, -0.2)):
            q.append(strand((-T, -T + dy, Z + dz), (T, -T + dy, Z + dz), 0.03, steel, sides=4))
        n = 11
        for k in range(n):
            x0, x1 = -T + 2 * T * k / n, -T + 2 * T * (k + 1) / n
            for (dy0, dz0), (dy1, dz1) in (((-0.2, 0.2), (0.0, -0.2)), ((0.2, 0.2), (0.0, -0.2)),
                                           ((-0.2, 0.2), (0.2, 0.2))):
                q.append(strand((x0, -T + dy0, Z + dz0), (x1, -T + dy1, Z + dz1), 0.015, steel, sides=3))
        for xs in (-2.2, 2.2):        # spotlights hanging from the truss, aimed at the centre
            p = Vector((xs, -T, Z - 0.75))
            aim = (Vector((0, 0, h)) - p).normalized()
            q.append(strand((xs, -T, Z - 0.2), (xs, -T, Z - 0.55), 0.03, steel, sides=4))
            body = strand(p - aim * 0.3, p + aim * 0.25, 0.22, steel, sides=10, r1=0.26, cap=True, angle=50)
            q.append(body)
            q.append(strand(p + aim * 0.25, p + aim * 0.27, 0.23, lens, sides=10, cap=True, angle=50))
            yoke = [p + Vector((0.3, 0, 0)), p + Vector((0.3, 0, 0.25)), p + Vector((-0.3, 0, 0.25)),
                    p + Vector((-0.3, 0, 0))]
            q.append(path_tube(yoke, 0.025, steel, sides=4))
        for o in q:
            xform(o, Rm)
        P += q
    return finish("BoxingRing", P)


def make_ball_basket():
    bake_textures(["pebble_n"])
    nb.reset_scene()
    M.clear()
    rub = mat("Rubber", (0.85, 0.36, 0.10), 0.0, 0.75, normal="pebble_n", nstrength=0.8)
    seam = mat("Seam", (0.03, 0.03, 0.03), 0.0, 0.6)
    R = 0.12
    P = [sphere(R, (0, 0, R), rub, 28, 16)]
    rs, r0 = 0.0028, R + 0.0004
    c = Vector((0, 0, R))

    def circle(axis, alpha, n=30):
        a = Vector(axis).normalized()
        _, b1, b2 = frame_of(a)
        return [c + (a * math.cos(alpha) + (b1 * math.cos(2 * math.pi * k / n) + b2 * math.sin(2 * math.pi * k / n))
                     * math.sin(alpha)) * r0 for k in range(n)]
    for axis, alpha in (((1, 0, 0), math.pi / 2), ((0, 1, 0), math.pi / 2), ((0, 0, 1), math.radians(52)),
                        ((0, 0, -1), math.radians(52))):
        P.append(path_tube(circle(axis, alpha), rs, seam, sides=4, closed=True))
    return finish("BallBasket", P)


def truncated_icosahedron():
    p = (1 + 5 ** 0.5) / 2
    ico = [Vector(v).normalized() for v in
           [(-1, p, 0), (1, p, 0), (-1, -p, 0), (1, -p, 0), (0, -1, p), (0, 1, p), (0, -1, -p), (0, 1, -p),
            (p, 0, -1), (p, 0, 1), (-p, 0, -1), (-p, 0, 1)]]
    edges = set()
    for i in range(12):
        for j in range(i + 1, 12):
            if abs((ico[i] - ico[j]).length - (ico[0] - ico[1]).length) < 1e-4:
                edges.add((i, j))
    pt = {}
    for i, j in edges:
        pt[(i, j)] = ico[i] + (ico[j] - ico[i]) / 3
        pt[(j, i)] = ico[i] + (ico[j] - ico[i]) * 2 / 3

    def order(ps, nrm):
        c = sum(ps, Vector()) / len(ps)
        _, a, b = frame_of(nrm)
        return sorted(ps, key=lambda q: math.atan2((q - c).dot(b), (q - c).dot(a)))
    faces = []
    for i in range(12):                                     # pentagons
        ps = [pt[(i, j)] for j in range(12) if (i, j) in pt]
        faces.append(("pent", order(ps, ico[i])))
    tris = [(i, j, k) for (i, j) in edges for k in range(12) if k > j and (i, k) in edges and (j, k) in edges]
    for i, j, k in tris:                                     # hexagons
        ps = [pt[(i, j)], pt[(j, i)], pt[(j, k)], pt[(k, j)], pt[(i, k)], pt[(k, i)]]
        faces.append(("hex", order(ps, ico[i] + ico[j] + ico[k])))
    return faces


def make_ball_soccer():
    nb.reset_scene()
    M.clear()
    white = mat("BallWhite", (0.95, 0.95, 0.95), 0.0, 0.45)
    black = mat("BallBlack", (0.03, 0.03, 0.035), 0.0, 0.45)
    R = 0.11
    P = []
    for kind, ps in truncated_icosahedron():
        nrm = sum(ps, Vector()).normalized()
        n = len(ps)
        mids = []
        for i in range(n):
            mids += [ps[i], (ps[i] + ps[(i + 1) % n]) / 2]
        c = sum(ps, Vector()) / n
        outer = [q.normalized() * R * 0.985 for q in mids]
        inner = [(c + (q - c) * 0.78).normalized() * R for q in mids]
        cen = nrm * R * 1.004
        v = [tuple(cen)] + [tuple(q) for q in inner] + [tuple(q) for q in outer]
        m = len(mids)
        f = []
        for i in range(m):
            j = (i + 1) % m
            f.append((0, 1 + i, 1 + j))
            f.append((1 + i, 1 + m + i, 1 + m + j, 1 + j))
        o = nb.mesh_object("Panel", v, f, [white if kind == "hex" else black])
        # make the winding outward
        me = o.data
        if me.polygons[0].normal.dot(nrm) < 0:
            for p in me.polygons:
                p.flip()
        P.append(smooth(o, 60))
    for o in P:
        xform(o, Matrix.Translation((0, 0, R)))
    return finish("BallSoccer", P)


def make_stadium_stand():
    bake_textures(["concrete"])
    nb.reset_scene()
    M.clear()
    conc = mat("Concrete", (0.62, 0.62, 0.64), 0.0, 0.85, img="concrete")
    seat_a = mat("SeatA", (0.05, 0.35, 0.95), 0.0, 0.5)
    seat_b = mat("SeatB", (1.0, 0.18, 0.55), 0.0, 0.5)
    seat_c = mat("SeatC", (0.92, 0.92, 0.95), 0.0, 0.5)
    steel = mat("Metal", (0.55, 0.56, 0.6), 0.8, 0.35)
    P = []
    rows, dep, rise, front_h = 12, 0.8, 0.4, 1.0
    Wd = 10.0
    D = rows * dep + 0.6
    y0 = -D / 2
    prof = [(y0, 0.0), (y0, front_h + 0.2), (y0 + 0.25, front_h + 0.2), (y0 + 0.25, front_h)]
    yy = y0 + 0.6
    zz = front_h
    for r in range(rows):
        prof.append((yy, zz))
        zz += rise
        prof.append((yy, zz))
        yy += dep
        prof.append((yy, zz))
    prof.append((yy, zz + 1.1))
    prof.append((yy + 0.25, zz + 1.1))
    prof.append((yy + 0.25, 0.0))
    # remove consecutive duplicates
    clean = [prof[0]]
    for p in prof[1:]:
        if (abs(p[0] - clean[-1][0]) > 1e-6) or (abs(p[1] - clean[-1][1]) > 1e-6):
            clean.append(p)
    P.append(extrude(clean[:3] + clean[3:], "X", -Wd / 2, Wd / 2, conc, 20, name="Stand"))
    # centre aisle: half steps on each tread
    for r in range(rows):
        ya = y0 + 0.6 + r * dep
        za = front_h + r * rise + rise
        P.append(bbox(-0.55, 0.55, ya + dep * 0.5, ya + dep, za, za + rise * 0.5, conc))
    seat = [(0.10, 0.0), (0.26, 0.0), (0.26, 0.36), (0.50, 0.40), (0.60, 0.82), (0.54, 0.84), (0.44, 0.48),
            (0.08, 0.46), (0.10, 0.38)]
    xs = [s * (0.95 + 0.5 * k) for s in (-1, 1) for k in range(8)]
    for r in range(rows):
        ya = y0 + 0.6 + r * dep
        za = front_h + (r + 1) * rise
        for i, x in enumerate(sorted(xs)):
            col = i if i < 8 else 15 - i
            mi = (r + col) % 5
            mm = seat_b if mi == 0 else (seat_c if (r % 6 == 5) else seat_a)
            sp = [(ya + 0.05 + a, za + b) for a, b in seat]
            P.append(extrude(sp, "X", x - 0.22, x + 0.22, mm, 30, name="Seat"))
    # rails: front parapet and rear, aisle hand rail
    P.append(strand((-Wd / 2, y0 + 0.12, front_h + 1.05), (Wd / 2, y0 + 0.12, front_h + 1.05), 0.03, steel, sides=6))
    ztop = front_h + rows * rise
    P.append(strand((-Wd / 2, yy + 0.12, ztop + 1.1 + 0.9), (Wd / 2, yy + 0.12, ztop + 1.1 + 0.9), 0.03, steel,
                    sides=6))
    for x in (-Wd / 2 + 0.05, 0.0, Wd / 2 - 0.05):
        P.append(strand((x, y0 + 0.12, front_h + 0.2), (x, y0 + 0.12, front_h + 1.05), 0.025, steel, sides=6))
        P.append(strand((x, yy + 0.12, ztop + 1.1), (x, yy + 0.12, ztop + 2.0), 0.025, steel, sides=6))
    hr = [(0.0, y0 + 0.6 + r * dep + 0.4, front_h + (r + 1) * rise + 0.9) for r in range(rows)]
    P.append(path_tube(hr, 0.025, steel, sides=6))
    for r in range(0, rows, 3):
        p = hr[r]
        P.append(strand((0.0, p[1], p[2] - 0.9 + rise * 0.5), p, 0.02, steel, sides=4))
    return finish("StadiumStand", P)


MODELS = {
    "lm_statue": make_statue, "lm_palace": make_palace,
    "prop_basket_hoop": make_basket_hoop, "prop_basket_court": make_basket_court,
    "prop_soccer_goal": make_soccer_goal, "prop_soccer_field": make_soccer_field,
    "prop_boxing_ring": make_boxing_ring, "prop_ball_basket": make_ball_basket,
    "prop_ball_soccer": make_ball_soccer, "prop_stadium_stand": make_stadium_stand,
}


def build(name):
    objs = MODELS[name]()
    tris = nb.scene_tris()
    pts = [o.matrix_world @ v.co for o in objs for v in o.data.vertices]
    lo = [min(p[i] for p in pts) for i in range(3)]
    hi = [max(p[i] for p in pts) for i in range(3)]
    path = nb.export_glb(name, texcoords=True)
    kb = os.path.getsize(path) / 1024
    print("[landmarks] %s: %d tris (budget %d), %.0f KB, size x %.2f  y(depth) %.2f  height %.2f  "
          "(z %.2f..%.2f), mats %s" % (name, tris, BUDGET[name], kb, hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2],
                                      lo[2], hi[2], sorted({m.name for o in objs for m in o.data.materials})))
    return path


# =========================================================================== preview sheets
SHEET_W, SHEET_H = 640, 400


def _look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def _light(name, loc, target, power, size, color=(1, 1, 1)):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy, ld.size, ld.color = power, size, color
    o = nb.link(bpy.data.objects.new(name, ld))
    o.location = loc
    _look_at(o, target)


def _backface_debug():
    """Back faces rendered in pure red: inverted normals show up immediately."""
    for m in bpy.data.materials:
        if not m.use_nodes:
            continue
        nt = m.node_tree
        out = next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"), None)
        if not out or not out.inputs["Surface"].links:
            continue
        src = out.inputs["Surface"].links[0].from_socket
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = (1, 0, 0, 1)
        em.inputs["Strength"].default_value = 3.0
        mix = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(geo.outputs["Backfacing"], mix.inputs[0])
        nt.links.new(src, mix.inputs[1])
        nt.links.new(em.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs["Surface"])


def render_view(name, view="34"):
    """view: '34' (3/4 from the front-right, above), 'low' (worm's-eye from the islet),
    'far' (game-like distance), 'top'."""
    nb.reset_scene()
    bpy.ops.import_scene.gltf(filepath=os.path.join(nb.MODELS, name + ".glb"))
    scene = bpy.context.scene
    pts = []
    for o in scene.objects:
        if o.type == "MESH":
            pts += [o.matrix_world @ v.co for v in o.data.vertices]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    c, size = (lo + hi) / 2, (hi - lo)
    L = max(size.length, 0.3)
    if os.environ.get("NB_BACKFACE"):
        _backface_debug()
    world = bpy.data.worlds.new("W")
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.32, 0.40, 0.52, 1) if name.startswith("lm_") else (0.11, 0.12, 0.14, 1)
    bg.inputs["Strength"].default_value = 0.8
    scene.world = world
    zfloor = 0.0 if not name.startswith("lm_statue") else -0.05
    bpy.ops.mesh.primitive_plane_add(size=60 * L, location=(c.x, c.y, min(lo.z, zfloor) - 0.002))
    fl = bpy.context.active_object
    if name == "lm_statue":
        fl.data.materials.append(nb.material("Sea", (0.04, 0.12, 0.16), roughness=0.15))
    else:
        fl.data.materials.append(nb.material("Backdrop", (0.16, 0.17, 0.19), roughness=0.9))
    _light("Key", c + Vector((0.6, -1.0, 1.3)) * L, c, 22 * L * L, 0.8 * L)
    _light("Fill", c + Vector((-1.2, -0.8, 0.5)) * L, c, 6 * L * L, 1.2 * L, (0.85, 0.9, 1.0))
    _light("Rim", c + Vector((-0.4, 1.3, 0.9)) * L, c, 14 * L * L, 0.8 * L, (0.9, 0.95, 1.0))
    sun = bpy.data.lights.new("Sun", "SUN")
    sun.energy = 2.5
    so = nb.link(bpy.data.objects.new("Sun", sun))
    so.rotation_euler = (math.radians(40), math.radians(10), math.radians(35))
    cam_d = bpy.data.cameras.new("Cam")
    cam = nb.link(bpy.data.objects.new("Cam", cam_d))
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = SHEET_W, SHEET_H
    from bpy_extras.object_utils import world_to_camera_view
    if view == "low":
        cam_d.lens = 18
        cam.location = Vector((14.0, -34.0, 4.5))
        _look_at(cam, Vector((0, 0, 56.0)))
    else:
        d = Vector((0.75, -1.0, 0.55 if view == "34" else 1.6)).normalized()
        cam_d.lens = 50
        corners = [Vector((x, y, z)) for x in (lo.x, hi.x) for y in (lo.y, hi.y) for z in (lo.z, hi.z)]
        dist = L * 4
        for _ in range(90):
            cam.location = c + d * dist
            _look_at(cam, c)
            bpy.context.view_layer.update()
            uv = [world_to_camera_view(scene, cam, k) for k in corners]
            if min(min(p.x, p.y) for p in uv) < 0.04 or max(max(p.x, p.y) for p in uv) > 0.96:
                cam.location = c + d * dist * 1.04
                _look_at(cam, c)
                break
            dist *= 0.97
    cam_d.clip_end = 100 * L
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = int(os.environ.get("NB_SAMPLES", "24"))
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 4
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = "AgX"
    os.makedirs(PREVIEWS, exist_ok=True)
    scene.render.filepath = os.path.join(PREVIEWS, "%s_%s%s.png" % (name, view, "_bf" if os.environ.get("NB_BACKFACE") else ""))
    bpy.ops.render.render(write_still=True)
    return scene.render.filepath


def glb_stats(name):
    import json
    import struct
    with open(os.path.join(nb.MODELS, name + ".glb"), "rb") as f:
        data = f.read()
    n = struct.unpack("<I", data[12:16])[0]
    js = json.loads(data[20:20 + n])
    t = sum(js["accessors"][p["indices"]]["count"] // 3 for m in js["meshes"] for p in m["primitives"])
    return t, len(data)


def sheet(entries, fname):
    from PIL import Image, ImageDraw
    pad, cols = 4, 2 if len(entries) <= 4 else 3
    rows = (len(entries) + cols - 1) // cols
    img = Image.new("RGB", (cols * (SHEET_W + pad) + pad, rows * (SHEET_H + pad) + pad), (12, 13, 16))
    dr = ImageDraw.Draw(img)
    for i, (name, view, path) in enumerate(entries):
        x, y = pad + (i % cols) * (SHEET_W + pad), pad + (i // cols) * (SHEET_H + pad)
        img.paste(Image.open(path).convert("RGB"), (x, y))
        t, b = glb_stats(name)
        dr.rectangle((x + 4, y + 4, x + 330, y + 22), fill=(0, 0, 0))
        dr.text((x + 10, y + 8), "%s (%s)  %d tris  %.0f KB" % (name, view, t, b / 1024), fill=(235, 240, 245))
    out = os.path.join(PREVIEWS, fname)
    img.save(out, optimize=True)
    print("[sheet]", out)
    return out


def make_sheets(names):
    lm, sp = [], []
    for n in names:
        views = ["34", "low"] if n == "lm_statue" else ["34"]
        for vw in views:
            (lm if n.startswith("lm_") else sp).append((n, vw, render_view(n, vw)))
    suffix = "_bf" if os.environ.get("NB_BACKFACE") else ""
    if lm:
        sheet(lm, "landmarks_sheet%s.png" % suffix)
    if sp:
        sheet(sp, "sport_sheet%s.png" % suffix)


def resolve(args):
    out = []
    for a in args:
        if a in MODELS:
            out.append(a)
        else:
            out += [k for k in MODELS if k.endswith("_" + a) or k.split("_", 1)[1] == a]
    return out


if __name__ == "__main__":
    args = sys.argv[1:]
    only_sheet = "--sheet" in args
    no_sheet = "--no-sheet" in args
    names = resolve([a for a in args if not a.startswith("--")]) or list(MODELS)
    if not only_sheet:
        for n in names:
            build(n)
    if not no_sheet:
        make_sheets(names)
