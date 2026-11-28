"""Test visuel: galerie de personnages + decor, un rendu fixe."""
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blocky as bk  # noqa: E402
import city  # noqa: E402

out = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
col = bpy.data.collections.new("Scene")
sc.collection.children.link(col)
city.build_city(col)
city.build_world(sc)

CAST = [
    dict(name="Maire", shirt=(0.15, 0.2, 0.55), pants=(0.1, 0.1, 0.15), hat="tophat", accessory="sash", hair="grey", skin=bk.SKINS[0]),
    dict(name="Ana", shirt=(0.9, 0.3, 0.45), pants=(0.2, 0.2, 0.45), hair="long", hair_color=(0.3, 0.15, 0.08), accessory="bag", skin=bk.SKINS[1]),
    dict(name="Docteur", shirt=(0.97, 0.97, 0.97), pants=(0.2, 0.5, 0.65), hair="cap", accessory="cross", skin=bk.SKINS[3]),
    dict(name="Sauveteur", shirt=(0.95, 0.15, 0.15), pants=(0.95, 0.75, 0.1), hair="spiky", hair_color=(0.95, 0.75, 0.2), accessory="whistle", skin=bk.SKINS[2]),
    dict(name="Boulanger", shirt=(0.95, 0.9, 0.85), pants=(0.3, 0.3, 0.35), hat="chef", accessory="apron", hair="cap", skin=bk.SKINS[4], face="happy"),
    dict(name="Pecheur", shirt=(0.2, 0.55, 0.3), pants=(0.45, 0.35, 0.2), hat="cap", hat_color=(0.95, 0.8, 0.1), hair="cap", face="angry", skin=bk.SKINS[1]),
]
for i, spec in enumerate(CAST):
    arm, _ = bk.make_character(collection=col, seed=i, **spec)
    arm.location = (-2.5 + i * 1.0, 7.0, 0.06)
    arm.rotation_euler = (0, 0, math.radians(180 - 180))  # face = -Y
    if i == 1:
        bk.reset_pose(arm, 1)
        bk.pose(arm, 1, **{"upper_arm__R": (0, 0, -150), "forearm__R": (0, 0, -15)})
    if i == 3:
        bk.pose(arm, 1, **{"upper_arm__L": (-60, 0, 20), "forearm__L": (-70, 0, 0), "thigh__R": (-35, 0, 0), "shin__R": (50, 0, 0)})

cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
col.objects.link(cam)
sc.camera = cam
cam.data.lens = 35
cam.location = (0, 2.0, 1.1)
cam.rotation_euler = (Vector((0, 7.0, 0.6)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = 24
sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 960, 540
try:
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.exposure = -0.3
except TypeError:
    pass
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=out.replace(".png", ".blend"))
