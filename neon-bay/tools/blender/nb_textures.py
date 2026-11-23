"""Neon Bay - procedural textures baked in Blender (Cycles, EMIT bake) for the humans.

Each texture is a shader node graph written with a tiny expression helper (Python
operators on node sockets create Math nodes), evaluated on a 1x1 UV plane and baked
to a 512x512 image with Cycles. The pixels are then quantised a little (PNG size),
fabric normal maps are derived from the baked height (wrap-around finite
differences, so they tile exactly) and everything is written as optimised PNG.

The colour textures are light, (almost) neutral greys: the game multiplies them by
material.color (glTF baseColorFactor x baseColorTexture), so the base colours stay
driven by the game. Mean values are kept high (~0.9 linear) so tinting is not darkened.

    textures(female)  -> dict(name -> png path), cached per process

Texture names / layout (UV conventions are set by gen_human.py):
    skin_m / skin_f : RGB. u in [0, .25] = body strip (arms, hands, legs: plain skin);
                      u in [.25, 1] = front projection of the head (see FACE_RECT):
                      faint blush on cheeks / nose / ears, slightly darker under-eye,
                      male: stubble shadow on jaw, chin and upper lip. Subtle pores.
    jersey / jersey_n : knitted T-shirt / hoodie (grey + tangent normal), tiles in u and v
    denim / denim_n   : twill jeans (steep diagonal lines + vertical slubs), tiles
    shoes             : grey; v in [.30, 1] leather grain (upper, belt, cap), v in [0, .26]
                        rubber sole side wall (two grooves + knurl), tiles in u
"""
import math
import os
import tempfile

import bpy  # noqa: F401
import numpy as np

SIZE = 512
# head-local rectangle (d = (p - hc) / hk) mapped to u in [.25, 1], v in [0, 1]
FACE_RECT = (-0.105, 0.105, -0.275, 0.125)
_CACHE = {}
_DIR = None


def face_uv(dx, dz):
    x0, x1, z0, z1 = FACE_RECT
    return 0.25 + 0.75 * (dx - x0) / (x1 - x0), (dz - z0) / (z1 - z0)


# --------------------------------------------------------------------------- node expressions
class X:
    """Wraps a float socket; arithmetic builds Math nodes in the current tree."""
    tree = None

    def __init__(self, sock):
        self.s = sock

    @staticmethod
    def _math(op, a, b=None, clamp=False):
        n = X.tree.nodes.new("ShaderNodeMath")
        n.operation = op
        n.use_clamp = clamp
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, X):
                X.tree.links.new(v.s, n.inputs[i])
            else:
                n.inputs[i].default_value = float(v)
        return X(n.outputs[0])

    def __add__(self, o): return X._math("ADD", self, o)
    def __radd__(self, o): return X._math("ADD", o, self)
    def __sub__(self, o): return X._math("SUBTRACT", self, o)
    def __rsub__(self, o): return X._math("SUBTRACT", o, self)
    def __mul__(self, o): return X._math("MULTIPLY", self, o)
    def __rmul__(self, o): return X._math("MULTIPLY", o, self)
    def __truediv__(self, o): return X._math("DIVIDE", self, o)
    def __rtruediv__(self, o): return X._math("DIVIDE", o, self)
    def __pow__(self, o): return X._math("POWER", self, o)
    def __neg__(self): return X._math("MULTIPLY", self, -1.0)


def sin(a): return X._math("SINE", a)
def cos(a): return X._math("COSINE", a)
def fabs(a): return X._math("ABSOLUTE", a)
def frac(a): return X._math("FRACT", a)
def sqrt(a): return X._math("SQRT", a)
def exp(a): return X._math("EXPONENT", a)
def vmin(a, b): return X._math("MINIMUM", a, b)
def vmax(a, b): return X._math("MAXIMUM", a, b)
def clamp01(a): return X._math("ADD", a, 0.0, clamp=True)


def smoothstep(e0, e1, a):
    t = clamp01((a - e0) * (1.0 / (e1 - e0)))
    return t * t * (3.0 - 2.0 * t)


