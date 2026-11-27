"""Episode generique 'Le monde se peuple': peuple la ville avec les habitants d'un episode (monde/episodes/epNN/episode.json).
Les anciens habitants sont deja la; les nouveaux arrivent; les habitants mis en avant ont un plan, leur prenom et leur metier au-dessus de la tete
et une expression de visage. Les temps suivent la voix (voice.json).

Usage: python episode_monde.py -- --spec episode.json --voice <dossier voice.json> --out frames/ [--res 540 960] [--samples 10] [--range a b] [--blend f.blend] [--no-render]"""
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
ap.add_argument("--spec", required=True)
ap.add_argument("--voice", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--res", type=int, nargs=2, default=[540, 960])
ap.add_argument("--samples", type=int, default=10)
ap.add_argument("--range", type=int, nargs=2)
ap.add_argument("--blend")
ap.add_argument("--no-render", action="store_true")
args = ap.parse_args(argv)
FPS = 24
spec = json.load(open(args.spec, encoding="utf-8"))
cues = json.load(open(os.path.join(args.voice, "voice.json"), encoding="utf-8"))["cues"]
fr = lambda t: int(round(t * FPS)) + 1
END = cues[-1]["end"] + 0.25
prefs = bpy.context.preferences.edit

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = FPS
col = bpy.data.collections.new("Monde")
sc.collection.children.link(col)
city.build_city(col)
city.build_world(sc)

PAL = city.PAL
COLORS = {"bleu_ciel": PAL["primaires"]["bleu_ciel"], "bleu_profond": PAL["primaires"]["bleu_profond"], "rouge": PAL["primaires"]["rouge"],
          "or": PAL["primaires"]["or"], "vert": PAL["primaires"]["vert"], "brun": PAL["bois_brique"]["brun"], "brun_fonce": PAL["bois_brique"]["brun_fonce"],
          "creme": PAL["pierre_sable"]["creme"], "quasi_noir": PAL["neutres"]["quasi_noir"], "blanc": "#F4F4F2", "gris": "#7A7A80"}
HAIR = [city.H(PAL["bois_brique"]["brun_fonce"]), city.H(PAL["neutres"]["quasi_noir"]), city.H(PAL["bois_brique"]["brun"]), city.H(PAL["bois_brique"]["ocre"]), city.H(PAL["primaires"]["rouge"])]
Z0 = 0.05


def spawn(h):
    lk = h["look"]
    c = lambda k: city.H(COLORS[k]) if k else None
    arm, _ = bk.make_character(f"{h['prenom']}_{h['id']}", col, shirt=c(lk["shirt"]), pants=c(lk["pants"]), hair=lk["hair"],
                               hair_color=HAIR[lk["hair_color"]], skin=bk.SKINS[lk["skin"]], hat=lk.get("hat"), hat_color=c(lk.get("hat_color")) or (0.1, 0.1, 0.1),
                               accessory=lk.get("accessory"), face="smile", faces=["smile", lk["face"], "happy", "surprise"], seed=h["id"])
    arm.scale = (0.0001,) * 3
    bk.reset_pose(arm, 1)
    return arm


def name_tag(arm, h):
    cu = bpy.data.curves.new("tag", 'FONT')
    cu.body, cu.size, cu.extrude, cu.align_x, cu.align_y = f"{h['prenom'].upper()}\n{h['metier_dit'].upper()[:16]}", 0.13, 0.01, 'CENTER', 'CENTER'
    tg = bpy.data.objects.new("tag", cu)
    col.objects.link(tg)
    tg.parent = arm
    tg.location = (0, -0.1, 1.38)
    tg.rotation_euler = (math.radians(90), 0, 0)
    cu.materials.append(bk.mat("tag_ink", city.H(PAL["primaires"]["or"]), 0.4))
    tg.scale = (0.0001,) * 3
    return tg


old = spec["anciens"]
new = spec["nouveaux"]
feat_ids = spec["mis_en_avant"]
rnd = random.Random(spec["episode"])
chars = {}
prefs.keyframe_new_interpolation_type = 'LINEAR'
# --- anciens habitants: deja la, repartis dans la rue
for i, h in enumerate(old):
    a = spawn(h)
    chars[h["id"]] = a
    x, y = (-3.0 + (i % 5) * 1.5) + rnd.uniform(-0.3, 0.3), 12.0 + (i // 5) * 2.2 + rnd.uniform(-0.3, 0.3)
    bk.key_obj(a, 1, loc=(x, y, Z0), rot_z=rnd.uniform(-25, 25), scale=1.0)
    bk.idle(a, 1, fr(END), 12)

# --- nouveaux: arrivent selon les phrases (1 phrase par habitant mis en avant, apres le titre et l'annonce)
events = [{"t": 0.0, "type": "hud_sub", "text": f"ÉPISODE {spec['episode']} · {spec['titre'].upper()}"}, {"t": 0.0, "type": "counter", "value": spec["total_avant"]}]
feat = [h for h in new if h["id"] in feat_ids]
others = [h for h in new if h["id"] not in feat_ids]
total = spec["total_avant"]
shots = []                                              # (t0, t1, cam0, cam1, tgt0, tgt1, lens)
shots.append((0, cues[1]["start"], (0, -3, 2.0), (0, 4, 2.2), (0, 14, 1.5), (0, 14, 1.6), 28))
for k, h in enumerate(feat):
    cue = cues[2 + k]
    t0, t1 = cue["start"], cue["end"]
    a = spawn(h)
    chars[h["id"]] = a
    tg = name_tag(a, h)
    side = -1 if k % 2 else 1
    spot = (side * 1.1, 9.0, Z0)
    bk.key_obj(a, fr(t0 - 0.9) - 1, scale=0.0001, loc=(side * 4.5, 9.0, Z0), rot_z=0)
    bk.key_obj(a, fr(t0 - 0.9), scale=1.0, loc=(side * 4.5, 9.0, Z0))
    bk.walk(a, fr(t0 - 0.9), fr(t0 + 0.3), (side * 4.5, 9.0, Z0), spot)
    bk.key_obj(a, fr(t0 + 0.3), loc=spot, rot_z=-side * 18)
    bk.wave(a, fr(t0 + 0.3), fr(t1) + 12, side="R" if side > 0 else "L")
    bk.set_face(a, 1, "smile")
    bk.set_face(a, fr(t0 + 0.2), h["look"]["face"])
    tg.scale = (0.0001,) * 3; tg.keyframe_insert("scale", frame=fr(t0))
    tg.scale = (1.0,) * 3; tg.keyframe_insert("scale", frame=fr(t0 + 0.25))
    total += 1
    events += [{"t": round(t0, 2), "type": "counter", "value": total}, {"t": round(t0, 2), "type": "badge", "text": f"{h['prenom'].upper()} · {h['metier_dit'].upper()}"[:26], "color": "yellow"},
               {"t": round(t0, 2), "type": "sfx", "name": "pop"}]
    shots.append((t0, t1 + 0.1, (spot[0] - side * 0.4, 6.2, 1.1), (spot[0] - side * 0.2, 7.2, 1.2), (spot[0], 9.0, 0.95), (spot[0], 9.0, 1.0), 50))
# foule des autres arrivants pendant "Et N autres encore"
ci = 2 + len(feat)
tc0 = cues[ci]["start"] if others else cues[ci]["start"]
for j, h in enumerate(others):
    a = spawn(h)
    chars[h["id"]] = a
    x, y = -3.2 + (j % 6) * 1.25 + rnd.uniform(-0.2, 0.2), 16.0 + (j // 6) * 2.0
    f0 = fr(tc0 - 0.2) + (j % 5) * 3
    bk.key_obj(a, f0 - 1, scale=0.0001, loc=(x, 30.0, Z0))
    bk.key_obj(a, f0, scale=1.0, loc=(x, 30.0, Z0))
    bk.walk(a, f0, f0 + 60, (x, 30.0, Z0), (x, y, Z0))
    bk.cheer(a, f0 + 61, fr(END), base_z=Z0)
if others:
    total += len(others)
    events += [{"t": round(tc0, 2), "type": "counter", "value": total}, {"t": round(tc0, 2), "type": "badge", "text": f"+{len(others)} HABITANTS", "color": "yellow"},
               {"t": round(tc0, 2), "type": "sfx", "name": "crowd_cheer", "gain": 0.7}]
    shots.append((tc0, cues[ci]["end"] + 0.1, (0, 0.5, 3.4), (0, 3.5, 2.0), (0, 18, 0.6), (0, 17, 0.8), 26))
    ci += 1
shots.append((shots[-1][1], END, (0, -2, 2.4), (0, 3, 3.2), (0, 14, 1.4), (0, 14, 1.6), 24))   # bilan + appel final
events.append({"t": round(cues[ci]["start"], 2), "type": "hud_sub", "text": f"{total} HABITANTS"})
events.append({"t": round(cues[ci]["start"], 2), "type": "sfx", "name": "ding"})
if any(total >= m > spec["total_avant"] for m in (15, 100)):
    events += [{"t": round(cues[ci]["start"], 2), "type": "milestone"}, {"t": round(cues[ci]["start"], 2), "type": "sfx", "name": "level_up"}]
prefs.keyframe_new_interpolation_type = 'BEZIER'

cams = []
for n, (t0, t1, l0, l1, g0, g1, lens) in enumerate(shots, 1):
    cd = bpy.data.cameras.new(f"Cam{n}")
    cd.lens = lens
    cd.dof.use_dof = True
    cd.dof.aperture_fstop = 3.2
    co = bpy.data.objects.new(f"Cam{n}", cd)
    col.objects.link(co)
    tgt = bpy.data.objects.new(f"Tgt{n}", None)
    col.objects.link(tgt)
    c = co.constraints.new('TRACK_TO')
    c.target, c.track_axis, c.up_axis = tgt, 'TRACK_NEGATIVE_Z', 'UP_Y'
    cd.dof.focus_object = tgt
    for f, l, g in ((fr(t0), l0, g0), (fr(t1) - 1, l1, g1)):
        co.location, tgt.location = l, g
        co.keyframe_insert("location", frame=f)
        tgt.keyframe_insert("location", frame=f)
    sc.timeline_markers.new(f"shot{n}", frame=fr(t0)).camera = co
    cams.append(co)
    if n > 1:
        events.append({"t": round(t0, 2), "type": "cut"})
sc.camera = cams[0]
sc.frame_start, sc.frame_end = 1, fr(END)
events.sort(key=lambda e: e["t"])
os.makedirs(args.out, exist_ok=True)
json.dump({"fps": FPS, "content_duration": round(END, 2), "events": events}, open(os.path.join(args.out, "events.json"), "w"), indent=2, ensure_ascii=False)

sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = args.samples
sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = args.res
sc.render.image_settings.file_format = 'PNG'
sc.view_settings.view_transform = 'Khronos PBR Neutral'
sc.view_settings.exposure = -0.75
if args.blend:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.blend))
if not args.no_render:
    if args.range:
        sc.frame_start, sc.frame_end = args.range
    sc.render.filepath = os.path.join(os.path.abspath(args.out), "f_")
    bpy.ops.render.render(animation=True)
