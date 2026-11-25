#!/usr/bin/env python3
"""Super-analyse d'une vidéo : seconde par seconde, moments forts, mots qui accrochent, SEO, prompts, améliorations.

  python3 outils/superanalyse.py video.mp4                       # transcrit (faster-whisper) puis analyse
  python3 outils/superanalyse.py video.mp4 --srt sous-titres.srt # utilise des sous-titres existants (CapCut, YouTube…)
  python3 outils/superanalyse.py video.mp4 --retention retention.csv   # + courbe de rétention réelle (YouTube Studio)
  python3 outils/superanalyse.py prompts analyses/<nom>/super.json     # régénère les prompts après description des plans

Aucune image n'est produite. Résultat dans analyses/<nom>/ :
  super.md     rapport : moments forts, mots et formulations, SEO, améliorations, pourquoi ça marche
  secondes.md  tableau seconde par seconde (texte dit, énergie, changement d'image, mots forts, potentiel)
  prompts.md   un prompt par plan pour recréer la vidéo avec un générateur (Seedance, Kling…)
  super.json   toutes les données

Le « potentiel d'engagement » sans courbe de rétention est une ESTIMATION à partir de signaux (énergie de la voix,
changement d'image, mots forts, débit) ; avec --retention, les moments forts viennent des vrais chiffres.
"""
import argparse
import csv
import importlib.util
import json
import math
import re
import statistics
import sys
import unicodedata
from collections import Counter
from pathlib import Path

ICI = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("analyser_video", ICI / "analyser-video.py")
av = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(av)

# ---------------------------------------------------------------- lexiques (fr / en / pt)

FORTS = {
    "curiosité": "secret secrets personne jamais vraiment vrai vérité révèle caché cachée découvrir découvert pourquoi comment voici voilà astuce truc "
                 "méthode personne-ne nobody never secret hidden truth reveal why how here trick hack segredo ninguém nunca verdade revela "
                 "escondido descobrir porque como truque",
    # « un », « one », « um » exclus : ce sont d'abord des articles.
    "chiffre": "deux trois quatre cinq six sept huit neuf dix vingt cent mille million millions milliard two three four five ten twenty "
               "hundred thousand million dois três quatro cinco dez vinte cem mil milhão milhões",
    "gratuit / valeur": "gratuit gratuite gratuitement offert free gratis grátis gratuito",
    "urgence / temps": "maintenant aujourd'hui vite secondes minutes jours enfin déjà now today fast seconds minutes finally agora hoje rápido "
                       "segundos minutos",
    "adresse directe": "tu toi ton ta tes te t' vous votre vos you your você seu sua seus suas te",
    "choc / superlatif": "meilleur meilleure pire incroyable dingue fou folle tuer tué mort fin énorme absurde jamais-vu best worst insane "
                         "crazy kill killed dead huge melhor pior incrível absurdo louco matar morto enorme",
    "contraste": "mais sauf pourtant alors sans but except however without mas porém exceto sem",
    "appel à l'action": "commente commentez abonne abonnez partage partagez lien enregistre enregistrez like comment subscribe share link "
                        "save follow comenta comente inscreva compartilhe siga salva",
}
LEX = {}
for cat, mots in FORTS.items():
    for m in mots.split():
        LEX.setdefault(m.replace("-", " "), cat)
POURQUOI = {
    "curiosité": "ouvre une question que seule la suite de la vidéo referme (écart de curiosité)",
    "chiffre": "un chiffre rend la promesse concrète et mesurable",
    "gratuit / valeur": "baisse le coût perçu : « je n'ai rien à perdre à regarder »",
    "urgence / temps": "donne une raison de regarder maintenant",
    "adresse directe": "le spectateur se sent visé personnellement",
    "choc / superlatif": "émotion forte : surprise, incrédulité, envie de vérifier",
    "contraste": "annonce un retournement : on reste pour la chute",
    "appel à l'action": "transforme la vue en interaction (commentaire, abonnement, partage)",
    "question": "une question appelle une réponse mentale, et souvent un commentaire",
}
VIDES = set("""le la les l un une des de du d et à a au aux en dans pour par sur avec ce cet cette ces c ça cela qui que qu quoi dont où
il elle ils elles on je j me m moi nous se s y est sont être été avoir as ai a ont fait faire plus moins très bien comme si ne n pas
tout tous toute toutes son sa ses leur leurs mon ma mes notre nos ton ta tes ou donc car mais the a an and or of to in on for with is
are be was were it this that these those as at by from so if not no do does did have has had i we they he she my our their his her
o os as um uma uns umas de do da dos das e em no na nos nas para por com que é são ser foi ter tem isso isto esse essa ele ela eles
elas eu nós se não mais muito também já então aqui lá
peut peux veut vais va vont fait faut sais sait chaque sauf aussi encore juste quand alors après avant toujours rien autre
numéro numero voici voilà vraiment chose choses truc trucs ici there here can will just get got like really very also when then
pode vai faz cada sempre ainda só coisa""".split())
ELISION = re.compile(r"^(?:l|c|d|j|m|n|s|t|qu|jusqu|lorsqu|puisqu)['’]", re.I)


