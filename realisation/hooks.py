"""Générateur de hooks (0-3 s) pour la série: formules testées + variantes A/B + note sur 10.

    python3 hooks.py --regle "il faut un ami pour entrer" --n 2 --manque 13 --prenom Robin --metier "T-rex singe" --k 10 [--json out.json]
Un hook = texte écrit (≤ 6-7 mots, affiché dès 0,15 s) + phrase dite + premier plan + mouvement + son. Il doit être TENU par la suite de l'épisode."""
import argparse
import json
import re

FORMULES = [
    # nom, texte écran, phrase dite, plan, camera, son, pourquoi
    ("lieu_regle", "Dans cette ville, {regle}", "Dans cette ville, {regle}.", "large", "push_in_lent", "whoosh_fast", "format n°1 des vidéos FR qui percent (veille 11/2026)"),
    ("pov", "POV : tu arrives dans notre ville", "Tu viens d'arriver dans une ville où tout est possible.", "gros_plan", "punch_in", "pop", "te met dans l'image dès la 1re seconde"),
    ("chiffre", "{n} habitants. Il en manque {manque}.", "{n} habitants. Il en manque {manque}.", "large", "pull_out_lent", "tick", "chiffre précis + manque = suspense mesurable"),
    ("question", "Et si cette ville existait vraiment ?", "Et si cette ville existait vraiment ?", "insert", "push_in_lent", "riser", "boucle ouverte: la réponse est dans la vidéo"),
    ("defi", "Tague {k} amis. Ils déménagent ici.", "Tague {k} amis, et ils déménagent chez nous.", "moyen", "orbite_legere", "pop_double", "appel à l'action dès le départ (épisode 0)"),
    ("avant_apres", "Avant : vide. Maintenant : {n} habitants.", "Hier, la ville était vide. Aujourd'hui, {n} habitants.", "large", "tilt_up", "sparkle", "contraste visible avant/après"),
    ("ciblage", "{prenom}, ton habitant est arrivé", "{prenom}, regarde : ton habitant est arrivé.", "gros_plan", "punch_in", "ding", "interpelle un commentateur par son prénom -> commentaires et partages"),
    ("anormal", "Cette ville n'a aucune règle", "Dans cette ville, aucune règle. Sauf une.", "large", "push_in_rapide", "boom", "détail qui cloche + promesse d'une règle à découvrir"),
]


def note(texte, parle):
    mots = len(re.findall(r"\w+", texte))
    s = 0
    s += 3 if mots <= 6 else 2 if mots <= 8 else 0 if mots <= 10 else -2           # lisible en 1 s
    s += 2 if re.search(r"\d", texte) or re.search(r"[A-Z][a-zé]+,", texte) else 0   # précis: chiffre ou prénom
    s += 2 if re.search(r"ville|monde", texte, re.I) else 0   # rappel de la série
    s += 2 if re.search(r"\?|manque|aucune|vide|POV|Tague", texte) else 0   # tension / ouverture / action
    s += 1 if len(parle.split()) <= 12 else 0                # phrase dite courte (< 3 s)
    s += 2 if texte.lower().startswith("dans cette ville") else 0   # format n°1 de la veille
    return min(s, 10)


def generer(a):
    ctx = {"regle": a.regle or "tout est possible", "n": a.n, "manque": a.manque, "prenom": a.prenom or "Toi", "k": a.k}
    out = []
    for nom, ecran, parle, plan, cam, son, pourquoi in FORMULES:
        if nom == "ciblage" and not a.prenom:
            continue
        if nom in ("chiffre", "avant_apres") and not a.n:
            continue
        t, p = ecran.format(**ctx), parle.format(**ctx)
        out.append({"formule": nom, "texte_ecran": t, "phrase_dite": p, "plan": plan, "camera": cam, "son": son, "note": note(t, p), "pourquoi": pourquoi})
    return sorted(out, key=lambda x: -x["note"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--regle")
    ap.add_argument("--n", type=int, default=0)
    ap.add_argument("--manque", type=int, default=0)
    ap.add_argument("--prenom")
    ap.add_argument("--metier")
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--json")
    a = ap.parse_args()
    h = generer(a)
    for x in h:
        print(f"{x['note']:>2}/10 [{x['formule']:11}] « {x['texte_ecran']} » | dit: {x['phrase_dite']} | {x['plan']}/{x['camera']}/{x['son']}")
    if a.json:
        json.dump(h, open(a.json, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
