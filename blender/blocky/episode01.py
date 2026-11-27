"""Episode pilote 'La ville des abonnes' - personnages articules en blocs colores, 20 s verticales (24 i/s).

Usage:
  python episode01.py -- --out frames_dir [--range 1 480] [--res 540 960] [--samples 16] [--blend episode01.blend]
Ecrit aussi events.json (badges / compteur pour le monteur autonome).
"""
import argparse
import json
import math
import os
import random
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blocky as bk  # noqa: E402
import city  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("--range", type=int, nargs=2)
ap.add_argument("--res", type=int, nargs=2, default=[540, 960])
ap.add_argument("--samples", type=int, default=16)
ap.add_argument("--blend")
ap.add_argument("--no-render", action="store_true")
args = ap.parse_args(argv)
FPS = 24

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = FPS
col = bpy.data.collections.new("Episode01")
sc.collection.children.link(col)
city.build_city(col)
city.build_world(sc)
prefs = bpy.context.preferences.edit


def interp(kind):
    prefs.keyframe_new_interpolation_type = kind


# ------------------------------------------------------------------ distribution
VIVID = [(0.92, 0.22, 0.22), (0.98, 0.70, 0.12), (0.18, 0.55, 0.92), (0.22, 0.75, 0.38), (0.90, 0.35, 0.70),
         (0.97, 0.50, 0.12), (0.55, 0.38, 0.88), (0.12, 0.72, 0.78)]
HAIRS = [(0.2, 0.12, 0.06), (0.05, 0.05, 0.06), (0.65, 0.4, 0.15), (0.9, 0.7, 0.25), (0.55, 0.12, 0.1)]
rnd = random.Random(11)

STARS = {  # les 6 premiers habitants, avec metier
    "Ana": dict(shirt=(0.9, 0.3, 0.45), pants=(0.2, 0.2, 0.5), hair="long", hair_color=HAIRS[0], accessory="bag", skin=bk.SKINS[1]),
    "Luc": dict(shirt=(0.97, 0.97, 0.97), pants=(0.2, 0.5, 0.65), hair="cap", accessory="cross", skin=bk.SKINS[3], hair_color=HAIRS[1]),
    "Lea": dict(shirt=(0.95, 0.15, 0.15), pants=(0.98, 0.78, 0.1), hair="spiky", hair_color=HAIRS[3], accessory="whistle", skin=bk.SKINS[2]),
    "Marc": dict(shirt=(0.95, 0.9, 0.85), pants=(0.3, 0.3, 0.35), hat="chef", accessory="apron", hair="cap", skin=bk.SKINS[4], face="happy", hair_color=HAIRS[2]),
    "Yan": dict(shirt=(0.2, 0.55, 0.3), pants=(0.45, 0.35, 0.2), hat="cap", hat_color=(0.98, 0.8, 0.1), hair="cap", skin=bk.SKINS[1], hair_color=HAIRS[4]),
    "Zoe": dict(shirt=(0.55, 0.38, 0.88), pants=(0.15, 0.15, 0.3), hair="bun", hair_color=HAIRS[4], skin=bk.SKINS[0], face="happy"),
}
MAIRE = dict(shirt=(0.12, 0.2, 0.6), pants=(0.1, 0.1, 0.14), hat="tophat", accessory="sash", hair="grey", skin=bk.SKINS[0], face="happy")
Z0 = 0.05
chars = {}
for i, (n, spec) in enumerate(STARS.items()):
    chars[n] = bk.make_character(n, col, seed=i, **spec)[0]
chars["Maire"] = bk.make_character("Maire", col, seed=99, **MAIRE)[0]
crowd = []
for i in range(16):
    spec = dict(shirt=rnd.choice(VIVID), pants=rnd.choice([(0.15, 0.2, 0.5), (0.2, 0.2, 0.22), (0.45, 0.32, 0.2), (0.3, 0.45, 0.6)]),
                hair=rnd.choice(["cap", "spiky", "bun", "long", "cap"]), hair_color=rnd.choice(HAIRS),
                skin=rnd.choice(bk.SKINS), face=rnd.choice(["smile", "happy"]))
    if rnd.random() < 0.3:
        spec.update(hat=rnd.choice(["cap", "beret"]), hat_color=rnd.choice(VIVID))
    crowd.append(bk.make_character(f"Citoyen{i:02d}", col, seed=100 + i, **spec)[0])

for a in list(chars.values()) + crowd:  # tout le monde cache jusqu'a son entree
    bk.reset_pose(a, 1)
    a.scale = (0.0001,) * 3
    a.keyframe_insert("scale", frame=1)
    a.location = (0, -30, Z0)
    a.keyframe_insert("location", frame=1)

events = []


def ev(frame, kind, **kw):
    events.append({"t": round((frame - 1) / FPS, 3), "type": kind, **kw})


# ------------------------------------------------------------------ chorégraphie
interp('LINEAR')
SH = [1, 85, 169, 289, 409, 481]  # debuts de plans (images)

# Plan 2: Ana entre par la droite, salue
ana = chars["Ana"]
bk.key_obj(ana, 84, scale=0.0001)
bk.key_obj(ana, 85, loc=(4.5, 10.0, Z0), scale=1.0)
bk.walk(ana, 85, 125, (4.5, 10.0, Z0), (0.6, 10.0, Z0))
bk.key_obj(ana, 126, loc=(0.6, 10.0, Z0), rot_z=-20)
bk.wave(ana, 126, 168, side="R")
ev(110, "counter", value=1, label="1")
ev(110, "badge", text="+1 HABITANT", color="yellow")
ev(135, "badge", text="+1 EMPLOI", color="green")

