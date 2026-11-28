"""Episode 0 (pub de la ville, foule anonyme, pas de faux compteur) - meme moteur que episode_monde.py.
Les temps suivent la voix (voice.json).
Usage (episode 0, pub de la ville): python episode_zero.py -- --spec episode.json --voice <dossier voice.json> --out frames/ [--res 540 960] [--samples 10] [--range a b] [--blend f.blend] [--no-render]"""
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
ap.add_argument("--decoupage", help="decoupage.json de realisation/realisation.py: remplace les plans de camera par defaut")
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
                               accessory=lk.get("accessory"), face="smile", faces=(["smile", lk["face"], "happy", "surprise", "scared", "sad", "angry", "love"] if args.decoupage else ["smile", lk["face"], "happy", "surprise"]), seed=h["id"])
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


OFF = spec.get("decalage_cues", 0)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "monde"))
import monde as M
chars = {}
spots = {}
shots = []
prefs.keyframe_new_interpolation_type = 'LINEAR'
events = [{"t": 0.0, "type": "hud_sub", "text": "OBJECTIF : 10 000 HABITANTS"}]
rz = random.Random(0)
KEYS = [k for k in M.METIERS if k not in ("habitant", "trexsinge", "mamie", "maire", "astronaute")]
_n = [0]


def anon(key=None):
    """Figurine anonyme (jamais un vrai spectateur): decor de foule."""
    _n[0] += 1
    key = key or rz.choice(KEYS)
    h = {"id": 900 + _n[0], "prenom": f"foule{_n[0]}", "look": M.look_for(f"foule{_n[0]}", key, _n[0])}
    return spawn(h)


def pop(a, t, x, y, rot=0.0):
    f0 = fr(t)
    bk.key_obj(a, f0 - 1, scale=0.0001, loc=(x, y, Z0), rot_z=rot)
    bk.key_obj(a, f0, scale=1.0, loc=(x, y, Z0), rot_z=rot)


# cue 1: trois metiers qui font rever (boulanger, astronaute, maire) -> cue 2: ils partent, la ville est vide
heroes = []
for i, k in enumerate(("boulanger", "astronaute", "maire")):
    a = anon(k)
    t = cues[1 + OFF]["start"] + 0.35 * i
    x = (-1.3, 0.0, 1.3)[i]
    pop(a, t, x, 12.0 + 0.6 * (i == 1), rot=(-8, 0, 8)[i])
    bk.wave(a, fr(t) + 6, fr(cues[2 + OFF]["start"]) + 10, side="R")
    events.append({"t": round(t, 2), "type": "sfx", "name": "pop"})
    heroes.append((a, x))
for a, x in heroes:                                   # la ville se vide
    t_out = cues[2 + OFF]["start"] + 0.3
    bk.walk(a, fr(t_out), fr(t_out + 1.0), (x, 12.0, Z0), (x * 6, 12.0, Z0))
    bk.key_obj(a, fr(t_out + 1.1), loc=(x * 6, 12.0, Z0), scale=0.0001)
