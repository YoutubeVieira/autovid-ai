#!/usr/bin/env python3
"""Machine à Reels : file de la semaine (7 vidéos), validation humaine, programmation, métriques.

Le seul travail de l'utilisateur est de relire et d'approuver. Rien n'est programmé ni publié sans
statut « approuve », donné par l'utilisateur.

  python3 outils/machine.py semaine [--debut 2026-11-30] [--n 7] [--heure 18:00]
  python3 outils/machine.py statut
  python3 outils/machine.py maj v3 titre="…" fichier=remotion/out/v3.mp4 statut=a_approuver
  python3 outils/machine.py approuver v3          (à la demande explicite de l'utilisateur)
  python3 outils/machine.py refuser v3 --raison "hook trop lent"
  python3 outils/machine.py programmer            → publications.csv + calendrier.ics
  python3 outils/machine.py publie v3 --plateforme instagram --url https://…
  python3 outils/machine.py metriques export.csv --plateforme youtube
  python3 outils/machine.py rapport               → rapport.md (meilleures vidéos, variantes à créer)

Données : machine/semaines/<AAAA-Sss>/semaine.json (une semaine = un dossier).
"""
import argparse
import csv
import datetime as dt
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "machine" / "semaines"
STATUTS = ["idee", "script", "monte", "a_approuver", "approuve", "programme", "publie", "refuse"]
PLATEFORMES = ["instagram", "tiktok", "youtube"]

# Noms de colonnes des exports (YouTube Studio, Instagram, TikTok, en anglais / français / portugais).
COLONNES = {
    "titre": ["video title", "titre de la vidéo", "título do vídeo", "title", "titre", "caption", "légende", "description"],
    "url": ["url", "permalink", "lien", "link", "video link"],
    "id": ["content", "contenu", "video id", "id", "post id"],
    "vues": ["views", "vues", "visualizações", "plays", "video views", "reach", "impressions"],
    "likes": ["likes", "j'aime", "curtidas"],
    "commentaires": ["comments", "commentaires", "comentários"],
    "partages": ["shares", "partages", "compartilhamentos"],
    "enregistrements": ["saves", "enregistrements", "salvamentos"],
    "abonnes": ["subscribers", "abonnés", "nouveaux abonnés", "inscritos", "novos seguidores", "follows", "new followers", "seguidores"],
    "duree_moy": ["average view duration", "durée moyenne de visionnage", "duração média da visualização", "average watch time"],
    "retention": ["average percentage viewed (%)", "pourcentage moyen regardé (%)", "porcentagem média visualizada (%)",
                  "watched full video (%)", "retention"],
}


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", s).strip()


def num(v):
    """'12 345', '1,2 k', '3.4K', '45%' → float ; vide → 0."""
    s = str(v or "").strip().lower().replace("\u202f", "").replace("\xa0", "").replace(" ", "").replace("%", "")
    mult = 1
    if s.endswith("k"):
        mult, s = 1_000, s[:-1]
    elif s.endswith("m"):
        mult, s = 1_000_000, s[:-1]
    if "," in s and "." not in s and not re.fullmatch(r"\d{1,3}(,\d{3})+", s):
        s = s.replace(",", ".")  # virgule décimale : « 1,2 » ; « 15,200 » reste un séparateur de milliers
    s = s.replace(",", "")
    try:
        return float(s) * mult
    except ValueError:
        if ":" in s:  # durée h:mm:ss ou mm:ss
            t = 0.0
            for p in s.split(":"):
                t = t * 60 + float(p or 0)
            return t
        return 0.0


# ---------------------------------------------------------------- stockage

def dossier(semaine=None):
    if semaine:
        return BASE / semaine
    if not BASE.exists() or not any(BASE.iterdir()):
        sys.exit("Aucune semaine : lancez « machine.py semaine ».")
    return sorted(p for p in BASE.iterdir() if p.is_dir())[-1]


def charger(semaine=None):
    d = dossier(semaine)
    return d, json.loads((d / "semaine.json").read_text(encoding="utf-8"))


