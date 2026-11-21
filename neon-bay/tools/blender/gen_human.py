"""Neon Bay - procedural skinned humans with animations.

    python3 tools/blender/gen_human.py          # human_m + human_f
    python3 tools/blender/gen_human.py f        # only human_f

Body = metaball sculpture (ellipsoids / capsules per body part) converted to a
mesh, decimated to budget, shaded smooth. Each metaball element knows its bone
and its clothing region, so skin weights and material slots are computed from
the same implicit field that built the surface (smooth joints, no bone-heat).

Contract (glTF, export_yup): up +Y, character faces +Z (Blender -Y), origin
between the feet on the ground, A-pose bind.
Bones: Hips Spine Chest Neck Head UpperArm.L/R LowerArm.L/R Hand.L/R
       UpperLeg.L/R LowerLeg.L/R Foot.L/R  (three.js strips the dot: UpperArmL)
Materials: Skin Shirt Pants Shoes Hair (+ Eyes)
Actions: Idle Walk Run (loops), Punch, Death (one-shot) at 24 fps.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Vector, Matrix, Quaternion, Euler  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402

import nb_common as nb  # noqa: E402

FPS = 24
SURF = 0.575  # metaball surface radius / element radius (stiffness 2, threshold 0.6)
REGIONS = ["Skin", "Shirt", "Pants", "Shoes", "Hair"]


# --------------------------------------------------------------------------- body spec
class Spec:
    def __init__(self, female):
        self.female = female
        k = 1.70 / 1.80 if female else 1.0
        self.k = k
        self.H = 1.70 if female else 1.80
        sh = 0.168 if female else 0.188          # shoulder joint half-width
        hip = 0.088 if female else 0.09
        th = math.radians(24)                     # arm A-pose angle from vertical
        J = {}
        J["hips"] = Vector((0, 0.0, 0.98 * k))
        J["spine"] = Vector((0, 0.0, 1.08 * k))
        J["chest"] = Vector((0, 0.0, 1.25 * k))
        J["neck"] = Vector((0, 0.012, 1.465 * k))
        J["head"] = Vector((0, 0.0, 1.585 * k))
        J["top"] = Vector((0, 0.0, 1.80 * k))
        for s, sx in (("L", 1), ("R", -1)):
            u = Vector((sx * math.sin(th), 0.0, -math.cos(th)))
            J["sho" + s] = Vector((sx * sh, 0.005, 1.435 * k))
            J["elb" + s] = J["sho" + s] + u * (0.29 * k) + Vector((0, 0.015, 0))
            J["wri" + s] = J["elb" + s] + u * (0.255 * k) + Vector((0, -0.01, 0))
            J["fin" + s] = J["wri" + s] + u * (0.185 * k)
            J["hip" + s] = Vector((sx * hip, 0.0, 0.93 * k))
            J["kne" + s] = Vector((sx * (hip + 0.005), -0.012, 0.505 * k))
            J["ank" + s] = Vector((sx * (hip + 0.01), 0.02, 0.085 * k))
            J["toe" + s] = Vector((sx * (hip + 0.025), -0.16 * k, 0.02))
        self.J = J
        self.th = th


def build_elements(sp):
    """List of (type, params, bone, region). Sizes are *surface* radii in metres."""
    J, k, f = sp.J, sp.k, sp.female
    E = []

    def ball(c, s, bone, reg):
        E.append(("BALL", dict(co=Vector(c), r=s / SURF), bone, reg))

    def caps(p0, p1, s, bone, reg):
        p0, p1 = Vector(p0), Vector(p1)
        E.append(("CAPSULE", dict(p0=p0, p1=p1, r=s / SURF), bone, reg))

    def ell(c, semi, bone, reg, axis=None, lateral=None):
        """Ellipsoid; semi = (lateral, depth, along-axis). axis = local Z direction."""
        z = Vector(axis).normalized() if axis else Vector((0, 0, 1))
        x = Vector(lateral) if lateral else Vector((1, 0, 0))
        x = (x - z * x.dot(z)).normalized()
        y = z.cross(x)
        rot = Matrix((x, y, z)).transposed()
        E.append(("ELLIPSOID", dict(co=Vector(c), semi=Vector(semi), rot=rot, r=1.0 / SURF), bone, reg))

    hk = 0.96 if f else 1.0          # head scale
    hc = Vector((0, 0.01, 1.70 * k))
    # ---- head (hc = cranium centre). Face plane at y ~ -0.086, nose tip ~ -0.108
    ell(hc, (0.076 * hk, 0.096 * hk, 0.094 * hk), "Head", "Skin")                                       # cranium
    ell(hc + Vector((0, -0.03, -0.064)) * hk, (0.058 * hk, 0.05 * hk, 0.066 * hk), "Head", "Skin")     # face/jaw
    ell(hc + Vector((0, -0.062, -0.112)) * hk, (0.022 * hk, 0.016, 0.014), "Head", "Skin")              # chin
    ell(hc + Vector((0, -0.088, -0.038)) * hk, (0.0095, 0.015, 0.021), "Head", "Skin",
        axis=(0, -0.3, 1))                                                                                # nose
    ell(hc + Vector((0, -0.07, 0.008)) * hk, (0.054 * hk, 0.017, 0.014), "Head", "Skin")               # brow
    for sx in (1, -1):
        ell(hc + Vector((sx * 0.075, 0.006, -0.03)) * hk, (0.01, 0.022, 0.03), "Head", "Skin")          # ears
        ell(hc + Vector((sx * 0.044, -0.052, -0.036)) * hk, (0.024, 0.022, 0.02), "Head", "Skin")       # cheekbones
    # ---- neck / torso
    nr = 0.043 if f else 0.049
    caps(J["neck"] + Vector((0, 0.01, -0.02)), J["head"] + Vector((0, 0.01, 0.02)), nr, "Neck", "Skin")
    cw = 0.135 if f else 0.155
    ell(Vector((0, 0.005, 1.33 * k)), (cw, 0.098 if f else 0.105, 0.15 * k), "Chest", "Shirt")
    caps(Vector((-0.1, 0.02, 1.44 * k)), Vector((0.1, 0.02, 1.44 * k)), 0.045 if f else 0.052, "Chest", "Shirt")
    ell(Vector((0, -0.005, 1.16 * k)), (0.112 if f else 0.13, 0.085 if f else 0.092, 0.12 * k), "Spine", "Shirt")
    ell(Vector((0, 0.01, 0.985 * k)), (0.165 if f else 0.152, 0.102, 0.105 * k), "Hips", "Pants")
    for sx in (1, -1):
        if f:
            ell(Vector((sx * 0.06, -0.075, 1.285 * k)), (0.058, 0.05, 0.055), "Chest", "Shirt")   # breasts
        else:
            ell(Vector((sx * 0.07, -0.062, 1.35 * k)), (0.07, 0.04, 0.058), "Chest", "Shirt")    # pecs
        ell(Vector((sx * 0.07, 0.062, 0.935 * k)), (0.08 if f else 0.074, 0.065 if f else 0.06, 0.085 * k),
            "Hips", "Pants")                                                                     # glutes
    # ---- arms
    a = 0.86 if f else 1.0
    for s, sx in (("L", 1), ("R", -1)):
        sho, elb, wri, fin = J["sho" + s], J["elb" + s], J["wri" + s], J["fin" + s]
        u = (elb - sho).normalized()
        ball(sho + Vector((sx * 0.0, 0, -0.012)), 0.054 * a, "UpperArm." + s, "Shirt")       # deltoid
        caps(sho + u * 0.04, sho + u * 0.16, 0.051 * a, "UpperArm." + s, "Shirt")            # sleeve
        caps(sho + u * 0.17, elb, 0.043 * a, "UpperArm." + s, "Skin")
        ell(elb + (wri - elb) * 0.33, (0.043 * a, 0.039 * a, 0.1 * k), "LowerArm." + s, "Skin", axis=wri - elb)
        caps(elb + (wri - elb) * 0.5, wri, 0.03 * a, "LowerArm." + s, "Skin")
        uh = (fin - wri).normalized()
        lat = Vector((1, 0, 0))
        ell(wri + uh * 0.055, (0.019, 0.045 * a, 0.055 * k), "Hand." + s, "Skin", axis=uh, lateral=lat)  # palm
        ell(wri + uh * 0.13, (0.0145, 0.04 * a, 0.055 * k), "Hand." + s, "Skin", axis=uh, lateral=lat)   # fingers
        caps(wri + uh * 0.03 + Vector((sx * -0.004, -0.03, 0)), wri + uh * 0.085 + Vector((sx * -0.012, -0.058, 0)),
             0.0125 * a, "Hand." + s, "Skin")                                                             # thumb
    # ---- legs
    lg = 0.93 if f else 1.0
    for s, sx in (("L", 1), ("R", -1)):
        hip, kne, ank, toe = J["hip" + s], J["kne" + s], J["ank" + s], J["toe" + s]
        ball(hip + Vector((sx * 0.012, 0.0, -0.05)), 0.088 * (1.04 if f else 1.0), "UpperLeg." + s, "Pants")
        ell(hip + (kne - hip) * 0.42, (0.078 * lg, 0.082 * lg, 0.21 * k), "UpperLeg." + s, "Pants", axis=kne - hip)
        ball(kne + Vector((0, -0.002, 0.02)), 0.046 * lg, "UpperLeg." + s, "Pants")
        ell(kne + (ank - kne) * 0.3 + Vector((0, 0.018, 0)), (0.056 * lg, 0.06 * lg, 0.15 * k), "LowerLeg." + s,
            "Pants", axis=ank - kne)
        caps(kne + (ank - kne) * 0.5, ank + Vector((0, 0, 0.02)), 0.04 * lg, "LowerLeg." + s, "Pants")
        # shoe
        ball(Vector((ank.x, 0.03, 0.05)), 0.046 * lg, "Foot." + s, "Shoes")
        ell(Vector((toe.x * 0.97 + ank.x * 0.03, -0.055 * k, 0.045)), (0.05 * lg, 0.042, 0.122 * k),
            "Foot." + s, "Shoes", axis=(0, -1, 0), lateral=(1, 0, 0))
    return E


def element_field(el, p):
    t, d, _, _ = el
    if t == "BALL":
        q = (p - d["co"]).length_squared / (d["r"] ** 2)
    elif t == "CAPSULE":
        a, b = d["p0"], d["p1"]
        ab = b - a
        h = max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared))
        q = (p - (a + ab * h)).length_squared / (d["r"] ** 2)
    else:
        loc = d["rot"].transposed() @ (p - d["co"])
        loc = Vector((loc.x / d["semi"].x, loc.y / d["semi"].y, loc.z / d["semi"].z))
        q = loc.length_squared / (d["r"] ** 2)
    if q >= 1.0:
        return 0.0
    return 2.0 * (1.0 - q) ** 3


def metaball_mesh(name, elements, resolution):
    mb = bpy.data.metaballs.new(name)
    mb.resolution = resolution
    mb.render_resolution = resolution
    mb.threshold = 0.6
    obj = nb.link(bpy.data.objects.new(name, mb))
    for t, d, _, _ in elements:
        e = mb.elements.new(type=t)
        e.stiffness = 2.0
        e.radius = d["r"]
        if t == "BALL":
            e.co = d["co"]
        elif t == "CAPSULE":
            a, b = d["p0"], d["p1"]
            e.co = (a + b) / 2
            e.size_x = (b - a).length / 2
            e.rotation = Vector((1, 0, 0)).rotation_difference((b - a).normalized())
        else:
            e.co = d["co"]
            e.size_x, e.size_y, e.size_z = d["semi"]
            e.rotation = d["rot"].to_quaternion()
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    me = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
    bpy.data.objects.remove(obj)
    bpy.data.metaballs.remove(mb)
    out = nb.link(bpy.data.objects.new(name, me))
    return out


def decimate(obj, target_tris):
    tris = nb.tri_count(obj)
    if tris > target_tris:
        m = obj.modifiers.new("Decimate", "DECIMATE")
        m.decimate_type = "COLLAPSE"
        m.ratio = target_tris / tris
        m.use_collapse_triangulate = True
        nb.apply_modifiers(obj)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()


# --------------------------------------------------------------------------- armature
BONES = [
    ("Hips", "hips", "spine", None),
    ("Spine", "spine", "chest", "Hips"),
    ("Chest", "chest", "neck", "Spine"),
    ("Neck", "neck", "head", "Chest"),
    ("Head", "head", "top", "Neck"),
]
for _s in ("L", "R"):
    BONES += [
        ("UpperArm." + _s, "sho" + _s, "elb" + _s, "Chest"),
        ("LowerArm." + _s, "elb" + _s, "wri" + _s, "UpperArm." + _s),
        ("Hand." + _s, "wri" + _s, "fin" + _s, "LowerArm." + _s),
        ("UpperLeg." + _s, "hip" + _s, "kne" + _s, "Hips"),
        ("LowerLeg." + _s, "kne" + _s, "ank" + _s, "UpperLeg." + _s),
        ("Foot." + _s, "ank" + _s, "toe" + _s, "LowerLeg." + _s),
    ]


def build_armature(sp):
    arm = bpy.data.armatures.new("Armature")
    obj = nb.link(bpy.data.objects.new("Armature", arm))
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    for name, h, t, parent in BONES:
        b = arm.edit_bones.new(name)
        b.head = sp.J[h]
        b.tail = sp.J[t]
        b.roll = 0.0
        if parent:
            b.parent = arm.edit_bones[parent]
            b.use_connect = (arm.edit_bones[parent].tail - b.head).length < 1e-4
    bpy.ops.object.mode_set(mode="OBJECT")
    for pb in obj.pose.bones:
        pb.rotation_mode = "QUATERNION"
    return obj


# --------------------------------------------------------------------------- build
def hair_spec(sp):
    """Extra hair volumes (metaballs, separate field from the body)."""
    k, f = sp.k, sp.female
    hk = 0.96 if f else 1.0
    hc = Vector((0, 0.01, 1.70 * k))
    E = []

    def ell(c, semi):
        E.append(("ELLIPSOID", dict(co=Vector(c), semi=Vector(semi), rot=Matrix.Identity(3), r=1.0 / SURF),
                  "Head", "Hair"))
    if f:
        ell(hc + Vector((0, 0.03, -0.075)) * hk, (0.085, 0.07, 0.11))      # bob at the back
        ell(hc + Vector((0, 0.045, -0.15)) * hk, (0.07, 0.05, 0.07))       # ends on the nape
        for sx in (1, -1):
            ell(hc + Vector((sx * 0.062, -0.005, -0.06)) * hk, (0.03, 0.06, 0.09))  # side locks
    return E


def build_human(female):
    nb.reset_scene()
    scene = bpy.context.scene
    scene.render.fps = FPS
    sp = Spec(female)
    elements = build_elements(sp)
    mats = {
        "Skin": nb.material("Skin", (0.78, 0.55, 0.42) if not female else (0.85, 0.63, 0.5), roughness=0.55),
        "Shirt": nb.material("Shirt", (0.12, 0.3, 0.55) if not female else (0.62, 0.12, 0.28), roughness=0.8),
        "Pants": nb.material("Pants", (0.12, 0.13, 0.17) if not female else (0.2, 0.22, 0.3), roughness=0.85),
        "Shoes": nb.material("Shoes", (0.08, 0.06, 0.05), roughness=0.5),
        "Hair": nb.material("Hair", (0.09, 0.06, 0.04) if not female else (0.25, 0.13, 0.06), roughness=0.6),
        "Eyes": nb.material("Eyes", (0.04, 0.03, 0.025), roughness=0.15),
    }
    order = REGIONS + ["Eyes"]

    hk = 0.96 if female else 1.0
    hc = Vector((0, 0.01, 1.70 * sp.k))

    def scalp(c):
        """Hairline: True when a point of the head lies under the hair."""
        d = (c - hc) / hk
        if d.length > 0.17 or d.z < -0.16:
            return False
        t = max(0.0, min(1.0, (d.y + 0.1) / 0.2))  # 0 = forehead, 1 = back of the head
        if female:
            zc = 0.05 + (-0.135 - 0.05) * t ** 0.9
            side = abs(d.x) > 0.055 and d.y < -0.045 and d.z < 0.03
        else:
            zc = 0.05 + (-0.095 - 0.05) * t ** 1.1
            side = abs(d.x) > 0.06 and d.y < 0.025 and d.z < 0.015
        return d.z > zc and not side

    # dense surface -> regions are assigned BEFORE decimation so seams stay clean
    body = metaball_mesh("Body", elements, 0.0095)
    for m in order:
        body.data.materials.append(mats[m])
    me = body.data
    detail = body.vertex_groups.new(name="Detail")
    waist = 1.035 * sp.k
    for p in me.polygons:
        c = p.center
        acc, bones = {}, {}
        for el in elements:
            w = element_field(el, c)
            if w > 0:
                acc[el[3]] = acc.get(el[3], 0) + w
                bones[el[2]] = bones.get(el[2], 0) + w
        reg = max(acc, key=acc.get) if acc else "Skin"
        bone = max(bones, key=bones.get) if bones else "Hips"
        # straight hems: waistband and sleeves follow planes, not the blobby field
        if reg in ("Shirt", "Pants") and bone in ("Hips", "Spine", "Chest"):
            reg = "Shirt" if c.z > waist else "Pants"
        elif bone.startswith("UpperArm"):
            sd = bone[-1]
            sho, elb = sp.J["sho" + sd], sp.J["elb" + sd]
            t = (c - sho).dot(elb - sho) / (elb - sho).length_squared
            reg = "Shirt" if t < 0.5 else "Skin"
        if c.z < 0.105 * sp.k and abs(c.x) > 0.02:
            reg = "Shoes"
        if scalp(c):
            reg = "Hair"
        p.material_index = order.index(reg)
    for v in me.vertices:
        if v.co.z > sp.J["head"].z - 0.03 or abs(v.co.x) > sp.J["wriL"].x - 0.02:
            detail.add([v.index], 0.45, "REPLACE")
    # flat shoe soles
    for v in me.vertices:
        if v.co.z < 0.006:
            v.co.z = 0.0

    # ---- hair cap: copy of the (dense) hair faces pushed out along the normals,
    # tapering to zero at the hairline so it blends into the scalp
    off = 0.012 if female else 0.0075
    bm = bmesh.new()
    bm.from_mesh(me)
    hair_idx = order.index("Hair")
    cap_faces = [f_ for f_ in bm.faces if f_.material_index == hair_idx]
    capbm = bmesh.new()
    vmap = {}
    for f_ in cap_faces:
        vs = []
        for v in f_.verts:
            if v.index not in vmap:
                vmap[v.index] = (capbm.verts.new(v.co), v.normal.copy())
            vs.append(vmap[v.index][0])
        try:
            capbm.faces.new(vs)
        except ValueError:
            pass
    bm.free()
    capbm.verts.ensure_lookup_table()
    ring = {}
    frontier = [v for v in capbm.verts if v.is_boundary]
    for v in frontier:
        ring[v] = 0
    lvl = 0
    while frontier and lvl < 4:
        lvl += 1
        nxt = []
        for v in frontier:
            for e in v.link_edges:
                o = e.other_vert(v)
                if o not in ring:
                    ring[o] = lvl
                    nxt.append(o)
        frontier = nxt
    nrm = {cv: n for cv, n in vmap.values()}
    for v in capbm.verts:
        r = ring.get(v, 4)
        v.co = v.co + nrm[v] * off * (0.15 + 0.85 * min(1.0, r / 3.0))
    hair = nb.bm_to_object("HairCap", capbm, [mats["Hair"]])
    decimate(hair, 440 if female else 420)

    # ---- decimate the body, keeping more triangles on the head and hands
    m = body.modifiers.new("Decimate", "DECIMATE")
    m.decimate_type = "COLLAPSE"
    m.ratio = 4900.0 / nb.tri_count(body)
    m.use_collapse_triangulate = True
    m.vertex_group = "Detail"
    m.vertex_group_factor = 1.0
    m.invert_vertex_group = True
    nb.apply_modifiers(body)
    body.vertex_groups.clear()

    parts = [body, hair]
    hv = hair_spec(sp)
    if hv:
        vol = metaball_mesh("HairVol", hv, 0.012)
        decimate(vol, 420)
        vol.data.materials.append(mats["Hair"])
        parts.append(vol)
    # ---- eyes, placed on the face surface by ray casting
    bvh = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
    for sx in (1, -1):
        hit = bvh.ray_cast(Vector((sx * 0.031 * hk, -0.5, hc.z - 0.016 * hk)), Vector((0, 1, 0)))
        if hit[0] is not None:
            pos = hit[0] + Vector((0, 0.0055, 0))
            parts.append(nb.uv_sphere("Eye", 0.0112 * hk, pos, 8, 6, mats["Eyes"]))
    body = nb.join(parts, "Body")
    nb.auto_smooth(body, 75)

    # ---- skin weights from the element fields (hair/eyes follow the head)
    armobj = build_armature(sp)
    bone_names = [b[0] for b in BONES]
    groups = {n: body.vertex_groups.new(name=n) for n in bone_names}
    head_z = sp.J["head"].z - 0.02
    for v in body.data.vertices:
        acc = {}
        for el in elements:
            w = element_field(el, v.co)
            if w > 0:
                acc[el[2]] = acc.get(el[2], 0) + w
        if not acc or (v.co.z > head_z + 0.03 and abs(v.co.x) < 0.11 and sum(acc.values()) < 0.3):
            acc = {"Head": 1.0}
        best = sorted(acc.items(), key=lambda kv: -kv[1])[:4]
        tot = sum(w for _, w in best)
        for n, w in best:
            w /= tot
            if w > 0.02:
                groups[n].add([v.index], w, "REPLACE")
    body.parent = armobj
    mod = body.modifiers.new("Armature", "ARMATURE")
    mod.object = armobj
    tris = nb.tri_count(body)
    make_actions(armobj, sp)
    path = nb.export_glb("human_f" if female else "human_m", animations=True)
    return path, tris


# --------------------------------------------------------------------------- animation
def pose_quat(pb, pitch=0.0, out=0.0, yaw=0.0):
    """Rotation given in armature axes (degrees): out about Y, then pitch about X,
    then yaw about Z; converted into the bone's local rest frame."""
    R = (Matrix.Rotation(math.radians(yaw), 3, "Z") @ Matrix.Rotation(math.radians(pitch), 3, "X")
         @ Matrix.Rotation(math.radians(out), 3, "Y"))
    M = pb.bone.matrix_local.to_3x3()
    return (M.inverted() @ R @ M).to_quaternion()


