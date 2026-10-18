"""Reconnaissance de la technique à partir du squelette + fiches anatomie / conseils (français)."""

from .pose import (L_ANK, L_EL, L_FOOT, L_HIP, L_KNEE, L_SH, L_WR, R_ANK, R_EL, R_FOOT, R_HIP, R_KNEE, R_SH,
                   R_WR, angle)

SIDE = {L_WR: "G", R_WR: "D", L_ANK: "G", R_ANK: "D", L_KNEE: "G", R_KNEE: "D"}
J = {  # articulations par côté : (épaule, coude, poignet, hanche, genou, cheville, pied)
    "G": (L_SH, L_EL, L_WR, L_HIP, L_KNEE, L_ANK, L_FOOT),
    "D": (R_SH, R_EL, R_WR, R_HIP, R_KNEE, R_ANK, R_FOOT),
}
COTE = {"G": "GAUCHE", "D": "DROIT"}
COTE_F = {"G": "GAUCHE", "D": "DROITE"}

HOOKS = {
    "pied": ("LE SECRET DE CE {nom}", "REGARDE SA HANCHE"),
    "poing": ("POURQUOI CE {nom} FAIT MAL", "TOUT PART DES PIEDS"),
    "genou": ("CE {nom} EST UNE ARME", "REGARDE SON BASSIN"),
}

TIPS = {
    "HIGH KICK": "PIVOTE SUR L'AVANT-PIED D'APPUI",
    "MIDDLE KICK": "TOURNE LA HANCHE PAR-DESSUS",
    "LOW KICK": "FRAPPE AVEC LE TIBIA, PAS LE PIED",
    "COUP DE PIED RETOURNÉ": "REGARDE LA CIBLE PAR-DESSUS L'ÉPAULE",
    "DIRECT": "MENTON RENTRÉ, ÉPAULE QUI PROTÈGE",
    "CROCHET": "COUDE À HAUTEUR DU POING",
    "UPPERCUT": "POUSSE AVEC LES JAMBES",
    "COUP DE GENOU": "TIRE LA TÊTE, MONTE LE BASSIN",
}


