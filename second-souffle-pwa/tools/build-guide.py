#!/usr/bin/env python3
"""Construit le guide de tournage et de posture (HTML A4, à imprimer en PDF).
Usage : python3 tools/build-guide.py sortie.html   puis   node tools/print-pdf.js sortie.html sortie.pdf"""
import json
import sys
from html import escape as E
from pathlib import Path

root = Path(__file__).resolve().parent.parent
data = json.loads((root / "docs" / "production-data.json").read_text(encoding="utf-8"))
ITEMS = {i["id"]: i for i in data["items"]}

GROUPS = [
    ("A", "Debout, sur le tapis", "Tapis, sol non glissant. Aucun autre matériel.",
     ["marche", "epaules-rot", "cou-rot"]),
    ("B", "Sur la chaise", "Chaise stable sans accoudoirs, dossier contre un mur. Élastique fixé à hauteur de poitrine (poignée de porte) et élastique à passer sous les pieds.",
     ["squat", "ext-jambe", "rowing", "developpe", "une-jambe"]),
    ("C", "Contre le mur", "Mur lisse, sol non glissant.",
     ["pompes-mur", "mollets"]),
    ("D", "Allongé sur le dos", "Tapis épais. Caméra posée au sol pour les plans à hauteur de hanche.",
     ["pont", "levee-jambe", "dead-bug", "bascule", "respiration"]),
    ("E", "À quatre pattes et genoux au sol", "Tapis épais, coussin pour le genou.",
     ["gainage", "bird-dog", "chat", "hanches-etir"]),
]

POSITION = {
    "marche": "Debout au centre du tapis, pieds largeur du bassin.",
    "epaules-rot": "Debout, bras le long du corps.",
    "cou-rot": "Debout, ou assis sur la chaise. Plan serré poitrine-tête.",
    "squat": "Debout devant la chaise, dos tourné vers l'assise.",
    "ext-jambe": "Assis sur la chaise, dos droit.",
    "rowing": "Assis sur la chaise, élastique tendu devant à hauteur de poitrine.",
    "developpe": "Assis sur la chaise, élastique sous les pieds.",
    "une-jambe": "Debout à côté de la chaise, une main sur le dossier.",
    "pompes-mur": "Face au mur, pieds à une longueur de bras.",
    "mollets": "Face au mur, un pied en arrière.",
    "pont": "Allongé sur le dos, genoux pliés, pieds à plat.",
    "levee-jambe": "Allongé sur le dos, une jambe pliée, l'autre tendue.",
    "dead-bug": "Allongé sur le dos, bras vers le plafond, genoux à angle droit.",
    "bascule": "Allongé sur le dos, genoux pliés, pieds à plat.",
    "respiration": "Allongé sur le dos, genoux pliés, une main sur le ventre.",
    "gainage": "Sur les genoux et les avant-bras, coudes sous les épaules.",
    "bird-dog": "À quatre pattes, mains sous les épaules, genoux sous les hanches.",
    "chat": "À quatre pattes, mains sous les épaules, genoux sous les hanches.",
    "hanches-etir": "Un genou au sol sur un coussin, l'autre pied devant.",
}

TAKE = {
    "marche": "20 s de marche régulière (une boucle de 5 s sera extraite)",
    "epaules-rot": "6 cercles vers l'arrière, puis 1 série lente",
    "cou-rot": "3 demi-cercles de chaque côté, très lents",
    "squat": "3 répétitions (2 s pour descendre, 2 s pour monter), puis 1 lente",
    "ext-jambe": "3 répétitions par jambe, tenue de 2 s, puis 1 lente",
    "rowing": "3 répétitions, puis 1 lente",
    "developpe": "3 répétitions, puis 1 lente",
    "une-jambe": "10 s par jambe",
    "pompes-mur": "3 répétitions, puis 1 lente",
    "mollets": "30 s de tenue (10 s utiles suffisent au montage)",
    "pont": "3 répétitions (tenue de 1 s en haut), puis 1 lente",
    "levee-jambe": "3 répétitions par jambe, puis 1 lente",
    "dead-bug": "3 répétitions par côté, très lentes",
    "bascule": "3 répétitions, tenue de 2 s",
    "respiration": "4 respirations lentes (environ 30 s)",
    "gainage": "2 tenues de 10 s. Arrêt immédiat si le dos se creuse.",
    "bird-dog": "3 répétitions par côté, tenue de 2 s",
    "chat": "4 allers-retours lents",
    "hanches-etir": "20 s de tenue par côté (10 s utiles suffisent au montage)",
}

