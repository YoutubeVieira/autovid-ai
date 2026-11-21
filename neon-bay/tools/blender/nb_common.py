"""Shared helpers for the Neon Bay procedural asset pipeline (Blender 5.x, bpy module).

Every generator imports this module:  scene reset, materials, mesh building,
auto-smooth, modifier application, glTF export (+ base64 .glb.js fallback).

Conventions (Blender side, Z-up):  the glTF exporter is always called with
export_yup=True, so Blender +X -> glTF +X, Blender +Z -> glTF +Y,
Blender -Y -> glTF +Z.
"""
import base64
import math
import os

import bpy  # noqa: F401  (must come before bmesh / mathutils)
import bmesh
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODELS = os.path.join(ROOT, "models")


# --------------------------------------------------------------------------- scene
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.actions, bpy.data.armatures):
        for block in list(coll):
            coll.remove(block)


def link(obj):
    bpy.context.scene.collection.objects.link(obj)
    return obj


# --------------------------------------------------------------------------- materials
def material(name, color, metallic=0.0, roughness=0.5, emission=None, strength=0.0,
             alpha=1.0, transmission=0.0):
    """Principled material; name is the contract the game relies on."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    c = tuple(color) + (1.0,) if len(color) == 3 else tuple(color)
    bsdf.inputs["Base Color"].default_value = c
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission is not None:
        bsdf.inputs["Emission Color"].default_value = tuple(emission) + (1.0,)
        bsdf.inputs["Emission Strength"].default_value = strength
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        try:
            mat.surface_render_method = "BLENDED"
        except Exception:
            pass
    mat.diffuse_color = c
    return mat


# --------------------------------------------------------------------------- mesh building
def mesh_object(name, verts, faces, mats=(), face_mats=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.validate(clean_customdata=False)
    me.update()
    obj = link(bpy.data.objects.new(name, me))
    for m in mats:
        me.materials.append(m)
    if face_mats is not None:
        for p, mi in zip(me.polygons, face_mats):
            p.material_index = mi
    return obj


def bm_to_object(name, bm, mats=()):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = link(bpy.data.objects.new(name, me))
    for m in mats:
        me.materials.append(m)
    return obj


def lathe(profile, segments, axis="Y", cap_start=False, cap_end=False):
    """Revolve a list of (radius, axial) points around an axis. Returns verts, faces."""
    verts, faces = [], []
    n = len(profile)
    for s in range(segments):
        a = 2 * math.pi * s / segments
        ca, sa = math.cos(a), math.sin(a)
        for r, h in profile:
            if axis == "Y":
                verts.append((r * ca, h, r * sa))
            elif axis == "Z":
                verts.append((r * ca, r * sa, h))
            else:
                verts.append((h, r * ca, r * sa))
    for s in range(segments):
        s2 = (s + 1) % segments
        for i in range(n - 1):
            a, b = s * n + i, s * n + i + 1
            c, d = s2 * n + i + 1, s2 * n + i
            faces.append((a, b, c, d))
    if cap_start:
        faces.append(tuple(s * n for s in reversed(range(segments))))
    if cap_end:
        faces.append(tuple(s * n + n - 1 for s in range(segments)))
    return verts, faces


def box(name, size, loc=(0, 0, 0), mat=None, bevel=0.0, segments=1):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2])) + Vector(loc)
    obj = bm_to_object(name, bm, [mat] if mat else [])
    if bevel > 0:
        add_bevel(obj, bevel, segments)
        apply_modifiers(obj)
    return obj


def cylinder(name, radius, depth, loc=(0, 0, 0), verts=12, mat=None, axis="Z", r2=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=radius,
                          radius2=radius if r2 is None else r2, depth=depth)
    if axis == "X":
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0),
                         matrix=__import__("mathutils").Matrix.Rotation(math.pi / 2, 3, "Y"))
    elif axis == "Y":
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0),
                         matrix=__import__("mathutils").Matrix.Rotation(math.pi / 2, 3, "X"))
    bmesh.ops.translate(bm, verts=bm.verts, vec=Vector(loc))
    return bm_to_object(name, bm, [mat] if mat else [])


def uv_sphere(name, radius, loc=(0, 0, 0), seg=10, rings=6, mat=None, scale=(1, 1, 1)):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=radius)
    for v in bm.verts:
        v.co = Vector((v.co.x * scale[0], v.co.y * scale[1], v.co.z * scale[2])) + Vector(loc)
    return bm_to_object(name, bm, [mat] if mat else [])


# --------------------------------------------------------------------------- modifiers
def add_bevel(obj, width, segments=2, angle=35):
    m = obj.modifiers.new("Bevel", "BEVEL")
    m.width = width
    m.segments = segments
    m.limit_method = "ANGLE"
    m.angle_limit = math.radians(angle)
    m.harden_normals = False
    return m


def add_subsurf(obj, levels=1):
    m = obj.modifiers.new("Subsurf", "SUBSURF")
    m.levels = levels
    m.render_levels = levels
    return m


def apply_modifiers(obj):
    """Apply the modifier stack without bpy.ops (works headless)."""
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=dg)
    old = obj.data
    obj.modifiers.clear()
    obj.data = me
    if old.users == 0:
        bpy.data.meshes.remove(old)
    return obj


def auto_smooth(obj, angle=40.0):
    """Shade smooth + mark edges sharper than `angle` as sharp (Blender 4.1+ auto smooth)."""
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    lim = math.radians(angle)
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        if len(e.link_faces) == 2:
            same_mat = e.link_faces[0].material_index == e.link_faces[1].material_index
            e.smooth = same_mat and e.calc_face_angle(0.0) <= lim
        else:
            e.smooth = False
    bm.to_mesh(me)
    bm.free()
    me.update()


def flat(obj):
    for p in obj.data.polygons:
        p.use_smooth = False


def join(objs, name=None):
    """Join mesh objects into objs[0] (no bpy.ops) keeping materials."""
    target = objs[0]
    bpy.context.view_layer.update()
    bm = bmesh.new()
    mats = []
    for o in objs:
        me = o.data.copy()
        me.transform(o.matrix_world)
        remap = []
        for m in me.materials:
            if m not in mats:
                mats.append(m)
            remap.append(mats.index(m))
        for p in me.polygons:
            p.material_index = remap[p.material_index] if remap else 0
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new(name or target.name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    keep_name = name or target.name
    for o in objs:
        old = o.data
        bpy.data.objects.remove(o)
        if old.users == 0:
            bpy.data.meshes.remove(old)
    obj = link(bpy.data.objects.new(keep_name, me))
    return obj


def tri_count(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def scene_tris():
    return sum(tri_count(o) for o in bpy.context.scene.objects if o.type == "MESH")


# --------------------------------------------------------------------------- export
def write_js_fallback(glb_path):
    key = os.path.splitext(os.path.basename(glb_path))[0]
    with open(glb_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    with open(glb_path + ".js", "w") as f:
        f.write("window.NB_MODEL_DATA=window.NB_MODEL_DATA||{};window.NB_MODEL_DATA.%s='%s';" % (key, b64))


def export_glb(name, animations=False, objects=None):
    os.makedirs(MODELS, exist_ok=True)
    path = os.path.join(MODELS, name + ".glb")
    for o in bpy.context.scene.objects:
        o.select_set(objects is None or o in objects)
    kw = dict(
        filepath=path,
        export_format="GLB",
        export_yup=True,
        export_apply=True,
        export_texcoords=False,
        export_normals=True,
        export_materials="EXPORT",
        export_cameras=False,
        export_lights=False,
        use_selection=objects is not None,
        export_animations=animations,
    )
    if animations:
        kw.update(export_animation_mode="ACTIONS", export_force_sampling=True,
                  export_frame_step=1, export_optimize_animation_size=True,
                  export_anim_slide_to_zero=True, export_skins=True,
                  export_def_bones=True, export_all_influences=False)
    bpy.ops.export_scene.gltf(**kw)
    write_js_fallback(path)
    print("[nb] wrote %s (%.1f KB, %d tris)" % (path, os.path.getsize(path) / 1024, scene_tris()))
    return path