def combine(x, y, z):
    n = X.tree.nodes.new("ShaderNodeCombineXYZ")
    for i, v in enumerate((x, y, z)):
        if isinstance(v, X):
            X.tree.links.new(v.s, n.inputs[i])
        else:
            n.inputs[i].default_value = float(v)
    return n.outputs[0]


def _wire(node, name, v):
    if isinstance(v, X):
        X.tree.links.new(v.s, node.inputs[name])
    elif v is not None and not hasattr(v, "is_output"):
        node.inputs[name].default_value = v
    elif v is not None:
        X.tree.links.new(v, node.inputs[name])


def noise(vec, w=None, scale=1.0, detail=2.0, rough=0.5, distortion=0.0):
    n = X.tree.nodes.new("ShaderNodeTexNoise")
    n.noise_dimensions = "4D" if w is not None else "3D"
    _wire(n, "Vector", vec)
    if w is not None:
        _wire(n, "W", w)
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    n.inputs["Roughness"].default_value = rough
    n.inputs["Distortion"].default_value = distortion
    return X(n.outputs["Fac"])


def voronoi(vec, w=None, scale=1.0, feature="F1", randomness=1.0):
    n = X.tree.nodes.new("ShaderNodeTexVoronoi")
    n.voronoi_dimensions = "4D" if w is not None else "3D"
    n.feature = feature
    _wire(n, "Vector", vec)
    if w is not None:
        _wire(n, "W", w)
    n.inputs["Scale"].default_value = scale
    n.inputs["Randomness"].default_value = randomness
    return X(n.outputs["Distance"])


def torus(u, v, ru, rv, seed=0.0):
    """Seamless 4D coordinates for tileable noise: (vector, w)."""
    a, b = u * (2 * math.pi), v * (2 * math.pi)
    return combine(cos(a) * ru + seed, sin(a) * ru, cos(b) * rv), sin(b) * rv


def ring_u(u, v, ru, sv, seed=0.0):
    """Coordinates tileable in u only (v stays linear)."""
    a = u * (2 * math.pi)
    return combine(cos(a) * ru + seed, sin(a) * ru, v * sv)


