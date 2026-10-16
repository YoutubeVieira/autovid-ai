"""Plan de montage (EDL): coupe des silences, jump-cuts avec punch-in."""


def keep_segments(duration, silences, silence_cfg):
    """Complement des silences longs, en gardant `keep_pad` de respiration de chaque cote."""
    pad, min_sil, min_keep = silence_cfg["keep_pad"], silence_cfg["min_silence"], silence_cfg["min_keep"]
    cuts = []
    for s, e in silences:
        if e - s >= min_sil and (e - s) > 2 * pad:
            cuts.append((s + pad, e - pad))
    segs, cur = [], 0.0
    for a, b in sorted(cuts):
        if a - cur > 0:
            segs.append([cur, a])
        cur = b
    if duration - cur > 0:
        segs.append([cur, duration])
    return [(round(a, 3), round(b, 3)) for a, b in segs if b - a >= min_keep]


def split_shots(segs, max_shot):
    """Decoupe les prises trop longues en plans <= max_shot (le son reste continu)."""
    shots = []
    for a, b in segs:
        n = max(1, int(-(-(b - a) // max_shot)))
        step = (b - a) / n
        for i in range(n):
            shots.append((round(a + i * step, 3), round(a + (i + 1) * step if i < n - 1 else b, 3), i > 0))
    return shots


def build_plan(analysis, preset):
    d = analysis["info"]["duration"]
    segs = keep_segments(d, analysis.get("silences", []), preset["silence"])
    if not segs:
        segs = [(0.0, d)]
    shots = split_shots(segs, preset["pacing"]["max_shot"])
    cycle = preset["pacing"]["zoom_cycle"]
    edl, t = [], 0.0
    for i, (a, b, contiguous) in enumerate(shots):
        prev_out = edl[-1]["src_out"] if edl else None
        edl.append({
            "src_in": a, "src_out": b,
            "out_start": round(t, 3), "out_end": round(t + (b - a), 3),
            "zoom": cycle[i % len(cycle)],
            "contiguous": prev_out is not None and abs(prev_out - a) < 1e-6,
        })
        t += b - a
    return {"source": analysis["file"], "shots": edl, "output_duration": round(t, 3),
            "removed": round(d - t, 3)}


def map_time(plan, t):
    """Temps source -> temps sortie (None si le temps est dans une zone coupee)."""
    for s in plan["shots"]:
        if s["src_in"] <= t <= s["src_out"]:
            return s["out_start"] + (t - s["src_in"])
    return None
