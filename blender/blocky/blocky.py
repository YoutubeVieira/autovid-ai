"""Personnages 'jouet' articules (style blocs colores) generes par script pour Blender (bpy).

Chaque personnage = 1 maillage + 1 armature (hanches, torse, tete, bras a coude et main, jambes a genou et pied).
Les parties sont rigides (chaque bloc suit un os), comme une figurine articulee.
Personnages originaux: aucune marque ni personnage existant n'est reproduit.
"""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

# ------------------------------------------------------------------ materiaux
_MATS = {}


def mat(name, rgb, rough=0.5):
    key = (name, tuple(round(c, 3) for c in rgb))
    if key in _MATS:
        return _MATS[key]
    lin = tuple(c ** 2.2 for c in rgb)  # les couleurs sont donnees en sRGB (comme dans un nuancier)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*lin, 1)
    b.inputs["Roughness"].default_value = rough
    m.diffuse_color = (*rgb, 1)
    _MATS[key] = m
    return m


SKINS = [(0.96, 0.78, 0.60), (0.85, 0.62, 0.45), (0.62, 0.42, 0.30), (0.42, 0.28, 0.20), (0.98, 0.85, 0.70)]
BONES = ["hips", "spine", "head",
         "upper_arm.L", "forearm.L", "hand.L", "upper_arm.R", "forearm.R", "hand.R",
         "thigh.L", "shin.L", "foot.L", "thigh.R", "shin.R", "foot.R"]


class _Builder:
    def __init__(self, obj_name):
        self.name = obj_name
        self.bm = bmesh.new()
        self.dl = self.bm.verts.layers.deform.verify()
        self.mats, self.mat_idx = [], {}

    def _slot(self, material):
        if material.name not in self.mat_idx:
            self.mat_idx[material.name] = len(self.mats)
            self.mats.append(material)
        return self.mat_idx[material.name]

    def _tag(self, verts, bone, material):
        gi = BONES.index(bone)
        idx = self._slot(material)
        faces = set()
        for v in verts:
            v[self.dl][gi] = 1.0
            faces.update(v.link_faces)
        for f in faces:
            f.material_index = idx

    def box(self, center, size, bone, material, rot=None):
        v = bmesh.ops.create_cube(self.bm, size=1.0)["verts"]
        bmesh.ops.scale(self.bm, vec=Vector(size), verts=v)
        if rot is not None:
            bmesh.ops.rotate(self.bm, cent=(0, 0, 0), matrix=rot, verts=v)
        bmesh.ops.translate(self.bm, vec=Vector(center), verts=v)
        self._tag(v, bone, material)
        return v

    def cyl(self, center, r1, r2, h, bone, material, seg=20, rot=None):
        v = bmesh.ops.create_cone(self.bm, cap_ends=True, cap_tris=False, segments=seg,
                                  radius1=r1, radius2=r2, depth=h)["verts"]
        if rot is not None:
            bmesh.ops.rotate(self.bm, cent=(0, 0, 0), matrix=rot, verts=v)
        bmesh.ops.translate(self.bm, vec=Vector(center), verts=v)
        self._tag(v, bone, material)
        return v

    def sphere(self, center, r, bone, material, squash=(1, 1, 1)):
        v = bmesh.ops.create_uvsphere(self.bm, u_segments=18, v_segments=10, radius=r)["verts"]
        bmesh.ops.scale(self.bm, vec=Vector(squash), verts=v)
        bmesh.ops.translate(self.bm, vec=Vector(center), verts=v)
        self._tag(v, bone, material)
        return v

    def finish(self, collection):
        me = bpy.data.meshes.new(self.name)
        self.bm.to_mesh(me)
        self.bm.free()
        for m in self.mats:
            me.materials.append(m)
        ob = bpy.data.objects.new(self.name, me)
        collection.objects.link(ob)
        for b in BONES:
            ob.vertex_groups.new(name=b)
        bev = ob.modifiers.new("Bevel", 'BEVEL')
        bev.width, bev.segments, bev.limit_method = 0.012, 2, 'ANGLE'
        return ob


