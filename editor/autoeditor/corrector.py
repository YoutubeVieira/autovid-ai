"""Correcteur audio et video: detecte les defauts techniques et les repare (ffmpeg), avec controle optionnel par Whisper.

check_audio / check_video -> rapport {"ok", "issues":[{niveau, code, detail, correction}], "mesures":{...}}
fix_audio / fix_video     -> fichier corrige + nouveau rapport"""
import json
import os
import re
import struct

from .analyze import detect_silences, measure_loudness
from .ff import probe, run

ERR, WARN, INFO = "erreur", "attention", "info"


def _issue(lst, level, code, detail, fix=None):
    lst.append({"niveau": level, "code": code, "detail": detail, "correction": fix})


def _astats(path):
    p = run(["ffmpeg", "-hide_banner", "-i", str(path), "-vn", "-af", "astats=metadata=0:reset=0", "-f", "null", "-"])
    txt = p.stderr
    block = txt[txt.rfind("Overall"):] if "Overall" in txt else txt
    get = lambda k: (lambda m: float(m.group(1)) if m else None)(re.search(rf"{k}[^:]*:\s*(-?[0-9.]+|-?inf)", block))
    return {"dc": get("DC offset"), "peak_db": get("Peak level dB"), "rms_db": get("RMS level dB"),
            "rms_trough_db": get("RMS trough dB"), "peak_count": get("Peak count")}


def _faststart(path):
    """True si l'atome 'moov' est avant 'mdat' (lecture progressive immediate, requis pour un bon demarrage sur mobile)."""
    with open(path, "rb") as f:
        pos, size = 0, os.path.getsize(path)
        while pos < size:
            f.seek(pos)
            head = f.read(8)
            if len(head) < 8:
                break
            n, typ = struct.unpack(">I4s", head)
            if typ == b"moov":
                return True
            if typ == b"mdat":
                return False
            if n == 1:
                n = struct.unpack(">Q", f.read(8))[0]
            if n < 8:
                break
            pos += n
    return True


def check_audio(path, preset=None, expected_text=None, asr_model=None, lufs=None, tp=None):
    a = (preset or {}).get("audio", {"lufs": -14.0, "true_peak": -1.5, "lra": 11.0})
    lufs, tp = lufs if lufs is not None else a["lufs"], tp if tp is not None else a["true_peak"]
    info = probe(path, need_video=False)
    issues, m = [], {"duree": info["duration"]}
    if not info["has_audio"]:
        _issue(issues, ERR, "pas_audio", "aucune piste audio", "ajouter une piste (voix off ou silence)")
        return {"ok": False, "issues": issues, "mesures": m}
    loud = measure_loudness(path, target=lufs, tp=tp, lra=a.get("lra", 11.0))
    m.update(lufs=float(loud["input_i"]), true_peak=float(loud["input_tp"]), lra=float(loud["input_lra"]))
    st = _astats(path)
    m.update({k: v for k, v in st.items() if v is not None})
    if abs(m["lufs"] - lufs) > 1.5:
        _issue(issues, WARN, "volume", f"{m['lufs']:.1f} LUFS (cible {lufs})", "normalisation loudnorm")
    if m["true_peak"] > tp + 0.3:
        _issue(issues, ERR, "crete", f"crete vraie {m['true_peak']:.1f} dBTP (max {tp})", "limiteur")
    if (st["peak_db"] is not None and st["peak_db"] >= -0.05) or (st["peak_count"] or 0) > 20:
        _issue(issues, ERR, "saturation", f"ecretage probable (crete {st['peak_db']} dB, {int(st['peak_count'] or 0)} echantillons au max)", "reparation adeclip + limiteur")
    if st["dc"] is not None and abs(st["dc"]) > 0.005:
        _issue(issues, WARN, "continu", f"decalage continu {st['dc']:.4f}", "filtre passe-haut")
    if st["rms_trough_db"] is not None and st["rms_trough_db"] > -50:
        _issue(issues, WARN, "bruit_de_fond", f"plancher de bruit eleve ({st['rms_trough_db']:.0f} dB)", "debruitage afftdn")
    sil = detect_silences(path, -45, 0.4)
    d = info["duration"]
    if sil and sil[0][0] <= 0.05 and sil[0][1] - sil[0][0] > 0.4:
        _issue(issues, WARN, "silence_debut", f"{sil[0][1]:.2f} s de silence au debut", "rognage")
    if sil and abs(sil[-1][1] - d) < 0.1 and sil[-1][1] - sil[-1][0] > 0.6:
        _issue(issues, INFO, "silence_fin", f"{sil[-1][1] - sil[-1][0]:.2f} s de silence a la fin", "rognage (ou garder si c'est un carton de fin voulu)")
    for s_, e_ in sil:
        if e_ - s_ > 1.2 and s_ > 0.05 and abs(e_ - d) > 0.1:
            _issue(issues, WARN, "silence_long", f"{s_:.1f}-{e_:.1f} s ({e_ - s_:.1f} s)", "a couper si ce n'est pas voulu")
    if expected_text and asr_model:
        from . import asr
        heard = asr.transcribe(asr_model, path)
        wer, diffs = asr.compare(expected_text, heard)
        m.update(entendu=heard, erreur_mots=wer)
        if wer > 0.35:
            _issue(issues, ERR, "diction", f"{wer:.0%} de mots mal compris par Whisper: {diffs[:4]}", "reecrire en orthographe phonetique (packs/voices/prononciation.json) ou baisser la vitesse")
        elif wer > 0.15:
            _issue(issues, WARN, "diction", f"{wer:.0%} de mots douteux: {diffs[:4]}", "verifier a l'oreille")
    return {"ok": not any(i["niveau"] == ERR for i in issues), "issues": issues, "mesures": m}


