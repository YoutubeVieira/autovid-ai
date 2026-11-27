"""Episode 1 'Le monde se peuple' - LA FIN DES DINOSAURES (~26 s verticales, 24 i/s).
Dinosaures en blocs, asteroide, explosion, ciel qui s'assombrit puis renaissance. Les plans suivent la voix (voice.json).

Usage: python episode_dino01.py -- --voice <dossier voice.json> --out frames/ [--res 540 960] [--samples 10] [--range a b] [--blend f.blend] [--no-render]"""
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
import dinos as dn  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--voice", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--res", type=int, nargs=2, default=[540, 960])
ap.add_argument("--samples", type=int, default=10)
ap.add_argument("--range", type=int, nargs=2)
ap.add_argument("--blend")
ap.add_argument("--no-render", action="store_true")
args = ap.parse_args(argv)
FPS = 24
cues = json.load(open(os.path.join(args.voice, "voice.json"), encoding="utf-8"))["cues"]
fr = lambda t: int(round(t * FPS)) + 1
T = lambda i: cues[i]["start"]
E = lambda i: cues[i]["end"]
END = E(7) + 0.25
T_IMP = 9.30                                   # impact (apres "Un astéroïde")
prefs = bpy.context.preferences.edit

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = FPS
col = bpy.data.collections.new("Dino01")
sc.collection.children.link(col)
dn.build_world(col)
sky, mix, bg, sun = dn.build_sky(sc)
P = dn.P

# ------------------------------------------------------------------ dinosaures
trex = dn.make_trex(col)
trice = dn.make_trice(col)
brach = dn.make_brachio(col)
prefs.keyframe_new_interpolation_type = 'LINEAR'
dn.walk(brach, fr(0), fr(T_IMP), (-13, 42, 0), (-8, 29, 0), cycle=40, amp=0.28, step=5)
dn.walk(trice, fr(0), fr(T_IMP), (12, 38, 0), (7.5, 27, 0), cycle=30, amp=0.4, step=5)
dn.place(trex, fr(0), (0, 24, 0), 0)
for f in range(fr(0), fr(T_IMP), 6):                      # respiration + petits pas sur place
    ph = (f - 1) / FPS * 2.2
    dn.place(trex, f, (0, 24, 0.05 * math.sin(ph)), 0)
    trex["hip"].rotation_euler = (0.02 * math.sin(ph), 0, 0)
    dn.key(trex["hip"], "rotation_euler", f)
prefs.keyframe_new_interpolation_type = 'BEZIER'
dn.roar(trex, fr(0.7), 24)
dn.roar(trex, fr(3.2), 26)
for d, tt in ((trex, 5.5), (trice, 5.6), (brach, 5.7)):   # ils levent la tete: ils ont vu le ciel
    dn.look_up(d, fr(tt - 0.4), fr(tt + 0.5))
    dn.set_eyes(d, fr(tt - 0.4), "normal")
    dn.set_eyes(d, fr(tt + 0.2), "scared")
for d in (trex, trice, brach):                            # le choc les efface
    dn.place(d, fr(T_IMP) + 1, None, None, 1.0)
    dn.place(d, fr(T_IMP) + 3, None, None, 0.0001)

# ------------------------------------------------------------------ asteroide
IMP = Vector((3, 27, 0.5))
P0 = Vector((46, 150, 78))
mp = dn.pivot(col, "Meteor")
rock = bk.mat("meteor_rock", (0.18, 0.12, 0.10), 0.9)
glow = dn.emissive("meteor_glow", (1.0, 0.45, 0.08), 22.0)
sb = city._Static("m_rock"); sb.sphere((0, 0, 0), 2.0, "hips", rock); mr = sb.finish(col); mr.parent = mp
sg = city._Static("m_glow"); sg.sphere((0, 0, 0), 2.8, "hips", glow); mg = sg.finish(col); mg.parent = mp
dirv = (IMP - P0).normalized()
tb = city._Static("m_tail"); tb.cyl((0, 0, 0), 2.6, 0.2, 26, "hips", glow, seg=16)
mt = tb.finish(col); mt.parent = mp
mt.rotation_euler = (-dirv).to_track_quat('Z', 'Y').to_euler()
mt.location = -dirv * 13
bpy.ops.object.light_add(type='POINT', location=(0, 0, 0))
ml = bpy.context.active_object
ml.parent = mp
ml.data.energy, ml.data.color = 4_000_000, (1.0, 0.5, 0.2)
mp.scale = (0.0001,) * 3
mp.location = P0
mp.keyframe_insert("scale", frame=fr(5.0)); mp.keyframe_insert("location", frame=fr(5.0))
mp.scale = (1, 1, 1)
mp.keyframe_insert("scale", frame=fr(5.05))
mid = P0.lerp(IMP, 0.72)
mp.location = mid
mp.keyframe_insert("location", frame=fr(8.2))
mp.location = IMP
mp.keyframe_insert("location", frame=fr(T_IMP))
mp.scale = (0.0001,) * 3
mp.keyframe_insert("scale", frame=fr(T_IMP) + 1)

