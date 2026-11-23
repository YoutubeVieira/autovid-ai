"""Neon Bay - preview renders of every generated model.

    python3 tools/blender/render_previews.py            # every models/*.glb (except robot)
    python3 tools/blender/render_previews.py car_sedan  # some models
    python3 tools/blender/render_previews.py human_m@AimRifle:12   # a clip at a frame
    python3 tools/blender/render_previews.py human_m@face          # head close-up

Writes models/previews/<name>.png (640x400, 3/4 view, studio light);
"<name>@<Clip>[:frame]" writes previews/<name>_<Clip>.png (default frame 1);
"<name>@face" writes previews/<name>_face.png (front 3/4 close-up of the head).
Weapons (w_*) are framed from their right side (+Z glTF), slightly from above.
Tries Eevee first; headless machines without GPU fall back to Cycles CPU.
"""
import glob
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import nb_common as nb  # noqa: E402

OUT = os.path.join(nb.MODELS, "previews")
SKIP = {"robot"}


def look_at(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def area_light(name, loc, target, power, size):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy = power
    ld.size = size
    o = nb.link(bpy.data.objects.new(name, ld))
    o.location = loc
    look_at(o, target)
    return o


def setup_engine(scene, engine):
    scene.render.engine = engine
    if engine == "CYCLES":
        scene.cycles.device = "CPU"
        scene.cycles.samples = 32
        scene.cycles.use_denoising = True
        scene.cycles.max_bounces = 4
        try:
            scene.cycles.denoiser = "OPENIMAGEDENOISE"
        except Exception:
            scene.cycles.use_denoising = False
    else:
        try:
            scene.eevee.taa_render_samples = 32
        except Exception:
            pass


def render_model(spec):
    name, _, variant = spec.partition("@")
    clip, _, frame = variant.partition(":")
    face = clip == "face"
    if face or not clip:
        clip = "Idle"
    out_name = name + ("_" + variant.split(":")[0] if variant else "")
    path = os.path.join(nb.MODELS, name + ".glb")
    nb.reset_scene()
    bpy.ops.import_scene.gltf(filepath=path)
    scene = bpy.context.scene
    # pose humans on a frame of a clip (Idle by default)
    for o in scene.objects:
        if o.type == "ARMATURE" and o.animation_data:
            act = bpy.data.actions.get(clip)
            if act:
                o.animation_data.action = act
                try:
                    o.animation_data.action_slot = act.slots[0]
                except Exception:
                    pass
            scene.frame_set(int(frame) if frame else 1)
    bpy.context.view_layer.update()

    meshes = [o for o in scene.objects if o.type == "MESH" and o.visible_get() and not o.hide_render]
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in meshes:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        pts += [ev.matrix_world @ v.co for v in me.vertices]
        ev.to_mesh_clear()
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    floor_z = lo.z
    if face:  # frame the head only
        top = hi.z
        hp = [p for p in pts if p.z > top - 0.30 and abs(p.x) < 0.15]
        lo = Vector((min(p.x for p in hp), min(p.y for p in hp), top - 0.30))
        hi = Vector((max(p.x for p in hp), max(p.y for p in hp), top + 0.01))
    center = (lo + hi) / 2
    radius = (hi - lo).length / 2

    # floor + world
    bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, floor_z))
    floor = bpy.context.active_object
    floor.data.materials.append(nb.material("PreviewFloor", (0.3, 0.31, 0.33), roughness=0.8))
    world = bpy.data.worlds.new("World")
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.18, 0.2, 0.24, 1)
    bg.inputs["Strength"].default_value = 0.35
    scene.world = world

    if name.startswith("car_"):
        d = Vector((1.25, -1.0, 0.55))
    elif name.startswith("w_"):
        d = Vector((0.22, -1.0, 0.32))
    elif face:
        d = Vector((0.55, -1.0, 0.12))
    else:
        d = Vector((0.75, -1.35, 0.35))
    d.normalize()
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = 50
    cam = nb.link(bpy.data.objects.new("Cam", cam_data))
    scene.camera = cam
    scene.render.resolution_x = 640
    scene.render.resolution_y = 400
    # fit: move the camera along d until the bounding box fills ~85% of the frame
    from bpy_extras.object_utils import world_to_camera_view
    corners = [Vector((x, y, z)) for x in (lo.x, hi.x) for y in (lo.y, hi.y) for z in (lo.z, hi.z)]
    dist = radius * 6
    for _ in range(60):
        cam.location = center + d * dist
        look_at(cam, center)
        bpy.context.view_layer.update()
        uv = [world_to_camera_view(scene, cam, c) for c in corners]
        if min(min(p.x, p.y) for p in uv) < 0.06 or max(max(p.x, p.y) for p in uv) > 0.94:
            dist *= 1.04
            cam.location = center + d * dist
            look_at(cam, center)
            break
        dist *= 0.96

    s = max(radius, 0.5)
    area_light("Key", center + Vector((2.5, -3.0, 4.0)) * s, center, 500 * s * s, 3 * s)
    area_light("Fill", center + Vector((-3.5, -1.5, 2.0)) * s, center, 150 * s * s, 4 * s)
    area_light("Rim", center + Vector((-1.0, 3.5, 3.0)) * s, center, 400 * s * s, 3 * s)

    scene.render.resolution_x = 640
    scene.render.resolution_y = 400
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "AgX" if "AgX" in [
        i.identifier for i in scene.view_settings.bl_rna.properties["view_transform"].enum_items] else "Filmic"
    os.makedirs(OUT, exist_ok=True)
    scene.render.filepath = os.path.join(OUT, out_name + ".png")

    engine = os.environ.get("NB_RENDER_ENGINE", "")
    order = [engine] if engine else ["BLENDER_EEVEE", "CYCLES"]
    for eng in order:
        try:
            setup_engine(scene, eng)
            bpy.ops.render.render(write_still=True)
            if os.path.exists(scene.render.filepath):
                print("[preview] %s (%s)" % (scene.render.filepath, eng))
                return eng
        except Exception as e:  # Eevee needs a GPU context
            print("[preview] %s failed with %s: %s" % (name, eng, e))
    return None


if __name__ == "__main__":
    names = sys.argv[1:] or sorted(
        os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(nb.MODELS, "*.glb")))
    names = [n for n in names if n.split("@")[0] not in SKIP]
    # Eevee in a headless process usually aborts; probe once in a cheap way and remember.
    if "NB_RENDER_ENGINE" not in os.environ:
        os.environ["NB_RENDER_ENGINE"] = "CYCLES" if not os.environ.get("DISPLAY") else ""
    for n in names:
        render_model(n)