def check_video(path, preset=None, target_duration=None, expect_aspect=(9, 16)):
    t = (preset or {}).get("target", {"width": 1080, "height": 1920, "fps": 30})
    info = probe(path)
    issues, m = [], dict(info)
    if (info["width"], info["height"]) != (t["width"], t["height"]):
        lvl = ERR if info["width"] * expect_aspect[1] != info["height"] * expect_aspect[0] else WARN
        _issue(issues, lvl, "format", f"{info['width']}x{info['height']} (cible {t['width']}x{t['height']})", "recadrage/mise a l'echelle")
    if abs(info["fps"] - t["fps"]) > 0.5:
        _issue(issues, WARN, "images_par_seconde", f"{info['fps']} i/s (cible {t['fps']})", "conversion de cadence")
    pf = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=pix_fmt,avg_frame_rate,r_frame_rate", "-of", "json", str(path)])
    vs = json.loads(pf.stdout)["streams"][0]
    m["pix_fmt"] = vs.get("pix_fmt")
    if vs.get("pix_fmt") != "yuv420p":
        _issue(issues, WARN, "pix_fmt", f"{vs.get('pix_fmt')} (yuv420p attendu par les reseaux)", "reencodage yuv420p")
    if vs.get("avg_frame_rate") != vs.get("r_frame_rate"):
        _issue(issues, INFO, "cadence_variable", f"{vs.get('avg_frame_rate')} vs {vs.get('r_frame_rate')}", "conversion de cadence constante")
    if info["video_codec"] not in ("h264", "hevc"):
        _issue(issues, WARN, "codec", f"{info['video_codec']} (h264 conseille)", "reencodage h264")
    if not _faststart(path):
        _issue(issues, WARN, "faststart", "l'index (moov) est a la fin du fichier: demarrage lent", "remux +faststart")
    if target_duration and not (target_duration[0] <= info["duration"] <= target_duration[1]):
        _issue(issues, WARN, "duree", f"{info['duration']:.1f} s (cible {target_duration[0]}-{target_duration[1]} s)", "couper/rallonger le montage")
    b = run(["ffmpeg", "-hide_banner", "-i", str(path), "-an", "-vf", "blackdetect=d=0.3:pix_th=0.10", "-f", "null", "-"]).stderr
    blacks = [(float(a), float(z)) for a, z in re.findall(r"black_start:([0-9.]+) black_end:([0-9.]+)", b)]
    m["noir"] = blacks
    if blacks and blacks[0][0] <= 0.05:
        _issue(issues, WARN, "noir_debut", f"{blacks[0][1]:.2f} s d'ecran noir au debut", "rognage")
    if blacks and abs(blacks[-1][1] - info["duration"]) < 0.2:
        _issue(issues, WARN, "noir_fin", f"{blacks[-1][1] - blacks[-1][0]:.2f} s d'ecran noir a la fin", "rognage")
    fz = run(["ffmpeg", "-hide_banner", "-i", str(path), "-an", "-vf", "freezedetect=n=-60dB:d=1.2", "-f", "null", "-"]).stderr
    frozen = re.findall(r"freeze_start: ([0-9.]+)", fz)
    if frozen:
        _issue(issues, INFO, "image_figee", f"image immobile >1,2 s a partir de {', '.join(frozen[:3])} s", "voulu ? (carton de fin) sinon ajouter du mouvement")
    if info["has_audio"]:
        au = check_audio(path, preset)
        m["audio"] = au["mesures"]
        issues += [dict(i, code="audio_" + i["code"]) for i in au["issues"]]
        sd = run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=duration", "-of", "csv=p=0", str(path)]).stdout.strip()
        try:
            if abs(float(sd) - info["duration"]) > 0.25:
                _issue(issues, WARN, "desynchro", f"audio {float(sd):.2f} s / video {info['duration']:.2f} s", "re-synchronisation aresample async")
        except ValueError:
            pass
        if info.get("audio_codec") not in ("aac", "mp3", "opus"):
            _issue(issues, WARN, "codec_audio", str(info.get("audio_codec")), "reencodage aac")
    else:
        _issue(issues, WARN, "pas_audio", "aucune piste audio", "ajouter une piste silencieuse ou la voix off")
    return {"ok": not any(i["niveau"] == ERR for i in issues), "issues": issues, "mesures": m}


