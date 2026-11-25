"""Neon Bay - portrait sheet of human faces (neutral, front + 3/4 close-ups).

    python3 tools/blender/face_portraits.py                       # the 9 humans -> previews/faces_v5_all.png
    python3 tools/blender/face_portraits.py human_m human_f       # some humans
    python3 tools/blender/face_portraits.py "v4 m=/tmp/old/human_m.glb" human_m   # label=path pairs
    NB_FACE_OUT=previews/faces_v5_before_after.png NB_FACE_COLS=2 ...   # output file, columns per row

Each entry gives two images (front, 3/4) side by side; entries are laid out NB_FACE_COLS per row
(default 3). Imports the .glb (Idle, frame 1), studio light, Cycles CPU. Look at the sheet with Read.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import nb_common as nb  # noqa: E402
from render_previews import look_at, area_light, setup_engine  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ALL = ["human_m", "human_f", "human_m2", "human_f2", "human_f3", "human_m3", "human_f4", "human_m4", "human_m5"]
W, H = int(os.environ.get("NB_FACE_W", "360")), int(os.environ.get("NB_FACE_H", "420"))


def render(path, tmp, tag):
    nb.reset_scene()
    bpy.ops.import_scene.gltf(filepath=path)
    scene = bpy.context.scene
    arm = next(o for o in scene.objects if o.type == "ARMATURE")
    act = bpy.data.actions.get("Idle")
    if act and arm.animation_data:
        arm.animation_data.action = act
        try:
            arm.animation_data.action_slot = act.slots[0]
        except Exception:
            pass
    scene.frame_set(1)
    for o in scene.objects:
        if o.type == "MESH" and o.data.shape_keys:
            for kb in o.data.shape_keys.key_blocks[1:]:
                kb.value = 0.0
    head = arm.matrix_world @ arm.pose.bones["Head"].head
    center = head + Vector((0, -0.02, float(os.environ.get("NB_FACE_DZ", "0.075"))))
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = 85
    cam = nb.link(bpy.data.objects.new("Cam", cam_data))
    scene.camera = cam
    world = bpy.data.worlds.new("World")
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.16, 0.18, 0.22, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.45
    scene.world = world
    area_light("Key", center + Vector((1.2, -1.8, 1.4)), center, 90, 1.2)
    area_light("Fill", center + Vector((-1.6, -1.2, 0.4)), center, 35, 1.5)
    area_light("Rim", center + Vector((-0.5, 1.5, 1.2)), center, 60, 1.0)
    scene.render.resolution_x, scene.render.resolution_y = W, H
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "AgX"
    setup_engine(scene, os.environ.get("NB_RENDER_ENGINE", "CYCLES"))
    scene.cycles.samples = int(os.environ.get("NB_SAMPLES", "24"))
    out = []
    for view, d in (("front", Vector((0.0, -1.0, 0.03))), ("34", Vector((0.62, -1.0, 0.06)))):
        d.normalize()
        cam.location = center + d * float(os.environ.get("NB_FACE_DIST", "0.74"))
        look_at(cam, center)
        scene.render.filepath = os.path.join(tmp, "%s_%s.png" % (tag, view))
        bpy.ops.render.render(write_still=True)
        out.append(scene.render.filepath)
    return out


def main():
    from PIL import Image, ImageDraw, ImageFont
    args = sys.argv[1:] or ALL
    entries = []
    for a in args:
        if "=" in a:
            lab, p = a.split("=", 1)
        else:
            lab, p = a, os.path.join(nb.MODELS, a + ".glb")
        entries.append((lab, p))
    cols = int(os.environ.get("NB_FACE_COLS", "3"))
    tmp = os.path.join(HERE, "previews", "_portraits_tmp")
    os.makedirs(tmp, exist_ok=True)
    imgs = [(lab, render(p, tmp, "e%d" % i)) for i, (lab, p) in enumerate(entries)]
    top = 34
    rows = (len(imgs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 2 * W + (cols - 1) * 12, rows * (H + top)), (24, 26, 32))
    dr = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
    except OSError:
        font = ImageFont.load_default()
    for i, (lab, (f, t)) in enumerate(imgs):
        x0, y0 = (i % cols) * (2 * W + 12), (i // cols) * (H + top)
        dr.text((x0 + 10, y0 + 5), lab, fill=(235, 235, 240), font=font)
        sheet.paste(Image.open(f).convert("RGB"), (x0, y0 + top))
        sheet.paste(Image.open(t).convert("RGB"), (x0 + W, y0 + top))
        os.remove(f)
        os.remove(t)
    out = os.environ.get("NB_FACE_OUT") or os.path.join(HERE, "previews", "faces_v5_all.png")
    if not os.path.isabs(out):
        out = os.path.join(HERE, out)
    sheet.save(out, optimize=True)
    try:
        os.rmdir(tmp)
    except OSError:
        pass
    print("[portraits] wrote", out)


if __name__ == "__main__":
    main()
