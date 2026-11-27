"""Synthese vocale francaise hors-ligne a partir d'un script minute.
Format du script (une ligne par phrase):   <debut_en_secondes> | <texte affiche> [|| <texte dit>]
Exemple:   3.6 | Mais des que tu t'abonnes, quelqu'un arrive.
           +0.15 | Phrase suivante, enchainee 0,15 s apres la precedente
           4.0 | Habitant de Caraguá || habitant de Caragoua      (orthographe phonetique pour la voix, sous-titre intact)
           Plusieurs essais: `|| texte A // texte B` + --verify --asr-model: Whisper garde la variante la mieux comprise

Usage: python3 tts.py script.txt --out voix_dir [--voice siwis] [--speaker 0] [--speed 1.0] [--models dossier]
Sortie: voice.wav (piste calee sur les horodatages), voice.srt (sous-titres a la bonne seconde), voice.json
Moteurs: --engine piper (pip install piper-tts + download_voices.py) ou --engine supertonic (pip install sherpa-onnx, voix 0-9, 5-9 = hommes)."""
import argparse
import sys
import json
import os
import struct
import wave


here = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("script")
ap.add_argument("--out", required=True)
ap.add_argument("--engine", default="piper", choices=["piper", "supertonic", "kokoro"])
ap.add_argument("--kokoro-model", help="dossier kokoro-multi-lang-v1_0 extrait (voix francaise: --speaker 30 = ff_siwis)")
ap.add_argument("--st-model", help="dossier du modele supertonic extrait")
ap.add_argument("--lang", default="fr")
ap.add_argument("--verify", action="store_true", help="controle Whisper: teste plusieurs ecritures de chaque phrase et garde la mieux comprise")
ap.add_argument("--asr-model", help="dossier sherpa-onnx-whisper-base extrait")
ap.add_argument("--voice", default="siwis")
ap.add_argument("--speaker", type=int, default=0, help="upmc: 0=jessica, 1=pierre")
ap.add_argument("--speed", type=float, default=1.0)
ap.add_argument("--models", default=os.path.join(here, "models"))
ap.add_argument("--fx", default="none", choices=["none", "viral"], help="viral = voix de narrateur TikTok: egaliseur + compression + limiteur")
ap.add_argument("--pitch", type=float, default=0.0, help="demi-tons (ex. -1.5 = voix plus grave), necessite ffmpeg avec rubberband")
ap.add_argument("--total", type=float, help="duree totale de la piste (s); sinon fin de la derniere phrase")
a = ap.parse_args()

meta = json.load(open(os.path.join(here, "voices.json"), encoding="utf-8"))
if a.engine == "kokoro":
    # Kokoro 82M (Apache-2.0). Pas de phonemiseur francais dans le wheel sherpa: on phonemise avec l'espeak de piper-tts
    # puis on appelle le modele ONNX directement (jetons = phonemes IPA, y compris la tilde combinante des nasales).
    import numpy as np
    import onnxruntime as ort
    from piper.phonemize_espeak import EspeakPhonemizer
    K = a.kokoro_model or os.path.join(a.models, "kokoro-multi-lang-v1_0")
    cfg = {"credit": "Voix: Kokoro-82M ff_siwis (donnees SIWIS, University of Edinburgh, CC BY 4.0)", "license": "modele Apache-2.0; voix ff_siwis CC BY 4.0"}
    _sess = ort.InferenceSession(os.path.join(K, "model.onnx"), providers=["CPUExecutionProvider"])
    _voices = np.fromfile(os.path.join(K, "voices.bin"), dtype=np.float32).reshape(-1, 510, 1, 256)
    _tok = {}
    for _l in open(os.path.join(K, "tokens.txt"), encoding="utf-8"):
        _p = _l.rstrip("\n").rsplit(" ", 1)
        if len(_p) == 2:
            _tok[_p[0]] = int(_p[1])
    _phon = EspeakPhonemizer()

    def synth(text):
        out = []
        for sent in _phon.phonemize("fr", text):
            ids = [_tok[c] for c in "".join(sent) if c in _tok][:500]
            if not ids:
                continue
            style = _voices[a.speaker, len(ids), 0][None, :]
            wav = _sess.run(None, {"tokens": np.array([[0] + ids + [0]], dtype=np.int64), "style": style,
                                   "speed": np.array([a.speed], dtype=np.float32)})[0].reshape(-1)
            out += list(wav) + [0.0] * int(0.12 * 24000)
        return out, 24000