def key_pose(armobj, frame, pose):
    """pose: bone -> (pitch, out, yaw) degrees; '_loc' -> armature-space hips offset."""
    for pb in armobj.pose.bones:
        p, o, y = pose.get(pb.name, (0, 0, 0))
        q = pose_quat(pb, p, o, y)
        pb.rotation_quaternion = q
        pb.keyframe_insert("rotation_quaternion", frame=frame, group=pb.name)
        if pb.name == "Hips":
            M = pb.bone.matrix_local.to_3x3()
            pb.location = M.inverted() @ Vector(pose.get("_loc", (0, 0, 0)))
            pb.keyframe_insert("location", frame=frame, group=pb.name)


def legs(pose, side, hip, knee, foot_world=0.0, out=0.0):
    pose["UpperLeg." + side] = (hip, out, 0)
    pose["LowerLeg." + side] = (knee, 0, 0)
    pose["Foot." + side] = (foot_world - hip - knee, 0, 0)


ARM_DOWN = 18  # degrees from the A-pose towards the body


def arms(pose, side, swing, elbow, down=ARM_DOWN, yaw=0.0, hand=0.0):
    sx = 1 if side == "L" else -1
    pose["UpperArm." + side] = (swing, sx * down, sx * yaw)
    pose["LowerArm." + side] = (-elbow, 0, 0)
    pose["Hand." + side] = (hand, 0, 0)