# cue 3-5: la foule arrive par vagues (20 -> 45 figurines), cue 5-7: tout le monde fete
grid = [(-4.4 + (j % 9) * 1.1 + rz.uniform(-0.15, 0.15), 11.5 + (j // 9) * 1.5) for j in range(45)]
for j, (x, y) in enumerate(grid):
    cue = cues[3 + OFF] if j < 20 else cues[4 + OFF] if j < 35 else cues[5 + OFF]
    t = cue["start"] + 0.12 * (j - (0 if j < 20 else 20 if j < 35 else 35))
    a = anon()
    pop(a, t, x, y, rot=rz.uniform(-20, 20))
    bk.cheer(a, fr(t) + 2, fr(END), base_z=Z0)
    if j in (0, 20, 35):
        events.append({"t": round(t, 2), "type": "sfx", "name": "pop_double"})
events += [{"t": round(cues[5 + OFF]["start"], 2), "type": "badge", "text": "OBJECTIF · 10 000 AMIS", "color": "yellow"},
           {"t": round(cues[5 + OFF]["start"], 2), "type": "sfx", "name": "crowd_cheer", "gain": 0.7}]
ci = 5 + OFF
total = 0

if args.decoupage:                                      # --- plans de camera, expressions, sons et effets pilotes par le decoupage
    DEC = json.load(open(args.decoupage, encoding="utf-8"))
    LENS = 35.0
    PLAN = {"large": (11.0, 2.4, 1.4, 0.0), "moyen": (4.6, 1.3, 1.0, 0.0), "gros_plan": (2.3, 1.05, 1.0, 0.0), "insert": (1.7, 0.7, 0.55, 0.0),
            "contre_plongee": (3.6, 0.35, 1.3, 0.0), "reaction": (2.6, 1.05, 1.0, 0.0)}   # distance, hauteur camera, hauteur cible
    shots, dec_cam = [], []
    faces_ok = {}
    for n_, d in enumerate(DEC):
        who = spots.get(d["sujet"])
        dist, hz, tz, _ = PLAN.get("gros_plan" if (who and d["plan"] == "insert") else d["plan"], PLAN["moyen"])   # un personnage se cadre en plan moyen/serre, pas en insert
        if who and d["plan"] in ("gros_plan", "insert"):
            dist, hz, tz = 2.7, 1.1, 0.95
        if who:
            (sx, sy, _z), arm_ = who
            tgt = (sx, sy, tz)
        else:
            arm_, tgt = None, (0.0, 14.0, tz + 0.3)
        side_ = 0.5 if n_ % 2 else -0.5
        cam = d["camera"]
        c0 = [tgt[0] + side_, tgt[1] - dist, hz]
        c1 = list(c0)
        t1_ = list(tgt)
        if cam.startswith("push_in") or cam == "punch_in":
            c1[1] += dist * 0.15
        elif cam == "pull_out_lent":
            c0[1] += dist * 0.12
        elif cam == "orbite_legere":
            c0[0], c1[0] = tgt[0] - 0.8, tgt[0] + 0.8
        elif cam == "tilt_up":
            t1_[2] += 0.5
        elif "shake" in cam:
            c1[0] += 0.05
        shots.append((d["debut"], d["fin"], tuple(c0), tuple(c1), tuple(tgt), tuple(t1_), LENS * d["zoom"][0]))
        dec_cam.append(LENS * d["zoom"][1])
        if arm_ is not None:
            try:
                bk.set_face(arm_, fr(d["debut"]), d["visage"])
            except Exception:
                pass
        if d.get("son"):
            events.append({"t": round(d["debut"], 2), "type": "sfx", "name": d["son"], "gain": 0.6})
        if d.get("effet") in ("flash", "shake"):
            events.append({"t": round(d["debut"], 2), "type": d["effet"]})
        if d.get("punch_in") and d.get("texte_ecran"):
            txt, mot = d["texte_ecran"].lower(), d["punch_in"]["mot"].lower()
            pos = txt.find(mot)
            if pos >= 0:
                ratio = pos / max(1, len(txt))
                events.append({"t": round(d["debut"] + ratio * (d["fin"] - d["debut"]) * 2.4, 2), "type": "punch"})
    shots[-1] = shots[-1][:1] + (END,) + shots[-1][2:]
prefs.keyframe_new_interpolation_type = 'BEZIER'
for mu in spec.get("musique", []):                      # fond sonore different a chaque episode (choisi par monde.py)
    t_mu = cues[ci]["start"] if mu.get("role") == "palier" else 0.0
    events.append({"t": round(t_mu, 2), "type": "sfx", "name": mu["role"], "file": mu["file"], "gain": mu.get("gain", 0.3), "dur": round(END - t_mu, 2)})

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
    if args.decoupage:
        cd.lens = shots[n - 1][6]
        cd.keyframe_insert("lens", frame=fr(t0))
        cd.lens = dec_cam[n - 1]
        cd.keyframe_insert("lens", frame=fr(t1) - 1)
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