elif a.engine == "supertonic":
    import sherpa_onnx
    M = a.st_model or os.path.join(a.models, meta["engines"]["supertonic"]["archive"])
    cfg = {"credit": "Voix: Supertonic 3 (Supertone), voix n\u00b0%d" % a.speaker, "license": meta["engines"]["supertonic"]["license"]}
    _tts = sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
        supertonic=sherpa_onnx.OfflineTtsSupertonicModelConfig(
            duration_predictor=M + "/duration_predictor.int8.onnx", text_encoder=M + "/text_encoder.int8.onnx",
            vector_estimator=M + "/vector_estimator.int8.onnx", vocoder=M + "/vocoder.int8.onnx",
            tts_json=M + "/tts.json", unicode_indexer=M + "/unicode_indexer.bin", voice_style=M + "/voice.bin"),
        num_threads=2)))

    def synth(text):
        gc = sherpa_onnx.GenerationConfig()
        gc.sid, gc.num_steps, gc.speed = a.speaker, 24, a.speed
        gc.extra["lang"] = a.lang
        g = _tts.generate(text, gc)
        return list(g.samples), g.sample_rate
else:
    from piper import PiperVoice, SynthesisConfig
    cfg = meta["voices"][a.voice]
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
        shown, _, said = text.partition("||")
        lines.append((t.strip(), shown.strip(), (said or shown).strip()))

clips, sr = [], None
prev_end = 0.0
verif = []
sys.path.insert(0, os.path.join(here, "..", "..", "editor"))
import prononciation as _pr
for t, text, said in lines:
    if a.verify and a.asr_model:
        from autoeditor import asr as _asr
        alts = [x.strip() for x in said.split("//")]          # variantes ecrites a la main: "texte A // texte B"
        base = alts[0]
        cands = [("brut", _pr.fix(base, "overrides")), ("leger", _pr.fix(base, "light")), ("complet", _pr.fix(base, "full"))]
        cands += [(f"variante{i}", x) for i, x in enumerate(alts[1:], 1)]
        seen, best = set(), None
        for name, cand in cands:
            if cand in seen:
                continue
            seen.add(cand)
            sm, sr_ = synth(cand)
            tmpw = os.path.join(a.out, "_verify.wav")
            os.makedirs(a.out, exist_ok=True)
            with wave.open(tmpw, "w") as w_:
                w_.setnchannels(1)
                w_.setsampwidth(2)
                w_.setframerate(sr_)
                w_.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, v)) * 32767)) for v in sm))
            heard = _asr.transcribe(a.asr_model, tmpw)
            wer, diffs = _asr.compare(text, heard)
            if best is None or wer < best[0] - 1e-9:
                best = (wer, name, cand, sm, sr_, heard)
        os.remove(os.path.join(a.out, "_verify.wav"))
        wer, name, said, samples, sr, heard = best
        verif.append({"phrase": text, "variante": name, "texte_envoye": said, "entendu": heard, "erreur_mots": wer})
    else:
        if not a.verify:
            said = _pr.fix(said, "overrides") if a.engine == "supertonic" else said
        samples, sr = synth(said)
    # debut absolu ("3.6") ou enchaine apres la phrase precedente ("+0.15" = pause de 0,15 s)
    start = prev_end + float(t[1:]) if t.startswith("+") else float(t)
    prev_end = start + len(samples) / sr
    clips.append((start, text, samples))

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
json.dump({"voice": a.voice, "credit": cfg["credit"], "license": cfg["license"], "duration": round(total, 2), "cues": cues, "warnings": warn, "verification": verif},
          open(os.path.join(a.out, "voice.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
VIRAL = ("highpass=f=85,equalizer=f=140:t=q:w=1:g=3.5,equalizer=f=320:t=q:w=1.2:g=-2,"
         "equalizer=f=3300:t=q:w=1.1:g=4.5,equalizer=f=9000:t=q:w=1.5:g=-3,"
         "acompressor=threshold=-24dB:ratio=5:attack=3:release=70:makeup=7,asoftclip=type=tanh:threshold=0.8,alimiter=limit=0.85,loudnorm=I=-16:TP=-2:LRA=7")
if a.fx != "none" or a.pitch:
    import shutil
    import subprocess
    raw = os.path.join(a.out, "voice_raw.wav")
    shutil.copy(os.path.join(a.out, "voice.wav"), raw)
    chain = []
    if a.pitch:
        chain.append(f"rubberband=pitch={2 ** (a.pitch / 12):.5f}:formant=preserved")
    if a.fx == "viral":
        chain.append(VIRAL)
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", raw, "-af", ",".join(chain),
                    os.path.join(a.out, "voice.wav")], check=True)
print(f"{len(cues)} phrases, {total:.1f}s -> {a.out}/voice.wav | credit: {cfg['credit']}")
for w_ in warn:
    print("ATTENTION:", w_)