# ------------------------------------------------------------------ personnage
def make_character(name, collection, shirt=(0.9, 0.2, 0.2), pants=(0.15, 0.2, 0.5), shoes=(0.15, 0.1, 0.1),
                   skin=None, hair="cap", hair_color=(0.25, 0.15, 0.08), hat=None, hat_color=(0.1, 0.1, 0.1),
                   accessory=None, face="smile", scale=1.0, seed=0):
    rnd = random.Random(seed)
    skin = skin or rnd.choice(SKINS)
    S, P, SH = mat(f"{name}_shirt", shirt), mat(f"{name}_pants", pants), mat(f"{name}_shoes", shoes, 0.7)
    SK, HR = mat(f"{name}_skin", skin, 0.45), mat(f"{name}_hair", hair_color, 0.4)
    BLK, WHT, MOUTH = mat("face_black", (0.02, 0.02, 0.03), 0.3), mat("white", (0.95, 0.95, 0.95)), mat("mouth", (0.55, 0.12, 0.12))
    b = _Builder(name + "_mesh")

    # torse, hanches
    b.box((0, 0, 0.545), (0.32, 0.17, 0.31), "spine", S)
    b.box((0, 0, 0.375), (0.32, 0.17, 0.07), "hips", P)
    # tete
    b.box((0, 0, 0.85), (0.30, 0.30, 0.30), "head", SK)
    ey = -0.152
    if face in ("smile", "happy", "shock", "angry"):
        h = 0.075 if face != "shock" else 0.10
        for sx in (-1, 1):
            b.box((sx * 0.07, ey, 0.89), (0.045, 0.02, h), "head", BLK)
            if face == "angry":
                b.box((sx * 0.07, ey, 0.955), (0.07, 0.02, 0.018), "head", BLK, rot=Matrix.Rotation(sx * 0.4, 3, 'Y'))
        if face == "shock":
            b.box((0, ey, 0.79), (0.06, 0.02, 0.06), "head", MOUTH)
        else:
            b.box((0, ey, 0.785), (0.10, 0.02, 0.02), "head", BLK)
            for sx in (-1, 1):
                b.box((sx * 0.055, ey, 0.80), (0.02, 0.02, 0.025), "head", BLK)
        for sx in (-1, 1):
            b.box((sx * 0.105, ey, 0.82), (0.05, 0.015, 0.03), "head", mat("blush", (0.95, 0.5, 0.5), 0.8))
    # cheveux
    if hair == "cap":
        b.box((0, 0, 1.03), (0.32, 0.32, 0.07), "head", HR)
        b.box((0, -0.135, 0.97), (0.32, 0.05, 0.09), "head", HR)
        b.box((0, 0.14, 0.90), (0.32, 0.05, 0.22), "head", HR)
        for sx in (-1, 1):
            b.box((sx * 0.155, 0.0, 0.95), (0.03, 0.30, 0.12), "head", HR)
    elif hair == "spiky":
        b.box((0, 0, 1.03), (0.32, 0.32, 0.05), "head", HR)
        for i, (x, y) in enumerate([(-0.1, -0.08), (0.1, -0.08), (0, 0), (-0.1, 0.08), (0.1, 0.08)]):
            b.cyl((x, y, 1.1), 0.075, 0.0, 0.14, "head", HR, seg=4)
        b.box((0, 0.14, 0.90), (0.32, 0.05, 0.20), "head", HR)
    elif hair == "bun":
        b.box((0, 0, 1.03), (0.32, 0.32, 0.07), "head", HR)
        b.box((0, 0.14, 0.90), (0.32, 0.05, 0.22), "head", HR)
        b.box((0, -0.135, 0.98), (0.32, 0.05, 0.07), "head", HR)
        b.sphere((0, 0.05, 1.13), 0.09, "head", HR)
    elif hair == "long":
        b.box((0, 0, 1.03), (0.32, 0.32, 0.07), "head", HR)
        b.box((0, 0.14, 0.78), (0.34, 0.06, 0.52), "head", HR)
        for sx in (-1, 1):
            b.box((sx * 0.165, 0.02, 0.84), (0.03, 0.28, 0.34), "head", HR)
        b.box((0, -0.135, 0.98), (0.32, 0.05, 0.08), "head", HR)
    elif hair == "grey":
        b.box((0, 0, 1.02), (0.31, 0.31, 0.05), "head", mat("grey_hair", (0.8, 0.8, 0.84), 0.4))
        b.box((0, 0.14, 0.92), (0.31, 0.05, 0.18), "head", mat("grey_hair", (0.8, 0.8, 0.84), 0.4))
        b.box((0, -0.14, 0.98), (0.31, 0.04, 0.06), "head", mat("grey_hair", (0.8, 0.8, 0.84), 0.4))
    # chapeaux
    HT = mat(f"{name}_hat", hat_color, 0.45)
    if hat == "tophat":
        b.cyl((0, 0, 1.045), 0.22, 0.22, 0.025, "head", HT)
        b.cyl((0, 0, 1.17), 0.13, 0.13, 0.23, "head", HT)
        b.cyl((0, 0, 1.085), 0.135, 0.135, 0.04, "head", mat("hatband", (0.85, 0.15, 0.15)))
    elif hat == "helmet":
        b.sphere((0, 0, 1.0), 0.19, "head", HT, squash=(1, 1, 0.7))
        b.box((0, -0.17, 1.0), (0.3, 0.14, 0.03), "head", HT)
    elif hat == "beret":
        b.cyl((0.03, 0, 1.065), 0.19, 0.17, 0.05, "head", HT, rot=Matrix.Rotation(0.12, 3, 'Y'))
        b.cyl((0.03, 0, 1.1), 0.02, 0.02, 0.04, "head", HT)
    elif hat == "cap":
        b.box((0, 0, 1.045), (0.33, 0.33, 0.07), "head", HT)
        b.box((0, -0.24, 1.02), (0.3, 0.2, 0.025), "head", HT)
    elif hat == "chef":
        b.cyl((0, 0, 1.14), 0.16, 0.2, 0.22, "head", mat("chefhat", (0.97, 0.97, 0.97)))
    # bras (os: epaule = haut du bloc)
    for sx, side in ((-1, "R"), (1, "L")):
        x = sx * 0.225
        b.box((x, 0, 0.575), (0.12, 0.12, 0.17), f"upper_arm.{side}", S)
        b.box((x, 0, 0.415), (0.115, 0.115, 0.15), f"forearm.{side}", SK)
        b.sphere((x, 0, 0.31), 0.058, f"hand.{side}", SK)
    # jambes
    for sx, side in ((-1, "R"), (1, "L")):
        x = sx * 0.08
        b.box((x, 0, 0.26), (0.15, 0.15, 0.18), f"thigh.{side}", P)
        b.box((x, 0, 0.13), (0.14, 0.14, 0.17), f"shin.{side}", P)
        b.box((x, -0.025, 0.035), (0.15, 0.22, 0.07), f"foot.{side}", SH)
    # accessoires
    if accessory == "sash":
        flag = [(0.1, 0.25, 0.75), (0.97, 0.97, 0.97), (0.85, 0.12, 0.15)]
        rot = Matrix.Rotation(math.radians(38), 3, 'Y')
        for i, c in enumerate(flag):
            off = Vector(((i - 1) * 0.026, 0, 0))
            off.rotate(rot)
            b.box((0.0 + off.x, -0.093 + 0.0, 0.53 + off.z), (0.026, 0.02, 0.5), "spine", mat(f"sash{i}", c, 0.6), rot=rot)
    elif accessory == "cross":
        b.box((0, -0.09, 0.56), (0.12, 0.015, 0.035), "spine", mat("cross", (0.9, 0.1, 0.1)))
        b.box((0, -0.09, 0.56), (0.035, 0.015, 0.12), "spine", mat("cross", (0.9, 0.1, 0.1)))
    elif accessory == "whistle":
        b.box((0.0, -0.095, 0.62), (0.05, 0.02, 0.03), "spine", mat("whistle", (0.98, 0.8, 0.1), 0.3))
    elif accessory == "apron":
        b.box((0, -0.095, 0.47), (0.24, 0.012, 0.24), "spine", mat("apron", (0.97, 0.97, 0.95)))
    elif accessory == "vest":
        b.box((0, 0, 0.53), (0.335, 0.18, 0.2), "spine", mat("vest", (0.98, 0.55, 0.05)))
    elif accessory == "bag":
        b.box((0.0, 0.1, 0.5), (0.2, 0.1, 0.22), "spine", mat("bag", (0.45, 0.25, 0.12)))

    ob = b.finish(collection)
    ob.scale = (scale, scale, scale)
    arm = _make_armature(name, collection)
    ob.parent = arm
    mod = ob.modifiers.new("Armature", 'ARMATURE')
    mod.object = arm
    arm.scale = (scale, scale, scale)
    ob.scale = (1, 1, 1)
    return arm, ob


