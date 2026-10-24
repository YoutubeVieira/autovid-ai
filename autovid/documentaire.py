"""Documentaire YouTube automatique (style National Geographic, true crime responsable).

  python -m autovid documentaire "L'affaire X" -o doc_x/            recherche + script par Claude (clé requise)
  python -m autovid documentaire "L'affaire X" -o doc_x/ --plan plan.json [--images dossier/]

1. plan : recherche web et script par Claude (faits sourcés, angle enquête, pas de détails sanglants) ou plan.json ;
2. voix off (ta voix ElevenLabs, sinon Kokoro) ;
3. un visuel par plan : archive libre trouvée automatiquement (Wikimedia Commons, Library of Congress, Openverse,
   Internet Archive), ou carte date / lieu / citation, ou plan d'ambiance ; zoom lent (Ken Burns), étalonnage froid,
   grain, vignette ; source de chaque archive affichée en petit ;
4. nappe sombre, coups sourds aux chapitres, voix au-dessus, −14 LUFS ;
5. vidéo longue 16:9 + chapitres YouTube + sous-titres .srt + générique des crédits + shorts 9:16 + a_publier.md.
"""
import json
import random
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from . import gfx, sfx
from .long import LH, LW, _body, _wrap, chapters_text
from .media import FPS, info, run
from .render import match_loudness

GRADE = ("eq=saturation=0.6:contrast=1.12:brightness=-0.03,colorbalance=rs=-0.03:bs=0.06:bm=0.03,"
         "vignette=angle=PI/4.5,noise=alls=7:allf=t")
VENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "8M", "-bufsize", "16M", "-pix_fmt", "yuv420p",
        "-r", str(FPS), "-an"]   # débit plafonné : le grain ferait exploser la taille du fichier
ROUGE = (200, 40, 40)
GRIS = (175, 178, 172)
TXT = {   # textes à l'écran et description, selon la langue du public
    "fr": {"doc": "UN DOCUMENTAIRE", "chap": "CHAPITRE", "lieu": "LIEU", "source": "Source", "sources_img": "SOURCES DES IMAGES",
           "merci": "MERCI D'AVOIR REGARDÉ", "intro": "Intro", "chapitres": "Chapitres", "sources": "Sources",
           "archives": "Images d'archives (licences libres)",
           "mention": "Ce documentaire relate des faits jugés, à partir de sources publiques. Pensées aux victimes et à leurs proches.",
           "tags": "#documentaire #truecrime #histoire"},
    "pt": {"doc": "UM DOCUMENTÁRIO", "chap": "CAPÍTULO", "lieu": "LOCAL", "source": "Fonte", "sources_img": "FONTES DAS IMAGENS",
           "merci": "OBRIGADO POR ASSISTIR", "intro": "Introdução", "chapitres": "Capítulos", "sources": "Fontes",
           "archives": "Imagens de arquivo (licenças livres)",
           "mention": "Este documentário relata fatos julgados, com base em fontes públicas. Nosso respeito às vítimas e às "
                      "suas famílias.",
           "tags": "#documentario #truecrime #casoreal #historia"},
}


# --------------------------------------------------------------------------- cartes (PNG)

def _canvas():
    img = Image.new("RGB", (LW, LH), (10, 11, 12))
    px = np.array(img).astype(np.float32)
    yy, xx = np.mgrid[0:LH, 0:LW]
    glow = np.exp(-(((xx - LW / 2) / (LW * 0.6)) ** 2 + ((yy - LH / 2) / (LH * 0.7)) ** 2))
    px += glow[..., None] * np.array([14, 16, 18])
    return Image.fromarray(px.clip(0, 255).astype(np.uint8))


def _center(d, text, font, y, fill, stroke=0):
    w = d.textlength(text, font=font)
    d.text(((LW - w) / 2, y), text, font=font, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0))


def card_titre(path, kicker, titre, sous=""):
    img = _canvas()
    d = ImageDraw.Draw(img)
    size = 150
    while True:                                 # le titre entier, sur 3 lignes au plus
        f = ImageFont.truetype(gfx.ANTON, size)
        lines = _wrap(d, titre.upper(), f, LW - 300)
        if len(lines) <= 3 or size <= 70:
            break
        size -= 10
    step = int(size * 1.15)
    y0 = LH / 2 - len(lines) * step / 2 - 30
    for i, line in enumerate(lines):
        _center(d, line, f, y0 + i * step, (240, 240, 236))
    bar = y0 + len(lines) * step + 30
    d.rectangle((LW / 2 - 60, bar, LW / 2 + 60, bar + 6), fill=ROUGE)
    if sous:
        _center(d, sous, _body(36), bar + 40, GRIS)
    if kicker:
        _center(d, kicker.upper(), _body(34), y0 - 70, GRIS)
    img.save(path)


