#!/usr/bin/env python3
"""Analyse « blow-up » d'une vidéo, étape par étape : pourquoi elle accroche (ou pas).

  python3 outils/analyser-video.py video.mp4 [autre.mp4 …] [--transcrire] [--langue fr] [--sortie analyses]

Pour chaque vidéo, écrit analyses/<nom>/ :
  rapport.md      les 9 étapes, mesures et score /100, avec une partie « à compléter » pour l'agent
  analyse.json    toutes les mesures
  hook.jpg        les 3 premières secondes (0 ; 0,5 ; 1 ; 1,5 ; 2 ; 3 s)
  planche.jpg     16 images réparties sur toute la vidéo
  texte-*.jpg     bandes où se trouvent d'habitude les sous-titres, 3 images/s (à lire pour reconstituer le texte)
  fin.jpg         les 15 % de fin (appel à l'action)
Avec plusieurs vidéos : analyses/comparatif.md.

Mesures faites avec FFmpeg (aucune dépendance Python obligatoire). --transcrire utilise faster-whisper
s'il est installé (pip install faster-whisper ; le modèle se télécharge au premier usage).
"""
import argparse
import json
import math
import re
import subprocess
import sys
from pathlib import Path


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def ffprobe(path):
    r = run(["ffprobe", "-v", "error", "-show_entries",
             "format=duration,size,bit_rate:stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels",
             "-of", "json", str(path)])
    if r.returncode:
        sys.exit(f"Lecture impossible : {path}\n{r.stderr.strip()}")
    return json.loads(r.stdout)


