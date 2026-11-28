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
    """Texte de voix off d'une analyse, court (≈ 5–7 s) : nom, placement, moteurs, risque."""
    m = [x[0].lower() for x in info["muscles"]]
    muscles = ", ".join(m[:-1]) + f" et {m[-1]}" if len(m) > 1 else (m[0] if m else "")
    zone, conseil = info.get("risque", ("", ""))
    parle = info.get("risque_parle") or (f"à : {zone.lower()}" if zone else "")
    nom = info["nom"].lower()
    parts = [f"{nom.capitalize()}.", info.get("placement", "")]
    if muscles:
        parts.append(f"Moteurs : {muscles}.")
    if parle:
        parts.append(f"Attention {parle} : {conseil}.")
    return info.get("narration") or " ".join(p for p in parts if p)


def script_short(info):
    """Version courte pour le mode fluide (≈ 3–4 s, la vidéo ne s'arrête pas) : nom, geste clé, risque."""
    geste = (info.get("placement") or "").split(",")[0].rstrip(".")
    parle = info.get("risque_parle")
    parts = [f"{info['nom'].lower().capitalize()} : {geste[:1].lower() + geste[1:]}." if geste else f"{info['nom'].capitalize()}."]
    if parle:
        parts.append(f"Attention {parle}.")
    return info.get("narration_courte") or " ".join(parts)


def build_script(impacts, discipline="combat", short=False):
    from .anatomy import tag_pt
    segs = []
    if impacts:
        top = max(range(len(impacts)), key=lambda j: impacts[j]["score"])
        h1, h2 = impacts[top]["info"]["hook"]
        sep = " " if h1.endswith("?") else ". "
        segs.append({"id": "hook", "fr": tag_pt(f"{h1.capitalize()}{sep}{h2.capitalize()}.")})
    for k, m in enumerate(impacts):
        txt = script_short(m["info"]) if short else script_for(m["info"], k + 1, discipline)
        segs.append({"id": k, "fr": tag_pt(txt)})
    outro = "Abonne-toi, la partie deux arrive."
    if discipline == "capoeira":
        outro = "Abonne-toi, et on se retrouve dans la [pt]roda[/pt]. [pt]Axé[/pt] !"
    segs.append({"id": "outro", "fr": outro})
    return segs


def plain(text):
    return re.sub(r"\[/?(?:pt|fr|en)\]", "", text)


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


def synth(text, voice_id, lang=None):
    """Texte balisé → audio + mots horodatés ; les morceaux [pt] sont dits en portugais.
    lang (« pt », « fr »…) : tout le texte dans cette langue (documentaire pour un public brésilien, par exemple)."""
    from .phonetique import morceaux
    pieces = morceaux(text, lang or "fr")
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


def kokoro_available():
    from .motion import MOTION
    import shutil
    if not shutil.which("npx") or not (MOTION / "node_modules" / ".bin" / "hyperframes").exists():
        return False
    import importlib.util
    return importlib.util.find_spec("kokoro_onnx") is not None


def synth_kokoro(text, voice="ff_siwis", speed=1.05, lang=None):
    """Voix locale Kokoro (via HyperFrames) : français, termes [pt] prononcés en portugais du Brésil.
    Kokoro ne donne pas l'heure des mots : on les répartit selon la longueur de chaque morceau."""
    import tempfile
    from .motion import MOTION, _env
    pieces = [(p.strip(), "pt-br" if i % 2 else "fr-fr")
              for i, p in enumerate(re.split(r"\[pt\](.*?)\[/pt\]", text)) if p.strip()]
    if lang:                                   # tout le texte dans une seule langue (ex. pt-br, voix pm_alex)
        pieces = [(plain(text).strip(), lang)]
    audio, words, t = [], [], 0.0
    gap = np.zeros((int(0.05 * sfx.SR), 2))
    with tempfile.TemporaryDirectory() as d:
        for k, (piece, lang) in enumerate(pieces):
            wav = Path(d) / f"p{k}.wav"
            r = subprocess.run(["npx", "hyperframes", "tts", piece, "--voice", voice, "--lang", lang, "--speed", str(speed),
                                "--output", str(wav), "--json"], cwd=MOTION, capture_output=True, text=True, env=_env())
            if r.returncode != 0 or not wav.exists():
                raise RuntimeError(f"Kokoro : {(r.stdout + r.stderr)[-400:]}")
            a = sfx.read_wav(wav)
            # retire les silences de début/fin que Kokoro ajoute, pour enchaîner les morceaux naturellement
            loud = np.where(np.abs(a).max(axis=1) > 0.01)[0]
            if len(loud):
                a = a[max(loud[0] - 400, 0): loud[-1] + 2400]
            dur = len(a) / sfx.SR
            ws = piece.split()
            total = sum(len(w) + 1 for w in ws) or 1
            cur = t
            for w in ws:
                d_w = dur * (len(w) + 1) / total
                words.append({"text": w, "start": cur, "end": cur + d_w * 0.95, "lang": lang[:2]})
                cur += d_w
            audio += [a, gap]
            t += dur + len(gap) / sfx.SR
    return (np.concatenate(audio) if audio else np.zeros((0, 2))), words, t