def idle_pose(t):
    ph = 2 * math.pi * t
    b = math.sin(ph)
    p = {"_loc": (0, 0, -0.004 + 0.003 * b)}
    p["Spine"] = (1.0 + 0.6 * b, 0, 0)
    p["Chest"] = (-1.0 - 1.2 * b, 0, 0)
    p["Neck"] = (2, 0, 0)
    p["Head"] = (-1 + 0.8 * b, 0, 2.5 * math.sin(ph))
    arms(p, "L", 2 + 1.5 * b, 10 + 2 * b)
    arms(p, "R", 2 - 1.5 * b, 10 - 2 * b)
    legs(p, "L", -2, 4, 0, out=-1.5)
    legs(p, "R", 2, 3, 0, out=1.5)
    return p


def walk_pose(t):
    p = {}
    ph = 2 * math.pi * t
    for side, o in (("L", 0.0), ("R", math.pi)):
        a = ph + o
        hip = -24 * math.sin(a) + 3
        knee = 6 + 52 * max(0.0, math.cos(a)) ** 2 + 10 * max(0.0, -math.sin(a)) * max(0.0, math.cos(a + 0.6))
        foot = -12 * math.sin(a) + 10 * max(0.0, -math.sin(a + 0.9))
        legs(p, side, hip, knee, foot)
        arms(p, side, 20 * math.sin(a), 14 + 16 * max(0.0, -math.sin(a)), down=ARM_DOWN + 2)
    p["_loc"] = (-0.018 * math.cos(ph), 0, -0.012 + 0.016 * math.cos(2 * ph))
    p["Hips"] = (0, 0, 5 * math.sin(ph))
    p["Spine"] = (3, 0, -4 * math.sin(ph))
    p["Chest"] = (1, 0, -4 * math.sin(ph))
    p["Neck"] = (1, 0, 0)
    p["Head"] = (-2 + 1.5 * math.cos(2 * ph), 0, 2.5 * math.sin(ph))
    return p


