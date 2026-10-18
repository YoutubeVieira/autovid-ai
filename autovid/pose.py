"""Suivi du squelette (MediaPipe Pose Landmarker) : 33 points par personne, 2 personnes max, lissé."""
import os
import subprocess
import urllib.request
from pathlib import Path

import numpy as np

MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
             "pose_landmarker_{v}/float16/latest/pose_landmarker_{v}.task")

# indices MediaPipe
NOSE, L_SH, R_SH, L_EL, R_EL, L_WR, R_WR = 0, 11, 12, 13, 14, 15, 16
L_HIP, R_HIP, L_KNEE, R_KNEE, L_ANK, R_ANK, L_FOOT, R_FOOT = 23, 24, 25, 26, 27, 28, 31, 32

BONES = [(L_SH, R_SH), (L_HIP, R_HIP), (L_SH, L_HIP), (R_SH, R_HIP),
         (L_SH, L_EL), (L_EL, L_WR), (R_SH, R_EL), (R_EL, R_WR),
         (L_HIP, L_KNEE), (L_KNEE, L_ANK), (L_ANK, L_FOOT), (R_HIP, R_KNEE), (R_KNEE, R_ANK), (R_ANK, R_FOOT)]


def model_path(variant="full"):
    cache = Path(os.environ.get("AUTOVID_CACHE", Path.home() / ".cache" / "autovid"))
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / f"pose_landmarker_{variant}.task"
    if not path.exists():
        print(f"  téléchargement du modèle de pose ({variant})…")
        urllib.request.urlretrieve(MODEL_URL.format(v=variant), path)
    return str(path)


def _landmarker(segmentation=False, variant="full"):
    from mediapipe.tasks.python import BaseOptions, vision
    opts = vision.PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=model_path(variant)),
        running_mode=vision.RunningMode.VIDEO, num_poses=2,
        min_pose_detection_confidence=0.4, min_tracking_confidence=0.4,
        output_segmentation_masks=segmentation)
    return vision.PoseLandmarker.create_from_options(opts)


def iter_frames(path, w, h, fps=None, start=None):
    """Images RGB décodées par ffmpeg (lit tous les codecs, AV1 compris)."""
    cmd = ["ffmpeg", "-v", "error"]
    if start:
        cmd += ["-ss", f"{start:.3f}"]
    vf = f"scale={w}:{h}" + (f",fps={fps}" if fps else "")
    cmd += ["-i", str(path), "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    size = w * h * 3
    try:
        while True:
            buf = p.stdout.read(size)
            if len(buf) < size:
                break
            yield np.frombuffer(buf, np.uint8).reshape(h, w, 3)
    finally:
        p.stdout.close()
        p.wait()


def track(path, fps=30, w=540, h=960):
    """Renvoie un tableau (2, N, 33, 3) [x, y, visibilité] normalisé 0–1, NaN si absent, piste 0 = personne principale."""
    import mediapipe as mp
    lm = _landmarker()
    raw = []
    for i, frame in enumerate(iter_frames(path, w, h)):
        res = lm.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(frame)),
                                  int(i * 1000 / fps))
        raw.append([np.array([[p.x, p.y, p.visibility] for p in pose]) for pose in res.pose_landmarks])
    lm.close()
    n = len(raw)
    tracks = np.full((2, n, 33, 3), np.nan)
    last = [None, None]
    for i, poses in enumerate(raw):
        centers = [np.nanmean(p[[L_HIP, R_HIP], :2], axis=0) for p in poses]
        used = set()
        for k in (0, 1):    # association au plus proche de la position précédente
            if last[k] is None or not centers:
                continue
            d = [np.linalg.norm(c - last[k]) if j not in used else 9 for j, c in enumerate(centers)]
            j = int(np.argmin(d))
            if d[j] < 0.25:
                tracks[k, i] = poses[j]
                last[k] = centers[j]
                used.add(j)
        for j, p in enumerate(poses):   # nouvelles personnes → première piste libre
            free = [k for k in (0, 1) if np.isnan(tracks[k, i, 0, 0])]
            if j in used or not free:
                continue
            k = min(free, key=lambda k: last[k] is not None)
            tracks[k, i] = p
            last[k] = centers[j]
            used.add(j)
    if np.isfinite(tracks[1, :, 0, 0]).sum() > np.isfinite(tracks[0, :, 0, 0]).sum():
        tracks = tracks[::-1].copy()
    return smooth(tracks)


def smooth(tracks, max_gap=6):
    out = tracks.copy()
    t = np.arange(tracks.shape[1])
    for k in range(tracks.shape[0]):
        ok = np.isfinite(tracks[k, :, 0, 0])
        if ok.sum() < 2:
            continue
        idx = t[ok]
        pos = np.searchsorted(idx, t).clip(1, len(idx) - 1)
        gap = np.minimum(np.abs(t - idx[pos - 1]), np.abs(idx[pos] - t))
        for c in range(3):
            for j in range(33):
                interp = np.interp(t, idx, tracks[k, ok, j, c])
                out[k, :, j, c] = np.where(gap <= max_gap, interp, np.nan)
        # moyenne glissante centrée sur 3 images : moins de tremblement, impacts conservés
        valid = np.isfinite(out[k, :, 0, 0])
        sm = out[k].copy()
        sm[1:-1] = (out[k, :-2] + out[k, 1:-1] + out[k, 2:]) / 3
        out[k] = np.where(np.isfinite(sm), sm, out[k])
        out[k, ~valid] = np.nan
    return out


def angle(a, b, c):
    """Angle ABC en degrés (en tenant compte du ratio 9:16 de l'image)."""
    s = np.array([1.0, 16 / 9])
    v1, v2 = (a[:2] - b[:2]) * s, (c[:2] - b[:2]) * s
    cos = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-9)
    return float(np.degrees(np.arccos(np.clip(cos, -1, 1))))


def torso_len(p):
    s = np.array([1.0, 16 / 9])
    sh = (p[L_SH, :2] + p[R_SH, :2]) / 2
    hp = (p[L_HIP, :2] + p[R_HIP, :2]) / 2
    return float(np.linalg.norm((sh - hp) * s)) + 1e-6


_IMAGE_LM = None


def segment(frame):
    """Pose + masque de silhouette sur une image fixe (utilisé pendant les arrêts sur image)."""
    global _IMAGE_LM
    import mediapipe as mp
    from mediapipe.tasks.python import BaseOptions, vision
    if _IMAGE_LM is None:
        _IMAGE_LM = vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model_path()), running_mode=vision.RunningMode.IMAGE,
            num_poses=2, min_pose_detection_confidence=0.3, output_segmentation_masks=True))
    res = _IMAGE_LM.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(frame)))
    poses = [np.array([[p.x, p.y, p.visibility] for p in pose]) for pose in res.pose_landmarks]
    masks = [np.squeeze(m.numpy_view()).astype(np.float32) for m in (res.segmentation_masks or [])]
    return poses, masks
