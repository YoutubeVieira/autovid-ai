"""Moteur de réalisation TikTok: scénario annoté (émotions, rôles, qui parle) + timings de la voix -> découpage plan par plan.

    python3 realisation.py beats.json voice.json --out decoupage   # -> decoupage.json + decoupage.md

beats.json = liste de répliques, dans l'ordre de voice.json:
  {"role": "hook|contexte|montee|climax|payoff|cta", "emotion": "peur|surprise|joie|tristesse|colere|suspense|fierte|curiosite|amour|neutre",
   "qui": "narrateur" ou un prenom (dialogue), "sujet": personnage cadre pendant la voix off (optionnel), "mot_fort": "mot a souligner", "ecoute": "prenom qui reagit"}
Regles (voir docs/REALISATION.md): changement visuel au plus toutes les 2,5 s, jamais deux fois le meme plan de suite, hook = texte + mouvement des 0,15 s,
plan serre sur le pic emotionnel, le personnage qui parle est a l'ecran, plan de reaction apres une replique, punch-in sur le mot fort, silence avant le climax."""
import argparse
import json
import os

MAX_SHOT = 2.5          # secondes: au-dela on recoupe (changement visuel)
EMOTIONS = {            # plan, mouvement de camera, zoom (debut->fin), expression du visage, bruitage, effet
    "peur":      dict(plan="gros_plan", cam="push_in_rapide", zoom=(1.0, 1.25), face="scared", sfx="gasp", fx="shake"),
    "surprise":  dict(plan="gros_plan", cam="punch_in", zoom=(1.0, 1.18), face="surprise", sfx="oh_surprise", fx="flash"),
    "joie":      dict(plan="moyen", cam="orbite_legere", zoom=(1.0, 1.06), face="happy", sfx="giggle", fx=None),
    "tristesse": dict(plan="large", cam="pull_out_lent", zoom=(1.12, 1.0), face="sad", sfx=None, fx="desature"),
    "colere":    dict(plan="gros_plan", cam="contre_plongee_shake", zoom=(1.0, 1.15), face="angry", sfx="stomp", fx="shake"),
    "suspense":  dict(plan="moyen", cam="push_in_lent", zoom=(1.0, 1.1), face="smile", sfx="riser", fx=None),
    "fierte":    dict(plan="contre_plongee", cam="tilt_up", zoom=(1.0, 1.08), face="happy", sfx="level_up", fx="sparkle"),
    "curiosite": dict(plan="insert", cam="push_in_lent", zoom=(1.0, 1.12), face="surprise", sfx="tick", fx=None),
    "amour":     dict(plan="gros_plan", cam="hold_doux", zoom=(1.0, 1.05), face="love", sfx="sparkle", fx=None),
    "neutre":    dict(plan="moyen", cam="hold", zoom=(1.0, 1.04), face="smile", sfx=None, fx=None),
}
ROLE_SFX = {"hook": "whoosh_fast", "climax": "boom", "payoff": "fanfare", "cta": "pop"}
VARIETE = ["large", "moyen", "gros_plan", "insert", "contre_plongee"]   # rotation anti-repetition


def next_plan(prefere, last):
    if prefere != last:
        return prefere
    i = VARIETE.index(prefere) if prefere in VARIETE else 0
    return VARIETE[(i + 1) % len(VARIETE)]