# --------------------------------------------------------------------------- Supertonic 3 (hors ligne, commercial OK)

ST_MODEL = "sherpa-onnx-supertonic-3-tts-int8-2026-05-11"
ST_URL = f"https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/{ST_MODEL}.tar.bz2"
ST_VOICE = int(os.environ.get("AUTOVID_SUPERTONIC_VOICE", 9))   # 0–4 femmes, 5–9 hommes ; 9 = homme grave et posé
_ST = None


def supertonic_available():
    import importlib.util
    return importlib.util.find_spec("sherpa_onnx") is not None


def _supertonic():
    """Charge Supertonic 3 (téléchargé une fois depuis GitHub, ~145 Mo, dans ~/.cache/autovid/tts)."""
    global _ST
    if _ST is None:
        import tarfile
        import urllib.request

        import sherpa_onnx as so
        root = Path(os.environ.get("AUTOVID_CACHE", Path.home() / ".cache" / "autovid")) / "tts"
        d = root / ST_MODEL
        if not (d / "vocoder.int8.onnx").exists():
            root.mkdir(parents=True, exist_ok=True)
            print("  téléchargement de la voix Supertonic 3 (~145 Mo, une seule fois)…")
            arc = root / f"{ST_MODEL}.tar.bz2"
            urllib.request.urlretrieve(ST_URL, arc)
            with tarfile.open(arc) as t:
                t.extractall(root, filter="data")
            arc.unlink()
        f = lambda n: str(d / n)  # noqa: E731
        mc = so.OfflineTtsModelConfig()
        mc.supertonic = so.OfflineTtsSupertonicModelConfig(
            f("duration_predictor.int8.onnx"), f("text_encoder.int8.onnx"), f("vector_estimator.int8.onnx"),
            f("vocoder.int8.onnx"), f("tts.json"), f("unicode_indexer.bin"), f("voice.bin"))
        mc.num_threads = max(os.cpu_count() or 2, 2)
        _ST = so.OfflineTts(so.OfflineTtsConfig(model=mc))
    return _ST


def synth_supertonic(text, voice=None, lang="fr", speed=1.0):
    """Supertonic 3 : français, portugais, anglais… (31 langues). Les morceaux [pt] d'un texte français sont dits en
    portugais avec la même voix. Pas d'horodatage des mots : on les répartit selon leur longueur."""
    import sherpa_onnx as so
    tts = _supertonic()
    voice = ST_VOICE if voice is None else voice
    from .phonetique import morceaux
    pieces = morceaux(text, lang)              # [pt]…[/pt], [fr]…[/fr], [en]…[/en] : chaque mot avec l'accent de son pays
    audio, words, t = [], [], 0.0
    gap = np.zeros((int(0.06 * sfx.SR), 2))
    for piece, lg in pieces:
        g = so.GenerationConfig()
        g.sid, g.num_steps, g.speed, g.extra = int(voice), 24, float(speed), {"lang": lg}
        out = tts.generate(piece, g)
        mono = np.asarray(out.samples, dtype=np.float64)
        if out.sample_rate != sfx.SR:            # 44,1 kHz → 48 kHz pour le mixage
            idx = np.arange(int(len(mono) * sfx.SR / out.sample_rate)) * out.sample_rate / sfx.SR
            mono = np.interp(idx, np.arange(len(mono)), mono)
        loud = np.where(np.abs(mono) > 0.01)[0]
        if len(loud):
            mono = mono[max(loud[0] - 400, 0): loud[-1] + 2400]
        a = np.stack([mono, mono], axis=1)
        dur = len(a) / sfx.SR
        ws = piece.split()
        total = sum(len(w) + 1 for w in ws) or 1
        cur = t
        for w in ws:
            d_w = dur * (len(w) + 1) / total
            words.append({"text": w, "start": cur, "end": cur + d_w * 0.95, "lang": lg})
            cur += d_w
        audio += [a, gap]
        t += dur + len(gap) / sfx.SR
    return (np.concatenate(audio) if audio else np.zeros((0, 2))), words, t


