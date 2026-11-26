#!/usr/bin/env python3
"""Contrôle des voix off : transcrit chaque fichier avec Whisper (sherpa-onnx, hors ligne) et compare au texte attendu.
  python3 tools/voix/ecoute_voix.py lignes.json dossier_wav/   (modèle dans ASR_DIR, défaut /home/user/tts/sherpa-onnx-whisper-small)"""
import json, os, sys, re, difflib, sherpa_onnx, soundfile as sf, numpy as np
D = os.environ.get('ASR_DIR', '/home/user/tts/sherpa-onnx-whisper-small')
rec = sherpa_onnx.OfflineRecognizer.from_whisper(encoder=f'{D}/small-encoder.int8.onnx', decoder=f'{D}/small-decoder.int8.onnx', tokens=f'{D}/small-tokens.txt', language='fr', task='transcribe', num_threads=4)
norm = lambda t: re.sub(r'[^a-zàâçéèêëîïôûùüÿœ\' ]', ' ', t.lower().replace('’', "'")).split()
lignes, d = json.load(open(sys.argv[1])), sys.argv[2]; bad = 0
for l in lignes:
    x, sr = sf.read(f"{d}/{l['id']}.wav", dtype='float32'); x = x if x.ndim == 1 else x.mean(1)
    s = rec.create_stream(); s.accept_waveform(sr, x); rec.decode_stream(s); got = s.result.text.strip()
    ratio = difflib.SequenceMatcher(None, norm(l['voix']), norm(got)).ratio(); ok = ratio >= .8; bad += not ok
    print(('OK  ' if ok else 'À REVOIR ') + f"{l['id']} ({ratio:.2f}) attendu : {l['voix']}\n      entendu : {got}")
print('Toutes les lignes sont bonnes.' if not bad else f'{bad} ligne(s) à revoir.')
