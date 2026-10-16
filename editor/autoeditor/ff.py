"""Appels ffmpeg/ffprobe."""
import json
import shutil
import subprocess


def need_tools():
    missing = [t for t in ("ffmpeg", "ffprobe") if shutil.which(t) is None]
    if missing:
        raise RuntimeError("Outils manquants: " + ", ".join(missing))


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        tail = "\n".join(p.stderr.strip().splitlines()[-15:])
        raise RuntimeError(f"Commande en echec ({cmd[0]}):\n{tail}")
    return p


def probe(path):
    p = run(["ffprobe", "-v", "error", "-show_entries",
             "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate",
             "-of", "json", str(path)])
    data = json.loads(p.stdout)
    video = next((s for s in data["streams"] if s["codec_type"] == "video"), None)
    audio = next((s for s in data["streams"] if s["codec_type"] == "audio"), None)
    if video is None:
        raise RuntimeError(f"Aucun flux video dans {path}")
    num, den = (video.get("r_frame_rate") or "30/1").split("/")
    fps = float(num) / float(den or 1) if float(den or 1) else 30.0
    return {
        "duration": float(data["format"]["duration"]),
        "width": int(video["width"]),
        "height": int(video["height"]),
        "fps": round(fps, 3),
        "video_codec": video["codec_name"],
        "has_audio": audio is not None,
        "audio_codec": audio["codec_name"] if audio else None,
    }