def run_pose(t):
    p = {}
    ph = 2 * math.pi * t
    for side, o in (("L", 0.0), ("R", math.pi)):
        a = ph + o
        hip = -40 * math.sin(a) - 8
        knee = 22 + 78 * max(0.0, math.cos(a)) ** 1.5 + 12 * max(0.0, math.sin(a))
        foot = -16 * math.sin(a) + 18 * max(0.0, -math.sin(a + 0.8))
        legs(p, side, hip, knee, foot)
        arms(p, side, 32 * math.sin(a) + 2, 92 - 12 * math.sin(a), down=ARM_DOWN - 2, yaw=-10)
    p["_loc"] = (0, -0.0, -0.06 + 0.035 * math.cos(2 * ph + math.pi))
    p["Hips"] = (6, 0, 8 * math.sin(ph))
    p["Spine"] = (6, 0, -7 * math.sin(ph))
    p["Chest"] = (2, 0, -6 * math.sin(ph))
    p["Neck"] = (-3, 0, 0)
    p["Head"] = (-4, 0, 3 * math.sin(ph))
    return p


def guard(p, twist=0.0):
    arms(p, "L", -40, 98, down=12, yaw=-16, hand=-10)
    arms(p, "R", -32, 106, down=12, yaw=-18, hand=-10)
    legs(p, "L", -16, 16, 0, out=-3)
    legs(p, "R", 10, 12, 0, out=3)
    p["_loc"] = (0, 0, -0.03)
    p["Hips"] = (0, 0, twist * 0.4 - 10)
    p["Spine"] = (5, 0, twist * 0.3)
    p["Chest"] = (3, 0, twist * 0.3)
    p["Head"] = (-6, 0, 8 - twist * 0.6)
    return p