def norm(s):
    return unicodedata.normalize("NFC", s.lower().strip(" .,;:!?«»\"'()…-–—"))


def sans_accents(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


# ---------------------------------------------------------------- sources du texte

def lire_srt(path):
    """SRT → mots avec horodatage approché (répartis dans chaque sous-titre)."""
    blocs = re.split(r"\n\s*\n", Path(path).read_text(encoding="utf-8-sig"))
    ts = lambda x: sum(float(p) * f for p, f in zip(x.replace(",", ".").split(":"), (3600, 60, 1)))
    segs, mots = [], []
    for b in blocs:
        m = re.search(r"(\d+:\d+:\d+[,.]\d+)\s*-->\s*(\d+:\d+:\d+[,.]\d+)\s*\n(.+)", b, re.S)
        if not m:
            continue
        d, f, texte = ts(m.group(1)), ts(m.group(2)), " ".join(m.group(3).split())
        segs.append({"debut": round(d, 2), "fin": round(f, 2), "texte": texte})
        ws = texte.split()
        for i, w in enumerate(ws):
            mots.append({"debut": round(d + (f - d) * i / len(ws), 2), "fin": round(d + (f - d) * (i + 1) / len(ws), 2), "mot": w})
    if not segs:
        sys.exit(f"Aucun sous-titre lisible dans {path}")
    return {"fait": True, "source": f"srt {Path(path).name}", "segments": segs, "mots": mots, "nb_mots": len(mots),
            "premiers_mots": " ".join(w["mot"] for w in mots if w["debut"] < 3),
            "mots_par_seconde": round(len(mots) / max(0.1, mots[-1]["fin"] - mots[0]["debut"]), 2)}


def energie_par_seconde(path, duree):
    """Volume momentané (EBU R128, fenêtre 400 ms) moyenné par seconde, en LUFS."""
    r = av.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vn", "-af", "ebur128", "-f", "null", "-"])
    par = {}
    for t, mom in re.findall(r"t:\s*([\d.]+)\s+TARGET:[^M]*M:\s*(-?[\d.]+|-inf)", r.stderr):
        if mom != "-inf":
            par.setdefault(int(float(t)), []).append(float(mom))
    return [round(statistics.mean(par[s]), 1) if s in par else -70.0 for s in range(math.ceil(duree))]


def lire_retention(path, duree):
    """Export « Audience retention » de YouTube Studio : 1re colonne = position (en % de la vidéo, ou en secondes
    si l'en-tête le dit), 2e colonne = rétention en %. Résultat : {seconde: rétention moyenne}."""
    texte = Path(path).read_text(encoding="utf-8-sig")
    dialecte = csv.Sniffer().sniff(texte[:2048], ",;\t")
    lignes = [r for r in csv.reader(texte.splitlines(), dialecte) if r]
    entete = " ".join(lignes[0]).lower() if lignes else ""
    en_secondes = any(k in entete for k in ("second", "(s)", "temps (s)", "time (s)"))
    pts = []
    for r in lignes:
        try:
            pts.append((float(r[0].replace(",", ".").rstrip("%")), float(r[1].replace(",", ".").rstrip("%"))))
        except (ValueError, IndexError):
            continue  # en-tête ou ligne vide
    if not pts:
        sys.exit("Courbe de rétention illisible : 2 colonnes attendues (position, rétention %).")
    if not en_secondes and max(x for x, _ in pts) <= 1.0:
        pts = [(x * 100, y) for x, y in pts]  # positions en fraction (0–1)
    par_s = {}
    for x, y in pts:
        s = int(x) if en_secondes else int(x / 100 * duree)
        par_s.setdefault(min(s, math.ceil(duree) - 1), []).append(y)
    return {s: statistics.mean(v) for s, v in par_s.items()}


# ---------------------------------------------------------------- analyse

def secondes(m, energie, retention):
    duree = m["fiche"]["duree"]
    n = math.ceil(duree)
    mots = m["transcription"].get("mots", [])
    changements = set(int(t) for t in m["plans"]["changements"])
    coupes = set(int(t) for t in m["plans"]["coupes"])
    table = []
    med = statistics.median([e for e in energie if e > -70] or [-30])
    for s in range(n):
        ws = [w for w in mots if s <= w["debut"] < s + 1]
        texte = " ".join(w["mot"] for w in ws)
        forts = []
        for w in ws:
            k = norm(w["mot"])
            cat = LEX.get(k) or LEX.get(sans_accents(k)) or ("chiffre" if re.search(r"\d", k) else None)
            if cat:
                forts.append((w["mot"].strip(" ,.!?"), cat))
        if "?" in texte:
            forts.append(("?", "question"))
        e = energie[s] if s < len(energie) else -70
        # Potentiel estimé : énergie au-dessus de la médiane, changement d'image, mots forts, débit.
        pot = 0.0
        pot += max(0.0, min(1.0, (e - med) / 6)) * 35
        pot += (25 if s in coupes else 15 if s in changements else 0)
        pot += min(3, len(forts)) * 10
        pot += min(10, len(ws) * 3) if ws else 0
        ligne = {"s": s, "dit": texte, "energie": e, "coupe": s in coupes, "changement": s in changements,
                 "forts": forts, "potentiel": round(pot)}
        if retention:
            ligne["retention"] = round(retention.get(s, float("nan")), 1) if s in retention else None
        table.append(ligne)
    return table


def moments_forts(table, retention, n=5):
    if retention:
        pts = [(l["s"], l["retention"]) for l in table if l.get("retention") is not None]
        deltas = [(pts[i][0], pts[i][1] - pts[i - 1][1]) for i in range(1, len(pts))]
        hausses = sorted(deltas, key=lambda x: -x[1])[:n]
        chutes = sorted(deltas, key=lambda x: x[1])[:n]
        return {"source": "rétention réelle", "forts": [s for s, d in hausses if d > 0], "faibles": [s for s, d in chutes if d < 0]}
    # Fenêtres de 3 s au plus fort potentiel estimé, sans chevauchement.
    fen = sorted(((sum(l["potentiel"] for l in table[i:i + 3]), i) for i in range(max(1, len(table) - 2))), reverse=True)
    pris, forts = set(), []
    for score, i in fen:
        if not pris & set(range(i, i + 3)):
            forts.append(i)
            pris |= set(range(i, i + 3))
        if len(forts) == n:
            break
    faibles = [l["s"] for l in sorted(table, key=lambda l: l["potentiel"])[:n]]
    return {"source": "estimation (signaux)", "forts": sorted(forts), "faibles": sorted(faibles)}


def mots_cles(texte, n=15):
    """Mots et expressions les plus répétés (hors mots vides), affichés avec leurs accents."""
    vides = {sans_accents(v) for v in VIDES}
    formes, toks = {}, []
    for brut in re.findall(r"[\w'’-]+", texte.lower()):
        mot = ELISION.sub("", norm(brut))
        cle = sans_accents(mot)
        if len(cle) > 2 and cle not in vides and not cle.isdigit():
            formes.setdefault(cle, Counter())[mot] += 1
            toks.append(cle)
    affiche = lambda k: " ".join(formes[w].most_common(1)[0][0] for w in k.split())
    uni = Counter({affiche(k): v for k, v in Counter(toks).items()})
    bi = Counter(affiche(" ".join(p)) for p in zip(toks, toks[1:]))
    bi = Counter({k: v for k, v in bi.items() if v >= 2})
    return uni.most_common(n), bi.most_common(8)


def ameliorations(m, table, mf):
    out = []
    for c in m["criteres"]:
        if not c["ok"]:
            out.append(f'{c["critere"]} : {c["valeur"]} → viser {c["regle"]}.')
    t = m["transcription"]
    if t.get("fait"):
        debut = " ".join(w["mot"] for w in t["mots"] if w["debut"] < 3)
        cats3 = {cat for l in table[:3] for _, cat in l["forts"]}
        if not cats3 & {"curiosité", "chiffre", "choc / superlatif", "adresse directe", "question"}:
            out.append(f"Hook sans mot d'accroche dans les 3 premières s (« {debut[:70]} ») : ajouter un chiffre, une promesse ou une question.")
        if not any(cat == "appel à l'action" for l in table for _, cat in l["forts"]):
            out.append("Aucun appel à l'action détecté : terminer par une seule action (commenter un mot, s'abonner, enregistrer).")
        hesitations = [w for w in t["mots"] if norm(w["mot"]) in {"euh", "heu", "bah", "ben", "um", "uh", "hum", "tipo", "né"}]
        if hesitations:
            out.append(f"{len(hesitations)} hésitation(s) (« euh »…) : à couper au montage (outils/couper-silences.py).")
        longues = [s for s in t["segments"] if len(s["texte"].split()) > 18]
        if longues:
            out.append(f"{len(longues)} phrase(s) de plus de 18 mots (ex. à {longues[0]['debut']:.0f} s) : couper en phrases de 6 à 10 mots.")
    if mf["faibles"]:
        out.append("Moments faibles à resserrer ou illustrer : " + ", ".join(f"{s} s" for s in mf["faibles"]) + ".")
    return out


def pourquoi(m, table, mf, cats):
    p, a = m["plans"], m["audio"]
    raisons = []
    if p["premiere_coupe"] is not None and p["premiere_coupe"] <= 3:
        raisons.append(f"l'image change dès {p['premiere_coupe']:.1f} s : le pouce n'a pas le temps de faire défiler")
    if p["plan_moyen"] <= 3.5:
        raisons.append(f"un changement visuel toutes les {p['plan_moyen']:.1f} s entretient l'attention")
    if a.get("present") and a["premier_son"] <= 0.5:
        raisons.append("la voix démarre immédiatement, sans intro")
    for cat, nb in cats.most_common(3):
        raisons.append(f"{nb} mot(s) de type « {cat} » : {POURQUOI.get(cat, '')}")
    return raisons


# ---------------------------------------------------------------- prompts

def plans_prompts(m, table, descriptions=None):
    """Un prompt par plan (entre deux changements visuels), à compléter par la description visuelle."""
    bornes = [0.0] + m["plans"]["changements"] + [m["fiche"]["duree"]]
    f = m["fiche"]
    out = []
    for i, (a, b) in enumerate(zip(bornes, bornes[1:])):
        dit = " ".join(l["dit"] for l in table if a <= l["s"] < b).strip()
        e = [l["energie"] for l in table if a <= l["s"] < b and l["energie"] > -70]
        energie = "haute" if e and statistics.mean(e) > -16 else "moyenne" if e and statistics.mean(e) > -24 else "calme"
        d = (descriptions or {}).get(str(i), {})
        image = d.get("image") or "[DÉCRIRE L'IMAGE : sujet, décor, cadrage, lumière]"
        camera = d.get("camera") or ("plan fixe, léger zoom avant" if b - a > 3 else "plan fixe")
        texte_ecran = d.get("texte_ecran") or (dit[:60] if dit else "")
        ratio = "9:16 vertical" if f["vertical"] else "16:9"
        out.append({
            "plan": i, "debut": round(a, 2), "fin": round(b, 2), "duree": round(b - a, 2), "dit": dit, "energie": energie,
            "image": d.get("image", ""), "camera": d.get("camera", ""), "texte_ecran": d.get("texte_ecran", ""),
            "prompt_fr": f"{ratio}, {round(b - a, 1)} s. {image}. Caméra : {camera}. Énergie {energie}."
                         + (f" Texte à l'écran : « {texte_ecran} »." if texte_ecran else ""),
            "prompt_en": f"{ratio}, {round(b - a, 1)}s shot. {image if d.get('image') else '[DESCRIBE THE SHOT: subject, setting, framing, light]'}. "
                         f"Camera: {d.get('camera') or ('static, slow push-in' if b - a > 3 else 'static')}. "
                         f"{'High' if energie == 'haute' else 'Medium' if energie == 'moyenne' else 'Calm'} energy."
                         + (f' On-screen text: "{texte_ecran}".' if texte_ecran else ""),
        })
    return out


def ecrire_prompts(dossier, nom, prompts):
    L = [f"# Prompts plan par plan — {nom}", "",
         "Un prompt par plan (entre deux changements d'image). Les champs « image » et « caméra » se remplissent dans "
         "`super.json` (clé `descriptions`), puis `python3 outils/superanalyse.py prompts analyses/<nom>/super.json`.", "",
         "Règle : s'inspirer de la mécanique (durée, cadrage, rythme), jamais copier le texte, les personnes ou les marques d'autrui.", ""]
    for p in prompts:
        L += [f"## Plan {p['plan']} — {p['debut']:.1f} → {p['fin']:.1f} s ({p['duree']} s, énergie {p['energie']})",
              f"- Dit : « {p['dit']} »" if p["dit"] else "- Dit : —",
              f"- Prompt (FR) : {p['prompt_fr']}", f"- Prompt (EN, générateurs vidéo) : {p['prompt_en']}", ""]
    (dossier / "prompts.md").write_text("\n".join(L), encoding="utf-8")


# ---------------------------------------------------------------- rapport

def rapport(dossier, nom, m, table, mf, uni, bi, amel, raisons, cats, exemples):
    t = m["transcription"]
    L = [f"# Super-analyse — {nom}", "",
         f"Score mesurable : **{m['score']}/100** · {m['fiche']['format']} · {m['fiche']['duree']:.1f} s · "
         f"texte : {t.get('source', 'transcription') if t.get('fait') else 'aucun (transcription impossible : ' + t.get('raison', '?') + ')'}", "",
         "## 1. Moments les plus puissants",
         f"_Source : {mf['source']}._", ""]
    for s in mf["forts"]:
        l3 = table[s:s + 3] if mf["source"].startswith("estimation") else table[s:s + 1]
        dit = " ".join(l["dit"] for l in l3).strip()
        signaux = []
        if any(l["coupe"] or l["changement"] for l in l3):
            signaux.append("changement d'image")
        if any(l["energie"] > -16 for l in l3):
            signaux.append("voix énergique")
        fs = [f"{w} ({c})" for l in l3 for w, c in l["forts"]]
        if fs:
            signaux.append("mots forts : " + ", ".join(fs[:4]))
        L.append(f"- **{s} s** — « {dit[:90]} » — {'; '.join(signaux) or 'signal faible'}")
    if mf["faibles"]:
        L += ["", "Moments les plus faibles : " + ", ".join(f"{s} s" for s in mf["faibles"]) + "."]
    L += ["", "## 2. Mots et formulations qui accrochent", "| Type | Nb | Exemples dans la vidéo | Pourquoi ça marche |", "|---|---|---|---|"]
    for cat, nb in cats.most_common():
        L.append(f"| {cat} | {nb} | {', '.join(exemples[cat][:5])} | {POURQUOI.get(cat, '')} |")
    if t.get("fait"):
        L += ["", f"- **Hook (0–3 s)** : « {t['premiers_mots']} »",
              f"- **Débit** : {t['mots_par_seconde']} mots/s ({t['nb_mots']} mots)."]
        qs = [s["texte"] for s in t["segments"] if "?" in s["texte"]]
        if qs:
            L.append("- **Questions** : " + " / ".join(f"« {q} »" for q in qs[:4]))
    L += ["", "## 3. Pourquoi cette vidéo peut faire beaucoup de vues"] + [f"- {r}" for r in raisons] + \
         ["", "_À compléter par l'agent `analyste-video` : formule du hook (n / 21), structure, émotion dominante._", "",
          "## 4. SEO — mots-clés", "| Mot-clé | Occurrences |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in uni]
    if bi:
        L += ["", "Expressions répétées : " + ", ".join(f"« {k} » ({v})" for k, v in bi)]
    principal = (bi[0][0] if bi else uni[0][0]) if (bi or uni) else "—"
    L += ["", f"- **Mot-clé principal proposé** : « {principal} » (à placer dans les 3 premiers mots du titre, la 1re phrase de la description et à l'oral dans les 5 premières secondes).",
          "- **Hashtags** : " + " ".join("#" + re.sub(r"\W", "", k) for k, _ in uni[:6]),
          "- **Tags YouTube** : " + ", ".join([principal] + [k for k, _ in uni[:9] if k != principal]),
          "", "## 5. Améliorations (par impact)"] + [f"{i}. {a}" for i, a in enumerate(amel, 1)] + \
         ["", "## 6. Fichiers", "- `secondes.md` : tableau seconde par seconde.", "- `prompts.md` : un prompt par plan pour recréer la vidéo.",
          "- `super.json` : toutes les données (à compléter : `descriptions`)."]
    (dossier / "super.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    S = [f"# Seconde par seconde — {nom}", "",
         "Potentiel = estimation 0–100 (énergie de la voix, changement d'image, mots forts, débit)"
         + (" ; rétention = vrais chiffres." if any("retention" in l for l in table) else "."), "",
         "| s | Dit | Énergie (LUFS) | Image | Mots forts | Potentiel |" + (" Rétention |" if any("retention" in l for l in table) else ""),
         "|---|---|---|---|---|---|" + ("---|" if any("retention" in l for l in table) else "")]
    for l in table:
        img = "coupe" if l["coupe"] else "change" if l["changement"] else ""
        barre = "█" * (l["potentiel"] // 10)
        S.append(f"| {l['s']} | {l['dit'][:60]} | {l['energie']} | {img} | {', '.join(w for w, _ in l['forts'])} | {barre} {l['potentiel']} |"
                 + (f" {l['retention']} |" if "retention" in l else ""))
    (dossier / "secondes.md").write_text("\n".join(S) + "\n", encoding="utf-8")


def analyser(video, a):
    nom = av.slug(video)
    dossier = Path(a.sortie) / nom
    dossier.mkdir(parents=True, exist_ok=True)
    print(f"▶ {video}")
    m = {"fichier": str(video)}
    print("  1/6 fiche, découpage, son")
    m["fiche"] = av.fiche(video)
    m["plans"] = av.plans(video, m["fiche"]["duree"], 0.3, a.seuil_visuel)
    m["audio"] = av.audio(video, m["fiche"]["duree"], m["fiche"]["audio"])
    print("  2/6 texte")
    m["transcription"] = lire_srt(a.srt) if a.srt else av.transcrire(video, a.langue)
    m["criteres"], m["score"] = av.criteres(m)
    print("  3/6 énergie seconde par seconde")
    energie = energie_par_seconde(video, m["fiche"]["duree"]) if m["fiche"]["audio"] else [-70.0] * math.ceil(m["fiche"]["duree"])
    retention = lire_retention(a.retention, m["fiche"]["duree"]) if a.retention else None
    print("  4/6 moments forts")
    table = secondes(m, energie, retention)
    mf = moments_forts(table, retention)
    print("  5/6 mots, SEO, améliorations")
    cats, exemples = Counter(), {}
    for l in table:
        for w, c in l["forts"]:
            cats[c] += 1
            exemples.setdefault(c, [])
            if w not in exemples[c]:
                exemples[c].append(w)
    texte = " ".join(s["texte"] for s in m["transcription"].get("segments", []))
    uni, bi = mots_cles(texte) if texte else ([], [])
    amel = ameliorations(m, table, mf)
    raisons = pourquoi(m, table, mf, cats)
    print("  6/6 prompts et rapport")
    prompts = plans_prompts(m, table)
    donnees = {**m, "secondes": table, "moments": mf, "mots_cles": uni, "expressions": bi, "ameliorations": amel,
               "pourquoi": raisons, "prompts": prompts, "descriptions": {}}
    (dossier / "super.json").write_text(json.dumps(donnees, indent=2, ensure_ascii=False), encoding="utf-8")
    rapport(dossier, nom, m, table, mf, uni, bi, amel, raisons, cats, exemples)
    ecrire_prompts(dossier, nom, prompts)
    print(f"  ✔ {dossier / 'super.md'}  (+ secondes.md, prompts.md, super.json)")


def regenerer_prompts(json_path):
    d = json.loads(Path(json_path).read_text(encoding="utf-8"))
    prompts = plans_prompts(d, d["secondes"], d.get("descriptions"))
    d["prompts"] = prompts
    Path(json_path).write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
    ecrire_prompts(Path(json_path).parent, Path(json_path).parent.name, prompts)
    print(f"✔ {Path(json_path).parent / 'prompts.md'}")


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "prompts":
        return regenerer_prompts(sys.argv[2])
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("videos", nargs="+")
    ap.add_argument("--srt", help="sous-titres existants (au lieu de transcrire)")
    ap.add_argument("--retention", help="export CSV de la rétention d'audience (YouTube Studio)")
    ap.add_argument("--langue", default=None)
    ap.add_argument("--seuil-visuel", type=float, default=0.06)
    ap.add_argument("--sortie", default=str(ICI.parent / "analyses"))
    a = ap.parse_args()
    if a.srt and len(a.videos) > 1:
        sys.exit("--srt ne s'utilise qu'avec une seule vidéo.")
    for v in a.videos:
        analyser(v, a)


if __name__ == "__main__":
    main()