# Code posture : T tête, É épaules, D dos, B bassin, G genoux, P pieds. Les lettres absentes ne sont pas critiques ici.
CODE = {
    "marche": {"T": "Regard devant, menton légèrement rentré.", "É": "Bas et relâchés, les bras balancent.", "D": "Long, sans se pencher en arrière.", "B": "À niveau, stable.", "G": "Montent à mi-hauteur seulement.", "P": "Se posent à plat, du talon aux orteils."},
    "epaules-rot": {"T": "Cou long, regard devant.", "É": "Cercles vers l'arrière, sans monter vers les oreilles.", "D": "Droit, sans cambrer.", "G": "Souples, jamais verrouillés.", "P": "Écartés largeur du bassin."},
    "cou-rot": {"T": "Le menton descend ; demi-cercle seulement, jamais la tête en arrière.", "É": "Bas et immobiles.", "D": "Droit, sans se pencher."},
    "squat": {"T": "Regard devant, menton rentré.", "É": "Bas, poitrine ouverte.", "D": "Droit, penché depuis les hanches.", "B": "Recule vers l'assise, comme pour s'asseoir.", "G": "Alignés sur les pieds, ne rentrent pas vers l'intérieur.", "P": "À plat, la poussée se fait dans les talons."},
    "ext-jambe": {"T": "Regard devant.", "É": "Bas.", "D": "Droit, sans se pencher en arrière.", "B": "Posé à plat sur l'assise.", "G": "Se tend sans se verrouiller brutalement.", "P": "Pied tiré vers soi à l'arrivée."},
    "rowing": {"T": "Neutre, regard devant.", "É": "Bas, loin des oreilles ; les omoplates se rapprochent.", "D": "Droit, sans s'arrondir.", "B": "Stable sur l'assise.", "P": "À plat au sol."},
    "developpe": {"T": "Neutre, regard devant.", "É": "Bas avant de pousser.", "D": "Droit, côtes rentrées, sans cambrer.", "B": "Stable sur l'assise.", "P": "À plat, l'élastique dessous."},
    "une-jambe": {"T": "Regard fixé devant.", "É": "Bas et détendus.", "D": "Droit.", "B": "À niveau, sans pencher.", "G": "Jambe d'appui souple, non verrouillée.", "P": "Pied d'appui à plat, orteils vers l'avant."},
    "pompes-mur": {"T": "Dans le prolongement du dos.", "É": "Loin des oreilles ; coudes à 45° du corps.", "D": "Corps aligné de la tête aux talons, sans creux.", "B": "Aligné, ni haut ni bas.", "G": "Tendus sans se verrouiller.", "P": "À plat, talons au sol."},
    "mollets": {"T": "Regard vers le mur.", "É": "Détendus.", "D": "Droit.", "B": "Face au mur, hanches de face.", "G": "Jambe arrière tendue, jambe avant fléchie.", "P": "Talon arrière au sol, pied droit."},
    "pont": {"T": "Posée au sol, regard au plafond.", "É": "À plat au sol.", "D": "Neutre, sans cambrer en haut.", "B": "Monte jusqu'à l'alignement épaules-genoux.", "G": "Alignés sur les pieds.", "P": "À plat, écartés largeur du bassin."},
    "levee-jambe": {"T": "Posée au sol.", "É": "À plat.", "D": "Bas du dos posé, sans creux.", "B": "Stable, ne bascule pas.", "G": "Jambe levée tendue, jambe pliée à 90°.", "P": "Pied de la jambe pliée à plat."},
    "dead-bug": {"T": "Posée, regard au plafond.", "É": "À plat.", "D": "Bas du dos collé au sol.", "B": "Stable.", "G": "À angle droit au départ."},
    "bascule": {"T": "Posée.", "É": "À plat.", "D": "Le bas du dos s'aplatit contre le sol.", "B": "Bascule ; les fessiers restent au sol.", "G": "Pliés.", "P": "À plat, écartés largeur du bassin."},
    "respiration": {"T": "Posée, mâchoire détendue.", "É": "Relâchées.", "D": "Naturel.", "B": "Neutre.", "G": "Pliés.", "P": "À plat."},
    "gainage": {"T": "Dans le prolongement du dos, regard vers le sol.", "É": "Loin des oreilles, coudes sous les épaules.", "D": "Droit, ni creusé ni arrondi.", "B": "Aligné, ni haut ni bas.", "G": "Sur le tapis épais."},
    "bird-dog": {"T": "Regard vers le sol, nuque longue.", "É": "Au-dessus des poignets, stables.", "D": "Plat, comme une table.", "B": "Horizontal, sans rotation.", "G": "Sous les hanches."},
    "chat": {"T": "Suit le mouvement, nuque détendue.", "É": "Au-dessus des poignets.", "D": "S'arrondit puis se creuse doucement.", "B": "Bascule avec le dos.", "G": "Sous les hanches."},
    "hanches-etir": {"T": "Regard devant.", "É": "Bas et relâchés.", "D": "Droit, buste haut.", "B": "Avance doucement, légèrement basculé vers l'arrière.", "G": "Genou avant au-dessus de la cheville ; genou arrière sur le coussin.", "P": "Pied avant à plat."},
}