def punch_pose(t):
    # 0 guard -> .25 wind-up -> .42 full extension (right jab-cross) -> 1 back to guard
    p = guard({})
    if t < 0.25:
        k = t / 0.25
        p = guard({}, twist=-10 * k)
    elif t < 0.42:
        k = (t - 0.25) / 0.17
        k = k * k * (3 - 2 * k)
        p = guard({}, twist=-10 + 42 * k)
        arms(p, "R", -32 - 56 * k, 106 * (1 - k) + 4 * k, down=12 + 4 * k, yaw=-18 - 4 * k, hand=-10 + 10 * k)
        arms(p, "L", -40 + 6 * k, 98 + 14 * k, down=12, yaw=-16, hand=-10)
    else:
        k = (t - 0.42) / 0.58
        k = k * k * (3 - 2 * k)
        p = guard({}, twist=32 * (1 - k))
        arms(p, "R", -88 + 56 * k, 4 + 102 * k, down=16 - 4 * k, yaw=-22 + 4 * k, hand=0 - 10 * k)
        arms(p, "L", -34 - 6 * k, 112 - 14 * k, down=12, yaw=-16, hand=-10)
    return p


def death_pose(t):
    """Hit, knees buckle, fall on the back, settle."""
    keys = [0.0, 0.12, 0.3, 0.55, 0.66, 0.75, 1.0]

    def at(vals):
        for i in range(len(keys) - 1):
            if t <= keys[i + 1]:
                k = (t - keys[i]) / (keys[i + 1] - keys[i])
                k = k * k * (3 - 2 * k)
                return vals[i] + (vals[i + 1] - vals[i]) * k
        return vals[-1]
    p = {}
    hip_pitch = at([0, 6, -25, -86, -91, -89, -90])
    drop = at([0, -0.05, -0.32, -0.78, -0.86, -0.84, -0.855])
    back = at([0, 0.03, 0.16, 0.34, 0.4, 0.4, 0.4])
    p["_loc"] = (0, back, drop)
    p["Hips"] = (hip_pitch, 0, at([0, 4, 8, 6, 5, 5, 5]))
    p["Spine"] = (at([0, 14, 4, -4, 0, 0, 0]), 0, 0)
    p["Chest"] = (at([0, 10, -2, -6, 2, 1, 0]), 0, 0)
    p["Neck"] = (at([0, -18, -10, 6, -4, -2, 0]), 0, 0)
    p["Head"] = (at([0, -20, -8, 10, -6, -4, -4]), 0, at([0, 0, 10, 20, 28, 30, 30]))
    kl = at([4, 40, 70, 30, 20, 22, 25])
    legs(p, "L", at([-2, -20, -40, -6, 0, -4, -8]) - 0, kl, 0, out=at([0, -2, -5, -10, -12, -12, -12]))
    legs(p, "R", at([2, -10, -25, 4, 6, 4, 2]), at([3, 30, 50, 15, 8, 10, 10]), 0, out=at([0, 2, 5, 8, 9, 9, 9]))
    arms(p, "L", at([2, -40, -70, -20, 4, 6, 8]), at([10, 50, 30, 15, 8, 10, 12]),
         down=at([ARM_DOWN, 10, -20, -45, -55, -52, -50]))
    arms(p, "R", at([2, -30, -80, -30, 2, 4, 6]), at([10, 60, 40, 20, 12, 14, 15]),
         down=at([ARM_DOWN, 5, -25, -40, -48, -46, -45]))
    return p


