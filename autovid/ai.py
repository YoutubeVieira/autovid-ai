"""Couche IA optionnelle : Claude regarde les images de chaque coup et rédige titre, accroche, anatomie, astuce.

Sans clé (ANTHROPIC_API_KEY ou `ant auth login`), le mode combat utilise la classification par squelette seule.
"""
import base64
import json

import cv2

from .anatomy import anchor_for
from .media import FPS
from .pose import iter_frames

MODEL = "claude-opus-5-5"

SCHEMA = {
    "type": "object",
    "properties": {
        "technique": {"type": "string", "description": "nom court en MAJUSCULES, 1 à 3 mots (ex. HIGH KICK, DIRECT DU DROIT)"},
        "accroche": {"type": "string", "description": "accroche virale en MAJUSCULES, 6 mots max"},
        "accroche_2": {"type": "string", "description": "deuxième ligne d'accroche, 4 mots max"},
        "muscles": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"nom": {"type": "string"}, "role": {"type": "string"}},
                "required": ["nom", "role"], "additionalProperties": False,
            },
        },
        "astuce": {"type": "string", "description": "conseil technique en MAJUSCULES, 7 mots max"},
        "placement": {"type": "string", "description": "placement du corps en une phrase (appuis, hanches, garde)"},
        "risque_zone": {"type": "string", "description": "zone à risque de blessure, MAJUSCULES, 3 mots max"},
        "risque_conseil": {"type": "string", "description": "comment l'éviter, 8 mots max, minuscules"},
        "narration": {"type": "string", "description": "voix off de 25 à 40 mots : nom, placement, muscles, risque"},
    },
    "required": ["technique", "accroche", "accroche_2", "muscles", "astuce", "placement", "risque_zone",
                 "risque_conseil", "narration"],
    "additionalProperties": False,
}

PROMPT = """Tu es coach de sports de combat et kinésithérapeute. Voici 3 images (avant / impact / après) d'un coup
extrait d'une vidéo. La détection automatique propose : {nom} ({membre}), angle {angle_nom} {angle:.0f}°.
Corrige le nom si l'image montre autre chose. Donne exactement 3 muscles moteurs (nom court en MAJUSCULES,
rôle en 3 à 4 mots en minuscules), une accroche pour un short TikTok/Reels éducatif, une astuce, le placement,
le principal risque de blessure et comment l'éviter, puis une voix off naturelle, parlée, tutoiement.
Discipline : {discipline}. En capoeira, utilise les noms brésiliens des mouvements (ginga, meia-lua de compasso,
armada, queixada, martelo, bênção, rasteira, aú, esquiva, negativa) sans les traduire.
Reste exact sur l'anatomie, en français."""


def _jpeg(frame):
    ok, buf = cv2.imencode(".jpg", cv2.cvtColor(cv2.resize(frame, (432, 768)), cv2.COLOR_RGB2BGR),
                           [cv2.IMWRITE_JPEG_QUALITY, 82])
    return base64.standard_b64encode(buf.tobytes()).decode()


def _frames_at(video, idxs):
    want = sorted(set(idxs))
    got = {}
    for i, f in enumerate(iter_frames(video, 540, 960)):
        if i in want:
            got[i] = f.copy()
        if i >= want[-1]:
            break
    return [got[i] for i in idxs if i in got]


def enrich(impacts, video, provider="claude", discipline="combat"):
    if provider != "claude" or not impacts:
        return
    import anthropic
    try:
        client = anthropic.Anthropic()
    except anthropic.AnthropicError as e:
        print(f"   IA : client Anthropic indisponible ({e}) ; on garde l'analyse automatique")
        return
    for m in impacts:
        info = m["info"]
        i = m["frame"]
        frames = _frames_at(video, [max(i - 9, 0), i, i + 6])
        content = [{"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": _jpeg(f)}}
                   for f in frames]
        name, _, deg = info["angle"]
        content.append({"type": "text", "text": PROMPT.format(nom=info["nom"], membre=info["membre"],
                                                              angle_nom=name, angle=deg,
                                                              discipline=discipline)})
        try:
            resp = client.beta.messages.create(
                model=MODEL, max_tokens=4000,
                betas=["server-side-fallback-2026-07-01"], fallbacks="default",
                output_config={"effort": "medium", "format": {"type": "json_schema", "schema": SCHEMA}},
                messages=[{"role": "user", "content": content}],
            )
        except anthropic.AuthenticationError:
            print("   IA : pas d'identifiants Anthropic valides, on garde l'analyse automatique")
            return
        except anthropic.APIError as e:
            print(f"   IA : erreur {e.__class__.__name__}, on garde l'analyse automatique pour t={i / FPS:.1f}s")
            continue
        if resp.stop_reason == "refusal":
            continue
        text = next((b.text for b in resp.content if b.type == "text"), None)
        if not text:
            continue
        data = json.loads(text)
        info["nom"] = data["technique"].upper()[:28]
        info["hook"] = [data["accroche"].upper()[:40], data["accroche_2"].upper()[:30]]
        info["tip"] = data["astuce"].upper()[:48]
        info["muscles"] = [(mu["nom"].upper()[:18], mu["role"][:28], anchor_for(mu["nom"], info["side"]))
                           for mu in data["muscles"][:3]]
        info["placement"] = data["placement"]
        info["risque"] = (data["risque_zone"].upper()[:24], data["risque_conseil"][:60])
        info["narration"] = data["narration"]


TRANSLATE_SCHEMA = {
    "type": "object",
    "properties": {lang: {"type": "array", "items": {"type": "string"}} for lang in ("pt", "en")},
    "required": ["pt", "en"],
    "additionalProperties": False,
}


def translate(texts):
    """Traduit des répliques françaises en portugais du Brésil et en anglais (mêmes indices).

    Renvoie {"pt": [...], "en": [...]} ou None sans identifiants Anthropic.
    """
    import anthropic
    try:
        client = anthropic.Anthropic()
    except anthropic.AnthropicError:
        return None
    prompt = ("Traduis chaque réplique de cette voix off de sport de combat en portugais du Brésil (pt) et en anglais "
              "(en). Garde le même nombre d'éléments, dans le même ordre, ton parlé et court pour des sous-titres. "
              "Ne traduis pas les noms de mouvements de capoeira (ginga, rasteira, aú, meia-lua…).\n\n"
              + json.dumps(texts, ensure_ascii=False))
    try:
        resp = client.beta.messages.create(
            model=MODEL, max_tokens=8000, betas=["server-side-fallback-2026-07-01"], fallbacks="default",
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": TRANSLATE_SCHEMA}},
            messages=[{"role": "user", "content": prompt}])
    except anthropic.APIError as e:
        print(f"   traduction : erreur {e.__class__.__name__}, sous-titres en français seulement")
        return None
    text = next((b.text for b in resp.content if b.type == "text"), None)
    if resp.stop_reason == "refusal" or not text:
        return None
    data = json.loads(text)
    if any(len(data[k]) != len(texts) for k in ("pt", "en")):
        return None
    return data
