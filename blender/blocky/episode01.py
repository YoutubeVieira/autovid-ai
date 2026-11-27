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
_P = city.PAL["primaires"]
_H = city.H
VIVID = [_H(_P["rouge"]), _H(_P["bleu_ciel"]), _H(_P["or"]), _H(_P["vert"]), _H(_P["bleu_profond"]),
         _H(_P["rouge"]), _H(_P["bleu_ciel"]), _H(_P["or"])]
HAIRS = [_H(city.PAL["bois_brique"]["brun_fonce"]), _H(city.PAL["neutres"]["quasi_noir"]), _H(city.PAL["bois_brique"]["brun"]),
         _H(city.PAL["bois_brique"]["ocre"]), _H(_P["rouge"])]
rnd = random.Random(11)

STARS = {  # les 6 premiers habitants, avec metier
    "Ana": dict(shirt=_H(_P["rouge"]), pants=_H(_P["bleu_profond"]), hair="long", hair_color=HAIRS[0], accessory="bag", skin=bk.SKINS[1]),
    "Luc": dict(shirt=(0.97, 0.97, 0.97), pants=(0.2, 0.5, 0.65), hair="cap", accessory="cross", skin=bk.SKINS[3], hair_color=HAIRS[1]),
    "Lea": dict(shirt=_H(_P["rouge"]), pants=_H(_P["or"]), hair="spiky", hair_color=HAIRS[3], accessory="whistle", skin=bk.SKINS[2]),
    "Marc": dict(shirt=(0.95, 0.9, 0.85), pants=(0.3, 0.3, 0.35), hat="chef", accessory="apron", hair="cap", skin=bk.SKINS[4], face="happy", hair_color=HAIRS[2]),
    "Yan": dict(shirt=_H(_P["vert"]), pants=_H(city.PAL["bois_brique"]["brun"]), hat="cap", hat_color=_H(_P["or"]), hair="cap", skin=bk.SKINS[1], hair_color=HAIRS[4]),
    "Zoe": dict(shirt=_H(_P["bleu_ciel"]), pants=_H(_P["bleu_profond"]), hair="bun", hair_color=HAIRS[4], skin=bk.SKINS[0], face="happy"),
}
MAIRE = dict(shirt=_H(_P["bleu_profond"]), pants=_H(city.PAL["neutres"]["quasi_noir"]), hat="tophat", accessory="sash", hair="grey", skin=bk.SKINS[0], face="happy")
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

# ------------------------------------------------------------------ plan heros: piece d'or geante "100"
gold = bk.mat("gold", _H(_P["or"]), 0.22)
gold.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 1.0
cb = city._Static("Coin")
cb.cyl((0, 0, 0), 0.95, 0.95, 0.16, "hips", gold, seg=48, rot=bk.Matrix.Rotation(math.pi / 2, 3, 'X'))
cb.cyl((0, -0.085, 0), 0.8, 0.8, 0.02, "hips", bk.mat("goldrim", _H(city.PAL["bois_brique"]["brun"]), 0.3), seg=48, rot=bk.Matrix.Rotation(math.pi / 2, 3, 'X'))
coin = cb.finish(col)
coin.location = (0, 10, 1.7)
cu = bpy.data.curves.new("coin_txt", 'FONT')
cu.body, cu.size, cu.extrude, cu.align_x, cu.align_y = "100", 0.62, 0.03, 'CENTER', 'CENTER'
txt = bpy.data.objects.new("coin_txt", cu)
col.objects.link(txt)
txt.parent = coin
txt.location = (0, -0.12, 0)
txt.rotation_euler = (math.radians(90), 0, 0)
txt.data.materials.append(bk.mat("coin_ink", _H(city.PAL["bois_brique"]["brun_fonce"]), 0.4))
interp('BEZIER')
bk.key_obj(coin, 350, scale=0.0001, loc=(0, 10, 1.7))
bk.key_obj(coin, 356, scale=1.15, loc=(0, 10, 1.7))
bk.key_obj(coin, 360, scale=1.0, loc=(0, 10, 1.7))
bk.key_obj(coin, 366, scale=1.0, loc=(0, 10, 1.7))
bk.key_obj(coin, 367, scale=0.0001, loc=(0, 10, 1.7))
coin.rotation_euler = (0, 0, math.radians(-28))
coin.keyframe_insert("rotation_euler", frame=351)
coin.rotation_euler = (0, 0, math.radians(28))
coin.keyframe_insert("rotation_euler", frame=366)
ev(352, "badge", text="100 HABITANTS", color="yellow")

# ------------------------------------------------------------------ cameras: montage RAPIDE (plans de 1 a 2 s)
interp('BEZIER')
cams = []


