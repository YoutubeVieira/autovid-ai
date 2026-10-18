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
    },
    "required": ["technique", "accroche", "accroche_2", "muscles", "astuce"],
    "additionalProperties": False,
}

PROMPT = """Tu es coach de sports de combat et kinésithérapeute. Voici 3 images (avant / impact / après) d'un coup
extrait d'une vidéo. La détection automatique propose : {nom} ({membre}), angle {angle_nom} {angle:.0f}°.
Corrige le nom si l'image montre autre chose. Donne exactement 3 muscles moteurs (nom court en MAJUSCULES,
rôle en 3 à 4 mots en minuscules), une accroche pour un short TikTok/Reels éducatif, et une astuce.
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


def enrich(impacts, video, provider="claude"):
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
                                                              angle_nom=name, angle=deg)})
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
