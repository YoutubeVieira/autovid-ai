"""Fichier projet modifiable (projet.json) : ce que la plateforme d'édition montre et renvoie.

Un montage écrit son projet à côté de la vidéo (`<sortie>.projet.json`). On le modifie (plateforme, à la main)
puis on relance : `python -m autovid projet fichier.projet.json -o nouvelle.mp4`.
"""
import json
import re
from pathlib import Path

FX = ("couleur", "fleche", "rond", "etoile", "zoom", "risque")
SONS = ("auto", "corps", "sac", "air", "aucun")


def hex_rgb(h):
    h = str(h).lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) if re.fullmatch(r"[0-9a-fA-F]{6}", h) else None


def rgb_hex(c):
    return "#%02x%02x%02x" % tuple(int(x) for x in c)


def plain(t):
    return re.sub(r"\[/?pt\]", "", t or "")


def load(path_or_dict):
    if path_or_dict is None or isinstance(path_or_dict, dict):
        return path_or_dict
    return json.loads(Path(path_or_dict).read_text(encoding="utf-8"))


def save(data, path):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return str(path)


# --------------------------------------------------------------------------- mode combat

def combat_export(src, impacts, segs, settings, cle, all_impacts=None):
    """Projet d'un montage combat : réglages, accroche, une entrée par analyse (y compris celles désactivées,
    pour pouvoir les remettre), fin."""
    by_id = {sg["id"]: plain(sg["fr"]) for sg in segs}
    for k, m in enumerate(impacts):
        m["_voix"] = by_id.get(k, "")
    top = max(range(len(impacts)), key=lambda j: impacts[j]["score"]) if impacts else None
    every = sorted(all_impacts or impacts, key=lambda m: m["frame"])
    return {
        "mode": "combat",
        "source": str(Path(src).resolve()),
        "reglages": settings,
        "accroche": {"l1": impacts[top]["info"]["hook"][0] if impacts else "",
                     "l2": impacts[top]["info"]["hook"][1] if impacts else "", "voix": by_id.get("hook", "")},
        "analyses": [{
            "id": int(m["frame"]), "t": round(m["frame"] / 30, 2), "actif": m.get("actif", True),
            "titre": m["info"]["nom"], "ligne2": m["info"].get("cle") or cle(m["info"]),
            "voix": m.get("_voix", ""), "risque": (m["info"].get("risque") or ["", ""])[0],
            "effets": {f: m["info"].get("fx", {}).get(f, True) for f in FX},
            "son": m.get("son_choisi", "auto"), "rotation": bool(m.get("contact", {}).get("rotation")),
            "detecte": {"kind": m["info"]["kind"], "membre": m["info"]["membre"],
                        "contact": m.get("contact", {}).get("cible")},
        } for m in every],
        "fin": {"voix": by_id.get("outro", "")},
        "notes": "",
    }


def combat_apply(projet, impacts):
    """Applique les choix du projet aux analyses détectées (repérées par leur image). Renvoie la liste gardée
    et un dict de textes de voix {id_segment: texte} à substituer au script automatique."""
    if not projet:
        return impacts, {}, impacts
    edits = {int(a["id"]): a for a in projet.get("analyses", [])}
    kept = []
    for m in impacts:
        a = edits.get(int(m["frame"]))
        if a is None:
            kept.append(m)
            continue
        if not a.get("actif", True):
            m["actif"] = False
            m["_voix"] = a.get("voix", "")
        info = m["info"]
        if a.get("titre"):
            info["nom"] = a["titre"].upper()[:28]
        if a.get("ligne2"):
            info["cle"] = a["ligne2"].upper()[:30]
        if "risque" in a:
            info["risque"] = (a["risque"].upper()[:28], (info.get("risque") or ["", ""])[1]) if a["risque"] else None
        info["fx"] = {f: bool(a.get("effets", {}).get(f, True)) for f in FX}
        son = a.get("son", "auto")
        if son in SONS and son != "auto":
            m["son_choisi"] = son
            m["contact"] = {"cible": son, "rotation": bool(a.get("rotation"))}
        elif "rotation" in a and "contact" in m:
            m["contact"]["rotation"] = bool(a["rotation"])
        if not a.get("actif", True):
            continue
        if a.get("voix") is not None:
            m["voix_projet"] = a["voix"]
        kept.append(m)
    acc = projet.get("accroche") or {}
    if kept and (acc.get("l1") or acc.get("l2")):
        top = max(range(len(kept)), key=lambda j: kept[j]["score"])
        kept[top]["info"]["hook"] = (acc.get("l1", "").upper()[:40], acc.get("l2", "").upper()[:30])
    voices = {k: m.pop("voix_projet") for k, m in enumerate(kept) if "voix_projet" in m}
    if acc.get("voix"):
        voices["hook"] = acc["voix"]
    if (projet.get("fin") or {}).get("voix"):
        voices["outro"] = projet["fin"]["voix"]
    return kept, voices, impacts


def apply_voices(segs, voices):
    from .anatomy import tag_pt
    for sg in segs:
        if sg["id"] in voices:
            sg["fr"] = tag_pt(plain(voices[sg["id"]]).strip())
    return segs
