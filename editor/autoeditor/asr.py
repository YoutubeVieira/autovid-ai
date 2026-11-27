"""Reconnaissance vocale hors-ligne (Whisper via sherpa-onnx) pour verifier ce que la voix dit vraiment.
Modele: sherpa-onnx-whisper-base (~200 Mo) -> https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-base.tar.bz2"""
import difflib
import os
import re
import subprocess
import tempfile
import unicodedata
import wave

_rec = {}


def load(model_dir, language="fr"):
    key = (model_dir, language)
    if key not in _rec:
        import sherpa_onnx
        name = os.path.basename(os.path.normpath(model_dir)).replace("sherpa-onnx-whisper-", "")
        files = os.listdir(model_dir)
        enc = next(f for f in files if f.startswith(name + "-encoder") and f.endswith(".int8.onnx"))
        dec = next(f for f in files if f.startswith(name + "-decoder") and f.endswith(".int8.onnx"))
        _rec[key] = sherpa_onnx.OfflineRecognizer.from_whisper(
            encoder=os.path.join(model_dir, enc), decoder=os.path.join(model_dir, dec),
            tokens=os.path.join(model_dir, name + "-tokens.txt"), language=language, task="transcribe", num_threads=2)
    return _rec[key]


def transcribe(model_dir, audio_path, language="fr", start=None, end=None):
    """Transcrit un fichier audio (n'importe quel format ffmpeg), ou un extrait [start, end] en secondes."""
    import numpy as np
    rec = load(model_dir, language)
    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, "a.wav")
        cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
        if start is not None:
            cmd += ["-ss", str(max(0.0, start))]
        cmd += ["-i", str(audio_path)]
        if end is not None:
            cmd += ["-t", str(end - (start or 0.0))]
        subprocess.run(cmd + ["-ac", "1", "-ar", "16000", "-sample_fmt", "s16", wav], check=True)
        with wave.open(wav) as w:
            x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
        s = rec.create_stream()
        s.accept_waveform(16000, x)
        rec.decode_stream(s)
        return s.result.text.strip()


_UN = "zéro un deux trois quatre cinq six sept huit neuf dix onze douze treize quatorze quinze seize".split()
_DIZ = {20: "vingt", 30: "trente", 40: "quarante", 50: "cinquante", 60: "soixante"}


def _num(n):
    if n < 17:
        return _UN[n]
    if n < 20:
        return "dix " + _UN[n - 10]
    if n < 70 and n % 10 == 0:
        return _DIZ[n]
    if n < 70:
        return _DIZ[n // 10 * 10] + (" et " if n % 10 == 1 else " ") + _UN[n % 10]
    return {100: "cent"}.get(n, str(n))


def norm_words(text):
    text = re.sub(r"\b(\d{1,3})\b", lambda m: _num(int(m.group(1))), text)
    t = unicodedata.normalize("NFKD", text.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.replace("œ", "oe").replace("’", "'")
    return re.findall(r"[a-z0-9]+", t.replace("'", " "))


def compare(expected, heard):
    """Compare le texte attendu et le texte entendu. Retourne (taux_erreur_mots, liste de differences)."""
    a, b = norm_words(expected), norm_words(heard)
    sm = difflib.SequenceMatcher(None, a, b)
    diffs, wrong = [], 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != "equal":
            diffs.append({"attendu": " ".join(a[i1:i2]), "entendu": " ".join(b[j1:j2])})
            wrong += max(i2 - i1, j2 - j1)
    return round(wrong / max(1, len(a)), 3), diffs