def shot(n, f0, f1, loc0, loc1, tgt0, tgt1, lens=30):
    cd = bpy.data.cameras.new(f"Cam{n}")
    cd.lens = lens
    cd.dof.use_dof = True
    cd.dof.aperture_fstop = 3.2
    co = bpy.data.objects.new(f"Cam{n}", cd)
    col.objects.link(co)
    tgt = bpy.data.objects.new(f"Target{n}", None)
    col.objects.link(tgt)
    c = co.constraints.new('TRACK_TO')
    c.target, c.track_axis, c.up_axis = tgt, 'TRACK_NEGATIVE_Z', 'UP_Y'
    cd.dof.focus_object = tgt
    for f, l, t in ((f0, loc0, tgt0), (f1, loc1, tgt1)):
        co.location, tgt.location = l, t
        co.keyframe_insert("location", frame=f)
        tgt.keyframe_insert("location", frame=f)
    m = sc.timeline_markers.new(f"shot{n}", frame=f0)
    m.camera = co
    cams.append((f0, co))


SHOTS = [  # (debut, fin, cam_debut, cam_fin, cible_debut, cible_fin, focale)
    (1, 36, (0, -2.0, 1.0), (0, 6.0, 1.2), (0, 40, 3.0), (0, 40, 3.4), 28),          # rue vide, travelling avant tres rapide
    (37, 60, (0, 14, 14), (0, 19, 6.5), (0, 22, 0), (0, 22, 0.5), 30),               # vue du ciel qui plonge
    (61, 84, (0.6, 1.5, 0.25), (0.6, 14, 0.4), (0, 30, 0.6), (0, 30, 0.6), 24),      # rase-sol sur les lignes de la route
    (85, 108, (3.2, 6.0, 1.0), (1.6, 7.2, 1.0), (3.8, 10, 0.7), (1.2, 10, 0.7), 32),  # Ana entre (travelling lateral)
    (109, 132, (0.9, 7.0, 0.95), (0.7, 7.9, 0.95), (1.8, 10, 0.8), (0.6, 10, 0.85), 55),  # gros plan Ana
    (133, 168, (-0.5, 7.6, 0.35), (0.3, 8.6, 0.55), (0.6, 10, 0.95), (0.6, 10, 1.0), 34),  # contre-plongee, elle salue
    (169, 200, (0, 4.0, 0.9), (0.3, 6.2, 1.0), (0, 11, 0.7), (0, 11, 0.75), 28),     # le rang apparait
    (201, 230, (-3.6, 7.0, 1.0), (-2.2, 8.2, 1.0), (-1.8, 10.8, 0.8), (-1.6, 11, 0.85), 40),  # coup de camera a gauche
    (231, 288, (0, 3.0, 0.8), (0, 5.8, 1.0), (0, 11, 0.7), (0, 11, 0.8), 24),        # poussee sur le groupe
    (289, 320, (0, 0.5, 3.4), (0, 3.0, 2.0), (0, 16, 0.5), (0, 15, 0.6), 26),        # la foule arrive, vue haute
    (321, 350, (2.8, 8.0, 0.3), (0.6, 10.2, 0.4), (0, 13, 0.6), (0, 13, 0.7), 30),   # rase-sol, jambes qui courent
    (351, 366, (0.5, 4.2, 1.8), (0.2, 5.4, 1.8), (0, 10, 1.75), (0, 10, 1.75), 50),    # plan heros: la piece geante 100
    (367, 380, (0, 1.5, 6.0), (0, 6.5, 3.6), (0, 16, 0.5), (0, 15, 0.7), 22),        # grue: les 100 habitants
    (381, 408, (0, 6.0, 1.2), (0, 7.2, 1.3), (0, 12.5, 1.0), (0, 12.5, 1.1), 45),    # la foule en fete
    (409, 440, (-2.4, 31.0, 1.1), (-1.0, 32.6, 1.4), (0, 36.7, 1.4), (0, 36.7, 1.5), 32),  # le maire
    (441, 480, (0.0, 32.6, 1.55), (0.0, 33.9, 1.6), (0, 36.7, 1.6), (0, 36.7, 1.62), 40),   # push final sur son visage
]
for n, (f0, f1, l0, l1, t0, t1, lens) in enumerate(SHOTS, 1):
    shot(n, f0, f1, l0, l1, t0, t1, lens)
for f0, _ in cams[1:]:
    ev(f0, "cut")
sc.frame_start, sc.frame_end = 1, 480
sc.camera = cams[0][1]

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
sc.view_settings.exposure = -0.75

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
