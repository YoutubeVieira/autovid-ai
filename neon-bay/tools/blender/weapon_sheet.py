"""Neon Bay - showcase contact sheet of the weapons (profile + 3/4 view of each).

    python3 tools/blender/weapon_sheet.py                 # every models/w_*.glb
    python3 tools/blender/weapon_sheet.py pistol rifle    # some weapons
    NB_SAMPLES=12 python3 tools/blender/weapon_sheet.py   # faster / noisier

Writes tools/blender/previews/w_<id>_side.png, w_<id>_34.png and the sheet
tools/blender/previews/weapons_sheet.png (weapons_sheet_partial.png when ids are given; each weapon on one row: right-side profile, then
3/4 view from the front right and above; label = id, triangles, file size).
Studio look: dark backdrop, soft key + rim + fill area lights, Cycles CPU with denoising.
The camera frames the bounding box, so relative scale is not kept between rows (the label
gives the length).
"""
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import nb_common as nb  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "previews")
W, H = 800, 400


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def light(name, loc, target, power, size, color=(1, 1, 1)):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy, ld.size, ld.color = power, size, color
    o = nb.link(bpy.data.objects.new(name, ld))
    o.location = loc
    look_at(o, target)


def render(name, view):
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
    L = max(size.x, 0.2)
    world = bpy.data.worlds.new("W")
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.11, 0.12, 0.14, 1)
    bg.inputs["Strength"].default_value = 1.0
    scene.world = world
    # backdrop well below so the weapon floats (contact shadows would hide floating parts)
    bpy.ops.mesh.primitive_plane_add(size=40 * L, location=(c.x, c.y, lo.z - 0.35 * L))
    bpy.context.active_object.data.materials.append(nb.material("Backdrop", (0.05, 0.055, 0.065), roughness=0.9))
    light("Key", c + Vector((0.5, -1.2, 1.4)) * L, c, 30 * L * L, 1.2 * L)
    light("Fill", c + Vector((-1.2, -1.0, 0.3)) * L, c, 8 * L * L, 1.5 * L, (0.85, 0.9, 1.0))
    light("Rim", c + Vector((-0.4, 1.4, 0.9)) * L, c, 30 * L * L, 0.8 * L, (0.8, 0.9, 1.0))
    light("Top", c + Vector((0.0, 0.0, 1.6)) * L, c, 12 * L * L, 2.5 * L)
    cam_d = bpy.data.cameras.new("Cam")
    cam = nb.link(bpy.data.objects.new("Cam", cam_d))
    scene.camera = cam
    if view == "side":
        d = Vector((0.0, -1.0, 0.0))
        cam_d.type = "ORTHO"
        cam_d.ortho_scale = max(size.x * 1.12, size.z * 1.12 * W / H)
        cam.location = c + d * 3 * L
        look_at(cam, c)
    else:
        d = Vector((0.55, -1.0, 0.38)).normalized()
        cam_d.lens = 70
        from bpy_extras.object_utils import world_to_camera_view
        corners = [Vector((x, y, z)) for x in (lo.x, hi.x) for y in (lo.y, hi.y) for z in (lo.z, hi.z)]
        scene.render.resolution_x, scene.render.resolution_y = W, H
        dist = L * 6
        for _ in range(80):
            cam.location = c + d * dist
            look_at(cam, c)
            bpy.context.view_layer.update()
            uv = [world_to_camera_view(scene, cam, k) for k in corners]
            if min(min(p.x, p.y) for p in uv) < 0.05 or max(max(p.x, p.y) for p in uv) > 0.95:
                cam.location = c + d * dist * 1.04
                look_at(cam, c)
                break
            dist *= 0.97
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = int(os.environ.get("NB_SAMPLES", "24"))
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 6
    scene.render.resolution_x, scene.render.resolution_y = W, H
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast" if "AgX - Medium High Contrast" in [
        i.identifier for i in scene.view_settings.bl_rna.properties["look"].enum_items] else "None"
    os.makedirs(OUT, exist_ok=True)
    scene.render.filepath = os.path.join(OUT, "%s_%s.png" % (name, view))
    bpy.ops.render.render(write_still=True)
    return scene.render.filepath


def tris_of(name):
    import json
    import struct
    with open(os.path.join(nb.MODELS, name + ".glb"), "rb") as f:
        data = f.read()
    n = struct.unpack("<I", data[12:16])[0]
    js = json.loads(data[20:20 + n])
    t = 0
    for m in js["meshes"]:
        for p in m["primitives"]:
            t += js["accessors"][p["indices"]]["count"] // 3
    return t, len(data)


def sheet(names, rows, fname="weapons_sheet.png"):
    from PIL import Image, ImageDraw
    pad = 4
    img = Image.new("RGB", (2 * W + 3 * pad, len(rows) * (H + pad) + pad), (12, 13, 16))
    dr = ImageDraw.Draw(img)
    for r, name in enumerate(names):
        for k, path in enumerate(rows[r]):
            img.paste(Image.open(path).convert("RGB"), (pad + k * (W + pad), pad + r * (H + pad)))
        t, b = tris_of(name)
        dr.text((pad + 10, pad + r * (H + pad) + 8), "%s   %d tris   %.0f KB" % (name, t, b / 1024),
                fill=(235, 240, 245))
    path = os.path.join(OUT, fname)
    img.save(path, optimize=True)
    return path


if __name__ == "__main__":
    want = sys.argv[1:]
    names = sorted(os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(nb.MODELS, "w_*.glb")))
    if want:
        names = [n for n in names if n[2:] in want or n in want]
    rows = [[render(n, "side"), render(n, "34")] for n in names]
    print("[sheet]", sheet(names, rows, "weapons_sheet_partial.png" if want else "weapons_sheet.png"))
