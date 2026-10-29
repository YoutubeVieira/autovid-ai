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


def build_ass(plan, srt_path, preset, hook_text=None):
    W, H = preset["target"]["width"], preset["target"]["height"]
    c, hk = preset["captions"], preset["hook"]
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Cap,{c['font']},{c['size']},{_bgr(c['primary'])},&H000000FF,{_bgr(c['outline_color'])},&H64000000,-1,0,0,0,100,100,0,0,1,{c['outline']},2,2,60,60,{c['margin_v']},1
Style: Hook,{c['font']},{hk['size']},{_bgr(hk['text_color'])},&H000000FF,{_bgr(hk['box_color'])},&H00000000,-1,0,0,0,100,100,0,0,3,18,0,8,70,70,{hk['margin_v']},1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
    events = []
    if hook_text:
        end = min(hk["seconds"], plan["output_duration"])
        events.append(f"Dialogue: 1,{_t(0)},{_t(end)},Hook,,0,0,0,,{_wrap(hook_text)}")
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
            events.append(f"Dialogue: 0,{_t(oa)},{_t(ob)},Cap,,0,0,0,,{' '.join(ws)}")
    return head + "\n".join(events) + "\n"
