"""Synthese vocale francaise hors-ligne a partir d'un script minute.
Format du script (une ligne par phrase):   <debut_en_secondes> | <texte>
Exemple:   3.6 | Mais des que tu t'abonnes, quelqu'un arrive.

Usage: python3 tts.py script.txt --out voix_dir [--voice siwis] [--speaker 0] [--speed 1.0] [--models dossier]
Sortie: voice.wav (piste calee sur les horodatages), voice.srt (sous-titres a la bonne seconde), voice.json
Necessite: pip install piper-tts  (et python3 download_voices.py)"""
import argparse
import json
import os
import struct
import wave

from piper import PiperVoice, SynthesisConfig

here = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("script")
ap.add_argument("--out", required=True)
ap.add_argument("--voice", default="siwis")
ap.add_argument("--speaker", type=int, default=0, help="upmc: 0=jessica, 1=pierre")
ap.add_argument("--speed", type=float, default=1.0)
ap.add_argument("--models", default=os.path.join(here, "models"))
ap.add_argument("--total", type=float, help="duree totale de la piste (s); sinon fin de la derniere phrase")
a = ap.parse_args()

cfg = json.load(open(os.path.join(here, "voices.json"), encoding="utf-8"))["voices"][a.voice]
d = os.path.join(a.models, cfg["archive"])
onnx = next(f for f in os.listdir(d) if f.endswith(".onnx"))
voice = PiperVoice.load(os.path.join(d, onnx), config_path=os.path.join(d, onnx + ".json"))
syn = SynthesisConfig(speaker_id=a.speaker if cfg["speakers"] > 1 else None, length_scale=1.0 / a.speed)


def synth(text):
    pcm = b"".join(c.audio_int16_bytes for c in voice.synthesize(text, syn_config=syn))
    n = len(pcm) // 2
    return [x / 32768.0 for x in struct.unpack(f"<{n}h", pcm)], voice.config.sample_rate


lines = []
for raw in open(a.script, encoding="utf-8"):
    raw = raw.strip()
    if raw and not raw.startswith("#") and "|" in raw:
        t, text = raw.split("|", 1)
        lines.append((float(t), text.strip()))

clips, sr = [], None
for t, text in lines:
    samples, sr = synth(text)
    clips.append((t, text, samples))

end = max(t + len(s) / sr for t, _, s in clips)
total = a.total or end + 0.3
track = [0.0] * int(total * sr)
cues, warn = [], []
for i, (t, text, s) in enumerate(clips):
    o = int(t * sr)
    for k, v in enumerate(s):
        if o + k < len(track):
            track[o + k] += v
    dur = len(s) / sr
    cues.append({"start": round(t, 3), "end": round(t + dur, 3), "text": text})
    if i + 1 < len(clips) and t + dur > clips[i + 1][0] + 0.05:
        warn.append(f"ligne {i + 1} deborde sur la suivante de {t + dur - clips[i + 1][0]:.2f}s: raccourcir le texte ou decaler")

os.makedirs(a.out, exist_ok=True)
peak = max(abs(v) for v in track) or 1.0
g = 0.9 / peak
with wave.open(os.path.join(a.out, "voice.wav"), "w") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(sr)
    w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, v * g)) * 32767)) for v in track))


def ts(x):
    h, r = divmod(int(x * 1000), 3600000)
    m, r = divmod(r, 60000)
    s_, ms = divmod(r, 1000)
    return f"{h:02d}:{m:02d}:{s_:02d},{ms:03d}"


with open(os.path.join(a.out, "voice.srt"), "w", encoding="utf-8") as f:
    for i, c in enumerate(cues, 1):
        f.write(f"{i}\n{ts(c['start'])} --> {ts(c['end'])}\n{c['text']}\n\n")
json.dump({"voice": a.voice, "credit": cfg["credit"], "license": cfg["license"], "duration": round(total, 2), "cues": cues, "warnings": warn},
          open(os.path.join(a.out, "voice.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print(f"{len(cues)} phrases, {total:.1f}s -> {a.out}/voice.wav | credit: {cfg['credit']}")
for w_ in warn:
    print("ATTENTION:", w_)