def _make_armature(name, collection):
    data = bpy.data.armatures.new(name + "_rig")
    arm = bpy.data.objects.new(name, data)
    collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    eb = data.edit_bones

    def bone(n, head, tail, parent=None):
        e = eb.new(n)
        e.head, e.tail = head, tail
        if parent:
            e.parent = eb[parent]
        return e

    bone("hips", (0, 0, 0.36), (0, 0, 0.40))
    bone("spine", (0, 0, 0.40), (0, 0, 0.70), "hips")
    bone("head", (0, 0, 0.70), (0, 0, 1.0), "spine")
    for sx, s in ((1, "L"), (-1, "R")):
        x = sx * 0.225
        bone(f"upper_arm.{s}", (x, 0, 0.66), (x, 0, 0.49), "spine")
        bone(f"forearm.{s}", (x, 0, 0.49), (x, 0, 0.34), f"upper_arm.{s}")
        bone(f"hand.{s}", (x, 0, 0.34), (x, 0, 0.27), f"forearm.{s}")
        x = sx * 0.08
        bone(f"thigh.{s}", (x, 0, 0.36), (x, 0, 0.18), "hips")
        bone(f"shin.{s}", (x, 0, 0.18), (x, 0, 0.07), f"thigh.{s}")
        bone(f"foot.{s}", (x, 0, 0.07), (x, -0.12, 0.03), f"shin.{s}")
    bpy.ops.object.mode_set(mode='OBJECT')
    for pb in arm.pose.bones:
        pb.rotation_mode = 'XYZ'
    arm.show_in_front = False
    data.display_type = 'STICK'
    arm.hide_viewport = False
    return arm


