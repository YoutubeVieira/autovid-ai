"""Voix off explicative (ta voix clonée, ElevenLabs) + sous-titres français / portugais du Brésil / anglais.

- Le texte est écrit en français ; les termes capoeira sont balisés [pt]…[/pt] et synthétisés à part avec
  la langue portugaise pour être bien prononcés (ginga, rasteira, aú…).
- ElevenLabs renvoie l'heure de chaque caractère : on en tire l'heure de chaque mot pour les sous-titres.
- Sans clé ElevenLabs : pas d'audio, mais le script et les sous-titres sont produits (durées estimées).
"""
import base64
import json
import os
import re
import subprocess
from pathlib import Path

import numpy as np

from . import sfx

API = "https://api.elevenlabs.io/v1"
CONFIG = Path(os.environ.get("AUTOVID_CONFIG", Path.home() / ".config" / "autovid")) / "voix.json"
LANG_ISO3 = {"fr": "fra", "pt": "por", "en": "eng"}


# --------------------------------------------------------------------------- script

def script_for(info, n, discipline="combat"):
    """Texte de voix off d'une analyse (≈ 6–9 s à l'oral)."""
    m = [x[0].lower() for x in info["muscles"]]
    muscles = ", ".join(m[:-1]) + f" et {m[-1]}" if len(m) > 1 else (m[0] if m else "")
    zone, conseil = info.get("risque", ("", ""))
    nom = info["nom"].lower()
    parts = [f"Analyse {n}. {nom.capitalize()}.", info.get("placement", "")]
    if muscles:
        parts.append(f"Les muscles moteurs : {muscles}.")
    if zone:
        parts.append(f"Attention à {zone.lower()} : {conseil}.")
    text = " ".join(p for p in parts if p)
    return info.get("narration") or text


def build_script(impacts, discipline="combat"):
    from .anatomy import tag_pt
    segs = []
    if impacts:
        top = max(range(len(impacts)), key=lambda j: impacts[j]["score"])
        h1, h2 = impacts[top]["info"]["hook"]
        segs.append({"id": "hook", "fr": tag_pt(f"{h1.capitalize()} ? {h2.capitalize()}.")})
    for k, m in enumerate(impacts):
        segs.append({"id": k, "fr": tag_pt(script_for(m["info"], k + 1, discipline))})
    outro = "Abonne-toi pour la partie deux, et enregistre la vidéo pour l'essayer à l'entraînement."
    if discipline == "capoeira":
        outro = "Abonne-toi pour la suite, et on se retrouve dans la [pt]roda[/pt]. [pt]Axé[/pt] !"
    segs.append({"id": "outro", "fr": outro})
    return segs


def plain(text):
    return re.sub(r"\[/?pt\]", "", text)


# --------------------------------------------------------------------------- ElevenLabs

def _key():
    return os.environ.get("ELEVENLABS_API_KEY")


def clone_voice(samples, name, description="Voix du créateur (consentement : c'est ma propre voix)"):
    """Clonage instantané (IVC) à partir de 1 à 25 enregistrements propres de TA voix (1 à 3 min au total)."""
    import requests
    key = _key()
    if not key:
        raise SystemExit("ELEVENLABS_API_KEY manquante")
    files = [("files", (Path(s).name, open(s, "rb"))) for s in samples]
    try:
        r = requests.post(f"{API}/voices/add", headers={"xi-api-key": key},
                          data={"name": name, "description": description}, files=files, timeout=300)
    finally:
        for _, (_, fh) in files:
            fh.close()
    r.raise_for_status()
    voice_id = r.json()["voice_id"]
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps({"voice_id": voice_id, "name": name}, ensure_ascii=False))
    return voice_id


def default_voice():
    if os.environ.get("ELEVENLABS_VOICE_ID"):
        return os.environ["ELEVENLABS_VOICE_ID"]
    if CONFIG.exists():
        return json.loads(CONFIG.read_text()).get("voice_id")
    return None


def _decode(mp3_bytes):
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", "-", "-ac", "2", "-ar", str(sfx.SR), "-f", "f32le", "-"],
                       input=mp3_bytes, capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.float32).reshape(-1, 2).astype(np.float64)


