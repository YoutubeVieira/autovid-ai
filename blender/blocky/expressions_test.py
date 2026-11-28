"""Galerie des 12 expressions de visage (rendu fixe)."""
import math, os, sys
import bpy
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blocky as bk
import city
out = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
col = bpy.data.collections.new("S"); sc.collection.children.link(col)
city.build_city(col); city.build_world(sc)
for i, ex in enumerate(bk.EXPRESSIONS):
    arm, _ = bk.make_character(f"P{i}", col, shirt=city.H("#198AE6") if i % 2 else city.H("#CC130E"), pants=city.H("#1B478C"),
                               hair=["cap", "spiky", "bun", "long"][i % 4], hair_color=(0.25, 0.14, 0.07), skin=bk.SKINS[i % 5], face=ex)
    arm.location = (-3.5 + (i % 6) * 1.4, 7.0, 0.05)
    if i >= 6:
        arm.location = (-3.5 + (i - 6) * 1.4, 7.0, 1.45)
cam = bpy.data.objects.new("C", bpy.data.cameras.new("C")); col.objects.link(cam); sc.camera = cam
cam.data.lens = 40
cam.location = (0, 0.2, 1.35)
cam.rotation_euler = (Vector((0, 7.0, 1.2)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.engine = 'CYCLES'; sc.cycles.samples = 16; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1500, 800
sc.view_settings.view_transform = 'Khronos PBR Neutral'; sc.view_settings.exposure = -0.75
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
