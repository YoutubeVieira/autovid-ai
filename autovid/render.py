"""Rendu d'un brief résolu (voir planner.resolve) en MP4 vertical 1080x1920 30 i/s."""
import shutil
from pathlib import Path

from .media import FPS, H, W, info, run
from .styles import get_style

FONTS_DIR = Path(__file__).parent / "fonts"


# ---------------------------------------------------------------- segments vidéo

def _layout_filter(layout, style):
    cover = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}"
    if layout == "cover":
        return cover
    fit = f"scale={W}:{H}:force_original_aspect_ratio=decrease"
    off = style.get("fit_offset_y", 0)
    if layout == "letterbox":
        return f"{fit},pad={W}:{H}:(ow-iw)/2:(oh-ih)/2+{off}:black"
    if layout == "fit_blur":
        return (f"split[bg0][fg0];[bg0]{cover},gblur=sigma=40,eq=brightness=-0.12[bg];"
                f"[fg0]{fit}[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2+{off}")
    raise ValueError(f"Mise en page inconnue : {layout}")


def _zoom_filter(zoom, dur, impact):
    if not zoom:
        return None
    t = "(in/%d)" % FPS
    if zoom == "punch":     # coup de zoom bref centré sur l'impact
        z = f"1+0.12*exp(-pow(({t}-{impact:.3f})*7\\,2))"
    elif zoom == "push":    # lente poussée avant
        z = f"1+0.08*{t}/{max(dur, 0.1):.3f}"
    else:
        raise ValueError(f"Zoom inconnu : {zoom}")
    return (f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS}")


def render_segment(seg, style, out_path, keep_audio):
    """Découpe, recadre, étalonne et (optionnellement) accélère/ralentit un plan."""
    dur = seg["duration"]
    speed = seg.get("speed", 1.0)
    src_dur = dur * speed
    chain = [f"[0:v]fps={FPS},setpts=(PTS-STARTPTS)/{speed}", _layout_filter(seg["layout"], style)]
    zoom = _zoom_filter(seg.get("zoom"), dur, seg.get("impact", dur / 2))
    if zoom:
        chain.append(zoom)
    if style.get("grade"):
        chain.append(style["grade"])
    if seg.get("transition") == "flash":
        chain.append("fade=t=in:st=0:d=0.15:color=white")
    elif seg.get("transition") == "fade":
        chain.append("fade=t=in:st=0:d=0.25")
    chain.append(f"trim=duration={dur:.3f},setsar=1,format=yuv420p[v]")
    vf = ",".join(chain)

    clip_info = info(seg["clip"])
    use_clip_audio = keep_audio and clip_info["has_audio"] and 0.5 <= speed <= 2.0
    if use_clip_audio:
        af = f"[0:a]atrim=duration={src_dur:.3f},asetpts=PTS-STARTPTS,atempo={speed},aresample=44100,apad,atrim=duration={dur:.3f}[a]"
        inputs = ["-ss", f"{seg['start']:.3f}", "-t", f"{src_dur + 0.5:.3f}", "-i", seg["clip"]]
    else:
        af = f"[1:a]atrim=duration={dur:.3f}[a]"
        inputs = ["-ss", f"{seg['start']:.3f}", "-t", f"{src_dur + 0.5:.3f}", "-i", seg["clip"],
                  "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
    run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", f"{vf};{af}",
         "-map", "[v]", "-map", "[a]", "-r", FPS, "-c:v", "libx264", "-preset", "veryfast", "-crf", "17",
         "-c:a", "aac", "-ar", 44100, "-ac", 2, "-t", f"{dur:.3f}", out_path])


# ---------------------------------------------------------------- habillage (ASS)

def _ass_time(t):
    t = max(t, 0)
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def _esc(text):
    return str(text).replace("\\", "/").replace("{", "(").replace("}", ")").replace("\n", "\\N")


def _anim(kind):
    if kind == "pop":
        return "\\fscx130\\fscy130\\t(0,140,\\fscx100\\fscy100)"
    if kind == "slide":
        return "\\fad(80,0)"
    return ""


def _circle(r):
    k = 0.5523 * r
    return (f"m {r} 0 b {r} {k} {k} {r} 0 {r} b {-k} {r} {-r} {k} {-r} 0 "
            f"b {-r} {-k} {-k} {-r} 0 {-r} b {k} {-r} {r} {-k} {r} 0")


def _hex_to_ass(color):
    c = color.lstrip("#")
    return f"&H00{c[4:6]}{c[2:4]}{c[0:2]}".upper()


