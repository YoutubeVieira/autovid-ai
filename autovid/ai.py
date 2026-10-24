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
        except (anthropic.AuthenticationError, TypeError):  # TypeError : aucun identifiant configuré
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
    except (anthropic.APIError, TypeError) as e:     # TypeError : aucun identifiant configuré
        print(f"   traduction : indisponible ({e.__class__.__name__}), sous-titres en français seulement")
        return None
    text = next((b.text for b in resp.content if b.type == "text"), None)
    if resp.stop_reason == "refusal" or not text:
        return None
    data = json.loads(text)
    if any(len(data[k]) != len(texts) for k in ("pt", "en")):
        return None
    return data


FUN_SCHEMA = {
    "type": "object",
    "properties": {
        "lignes": {"type": "array", "description": "3 textes à l'écran : début, ralenti, fin",
                   "items": {"type": "object", "properties": {"l1": {"type": "string"}, "l2": {"type": "string"}},
                             "required": ["l1", "l2"], "additionalProperties": False}},
        "genere_par_ia": {"type": "boolean", "description": "la vidéo semble générée par IA"},
    },
    "required": ["lignes", "genere_par_ia"],
    "additionalProperties": False,
}

FUN_PROMPT = """Voici 3 images d'un clip court (début, moment fort, fin) qu'on monte en short TikTok/Reels drôle.
Écris 3 textes à l'écran en français, chacun sur 2 lignes en MAJUSCULES (ligne 1 : 4 mots max, ligne 2 : 3 mots
max) : un pour le début, un pendant le ralenti du moment fort, un pour la fin. Ton parlé, comme un pote qui
commente. Décris seulement ce qu'on voit. Pas de « secret », pas de question suivie de sa réponse, pas de tiret
long, pas d'emoji. Dis aussi si la vidéo semble générée par IA."""


def fun_texts(video, idxs):
    """Textes d'écran du mode fun écrits par Claude à partir de 3 images. None sans identifiants Anthropic."""
    import anthropic
    try:
        client = anthropic.Anthropic()
    except anthropic.AnthropicError:
        return None
    content = [{"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": _jpeg(f)}}
               for f in _frames_at(video, idxs)]
    content.append({"type": "text", "text": FUN_PROMPT})
    try:
        resp = client.beta.messages.create(
            model=MODEL, max_tokens=2000, betas=["server-side-fallback-2026-07-01"], fallbacks="default",
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": FUN_SCHEMA}},
            messages=[{"role": "user", "content": content}])
    except (anthropic.APIError, TypeError) as e:     # TypeError : aucun identifiant configuré
        print(f"   IA : textes indisponibles ({e.__class__.__name__}), textes par défaut")
        return None
    text = next((b.text for b in resp.content if b.type == "text"), None)
    if resp.stop_reason == "refusal" or not text:
        return None
    data = json.loads(text)
    lines = [(x["l1"].upper()[:28], x["l2"].upper()[:24]) for x in data["lignes"][:3]]
    return (lines + [("", "")] * 3)[:3], bool(data["genere_par_ia"])


# --------------------------------------------------------------------------- documentaire

DOC_SCHEMA = {
    "type": "object",
    "properties": {
        "titre": {"type": "string", "description": "titre YouTube factuel, 70 caractères max"},
        "accroche": {"type": "string", "description": "voix off des 15 premières secondes : le fait le plus fort, "
                                                       "une vraie question, pas de « secret »"},
        "chapitres": {"type": "array", "items": {"type": "object", "properties": {
            "titre": {"type": "string"},
            "plans": {"type": "array", "items": {"type": "object", "properties": {
                "texte": {"type": "string", "description": "voix off de ce plan, 1 à 3 phrases parlées"},
                "visuel": {"type": "string", "enum": ["archive", "film", "date", "lieu", "citation", "ambiance"]},
                "requete": {"type": "string", "description": "recherche d'archive EN ANGLAIS, précise : lieu AVEC "
                                                             "son pays, époque, sujet (ex. « Paris France 1916 street », "
                                                             "« Sao Paulo Brazil 1998 »), ou nom d'une personne publique ; "
                                                             "jamais de victime ni de corps"},
                "legende": {"type": "string", "description": "texte court affiché (date, lieu, citation exacte)"},
            }, "required": ["texte", "visuel", "requete", "legende"], "additionalProperties": False}},
        }, "required": ["titre", "plans"], "additionalProperties": False}},
        "sources": {"type": "array", "items": {"type": "object", "properties": {
            "titre": {"type": "string"}, "url": {"type": "string"}},
            "required": ["titre", "url"], "additionalProperties": False}},
    },
    "required": ["titre", "accroche", "chapitres", "sources"],
    "additionalProperties": False,
}

