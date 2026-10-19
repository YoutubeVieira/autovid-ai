"""Automate « projet viral » : une vidéo → une vidéo longue YouTube + des shorts + SEO + plan de publication.

  python -m autovid viral roda.mp4 -o projet_roda/ --discipline capoeira --handle @toncompte

1. short principal (toutes les analyses) avec le moteur combat ;
2. vidéo longue 16:9 à chapitres (long.py) construite sur ce short ;
3. un short par mouvement différent (le meilleur de chaque), chacun avec sa propre accroche ;
4. titres / descriptions / chapitres et un plan de publication (`a_publier.md`).
"""
import copy
import json
import re
import unicodedata
from pathlib import Path

from . import gfx


def _slug(text):
    t = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", t).strip("_")[:30] or "moment"


def short_variant(projet, keep_id):
    """Projet du short principal réduit à un seul moment ; l'accroche redevient celle de ce mouvement."""
    p = copy.deepcopy(projet)
    for a in p["analyses"]:
        a["actif"] = a["id"] == keep_id
    p["accroche"] = {}
    return p


def plan_markdown(name, long_title, chapters, shorts, seo_fr, handle):
    lines = [f"# À publier : {name}", "",
             "Ordre conseillé : la vidéo longue d'abord (elle reçoit les vues des shorts), puis un short par jour, "
             "chacun avec la vidéo longue en lien ou en commentaire épinglé.", "",
             "## 1. Vidéo longue (YouTube)", "", "Fichier : `longue_youtube.mp4`, miniature `short_principal_youtube.jpg`", "",
             f"Titre : {long_title}", "", "Description :", "", "```",
             seo_fr["description"].split("\n\nDans cette vidéo")[0], "", "Chapitres :", chapters.strip(), "",
             f"Abonne-toi pour la suite {handle}".strip(), "", " ".join(h for h in seo_fr["hashtags"] if h != "#shorts"),
             "```", "", "## 2. Short principal (TikTok, Reels, YouTube Shorts)", "",
             "Fichier : `short_principal.mp4`, textes dans `short_principal.seo.txt`", ""]
    for i, (path, nom) in enumerate(shorts, 2):
        lines += [f"## {i + 1}. Short « {nom} » (jour {i})", "", f"Fichier : `{path}`, textes dans le .seo.txt du même nom", ""]
    lines += ["## Rappels", "", "- Une seule demande par vidéo (s'abonner OU commenter), pas les deux.",
              "- 5 hashtags maximum.", "- Répondre aux commentaires de la première heure.",
              "- Mention IA obligatoire si un plan a été généré par IA."]
    return "\n".join(lines) + "\n"


def viral(src, out_dir, workdir, discipline="combat", handle=None, tts="auto", framing="auto", max_shorts=4, ai=None,
          accent=None, projet=None, **combat_kw):
    from .combat import combat
    from .long import long_video
    from .projet import load
    out = Path(out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    work = Path(workdir)
    accent = accent or gfx.GREEN

    print("━━ 1/4 short principal")
    main = out / "short_principal.mp4"
    combat(src, main, work / "combat", handle=handle, discipline=discipline, tts=tts, framing=framing, ai=ai,
           accent=accent, projet=projet, **combat_kw)
    projet = load(main.with_suffix(".projet.json"))
    seo = json.loads(main.with_suffix(".seo.json").read_text(encoding="utf-8"))

    print("━━ 2/4 vidéo longue YouTube 16:9")
    _, marks = long_video(src, str(main), main.with_suffix(".segments.json"), out / "longue_youtube.mp4", work / "longue",
                          handle or "", accent)

    print("━━ 3/4 un short par mouvement")
    scores = {round(x["src_t"], 1): x["score"]
              for x in json.loads(main.with_suffix(".segments.json").read_text(encoding="utf-8"))["analyses"]}
    seen, picks = set(), []
    for a in sorted(projet["analyses"], key=lambda a: -scores.get(round(a["t"], 1), 0)):
        if a["titre"] not in seen and a.get("actif", True):
            seen.add(a["titre"])
            picks.append(a)
    picks = picks[:max_shorts] if len(projet["analyses"]) > 1 else []
    shorts = []
    for a in picks:
        path = out / "shorts" / f"short_{_slug(a['titre'])}.mp4"
        path.parent.mkdir(exist_ok=True)
        print(f"   → {a['titre']} ({a['t']:.1f} s)")
        combat(src, path, work / "combat", tts=tts, projet=short_variant(projet, a["id"]))
        shorts.append((str(path.relative_to(out)), a["titre"]))

    print("━━ 4/4 SEO et plan de publication")
    chapters = main.with_name("longue_youtube.chapitres.txt").read_text(encoding="utf-8")
    long_title = seo["fr"]["titres"][0].replace("ANALYSE AU RALENTI", "ANALYSE COMPLÈTE")
    (out / "a_publier.md").write_text(plan_markdown(Path(src).stem, long_title, chapters, shorts, seo["fr"], handle or ""),
                                      encoding="utf-8")
    manifest = {"source": str(Path(src).resolve()), "short_principal": "short_principal.mp4",
                "longue": "longue_youtube.mp4", "chapitres": [[round(t, 2), c] for t, c in marks],
                "shorts": [p for p, _ in shorts]}
    (out / "projet_viral.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"→ {out}")
    return str(out)