# explosion + onde de choc + flash
boom = dn.emissive("boom", (1.0, 0.55, 0.15), 40.0)
bb = city._Static("boom"); bb.sphere((0, 0, 0), 1.0, "hips", boom); ex = bb.finish(col)
ex.location = IMP
ex.scale = (0.0001,) * 3
ex.keyframe_insert("scale", frame=fr(T_IMP) - 1)
ex.scale = (14,) * 3; ex.keyframe_insert("scale", frame=fr(T_IMP) + 6)
ex.scale = (34,) * 3; ex.keyframe_insert("scale", frame=fr(T_IMP + 1.2))
ex.scale = (0.0001,) * 3; ex.keyframe_insert("scale", frame=fr(T_IMP + 1.6))
ring = dn.emissive("ring", (1.0, 0.8, 0.5), 8.0)
rb = city._Static("ring"); rb.cyl((0, 0, 0), 1.0, 1.0, 0.6, "hips", ring, seg=48); rg = rb.finish(col)
rg.location = (IMP.x, IMP.y, 0.4)
rg.scale = (0.0001, 0.0001, 1)
rg.keyframe_insert("scale", frame=fr(T_IMP))
rg.scale = (130, 130, 1); rg.keyframe_insert("scale", frame=fr(T_IMP + 1.5))
rg.scale = (0.0001, 0.0001, 1); rg.keyframe_insert("scale", frame=fr(T_IMP + 1.55))
base_exp = -1.35
sc.view_settings.view_transform = 'Khronos PBR Neutral'
for t, v in ((0, base_exp), (T_IMP - 0.05, base_exp), (T_IMP, 3.0), (T_IMP + 0.15, 0.8), (T_IMP + 0.5, base_exp)):
    sc.view_settings.exposure = v
    sc.view_settings.keyframe_insert("exposure", frame=fr(t))

# ciel / lumiere: jour -> apocalypse -> aube
def anim_world(t, factor, strength, sun_e, sun_col, elev):
    f = fr(t)
    mix.inputs[0].default_value = factor; mix.inputs[0].keyframe_insert("default_value", frame=f)
    bg.inputs["Strength"].default_value = strength; bg.inputs["Strength"].keyframe_insert("default_value", frame=f)
    sun.data.energy = sun_e; sun.data.keyframe_insert("energy", frame=f)
    sun.data.color = sun_col; sun.data.keyframe_insert("color", frame=f)
    sky.sun_elevation = math.radians(elev); sky.keyframe_insert("sun_elevation", frame=f)


DAY, FIRE, DAWN = (1.0, 0.95, 0.85), (1.0, 0.4, 0.15), (1.0, 0.72, 0.45)
anim_world(0, 0.0, 0.22, 2.6, DAY, 42)
anim_world(T_IMP, 0.0, 0.22, 2.6, DAY, 42)
anim_world(T_IMP + 0.9, 1.0, 0.18, 1.0, FIRE, 12)
anim_world(13.3, 1.0, 0.18, 1.0, FIRE, 6)
anim_world(15.6, 0.0, 0.22, 2.4, DAWN, 9)
anim_world(20.0, 0.0, 0.22, 2.8, (1.0, 0.92, 0.8), 32)

# cendres
ash_m = bk.mat("ash", (0.12, 0.11, 0.11), 0.9)
rnd = random.Random(9)
prefs.keyframe_new_interpolation_type = 'LINEAR'
for i in range(80):
    ab = city._Static(f"ash{i}"); ab.box((0, 0, 0), (0.28, 0.28, 0.28), "hips", ash_m); a = ab.finish(col)
    x, y = rnd.uniform(-16, 16), rnd.uniform(6, 44)
    t0 = T_IMP + 0.4 + rnd.uniform(0, 3.4)
    a.scale = (0.0001,) * 3; a.location = (x, y, 20); a.keyframe_insert("scale", frame=fr(t0) - 1); a.keyframe_insert("location", frame=fr(t0) - 1)
    a.scale = (1, 1, 1); a.keyframe_insert("scale", frame=fr(t0))
    a.rotation_euler = (0, 0, 0); a.keyframe_insert("rotation_euler", frame=fr(t0))
    a.location = (x + rnd.uniform(-2, 2), y, 0.15); a.keyframe_insert("location", frame=fr(t0 + rnd.uniform(1.8, 2.8)))
    a.rotation_euler = (rnd.uniform(2, 6), rnd.uniform(2, 6), 0); a.keyframe_insert("rotation_euler", frame=fr(t0 + 2.2))
    a.scale = (1, 1, 1); a.keyframe_insert("scale", frame=fr(13.3))
    a.scale = (0.0001,) * 3; a.keyframe_insert("scale", frame=fr(15.0))