LETTERS = [("T", "Tête", "Dans le prolongement de la colonne, regard devant (ou vers le plafond ou le sol selon la position), menton légèrement rentré."),
           ("É", "Épaules", "Basses, loin des oreilles, relâchées."),
           ("D", "Dos", "Long et naturel, sans creux ni arrondi forcé (sauf pour l'étirement du chat)."),
           ("B", "Bassin", "Stable et à niveau. Il ne bascule que dans les exercices qui le demandent."),
           ("G", "Genoux", "Alignés avec les pieds. Jamais verrouillés brutalement."),
           ("P", "Pieds", "À plat, écartés de la largeur du bassin, orteils vers l'avant.")]

CAMNOTE = {
    "Face": "Caméra en face, à 2,5 m. Objectif à hauteur de poitrine (debout ou assis) ou posée au sol à hauteur du tapis (allongé).",
    "Profil": "Caméra sur le côté droit du démonstrateur, perpendiculaire, à la même distance. Corps entier, 30 cm de marge au-dessus de la tête et sous les pieds.",
    "3/4": "Caméra à 45° côté droit, à 2,5 m. Sert à voir à la fois l'alignement des genoux et le recul des hanches.",
    "Dessus": "Caméra au-dessus du démonstrateur, sur trépied, à 1,5 m, objectif vers le bas.",
}

def minutes_per_person(item):
    return len(item["angles"]) * 6   # 3 versions (principale, douce, soutenue) x 2 min par angle : estimation

