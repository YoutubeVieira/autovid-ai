"""Serveur de voix permanent : garde les modeles (Kokoro, Chatterbox) en memoire entre deux phrases.
Protocole : une demande JSON par ligne sur l'entree standard, une reponse JSON par ligne sur la sortie standard.
  demande : {"id": "...", "moteur": "kokoro"|"chatterbox"|"test", "texte": "...", "langue": "fr"|"pt"|"en",
             "voix": "ff_siwis", "echantillon": "chemin.wav", "sortie": "chemin.wav", "vitesse": 1.0}
  reponse : {"id": "...", "ok": true} ou {"id": "...", "ok": false, "erreur": "..."}
Les messages des bibliotheques vont sur la sortie d'erreur, pour ne pas melanger le protocole."""
import json
import math
import re
import struct
import sys
import traceback
import wave

sys.stdout.reconfigure(encoding="utf-8")
sys.stdin.reconfigure(encoding="utf-8")
PROTOCOLE = sys.stdout
sys.stdout = sys.stderr  # toute impression parasite part sur stderr

KOKORO_LANG = {"fr": "f", "pt": "p", "en": "a"}
PHRASES = re.compile(r"(?<=[.!?…])\s+")
_kokoro = {}
_chatterbox = {"modele": None, "echantillon": None}


def ecrire_test(texte, sortie):
    """Son de test (sans dependance) : un bip dont la duree suit la longueur du texte."""
    duree = min(12.0, 0.5 + 0.33 * len(texte.split()))
    sr = 24000
    with wave.open(sortie, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(b"".join(struct.pack("<h", int(8000 * math.sin(2 * math.pi * 240 * i / sr))) for i in range(int(duree * sr))))


def kokoro(texte, langue, voix, vitesse, sortie):
    import numpy as np
    import soundfile as sf
    from kokoro import KPipeline

    code = KOKORO_LANG.get(langue, "f")
    if code not in _kokoro:
        _kokoro[code] = KPipeline(lang_code=code)
    morceaux = []
    for r in _kokoro[code](texte, voice=voix, speed=vitesse, split_pattern=PHRASES.pattern):
        if r.audio is not None:
            morceaux.append(r.audio.numpy())
            morceaux.append(np.zeros(int(24000 * 0.18), dtype=np.float32))
    if not morceaux:
        raise RuntimeError("Aucun son produit.")
    sf.write(sortie, np.concatenate(morceaux), 24000)


def chatterbox(texte, langue, echantillon, sortie):
    import torch
    import torchaudio as ta
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS

    if _chatterbox["modele"] is None:
        device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
        _chatterbox["modele"] = ChatterboxMultilingualTTS.from_pretrained(device=device)
    modele = _chatterbox["modele"]
    # La voix de reference n'est analysee qu'une fois tant que l'echantillon ne change pas.
    if _chatterbox["echantillon"] != echantillon:
        modele.prepare_conditionals(echantillon)
        _chatterbox["echantillon"] = echantillon
    morceaux = []
    for phrase in [p for p in PHRASES.split(texte) if p.strip()]:
        morceaux.append(modele.generate(phrase, language_id=langue))
        morceaux.append(torch.zeros(1, int(modele.sr * 0.2)))
    ta.save(sortie, torch.cat(morceaux, dim=1), modele.sr)


def traiter(d):
    moteur = d.get("moteur")
    texte = d.get("texte", "")
    if moteur == "test":
        ecrire_test(texte, d["sortie"])
    elif moteur == "kokoro":
        kokoro(texte, d.get("langue", "fr"), d.get("voix", "ff_siwis"), float(d.get("vitesse", 1)), d["sortie"])
    elif moteur == "chatterbox":
        chatterbox(texte, d.get("langue", "fr"), d["echantillon"], d["sortie"])
    else:
        raise ValueError("Moteur inconnu : %s" % moteur)


def repondre(obj):
    PROTOCOLE.write(json.dumps(obj, ensure_ascii=False) + "\n")
    PROTOCOLE.flush()


repondre({"pret": True})
for ligne in sys.stdin:
    ligne = ligne.strip()
    if not ligne:
        continue
    demande = {}
    try:
        demande = json.loads(ligne)
        traiter(demande)
        repondre({"id": demande.get("id"), "ok": True})
    except Exception as e:  # une phrase ratee ne doit pas arreter le serveur
        traceback.print_exc()
        repondre({"id": demande.get("id"), "ok": False, "erreur": "%s: %s" % (type(e).__name__, e)})