prefs.keyframe_new_interpolation_type = 'BEZIER'

# crane de T-Rex + cotes (apparaissent apres le choc)
bone = bk.mat("bone", (0.93, 0.9, 0.8), 0.6)
sk = dn.pivot(col, "Fossile", None, (-2.2, 14, 0))
dn.block(col, "crane", sk, (0, 0, 0.55), (1.0, 1.6, 0.8), bone)
dn.block(col, "machoire", sk, (0, -0.15, 0.2), (0.8, 1.2, 0.2), bone)
for k in range(4):
    dn.block(col, "dent", sk, (-0.3 + k * 0.2, -0.85, 0.34), (0.07, 0.07, 0.16), bone, bevel=0.01)
for k in range(5):
    dn.block(col, "cote", sk, (1.0 + k * 0.35, 1.2 + k * 0.1, 0.5), (0.12, 0.12, 1.1), bone, rot=bk.Matrix.Rotation(0.35, 3, 'Y'), bevel=0.02)
sk.scale = (0.0001,) * 3
sk.keyframe_insert("scale", frame=fr(11.0))
sk.scale = (1.15,) * 3
sk.keyframe_insert("scale", frame=fr(11.3))

# jeunes pousses (renaissance) + panneau "0 habitant"
sap = []
for k in range(14):
    x, y = rnd.uniform(-7, 7), rnd.uniform(12, 24)
    r = dn.tree_fern(col, (x, y, 0), 0.0001, 100 + k)
    t0 = 16.1 + k * 0.14
    r.scale = (0.0001,) * 3; r.keyframe_insert("scale", frame=fr(t0))
    r.scale = (0.9,) * 3; r.keyframe_insert("scale", frame=fr(t0 + 0.5))
    r.scale = (0.7,) * 3; r.keyframe_insert("scale", frame=fr(t0 + 0.7))
wood = bk.mat("wood", city.H(dn.BB["brun"]), 0.7)
sign = dn.pivot(col, "Panneau", None, (0, 10, 0))
dn.block(col, "poteau", sign, (0, 0, 1.1), (0.25, 0.25, 2.2), wood)
dn.block(col, "planche", sign, (0, -0.05, 2.0), (3.2, 0.2, 1.3), bk.mat("board", city.H(city.PAL["pierre_sable"]["creme"]), 0.7))
cu = bpy.data.curves.new("txt", 'FONT')
cu.body, cu.size, cu.extrude, cu.align_x, cu.align_y = "0 HABITANT", 0.36, 0.02, 'CENTER', 'CENTER'
tx = bpy.data.objects.new("txt", cu); col.objects.link(tx); tx.parent = sign
tx.location = (0, -0.17, 2.0); tx.rotation_euler = (math.radians(90), 0, 0)
cu.materials.append(bk.mat("ink", city.H(dn.BB["brun_fonce"]), 0.5))
sign.scale = (0.0001,) * 3; sign.keyframe_insert("scale", frame=fr(18.3))
sign.scale = (1.2,) * 3; sign.keyframe_insert("scale", frame=fr(18.55))
sign.scale = (1.0,) * 3; sign.keyframe_insert("scale", frame=fr(18.75))

# ------------------------------------------------------------------ cameras (montage rapide)
cams = []


def shot(n, t0, t1, l0, l1, g0, g1, lens=28):
    cd = bpy.data.cameras.new(f"Cam{n}")
    cd.lens = lens
    cd.dof.use_dof = True
    cd.dof.aperture_fstop = 3.5
    co = bpy.data.objects.new(f"Cam{n}", cd)
    col.objects.link(co)
    tg = bpy.data.objects.new(f"Tgt{n}", None)
    col.objects.link(tg)
    c = co.constraints.new('TRACK_TO')
    c.target, c.track_axis, c.up_axis = tg, 'TRACK_NEGATIVE_Z', 'UP_Y'
    cd.dof.focus_object = tg
    for f, l, g in ((fr(t0), l0, g0), (fr(t1) - 1, l1, g1)):
        co.location, tg.location = l, g
        co.keyframe_insert("location", frame=f)
        tg.keyframe_insert("location", frame=f)
    m = sc.timeline_markers.new(f"shot{n}", frame=fr(t0))
    m.camera = co
    cams.append((t0, co))


