"""Controle qualite du rendu final."""
from .analyze import detect_silences, measure_loudness
from .ff import probe


def check(out_path, preset, plan=None):
    t, a = preset["target"], preset["audio"]
    info = probe(out_path)
    checks = []

    def add(name, ok, detail):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    add("resolution", (info["width"], info["height"]) == (t["width"], t["height"]), f"{info['width']}x{info['height']}")
    add("fps", abs(info["fps"] - t["fps"]) < 0.5, str(info["fps"]))
    add("audio_present", info["has_audio"], str(info["audio_codec"]))
    if plan:
        add("duree_attendue", abs(info["duration"] - plan["output_duration"]) < 0.3,
            f"{info['duration']:.2f}s vs plan {plan['output_duration']:.2f}s")
    if info["has_audio"]:
        loud = measure_loudness(out_path, target=a["lufs"], tp=a["true_peak"], lra=a["lra"])
        lufs, tp = float(loud["input_i"]), float(loud["input_tp"])
        add("loudness", abs(lufs - a["lufs"]) <= 1.0, f"{lufs:.1f} LUFS (cible {a['lufs']})")
        add("true_peak", tp <= a["true_peak"] + 0.3, f"{tp:.1f} dBTP (max {a['true_peak']})")
        long_sil = [s for s in detect_silences(out_path, preset["silence"]["noise_db"], 0.6)]
        add("pas_de_silence_long", not long_sil, f"{len(long_sil)} silence(s) > 0.6s")
    return {"passed": all(c["ok"] for c in checks), "checks": checks, "info": info}