def fiche(path):
    """Étape 1 — fiche technique."""
    p = ffprobe(path)
    v = next((s for s in p["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in p["streams"] if s["codec_type"] == "audio"), None)
    if not v:
        sys.exit(f"Pas de piste vidéo : {path}")
    num, den = (int(x) for x in v["r_frame_rate"].split("/"))
    w, h = v["width"], v["height"]
    ratio = w / h
    fmt = "vertical 9:16" if ratio < 0.7 else "carré / 4:5" if ratio < 1.1 else "horizontal 16:9"
    duree = float(p["format"]["duration"])
    return {"duree": round(duree, 2), "largeur": w, "hauteur": h, "format": fmt, "vertical": ratio < 0.7,
            "ips": round(num / den, 2) if den else 0, "codec": v["codec_name"],
            "audio": bool(a), "audio_codec": a["codec_name"] if a else None,
            "taille_mo": round(int(p["format"]["size"]) / 1e6, 1)}


def plans(path, duree, seuil, seuil_visuel=0.06):
    """Étape 2 — découpage : coupes franches (changement de plan) et changements visuels.

    Sur une vidéo facecam, le visage reste à l'image : le rythme vient des incrustations (carte, clip, zoom).
    On garde donc deux niveaux : score de scène ≥ seuil (coupe franche) et ≥ seuil_visuel (tout changement
    visible), ces derniers fusionnés s'ils sont à moins de 0,4 s l'un de l'autre. Le rythme se juge sur le second.
    """
    r = run(["ffmpeg", "-hide_banner", "-i", str(path), "-an", "-vf",
             f"scale=160:-2,select='gt(scene,{seuil_visuel})',metadata=print", "-f", "null", "-"])
    evts, t = [], None
    for ligne in r.stderr.splitlines():
        m = re.search(r"pts_time:([\d.]+)", ligne)
        if m:
            t = float(m.group(1))
        m = re.search(r"scene_score=([\d.]+)", ligne)
        if m and t is not None and 0.2 < t < duree - 0.2:
            evts.append((round(t, 2), float(m.group(1))))
    coupes = sorted({t for t, sc in evts if sc >= seuil})
    changements = []
    for t, _ in sorted(evts):
        if not changements or t - changements[-1] >= 0.4:
            changements.append(t)

    def stats(instants):
        bornes = [0.0] + instants + [duree]
        durees = [round(b - a, 2) for a, b in zip(bornes, bornes[1:])]
        return bornes, durees

    bornes, durees = stats(changements)
    _, durees_coupes = stats(coupes)
    return {"coupes": coupes, "nb_coupes": len(coupes),
            "plan_moyen_coupes": round(sum(durees_coupes) / len(durees_coupes), 2),
            "changements": changements, "nb_plans": len(durees), "durees_plans": durees,
            "plan_moyen": round(sum(durees) / len(durees), 2),
            "plan_max": max(durees), "plan_max_debut": bornes[durees.index(max(durees))],
            "coupes_par_minute": round(len(changements) / duree * 60, 1) if duree else 0,
            "premiere_coupe": changements[0] if changements else None,
            "part_plans_courts": round(sum(d < 2 for d in durees) / len(durees) * 100)}


def audio(path, duree, a_audio):
    """Étape 4 — son : volume perçu, silences, part de la vidéo où l'on entend quelque chose."""
    if not a_audio:
        return {"present": False}
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vn", "-af",
             "ebur128=peak=true,silencedetect=n=-35dB:d=0.35", "-f", "null", "-"])
    err = r.stderr
    lufs = re.findall(r"I:\s+(-?[\d.]+) LUFS", err)
    tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", err)
    lra = re.findall(r"LRA:\s+([\d.]+) LU", err)
    debuts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", err)]
    fins = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    if len(fins) < len(debuts):
        fins.append(duree)
    silences = [(max(0.0, a), b) for a, b in zip(debuts, fins)]
    silence_total = sum(b - a for a, b in silences)
    premier_son = 0.0
    for a, b in silences:
        if a <= 0.05:
            premier_son = b
    longs = [(round(a, 1), round(b - a, 1)) for a, b in silences if b - a >= 1.0]
    return {"present": True, "lufs": float(lufs[-1]) if lufs else None, "crete_dbtp": float(tp[-1]) if tp else None,
            "plage_lu": float(lra[-1]) if lra else None, "premier_son": round(premier_son, 2),
            "part_son": round((1 - silence_total / duree) * 100) if duree else 0,
            "silences_longs": longs}


def images(path, duree, vertical, dossier):
    """Étapes 3, 5, 6, 8 — planches d'images à lire par l'agent."""
    def ff(*args):
        run(["ffmpeg", "-v", "error", "-y", *args])

    instants = [t for t in (0, 0.5, 1, 1.5, 2, 3) if t < duree]
    larg = 360 if vertical else 480
    entrees = sum([["-ss", str(t), "-i", str(path)] for t in instants], [])
    ff(*entrees, "-filter_complex",
       "".join(f"[{i}:v]scale={larg}:-2,trim=end_frame=1[h{i}];" for i in range(len(instants)))
       + "".join(f"[h{i}]" for i in range(len(instants))) + f"hstack=inputs={len(instants)}", "-frames:v", "1",
       str(dossier / "hook.jpg"))
    ff("-i", str(path), "-vf", f"fps=16/{duree:.3f},scale={larg // 1.5:.0f}:-2,tile=8x2", "-frames:v", "1",
       str(dossier / "planche.jpg"))
    # Bandes de texte : bas-milieu (sous-titres TikTok/Reels), haut (titres) ; 3 images/s, 36 par planche.
    bandes = {"milieu": "ih*0.55:ih*0.12", "bas": "ih*0.74:ih*0.14", "haut": "ih*0.06:ih*0.14"} if vertical else \
             {"bas": "ih*0.78:ih*0.16", "haut": "ih*0.04:ih*0.16"}
    fichiers = []
    for nom, pos in bandes.items():
        y, h = pos.split(":")
        n = math.ceil(duree * 3 / 36)
        for k in range(n):
            out = dossier / f"texte-{nom}-{k + 1}.jpg"
            ff("-ss", str(k * 12), "-t", "12", "-i", str(path), "-vf",
               f"fps=3,crop=iw:{h}:0:{y},scale=300:-2,tile=6x6", "-frames:v", "1", str(out))
            if out.exists():
                fichiers.append(out.name)
    debut_fin = duree * 0.85
    ff("-ss", f"{debut_fin:.2f}", "-i", str(path), "-vf",
       f"fps=6/{max(0.5, duree - debut_fin):.2f},scale={larg // 1.5:.0f}:-2,tile=6x1", "-frames:v", "1",
       str(dossier / "fin.jpg"))
    return fichiers


def transcrire(path, langue):
    """Étape 7 — transcription horodatée (facultative)."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return {"fait": False, "raison": "faster-whisper non installé (pip install faster-whisper)"}
    try:
        modele = WhisperModel("small", device="cpu", compute_type="int8")
        segs, info = modele.transcribe(str(path), language=langue, word_timestamps=True)
        segs = list(segs)
    except Exception as e:  # modèle non téléchargeable, fichier sans voix…
        return {"fait": False, "raison": f"transcription impossible : {e}"}
    mots = [w for s in segs for w in (s.words or [])]
    return {"fait": True, "langue": info.language,
            "segments": [{"debut": round(s.start, 2), "fin": round(s.end, 2), "texte": s.text.strip()} for s in segs],
            "mots": [{"debut": round(w.start, 2), "fin": round(w.end, 2), "mot": w.word.strip()} for w in mots],
            "nb_mots": len(mots),
            "premiers_mots": " ".join(w.word.strip() for w in mots if w.start < 3.0),
            "mots_par_seconde": round(len(mots) / (mots[-1].end - mots[0].start), 2) if len(mots) > 1 else 0}


# ---------------------------------------------------------------- score « blow-up »

def criteres(m):
    """Grille mesurable. Seuils pour un format court (Short / Reel / TikTok) ; plus souples en horizontal long."""
    f, p, a, t = m["fiche"], m["plans"], m["audio"], m.get("transcription", {})
    court = f["vertical"] or f["duree"] <= 90
    c = []

    def add(nom, pts, ok, valeur, regle):
        c.append({"critere": nom, "points": pts if ok else 0, "max": pts, "ok": bool(ok), "valeur": valeur, "regle": regle})

    if court:
        add("Durée", 10, 15 <= f["duree"] <= 60, f'{f["duree"]:.0f} s', "15–60 s pour un format court")
        add("Format vertical", 5, f["vertical"], f["format"], "9:16 pour Shorts / Reels / TikTok")
    else:
        add("Durée", 10, f["duree"] >= 480, f'{f["duree"] / 60:.1f} min', "≥ 8 min pour une vidéo longue (mid-roll)")
        add("Format", 5, not f["vertical"], f["format"], "16:9 pour une vidéo longue")
    pc = p["premiere_coupe"]
    add("Premier changement visuel", 15, pc is not None and pc <= 3.0, f"{pc:.1f} s" if pc else "aucun",
        "≤ 3 s : le hook doit bouger tout de suite")
    lim_moy, lim_max = (3.5, 6.0) if court else (6.0, 15.0)
    add("Rythme (un changement visuel toutes les…)", 15, p["plan_moyen"] <= lim_moy, f'{p["plan_moyen"]:.1f} s', f"≤ {lim_moy} s")
    add("Aucun moment figé trop long", 10, p["plan_max"] <= lim_max, f'{p["plan_max"]:.1f} s (à {p["plan_max_debut"]:.0f} s)',
        f"≤ {lim_max:.0f} s sans changement")
    if a.get("present"):
        add("Son dès le début", 10, a["premier_son"] <= 0.5, f'{a["premier_son"]:.1f} s', "≤ 0,5 s")
        lufs = a["lufs"]
        add("Volume adapté au mobile", 10, lufs is not None and -18 <= lufs <= -8, f"{lufs:.1f} LUFS" if lufs is not None else "?",
            "entre -18 et -8 LUFS (plateformes ≈ -14)")
        add("Peu de silences", 10, a["part_son"] >= 85 and not a["silences_longs"],
            f'{a["part_son"]} % sonore, {len(a["silences_longs"])} silence(s) ≥ 1 s', "≥ 85 % et aucun silence ≥ 1 s")
    else:
        add("Son", 30, False, "aucune piste audio", "une vidéo muette perd l'essentiel de la rétention")
    if t.get("fait"):
        mps = t["mots_par_seconde"]
        add("Débit de parole", 10, 2.0 <= mps <= 3.8, f"{mps} mots/s", "2 à 3,8 mots/s (énergique mais compréhensible)")
        add("Hook parlé", 5, len(t["premiers_mots"].split()) >= 4, f'« {t["premiers_mots"][:60]} »', "≥ 4 mots dans les 3 premières s")
    total = sum(x["points"] for x in c)
    maxi = sum(x["max"] for x in c)
    return c, round(total / maxi * 100)


def barre_rythme(m, largeur=60):
    """Frise des coupes : un trait par coupe, sur la durée de la vidéo."""
    d = m["fiche"]["duree"]
    ligne = ["─"] * largeur
    for t in m["plans"]["changements"]:
        ligne[min(largeur - 1, int(t / d * largeur))] = "┆"
    for t in m["plans"]["coupes"]:
        ligne[min(largeur - 1, int(t / d * largeur))] = "│"
    return "".join(ligne)


def rapport(nom, m, dossier):
    f, p, a, t = m["fiche"], m["plans"], m["audio"], m.get("transcription", {})
    c, score = m["criteres"], m["score"]
    L = [f"# Analyse « blow-up » — {nom}", "", f"**Score mesurable : {score}/100** (critères chiffrés ci-dessous ; "
         "le hook, le texte et l'appel à l'action sont jugés à l'étape 9).", "",
         "## 1. Fiche technique",
         f"{f['format']}, {f['largeur']}×{f['hauteur']}, {f['ips']} i/s, {f['duree']:.1f} s, {f['codec']}"
         f"{', audio ' + f['audio_codec'] if f['audio'] else ', sans audio'}, {f['taille_mo']} Mo.", "",
         "## 2. Découpage et rythme",
         f"- **Changements visuels** (coupe, incrustation, zoom) : {len(p['changements'])}, soit un toutes les "
         f"**{p['plan_moyen']} s** ({p['coupes_par_minute']}/min) ; {p['part_plans_courts']} % des segments durent moins de 2 s.",
         f"- **Coupes franches** (changement de plan) : {p['nb_coupes']}, plan moyen {p['plan_moyen_coupes']} s.",
         f"- Plus long moment sans changement : {p['plan_max']} s (à {p['plan_max_debut']:.1f} s).",
         f"- Frise (0 → {f['duree']:.0f} s ; │ coupe franche, ┆ autre changement) : `{barre_rythme(m)}`",
         f"- Instants des changements : {', '.join(f'{x:.1f}' for x in p['changements'][:40])}{' …' if len(p['changements']) > 40 else ''}", "",
         "## 3. Hook (0–3 s)",
         f"- Premier changement d'image : {p['premiere_coupe'] if p['premiere_coupe'] is not None else 'aucun'} s ; "
         f"premier son : {a.get('premier_son', '—')} s.",
         f"- Images : `hook.jpg` (0 ; 0,5 ; 1 ; 1,5 ; 2 ; 3 s)."
         + (f"\n- Premiers mots : « {t['premiers_mots']} »" if t.get("fait") else ""), "",
         "## 4. Son"]
    if a.get("present"):
        L += [f"- Volume perçu {a['lufs']} LUFS, crête {a['crete_dbtp']} dBTP, plage {a['plage_lu']} LU.",
              f"- Partie sonore : {a['part_son']} % ; silences ≥ 1 s : "
              + (", ".join(f"{s[1]} s à {s[0]} s" for s in a["silences_longs"]) or "aucun") + "."]
    else:
        L += ["- Aucune piste audio."]
    L += ["", "## 5. Images de toute la vidéo", "`planche.jpg` : 16 images réparties.", "",
          "## 6. Texte à l'écran", "Planches à lire (3 images/s) : " + ", ".join(f"`{x}`" for x in m["planches_texte"]) + ".", "",
          "## 7. Transcription"]
    if t.get("fait"):
        L += [f"{t['nb_mots']} mots, {t['mots_par_seconde']} mots/s.", ""] + \
             [f"- [{s['debut']:5.1f}–{s['fin']:5.1f}] {s['texte']}" for s in t["segments"]]
    else:
        L += [f"Non faite : {t.get('raison', 'option --transcrire non demandée')}. Reconstituer le texte depuis les planches de l'étape 6."]
    L += ["", "## 8. Fin et appel à l'action", "`fin.jpg` : les 15 % de fin.", "",
          "## Score mesurable", "| Critère | Mesure | Règle | Points |", "|---|---|---|---|"]
    L += [f"| {'✅' if x['ok'] else '❌'} {x['critere']} | {x['valeur']} | {x['regle']} | {x['points']}/{x['max']} |" for x in c]
    L += ["", "## 9. À compléter par l'agent `analyste-video` (après lecture des images)",
          "- **Hook** : phrase exacte, formule (`.claude/skills/yt-script/formules.md`, n / 21), promesse.",
          "- **Structure** : hook → preuve → corps → virage → CTA, avec les instants.",
          "- **Texte à l'écran** : style des sous-titres, mots mis en valeur, lisibilité.",
          "- **Appel à l'action** : lequel, à quel instant, mot à commenter.",
          "- **Pourquoi ça marche / ne marche pas** : 3 raisons, appuyées sur les mesures ci-dessus.",
          "- **À reprendre pour nos vidéos** : la mécanique (jamais le texte ni les images), et la recette pour `remotion/data/<slug>.json`."]
    (dossier / "rapport.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def slug(p):
    return re.sub(r"[^a-z0-9]+", "-", Path(p).stem.lower()).strip("-")[:40] or "video"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("videos", nargs="+")
    ap.add_argument("--transcrire", action="store_true")
    ap.add_argument("--langue", default=None, help="fr, en, pt… (défaut : détection automatique)")
    ap.add_argument("--sortie", default=str(Path(__file__).resolve().parent.parent / "analyses"))
    ap.add_argument("--seuil", type=float, default=0.3, help="score de scène d'une coupe franche (défaut 0,3)")
    ap.add_argument("--seuil-visuel", type=float, default=0.06, help="score d'un changement visuel (défaut 0,06 ; plus bas = plus sensible)")
    a = ap.parse_args()

    resultats = []
    for v in a.videos:
        nom = slug(v)
        dossier = Path(a.sortie) / nom
        dossier.mkdir(parents=True, exist_ok=True)
        print(f"▶ {v}")
        m = {"fichier": str(v)}
        print("  1/9 fiche technique");        m["fiche"] = fiche(v)
        print("  2/9 découpage en plans");     m["plans"] = plans(v, m["fiche"]["duree"], a.seuil, a.seuil_visuel)
        print("  3-6/9 images");               m["planches_texte"] = images(v, m["fiche"]["duree"], m["fiche"]["vertical"], dossier)
        print("  4/9 son");                    m["audio"] = audio(v, m["fiche"]["duree"], m["fiche"]["audio"])
        if a.transcrire:
            print("  7/9 transcription");      m["transcription"] = transcrire(v, a.langue)
        m["criteres"], m["score"] = criteres(m)
        (dossier / "analyse.json").write_text(json.dumps(m, indent=2, ensure_ascii=False), encoding="utf-8")
        rapport(nom, m, dossier)
        print(f"  ✔ {dossier / 'rapport.md'}  —  score mesurable {m['score']}/100")
        resultats.append((nom, m))

    if len(resultats) > 1:
        L = ["# Comparatif", "", "| Vidéo | Durée | Changement toutes les | Changements/min | 1er changement | Son à | LUFS | Score |",
             "|---|---|---|---|---|---|---|---|"]
        for nom, m in sorted(resultats, key=lambda x: -x[1]["score"]):
            f, p, au = m["fiche"], m["plans"], m["audio"]
            L.append(f"| {nom} | {f['duree']:.0f} s | {p['plan_moyen']} s | {p['coupes_par_minute']} | "
                     f"{p['premiere_coupe'] if p['premiere_coupe'] is not None else '—'} s | {au.get('premier_son', '—')} s | "
                     f"{au.get('lufs', '—')} | **{m['score']}** |")
        Path(a.sortie, "comparatif.md").write_text("\n".join(L) + "\n", encoding="utf-8")
        print(f"\n✔ {Path(a.sortie) / 'comparatif.md'}")


if __name__ == "__main__":
    main()
