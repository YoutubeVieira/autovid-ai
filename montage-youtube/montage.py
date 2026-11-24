#!/usr/bin/env python3
"""Montage automatique d'une vidéo YouTube 16:9 : voix off + clips Pexels / Pixabay + sous-titres.

Aucune dépendance Python : il faut seulement Python 3.9+ et ffmpeg (avec ffprobe).

Essai sans clé (faux clips de couleur, voix muette, vérifie tout le montage) :
    python montage.py videos/gym-over-60.json --demo
Vraie vidéo :
    python montage.py videos/gym-over-60.json
    python montage.py videos/gym-over-60.json --music ma-musique.mp3

Clés (variables d'environnement, jamais dans le code) :
    PEXELS_API_KEY    https://www.pexels.com/api/   (gratuite)
    PIXABAY_API_KEY   https://pixabay.com/api/docs/  (gratuite)
    GEMINI_API_KEY    https://aistudio.google.com/apikey  (voix off)
Il faut au moins une des deux clés de clips. Sans GEMINI_API_KEY, mettez vos propres fichiers de voix
dans le dossier <sortie>/voice (scene-01.wav, scene-02.wav... ou .mp3) : ils sont utilisés tels quels.

Réglages facultatifs :
    TTS_MODEL   modèle de voix (gemini-3.8-flash-tts par défaut)
    VOICE       voix Gemini (Sulafat par défaut : voix de femme chaleureuse)
    TTS_STYLE   consigne de ton placée devant le texte (vide par défaut)

Tout est mis en cache dans le dossier de sortie (build/<slug>) : relancer la commande reprend là où elle
s'est arrêtée. Supprimez un fichier (par exemple voice/scene-03.wav ou clips/choix.json) pour le refaire.

Produit dans build/<slug> :
    <slug>.mp4        la vidéo 1920x1080, 30 i/s, son normalisé à -14 LUFS (niveau YouTube)
    <slug>.srt        les sous-titres à envoyer à YouTube
    description.txt  titre, description avec chapitres, crédits des clips, tags
"""
import argparse, base64, json, math, os, re, shutil, subprocess, sys, time, urllib.error, urllib.parse, urllib.request, wave

W, H, FPS = 1920, 1080, 30
SHOT_MAX = 5.0          # durée maximale d'un plan (secondes) : un plan change toutes les 3 à 5 s
SHOT_MIN = 2.5
GAP = 0.45              # silence après chaque scène
LEAD_IN = 0.4           # silence avant la première phrase
UA = "montage-youtube/1.0"


def log(*a):
    print(*a, flush=True)


def run(cmd):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        sys.exit("ffmpeg a échoué :\n" + " ".join(cmd) + "\n" + p.stderr[-2000:])
    return p.stdout


def probe_duration(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", path])
    return float(out.strip())


def http_json(url, headers=None, body=None, tries=5):
    data = json.dumps(body).encode() if body is not None else None
    h = {"User-Agent": UA, **(headers or {})}
    if data:
        h["Content-Type"] = "application/json"
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h), timeout=120) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            msg = e.read().decode("utf8", "replace")[:300]
            if e.code == 429 or e.code >= 500:
                wait = 60 if e.code == 429 else 5 * 2 ** i
                log(f"  Service occupé (HTTP {e.code}), nouvelle tentative dans {wait} s...")
                time.sleep(wait)
                continue
            raise RuntimeError(f"HTTP {e.code} : {msg}")
        except urllib.error.URLError as e:
            log(f"  Réseau : {e.reason}, nouvelle tentative...")
            time.sleep(5 * 2 ** i)
    raise RuntimeError("Le service ne répond pas, relancez plus tard.")


def download(url, dest):
    tmp = dest + ".part"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=300) as r, open(tmp, "wb") as f:
        shutil.copyfileobj(r, f)
    os.replace(tmp, dest)


# ---------------------------------------------------------------- voix

def write_wav(path, pcm, rate):
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(pcm)