def sauver(d, data):
    (d / "semaine.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def video(data, vid):
    for v in data["videos"]:
        if v["id"] == vid:
            return v
    sys.exit(f"Vidéo inconnue : {vid} (ids : {', '.join(v['id'] for v in data['videos'])})")


# ---------------------------------------------------------------- commandes

def cmd_semaine(a):
    debut = dt.date.fromisoformat(a.debut) if a.debut else dt.date.today() + dt.timedelta(days=(7 - dt.date.today().weekday()) % 7 or 7)
    iso = debut.isocalendar()
    nom = f"{iso[0]}-S{iso[1]:02d}"
    d = BASE / nom
    if (d / "semaine.json").exists():
        sys.exit(f"La semaine {nom} existe déjà : {d}")
    d.mkdir(parents=True)
    data = {
        "semaine": nom, "debut": debut.isoformat(), "heure": a.heure, "fuseau": a.fuseau,
        "plateformes": a.plateformes.split(","),
        "videos": [{"id": f"v{i}", "statut": "idee", "titre": "", "sujet": "", "hook": "", "variante_de": None,
                    "script": "", "fichier": "", "legende": "", "hashtags": [], "jour": None,
                    "publications": {}, "metriques": {}, "notes": []} for i in range(1, a.n + 1)],
    }
    sauver(d, data)
    print(f"✔ {d / 'semaine.json'} : {a.n} emplacements, du {debut} à {a.heure}")


def cmd_statut(a):
    d, data = charger(a.semaine)
    print(f'Semaine {data["semaine"]} (début {data["debut"]}, {data["heure"]} {data["fuseau"]}) — {d}')
    print(f'{"id":<4} {"statut":<12} {"jour":<11} {"titre":<44} fichier')
    for v in data["videos"]:
        f = v["fichier"]
        ok = "" if not f else ("✔" if (ROOT / f).exists() else "✕ absent")
        print(f'{v["id"]:<4} {v["statut"]:<12} {v["jour"] or "—":<11} {(v["titre"] or v["sujet"] or "—")[:44]:<44} {f} {ok}')
    compte = {s: sum(v["statut"] == s for v in data["videos"]) for s in STATUTS}
    print("\n" + " · ".join(f"{s} {n}" for s, n in compte.items() if n))
    attente = [v["id"] for v in data["videos"] if v["statut"] == "a_approuver"]
    if attente:
        print(f"→ À relire et approuver par vous : {', '.join(attente)}")


def cmd_maj(a):
    d, data = charger(a.semaine)
    v = video(data, a.id)
    for kv in a.champs:
        k, _, val = kv.partition("=")
        if k not in v or k in ("publications", "metriques", "id"):
            sys.exit(f"Champ non modifiable : {k}")
        if k == "statut":
            if val not in STATUTS:
                sys.exit(f"Statut inconnu : {val} ({', '.join(STATUTS)})")
            if val in ("approuve", "programme", "publie"):
                sys.exit(f"« {val} » ne se met pas avec maj : utilisez approuver / programmer / publie.")
        v[k] = [h.strip() for h in val.split(",") if h.strip()] if k == "hashtags" else val
    sauver(d, data)
    print(f"✔ {a.id} mis à jour")


def cmd_approuver(a):
    d, data = charger(a.semaine)
    v = video(data, a.id)
    if v["statut"] != "a_approuver":
        sys.exit(f'{a.id} est « {v["statut"]} » : seule une vidéo « a_approuver » peut être approuvée.')
    if not v["fichier"] or not (ROOT / v["fichier"]).exists():
        sys.exit(f'{a.id} : fichier vidéo absent ({v["fichier"] or "non renseigné"}).')
    if not v["legende"]:
        sys.exit(f"{a.id} : légende vide — à écrire avant approbation.")
    v["statut"] = "approuve"
    v["notes"].append(f"approuvée le {dt.datetime.now():%Y-%m-%d %H:%M}")
    sauver(d, data)
    print(f"✔ {a.id} approuvée")


def cmd_refuser(a):
    d, data = charger(a.semaine)
    v = video(data, a.id)
    if v["statut"] in ("programme", "publie"):
        sys.exit(f'{a.id} est déjà {v["statut"]} : retirez-la d\'abord de la plateforme.')
    v["statut"] = "refuse"
    v["notes"].append(f"refusée le {dt.datetime.now():%Y-%m-%d %H:%M} : {a.raison}")
    sauver(d, data)
    print(f"✔ {a.id} refusée ({a.raison})")


def ics_echap(s):
    return s.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")


def cmd_programmer(a):
    """Une publication par jour, dans l'ordre des vidéos approuvées, aux jours encore libres."""
    d, data = charger(a.semaine)
    debut = dt.date.fromisoformat(data["debut"])
    pris = {v["jour"] for v in data["videos"] if v["statut"] in ("programme", "publie") and v["jour"]}
    libres = [debut + dt.timedelta(days=i) for i in range(7) if (debut + dt.timedelta(days=i)).isoformat() not in pris]
    a_prog = [v for v in data["videos"] if v["statut"] == "approuve"]
    if not a_prog:
        sys.exit("Aucune vidéo approuvée à programmer.")
    for v, jour in zip(a_prog, libres):
        v["jour"], v["statut"] = jour.isoformat(), "programme"
    restantes = [v["id"] for v in a_prog if v["statut"] == "approuve"]
    sauver(d, data)

    lignes, ev = [], []
    h, m = (int(x) for x in data["heure"].split(":"))
    for v in sorted((v for v in data["videos"] if v["statut"] in ("programme", "publie")), key=lambda v: v["jour"]):
        tags = " ".join("#" + t.lstrip("#") for t in v["hashtags"])
        for p in data["plateformes"]:
            lignes.append({"date": v["jour"], "heure": data["heure"], "fuseau": data["fuseau"], "plateforme": p,
                           "id": v["id"], "titre": v["titre"], "fichier": v["fichier"],
                           "legende": (v["legende"] + ("\n\n" + tags if tags else "")).strip(),
                           "statut": "publie" if p in v["publications"] else "a_publier"})
        start = dt.datetime.fromisoformat(v["jour"]).replace(hour=h, minute=m)
        ev.append("\r\n".join([
            "BEGIN:VEVENT", f"UID:{data['semaine']}-{v['id']}@autovid-shorts",
            f"DTSTAMP:{dt.datetime.now(dt.timezone.utc):%Y%m%dT%H%M%SZ}",
            f"DTSTART;TZID={data['fuseau']}:{start:%Y%m%dT%H%M%S}",
            f"DTEND;TZID={data['fuseau']}:{start + dt.timedelta(minutes=15):%Y%m%dT%H%M%S}",
            f"SUMMARY:{ics_echap('Publier ' + v['id'] + ' : ' + (v['titre'] or v['sujet']))}",
            f"DESCRIPTION:{ics_echap(v['fichier'] + chr(10) + ', '.join(data['plateformes']))}",
            "END:VEVENT"]))
    with open(d / "publications.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0]))
        w.writeheader()
        w.writerows(lignes)
    (d / "calendrier.ics").write_text("\r\n".join(["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//autovid-shorts//machine//FR",
                                                    *ev, "END:VCALENDAR"]) + "\r\n", encoding="utf-8")
    print(f"✔ {len(a_prog) - len(restantes)} vidéo(s) programmée(s) → {d / 'publications.csv'}, {d / 'calendrier.ics'}")
    if restantes:
        print(f"⚠ plus de jour libre cette semaine pour : {', '.join(restantes)}")


def cmd_publie(a):
    d, data = charger(a.semaine)
    v = video(data, a.id)
    if v["statut"] not in ("programme", "publie"):
        sys.exit(f'{a.id} est « {v["statut"]} » : une vidéo doit être approuvée puis programmée avant publication.')
    v["publications"][a.plateforme] = {"url": a.url, "le": dt.datetime.now().isoformat(timespec="minutes")}
    if all(p in v["publications"] for p in data["plateformes"]):
        v["statut"] = "publie"
    sauver(d, data)
    print(f"✔ {a.id} publiée sur {a.plateforme}")


def trouver_colonnes(entetes):
    n = {norm(h): h for h in entetes}
    out = {}
    for champ, noms in COLONNES.items():
        for nom in noms:
            if norm(nom) in n:
                out[champ] = n[norm(nom)]
                break
    return out


def cmd_metriques(a):
    d, data = charger(a.semaine)
    with open(a.csv, encoding="utf-8-sig", newline="") as f:
        sample = f.read(4096)
        f.seek(0)
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        rows = list(csv.DictReader(f, dialect=dialect))
    if not rows:
        sys.exit("Fichier vide.")
    cols = trouver_colonnes(rows[0].keys())
    if "vues" not in cols:
        sys.exit(f"Colonne des vues introuvable. Colonnes du fichier : {', '.join(rows[0].keys())}")
    trouvees = 0
    for r in rows:
        titre, url, rid = (norm(r.get(cols.get(k, ""), "")) for k in ("titre", "url", "id"))
        if titre in ("total", ""):
            if not url and not rid:
                continue
        for v in data["videos"]:
            pub = v["publications"].get(a.plateforme, {})
            ok = (url and pub.get("url") and norm(pub["url"]) in url) or \
                 (rid and pub.get("url") and rid in norm(pub["url"])) or \
                 (titre and v["titre"] and (norm(v["titre"]) in titre or titre in norm(v["titre"])))
            if ok:
                v["metriques"][a.plateforme] = {k: num(r.get(c)) for k, c in cols.items() if k not in ("titre", "url", "id")}
                v["metriques"][a.plateforme]["importe_le"] = dt.date.today().isoformat()
                trouvees += 1
                break
    sauver(d, data)
    print(f"✔ {trouvees} vidéo(s) associée(s) sur {len(rows)} ligne(s) ({a.plateforme}). Colonnes lues : {', '.join(cols)}")
    if trouvees == 0:
        print("  Aucune correspondance : vérifiez que les titres ou les liens (machine.py publie … --url) correspondent.")


def score(m):
    """Performance comparable entre plateformes : vues + engagement pondéré (partages et abonnés comptent le plus)."""
    if not m:
        return 0.0
    vues = m.get("vues", 0)
    eng = m.get("likes", 0) + 2 * m.get("commentaires", 0) + 4 * m.get("partages", 0) + 3 * m.get("enregistrements", 0) + 10 * m.get("abonnes", 0)
    return vues + 20 * eng


def cmd_rapport(a):
    d, data = charger(a.semaine)
    lignes = []
    for v in data["videos"]:
        for p, m in v["metriques"].items():
            taux = (m.get("partages", 0) + m.get("enregistrements", 0)) / m["vues"] * 100 if m.get("vues") else 0
            lignes.append((score(m), v, p, m, taux))
    if not lignes:
        sys.exit("Aucune métrique : importez d'abord un export avec « machine.py metriques ».")
    lignes.sort(key=lambda x: -x[0])
    out = [f"# Rapport — semaine {data['semaine']}", "",
           "| # | Vidéo | Plateforme | Vues | Partages + enreg. / 100 vues | Abonnés | Hook |",
           "|---|-------|------------|------|------------------------------|---------|------|"]
    for i, (s, v, p, m, taux) in enumerate(lignes, 1):
        out.append(f'| {i} | {v["id"]} {v["titre"][:40]} | {p} | {m.get("vues", 0):,.0f} | {taux:.1f} | {m.get("abonnes", 0):,.0f} | {v["hook"] or "—"} |'.replace(",", " "))
    med = sorted(x[0] for x in lignes)[len(lignes) // 2]
    tops = [x for x in lignes if x[0] >= 2 * med][:3] or lignes[:1]
    flops = [x for x in lignes if x[0] < med / 2][-3:]
    out += ["", "## À refaire en variantes (même sujet, autre approche)"]
    for _, v, p, _, _ in tops:
        out.append(f'- **{v["id"]}** « {v["titre"]} » ({p}) : garder le sujet, tester un autre hook que « {v["hook"] or "?"} » '
                   f'et un autre format (durée, ouverture, CTA). → `variante_de: {data["semaine"]}/{v["id"]}`')
    if flops:
        out += ["", "## À ne pas reconduire tel quel"]
        for _, v, p, _, _ in flops:
            out.append(f'- {v["id"]} « {v["titre"]} » ({p}) : sous la moitié de la médiane — changer d\'angle ou de sujet.')
    out += ["", f"Médiane du score : {med:,.0f}. Score = vues + 20 × (likes + 2 commentaires + 4 partages + 3 enregistrements + 10 abonnés).".replace(",", " "),
            "Les chiffres viennent des exports importés ; une vidéo publiée depuis moins de 48 h est rarement comparable."]
    (d / "rapport.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--semaine", help="AAAA-Sss (défaut : la plus récente)")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("semaine")
    s.add_argument("--debut")
    s.add_argument("--n", type=int, default=7)
    s.add_argument("--heure", default="18:00")
    s.add_argument("--fuseau", default="Europe/Paris")
    s.add_argument("--plateformes", default="instagram,tiktok,youtube")
    sub.add_parser("statut")
    m = sub.add_parser("maj")
    m.add_argument("id")
    m.add_argument("champs", nargs="+")
    ap = sub.add_parser("approuver")
    ap.add_argument("id")
    r = sub.add_parser("refuser")
    r.add_argument("id")
    r.add_argument("--raison", required=True)
    sub.add_parser("programmer")
    pu = sub.add_parser("publie")
    pu.add_argument("id")
    pu.add_argument("--plateforme", choices=PLATEFORMES, required=True)
    pu.add_argument("--url", required=True)
    me = sub.add_parser("metriques")
    me.add_argument("csv")
    me.add_argument("--plateforme", choices=PLATEFORMES, required=True)
    sub.add_parser("rapport")
    a = p.parse_args()
    {"semaine": cmd_semaine, "statut": cmd_statut, "maj": cmd_maj, "approuver": cmd_approuver, "refuser": cmd_refuser,
     "programmer": cmd_programmer, "publie": cmd_publie, "metriques": cmd_metriques, "rapport": cmd_rapport}[a.cmd](a)


if __name__ == "__main__":
    main()