ACTIONS = [
    # name, frames, pose fn, loop
    ("Idle", 48, idle_pose, True),
    ("Walk", 24, walk_pose, True),
    ("Run", 16, run_pose, True),
    ("Punch", 16, punch_pose, False),
    ("Death", 36, death_pose, False),
]


def make_actions(armobj, sp):
    ad = armobj.animation_data_create()
    for name, frames, fn, loop in ACTIONS:
        act = bpy.data.actions.new(name)
        act.use_fake_user = True
        ad.action = act
        step = 2 if frames > 20 else 1
        fr = list(range(0, frames + 1, step))
        if fr[-1] != frames:
            fr.append(frames)
        for f_ in fr:
            t = f_ / frames
            key_pose(armobj, f_, fn(0.0 if (loop and f_ == frames) else t) if loop else fn(t))
        track = ad.nla_tracks.new()
        track.name = name
        strip = track.strips.new(name, 0, act)
        strip.name = name
        track.mute = True
        ad.action = None
    # reset the pose to rest so the bind pose is exported cleanly
    for pb in armobj.pose.bones:
        pb.rotation_quaternion = Quaternion()
        pb.location = Vector()


if __name__ == "__main__":
    which = sys.argv[1:] or ["m", "f"]
    for w in which:
        p, t = build_human(w == "f")
        print("[human] %s: %d tris" % (p, t))
