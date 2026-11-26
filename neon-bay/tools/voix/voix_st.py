#!/usr/bin/env python3
"""Voix off Supertonic 3 (sherpa-onnx, hors ligne, usage commercial : code MIT, modèle OpenRAIL-M).
  python3 tools/voix/voix_st.py lignes.json sortie/ [--voix 9] [--vitesse 1.0]
  python3 tools/voix/voix_st.py --essai sortie/      (même phrase avec les 10 voix : 0-4 femmes, 5-9 hommes)
lignes.json : [{"id": "l1", "dit": "texte prononcé (orthographe phonétique si besoin)"}, ...]
Modèle attendu dans TTS_DIR (défaut /home/user/tts/sherpa-onnx-supertonic-3-tts-int8-2026-05-11)."""
import json, os, sys, sherpa_onnx, soundfile as sf
D = os.environ.get('TTS_DIR', '/home/user/tts/sherpa-onnx-supertonic-3-tts-int8-2026-05-11')
def arg(k, d):
    return sys.argv[sys.argv.index('--' + k) + 1] if '--' + k in sys.argv else d
cfg = sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(supertonic=sherpa_onnx.OfflineTtsSupertonicModelConfig(
    duration_predictor=f'{D}/duration_predictor.int8.onnx', text_encoder=f'{D}/text_encoder.int8.onnx', vector_estimator=f'{D}/vector_estimator.int8.onnx',
    vocoder=f'{D}/vocoder.int8.onnx', tts_json=f'{D}/tts.json', unicode_indexer=f'{D}/unicode_indexer.bin', voice_style=f'{D}/voice.bin'), num_threads=4))
tts = sherpa_onnx.OfflineTts(cfg)
def say(text, sid, speed, out):
    gc = sherpa_onnx.GenerationConfig(); gc.sid = sid; gc.num_steps = 24; gc.speed = speed; gc.extra = {'lang': 'fr'}
    a = tts.generate(text, gc); sf.write(out, a.samples, a.sample_rate); return len(a.samples) / a.sample_rate
if '--essai' in sys.argv:
    out = sys.argv[sys.argv.index('--essai') + 1]; os.makedirs(out, exist_ok=True)
    for v in range(10): print(v, round(say("Cette nuit, Néon Bay ne dormira pas. La police est partout, mais moi, je n'ai plus rien à perdre.", v, 1.0, f'{out}/essai-{v}.wav'), 2), 's')
else:
    lignes, out = json.load(open(sys.argv[1])), sys.argv[2]; os.makedirs(out, exist_ok=True)
    v, sp = int(arg('voix', 9)), float(arg('vitesse', 1.0))
    for l in lignes: print(l['id'], round(say(l['dit'], v, float(l.get('vitesse', sp)), f"{out}/{l['id']}.wav"), 2), 's')
