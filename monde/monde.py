"""Le monde se peuple: registre des habitants + plan d'episode (25 a 30 s) a partir des commentaires des spectateurs.

    python3 monde.py ajouter --episode 2 --titre "Les premiers habitants" --commentaires commentaires.txt
    python3 monde.py etat

Lignes acceptees (une par commentaire):  « Léa, boulangère »  « Karim - pompier »  « Moi c'est Zoé, je veux être astronaute »
Vie privee/securite: on ne garde que le PRENOM (pas de pseudo, lien, e-mail ni numero), les insultes sont ecartees, aucun genre n'est devine a partir d'un prenom.
Aucun nom n'est invente: seuls les commentaires fournis peuplent le monde."""
import argparse
import json
import os
import random
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "etat.json")
METIERS = {k: v for k, v in json.load(open(os.path.join(HERE, "metiers.json"), encoding="utf-8")).items() if not k.startswith("_")}
BLOCK = {"con", "connard", "connasse", "pute", "salope", "merde", "nazi", "hitler", "viol", "pedo", "nique", "fdp", "ntm", "tg"}
FACES = ["smile", "happy", "laugh", "love", "tongue", "wink", "surprise"]
SPEECH_WPS = 1.85                      # mots par seconde mesurés sur la voix (vitesse 1,05; prénoms et métiers = débit plus lent)
TARGET = (25.0, 30.0)
OUTRO = 2.2
MOOD_CYCLE = ["aventure", "joyeux", "calme", "melancolique"]      # le fond change a chaque episode (jamais deux fois de suite le meme)
AMBIANCE_CYCLE = ["oiseaux", "foule", "vent", "riviere", "grillons", "pluie"]
MILESTONES = [(15, "les 15 premiers conseillers"), (100, "l'élection du maire")]


def strip(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s.lower()) if not unicodedata.combining(c))


def metier_key(raw):
    w = strip(raw)
    for k, v in METIERS.items():
        if any(re.search(rf"\b{re.escape(a)}\b", w) for a in v["alias"]):
            return k
    return "habitant"


def safe(text):
    t = strip(text)
    if re.search(r"https?://|www\.|@|\d{6,}", t):
        return False
    return not (set(re.findall(r"[a-z]+", t)) & BLOCK)


def parse_line(line):
    """-> (prenom, metier_brut, ok, motif)."""
    raw = line.strip()
    if not raw or raw.startswith("#"):
        return None
    if not safe(raw):
        return {"ok": False, "motif": "contenu écarté (lien, contact ou terme interdit)", "ligne": raw[:40]}
    m = re.search(r"(?:c'est|m'appelle|je suis)\s+([A-Za-zÀ-ÿ'-]{2,14})", raw, re.I)
    if m:
        name = m.group(1)
        rest = raw[m.end():]
    else:
        parts = re.split(r"\s*[,;:–—-]\s*", raw, maxsplit=1)
        name, rest = parts[0], (parts[1] if len(parts) > 1 else "")
    name = re.sub(r"[^A-Za-zÀ-ÿ'-]", "", name.split()[0] if name.split() else "")
    if not (2 <= len(name) <= 14):
        return {"ok": False, "motif": "prénom illisible", "ligne": raw[:40]}
    mw = re.search(r"(?:veux être|veux devenir|voudrais être|serai|être|devenir)\s+(.+)$", rest, re.I)
    metier = (mw.group(1) if mw else rest).strip(" .!?")
    return {"ok": True, "prenom": name[0].upper() + name[1:], "metier_brut": metier or "habitant"}


def look_for(prenom, metier, seed_extra=0):
    cfg = METIERS[metier]
    rnd = random.Random(sum(map(ord, prenom)) * 31 + seed_extra)
    return {"metier": metier, "shirt": cfg["shirt"], "pants": cfg["pants"], "accessory": cfg.get("accessory"),
            "hat": cfg.get("hat"), "hat_color": cfg.get("hat_color"), "hair": cfg.get("hair") or rnd.choice(["cap", "spiky", "bun", "long", "cap"]),
            "skin": rnd.randrange(5), "hair_color": rnd.randrange(5), "face": rnd.choice(FACES)}


def load():
    if os.path.exists(STATE):
        return json.load(open(STATE, encoding="utf-8"))
    return {"monde": "Le monde se peuple", "episodes": [{"numero": 1, "titre": "La fin des dinosaures", "arrivees": []}], "habitants": []}


def save(st):
    json.dump(st, open(STATE, "w", encoding="utf-8"), indent=2, ensure_ascii=False)


def say(text):
    """Un nom de metier au pluriel/feminin reste tel qu'ecrit par le spectateur."""
    return text


def plan_script(titre, num, new, total_before, total_after):
    """Phrases de voix off et habitants mis en avant: on en ajoute tant que la duree estimee (carton de fin compris) reste <= 29,5 s."""
    def build(chosen, missing=True):
        lines = [f"Épisode {num} : {titre}.", "Un nouvel habitant arrive." if len(new) == 1 else f"{len(new)} nouveaux habitants arrivent."]
        lines += [f"{c['prenom']}, {c['metier_dit']}." for c in chosen]
        rest = len(new) - len(chosen)
        if rest > 0:
            lines.append(f"Et {rest} autre{'s' if rest > 1 else ''} encore.")
        lines.append(f"Le monde compte maintenant {total_after} habitant{'s' if total_after > 1 else ''}.")
        nxt = next(((m, t) for m, t in MILESTONES if total_after < m), None)
        if nxt and missing:
            lines.append(f"Il en manque {nxt[0] - total_after} pour {nxt[1]}.")
        crossed = [t for m, t in MILESTONES if total_before < m <= total_after]
        if crossed:
            lines.append("Palier atteint : " + crossed[0] + " !")
        lines.append("Commente ton prénom et ton métier : le prochain, c'est toi.")
        return lines
    seen, order = set(), []
    for c in new:                                          # un habitant par metier d'abord, puis les autres
        if c["look"]["metier"] not in seen:
            seen.add(c["look"]["metier"])
            order.append(c)
    order += [c for c in new if c not in order]
    chosen, missing = [], True
    for c in order:
        if len(chosen) >= 5:
            break
        if estimate(build(chosen + [c], missing)) > TARGET[1] - 0.5:
            if missing and estimate(build(chosen + [c], False)) <= TARGET[1] - 0.5:
                missing = False                      # on sacrifie « il en manque N » pour garder un habitant a l'ecran
            else:
                break
        chosen.append(c)
    return build(chosen, missing), chosen


