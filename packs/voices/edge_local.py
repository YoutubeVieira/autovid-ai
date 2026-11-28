"""A LANCER SUR TON ORDINATEUR (pas dans l'environnement cloud: le service Microsoft y est inaccessible).
Voix neuronales Microsoft « Edge » (dont Vivienne et Remy, tres naturelles) a partir du meme script minute que tts.py.
Sortie identique: voice.wav, voice.srt, voice.json. NON TESTE ici (reseau bloque).

    pip install edge-tts           # + ffmpeg installe
    python edge_local.py script.txt --out voix --voice fr-FR-VivienneMultilingualNeural --rate +8%
    edge-tts --list-voices | grep fr-    # liste exacte des voix francaises disponibles

Voix francaises courantes: fr-FR-VivienneMultilingualNeural (femme), fr-FR-RemyMultilingualNeural (homme),
fr-FR-DeniseNeural (femme), fr-FR-HenriNeural (homme), fr-FR-EloiseNeural (fille). A confirmer avec --list-voices.

ATTENTION licence: edge-tts utilise l'API non officielle de la lecture a voix haute d'Edge. Pour une video monetisee,
prefere Azure AI Speech (meme voix, offre gratuite limitee, usage commercial couvert par le contrat Microsoft)."""
import argparse
import asyncio
import json
import os
import subprocess
import tempfile

import edge_tts

ap = argparse.ArgumentParser()
ap.add_argument("script")
ap.add_argument("--out", required=True)
ap.add_argument("--voice", default="fr-FR-VivienneMultilingualNeural")
ap.add_argument("--rate", default="+0%")
ap.add_argument("--pitch", default="+0Hz")
ap.add_argument("--total", type=float)
a = ap.parse_args()

lines = []
for raw in open(a.script, encoding="utf-8"):
    raw = raw.strip()
    if raw and not raw.startswith("#") and "|" in raw:
        t, text = raw.split("|", 1)
        shown, _, said = text.partition("||")
        lines.append((t.strip(), shown.strip(), (said or shown).strip()))


def dur(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]))


async def main():
    tmp = tempfile.mkdtemp()
    clips, prev_end = [], 0.0
    for i, (t, shown, said) in enumerate(lines):
        mp3 = os.path.join(tmp, f"{i}.mp3")
        await edge_tts.Communicate(said, a.voice, rate=a.rate, pitch=a.pitch).save(mp3)
        start = prev_end + float(t[1:]) if t.startswith("+") else float(t)
        d = dur(mp3)
        prev_end = start + d
        clips.append((start, d, shown, mp3))
    total = a.total or prev_end + 0.3
    os.makedirs(a.out, exist_ok=True)
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    for _, _, _, mp3 in clips:
        cmd += ["-i", mp3]
    parts = [f"[{i}:a]aformat=sample_rates=44100:channel_layouts=mono,adelay={int(s * 1000)}:all=1[a{i}]" for i, (s, _, _, _) in enumerate(clips)]
    graph = ";".join(parts) + ";" + "".join(f"[a{i}]" for i in range(len(clips))) + f"amix=inputs={len(clips)}:normalize=0,apad=whole_dur={total}[o]"
    subprocess.run(cmd + ["-filter_complex", graph, "-map", "[o]", "-t", str(total), os.path.join(a.out, "voice.wav")], check=True)

    def ts(x):
        h, r = divmod(int(x * 1000), 3600000)
        m, r = divmod(r, 60000)
        s, ms = divmod(r, 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    with open(os.path.join(a.out, "voice.srt"), "w", encoding="utf-8") as f:
        for i, (s, d, shown, _) in enumerate(clips, 1):
            f.write(f"{i}\n{ts(s)} --> {ts(s + d)}\n{shown}\n\n")
    json.dump({"voice": a.voice, "credit": "Voix: Microsoft " + a.voice, "duration": round(total, 2),
               "cues": [{"start": round(s, 3), "end": round(s + d, 3), "text": shown} for s, d, shown, _ in clips], "warnings": []},
              open(os.path.join(a.out, "voice.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(len(clips), "phrases ->", a.out)

asyncio.run(main())