def voice_segments(segs, voice_id=None, engine="auto", lang=None, controle=None):
    """Ajoute à chaque segment : audio (ou None), mots horodatés relatifs, durée.

    engine : "elevenlabs" (ta voix clonée), "supertonic" (Supertonic 3, hors ligne, commercial OK, voix n° 9 par
    défaut), "kokoro" (voix locale de test), "auto" (ElevenLabs si clé + voix, sinon Supertonic, sinon Kokoro). lang : « pt » = tout en portugais du Brésil
    (voix Kokoro masculine pm_alex), « fr » / None = français avec les termes [pt] en portugais. Renvoie le moteur."""
    if engine == "none":
        engine = None
    elif engine == "auto":                     # ta voix ElevenLabs, sinon Supertonic 3, sinon Kokoro
        engine = "elevenlabs" if voice_id and _key() else (
            "supertonic" if supertonic_available() else ("kokoro" if kokoro_available() else None))
    elif engine == "supertonic" and not supertonic_available():
        engine = None
    if controle is None:                       # correcteur + contrôle audio dès que Whisper est installable
        from .phonetique import whisper_disponible
        controle = whisper_disponible() and os.environ.get("AUTOVID_SANS_CONTROLE") != "1"
    elif engine == "elevenlabs" and not (voice_id and _key()):
        engine = None
    elif engine == "kokoro" and not kokoro_available():
        engine = None
    if engine and controle:
        return _voice_checked(segs, voice_id, engine, lang or "fr")
    for s in segs:
        if engine == "elevenlabs":
            s["audio"], s["words"], s["dur"] = synth(s["fr"], voice_id, lang if lang and lang != "fr" else None)
        elif engine == "supertonic":
            s["audio"], s["words"], s["dur"] = synth_supertonic(s["fr"], lang=lang or "fr")
        elif engine == "kokoro":
            if lang == "pt":
                s["audio"], s["words"], s["dur"] = synth_kokoro(s["fr"], voice="pm_alex", speed=1.0, lang="pt-br")
            else:
                s["audio"], s["words"], s["dur"] = synth_kokoro(s["fr"])
        else:
            s["audio"] = None
            s["words"], s["dur"] = estimate_words(s["fr"])
    return engine


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
    out = [(c[0]["start"], c[-1]["end"] + 0.12, " ".join(x["text"] for x in c)) for c in cues]
    return [(a, min(b, out[i + 1][0]) if i + 1 < len(out) else b, t) for i, (a, b, t) in enumerate(out)]


def fit_words(words, window):
    """Comprime les temps des mots pour tenir dans `window` secondes (texte sans voix, plus long que l'arrêt)."""
    end = max((w["end"] for w in words), default=0)
    if end <= window or end <= 0:
        return words
    k = window / end
    return [{**w, "start": w["start"] * k, "end": w["end"] * k} for w in words]


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


# --------------------------------------------------------------------------- agents : correcteur de texte + contrôle audio

RAPPORT = []                                   # dernier contrôle, écrit à côté de la vidéo par l'appelant