def classify(track, i, eff):
    """Nomme la technique frappée à l'image i par l'extrémité `eff` (poignet, cheville ou genou)."""
    p = track[i]
    s = SIDE[eff]
    o = "D" if s == "G" else "G"
    sh, el, wr, hip, knee, ank, foot = J[s]
    osh, oel, owr, ohip, oknee, oank, ofoot = J[o]
    hip_y = (p[L_HIP, 1] + p[R_HIP, 1]) / 2
    sh_y = (p[L_SH, 1] + p[R_SH, 1]) / 2
    # NB : un coup retourné ne se distingue pas de façon fiable d'un circulaire par le squelette 2D
    # (les épaules « s'inversent » aussi pendant un circulaire) : seul --ai claude peut le nommer.

    if eff in (L_WR, R_WR):
        kind = "poing"
        elbow = angle(p[sh], p[el], p[wr])
        rise = track[max(i - 6, 0), wr, 1] - p[wr, 1]
        run = abs(track[max(i - 6, 0), wr, 0] - p[wr, 0])
        nom = "UPPERCUT" if rise > 0.05 and rise > run else ("DIRECT" if elbow > 140 else "CROCHET")
        joint_angle = ("COUDE", (sh, el, wr), elbow)
        chain = [(ank, knee), (knee, hip), (hip, sh), (sh, el), (el, wr)]
        support = [(oank, oknee), (oknee, ohip)]
        joints = [ank, hip, sh, el, wr]
        muscles = [("TRICEPS", "étend le bras", (sh, el)),
                   ("DELTOÏDE", "lance l'épaule", (sh,)),
                   ("OBLIQUES", "rotation du buste", (hip, osh)),
                   ("MOLLET", "poussée du pied", (knee, ank))]
        if nom == "CROCHET":
            muscles[0] = ("GRAND DORSAL", "verrouille le bras", (sh, hip))
        if nom == "UPPERCUT":
            muscles[0] = ("QUADRICEPS", "pousse vers le haut", (hip, knee))
        membre = f"BRAS {COTE[s]}"
    elif eff in (L_KNEE, R_KNEE) or (p[knee, 1] < hip_y and angle(p[hip], p[knee], p[ank]) < 80):
        kind = "genou"
        nom = "COUP DE GENOU"
        knee_a = angle(p[hip], p[knee], p[ank])
        joint_angle = ("GENOU", (hip, knee, ank), knee_a)
        chain = [(oank, oknee), (oknee, ohip), (ohip, hip), (hip, knee)]
        support = []
        joints = [oank, hip, knee]
        muscles = [("PSOAS", "monte la cuisse", (hip,)),
                   ("ABDOMINAUX", "enroulent le bassin", (hip, osh)),
                   ("FESSIERS", "poussent la hanche", (ohip,))]
        membre = f"JAMBE {COTE_F[s]}"
    else:
        kind = "pied"
        y = p[ank, 1]
        nom = "HIGH KICK" if y < sh_y + 0.02 else ("MIDDLE KICK" if y < hip_y + 0.05 else "LOW KICK")
        knee_a = angle(p[hip], p[knee], p[ank])
        joint_angle = ("GENOU", (hip, knee, ank), knee_a)
        chain = [(ohip, hip), (hip, knee), (knee, ank), (ank, foot)]
        support = [(oank, oknee), (oknee, ohip)]
        joints = [oank, hip, knee, ank]
        muscles = [("PSOAS-ILIAQUE", "monte le genou", (hip,)),
                   ("QUADRICEPS", "fouette la jambe", (hip, knee)),
                   ("FESSIERS", "rotation de hanche", (ohip, hip)),
                   ("MOLLET D'APPUI", "pivot sur l'avant-pied", (oknee, oank))]
        membre = f"JAMBE {COTE_F[s]}"
    court = nom.split(" (")[0]
    h1, h2 = HOOKS[kind]
    return {
        "kind": kind, "nom": nom, "membre": membre, "side": s,
        "hook": [h1.format(nom=court), h2], "tip": TIPS.get(nom, "RESTE EN GARDE"),
        "chain": chain, "support": support, "joints": joints,
        "angle": joint_angle, "muscles": muscles[:3], "effector": int(eff),
    }


# correspondance texte libre (IA) → points d'ancrage sur le squelette
ANCHORS = [
    ("quadri", lambda s, o: (J[s][3], J[s][4])), ("ischio", lambda s, o: (J[s][3], J[s][4])),
    ("psoas", lambda s, o: (J[s][3],)), ("fess", lambda s, o: (J[o][3], J[s][3])),
    ("oblique", lambda s, o: (J[s][3], J[o][0])), ("abdo", lambda s, o: (J[s][3], J[o][0])),
    ("mollet", lambda s, o: (J[o][4], J[o][5])), ("tibia", lambda s, o: (J[s][4], J[s][5])),
    ("tricep", lambda s, o: (J[s][0], J[s][1])), ("bicep", lambda s, o: (J[s][0], J[s][1])),
    ("delto", lambda s, o: (J[s][0],)), ("épaule", lambda s, o: (J[s][0],)),
    ("pector", lambda s, o: (J[s][0], J[o][0])), ("dorsal", lambda s, o: (J[s][0], J[s][3])),
    ("hanche", lambda s, o: (J[s][3],)), ("genou", lambda s, o: (J[s][4],)),
]


def anchor_for(muscle, side):
    o = "D" if side == "G" else "G"
    m = muscle.lower()
    for key, fn in ANCHORS:
        if key in m:
            return fn(side, o)
    return (J[side][3],)


# --------------------------------------------------------------------------- placement et risques de blessure