DOC_RULES = """Règles (non négociables) :
- Seulement des faits établis et sourcés : condamnations définitives, archives judiciaires, presse de référence.
  Pas de spéculation présentée comme un fait, pas de nom de suspect jamais condamné.
- Angle enquête et victimes : comment l'affaire a été résolue, les erreurs, les leçons. Jamais glorifier l'auteur,
  pas de détails sanglants ni de description des corps. Les victimes sont nommées avec respect ou pas du tout.
- Ton documentaire calme et précis (National Geographic), phrases courtes, à l'oral, en français. Pas de « secret »,
  pas de question suivie de sa réponse, pas de tiret long.
- Mineurs (victimes, témoins, auteurs) jamais identifiés, comme l'exige l'ECA au Brésil ; pas de nom ni de visage.
- Visuels : « archive » (photo d'archive libre à chercher), « film » (film d'archive), « date », « lieu »,
  « citation » (phrase exacte tirée d'une source), « ambiance » (plan neutre : route, forêt, ville la nuit)."""


def doc_plan(sujet, minutes=8, langue="fr"):
    """Recherche web (Claude + web_search) puis plan structuré du documentaire. None sans identifiants."""
    import anthropic
    try:
        client = anthropic.Anthropic()
    except anthropic.AnthropicError:
        return None
    public = {"pt": "Public : brésilien. Écris le script final en portugais du Brésil, naturel et parlé (pas de portugais "
                    "du Portugal), avec les repères brésiliens (villes, institutions, presse brésilienne quand c'est une "
                    "affaire brésilienne).", "fr": "Public : francophone. Script en français."}.get(langue, "")
    ask = (f"Prépare un documentaire YouTube d'environ {minutes} minutes sur : {sujet}.\n{public}\n{DOC_RULES}\n"
           "Cherche d'abord les faits sur le web (sources fiables), puis écris des notes détaillées : chronologie, "
           "lieux, citations exactes avec leur source, et la liste des URL utilisées.")
    messages = [{"role": "user", "content": ask}]
    try:
        for _ in range(6):                        # la recherche web peut demander plusieurs tours (pause_turn)
            with client.beta.messages.stream(
                    model=MODEL, max_tokens=64000, betas=["server-side-fallback-2026-07-01"], fallbacks="default",
                    output_config={"effort": "high"}, messages=messages,
                    tools=[{"type": "web_search_20260209", "name": "web_search", "max_uses": 15}]) as stream:
                resp = stream.get_final_message()
            messages.append({"role": "assistant", "content": resp.content})
            if resp.stop_reason != "pause_turn":
                break
        if resp.stop_reason == "refusal":
            print("   IA : demande refusée pour ce sujet")
            return None
        notes = "\n".join(b.text for b in resp.content if b.type == "text")
        with client.beta.messages.stream(
                model=MODEL, max_tokens=64000, betas=["server-side-fallback-2026-07-01"], fallbacks="default",
                output_config={"effort": "high", "format": {"type": "json_schema", "schema": DOC_SCHEMA}},
                messages=[{"role": "user", "content":
                           f"{DOC_RULES}\n\nÀ partir de ces notes de recherche, écris le plan complet du documentaire "
                           f"(environ {minutes} minutes de voix off, soit {minutes * 140} mots ; 4 à 7 chapitres ; "
                           f"un plan toutes les 6 à 12 secondes). {public} Les champs « requete » restent en anglais (recherche "
                           f"d'archives).\n\nNOTES :\n{notes}"}]) as stream:
            plan = stream.get_final_message()
    except (anthropic.AuthenticationError, TypeError):
        print("   IA : pas d'identifiants Anthropic valides")
        return None
    except anthropic.APIError as e:
        print(f"   IA : erreur {e.__class__.__name__}")
        return None
    text = next((b.text for b in plan.content if b.type == "text"), None)
    if plan.stop_reason == "refusal" or not text:
        return None
    return json.loads(text)


def has_credentials():
    """Vrai si un identifiant Anthropic est configuré (clé ou jeton), sans faire d'appel."""
    import anthropic
    try:
        c = anthropic.Anthropic()
    except anthropic.AnthropicError:
        return False
    return bool(getattr(c, "api_key", None) or getattr(c, "auth_token", None))


def image_pertinente(requete, path):
    """Claude regarde l'image d'archive : montre-t-elle vraiment « requete » (lieu, époque, sujet) ?
    Refuse aussi les images choquantes. En cas d'erreur, on garde l'image (le filtre par mots-clés a déjà agi)."""
    import anthropic
    from PIL import Image
    try:
        im = Image.open(path).convert("RGB")
        im.thumbnail((768, 768))
        import io
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=80)
        data = base64.standard_b64encode(buf.getvalue()).decode()
        resp = anthropic.Anthropic().messages.create(
            model=MODEL, max_tokens=300, output_config={"effort": "low", "format": {"type": "json_schema", "schema": {
                "type": "object", "properties": {"pertinente": {"type": "boolean"}, "choquante": {"type": "boolean"}},
                "required": ["pertinente", "choquante"], "additionalProperties": False}}},
            messages=[{"role": "user", "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": data}},
                {"type": "text", "text": f"Image d'archive pour illustrer : « {requete} ». Est-ce qu'elle montre bien ce "
                                         "sujet (lieu, époque, personne, objet) ? Est-elle choquante (corps, sang, "
                                         "violence) ?"}]}])
        text = next((b.text for b in resp.content if b.type == "text"), None)
        if resp.stop_reason == "refusal" or not text:
            return False
        r = json.loads(text)
        return r["pertinente"] and not r["choquante"]
    except Exception:
        return True