def gemini_tts(text, dest):
    key = os.environ["GEMINI_API_KEY"]
    model = os.environ.get("TTS_MODEL", "gemini-3.8-flash-tts")
    voice = os.environ.get("VOICE", "Sulafat")
    style = os.environ.get("TTS_STYLE", "")
    body = {"contents": [{"parts": [{"text": (style + " " + text).strip()}]}],
            "generationConfig": {"responseModalities": ["AUDIO"],
                                 "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{urllib.parse.quote(model)}:generateContent"
    j = http_json(url, {"x-goog-api-key": key}, body)
    parts = j.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    inline = next((p.get("inlineData") or p.get("inline_data") for p in parts if p.get("inlineData") or p.get("inline_data")), None)
    if not inline:
        raise RuntimeError("Réponse sans audio : " + json.dumps(j)[:300])
    raw = base64.b64decode(inline["data"])
    mime = inline.get("mimeType") or inline.get("mime_type") or ""
    if raw[:4] == b"RIFF":
        with open(dest, "wb") as f:
            f.write(raw)
    else:
        m = re.search(r"rate=(\d+)", mime)
        write_wav(dest, raw, int(m.group(1)) if m else 24000)


def make_voices(scenes, vdir, demo):
    os.makedirs(vdir, exist_ok=True)
    files = []
    for i, s in enumerate(scenes, 1):
        base = os.path.join(vdir, f"scene-{i:02d}")
        found = next((base + e for e in (".wav", ".mp3", ".m4a") if os.path.exists(base + e)), None)
        if not found:
            found = base + ".wav"
            if demo:
                secs = max(2.0, len(s["text"].split()) / 2.4)       # environ 145 mots par minute
                run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", f"{secs:.2f}", found])
            elif os.environ.get("GEMINI_API_KEY"):
                log(f"  Voix de la scène {i}/{len(scenes)}...")
                gemini_tts(s["text"], found)
                time.sleep(6)                                       # rester sous la limite par minute
            else:
                sys.exit(f"Pas de voix pour la scène {i} : donnez GEMINI_API_KEY ou déposez {base}.wav (ou .mp3).")
        files.append(found)
    return files


# ---------------------------------------------------------------- clips

def search_pexels(q):
    key = os.environ.get("PEXELS_API_KEY")
    if not key:
        return []
    url = "https://api.pexels.com/videos/search?" + urllib.parse.urlencode({"query": q, "orientation": "landscape", "per_page": 15})
    out = []
    for v in http_json(url, {"Authorization": key}).get("videos", []):
        files = [f for f in v.get("video_files", []) if f.get("file_type") == "video/mp4" and (f.get("width") or 0) > (f.get("height") or 1)]
        good = [f for f in files if 1280 <= f["width"] <= 2560] or files
        if not good:
            continue
        f = min(good, key=lambda f: abs(f["width"] - W))
        out.append({"id": f"pexels-{v['id']}", "url": f["link"], "duration": v.get("duration", 0), "width": f["width"],
                    "credit": f"{v.get('user', {}).get('name', 'Pexels')} (Pexels) {v.get('url', '')}"})
    return out


def search_pixabay(q):
    key = os.environ.get("PIXABAY_API_KEY")
    if not key:
        return []
    url = "https://pixabay.com/api/videos/?" + urllib.parse.urlencode({"key": key, "q": q, "per_page": 20, "safesearch": "true"})
    out = []
    for v in http_json(url).get("hits", []):
        vids = v.get("videos", {})
        f = next((vids[k] for k in ("large", "medium") if vids.get(k, {}).get("url") and vids[k]["width"] >= 1280
                  and vids[k]["width"] > vids[k]["height"]), None)
        if not f:
            continue
        out.append({"id": f"pixabay-{v['id']}", "url": f["url"], "duration": v.get("duration", 0), "width": f["width"],
                    "credit": f"{v.get('user', 'Pixabay')} (Pixabay) {v.get('pageURL', '')}"})
    return out


def pick_clips(data, cdir, demo):
    """Choisit, pour chaque scène, autant de clips différents qu'il faut de plans. Résultat mis en cache dans choix.json."""
    os.makedirs(cdir, exist_ok=True)
    plan_path = os.path.join(cdir, "choix.json")
    if os.path.exists(plan_path):
        return json.load(open(plan_path, encoding="utf8"))
    if not demo and not (os.environ.get("PEXELS_API_KEY") or os.environ.get("PIXABAY_API_KEY")):
        sys.exit("Il faut PEXELS_API_KEY ou PIXABAY_API_KEY (ou --demo pour un essai sans clé).")
    cache = {}

    def results(q):
        if q not in cache:
            if demo:
                cache[q] = [{"id": f"demo-{abs(hash(q + str(k))) % 10**8}", "url": "", "duration": 12, "width": W,
                             "credit": "clip de démonstration", "label": q} for k in range(4)]
            else:
                log(f"  Recherche : {q}")
                r = search_pexels(q) + search_pixabay(q)
                # alterner les deux banques, garder les clips assez longs en premier
                r.sort(key=lambda c: (c["duration"] < 6,))
                cache[q] = r
        return cache[q]

    used, plan = set(), []
    for s in data["scenes"]:
        chosen = []
        queries = s.get("queries", []) + data.get("fallback_queries", [])
        for q in queries:
            for c in results(q):
                if c["id"] not in used and len(chosen) < 8:
                    chosen.append(c); used.add(c["id"])
            if len(chosen) >= 8:
                break
        if not chosen:                                   # en dernier recours, réutiliser un clip déjà vu
            for q in queries:
                chosen = results(q)[:3]
                if chosen:
                    break
        if not chosen:
            sys.exit(f"Aucun clip trouvé pour la scène « {s.get('chapter', s['text'][:40])} ». Changez ses « queries ».")
        # entrelacer les recherches : premier clip de chaque requête d'abord
        plan.append(chosen)
    json.dump(plan, open(plan_path, "w", encoding="utf8"), indent=1, ensure_ascii=False)
    return plan


def fetch_clip(c, cdir):
    dest = os.path.join(cdir, c["id"] + ".mp4")
    if os.path.exists(dest):
        return dest
    if c["url"]:
        log(f"  Téléchargement {c['id']}...")
        download(c["url"], dest)
    else:                                                # clip de démonstration : fond coloré + mots de la recherche
        hue = int(c["id"].split("-")[1]) % 360
        label = c.get("label", "clip").replace(":", " ").replace("'", " ")
        run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
             f"gradients=s={W}x{H}:c0=0x{_hsl(hue)}:c1=0x203040:speed=0.02:d={c['duration']}:r={FPS}",
             "-vf", f"drawtext=text='{label}':fontcolor=white@0.85:fontsize=64:x=(w-text_w)/2:y=h*0.28",
             "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", dest])
    return dest


