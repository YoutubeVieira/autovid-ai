"""Sous-titres dynamiques (ASS): 1-3 mots a l'ecran, mot cle en surbrillance, remappes sur la timeline coupee."""
import re
import textwrap

from .plan import map_time
from .transcribe import parse_srt


def _bgr(rgb):
    rgb = rgb.lstrip("#")
    return f"&H00{rgb[4:6]}{rgb[2:4]}{rgb[0:2]}"


def _t(sec):
    cs = int(round(sec * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _esc(text):
    return text.replace("\\", "").replace("{", "(").replace("}", ")")


def _wrap(text, width=22):
    return "\\N".join(textwrap.wrap(_esc(text), width=width)) or _esc(text)


def _chunks(cues, max_words):
    """Cue SRT -> petits groupes de mots, duree repartie au prorata des caracteres."""
    out = []
    for a, b, text in cues:
        words = text.split()
        if not words:
            continue
        groups = [words[i:i + max_words] for i in range(0, len(words), max_words)]
        total = sum(len(" ".join(g)) for g in groups) or 1
        t = a
        for g in groups:
            dur = (b - a) * len(" ".join(g)) / total
            out.append((t, t + dur, g))
            t += dur
    return out


def _emphasis(words):
    """Mot cle = le mot le plus long (>= 5 lettres) du groupe."""
    best = max(range(len(words)), key=lambda i: len(re.sub(r"\W", "", words[i])))
    return best if len(re.sub(r"\W", "", words[best])) >= 5 else None


def build_ass(plan, srt_path, preset, hook_text=None, events=None):
    W, H = preset["target"]["width"], preset["target"]["height"]
    c, hk = preset["captions"], preset["hook"]
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Cap,{c['font']},{c['size']},{_bgr(c['primary'])},&H000000FF,{_bgr(c['outline_color'])},&H64000000,-1,0,0,0,100,100,0,0,1,{c['outline']},2,2,60,60,{c['margin_v']},1
Style: HUD,{c['font']},30,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: Badge,{c['font']},46,&H00111111,&H000000FF,&H0000D4FF,&H0000D4FF,-1,0,0,0,100,100,0,0,3,16,0,5,0,0,0,1
Style: Hook,{c['font']},{hk['size']},{_bgr(hk['text_color'])},&H000000FF,{_bgr(hk['box_color'])},&H00000000,-1,0,0,0,100,100,0,0,3,18,0,8,70,70,{hk['margin_v']},1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
    out_ev = []
    if hook_text and hk["seconds"] > 0:
        end = min(hk["seconds"], plan["content_duration"])
        out_ev.append(f"Dialogue: 1,{_t(0)},{_t(end)},Hook,,0,0,0,,{_wrap(hook_text)}")
    out_ev += _game_events(plan, preset, events or [])
    if srt_path:
        for a, b, words in _chunks(parse_srt(srt_path), c["max_words"]):
            oa, ob = map_time(plan, a + 0.001), map_time(plan, b - 0.001)
            if oa is None and ob is None:
                continue
            oa = 0.0 if oa is None else oa
            ob = plan["output_duration"] if ob is None else ob
            if ob - oa < 0.08:
                continue
            ws = [(_esc(w.upper() if c["uppercase"] else w)) for w in words]
            k = _emphasis(ws)
            if k is not None:
                ws[k] = "{\\c%s}%s{\\c%s}" % (_bgr(c["highlight"]), ws[k], _bgr(c["primary"]))
            out_ev.append(f"Dialogue: 0,{_t(oa)},{_t(ob)},Cap,,0,0,0,,{' '.join(ws)}")
    return head + "\n".join(out_ev) + "\n"


def _rect(w, h, rgb, alpha, x=0, y=0):
    """Rectangle plein en dessin vectoriel ASS (alpha: 00 opaque .. FF transparent)."""
    return (f"{{\\an7\\pos({x},{y})\\p1\\bord0\\shad0\\1c{_bgr(rgb)}&\\1a&H{alpha}&}}"
            f"m 0 0 l {w} 0 l {w} {h} l 0 {h}{{\\p0}}")


def _game_events(plan, preset, events):
    """HUD (titre + compteur), badges +1 et carton de fin, a partir de la liste d'evenements (secondes, timeline de sortie)."""
    W = preset["target"]["width"]
    H = preset["target"]["height"]
    base, total = plan["content_duration"], plan["output_duration"]
    out = []
    hud = preset.get("hud", {})
    if hud.get("enabled"):
        bh = hud["bar_height"]
        oy = hud.get("top_offset", 0)
        out.append(f"Dialogue: 2,{_t(0)},{_t(base)},HUD,,0,0,0,,{_rect(W, bh, '0A1020', '60', 0, oy)}")
        out.append(f"Dialogue: 3,{_t(0)},{_t(base)},HUD,,0,0,0,,{{\\an7\\pos(36,{40 + oy})\\fs{hud['title_size']}\\1c{_bgr('FFFFFF')}&}}{_esc(hud['title'])}")
        subs = [(0.0, hud.get("default_sub", ""))] + [(e["t"], e["text"]) for e in events if e["type"] == "hud_sub"]
        subs.sort(key=lambda x: x[0])
        for i, (t0, txt) in enumerate(subs):
            t1 = subs[i + 1][0] if i + 1 < len(subs) else base
            if t1 > t0 and txt:
                out.append(f"Dialogue: 3,{_t(t0)},{_t(t1)},HUD,,0,0,0,,{{\\an7\\pos(36,{40 + oy + hud['title_size'] + 14})\\fs{max(8, hud['title_size'] - 6)}\\1c{_bgr('C8D0E0')}&}}{_esc(txt)}")
        steps = [(0.0, 0)] + [(e["t"], e["value"]) for e in events if e["type"] == "counter"]
        steps.sort()
        for i, (t0, val) in enumerate(steps):
            t1 = steps[i + 1][0] if i + 1 < len(steps) else base
            if t1 <= t0:
                continue
            col = preset["captions"]["highlight"]
            out.append(f"Dialogue: 3,{_t(t0)},{_t(t1)},HUD,,0,0,0,,{{\\an9\\pos({W - 36},{34 + oy})\\fs{hud['counter_size']}\\1c{_bgr(col)}&}}{val} / {hud['counter_max']}")
            out.append(f"Dialogue: 3,{_t(t0)},{_t(t1)},HUD,,0,0,0,,{{\\an9\\pos({W - 36},{34 + oy + hud['counter_size'] + 22})\\fs{hud['title_size'] - 6}\\1c{_bgr('FFFFFF')}&}}{val} {hud['counter_label']}")
    bd = preset.get("badge", {})
    for e in events:
        if e["type"] != "badge":
            continue
        col = bd["colors"].get(e.get("color", "yellow"), "FFD400")
        t0, t1 = e["t"], min(base, e["t"] + bd["seconds"])
        txt = _esc(e["text"])
        out.append(
            f"Dialogue: 4,{_t(t0)},{_t(t1)},Badge,,0,0,0,,{{\\an5\\pos({W // 2},{bd['y']})\\fs{bd['size']}"
            f"\\fscx60\\fscy60\\t(0,140,\\fscx100\\fscy100)\\fad(60,220)\\1c{_bgr('111111')}&\\3c{_bgr(col)}&\\4c{_bgr(col)}&}}{txt}")
    ep = preset.get("episode")
    if ep and hud.get("enabled"):
        y = hud.get("top_offset", 0) + hud["bar_height"] + 70
        out.append(f"Dialogue: 4,{_t(0.2)},{_t(min(base, ep['seconds']))},Badge,,0,0,0,,{{\\an5\\pos({W // 2},{y})\\fs{ep['size']}\\fad(150,300)\\1c{_bgr('FFFFFF')}&\\3c{_bgr('111111')}&\\4c{_bgr('111111')}&}}{_esc(ep['label'])}")
    ot = preset.get("outro", {})
    if plan["outro"] > 0 and ot:
        out.append(f"Dialogue: 5,{_t(base)},{_t(total)},HUD,,0,0,0,,{_rect(W, H, '0A1020', '30')}")
        out.append(f"Dialogue: 6,{_t(base)},{_t(total)},HUD,,0,0,0,,{{\\an5\\pos({W // 2},{H // 2 - 40})\\fs{ot['title_size']}\\fscx140\\fscy140\\t(0,180,\\fscx100\\fscy100)\\1c{_bgr(preset['captions']['highlight'])}&}}{_wrap(ot['title'], 14)}")
        out.append(f"Dialogue: 6,{_t(base)},{_t(total)},HUD,,0,0,0,,{{\\an5\\pos({W // 2},{H // 2 + 150})\\fs{ot['subtitle_size']}\\1c{_bgr('FFFFFF')}&}}{_esc(ot['subtitle']).replace('|', chr(92) + 'N')}")
    return out