def card_date(path, legende, sous=""):
    img = _canvas()
    d = ImageDraw.Draw(img)
    _center(d, legende.upper(), ImageFont.truetype(gfx.ANTON, 170), 380, (240, 240, 236))
    d.rectangle((LW / 2 - 60, 600, LW / 2 + 60, 606), fill=ROUGE)
    if sous:
        for i, line in enumerate(_wrap(d, sous, _body(40), LW - 500)[:2]):
            _center(d, line, _body(40), 640 + i * 54, GRIS)
    img.save(path)


def card_citation(path, citation, source=""):
    img = _canvas()
    d = ImageDraw.Draw(img)
    f = _body(54)
    lines = _wrap(d, f"« {citation} »", f, LW - 480)[:5]
    y0 = LH / 2 - len(lines) * 38
    for i, line in enumerate(lines):
        _center(d, line, f, y0 + i * 76, (236, 236, 230))
    if source:
        _center(d, "— " + source, _body(32), y0 + len(lines) * 76 + 30, GRIS)
    img.save(path)


def overlay_png(path, legende="", credit="", lieu=False, mot_lieu="LIEU"):
    """Calque transparent : légende en bas à gauche (lieu, date), source de l'archive en bas à droite."""
    img = Image.new("RGBA", (LW, LH), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if legende:
        f = ImageFont.truetype(gfx.ANTON, 54)
        txt = legende.upper()
        d.rectangle((90, LH - 200, 90 + 10, LH - 120), fill=ROUGE + (255,))
        d.text((122, LH - 196), txt, font=f, fill=(245, 245, 240, 255), stroke_width=3, stroke_fill=(0, 0, 0, 200))
        if lieu:
            d.text((122, LH - 236), mot_lieu, font=_body(26), fill=GRIS + (255,))
    if credit:
        f = _body(22)
        w = d.textlength(credit, font=f)
        d.text((LW - w - 40, LH - 52), credit, font=f, fill=(210, 210, 205, 200), stroke_width=2, stroke_fill=(0, 0, 0, 160))
    img.save(path)


def ambiance_png(path, seed):
    """Plan d'ambiance de secours (aucune archive) : brume sombre et grain, rien d'inventé."""
    r = np.random.default_rng(seed)
    small = r.normal(0, 1, (27, 48)).astype(np.float32)
    import cv2
    fog = cv2.GaussianBlur(cv2.resize(small, (LW, LH), interpolation=cv2.INTER_CUBIC), (0, 0), 60)
    fog = (fog - fog.min()) / (np.ptp(fog) + 1e-6)
    base = np.stack([fog * 40 + 10, fog * 44 + 12, fog * 52 + 16], axis=-1)
    Image.fromarray(base.clip(0, 255).astype(np.uint8)).save(path)


# --------------------------------------------------------------------------- morceaux vidéo (muets)

def ken_burns(src_img, dur, out, overlay, seed):
    """Zoom lent sur une image fixe (Ken Burns), image entière sur fond flouté si elle n'est pas en 16:9."""
    rnd = random.Random(seed)
    frames = max(int(dur * FPS), 2)
    zin = rnd.random() < 0.6
    ax, ay = rnd.choice([(0.5, 0.5), (0.35, 0.4), (0.65, 0.45), (0.5, 0.3)])
    z = f"1+0.13*on/{frames}" if zin else f"1.13-0.13*on/{frames}"
    W2, H2 = LW * 3 // 2, LH * 3 // 2           # 1,5x suffit pour un zoom lent net, et rend 2 à 3 fois plus vite
    fc = (f"[0:v]split[a][b];[a]scale=480:270:force_original_aspect_ratio=increase,crop=480:270,gblur=sigma=10,"
          f"scale={W2}:{H2},eq=brightness=-0.25[bg];[b]scale={W2}:{H2}:force_original_aspect_ratio=decrease[fg];"
          f"[bg][fg]overlay=(W-w)/2:(H-h)/2,zoompan=z='{z}':x='(iw-iw/zoom)*{ax}':y='(ih-ih/zoom)*{ay}':"
          f"d={frames}:s={LW}x{LH}:fps={FPS},{GRADE}[m];[m][1:v]overlay=0:0,format=yuv420p[v]")
    run(["ffmpeg", "-y", "-v", "error", "-i", src_img, "-i", overlay, "-filter_complex", fc, "-map", "[v]",
         "-frames:v", str(frames), *VENC, out])


def film(src, dur, out, overlay):
    """Extrait de film d'archive, plein cadre 16:9 (fond flouté si besoin), même étalonnage."""
    fc = (f"[0:v]fps={FPS},split[a][b];[a]scale={LW}:{LH}:force_original_aspect_ratio=increase,crop={LW}:{LH},"
          f"gblur=sigma=30,eq=brightness=-0.25[bg];[b]scale={LW}:{LH}:force_original_aspect_ratio=decrease[fg];"
          f"[bg][fg]overlay=(W-w)/2:(H-h)/2,{GRADE}[m];[m][1:v]overlay=0:0,format=yuv420p[v]")
    start = min(2.0, max(float(info(src)["duration"]) - dur, 0) / 2)
    run(["ffmpeg", "-y", "-v", "error", "-stream_loop", "-1", "-ss", f"{start:.2f}", "-i", src, "-i", overlay,
         "-filter_complex", fc, "-map", "[v]", "-t", f"{dur:.3f}", *VENC, out])


# --------------------------------------------------------------------------- assemblage

def _segments(plan):
    """Liste ordonnée des morceaux : accroche, titre, puis par chapitre une carte et ses plans."""
    segs = [{"id": "accroche", "kind": "plan", "texte": plan["accroche"], "visuel": "ambiance",
             "requete": (plan["chapitres"][0]["plans"][0].get("requete") if plan["chapitres"] else "") or "night road",
             "legende": ""},
            {"id": "titre", "kind": "carte_titre", "titre": plan["titre"], "dur": 4.5}]
    for c, ch in enumerate(plan["chapitres"], 1):
        segs.append({"id": f"ch{c}", "kind": "carte_chapitre", "num": c, "titre": ch["titre"], "dur": 3.2})
        for p, pl in enumerate(ch["plans"]):
            segs.append({"id": f"c{c}p{p}", "kind": "plan", "chapitre": c, **pl})
    return segs


def documentaire(sujet, out_dir, workdir, plan=None, images=None, tts="auto", voice_id=None, handle="", minutes=8,
                 max_shorts=3, video=True, langue="fr"):
    """langue : « fr » ou « pt » (portugais du Brésil : script, voix, textes à l'écran et description)."""
    T = TXT[langue]
    from . import narration as nar
    from .archives import Archives
    out = Path(out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    work = Path(workdir)
    work.mkdir(parents=True, exist_ok=True)

    print("1/6 plan du documentaire")
    if plan:
        plan = json.loads(Path(plan).read_text(encoding="utf-8")) if not isinstance(plan, dict) else plan
    else:
        from .ai import doc_plan
        plan = doc_plan(sujet, minutes, langue)
        if not plan:
            raise SystemExit("Pas de plan : il faut une clé Anthropic (recherche + script automatiques) ou --plan plan.json")
    (out / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    segs = _segments(plan)
    print(f"   « {plan['titre']} » : {len(plan['chapitres'])} chapitres, "
          f"{sum(1 for s in segs if s['kind'] == 'plan')} plans")

    print("2/6 voix off")
    voiced = [s for s in segs if s["kind"] == "plan"]
    for s in voiced:
        s["fr"] = s["texte"]
    engine = nar.voice_segments(voiced, voice_id or nar.default_voice(), tts, langue)
    print(f"   moteur : {engine or 'aucun (durées estimées, vidéo sans voix)'}")
    for s in voiced:
        s["dur"] = max(s["dur"] + 0.7, 3.0)

    print("3/6 archives libres (licence vérifiée) + visuels")
    from .ai import has_credentials, image_pertinente
    check = image_pertinente if has_credentials() else None   # avec une clé : Claude regarde chaque archive retenue
    print("   vérification des images par Claude : " + ("oui" if check else "non (pas de clé), filtre par mots-clés"))
    arch = Archives(work / "archives", local=images, video=video, verifier=check)
    for k, s in enumerate(segs):
        if s["kind"] != "plan":
            continue
        want = {"film": "video"}.get(s["visuel"], "image")
        if s["visuel"] in ("archive", "film", "ambiance", "lieu"):
            s["media"] = arch.find(s.get("requete") or s["texte"][:60], want)
        print(f"   {s['id']:<8} {s['visuel']:<9} {s.get('requete', '')[:40]:<40} → "
              f"{(s.get('media') or {}).get('credit', {}).get('source', 'carte' if s['visuel'] in ('date', 'citation') else 'ambiance')}")
    arch.save_credits(out / "credits.json")

    print("4/6 montage image")
    parts, t, marks, starts = [], 0.0, [], {}
    for k, s in enumerate(segs):
        seg_out = str(work / f"s{k:03d}.mp4")
        png = str(work / f"s{k:03d}.png")
        ov = str(work / f"s{k:03d}_ov.png")
        if s["kind"] == "carte_titre":
            card_titre(png, "", s["titre"], T["doc"] + " " + (handle or "").upper())
            overlay_png(ov)
            ken_burns(png, s["dur"], seg_out, ov, k)
        elif s["kind"] == "carte_chapitre":
            marks.append((t, f"{s['num']}. {s['titre']}"))
            card_titre(png, f"{T['chap']} {s['num']}", s["titre"])
            overlay_png(ov)
            ken_burns(png, s["dur"], seg_out, ov, k)
        else:
            m = s.get("media")
            credit = ""
            if m and m["credit"]["source"] != "local":
                c = m["credit"]
                credit = f"{T['source']} : {c['source']} · {c['auteur'][:40]} · {c['licence']}"
            overlay_png(ov, s.get("legende") if s["visuel"] in ("lieu", "archive", "film") else "", credit,
                        lieu=s["visuel"] == "lieu", mot_lieu=T["lieu"])
            if s["visuel"] == "date":
                card_date(png, s.get("legende") or "")
                ken_burns(png, s["dur"], seg_out, ov, k)
            elif s["visuel"] == "citation":
                card_citation(png, s.get("legende") or s["texte"], "")
                ken_burns(png, s["dur"], seg_out, ov, k)
            elif m and m["type"] == "video":
                film(m["chemin"], s["dur"], seg_out, ov)
            elif m:
                ken_burns(m["chemin"], s["dur"], seg_out, ov, k)
            else:
                ambiance_png(png, k)
                ken_burns(png, s["dur"], seg_out, ov, k)
        starts[s["id"]] = t
        parts.append(seg_out)
        t += s["dur"]
    # générique : crédits des archives (obligatoire pour les licences CC BY)
    cred = arch.credits
    pages = [cred[i:i + 8] for i in range(0, len(cred), 8)] or [[]]
    for j, page in enumerate(pages):
        img = _canvas()
        d = ImageDraw.Draw(img)
        _center(d, T["sources_img"] if page else T["merci"], ImageFont.truetype(gfx.ANTON, 70), 120,
                (240, 240, 236))
        for i, c in enumerate(page):
            line = f"{c['titre'][:60]} · {c['auteur'][:30]} · {c['licence']} · {c['source']}"
            _center(d, line, _body(28), 260 + i * 70, GRIS)
        if handle:
            _center(d, handle, _body(34), LH - 120, GRIS)
        png = str(work / f"gen{j}.png")
        img.save(png)
        ov = str(work / "vide.png")
        overlay_png(ov)
        seg_out = str(work / f"gen{j}.mp4")
        ken_burns(png, 5.0, seg_out, ov, 1000 + j)
        parts.append(seg_out)
        t += 5.0
    total = t
    lst = work / "parts.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in parts))
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", work / "image.mp4"])

    print("5/6 son : voix, nappe sombre, coups aux chapitres")
    sr = sfx.SR
    n = int(total * sr) + sr
    mus = sfx.ambiance_sombre(n / sr)[:n] * 0.55
    voice = np.zeros((n, 2))
    duck = np.ones(n)
    fx = np.zeros((n, 2))
    for s in voiced:
        if s.get("audio") is None:
            continue
        i = int((starts[s["id"]] + 0.3) * sr)
        a = s["audio"][: max(n - i, 0)]
        voice[i: i + len(a)] += a
        duck[i: i + len(a)] = 0.45
    for s in segs:
        if s["kind"] in ("carte_titre", "carte_chapitre"):
            h = sfx.tension_hit()
            i = int(starts[s["id"]] * sr)
            h = h[: max(n - i, 0)]
            fx[i: i + len(h)] += h * 0.8
    duck = np.convolve(duck, np.ones(sr // 3) / (sr // 3), mode="same")
    if np.abs(voice).max() > 0:
        voice *= 0.85 / np.abs(voice).max()
    mix = mus * duck[:, None] + voice * 1.3 + fx * 0.6
    sfx.write_wav(work / "son.wav", mix / (np.abs(mix).max() or 1) * 0.9)
    run(["ffmpeg", "-y", "-v", "error", "-i", work / "image.mp4", "-i", work / "son.wav", "-map", "0:v", "-map", "1:a",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", work / "brut.mp4"])
    long_out = out / "documentaire.mp4"
    match_loudness(str(work / "brut.mp4"), str(long_out), -14)

    print("6/6 chapitres, sous-titres, shorts, plan de publication")
    marks = [(0.0, T["intro"])] + marks
    marks = [m for i, m in enumerate(marks) if i + 1 >= len(marks) or marks[i + 1][0] - m[0] >= 10]
    chap = chapters_text(marks)
    (out / "chapitres.txt").write_text(chap + "\n", encoding="utf-8")
    words = []
    for s in voiced:
        words += [{**w, "start": w["start"] + starts[s["id"]] + 0.3, "end": w["end"] + starts[s["id"]] + 0.3}
                  for w in s.get("words", [])]
    nar.write_srt(nar.cues_from_words(words), out / "documentaire.fr.srt")
    shorts = make_shorts(long_out, segs, starts, words, out / "shorts", work, max_shorts)
    write_plan(out, plan, chap, arch.credits, shorts, handle, T)
    print(f"→ {out}  ({total / 60:.1f} min, {len(arch.credits)} archives créditées)")
    return str(out)


def make_shorts(long_out, segs, starts, words, folder, work, n):
    """Shorts 9:16 : l'accroche puis le début de chaque chapitre (≤ 45 s), sous-titres mot par mot incrustés."""
    import shutil
    from .talk import captions_ass
    folder.mkdir(parents=True, exist_ok=True)
    shutil.copytree(Path(__file__).parent / "fonts", work / "fonts", dirs_exist_ok=True)
    cuts = [("accroche", 0.0, starts.get("titre", 15))]
    for s in segs:
        if s["kind"] == "carte_chapitre" and len(cuts) < n:
            nxt = [starts[x["id"]] for x in segs if x["kind"] == "carte_chapitre" and starts[x["id"]] > starts[s["id"]]]
            end = min(starts[s["id"]] + 45, nxt[0] if nxt else starts[s["id"]] + 45)
            cuts.append((f"chapitre_{s['num']}", starts[s["id"]], end))
    out = []
    for name, a, b in cuts[:n]:
        ws = [{**w, "start": w["start"] - a, "end": w["end"] - a} for w in words if a <= w["start"] < b]
        ass = work / f"short_{name}.ass"
        captions_ass(ws, ass, y=1500, max_words=3)
        path = folder / f"short_{name}.mp4"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{a:.2f}", "-to", f"{b:.2f}", "-i", str(long_out),
                        "-filter_complex",
                        "[0:v]split[x][y];[x]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
                        "gblur=sigma=40,eq=brightness=-0.3[bg];[y]scale=1080:-2[fg];[bg][fg]overlay=0:(H-h)/2-120,"
                        f"ass={ass.name}:fontsdir=fonts[v]", "-map", "[v]", "-map", "0:a", "-c:v", "libx264",
                        "-crf", "20", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(path)],
                       check=True, cwd=work)
        out.append(str(path.relative_to(folder.parent)))
    return out


def write_plan(out, plan, chap, credits, shorts, handle, T=TXT["fr"]):
    srcs = "\n".join(f"- {s['titre']} : {s['url']}" for s in plan.get("sources", []))
    creds = "\n".join(f"- {c['titre']} · {c['auteur']} · {c['licence']} · {c['page']}" for c in credits) or "- (aucune)"
    desc = (f"{plan['accroche']}\n\n{T['chapitres']}:\n{chap}\n\n{T['sources']}:\n{srcs}\n\n{T['archives']}:\n"
            f"{creds}\n\n{T['mention']}\n\n{handle}\n\n{T['tags']}")
    lines = ["# À publier", "", f"**Titre :** {plan['titre']}", "", "**Description :**", "", "```", desc, "```", "",
             "## Shorts", ""] + [f"- `{s}`" for s in shorts] + [
             "", "## Vérifications avant publication", "",
             "- Relire chaque fait avec les sources ci-dessus (l'IA peut se tromper).",
             "- YouTube Studio : catégorie « Éducation », pas de miniature choquante, ne pas cocher « contenu pour enfants ».",
             "- Si des images ont été générées par IA : cocher « contenu modifié ou synthétique ».",
             "- Les crédits des images CC BY doivent rester dans la description et le générique."]
    (out / "a_publier.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