def _two_pass_loudnorm(path, pre, lufs, tp, lra):
    m = measure_loudness(None, filter_chain=pre, stream_args=["-i", str(path)], target=lufs, tp=tp, lra=lra)
    return (f"loudnorm=I={lufs}:TP={tp}:LRA={lra}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
            f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")


def _audio_chain(path, rep, lufs, tp, lra, trim=True, denoise=None):
    codes = {i["code"].replace("audio_", "") for i in rep["issues"]}
    pre = []
    if "saturation" in codes:
        pre.append("adeclip")
    pre += ["highpass=f=70", "adeclick"]
    if denoise or (denoise is None and "bruit_de_fond" in codes):
        pre.append("afftdn=nf=-30")
    if trim and ({"silence_debut", "silence_fin"} & codes):
        pre.append("silenceremove=start_periods=1:start_duration=0.05:start_threshold=-45dB:start_silence=0.12,"
                   "areverse,silenceremove=start_periods=1:start_duration=0.05:start_threshold=-45dB:start_silence=0.2,areverse")
    pre_s = ",".join(pre)
    return pre_s + "," + _two_pass_loudnorm(path, pre_s, lufs, tp, lra) + f",alimiter=limit={10 ** ((tp - 0.3) / 20):.3f}:level=disabled"


def fix_audio(src, dst, preset=None, expected_text=None, asr_model=None, **kw):
    a = (preset or {}).get("audio", {"lufs": -14.0, "true_peak": -1.5, "lra": 11.0})
    rep = check_audio(src, preset, expected_text, asr_model)
    chain = _audio_chain(src, rep, a["lufs"], a["true_peak"], a.get("lra", 11.0), **kw)
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(src), "-vn", "-af", chain, "-ar", "48000", str(dst)])
    return rep, check_audio(dst, preset, expected_text, asr_model)


def fix_video(src, dst, preset=None, trim_black=True, add_silent_audio=False):
    t = (preset or {}).get("target", {"width": 1080, "height": 1920, "fps": 30})
    a = (preset or {}).get("audio", {"lufs": -14.0, "true_peak": -1.5, "lra": 11.0})
    rep = check_video(src, preset)
    info = rep["mesures"]
    W, H, fps = t["width"], t["height"], t["fps"]
    ss, to = 0.0, info["duration"]
    if trim_black:
        for s_, e_ in info.get("noir", []):
            if s_ <= 0.05:
                ss = e_
            elif abs(e_ - info["duration"]) < 0.2:
                to = s_
    vf = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={fps},format=yuv420p"
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{ss:.3f}", "-to", f"{to:.3f}", "-i", str(src)]
    if info["has_audio"]:
        arep = {"issues": [i for i in rep["issues"] if i["code"].startswith("audio_")]}
        af = "aresample=async=1:first_pts=0," + _audio_chain(src, arep, a["lufs"], a["true_peak"], a.get("lra", 11.0), trim=False)
        cmd += ["-vf", vf, "-af", af, "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"]
    elif add_silent_audio:
        cmd = cmd[:-2] + ["-ss", f"{ss:.3f}", "-to", f"{to:.3f}", "-i", str(src), "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                          "-shortest", "-vf", vf, "-c:a", "aac", "-b:a", "128k"]
    else:
        cmd += ["-vf", vf, "-an"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "19", "-profile:v", "high", "-movflags", "+faststart", str(dst)]
    run(cmd)
    return rep, check_video(dst, preset)


def format_report(rep, title=""):
    lines = [f"== {title} : {'OK' if rep['ok'] else 'A CORRIGER'}"]
    for i in rep["issues"]:
        lines.append(f"  [{i['niveau']:9}] {i['code']:22} {i['detail']}" + (f"  -> {i['correction']}" if i["correction"] else ""))
    if not rep["issues"]:
        lines.append("  aucun probleme detecte")
    return "\n".join(lines)
