"""Titres, descriptions, tags et hashtags en français, portugais du Brésil et anglais.

Structure de titre reprise de la chaîne de référence (FISH13) : SUJET EN MAJUSCULES + émoji + promesse,
puis des mots-clés entre crochets, ex. « LUXURY CAMPING IN THE RAIN ⛈️ XXL INFLATABLE CAPSULE TENT »
→ « HIGH KICK 🦵 LE SECRET DE LA HANCHE [ Anatomie, Placement, Erreurs ] ».
"""
import json
from pathlib import Path

EMOJI = {"pied": "🦵", "poing": "🥊", "genou": "🦵", "au": "🤸", "esquive": "🌀", "rasteira": "🌀"}

T = {
    "fr": {
        "promesse": ["LE SECRET DE LA TECHNIQUE", "ANALYSE AU RALENTI", "CE QUE PERSONNE NE T'EXPLIQUE"],
        "crochets": "[ Anatomie, Placement, Erreurs ]",
        "desc": ("{nom} expliqué au ralenti : placement, muscles moteurs et risques de blessure.\n\n"
                 "Dans cette vidéo :\n{liste}\n\n"
                 "⚠️ Échauffe-toi et progresse avec un coach. Les conseils ne remplacent pas un avis médical.\n\n"
                 "Abonne-toi pour la suite 👊 {handle}"),
        "tags": ["technique de combat", "analyse au ralenti", "anatomie du sport", "self défense", "entraînement",
                 "biomécanique", "prévention des blessures"],
        "hashtags": ["#combat", "#anatomie", "#entrainement", "#selfdefense"],
    },
    "pt": {
        "promesse": ["O SEGREDO DA TÉCNICA", "ANÁLISE EM CÂMERA LENTA", "O QUE NINGUÉM TE EXPLICA"],
        "crochets": "[ Anatomia, Posicionamento, Erros ]",
        "desc": ("{nom} explicado em câmera lenta: posicionamento, músculos e riscos de lesão.\n\n"
                 "Neste vídeo:\n{liste}\n\n"
                 "⚠️ Aqueça bem e treine com um professor. Isto não substitui orientação médica.\n\n"
                 "Inscreva-se para a próxima 👊 {handle}"),
        "tags": ["técnica de luta", "câmera lenta", "anatomia do esporte", "defesa pessoal", "treino",
                 "biomecânica", "prevenção de lesões"],
        "hashtags": ["#luta", "#anatomia", "#treino", "#defesapessoal"],
    },
    "en": {
        "promesse": ["THE SECRET BEHIND IT", "SLOW MOTION BREAKDOWN", "WHAT NOBODY TELLS YOU"],
        "crochets": "[ Anatomy, Placement, Mistakes ]",
        "desc": ("{nom} broken down in slow motion: placement, prime movers and injury risks.\n\n"
                 "In this video:\n{liste}\n\n"
                 "⚠️ Warm up and train with a coach. This is not medical advice.\n\n"
                 "Subscribe for part 2 👊 {handle}"),
        "tags": ["fight technique", "slow motion breakdown", "sports anatomy", "self defense", "training",
                 "biomechanics", "injury prevention"],
        "hashtags": ["#martialarts", "#anatomy", "#training", "#selfdefense"],
    },
}

DISCIPLINE_TAGS = {
    "capoeira": {"fr": ["capoeira", "ginga", "roda de capoeira"], "pt": ["capoeira", "ginga", "roda de capoeira"],
                 "en": ["capoeira", "ginga", "capoeira kicks"], "hash": ["#capoeira", "#ginga", "#roda"]},
    "combat": {"fr": ["boxe", "mma", "muay thai", "kickboxing"], "pt": ["boxe", "mma", "muay thai", "kickboxing"],
               "en": ["boxing", "mma", "muay thai", "kickboxing"], "hash": ["#mma", "#boxing", "#muaythai"]},
}


def _mmss(t):
    return f"{int(t // 60)}:{int(t % 60):02d}"


def build(analyses, discipline="combat", handle="", shorts=True):
    """analyses : [{'t_out': secondes dans la vidéo finale, 'nom', 'kind', 'muscles': [...]}]."""
    if not analyses:
        analyses = [{"t_out": 0, "nom": discipline.upper(), "kind": "pied", "muscles": []}]
    main = analyses[0]
    emoji = EMOJI.get(main["kind"], "🥋")
    noms = list(dict.fromkeys(a["nom"] for a in analyses))
    sujet = main["nom"] if len(noms) == 1 else f"{noms[0]} + {len(noms) - 1}"
    dtags = DISCIPLINE_TAGS.get(discipline, DISCIPLINE_TAGS["combat"])
    out = {}
    for lang, t in T.items():
        titres = [f"{sujet} {emoji} {p} {t['crochets']}" for p in t["promesse"]]
        titres = [x if len(x) <= 100 else x[:97] + "…" for x in titres]
        liste = "\n".join(f"{_mmss(a['t_out'])} {a['nom']}" for a in analyses)
        hashtags = dtags["hash"] + t["hashtags"] + (["#shorts"] if shorts else [])
        tags = [n.lower() for n in noms] + dtags[lang] + t["tags"]
        out[lang] = {
            "titres": titres,
            "description": t["desc"].format(nom=sujet, liste=liste, handle=handle) + "\n\n" + " ".join(hashtags),
            "tags": list(dict.fromkeys(tags))[:20],
            "hashtags": hashtags,
        }
    return out


def write(seo, base):
    Path(f"{base}.seo.json").write_text(json.dumps(seo, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = []
    for lang, d in seo.items():
        lines += [f"===== {lang.upper()} =====", "Titres :"] + [f"  - {x}" for x in d["titres"]]
        lines += ["", "Description :", d["description"], "", "Tags : " + ", ".join(d["tags"]), "", ""]
    Path(f"{base}.seo.txt").write_text("\n".join(lines), encoding="utf-8")
