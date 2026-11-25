#!/usr/bin/env python3
"""Coupe les silences d'une prise brute (utilisé par l'agent monteur-video).

Usage : couper-silences.py entree.mp4 sortie.mp4 [--seuil -35] [--min 0.4] [--marge 0.08]
Écrit aussi sortie.segments.txt : les segments gardés (début fin, en secondes, dans la prise brute).
"""
import argparse
import re
import subprocess
import sys


def duree(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def silences(path, seuil, minimum):
    log = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", path, "-af", f"silencedetect=n={seuil}dB:d={minimum}", "-f", "null", "-"],
        capture_output=True, text=True,
    ).stderr
    debuts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
    fins = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    return list(zip(debuts, fins))


def segments_gardes(total, sil, marge):
    segs, t = [], 0.0
    for debut, fin in sil:
        if debut + marge > t:
            segs.append((t, debut + marge))
        t = max(t, fin - marge)
    if total > t:
        segs.append((t, total))
    return [(a, b) for a, b in segs if b - a > 0.05]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("entree")
    p.add_argument("sortie")
    p.add_argument("--seuil", type=float, default=-35)
    p.add_argument("--min", type=float, default=0.4)
    p.add_argument("--marge", type=float, default=0.08)
    a = p.parse_args()

    total = duree(a.entree)
    segs = segments_gardes(total, silences(a.entree, a.seuil, a.min), a.marge)
    if not segs:
        sys.exit("Aucun segment parlé détecté : baisse --seuil.")

    parts = "".join(
        f"[0:v]trim={s:.3f}:{e:.3f},setpts=PTS-STARTPTS[v{i}];[0:a]atrim={s:.3f}:{e:.3f},asetpts=PTS-STARTPTS[a{i}];"
        for i, (s, e) in enumerate(segs)
    )
    concat = "".join(f"[v{i}][a{i}]" for i in range(len(segs))) + f"concat=n={len(segs)}:v=1:a=1[v][a]"
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", a.entree,
         "-filter_complex", parts + concat, "-map", "[v]", "-map", "[a]",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", a.sortie],
        check=True,
    )
    with open(a.sortie.rsplit(".", 1)[0] + ".segments.txt", "w") as f:
        f.writelines(f"{s:.3f} {e:.3f}\n" for s, e in segs)

    garde = sum(e - s for s, e in segs)
    print(f"{len(segs)} segments gardés · {total:.1f} s → {garde:.1f} s ({total - garde:.1f} s de silence coupés)")


if __name__ == "__main__":
    main()