def body_svg(small=False):
    w = 150 if small else 210
    return ('<svg viewBox="0 0 210 330" width="%d" role="img" aria-label="Code posture : tête, épaules, dos, bassin, genoux, pieds">' % w +
        '<g fill="#E4E8F5" stroke="#8A93B8" stroke-width="2"><circle cx="105" cy="40" r="22"/><rect x="75" y="68" width="60" height="120" rx="28"/><rect x="42" y="78" width="24" height="100" rx="12"/><rect x="144" y="78" width="24" height="100" rx="12"/><rect x="77" y="186" width="26" height="124" rx="13"/><rect x="107" y="186" width="26" height="124" rx="13"/></g>' +
        '<g font-family="Inter,Arial,sans-serif" font-weight="700" font-size="15" text-anchor="middle" fill="#fff">'
        '<circle cx="180" cy="40" r="15" fill="#3B3F8F"/><text x="180" y="45">T</text><path d="M127 40H165" stroke="#3B3F8F" stroke-width="2"/>'
        '<circle cx="30" cy="84" r="15" fill="#3B3F8F"/><text x="30" y="89">É</text><path d="M45 84H76" stroke="#3B3F8F" stroke-width="2"/>'
        '<circle cx="180" cy="120" r="15" fill="#3B3F8F"/><text x="180" y="125">D</text><path d="M135 120H165" stroke="#3B3F8F" stroke-width="2"/>'
        '<circle cx="30" cy="186" r="15" fill="#3B3F8F"/><text x="30" y="191">B</text><path d="M45 186H80" stroke="#3B3F8F" stroke-width="2"/>'
        '<circle cx="180" cy="248" r="15" fill="#3B3F8F"/><text x="180" y="253">G</text><path d="M133 248H165" stroke="#3B3F8F" stroke-width="2"/>'
        '<circle cx="30" cy="310" r="15" fill="#3B3F8F"/><text x="30" y="315">P</text><path d="M45 310H80" stroke="#3B3F8F" stroke-width="2"/></g></svg>')

def cam_svg():
    return ('<svg viewBox="0 0 520 300" width="100%" role="img" aria-label="Positions de la caméra autour du démonstrateur" font-family="Inter,Arial,sans-serif">'
        '<rect width="520" height="300" fill="#F3F5FA" rx="12"/>'
        '<circle cx="260" cy="130" r="22" fill="#E4E8F5" stroke="#3B3F8F" stroke-width="3"/><path d="M260 130V104" stroke="#3B3F8F" stroke-width="4"/><path d="M252 112L260 100L268 112" fill="none" stroke="#3B3F8F" stroke-width="4"/>'
        '<text x="260" y="176" text-anchor="middle" font-size="13" fill="#566080">démonstrateur (il regarde vers le haut de la page)</text>'
        '<g fill="#F2784B" stroke="#1A2036" stroke-width="2"><rect x="238" y="236" width="44" height="28" rx="6"/><rect x="420" y="116" width="44" height="28" rx="6"/><rect x="238" y="22" width="44" height="28" rx="6" fill="#fff"/><rect x="394" y="204" width="44" height="28" rx="6"/></g>'
        '<g font-size="14" font-weight="700" fill="#1A2036" text-anchor="middle"><text x="260" y="256">FACE</text><text x="442" y="136">PROFIL</text><text x="260" y="42">DESSUS</text><text x="416" y="224">3/4</text></g>'
        '<g font-size="12" fill="#566080" text-anchor="middle"><text x="260" y="284">2,5 m, hauteur poitrine</text><text x="442" y="160">côté droit, 2,5 m</text><text x="416" y="248">45°, côté droit</text><text x="360" y="42">trépied à 1,5 m, vers le bas</text></g></svg>')