def _hsl(h):
    import colorsys
    r, g, b = colorsys.hls_to_rgb(h / 360, 0.45, 0.45)
    return "%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))


# ---------------------------------------------------------------- sous-titres

def chunks(text, maxlen=42):
    """Coupe le texte en blocs d'une ou deux lignes de 42 caractères au plus, en suivant la ponctuation."""
    sentences = re.split(r"(?<=[.?!])\s+", text.strip())
    out = []
    for s in sentences:
        parts = re.split(r"(?<=,)\s+", s) if len(s) > maxlen * 2 else [s]
        for p in parts:
            words, line = p.split(), ""
            for w in words:
                if line and len(line) + 1 + len(w) > maxlen * 2:
                    out.append(line); line = w
                else:
                    line = (line + " " + w).strip()
            if line:
                out.append(line)
    # éviter les blocs d'un seul mot : les coller au précédent
    merged = []
    for c in out:
        if merged and len(c.split()) == 1 and len(merged[-1]) + len(c) < maxlen * 2:
            merged[-1] += " " + c
        else:
            merged.append(c)
    return [wrap2(c, maxlen) for c in merged]


def wrap2(c, maxlen):
    if len(c) <= maxlen:
        return c
    words, best = c.split(), None
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        score = abs(len(a) - len(b))
        if best is None or score < best[0]:
            best = (score, a + "\n" + b)
    return best[1]


