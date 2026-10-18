"""Petits utilitaires autour de ffmpeg / ffprobe."""
import json
import subprocess

import numpy as np

FPS = 30
W, H = 1080, 1920


def run(cmd, cwd=None):
    """Lance une commande et renvoie stdout+stderr ; lève une erreur lisible en cas d'échec."""
    p = subprocess.run([str(c) for c in cmd], cwd=cwd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"Commande échouée : {' '.join(map(str, cmd))}\n{p.stderr[-3000:]}")
    return p.stdout + p.stderr


def probe(path):
    out = run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", path])
    return json.loads(out[out.index("{"):])


def info(path):
    """Résumé : durée, taille, fps, codecs, présence d'audio."""
    p = probe(path)
    v = next((s for s in p["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in p["streams"] if s["codec_type"] == "audio"), None)
    num, den = (v["r_frame_rate"].split("/") if v else ("0", "1"))
    return {
        "duration": float(p["format"].get("duration", 0)),
        "width": int(v["width"]) if v else 0,
        "height": int(v["height"]) if v else 0,
        "fps": round(int(num) / max(int(den), 1), 3),
        "video_codec": v["codec_name"] if v else None,
        "audio_codec": a["codec_name"] if a else None,
        "has_audio": a is not None,
        "sample_rate": int(a["sample_rate"]) if a else None,
        "bitrate_kbps": round(int(p["format"].get("bit_rate", 0)) / 1000),
    }


def audio_mono(path, sr=22050):
    """Décode la piste audio en mono float32."""
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", str(sr),
                        "-f", "s16le", "-"], capture_output=True)
    if p.returncode != 0 or not p.stdout:
        return np.zeros(0, dtype=np.float32)
    return np.frombuffer(p.stdout, dtype=np.int16).astype(np.float32) / 32768.0


def gray_frames(path, fps=2, w=108, h=192):
    """Images en niveaux de gris réduites, shape (n, h, w)."""
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf",
                        f"fps={fps},scale={w}:{h},format=gray", "-f", "rawvideo", "-"],
                       capture_output=True)
    buf = np.frombuffer(p.stdout, dtype=np.uint8)
    n = len(buf) // (w * h)
    return buf[: n * w * h].reshape(n, h, w).astype(np.float32)