def tts_piece(text, voice_id, lang):
    """Une phrase → (audio stéréo 48 kHz, [(caractère, début, fin)])."""
    import requests
    body = {"text": text, "model_id": os.environ.get("ELEVENLABS_TTS_MODEL", "eleven_multilingual_v2"),
            "voice_settings": {"stability": 0.45, "similarity_boost": 0.85, "style": 0.35, "use_speaker_boost": True}}
    url = f"{API}/text-to-speech/{voice_id}/with-timestamps?output_format=mp3_44100_128"
    headers = {"xi-api-key": _key()}
    r = requests.post(url, headers=headers, json={**body, "language_code": lang}, timeout=180)
    if r.status_code in (400, 422):            # modèle sans forçage de langue : on renvoie sans language_code
        r = requests.post(url, headers=headers, json=body, timeout=180)
    r.raise_for_status()
    data = r.json()
    al = data.get("alignment") or data.get("normalized_alignment") or {}
    chars = list(zip(al.get("characters", []), al.get("character_start_times_seconds", []),
                     al.get("character_end_times_seconds", [])))
    return _decode(base64.b64decode(data["audio_base64"])), chars


def synth(text, voice_id):
    """Texte balisé → audio + mots horodatés ; les morceaux [pt] sont dits en portugais."""
    pieces = [(p, "pt" if i % 2 else "fr") for i, p in enumerate(re.split(r"\[pt\](.*?)\[/pt\]", text)) if p.strip()]
    audio, words, t = [], [], 0.0
    gap = np.zeros((int(0.04 * sfx.SR), 2))
    for piece, lang in pieces:
        a, chars = tts_piece(piece.strip(), voice_id, lang)
        cur, start, end = "", None, None
        for ch, s, e in chars + [(" ", 0, 0)]:
            if ch.isspace():
                if cur:
                    words.append({"text": cur, "start": t + start, "end": t + end, "lang": lang})
                cur = ""
                continue
            if not cur:
                start = s
            cur += ch
            end = e
        audio += [a, gap]
        t += (len(a) + len(gap)) / sfx.SR
    return (np.concatenate(audio) if audio else np.zeros((0, 2))), words, t


def estimate_words(text, rate=14.0):
    """Sans voix : heure de chaque mot estimée à 14 caractères/s."""
    out, t = [], 0.0
    for w in plain(text).split():
        d = (len(w) + 1) / rate
        out.append({"text": w, "start": t, "end": t + d, "lang": "fr"})
        t += d
    return out, t


def voice_segments(segs, voice_id=None):
    """Ajoute à chaque segment : audio (ou None), mots horodatés relatifs, durée."""
    use_voice = bool(voice_id and _key())
    for s in segs:
        if use_voice:
            s["audio"], s["words"], s["dur"] = synth(s["fr"], voice_id)
        else:
            s["audio"] = None
            s["words"], s["dur"] = estimate_words(s["fr"])
    return use_voice


# --------------------------------------------------------------------------- sous-titres

def _srt_time(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def cues_from_words(words, max_chars=32):
    cues, cur = [], []
    for w in words:
        if cur and (len(" ".join(x["text"] for x in cur + [w])) > max_chars or w["start"] - cur[-1]["end"] > 0.6):
            cues.append(cur)
            cur = []
        cur.append(w)
    if cur:
        cues.append(cur)
    return [(c[0]["start"], c[-1]["end"] + 0.12, " ".join(x["text"] for x in c)) for c in cues]


def cues_from_text(text, t0, t1, max_chars=32):
    """Traduction sans horodatage par mot : on répartit les répliques sur la durée du segment."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > max_chars:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    total = sum(len(x) for x in lines) or 1
    out, t = [], t0
    for ln in lines:
        d = (t1 - t0) * len(ln) / total
        out.append((t, t + d, ln))
        t += d
    return out


def write_srt(cues, path):
    Path(path).write_text("".join(f"{i}\n{_srt_time(a)} --> {_srt_time(b)}\n{txt}\n\n"
                                  for i, (a, b, txt) in enumerate(cues, 1)), encoding="utf-8")
