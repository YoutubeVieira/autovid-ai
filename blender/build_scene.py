"""Construit un projet Blender (.blend) a partir du personnage OBJ: materiaux, eclairage studio, camera, rendu.
Fonctionne avec le module Python `bpy` (pip) ou dans Blender: blender -b -P build_scene.py -- <args>

Exemple:
  python build_scene.py --obj ../models/coach_senior_tpose.obj --blend ../blender/coach_scene.blend --render ../blender/coach_render.png
"""
import argparse
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
ap = argparse.ArgumentParser()
ap.add_argument("--obj", required=True)
ap.add_argument("--blend", required=True)
ap.add_argument("--render", help="PNG de sortie (rendu fixe)")
ap.add_argument("--samples", type=int, default=64)
ap.add_argument("--res", type=int, nargs=2, default=[1080, 1080])
ap.add_argument("--close", action="store_true", help="cadrage portrait (visage)")
args = ap.parse_args(argv)
args.obj, args.blend = os.path.abspath(args.obj), os.path.abspath(args.blend)
if args.render:
    args.render = os.path.abspath(args.render)

# ---------- scene vide ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------- import ----------
bpy.ops.wm.obj_import(filepath=args.obj, forward_axis='NEGATIVE_Z', up_axis='Y')
chars = [o for o in bpy.context.selected_objects if o.type == 'MESH']
col = bpy.data.collections.new("Character")
scene.collection.children.link(col)
for o in chars:
    for c in o.users_collection:
        c.objects.unlink(o)
    col.objects.link(o)

# ---------- materiaux (Principled BSDF) ----------
LOOK = {  # nom: (roughness, sss_weight, sss_radius, specular)
    "skin": (0.45, 0.35, (1.0, 0.35, 0.2), 0.45), "lips": (0.35, 0.2, (1.0, 0.3, 0.2), 0.5),
    "hair": (0.32, 0.0, None, 0.6), "brows": (0.6, 0.0, None, 0.3),
    "eye_white": (0.15, 0.0, None, 0.8), "iris": (0.2, 0.0, None, 0.8), "pupil": (0.1, 0.0, None, 0.5),
    "bra": (0.6, 0.0, None, 0.35), "leggings": (0.75, 0.0, None, 0.2), "waistband": (0.7, 0.0, None, 0.2),
    "shoes": (0.5, 0.0, None, 0.4), "soles": (0.8, 0.0, None, 0.2),
}
for mat in bpy.data.materials:
    if mat.name.split(".")[0] not in LOOK:
        continue
    rough, sss, radius, spec = LOOK[mat.name.split(".")[0]]
    base = tuple(mat.diffuse_color)
    mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs["Base Color"].default_value = base
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Subsurface Weight"].default_value = sss
    if radius:
        bsdf.inputs["Subsurface Radius"].default_value = radius
        bsdf.inputs["Subsurface Scale"].default_value = 0.02
    for key in ("Specular IOR Level",):
        if key in bsdf.inputs:
            bsdf.inputs[key].default_value = spec

# ---------- lissage ----------
for o in chars:
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
for o in chars:
    for p in o.data.polygons:
        p.use_smooth = True
    mod = o.modifiers.new("Subsurf", 'SUBSURF')
    mod.levels = 1
    mod.render_levels = 2

# ---------- studio: sol + fond en cyclo ----------
def plane(name, size, loc, rot, color, rough):
    bpy.ops.mesh.primitive_plane_add(size=size, location=loc, rotation=rot)
    p = bpy.context.active_object
    p.name = name
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = color
    b.inputs["Roughness"].default_value = rough
    p.data.materials.append(m)
    return p

plane("Floor", 14, (0, 0, 0), (0, 0, 0), (0.10, 0.13, 0.17, 1), 0.35)
plane("Backdrop", 14, (0, 3.2, 3.5), (math.radians(90), 0, 0), (0.12, 0.17, 0.22, 1), 0.8)

# ---------- eclairage trois points ----------
def area(name, loc, energy, size, color=(1, 1, 1)):
    bpy.ops.object.light_add(type='AREA', location=loc)
    l = bpy.context.active_object
    l.name = name
    l.data.energy, l.data.size, l.data.color = energy, size, color
    direction = Vector((0, 0, 0.9)) - Vector(loc)
    l.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    return l

area("Key", (-2.2, -3.0, 2.6), 180, 2.5, (1.0, 0.93, 0.85))
area("Fill", (2.8, -2.6, 1.4), 60, 3.0, (0.85, 0.92, 1.0))
area("Rim", (0.5, 2.4, 2.4), 140, 1.5, (1.0, 1.0, 1.0))

world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.18, 0.21, 0.25, 1)
bg.inputs["Strength"].default_value = 0.25

# ---------- camera ----------
cam_data = bpy.data.cameras.new("Camera")
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
cam_data.sensor_width = 36
if args.close:
    cam_data.lens = 85
    cam.location = (0, -2.0, 1.52)
    target = Vector((0, 0, 1.45))
else:
    cam_data.lens = 70
    cam.location = (0, -5.0, 0.95)
    target = Vector((0, 0, 0.85))
cam.rotation_euler = (target - Vector(cam.location)).to_track_quat('-Z', 'Y').to_euler()
cam_data.dof.use_dof = True
cam_data.dof.focus_distance = (target - Vector(cam.location)).length
cam_data.dof.aperture_fstop = 5.6

# ---------- rendu ----------
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = args.samples
scene.cycles.use_denoising = True
scene.render.resolution_x, scene.render.resolution_y = args.res
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
try:
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
except TypeError:
    scene.view_settings.view_transform = 'Filmic'

bpy.ops.wm.save_as_mainfile(filepath=args.blend)
print("Projet enregistre:", args.blend)
if args.render:
    scene.render.filepath = args.render
    bpy.ops.render.render(write_still=True)
    print("Rendu:", args.render)