def decouper(beats, cues):
    shots, last = [], None
    for k, (b, c) in enumerate(zip(beats, cues)):
        e = EMOTIONS.get(b.get("emotion", "neutre"), EMOTIONS["neutre"])
        t0, t1 = c["start"], c["end"]
        dur = t1 - t0
        parle = b.get("qui", "narrateur")
        n = max(1, round(dur / MAX_SHOT))                  # coupes pour garder un changement visuel regulier
        for i in range(n):
            a = t0 + dur * i / n
            z = t0 + dur * (i + 1) / n
            prefere = e["plan"] if i == 0 else VARIETE[(VARIETE.index(e["plan"]) + i) % len(VARIETE)] if e["plan"] in VARIETE else "moyen"
            if b.get("role") == "hook" and i == 0:
                prefere = "large"                          # le hook montre le decor / l'enjeu, puis on serre
            plan = next_plan(prefere, last)
            last = plan
            serre = plan in ("gros_plan", "insert")
            shots.append({"debut": round(a, 2), "fin": round(z, 2), "replique": k,
                          "plan": plan, "camera": e["cam"] if i == 0 else "push_in_lent",
                          "zoom": list(e["zoom"] if i == 0 else (1.0, 1.08 if serre else 1.04)),
                          "sujet": b.get("sujet") or (parle if parle != "narrateur" else "decor"),
                          "parle": parle != "narrateur" and i < n,
                          "visage": e["face"], "effet": e["fx"] if i == 0 else None,
                          "son": (ROLE_SFX.get(b.get("role")) or e["sfx"]) if i == 0 else None,
                          "texte_ecran": c["text"] if i == 0 else None,
                          "punch_in": {"mot": b["mot_fort"], "zoom": 1.2, "duree": 0.18} if b.get("mot_fort") and i == 0 else None})
        if b.get("ecoute") and k + 1 <= len(cues):
            fin = t1
            shots.append({"debut": round(fin - 0.7, 2), "fin": round(fin, 2), "replique": k, "plan": "reaction", "camera": "hold",
                          "zoom": [1.0, 1.1], "sujet": b["ecoute"], "parle": False, "visage": "surprise", "effet": None, "son": None,
                          "texte_ecran": None, "punch_in": None})
        if b.get("role") == "climax" and k > 0:
            shots[-1]["note"] = "silence 0,3 s de la voix avant la replique + riser; musique baisse (ducking)"
    return shots


def markdown(shots, beats):
    L = ["| t (s) | rôle | plan | caméra | zoom | sujet | visage | son | effet | note |", "|---|---|---|---|---|---|---|---|---|---|"]
    for s in shots:
        b = beats[s["replique"]]
        L.append(f"| {s['debut']:.1f}-{s['fin']:.1f} | {b.get('role', '')} | {s['plan']} | {s['camera']} | {s['zoom'][0]}→{s['zoom'][1]} | "
                 f"{s['sujet']}{' 🗣' if s['parle'] else ''} | {s['visage']} | {s['son'] or ''} | {s['effet'] or ''} | "
                 f"{('punch « ' + s['punch_in']['mot'] + ' »') if s['punch_in'] else ''}{s.get('note', '')} |")
    return "\n".join(L)


def audit(shots, duree):
    pb = []
    if shots and shots[0]["debut"] > 0.5:
        pb.append("hook trop tard (>0,5 s)")
    for a, b in zip(shots, shots[1:]):
        if a["plan"] == b["plan"]:
            pb.append(f"même plan deux fois à {b['debut']} s")
    if max(s["fin"] - s["debut"] for s in shots) > MAX_SHOT + 0.8:
        pb.append("plan trop long (>3,3 s)")
    return pb or ["OK"]


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("beats")
    ap.add_argument("voice")
    ap.add_argument("--out", default="decoupage")
    a = ap.parse_args()
    beats = json.load(open(a.beats, encoding="utf-8"))
    cues = json.load(open(a.voice, encoding="utf-8"))["cues"]
    assert len(beats) == len(cues), f"{len(beats)} répliques annotées pour {len(cues)} répliques de voix"
    sh = decouper(beats, cues)
    json.dump(sh, open(a.out + ".json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    open(a.out + ".md", "w", encoding="utf-8").write(markdown(sh, beats) + "\n\nAudit: " + "; ".join(audit(sh, cues[-1]["end"])) + "\n")
    print(f"{len(sh)} plans, {cues[-1]['end']:.1f} s | audit:", "; ".join(audit(sh, cues[-1]["end"])))