B = [0, 1.7, 3.0, 4.9, 5.9, 7.0, 7.94, 9.2, 10.0, 11.33, 13.51, 16.03, 18.5, 21.83, END]
SH = [
    ((0, -4, 2.0), (0, 6, 2.4), (0, 26, 3.5), (0, 26, 3.8), 28),
    ((-4, 12, 0.5), (-5, 16, 0.7), (-9, 33, 3), (-8, 30, 3.4), 30),
    ((2.5, 8, 3.4), (1.5, 12, 3.6), (0, 23, 3.9), (0, 23, 4.0), 45),
    ((0, 10, 1.5), (0, 12, 2.0), (0, 100, 45), (10, 100, 50), 24),
    ((-2, 9, 3.8), (-1, 13, 4.0), (0, 23, 3.9), (0, 23, 3.9), 50),
    ((0, 6, 1.2), (0, 8, 1.5), (8, 70, 35), (4, 45, 18), 24),
    ((-12, 2, 3), (-10, 6, 3.5), (3, 30, 6), (3, 27, 2), 26),
    ((0, -6, 3.0), (0, -4, 3.4), (2, 27, 5), (2, 27, 5), 24),
    ((0, 2, 2), (0, 4, 2.5), (0, 40, 8), (0, 40, 9), 28),
    ((-3, 6, 1.3), (-2.6, 8, 1.2), (-2, 14, 0.8), (-2, 14, 0.9), 35),
    ((0, -2, 1.0), (0, 3, 4.5), (0, 40, 3), (0, 40, 6), 26),
    ((6, 6, 1.4), (3, 8, 1.8), (0, 18, 1.0), (0, 18, 1.2), 32),
    ((3, 6.5, 1.8), (-3, 7, 1.8), (0, 10, 1.4), (0, 10, 1.5), 40),
    ((0, -3, 2.4), (0, 3, 3.5), (0, 30, 4), (0, 30, 5), 24),
]
for n, (l0, l1, g0, g1, lens) in enumerate(SH, 1):
    shot(n, B[n - 1], B[n], l0, l1, g0, g1, lens)
sc.camera = cams[0][1]
sc.frame_start, sc.frame_end = 1, fr(END)

# ------------------------------------------------------------------ evenements pour le monteur autonome
ev = [{"t": 0.0, "type": "hud_sub", "text": "ÉPISODE 1 · LA FIN DES DINOSAURES"},
      {"t": 13.51, "type": "hud_sub", "text": "PLANÈTE : VIDE"},
      {"t": 18.5, "type": "hud_sub", "text": "0 HABITANT · À PEUPLER"},
      {"t": 18.6, "type": "badge", "text": "0 HABITANT", "color": "red"},
      {"t": 0.7, "type": "sfx", "name": "roar"}, {"t": 1.9, "type": "sfx", "name": "stomp"},
      {"t": 3.2, "type": "sfx", "name": "roar", "gain": 1.0}, {"t": 5.5, "type": "sfx", "name": "gasp"},
      {"t": 6.75, "type": "sfx", "name": "meteor_whistle"}, {"t": 8.9, "type": "sfx", "name": "rumble"},
      {"t": T_IMP, "type": "sfx", "name": "explosion", "gain": 1.0}, {"t": T_IMP, "type": "impact"},
      {"t": 10.3, "type": "sfx", "name": "wind_ash", "gain": 0.8},
      {"t": 4.9, "type": "sfx", "name": "music_suspense", "file": "music_suspense.mp3", "gain": 0.35, "dur": 4.4},
      {"t": 13.6, "type": "sfx", "name": "music_calme", "file": "music_calme.mp3", "gain": 0.4, "dur": END - 13.6},
      {"t": 16.3, "type": "sfx", "name": "sparkle"}, {"t": 18.5, "type": "sfx", "name": "coin"},
      {"t": 21.9, "type": "sfx", "name": "ding"}]
ev += [{"t": round(B[i], 2), "type": "cut"} for i in range(1, len(B) - 1)]
ev.sort(key=lambda e: e["t"])
os.makedirs(args.out, exist_ok=True)
json.dump({"fps": FPS, "content_duration": round(END, 2), "events": ev}, open(os.path.join(args.out, "events.json"), "w"), indent=2, ensure_ascii=False)

# ------------------------------------------------------------------ rendu
sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = args.samples
sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = args.res
sc.render.image_settings.file_format = 'PNG'
sc.view_settings.exposure = base_exp
if args.blend:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.blend))
if not args.no_render:
    if args.range:
        sc.frame_start, sc.frame_end = args.range
    sc.render.filepath = os.path.join(os.path.abspath(args.out), "f_")
    bpy.ops.render.render(animation=True)