CSS = """
@page{size:A4;margin:14mm 14mm 16mm}
*{box-sizing:border-box}
body{font-family:Inter,Carlito,Arial,sans-serif;color:#1A2036;font-size:10.5pt;line-height:1.45;margin:0}
h1,h2,h3{margin:0;line-height:1.1}
h1{font-size:30pt;letter-spacing:-.02em}h2{font-size:17pt}h3{font-size:12pt}
p{margin:0}
.page{page-break-after:always;display:flex;flex-direction:column;gap:9pt;min-height:262mm}
.page:last-child{page-break-after:auto}
.kick{font-size:8.5pt;letter-spacing:.12em;text-transform:uppercase;color:#566080;font-weight:600}
.muted{color:#566080}.small{font-size:9pt}
.box{border:1px solid #D3D9E8;border-radius:8px;padding:8pt 10pt;background:#fff}
.soft{background:#F3F5FA}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:8pt}
.tag{display:inline-block;background:#E4E8F5;border-radius:99px;padding:1pt 8pt;font-size:9pt;margin-right:3pt}
table{border-collapse:collapse;width:100%;font-size:9.5pt}
th,td{border-bottom:1px solid #D3D9E8;padding:4pt 5pt;text-align:left;vertical-align:top}
th{font-size:8pt;text-transform:uppercase;letter-spacing:.06em;color:#566080}
.cb{display:inline-block;width:11pt;height:11pt;border:1.5px solid #1A2036;border-radius:2pt;vertical-align:middle}
.code{display:grid;grid-template-columns:20pt 1fr;gap:4pt 8pt;align-items:start;font-size:9.5pt}
.code b.l{display:grid;place-items:center;width:18pt;height:18pt;border-radius:50%;background:#3B3F8F;color:#fff;font-size:9pt}
.code b.off{background:#D3D9E8;color:#566080}
.head{display:flex;justify-content:space-between;align-items:flex-start;gap:10pt;border-bottom:3px solid #F2784B;padding-bottom:6pt}
.num{font-size:26pt;font-weight:800;color:#F2784B;line-height:1}
.bigcode{font-size:15pt;font-weight:800;letter-spacing:.2em;color:#3B3F8F}
.order td,.order th{padding:2.5pt 4pt;font-size:9pt}
.foot{margin-top:auto;font-size:8pt;color:#566080;display:flex;justify-content:space-between}
"""

def page_exercise(n, g, item):
    i = item["id"]
    code_rows = ""
    for L, name, rule in LETTERS:
        if L in CODE[i]:
            code_rows += '<b class="l">%s</b><div><b>%s</b> : %s</div>' % (L, name, E(CODE[i][L]))
        else:
            code_rows += '<b class="l off">%s</b><div class="muted">%s : pas critique ici.</div>' % (L, name)
    angle_notes = "".join('<p class="small"><b>%s</b> : %s</p>' % (a, E(CAMNOTE.get(a, ""))) for a in item["angles"])
    boxes = "".join('<td>%s</td>' % '<span class="cb"></span>' for _ in item["angles"])
    angle_heads = "".join("<th>%s</th>" % a for a in item["angles"])
    rows = ""
    for who in ("Femme", "Homme"):
        rows += "<tr><td><b>%s</b></td>%s</tr>" % (who, boxes)
    zones = ", ".join(item["zones"]) if item["zones"] else "aucune zone sensible"
    return ('<section class="page"><div class="head"><div><div class="kick">Exercice %d sur 19 · Groupe %s</div><h2>%s</h2><p class="muted small">%s · %s</p></div><div class="num">%d</div></div>' % (n, g[0], E(item["fr"]), E(item["en"]), E(item["pt"]), n) +
        '<div class="box soft"><b>Position :</b> %s</div>' % E(POSITION[i]) +
        '<div class="grid2"><div class="box"><h3>Le geste</h3><p>%s</p><p class="small muted" style="margin-top:4pt">Texte de la voix off, en français.</p></div>' % E(item["s"]["fr"]) +
        '<div class="box"><h3>À filmer</h3><p>%s</p><p class="small" style="margin-top:4pt"><b>Dans l\'application :</b> de 20 à 90 s selon le niveau.</p><p class="small"><b>Zones sensibles :</b> %s.</p></div></div>' % (E(TAKE[i]), E(zones)) +
        '<div class="grid2"><div class="box"><h3>Code posture</h3><div class="code">%s</div></div>' % code_rows +
        '<div><div class="box" style="margin-bottom:8pt"><h3>À surveiller</h3><p>%s</p></div>' % E(item["watch"]) +
        '<div class="box"><h3>Variantes à filmer</h3><p><b>Douce :</b> %s</p><p><b>Soutenue :</b> %s</p></div></div></div>' % (E(item["easy"]), E(item["hard"])) +
        '<div class="box"><h3>Angles de caméra</h3>%s</div>' % angle_notes +
        '<div class="box"><h3>Suivi (principale, douce, soutenue : cochez quand les trois sont filmées)</h3><table><tr><th>Personne</th>%s</tr>%s</table><p class="small muted" style="margin-top:4pt">Temps prévu sur place pour une personne : environ %d min (estimation : 3 versions × 2 min × %d angle(s)).</p></div>' % (angle_heads, rows, minutes_per_person(item), len(item["angles"])) +
        '<div class="foot"><span>Second Souffle · guide de tournage</span><span>Validation par un professionnel requise avant tournage</span></div></section>')

