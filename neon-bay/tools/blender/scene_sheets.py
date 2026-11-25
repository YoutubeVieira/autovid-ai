"""Neon Bay - preview sheets of the v4 characters, the animals and the scene props.

    python3 tools/blender/scene_sheets.py                 # every sheet
    python3 tools/blender/scene_sheets.py animals props   # some sheets

Renders the views with render_previews.py (Cycles, NB_SAMPLES=12 by default) into a temporary
folder and assembles labelled sheets in tools/blender/previews/:
    humans_v4_sheet.png   human_f3 m3 f4 m4 m5: full body (Idle) + face close-ups
    humans_clips_sheet.png  new clips Dance, Dance2, Sit, Workout (on several humans)
    animals_sheet.png     dog, cat, gull, parrot, crab with their clips
    props_sheet.png       lifeguard tower, parasol, towel, DJ booth, speakers, weights, dumbbell, tube
Look at them (Read) after any change: floating parts, flipped normals, broken proportions.
"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "previews")
SHEETS = {
    "humans_v4": (["human_f3", "human_m3", "human_f4", "human_m4", "human_m5",
                   "human_f3@face", "human_m3@face", "human_f4@face", "human_m4@face", "human_m5@face"], 5),
    "humans_clips": (["human_f4@Dance:12", "human_m4@Dance2:18", "human_f3@Dance2:6", "human_m@Dance:30",
                      "human_m5@Workout:10", "human_m5@Sit:0", "human_f2@Sit:0", "human_m3@Workout:34"], 4),
    "animals": (["animal_dog", "animal_dog@Walk:6", "animal_dog@Run:3", "animal_dog@Sit:0",
                 "animal_cat", "animal_cat@Walk:8", "animal_cat@Sit:0", "animal_crab@Walk:4",
                 "animal_bird", "animal_bird@Fly:3", "animal_parrot", "animal_parrot@Fly:3"], 4),
    "props": (["prop_lifeguard_tower", "prop_parasol", "prop_towel", "prop_dj_booth",
               "prop_speaker_stack", "prop_weights", "prop_dumbbell", "prop_rescue_tube"], 4),
}


def out_name(spec):
    spec, _, weapon = spec.partition("+")
    name, _, variant = spec.partition("@")
    variant, _, cview = variant.partition("/")
    return name + ("_" + variant.replace(":", "_") if variant else "") + ("_" + cview if cview else "") + \
        ("+" + weapon if weapon else "")


def build(sheet, tmp):
    from PIL import Image, ImageDraw
    specs, cols = SHEETS[sheet]
    env = dict(os.environ, NB_PREVIEW_OUT=tmp, NB_SAMPLES=os.environ.get("NB_SAMPLES", "12"))
    subprocess.run([sys.executable, os.path.join(HERE, "render_previews.py")] + specs, env=env, check=True,
                   stdout=subprocess.DEVNULL)
    w, h = 480, 300
    rows = (len(specs) + cols - 1) // cols
    sheet_img = Image.new("RGB", (cols * w, rows * h), (20, 22, 26))
    d = ImageDraw.Draw(sheet_img)
    for i, s in enumerate(specs):
        im = Image.open(os.path.join(tmp, out_name(s) + ".png")).convert("RGB").resize((w, h))
        x, y = (i % cols) * w, (i // cols) * h
        sheet_img.paste(im, (x, y))
        d.rectangle([x, y, x + w - 1, y + 18], fill=(0, 0, 0))
        d.text((x + 6, y + 3), s, fill=(255, 255, 255))
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, sheet + "_sheet.png")
    sheet_img.save(path, optimize=True)
    print("[sheet]", path)


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="nb_sheet_") as tmp:
        for sh in (sys.argv[1:] or list(SHEETS)):
            build(sh, tmp)