# --------------------------------------------------------------------------- bake
def _bake(name, build, channels):
    """build(u, v) -> list of X (1 or 3 channels, 0..1). Returns float array (H, W, channels)."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 4
    scene.cycles.use_denoising = False
    scene.render.bake.margin = 0
    me = bpy.data.meshes.new("TexPlane")
    me.from_pydata([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(name="UVMap")
    for li, (a, b) in enumerate(((0, 0), (1, 0), (1, 1), (0, 1))):
        uv.data[li].uv = (a, b)
    obj = bpy.data.objects.new("TexPlane", me)
    scene.collection.objects.link(obj)
    mat = bpy.data.materials.new("Tex_" + name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    X.tree = nt
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["UV"], sep.inputs[0])
    u, v = X(sep.outputs[0]), X(sep.outputs[1])
    ch = build(u, v)
    if len(ch) == 1:
        ch = [ch[0], ch[0], ch[0]]
    col = nt.nodes.new("ShaderNodeCombineColor")
    for i in range(3):
        nt.links.new(ch[i].s, col.inputs[i])
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(col.outputs[0], em.inputs["Color"])
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    img = bpy.data.images.new("bake_" + name, SIZE, SIZE, float_buffer=True, is_data=True)
    it = nt.nodes.new("ShaderNodeTexImage")
    it.image = img
    nt.nodes.active = it
    me.materials.append(mat)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.bake(type="EMIT", margin=0, use_clear=True)
    px = np.array(img.pixels[:], dtype=np.float32).reshape(SIZE, SIZE, 4)[::-1]   # row 0 = top (v = 1)
    X.tree = None
    return px[:, :, :channels]


def _normal_from_height(h, strength):
    """Tangent-space normal map (OpenGL / glTF convention, +Y = +v) from a tileable height."""
    hv = h[::-1]                                  # row 0 = v 0
    dx = (np.roll(hv, -1, 1) - np.roll(hv, 1, 1)) * 0.5
    dy = (np.roll(hv, -1, 0) - np.roll(hv, 1, 0)) * 0.5
    n = np.stack([-dx * strength, -dy * strength, np.ones_like(hv)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return (n * 0.5 + 0.5)[::-1]


def _fold(h, ph, pw):
    """Average all (ph, pw) pixel periods of a periodic image: exact periodicity, no bake noise."""
    H, W = h.shape
    t = h.reshape(H // ph, ph, W // pw, pw).mean(axis=(0, 2))
    return np.tile(t, (H // ph, W // pw))


def _save(name, arr, levels=None, mode="L"):
    from PIL import Image
    a = np.clip(arr, 0, 1)
    if levels:
        a = np.round(a * (levels - 1)) / (levels - 1)
    a8 = (a * 255 + 0.5).astype(np.uint8)
    if mode == "L" and a8.ndim == 3:
        a8 = a8[:, :, 0]
    path = os.path.join(_DIR, name + ".png")
    Image.fromarray(a8, mode).save(path, optimize=True, compress_level=9)
    return path


# --------------------------------------------------------------------------- texture designs
def _skin(female):
    def build(u, v):
        # body strip and face share pores + mottling; face features only where u > .25
        vec = combine(u * 4.0, v * 4.0, 0.0)
        mott = noise(vec, scale=2.2, detail=4, rough=0.55) - 0.5
        fine = noise(vec, scale=14.0, detail=3, rough=0.6) - 0.5
        pores = smoothstep(0.0, 0.16, voronoi(vec, scale=55.0, randomness=0.9))
        base = 0.945 + mott * 0.07 + fine * 0.035 - (1.0 - pores) * 0.035

        def blob(cx, cz, rx, rz):
            cu, cv = face_uv(cx, cz)
            su = rx * 0.75 / (FACE_RECT[1] - FACE_RECT[0])
            sv = rz / (FACE_RECT[3] - FACE_RECT[2])
            du, dv = (u - cu) * (1.0 / su), (v - cv) * (1.0 / sv)
            return exp(-(du * du + dv * dv))
        blush = (blob(0.043, -0.052, 0.024, 0.020) + blob(-0.043, -0.052, 0.024, 0.020)) * (0.9 if female else 0.6)
        blush = blush + blob(0.0, -0.050, 0.011, 0.014) * 0.8 + blob(0.0, -0.032, 0.006, 0.014) * 0.3
        blush = blush + (blob(0.082, -0.02, 0.012, 0.03) + blob(-0.082, -0.02, 0.012, 0.03)) * 0.6
        blush = blush + blob(0.0, -0.118, 0.016, 0.012) * 0.25
        blush = vmin(blush, 1.0) * (1.0 + mott * 0.6)
        under = blob(0.031, -0.024, 0.014, 0.006) + blob(-0.031, -0.024, 0.014, 0.006)
        face = smoothstep(0.24, 0.27, u)
        r = base - under * 0.03 * face
        g = base - blush * 0.075 * face - under * 0.045 * face
        b = base - blush * 0.07 * face - under * 0.03 * face
        if not female:
            # stubble shadow, in head coordinates: from the sideburns down the jaw to the chin,
            # upper lip, under the chin, fading down the neck
            x0, x1, z0, z1 = FACE_RECT
            dx = (u - 0.25) * ((x1 - x0) / 0.75) + x0
            dz = v * (z1 - z0) + z0
            t = fabs(dx) * (1.0 / 0.07)
            ztop = -0.066 + 0.046 * t * t
            zbot = -0.19 + 0.075 * t * t
            m = (1.0 - smoothstep(-0.006, 0.004, dz - ztop)) * smoothstep(0.0, 0.025, dz - zbot) * \
                (1.0 - smoothstep(0.95, 1.08, t))
            # thinner on the cheeks, densest on the chin / upper lip
            m = m * (0.65 + 0.35 * (1.0 - smoothstep(0.3, 0.9, t)))
            speck = noise(combine(u * 40.0, v * 40.0, 3.0), scale=9.0, detail=1, rough=0.4)
            m = m * face * (0.75 + speck * 0.5)
            r, g, b = r - m * 0.13, g - m * 0.12, b - m * 0.095
        return [r, g, b]
    return build


def _jersey_height(u, v):
    cols, rows = 32, 32                           # 16 px stitches: exact pixel period
    x = frac(u * cols)
    s = frac(v * rows + fabs(x - 0.5) * 0.9)
    leg = sin(frac(x * 2.0) * math.pi) ** 0.55
    loop = sin(s * math.pi) ** 0.8
    return leg * loop


def _jersey(u, v):
    h = _jersey_height(u, v)
    vec, w = torus(u, v, 1.3, 1.3, 2.0)
    heather = noise(vec, w, scale=1.6, detail=3, rough=0.6) - 0.5
    vec2, w2 = torus(u, v, 6.0, 6.0, 7.0)
    fib = noise(vec2, w2, scale=2.5, detail=2, rough=0.5) - 0.5
    return [0.885 + h * 0.085 + heather * 0.05 + fib * 0.03]


def _denim_height(u, v):
    n = 64                                         # 8 px x 4 px period: exact pixel period
    s = frac(v * n + u * (2 * n))
    tw = fabs(s - 0.5) * 2.0                        # triangle wave
    thread = 0.5 + 0.5 * cos(u * (2 * math.pi * 128))
    return smoothstep(0.15, 0.85, tw) * (0.8 + 0.2 * thread)


def _denim(u, v):
    h = _denim_height(u, v)
    vec, w = torus(u, v, 7.0, 0.7, 4.0)              # vertical slubs (warp threads)
    slub = noise(vec, w, scale=1.4, detail=3, rough=0.6) - 0.5
    vec2, w2 = torus(u, v, 1.0, 1.0, 9.0)
    fade = noise(vec2, w2, scale=1.3, detail=2, rough=0.5) - 0.5
    return [0.86 + h * 0.12 + slub * 0.09 + fade * 0.06]


def _shoes(u, v):
    grain = noise(ring_u(u, v, 14.0, 90.0, 1.0), scale=1.0, detail=2, rough=0.5) - 0.5
    leather = 0.95 + grain * 0.04 + (noise(ring_u(u, v, 1.5, 9.0, 3.0), scale=1.0, detail=3) - 0.5) * 0.05
    # sole band
    groove = 1.0 - (exp(-((v - 0.085) * 160.0) ** 2) + exp(-((v - 0.175) * 160.0) ** 2)) * 0.35
    knurl = 1.0 - fabs(sin(u * (math.pi * 120))) * 0.07 * (1.0 - smoothstep(0.06, 0.075, v))
    rub = (noise(ring_u(u, v, 12.0, 80.0, 5.0), scale=1.0, detail=2) - 0.5) * 0.04
    sole = (0.93 + rub) * groove * knurl
    t = smoothstep(0.26, 0.30, v)
    return [sole * (1.0 - t) + leather * t]


# --------------------------------------------------------------------------- public
def textures(female):
    """Bake (once per process) and return {name: png path} for one gender."""
    global _DIR
    if _DIR is None:
        _DIR = tempfile.mkdtemp(prefix="nb_tex_")
    key = "skin_f" if female else "skin_m"
    if key not in _CACHE:
        _CACHE[key] = _save(key, _bake(key, _skin(female), 3), levels=96, mode="RGB")
    if "jersey" not in _CACHE:
        g = _bake("jersey", _jersey, 1)
        _CACHE["jersey"] = _save("jersey", g, levels=64)
        h = _fold(_bake("jersey_h", lambda u, v: [_jersey_height(u, v)], 1)[:, :, 0], 16, 16)
        _CACHE["jersey_n"] = _save("jersey_n", _normal_from_height(h, 2.2), levels=64, mode="RGB")
        g = _bake("denim", _denim, 1)
        _CACHE["denim"] = _save("denim", g, levels=64)
        h = _fold(_bake("denim_h", lambda u, v: [_denim_height(u, v)], 1)[:, :, 0], 8, 4)
        _CACHE["denim_n"] = _save("denim_n", _normal_from_height(h, 2.0), levels=64, mode="RGB")
        _CACHE["shoes"] = _save("shoes", _bake("shoes", _shoes, 1), levels=64)
    return {k: _CACHE[k] for k in (key, "jersey", "jersey_n", "denim", "denim_n", "shoes")}


if __name__ == "__main__":
    import sys
    out = textures(len(sys.argv) > 1 and sys.argv[1] == "f")
    for k, p in out.items():
        print(k, p, os.path.getsize(p))
