"""Neon Bay - preview renders of every generated model.

    python3 tools/blender/render_previews.py            # every models/*.glb (except robot)
    python3 tools/blender/render_previews.py car_sedan  # some models
    python3 tools/blender/render_previews.py human_m@AimRifle:12   # a clip at a frame
    python3 tools/blender/render_previews.py human_m@face          # head close-up

Writes models/previews/<name>.png (640x400, 3/4 view, studio light);
"<name>@<Clip>[:frame]" writes previews/<name>_<Clip>[_<frame>].png (default frame 1);
"<name>@face" writes previews/<name>_face.png (3/4 close-up of the head);
debug close-ups: @front, @side (head), @feet, @hands (left hand), @chest (head + torso, from the front), @waist;
"<name>@far" / "@top": whole body from 10 m (3/4 from above / almost top-down, game distance);
"<name>@<Clip>:<frame>/handR" (or /handL, /face, /far, /top): a view of a posed clip, e.g.
"human_m@Aim:0/handR+w_pistol" = close-up of the right hand holding the pistol;
"<human>@<Clip>:<frame>+w_<id>" puts a weapon in the right hand (grip rule of check_glb_three.js);
NB_PREVIEW_VIEW=side|front|back forces the camera direction, NB_PREVIEW_OUT=<dir> redirects the output.
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

OUT = os.environ.get("NB_PREVIEW_OUT") or os.path.join(nb.MODELS, "previews")
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
        scene.cycles.samples = int(os.environ.get("NB_SAMPLES", "32"))
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


def attach_weapon(weapon):
    """Put models/<weapon>.glb in the right hand of the posed human (same rule as
    check_glb_three.js: grip 7.8 cm along the hand + 1.8 cm towards the palm, barrel forward)."""
    arm = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE")
    pb = arm.pose.bones.get("Hand.R")
    mw = arm.matrix_world
    head, tail = mw @ pb.head, mw @ pb.tail
    along = (tail - head).normalized()
    delta = (mw @ pb.matrix).to_3x3() @ (mw @ pb.bone.matrix_local).to_3x3().inverted()
    palm = delta @ Vector((1, 0, 0))
    palm = (palm - along * palm.dot(along)).normalized()
    grip = head + along * 0.078 + palm * 0.018
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(nb.MODELS, weapon + ".glb"))
    for o in set(bpy.context.scene.objects) - before:
        if o.parent is None:
            o.location = grip
            o.rotation_mode = "XYZ"
            o.rotation_euler = (0, 0, -math.pi / 2)      # weapon +X -> character forward (-Y)


def render_model(spec):
    spec, _, weapon = spec.partition("+")
    name, _, variant = spec.partition("@")
    variant, _, cview = variant.partition("/")          # "<Clip>:<frame>/<view>"
    clip, _, frame = variant.partition(":")
    face = clip in ("face", "front", "side", "feet", "hands", "far", "top", "chest", "waist")
    view = clip
    if face or not clip:
        clip = "Idle"
    if cview:
        view, face = cview, True
    out_name = name + ("_" + variant.replace(":", "_") if variant else "") + ("_" + cview if cview else "")
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
    if weapon:
        attach_weapon(weapon)
        out_name += "+" + weapon
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
    lens = 50
    if view in ("far", "top"):     # game-like distance: whole body seen from ~10 m
        face = False
        lens = 50
    if face:  # frame the head only
        top = hi.z
        arm = next((o for o in scene.objects if o.type == "ARMATURE"), None)
        if view in ("handR", "handL") and arm:
            pb = arm.pose.bones["Hand." + view[-1]]
            hp_c = arm.matrix_world @ (pb.head * 0.4 + pb.tail * 0.6)
            hp = [p for p in pts if (p - hp_c).length < 0.11] or [hp_c]
        elif view == "feet":
            hp = [p for p in pts if p.z < 0.25]
        elif view == "hands":
            hp = [p for p in pts if 0.6 < p.z < 0.95 and p.x > 0.15]
        elif view == "waist":
            hp = [p for p in pts if 0.75 < p.z < 1.2 and abs(p.x) < 0.25]
        else:
            hp = [p for p in pts if p.z > top - (0.62 if view == "chest" else 0.30) and abs(p.x) < (0.24 if view == "chest" else 0.15)]
        lo = Vector([min(p[i] for p in hp) for i in range(3)])
        hi = Vector([max(p[i] for p in hp) for i in range(3)])
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

    if os.environ.get("NB_PREVIEW_VIEW") == "side":
        d = Vector((1.0, 0.0, 0.08))
    elif os.environ.get("NB_PREVIEW_VIEW") == "front":
        d = Vector((0.0, -1.0, 0.08))
    elif os.environ.get("NB_PREVIEW_VIEW") == "back":
        d = Vector((0.6, 1.0, 0.25))
    elif name.startswith("car_"):
        d = Vector((1.25, -1.0, 0.55))
    elif name.startswith("w_"):
        d = Vector((0.22, -1.0, 0.32))
    elif view in ("front", "chest"):
        d = Vector((0.0, -1.0, 0.05))
    elif view == "side":
        d = Vector((1.0, 0.0, 0.05))
    elif view == "hands":
        d = Vector((1.0, -0.6, 0.1))
    elif view == "handR":
        d = Vector((-1.0, -0.5, 0.35))
    elif view == "handL":
        d = Vector((1.0, -0.7, -0.25))
    elif view == "top":
        d = Vector((0.25, -0.35, 1.0))
    elif view == "far":
        d = Vector((0.7, -1.0, 0.75))
    elif face:
        d = Vector((0.55, -1.0, 0.12))
    else:
        d = Vector((0.75, -1.35, 0.35))
    d.normalize()
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = lens
    cam = nb.link(bpy.data.objects.new("Cam", cam_data))
    scene.camera = cam
    scene.render.resolution_x = 640
    scene.render.resolution_y = 400
    # fit: move the camera along d until the bounding box fills ~85% of the frame
    from bpy_extras.object_utils import world_to_camera_view
    corners = [Vector((x, y, z)) for x in (lo.x, hi.x) for y in (lo.y, hi.y) for z in (lo.z, hi.z)]
    dist = radius * 6
    if view in ("far", "top"):    # fixed 10 m camera, no framing
        cam.location = center + d * 10.0
        look_at(cam, center)
    for _ in range(0 if view in ("far", "top") else 60):
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
