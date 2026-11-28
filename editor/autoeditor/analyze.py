"""Analyse d'une video: silences, changements de plan, loudness."""
import json
import re

from .ff import probe, run


def detect_silences(path, noise_db=-35, min_dur=0.3):
    p = run(["ffmpeg", "-hide_banner", "-i", str(path), "-vn",
             "-af", f"silencedetect=n={noise_db}dB:d={min_dur}", "-f", "null", "-"])
    out, start = [], None
    for line in p.stderr.splitlines():
        m = re.search(r"silence_start: (-?[0-9.]+)", line)
        if m:
            start = max(0.0, float(m.group(1)))
        m = re.search(r"silence_end: ([0-9.]+)", line)
        if m and start is not None:
            out.append((round(start, 3), round(float(m.group(1)), 3)))
            start = None
    return out


def detect_scenes(path, threshold=0.25):
    p = run(["ffmpeg", "-hide_banner", "-i", str(path), "-an",
             "-vf", f"select='gt(scene,{threshold})',showinfo", "-f", "null", "-"])
    return [round(float(t), 3) for t in re.findall(r"pts_time:([0-9.]+)", p.stderr)]


def measure_loudness(path_or_none, filter_chain="", stream_args=None, target=-14.0, tp=-1.5, lra=11.0):
    """Premiere passe loudnorm. Retourne le dict de mesures (input_i, input_tp, ...)."""
    af = (filter_chain + "," if filter_chain else "") + f"loudnorm=I={target}:TP={tp}:LRA={lra}:print_format=json"
    cmd = ["ffmpeg", "-hide_banner"] + (stream_args or ["-i", str(path_or_none)]) + ["-vn", "-af", af, "-f", "null", "-"]
    p = run(cmd)
    blob = p.stderr[p.stderr.rfind("{"):p.stderr.rfind("}") + 1]
    return json.loads(blob)


def analyze(path, preset):
    info = probe(path)
    sil = preset["silence"]
    result = {"file": str(path), "info": info}
    if info["has_audio"]:
        result["silences"] = detect_silences(path, sil["noise_db"], sil["min_silence"])
        result["loudness"] = measure_loudness(path, target=preset["audio"]["lufs"],
                                              tp=preset["audio"]["true_peak"], lra=preset["audio"]["lra"])
    else:
        result["silences"] = []
    result["scene_cuts"] = detect_scenes(path)
    d = info["duration"]
    cuts = result["scene_cuts"]
    result["cut_rate_per_10s"] = round(len(cuts) / d * 10, 2) if d else 0
    return result