# ------------------------------------------------------------------ animation
def pose(arm, frame, **rots):
    """pose(arm, 24, **{'upper_arm.L': (rx, ry, rz)}) en degres; les os non cites ne sont pas modifies."""
    for bn, r in rots.items():
        pb = arm.pose.bones[bn.replace("__", ".")]
        pb.rotation_euler = tuple(math.radians(a) for a in r)
        pb.keyframe_insert("rotation_euler", frame=frame)


def reset_pose(arm, frame):
    for pb in arm.pose.bones:
        pb.rotation_euler = (0, 0, 0)
        pb.keyframe_insert("rotation_euler", frame=frame)


def key_obj(ob, frame, loc=None, rot_z=None, scale=None):
    if loc is not None:
        ob.location = loc
        ob.keyframe_insert("location", frame=frame)
    if rot_z is not None:
        ob.rotation_euler = (0, 0, math.radians(rot_z))
        ob.keyframe_insert("rotation_euler", frame=frame)
    if scale is not None:
        ob.scale = (scale, scale, scale)
        ob.keyframe_insert("scale", frame=frame)


def walk(arm, f0, f1, p0, p1, speed_cycle=16, base_scale=1.0):
    """Marche lineaire de p0 a p1 entre les images f0 et f1 (cycle de jambes/bras)."""
    d = Vector(p1) - Vector(p0)
    yaw = math.degrees(math.atan2(d.x, -d.y)) if d.length else 0  # face = -Y
    for f in range(f0, f1 + 1, speed_cycle // 4):
        t = (f - f0) / max(1, f1 - f0)
        loc = Vector(p0).lerp(Vector(p1), t)
        bob = abs(math.sin((f - f0) / speed_cycle * 2 * math.pi)) * 0.025
        key_obj(arm, f, loc=(loc.x, loc.y, loc.z + bob), rot_z=yaw)
        ph = (f - f0) / speed_cycle * 2 * math.pi
        sw = 32 * math.sin(ph)
        pose(arm, f, **{"thigh__L": (sw, 0, 0), "thigh__R": (-sw, 0, 0),
                        "shin__L": (max(0, -sw) * 0.9, 0, 0), "shin__R": (max(0, sw) * 0.9, 0, 0),
                        "upper_arm__L": (-sw * 0.9, 0, 0), "upper_arm__R": (sw * 0.9, 0, 0),
                        "forearm__L": (-18, 0, 0), "forearm__R": (-18, 0, 0)})


def idle(arm, f0, f1, step=12):
    for f in range(f0, f1 + 1, step):
        ph = (f - f0) / 48 * 2 * math.pi
        pose(arm, f, **{"spine": (1.5 * math.sin(ph), 0, 0), "head": (0, 0, 2 * math.sin(ph / 2)),
                        "upper_arm__L": (2 * math.sin(ph), 0, 2), "upper_arm__R": (-2 * math.sin(ph), 0, -2)})


def wave(arm, f0, f1, side="R"):
    s = 1 if side == "L" else -1
    n = 0
    for f in range(f0, f1 + 1, 4):
        osc = 18 * math.sin(n * 1.3)
        pose(arm, f, **{f"upper_arm__{side}": (0, 0, s * (150 if f > f0 + 2 else 60)),
                        f"forearm__{side}": (0, 0, s * (osc + 10)), "head": (0, 0, 6)})
        n += 1


def cheer(arm, f0, f1, base_z=0.0, period=16):
    for f in range(f0, f1 + 1, period // 4):
        ph = (f - f0) / period * 2 * math.pi
        up = max(0, math.sin(ph)) * 0.22
        key_obj(arm, f, loc=(arm.location.x, arm.location.y, base_z + up))
        arm_up = 150 if up > 0.02 else 110
        pose(arm, f, **{"upper_arm__L": (0, 0, arm_up), "upper_arm__R": (0, 0, -arm_up),
                        "thigh__L": (-up * 90, 0, 0), "thigh__R": (-up * 90, 0, 0),
                        "shin__L": (up * 140, 0, 0), "shin__R": (up * 140, 0, 0)})


def pop_in(arm, f0, dur=8, to_scale=1.0):
    key_obj(arm, f0, scale=0.001)
    key_obj(arm, f0 + dur // 2, scale=to_scale * 1.25)
    key_obj(arm, f0 + dur, scale=to_scale)


def linear_all(ob):
    ad = ob.animation_data
    if ad and ad.action:
        try:
            for fc in ad.action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = 'LINEAR'
        except AttributeError:
            pass  # Blender 5: actions en couches; interpolation Bezier par defaut conservee