def ts(t, sep=","):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d}{sep}{ms % 1000:03d}"


def build_srt(scenes, starts, voice_durs, path):
    n, lines = 1, []
    for s, t0, vd in zip(scenes, starts, voice_durs):
        cs = chunks(s["text"])
        total = sum(len(c) for c in cs)
        t = t0
        for c in cs:
            d = vd * len(c) / total
            lines += [str(n), f"{ts(t)} --> {ts(t + d - 0.04)}", c, ""]
            n += 1; t += d
    open(path, "w", encoding="utf8").write("\n".join(lines))


# ---------------------------------------------------------------- montage

def render_shot(src, start, length, dest):
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},setsar=1,"
          f"eq=saturation=1.06:contrast=1.03,format=yuv420p")
    run(["ffmpeg", "-y", "-v", "error", "-stream_loop", "-1", "-ss", f"{start:.2f}", "-i", src, "-t", f"{length:.3f}",
         "-an", "-vf", vf, "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", dest])


def main():
    ap = argparse.ArgumentParser(description="Montage automatique d'une vidéo YouTube 16:9.")
    ap.add_argument("script", help="fichier JSON de la vidéo (voir videos/gym-over-60.json)")
    ap.add_argument("--demo", action="store_true", help="essai sans clé : faux clips, voix muette")
    ap.add_argument("--music", help="musique de fond (mp3/wav), baissée automatiquement sous la voix")
    ap.add_argument("--music-volume", type=float, default=0.18)
    ap.add_argument("--no-burn", action="store_true", help="ne pas incruster les sous-titres dans l'image")
    ap.add_argument("--out", help="dossier de sortie (build/<slug> par défaut)")
    a = ap.parse_args()

    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            sys.exit(f"{tool} est introuvable. Sous Windows : winget install Gyan.FFmpeg, puis rouvrez la fenêtre.")

    data = json.load(open(a.script, encoding="utf8"))
    scenes, slug = data["scenes"], data.get("slug", "video") + ("-demo" if a.demo else "")
    out = a.out or os.path.join(os.path.dirname(os.path.abspath(__file__)), "build", slug)
    os.makedirs(out, exist_ok=True)
    log(f"Vidéo : {data['title']}\nDossier : {out}\n")

    log("1/5 Voix off")
    vfiles = make_voices(scenes, os.path.join(out, "voice"), a.demo)
    vdurs = [probe_duration(f) for f in vfiles]
    sdurs = [vd + GAP for vd in vdurs]
    sdurs[0] += LEAD_IN
    starts, t = [], 0.0
    for i, d in enumerate(sdurs):
        starts.append(t + (LEAD_IN if i == 0 else 0)); t += d
    total = t
    log(f"  Durée totale : {int(total // 60)} min {int(total % 60)} s")

    log("2/5 Clips")
    plan = pick_clips(data, os.path.join(out, "clips"), a.demo)

    log("3/5 Plans")
    sdir = os.path.join(out, "shots"); os.makedirs(sdir, exist_ok=True)
    shot_list, credits = [], {}
    for i, (clips, sd) in enumerate(zip(plan, sdurs), 1):
        n = max(1, min(len(clips) if len(clips) > 1 else 99, math.ceil(sd / SHOT_MAX)))
        if sd / n < SHOT_MIN:
            n = max(1, int(sd // SHOT_MIN))
        for k in range(n):
            c = clips[k % len(clips)]
            length = sd / n
            dest = os.path.join(sdir, f"s{i:02d}-{k:02d}.mp4")
            src = fetch_clip(c, os.path.join(out, "clips"))
            credits[c["id"]] = c["credit"]
            if not os.path.exists(dest) or abs(probe_duration(dest) - length) > 0.1:
                cd = probe_duration(src)
                start = min(1.0, max(0.0, cd - length)) if cd > length + 0.5 else 0.0
                if k >= len(clips):                       # même clip réutilisé : prendre un autre passage
                    start = (start + length) % max(cd - length, 1)
                render_shot(src, start, length, dest)
            shot_list.append(dest)
        log(f"  Scène {i}/{len(plan)} : {n} plan(s), {sd:.1f} s")

    log("4/5 Assemblage")
    lst = os.path.join(out, "plans.txt")
    open(lst, "w", encoding="utf8").write("".join(f"file '{os.path.abspath(p)}'\n" for p in shot_list))
    video = os.path.join(out, "video-muette.mp4")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", video])

    # voix : chaque scène complétée de silence jusqu'à sa durée exacte, puis mises bout à bout
    vin, fl = [], []
    for i, (f, sd) in enumerate(zip(vfiles, sdurs)):
        vin += ["-i", f]
        delay = int(LEAD_IN * 1000) if i == 0 else 0
        fl.append(f"[{i}:a]aformat=sample_rates=48000:channel_layouts=mono,adelay={delay},apad,atrim=0:{sd:.3f}[v{i}]")
    fl.append("".join(f"[v{i}]" for i in range(len(vfiles))) + f"concat=n={len(vfiles)}:v=0:a=1[voice]")
    voice = os.path.join(out, "voix.wav")
    run(["ffmpeg", "-y", "-v", "error", *vin, "-filter_complex", ";".join(fl), "-map", "[voice]", voice])

    srt = os.path.join(out, data.get("slug", "video") + ".srt")
    build_srt(scenes, starts, vdurs, srt)

    log("5/5 Vidéo finale")
    final = os.path.join(out, slug + ".mp4")
    inputs = ["-i", video, "-i", voice]
    if a.music:
        inputs += ["-stream_loop", "-1", "-i", a.music]
        af = (f"[1:a]aformat=channel_layouts=stereo,asplit=2[vo][key];"
              f"[2:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={a.music_volume},atrim=0:{total:.3f},"
              f"afade=t=in:d=1.5,afade=t=out:st={max(0, total - 3):.3f}:d=3[mu];"
              f"[mu][key]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[duck];"
              f"[vo][duck]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    else:
        af = "[1:a]aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.5:LRA=11[a]"
    vf = f"fade=t=in:d=0.6,fade=t=out:st={max(0, total - 1.2):.3f}:d=1.2"
    if not a.no_burn:
        style = ("FontName=DejaVu Sans,FontSize=17,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
                 "BackColour=&H80000000,BorderStyle=1,Outline=2.2,Shadow=1,MarginV=38")
        sub = os.path.relpath(srt, out).replace("\\", "/")
        vf += f",subtitles='{sub}':force_style='{style}'"
    cwd = os.getcwd(); os.chdir(out)                      # chemin court pour le filtre subtitles (Windows)
    try:
        run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", af + f";[0:v]{vf}[v]", "-map", "[v]", "-map", "[a]",
             "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
             "-ar", "48000", "-t", f"{total:.3f}", "-movflags", "+faststart", final])
    finally:
        os.chdir(cwd)

    # description avec chapitres (YouTube : premier chapitre à 0:00, au moins 10 s chacun)
    chap = []
    for s, t0 in zip(scenes, [0.0] + [sum(sdurs[:i]) for i in range(1, len(sdurs))]):
        if s.get("chapter"):
            if chap and t0 - chap[-1][0] < 10:
                continue
            chap.append((t0, s["chapter"]))
    desc = [data["title"], "", data.get("description", ""), "", "Chapters"]
    desc += [f"{int(t0 // 60)}:{int(t0 % 60):02d} {name}" for t0, name in chap]
    desc += ["", "Stock footage"] + [f"- {c}" for c in credits.values()]
    desc += ["", "Tags : " + ", ".join(data.get("tags", []))]
    open(os.path.join(out, "description.txt"), "w", encoding="utf8").write("\n".join(desc) + "\n")

    log(f"\nTerminé : {final}\nSous-titres : {srt}\nDescription : {os.path.join(out, 'description.txt')}")


if __name__ == "__main__":
    main()