def estimate(lines):
    return sum(len(l.split()) for l in lines) / SPEECH_WPS + 0.22 * len(lines) + 0.4 + OUTRO


def ajouter(args):
    st = load()
    txt = open(args.commentaires, encoding="utf-8").read().splitlines()
    exist = {strip(h["prenom"]) + "|" + h["look"]["metier"] for h in st["habitants"]}
    new, rejected = [], []
    for ln in txt:
        r = parse_line(ln)
        if r is None:
            continue
        if not r["ok"]:
            rejected.append(r)
            continue
        key = metier_key(r["metier_brut"])
        sig = strip(r["prenom"]) + "|" + key
        if sig in exist:
            rejected.append({"ligne": ln[:40], "motif": "déjà habitant"})
            continue
        exist.add(sig)
        hid = len(st["habitants"]) + len(new) + 1
        new.append({"id": hid, "prenom": r["prenom"], "metier_dit": r["metier_brut"], "look": look_for(r["prenom"], key, hid), "episode": args.episode})
    if args.max and len(new) > args.max:
        rejected += [{"ligne": c["prenom"], "motif": "au-delà du maximum de l'épisode (reporté)"} for c in new[args.max:]]
        new = new[:args.max]
    before = len(st["habitants"])
    lines, featured = plan_script(args.titre, args.episode, new, before, before + len(new))
    dur = estimate(lines)
    sys.path.insert(0, os.path.join(HERE, "..", "packs", "sfx"))
    import music_pick
    rec = not args.simuler
    musique = [dict(music_pick.pick(MOOD_CYCLE[args.episode % len(MOOD_CYCLE)], args.episode, record=rec), gain=0.3, role="fond"),
               dict(music_pick.pick(AMBIANCE_CYCLE[args.episode % len(AMBIANCE_CYCLE)], args.episode, kind="ambiance", record=rec), gain=0.22, role="ambiance")]
    if any(before < mm <= before + len(new) for mm, _ in MILESTONES):
        musique.append(dict(music_pick.pick("victoire", args.episode, record=rec), gain=0.35, role="palier"))
    out = os.path.join(HERE, "episodes", f"ep{args.episode:02d}")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "script.txt"), "w", encoding="utf-8") as f:
        f.write(f"# Épisode {args.episode} - {args.titre} (≈ {dur:.0f} s). <début | +pause> | texte\n")
        for i, l in enumerate(lines):
            f.write(("0.15" if i == 0 else "+0.22") + f" | {l}\n")
    spec = {"episode": args.episode, "titre": args.titre, "nouveaux": new, "mis_en_avant": [c["id"] for c in featured],
            "anciens": st["habitants"], "musique": musique, "total_avant": before, "total_apres": before + len(new), "duree_estimee_s": round(dur, 1),
            "ecartes": rejected}
    json.dump(spec, open(os.path.join(out, "episode.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    if not args.simuler:
        st["habitants"] += new
        st["episodes"] = [e for e in st["episodes"] if e["numero"] != args.episode] + [
            {"numero": args.episode, "titre": args.titre, "arrivees": [h["id"] for h in new]}]
        save(st)
    print(f"Épisode {args.episode} « {args.titre} » : {len(new)} arrivées (total {before + len(new)}), durée estimée {dur:.0f} s "
          f"{'(HORS 25-30 s: réduire --max)' if not TARGET[0] - 2 <= dur <= TARGET[1] + 1 else ''}")
    for r in rejected:
        print("  écarté:", r.get("ligne"), "-", r["motif"])
    print("  fichiers:", out)
    return spec


def etat(_):
    st = load()
    print(f"{st['monde']} : {len(st['habitants'])} habitants, {len(st['episodes'])} épisode(s)")
    par = {}
    for h in st["habitants"]:
        par[h["look"]["metier"]] = par.get(h["look"]["metier"], 0) + 1
    for k, n in sorted(par.items(), key=lambda x: -x[1]):
        print(f"  {k:12} {n}")
    nxt = next(((m, t) for m, t in MILESTONES if len(st["habitants"]) < m), None)
    if nxt:
        print(f"Prochain palier : {nxt[0]} habitants ({nxt[1]}), il en manque {nxt[0] - len(st['habitants'])}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    pa = sub.add_parser("ajouter", help="ajoute les habitants d'un épisode et génère script + plan")
    pa.add_argument("--episode", type=int, required=True)
    pa.add_argument("--titre", required=True)
    pa.add_argument("--commentaires", required=True)
    pa.add_argument("--max", type=int, default=30, help="habitants max par épisode")
    pa.add_argument("--simuler", action="store_true", help="ne pas enregistrer dans etat.json")
    pa.set_defaults(fn=ajouter)
    pe = sub.add_parser("etat", help="résumé du monde")
    pe.set_defaults(fn=etat)
    a = p.parse_args()
    a.fn(a)