PLACEMENT = {
    "HIGH KICK": "Pied d'appui pivoté à 90°, hanche ouverte, bras opposé en garde.",
    "MIDDLE KICK": "Tibia à hauteur des côtes, hanche qui passe par-dessus.",
    "LOW KICK": "Frappe avec le tibia au-dessus du genou adverse, appui fléchi.",
    "DIRECT": "Épaule devant le menton, poing aligné avec l'avant-bras, talon arrière levé.",
    "CROCHET": "Coude à hauteur du poing, rotation sur l'avant-pied.",
    "UPPERCUT": "Genoux fléchis, poussée des jambes, poing qui monte près du corps.",
    "COUP DE GENOU": "Mains qui contrôlent la nuque, bassin projeté vers l'avant.",
}

RISQUES = {
    "pied": ("ISCHIOS ET HANCHE", "échauffe-toi, monte l'amplitude progressivement"),
    "poing": ("POIGNET", "aligne les métacarpes, bande tes mains"),
    "genou": ("GENOU D'APPUI", "ne verrouille pas l'appui, reste fléchi"),
    "au": ("POIGNETS ET NUQUE", "mains à plat, doigts écartés, regard au sol"),
    "esquive": ("GENOUX", "genou dans l'axe du pied, pas vers l'intérieur"),
    "rasteira": ("CHEVILLE DU PARTENAIRE", "balaye doucement à l'entraînement"),
}

# Vocabulaire capoeira (prononcé en portugais du Brésil dans la voix off)
CAPOEIRA = {
    "pied_haut": "MEIA-LUA DE COMPASSO", "pied_moyen": "ARMADA", "pied_bas": "RASTEIRA",
    "genou": "JOELHADA", "poing": "GALOPANTE", "au": "AÚ", "esquive": "ESQUIVA", "ginga": "GINGA",
}
PT_TERMS = ["meia-lua de compasso", "meia-lua de frente", "meia-lua", "queixada", "armada", "martelo", "bênção",
            "rasteira", "esquiva", "negativa", "cocorinha", "rolê", "macaco", "joelhada", "galopante", "ginga",
            "capoeira", "berimbau", "mestre", "malícia", "chamada", "roda", "axé", "aú"]


def tag_pt(text):
    """Entoure les termes capoeira de [pt]…[/pt] pour que la voix off les prononce en portugais du Brésil."""
    import re
    if "[pt]" in text:
        return text
    pattern = "|".join(re.escape(t) for t in sorted(PT_TERMS, key=len, reverse=True))
    return re.sub(rf"(?<![\w-])({pattern})(?![\w-])", r"[pt]\1[/pt]", text, flags=re.IGNORECASE)


def capoeira_variant(track, i, info):
    """Adapte le nom au vocabulaire capoeira + repère les positions propres à la capoeira (aú, esquiva)."""
    p = track[i]
    head_y = p[0, 1]
    ank_y = min(p[L_ANK, 1], p[R_ANK, 1])
    wr_y = max(p[L_WR, 1], p[R_WR, 1])
    hip_y = (p[L_HIP, 1] + p[R_HIP, 1]) / 2
    knee_y = (p[L_KNEE, 1] + p[R_KNEE, 1]) / 2
    if ank_y < head_y and wr_y > hip_y:                 # pieds au-dessus de la tête, mains au sol : aú
        info.update(nom=CAPOEIRA["au"], kind="au", membre="CORPS ENTIER")
    elif hip_y > knee_y - 0.02 and info["kind"] != "pied":  # bassin plus bas que les genoux : esquiva
        info.update(nom=CAPOEIRA["esquiva"], kind="esquive")
    elif info["kind"] == "pied":
        info["nom"] = {"HIGH KICK": CAPOEIRA["pied_haut"], "MIDDLE KICK": CAPOEIRA["pied_moyen"],
                       "LOW KICK": CAPOEIRA["pied_bas"]}.get(info["nom"], info["nom"])
        if info["nom"] == CAPOEIRA["pied_bas"]:
            info["kind"] = "rasteira"
    elif info["kind"] == "genou":
        info["nom"] = CAPOEIRA["genou"]
    return info


def add_safety(info):
    info["risque"] = RISQUES.get(info["kind"], RISQUES["pied"])
    info["placement"] = PLACEMENT.get(info["nom"], info.get("placement", "Garde haute, appuis stables."))
    return info
