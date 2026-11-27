"""Neon Bay - contact sheet of the facial expressions (shape keys / glTF morph targets).

    python3 tools/blender/face_sheet.py                    # human_m + human_f -> previews/faces_expressions_sheet.png
    python3 tools/blender/face_sheet.py human_m4 human_f3  # other characters (same output file)
    NB_FACE_VIEW=front python3 tools/blender/face_sheet.py # straight front view (default: slight 3/4)
    NB_FACE_OUT=/tmp/x.png ...                             # another output file

Imports each models/<name>.glb (Idle, frame 1), then renders the head once at rest and once per
expression (influence 1.0), close-up, studio light, Cycles CPU (~3 s per image). One row per
character: Neutral + the 8 EXPRESSIONS of gen_human.py. Look at the sheet with Read.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import nb_common as nb  # noqa: E402
from render_previews import look_at, area_light, setup_engine  # noqa: E402

EXPRESSIONS = ["Blink", "Smile", "Angry", "Fear", "Surprise", "Sad", "MouthOpen", "JawClench"]
HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 300, 340


def render_row(name, tmp):
    nb.reset_scene()
    bpy.ops.import_scene.gltf(filepath=os.path.join(nb.MODELS, name + ".glb"))
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
    keyed = [o for o in scene.objects if o.type == "MESH" and o.data.shape_keys]
    names = {kb.name for o in keyed for kb in o.data.shape_keys.key_blocks}
    missing = [e for e in EXPRESSIONS if e not in names]
    if missing:
        print("[faces] %s: missing shape keys %s" % (name, missing))
    head = arm.matrix_world @ arm.pose.bones["Head"].head
    center = head + Vector((0, -0.03, 0.06))
    view = os.environ.get("NB_FACE_VIEW", "34")
    d = Vector((0.0, -1.0, 0.04)) if view == "front" else Vector((0.42, -1.0, 0.06))
    d.normalize()
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = 85
    cam = nb.link(bpy.data.objects.new("Cam", cam_data))
    scene.camera = cam
    cam.location = center + d * 0.62
    look_at(cam, center)
    world = bpy.data.worlds.new("World")
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.16, 0.18, 0.22, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.4
    scene.world = world
    area_light("Key", center + Vector((1.2, -1.8, 1.4)), center, 90, 1.2)
    area_light("Fill", center + Vector((-1.6, -1.2, 0.4)), center, 35, 1.5)
    area_light("Rim", center + Vector((-0.5, 1.5, 1.2)), center, 60, 1.0)
    scene.render.resolution_x, scene.render.resolution_y = W, H
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "AgX"
    try:
        scene.view_settings.look = "AgX - Punchy"
    except TypeError:
        pass
    setup_engine(scene, os.environ.get("NB_RENDER_ENGINE", "CYCLES"))
    scene.cycles.samples = int(os.environ.get("NB_SAMPLES", "24"))
    out = []
    for ex in ["Neutral"] + EXPRESSIONS:
        for o in keyed:
            for kb in o.data.shape_keys.key_blocks[1:]:
                kb.value = 1.0 if kb.name == ex else 0.0
        bpy.context.view_layer.update()
        scene.render.filepath = os.path.join(tmp, "%s_%s.png" % (name, ex))
        bpy.ops.render.render(write_still=True)
        out.append((ex, scene.render.filepath))
    return out


def main():
    from PIL import Image, ImageDraw, ImageFont
    names = sys.argv[1:] or ["human_m", "human_f"]
    tmp = os.path.join(HERE, "previews", "_faces_tmp")
    os.makedirs(tmp, exist_ok=True)
    rows = [(n, render_row(n, tmp)) for n in names]
    lab, top = 150, 34
    sheet = Image.new("RGB", (lab + W * 9, top + H * len(rows)), (24, 26, 32))
    dr = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
    except OSError:
        font = ImageFont.load_default()
    for j, ex in enumerate(["Neutral"] + EXPRESSIONS):
        dr.text((lab + W * j + 10, 5), ex, fill=(235, 235, 240), font=font)
    for i, (n, imgs) in enumerate(rows):
        dr.text((10, top + H * i + H // 2 - 12), n, fill=(235, 235, 240), font=font)
        for j, (_, p) in enumerate(imgs):
            sheet.paste(Image.open(p).convert("RGB"), (lab + W * j, top + H * i))
            os.remove(p)
    out = os.environ.get("NB_FACE_OUT") or os.path.join(HERE, "previews", "faces_expressions_sheet.png")
    sheet.save(out, optimize=True)
    try:
        os.rmdir(tmp)
    except OSError:
        pass
    print("[faces] wrote", out)


if __name__ == "__main__":
    main()
