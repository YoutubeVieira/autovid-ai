"""Transcription -> SRT. Utilise un .srt fourni, sinon faster-whisper / whisper s'ils sont installes."""
from pathlib import Path


def _ts(t):
    h, rem = divmod(int(t * 1000), 3600000)
    m, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _write_srt(segments, out):
    lines = []
    for i, (a, b, text) in enumerate(segments, 1):
        lines += [str(i), f"{_ts(a)} --> {_ts(b)}", text.strip(), ""]
    Path(out).write_text("\n".join(lines), encoding="utf-8")
    return out


def parse_srt(path):
    import re
    text = Path(path).read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    cues = []
    for block in re.split(r"\n\s*\n", text.strip()):
        rows = block.strip().split("\n")
        if len(rows) < 2:
            continue
        m = re.match(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)", rows[1] if "-->" in rows[1] else rows[0])
        if not m:
            continue
        g = [int(x) for x in m.groups()]
        a = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
        b = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
        body = rows[2:] if "-->" in rows[1] else rows[1:]
        cues.append((a, b, " ".join(r.strip() for r in body)))
    return cues


def transcribe(video, srt_path=None, out_srt=None, language=None):
    """Retourne le chemin d'un SRT, ou None si aucune transcription n'est possible."""
    if srt_path:
        return str(srt_path)
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel("small", compute_type="int8")
        segs, _ = model.transcribe(str(video), language=language)
        return _write_srt([(s.start, s.end, s.text) for s in segs], out_srt)
    except ImportError:
        pass
    try:
        import whisper
        res = whisper.load_model("small").transcribe(str(video), language=language)
        return _write_srt([(s["start"], s["end"], s["text"]) for s in res["segments"]], out_srt)
    except ImportError:
        return None
