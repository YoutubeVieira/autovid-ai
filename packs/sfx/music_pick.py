"""Choisit un fond sonore DIFFERENT a chaque episode: la piste la moins recemment utilisee; si toutes ont servi dans les derniers
`memoire` episodes, une nouvelle piste est composee (graine inedite, meme humeur).
    from music_pick import pick
    pick("suspense", episode=3)   # -> {"file": "music_gen/suspense_4.mp3", "mood": "suspense", ...}
Historique: monde/musique_historique.json"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HIST = os.path.join(HERE, "..", "..", "monde", "musique_historique.json")
LIB = {"suspense": ["music_suspense.mp3"], "calme": ["music_calme.mp3"], "aventure": ["music_aventure.mp3"], "victoire": ["music_victoire.mp3"]}


def _load():
    return json.load(open(HIST, encoding="utf-8")) if os.path.exists(HIST) else {"utilises": []}


def pick(mood, episode, kind="musique", memoire=5, record=True):
    h = _load()
    key = "ambiance" if kind == "ambiance" else "mood"
    pool = list(LIB.get(mood, [])) if kind == "musique" else []
    gen_dir = os.path.join(HERE, "music_gen")
    if os.path.isdir(gen_dir):
        pool += [f"music_gen/{f}" for f in sorted(os.listdir(gen_dir)) if f.startswith(mood + "_") and f.endswith(".mp3")]
    recent = {u["file"] for u in h["utilises"] if u["episode"] > episode - memoire and u["episode"] != episode and u.get(key) == mood}
    last = {u["file"]: u["episode"] for u in h["utilises"]}
    free = [f for f in pool if f not in recent]
    if free:
        f = min(free, key=lambda x: last.get(x, -1))
    else:
        sys.path.insert(0, HERE)
        import make_music
        seed = len([u for u in h["utilises"] if u.get(key) == mood]) + 1
        while os.path.exists(os.path.join(gen_dir, f"{mood}_{seed}.mp3")):
            seed += 1
        f = f"music_gen/{mood}_{seed}.mp3"
        if True:
            x, _ = make_music.ambiance(mood, seed) if kind == "ambiance" else make_music.compose(mood, seed)
            make_music.save_mp3(x, os.path.join(HERE, f))
    entry = {"episode": episode, key: mood, "file": f}
    if record:
        h["utilises"] = [u for u in h["utilises"] if not (u["episode"] == episode and u.get(key) == mood)] + [entry]
        os.makedirs(os.path.dirname(HIST), exist_ok=True)
        json.dump(h, open(HIST, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    return entry
