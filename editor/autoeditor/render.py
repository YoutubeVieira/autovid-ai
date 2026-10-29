"""Rendu ffmpeg: jump-cuts, cadrage 9:16, punch-in, sous-titres, mastering loudness (+ musique avec ducking)."""
import json
import os

from .ff import run


def _video_chain(shots, W, H, fps):
    parts, labels = [], []
    for i, s in enumerate(shots):
        z = s["zoom"]
        zw, zh = int(W * z) // 2 * 2, int(H * z) // 2 * 2
        parts.append(
            f"[0:v]trim=start={s['src_in']}:end={s['src_out']},setpts=PTS-STARTPTS,"
            f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"scale={zw}:{zh},crop={W}:{H}:(iw-ow)/2:(ih-oh)*0.35,setsar=1,fps={fps}[v{i}]")
        labels.append(f"[v{i}]")
    return parts, labels


def _audio_chain(shots):
    parts, labels = [], []
    for i, s in enumerate(shots):
        fade = ""
        if not s["contiguous"]:
            d = s["src_out"] - s["src_in"]
            fade = f",afade=t=in:d=0.008,afade=t=out:st={max(0.0, d - 0.008):.3f}:d=0.008"
        parts.append(f"[0:a]atrim=start={s['src_in']}:end={s['src_out']},asetpts=PTS-STARTPTS,"
                     f"aformat=sample_rates=48000:channel_layouts=stereo{fade}[a{i}]")
        labels.append(f"[a{i}]")
    return parts, labels


def _audio_graph(shots, a, music):
    """Graphe audio seul: concat des prises, musique avec ducking. Retourne (parties, label_final)."""
    parts, labels = _audio_chain(shots)
    parts = list(parts)
    parts.append("".join(labels) + f"concat=n={len(shots)}:v=0:a=1[ac]")
    src = "ac"
    if music:
        parts.append("[ac]asplit[av][ak]")
        parts.append(f"[1:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={a['music_gain']}[mu]")
        parts.append("[mu][ak]sidechaincompress=threshold=0.04:ratio=10:attack=20:release=500[duck]")
        parts.append("[av][duck]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[mx]")
        src = "mx"
    return parts, src


def render(plan, source, out_path, preset, ass_path=None, music=None, has_audio=True):
    t, a = preset["target"], preset["audio"]
    W, H, fps = t["width"], t["height"], t["fps"]
    shots = plan["shots"]

    vparts, vlabels = _video_chain(shots, W, H, fps)
    vgraph = list(vparts) + ["".join(vlabels) + f"concat=n={len(shots)}:v=1:a=0[vc]"]
    last_v = "vc"
    if ass_path:
        vgraph.append(f"[vc]ass={_filter_path(ass_path)}[vs]")
        last_v = "vs"

    inputs = ["-i", str(source)] + (["-stream_loop", "-1", "-i", str(music)] if music else [])
    graph, amap = list(vgraph), []
    if has_audio:
        aparts, src = _audio_graph(shots, a, music)
        m = _measure(inputs, aparts, src, a)
        graph += aparts
        graph.append(
            f"[{src}]loudnorm=I={a['lufs']}:TP={a['true_peak']}:LRA={a['lra']}:"
            f"measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
            f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true[aout]")
        amap = ["-map", "[aout]", "-c:a", "aac", "-b:a", "192k", "-ar", "48000"]

    cmd = ["ffmpeg", "-hide_banner", "-y"] + inputs + ["-filter_complex", ";".join(graph),
           "-map", f"[{last_v}]"] + amap + [
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
           "-r", str(fps), "-movflags", "+faststart", "-shortest", str(out_path)]
    run(cmd)
    return out_path


def _filter_path(p):
    p = os.path.abspath(str(p)).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
    return f"'{p}'"


def _measure(inputs, aparts, src, a):
    """Passe 1 loudnorm sur le mixage final (graphe audio seul, sans video)."""
    g = ";".join(aparts) + f";[{src}]loudnorm=I={a['lufs']}:TP={a['true_peak']}:LRA={a['lra']}:print_format=json[ao]"
    p = run(["ffmpeg", "-hide_banner"] + inputs + ["-filter_complex", g, "-map", "[ao]", "-f", "null", "-"])
    return json.loads(p.stderr[p.stderr.rfind("{"):p.stderr.rfind("}") + 1])