def _synth_any(engine, spoken, voice_id, lang, speed=1.0):
    if engine == "elevenlabs":
        return synth(spoken, voice_id, lang if lang != "fr" else None)
    if engine == "supertonic":
        return synth_supertonic(spoken, lang=lang, speed=speed)
    if lang == "pt":
        return synth_kokoro(spoken, voice="pm_alex", speed=speed, lang="pt-br")
    return synth_kokoro(spoken, speed=1.05 * speed)


def _voice_checked(segs, voice_id, engine, lang):
    """Pour chaque réplique : 1) texte écrit en toutes lettres (sous-titres), 2) graphie phonétique + balises de
    langue pour les mots étrangers (voix), 3) Whisper réécoute ; si des mots sont mal dits, on relance (débit plus
    lent, puis mot lu avec l'accent d'une autre langue) et on garde la meilleure prise. Les corrections qui marchent
    vont dans le lexique."""
    from . import phonetique as ph
    RAPPORT.clear()
    from .ai import has_credentials, relecture_phonetique
    if has_credentials():                      # agent de relecture : mots de chaque pays, avant la synthèse
        n = relecture_phonetique([s["fr"] for s in segs], lang)
        print(f"   relecture phonétique par Claude : {n} mot(s) ajouté(s) au lexique")
    langs = {"fr", "pt", "en"} - {lang}
    for s in segs:
        shown = ph.ecrire(s["fr"], lang)
        tagged = ph.marquer(shown, lang)
        ignorer = [m for m, lg in ph.morceaux(tagged, lang) if lg != lang]     # mots étrangers : jugés à part
        tries = [({}, 1.0)]
        best = None
        for k in range(4):
            if k >= len(tries):
                break
            variantes, speed = tries[k]
            spoken = ph.dire(tagged, lang, variantes)
            for mot, lg in variantes.get("__tags__", {}).items():
                spoken = re.sub(rf"(?<![\w\]-]){re.escape(mot)}(?![\w-])", f"[{lg}]{mot}[/{lg}]", spoken, count=1)
            audio, words, dur = _synth_any(engine, spoken, voice_id, lang, speed)
            heard = ph.transcrire(audio, sfx.SR, lang)
            errs = ph.comparer(shown, heard, lang, ignorer)
            cand = (ph.score(errs), k, audio, words, dur, spoken, heard, errs)
            if best is None or cand[0] < best[0]:
                best = cand
            if not errs:
                break
            if k == 0:                         # 2e prise : un peu plus lent
                tries.append(({}, 0.92))
                # 3e et 4e prises : un nom propre ou un mot long mal dit, lu avec l'accent d'un autre pays
                names = [w for w in re.findall(r"[^\W\d_][\w'-]*", plain(shown))
                         if (w[0].isupper() or len(w) >= 6) and any(ph.normaliser(w, lang) and
                                                                     ph.normaliser(w, lang)[0] in a.split() for a, _ in errs)]
                for lg in sorted(langs) if names else []:
                    tries.append(({"__tags__": {w: lg for w in names[:2]}}, 1.0))
        sc, k, audio, words, dur, spoken, heard, errs = best
        if k >= 2 and sc == 0:                 # une balise de langue a réglé le problème : on la retient
            for mot, lg in tries[k][0]["__tags__"].items():
                lex = ph.lexique()
                lex.setdefault(lang, {}).setdefault("etrangers", {})[mot] = lg
                ph.LEXIQUE.write_text(json.dumps(lex, ensure_ascii=False, indent=1), encoding="utf-8")
        shown_words = plain(shown).split()
        if len(shown_words) == len(words):     # sous-titres : les mots écrits, pas la graphie phonétique
            for w, t in zip(words, shown_words):
                w["text"] = t
        s.update(audio=audio, words=words, dur=dur, fr=shown, dit=spoken)
        RAPPORT.append({"id": str(s["id"]), "ecrit": shown, "dit": spoken, "entendu": heard, "prises": k + 1,
                        "erreurs": [{"attendu": a, "entendu": e} for a, e in errs]})
        etat = "OK" if not errs else "À ÉCOUTER : " + " ; ".join(f"« {a} » entendu « {e} »" for a, e in errs)
        print(f"   voix [{s['id']}] {etat}" + (f" (prise {k + 1})" if k else ""))
    return engine