def build_ass(brief, style, path):
    f = style["fonts"]
    ol, sh = style["outline"], style["shadow"]
    styles = "\n".join(
        f"Style: {name},{font},{size},{color},&H000000FF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,{ol},{sh},5,0,0,0,1"
        for name, (font, size, color) in f.items())
    events = []

    def add(start, end, name, text, y, extra=""):
        events.append(f"Dialogue: 0,{_ass_time(start)},{_ass_time(end)},{name},,0,0,0,,"
                      f"{{\\an5\\pos({W // 2},{y}){extra}}}{_esc(text)}")

    anim = _anim(style.get("title_anim"))
    total = brief["total_duration"]
    cta = brief.get("cta")
    last = brief["segments"][-1]["duration"]
    cta_start = total - cta.get("seconds", min(2.0, last)) if cta else total

    # Les titres identiques sur des plans consécutifs ne forment qu'un seul événement (pas de clignotement).
    groups = []
    for seg in brief["segments"]:
        key = (seg.get("kicker"), seg.get("title"), seg.get("subtitle"), seg.get("step"))
        if groups and groups[-1][0] == key:
            groups[-1][2] = seg["t1"]
        else:
            groups.append([key, seg["t0"], seg["t1"]])
    for (kicker, title, subtitle, step), t0, t1 in groups:
        t1 = min(t1, cta_start)
        if t1 <= t0:
            continue
        if step:
            add(t0, t1, "step", step, style["kicker_y"] + 40, anim)
            continue
        if kicker:
            add(t0, t1, "kicker", kicker, style["kicker_y"], anim)
        if title:
            add(t0, t1, "title", title, style["title_y"] if kicker else style["kicker_y"] + 40, anim)
        if subtitle:
            add(t0, t1, "subtitle", subtitle, (style["title_y"] if kicker else style["kicker_y"] + 40) + 85, anim)

    for seg in brief["segments"]:
        for m in seg.get("markers", []):
            start = seg["t0"] + m.get("at", 0.0)
            end = min(start + m.get("dur", seg["duration"]), seg["t1"])
            r = m.get("r", 90)
            sy = 40 if m.get("shape") == "ellipse" else 100   # ellipse = cercle « au sol » en perspective
            color = _hex_to_ass(m.get("color", "#39FF14"))
            events.append(
                f"Dialogue: 1,{_ass_time(start)},{_ass_time(end)},title,,0,0,0,,"
                f"{{\\an5\\pos({m['x']},{m['y']})\\1a&HFF&\\3c{color}\\bord{m.get('width', 7)}\\shad0"
                f"\\fscy{sy}\\fscx100\\t(0,180,\\fscx112\\fscy{int(sy * 1.12)})\\t(180,360,\\fscx100\\fscy{sy})\\p1}}"
                f"{_circle(r)}{{\\p0}}")

    if cta:
        add(cta_start, total, "cta", cta["text"], style["kicker_y"] + 40, _anim("pop"))
    if brief.get("watermark"):
        add(0, total, "watermark", brief["watermark"], style["watermark_y"])

    Path(path).write_text(
        "[Script Info]\nScriptType: v4.00+\nPlayResX: %d\nPlayResY: %d\nWrapStyle: 2\nScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
        "MarginL, MarginR, MarginV, Encoding\n%s\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, "
        "MarginR, MarginV, Effect, Text\n%s\n" % (W, H, styles, "\n".join(events)), encoding="utf-8")


# ---------------------------------------------------------------- assemblage final

def render(brief, out_path, workdir):
    style = get_style(brief.get("style", "bincombat"), brief.get("style_overrides"))
    work = Path(workdir)
    work.mkdir(parents=True, exist_ok=True)
    shutil.copytree(FONTS_DIR, work / "fonts", dirs_exist_ok=True)
    keep_audio = brief.get("keep_clip_audio", not brief.get("music"))

    names = []
    for i, seg in enumerate(brief["segments"]):
        name = f"seg_{i:03d}.mp4"
        print(f"  plan {i + 1}/{len(brief['segments'])} : {Path(seg['clip']).name} "
              f"[{seg['start']:.2f}s +{seg['duration']:.2f}s, {seg['layout']}]")
        render_segment(seg, style, work / name, keep_audio)
        names.append(name)
    (work / "concat.txt").write_text("".join(f"file '{n}'\n" for n in names))
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", "concat.txt", "-c", "copy",
         "montage.mp4"], cwd=work)
    build_ass(brief, style, work / "habillage.ass")

    total = brief["total_duration"]
    inputs = ["-i", "montage.mp4"]
    if brief.get("music"):
        inputs += ["-ss", f"{brief.get('music_offset', 0):.3f}", "-i", str(Path(brief["music"]).resolve())]
        mix = f"[1:a]atrim=duration={total:.3f},asetpts=PTS-STARTPTS,afade=t=out:st={max(total - 0.6, 0):.3f}:d=0.6"
        if keep_audio:
            mix += f"[m];[0:a]volume={brief.get('clip_audio_volume', 0.35)}[c];[m][c]amix=inputs=2:normalize=0"
    else:
        mix = "[0:a]anull"
    lufs = brief.get("target_lufs", -14)
    fc = (f"[0:v]ass=habillage.ass:fontsdir=fonts[v];"
          f"{mix},loudnorm=I={lufs}:TP=-1.0:LRA=7,aresample=44100[a]")
    out_abs = Path(out_path).resolve()
    out_abs.parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-profile:v", "high", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.3f}", "-movflags", "+faststart", work / "brut.mp4"], cwd=work)
    match_loudness(work / "brut.mp4", out_abs, lufs)
    return out_abs


def match_loudness(src, dst, target):
    """loudnorm seul sous-dose les clips très courts : on mesure puis on corrige le gain (vidéo copiée)."""
    from .analyze import loudness
    measured = loudness(str(src))["integrated_lufs"]
    gain = 0.0 if measured is None or measured < -60 else target - measured
    run(["ffmpeg", "-y", "-v", "error", "-i", src, "-c:v", "copy", "-af",
         f"volume={gain:.2f}dB,alimiter=limit=0.89:level=disabled", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", dst])