# Plan 3: les cinq autres apparaissent en rang (pop-in)
slots = {"Luc": (-1.8, 10.0), "Lea": (1.9, 10.0), "Marc": (-0.9, 12.0), "Yan": (1.1, 12.5), "Zoe": (-2.4, 12.2)}
for k, (name, (x, y)) in enumerate(slots.items()):
    a = chars[name]
    f = 172 + k * 18
    bk.key_obj(a, f - 1, scale=0.0001, loc=(x, y, Z0), rot_z=0)
    interp('BEZIER')
    bk.pop_in(a, f, dur=8)
    interp('LINEAR')
    bk.key_obj(a, f + 8, loc=(x, y, Z0), rot_z=0, scale=1.0)
    bk.wave(a, f + 8, 288, side="R" if k % 2 else "L")
    ev(f, "counter", value=2 + k, label=str(2 + k))
    ev(f, "badge", text="+1 HABITANT", color="yellow")
# Ana reste visible dans le plan 3 (reste en place)
bk.key_obj(ana, 288, loc=(0.6, 10.0, Z0), rot_z=-20)

# Plan 4: la foule arrive en marchant, puis fete
for i, a in enumerate(crowd):
    f0 = 289 + (i % 8) * 3
    x = -2.6 + (i % 6) * 1.0 + rnd.uniform(-0.2, 0.2)
    y0 = 24 + (i // 6) * 3.0 + rnd.uniform(0, 1.5)
    y1 = 11 + (i // 6) * 2.4
    bk.key_obj(a, f0 - 1, scale=0.0001, loc=(x, y0, Z0))
    bk.key_obj(a, f0, scale=1.0, loc=(x, y0, Z0), rot_z=0)
    end = f0 + 60 + (i % 5) * 4
    bk.walk(a, f0, end, (x, y0, Z0), (x, y1, Z0))
    bk.cheer(a, end + 1, 408, base_z=Z0)
ev(289, "counter", value=7, label="7")
ev(330, "counter", value=40, label="40")
ev(375, "counter", value=100, label="100")
ev(375, "badge", text="100 / 100", color="yellow")
ev(375, "milestone")

# Plan 5: le maire sur le perron de la mairie
mairie_y = 34 + 6
maire = chars["Maire"]
bk.key_obj(maire, 408, scale=0.0001, loc=(0, 36.7, 0.42), rot_z=0)
bk.key_obj(maire, 409, scale=1.5, loc=(0, 36.7, 0.42), rot_z=0)
bk.wave(maire, 409, 480, side="R")
ev(410, "badge", text="ELECTION DU MAIRE", color="yellow")

# ------------------------------------------------------------------ cameras (un par plan, lies par marqueurs)
interp('BEZIER')
cams = []


def shot(i, loc0, loc1, tgt0, tgt1, lens=30):
    f0, f1 = SH[i], SH[i + 1] - 1
    cd = bpy.data.cameras.new(f"Cam{i + 1}")
    cd.lens = lens
    co = bpy.data.objects.new(f"Cam{i + 1}", cd)
    col.objects.link(co)
    tgt = bpy.data.objects.new(f"Target{i + 1}", None)
    col.objects.link(tgt)
    c = co.constraints.new('TRACK_TO')
    c.target, c.track_axis, c.up_axis = tgt, 'TRACK_NEGATIVE_Z', 'UP_Y'
    for f, l, t in ((f0, loc0, tgt0), (f1, loc1, tgt1)):
        co.location, tgt.location = l, t
        co.keyframe_insert("location", frame=f)
        tgt.keyframe_insert("location", frame=f)
    m = sc.timeline_markers.new(f"shot{i + 1}", frame=f0)
    m.camera = co
    cams.append(co)


shot(0, (0, -1.0, 0.9), (0, 7.0, 1.1), (0, 40, 3.0), (0, 40, 3.2))            # rue vide
shot(1, (2.6, 4.5, 0.95), (1.6, 5.6, 1.0), (0.6, 10, 0.7), (0.6, 10, 0.75), 34)  # Ana
shot(2, (0.0, 3.5, 0.85), (0.4, 4.6, 0.95), (0.0, 11, 0.6), (0.3, 11, 0.65), 28)  # le rang
shot(3, (0, 0.5, 3.4), (0, 3.5, 1.4), (0, 14, 0.5), (0, 13, 0.7), 26)             # la foule, grue
shot(4, (-1.3, 32.6, 1.0), (-0.5, 33.8, 1.15), (0, 36.7, 1.05), (0, 36.7, 1.15), 34)  # le maire
for f in SH[1:5]:
    ev(f, "cut")
sc.frame_start, sc.frame_end = 1, 480
sc.camera = cams[0]

# ------------------------------------------------------------------ rendu
sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = args.samples
sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = args.res
sc.render.image_settings.file_format = 'PNG'
try:
    sc.view_settings.view_transform = 'Khronos PBR Neutral'
except TypeError:
    pass
sc.view_settings.exposure = -0.6

os.makedirs(args.out, exist_ok=True)
with open(os.path.join(args.out, "events.json"), "w", encoding="utf-8") as fh:
    json.dump({"fps": FPS, "frames": 480, "events": events}, fh, indent=2, ensure_ascii=False)
if args.blend:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.blend))
if not args.no_render:
    if args.range:
        sc.frame_start, sc.frame_end = args.range
    sc.render.filepath = os.path.join(os.path.abspath(args.out), "f_")
    bpy.ops.render.render(animation=True)
