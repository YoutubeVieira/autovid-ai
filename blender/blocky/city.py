"""Decor de ville 'jouet': rue, maisons colorees, mairie avec tour a horloge, arbres, lampadaires, guirlandes."""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

from blocky import _Builder, mat  # noqa: F401  (meme module que les personnages)

PALETTE = [(0.95, 0.35, 0.30), (0.98, 0.75, 0.25), (0.35, 0.65, 0.95), (0.45, 0.80, 0.50),
           (0.95, 0.55, 0.75), (0.97, 0.60, 0.25), (0.65, 0.50, 0.90), (0.95, 0.95, 0.85)]
ROOFS = [(0.65, 0.18, 0.15), (0.25, 0.30, 0.55), (0.55, 0.30, 0.15), (0.20, 0.40, 0.30)]


class _Static(_Builder):
    """_Builder sans groupes de sommets: on utilise un seul groupe 'hips' factice supprime ensuite."""

    def finish(self, collection):
        me = bpy.data.meshes.new(self.name)
        self.bm.to_mesh(me)
        self.bm.free()
        for m in self.mats:
            me.materials.append(m)
        ob = bpy.data.objects.new(self.name, me)
        collection.objects.link(ob)
        return ob


def _wedge(b, center, size, material, bone="hips"):
    """Toit en prisme triangulaire (pignon face a Y)."""
    cx, cy, cz = center
    w, d, h = size
    verts = [(cx - w / 2, cy - d / 2, cz), (cx + w / 2, cy - d / 2, cz), (cx, cy - d / 2, cz + h),
             (cx - w / 2, cy + d / 2, cz), (cx + w / 2, cy + d / 2, cz), (cx, cy + d / 2, cz + h)]
    vs = [b.bm.verts.new(v) for v in verts]
    for f in ((0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (0, 2, 5, 3), (1, 4, 5, 2)):
        b.bm.faces.new([vs[i] for i in f])
    b._tag(vs, bone, material)


def build_city(collection, seed=3, length=34):
    rnd = random.Random(seed)
    b = _Static("City")
    G = mat("grass", (0.35, 0.72, 0.30), 0.9)
    ROAD = mat("road", (0.20, 0.21, 0.25), 0.8)
    WALK = mat("sidewalk", (0.82, 0.80, 0.74), 0.8)
    WIN = mat("window", (0.55, 0.82, 0.98), 0.1)
    DOOR = mat("door", (0.45, 0.25, 0.12), 0.6)
    LINE = mat("line", (0.95, 0.9, 0.5), 0.7)

    b.box((0, length / 2 + 8, -0.06), (90, length + 60, 0.1), "hips", G)
    b.box((0, length / 2 + 6, 0.0), (6.0, length + 28, 0.06), "hips", ROAD)
    for sx in (-1, 1):
        b.box((sx * 3.9, length / 2 + 6, 0.03), (1.8, length + 28, 0.12), "hips", WALK)
    for y in range(0, length + 24, 4):
        b.box((0, y, 0.04), (0.18, 1.4, 0.02), "hips", LINE)

    # maisons
    y = 2.0
    while y < length - 4:
        for sx in (-1, 1):
            w, d, h = rnd.uniform(3.4, 4.2), rnd.uniform(3.6, 4.2), rnd.uniform(2.6, 3.8)
            x = sx * (4.8 + d / 2 + rnd.uniform(0.2, 0.8))
            col = mat(f"house{len(b.mats)}", rnd.choice(PALETTE), 0.7)
            b.box((x, y, h / 2), (d, w, h), "hips", col)
            _wedge(b, (x, y, h), (d + 0.3, w + 0.3, 1.3), mat("roof", rnd.choice(ROOFS), 0.6))
            fx = x - sx * (d / 2 + 0.02)
            b.box((fx, y, 0.8), (0.06, 0.8, 1.6), "hips", DOOR)
            for dy in (-1.2, 1.2):
                b.box((fx, y + dy, 1.7), (0.05, 0.7, 0.7), "hips", WIN)
            if rnd.random() < 0.5:
                b.box((x + sx * 0.5, y + 0.7, h + 1.0), (0.4, 0.4, 0.9), "hips", mat("chimney", (0.55, 0.3, 0.25)))
            # arbre devant certaines maisons
            if rnd.random() < 0.6:
                tx = sx * 4.4
                ty = y + rnd.uniform(1.8, 2.3)
                b.cyl((tx, ty, 0.6), 0.14, 0.18, 1.2, "hips", mat("trunk", (0.45, 0.28, 0.15)), seg=8)
                b.sphere((tx, ty, 1.7), rnd.uniform(0.7, 0.95), "hips", mat("leaf", (0.2, 0.62, 0.25), 0.8))
        y += 4.6

    # lampadaires
    for yy in range(3, length, 7):
        for sx in (-1, 1):
            b.cyl((sx * 3.3, yy, 1.4), 0.05, 0.05, 2.8, "hips", mat("lampost", (0.15, 0.15, 0.18)), seg=8)
            b.sphere((sx * 3.3, yy, 2.85), 0.18, "hips", mat("lamp", (1.0, 0.9, 0.55), 0.3))

    # mairie
    my = length + 6
    cream = mat("mairie", (0.86, 0.76, 0.58), 0.7)
    b.box((0, my, 2.6), (12, 5, 5.2), "hips", cream)
    b.box((0, my - 3.2, 0.2), (8, 1.6, 0.4), "hips", WALK)
    b.box((0, my - 2.9, 0.5), (7, 1.0, 0.2), "hips", WALK)
    for cx in (-3.2, -1.1, 1.1, 3.2):
        b.cyl((cx, my - 2.8, 2.4), 0.28, 0.28, 4.4, "hips", mat("col", (0.97, 0.95, 0.9)), seg=12)
    _wedge(b, (0, my - 0.2, 5.1), (12.6, 6.2, 2.0), mat("mairieroof", (0.28, 0.32, 0.42), 0.6))
    b.box((0, my - 2.6, 1.3), (1.6, 0.1, 2.6), "hips", mat("bigdoor", (0.3, 0.2, 0.4), 0.6))
    for sx in (-1, 1):
        for wy in (-4.4, 4.4):
            b.box((sx * 3 + (0 if wy < 0 else 0), my - 2.52, 2.8), (1.2, 0.08, 1.5), "hips", WIN)
    b.box((0, my, 8.2), (3, 3, 4.6), "hips", cream)
    b.cyl((0, my - 1.55, 8.6), 1.0, 1.0, 0.12, "hips", mat("clock", (0.98, 0.98, 0.95)), seg=24,
          rot=Matrix.Rotation(math.pi / 2, 3, 'X'))
    b.box((0, my - 1.64, 8.9), (0.09, 0.05, 0.7), "hips", mat("hand", (0.1, 0.1, 0.1)))
    b.box((0.25, my - 1.64, 8.6), (0.5, 0.05, 0.09), "hips", mat("hand", (0.1, 0.1, 0.1)))
    _wedge(b, (0, my, 10.5), (3.4, 3.4, 1.8), mat("towerroof", (0.7, 0.15, 0.15), 0.6))
    # drapeau tricolore
    b.cyl((4.8, my - 2.7, 5.2), 0.05, 0.05, 3.0, "hips", mat("pole", (0.7, 0.7, 0.7)), seg=8)
    for i, c in enumerate([(0.1, 0.25, 0.75), (0.97, 0.97, 0.97), (0.85, 0.12, 0.15)]):
        b.box((5.2 + i * 0.4, my - 2.7, 6.2), (0.4, 0.04, 0.7), "hips", mat(f"fl{i}", c, 0.7))

    # guirlandes (fanions) en travers de la rue
    flags = [(0.95, 0.25, 0.25), (0.98, 0.8, 0.2), (0.3, 0.6, 0.95), (0.4, 0.8, 0.4)]
    for yy in (9, 15, 21, 27):
        for i in range(14):
            x = -4.6 + i * (9.2 / 13)
            z = 3.4 - 0.55 * math.sin(math.pi * i / 13)
            fm = mat(f"flag{i % 4}", flags[i % 4], 0.7)
            pts = ((x - 0.18, yy, z), (x + 0.18, yy, z), (x, yy, z - 0.4))
            vs = [b.bm.verts.new(p) for p in pts]
            vb = [b.bm.verts.new((p[0], p[1] + 0.004, p[2])) for p in pts]
            b.bm.faces.new(vs)
            b.bm.faces.new(vb[::-1])
            b._tag(vs + vb, "hips", fm)
    return b.finish(collection)


def build_world(scene, sun_strength=2.2):
    world = bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.sky_type = 'MULTIPLE_SCATTERING'
    sky.sun_elevation = math.radians(32)
    sky.sun_rotation = math.radians(210)
    sky.sun_size = math.radians(1.5)
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = 0.35
    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    sun = bpy.context.active_object
    sun.name = "Sun"
    sun.data.energy = sun_strength
    sun.data.color = (1.0, 0.95, 0.85)
    sun.rotation_euler = (math.radians(50), 0, math.radians(35))
    return sun