def build():
    total_angles = sum(len(ITEMS[i]["angles"]) for _, _, _, ids in GROUPS for i in ids)
    per_person = sum(minutes_per_person(ITEMS[i]) for _, _, _, ids in GROUPS for i in ids)
    total_min = per_person * 2 + len(GROUPS) * 10
    pages = []
    pages.append('<section class="page"><div style="margin-top:60mm"><div class="kick">Second Souffle · version 1</div><h1>Guide de tournage<br>et de posture</h1><p class="muted" style="margin-top:10pt;font-size:13pt">19 exercices, dans l\'ordre de tournage, avec les angles, la durée et le code posture.</p></div>'
        '<div class="box soft" style="margin-top:20mm"><b>Comment l\'utiliser</b><ol style="margin:6pt 0 0 14pt;padding:0"><li>Lisez les pages « Avant de commencer », « Code posture » et « Angles de caméra ».</li><li>Suivez l\'ordre indiqué : on change de matériel le moins possible.</li><li>Pour chaque exercice : lisez le geste, vérifiez le code posture, filmez les angles et les variantes, puis cochez.</li><li>Faites valider chaque geste par un professionnel avant de filmer.</li></ol></div>'
        '<div class="foot"><span>Second Souffle</span><span>%d angles × 2 personnes · environ %.0f h de tournage (estimation)</span></div></section>' % (total_angles, total_min / 60))
    pages.append('<section class="page"><h2>Avant de commencer</h2><div class="grid2"><div class="box"><h3>Personnes</h3><ul style="margin:4pt 0 0 14pt;padding:0"><li>Une femme et un homme, adultes, environ 45 à 60 ans.</li><li>Un coach diplômé sur place, avec le droit de refaire un plan.</li><li>Contrat de cession de droit à l\'image signé avant de filmer.</li></ul></div>'
        '<div class="box"><h3>Matériel</h3><ul style="margin:4pt 0 0 14pt;padding:0"><li>Tapis épais, coussin.</li><li>Chaise stable sans accoudoirs.</li><li>Deux élastiques (léger et fort), petite bouteille d\'eau.</li><li>Trépied, téléphone ou caméra, bonne lumière.</li></ul></div>'
        '<div class="box"><h3>Tenue</h3><ul style="margin:4pt 0 0 14pt;padding:0"><li>Aube : prune et corail. Ardoise : bleu pétrole et cuivre.</li><li>Vêtements ajustés pour voir les alignements.</li><li>Pas de vert citron ni de camouflage.</li></ul></div>'
        '<div class="box"><h3>Format des prises</h3><ul style="margin:4pt 0 0 14pt;padding:0"><li>Horizontal 16:9, haute définition.</li><li>3 répétitions propres + 1 lente, par angle et par version.</li><li>Boucle finale de 5 s, sans son.</li></ul></div></div>'
        '<div class="box soft"><b>Sécurité.</b> Chaque exercice, chaque variante et chaque point à surveiller doit être validé par un kinésithérapeute ou un enseignant en activité physique adaptée avant de filmer. Le démonstrateur arrête dès qu\'une douleur apparaît.</div>'
        '<div class="box"><h3>Temps prévu (estimation)</h3><p>Environ %d min pour une personne, soit %d min pour les deux, plus 10 min d\'installation par groupe. Au total, environ %.0f heures, pauses comprises à prévoir en plus.</p></div></section>' % (per_person, per_person * 2, total_min / 60))
    code_rows = "".join('<b class="l">%s</b><div><b>%s</b> : %s</div>' % (L, n, E(r)) for L, n, r in LETTERS)
    pages.append('<section class="page"><h2>Code posture : T É D B G P</h2><p class="muted">Six lettres à vérifier avant de lancer la prise. Chaque fiche d\'exercice précise ce que chaque lettre veut dire pour ce geste.</p><div class="grid2" style="align-items:center"><div style="text-align:center">%s</div><div class="code" style="gap:8pt 8pt">%s</div></div>' % (body_svg(), code_rows) +
        '<div class="box soft"><b>Avant chaque prise, dites à voix haute :</b> <span class="bigcode">T É D B G P</span><br><span class="small muted">Tête, Épaules, Dos, Bassin, Genoux, Pieds. Si une lettre est fausse, on recommence.</span></div>'
        '<div class="box"><h3>Les trois signes qui arrêtent la prise</h3><ol style="margin:4pt 0 0 14pt;padding:0"><li>Une douleur, même légère, chez le démonstrateur.</li><li>Un dos qui se creuse ou s\'arrondit sans que le geste le demande.</li><li>Un genou qui part vers l\'intérieur ou un souffle bloqué.</li></ol></div></section>')
    pages.append('<section class="page"><h2>Angles de caméra</h2><p class="muted">Gardez toujours la même distance et la même hauteur pour toute une série, afin que les vidéos se raccordent.</p>%s' % cam_svg() +
        '<div class="grid2">' + "".join('<div class="box"><h3>%s</h3><p class="small">%s</p></div>' % (a, E(t)) for a, t in CAMNOTE.items()) + '</div>'
        '<div class="box soft"><b>Cadrage :</b> corps entier, 30 cm de marge au-dessus de la tête et sous les pieds. Pour les plans serrés (cou, respiration), poitrine et tête seulement.</div></section>')
    order_rows = ""
    n = 0
    for g in GROUPS:
        order_rows += '<tr><td colspan="5" style="background:#E4E8F5"><b>Groupe %s · %s</b> <span class="small muted">%s</span></td></tr>' % (g[0], E(g[1]), E(g[2]))
        for i in g[3]:
            n += 1
            it = ITEMS[i]
            order_rows += "<tr><td>%d</td><td><b>%s</b></td><td>%s</td><td>%s</td><td>%d min</td></tr>" % (n, E(it["fr"]), " · ".join(it["angles"]), E(TAKE[i]), minutes_per_person(it))
    pages.append('<section class="page"><h2>Ordre de tournage</h2><p class="muted">Cinq groupes, pour changer de matériel le moins possible. Le temps est pour une personne, tous les angles et les trois versions.</p><table class="order"><tr><th>#</th><th>Exercice</th><th>Angles</th><th>À filmer</th><th>Temps</th></tr>%s</table></section>' % order_rows)
    n = 0
    for g in GROUPS:
        for i in g[3]:
            n += 1
            pages.append(page_exercise(n, g, ITEMS[i]))
    follow = ""
    n = 0
    for g in GROUPS:
        for i in g[3]:
            n += 1
            follow += "<tr><td>%d</td><td>%s</td>%s</tr>" % (n, E(ITEMS[i]["fr"]), "".join('<td><span class="cb"></span></td>' for _ in range(5)))
    pages.append('<section class="page"><h2>Fiche de suivi</h2><table><tr><th>#</th><th>Exercice</th><th>Filmé femme</th><th>Filmé homme</th><th>Voix FR</th><th>Voix EN</th><th>Voix PT</th></tr>%s</table></section>' % follow)
    return '<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>Guide de tournage et de posture</title><style>%s</style></head><body>%s</body></html>' % (CSS, "".join(pages))

out = Path(sys.argv[1] if len(sys.argv) > 1 else "guide-tournage.html")
out.write_text(build(), encoding="utf-8")
print("écrit", out)
