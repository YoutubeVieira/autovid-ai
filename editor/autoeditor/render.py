"""Rendu ffmpeg: jump-cuts, cadrage 9:16, punch-in, HUD/sous-titres, carton de fin,
voix off + musique (ducking) + bruitages, mastering loudness en 2 passes."""
import json
import os

from .ff import run
from .plan import map_time


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


def _times(plan, events, kinds):
    out = []
    for e in events or []:
        if e["type"] in kinds:
            mt = map_time(plan, e["t"])
            out.append(e["t"] if mt is None else mt)
    return sorted(out)


def fx_chain(plan, preset, events, W, H):
    """Montage rapide: zoom 'punch' qui retombe, secousse, flou de balayage (whip) et flash, cales sur les evenements."""
    fx = preset.get("fx")
    if not fx:
        return None
    parts = []
    wh = fx.get("whip")
    wt = _times(plan, events, wh["on"]) if wh else []
    if wt:
        en = "+".join(f"between(t,{t - wh['pre']:.3f},{t + wh['post']:.3f})" for t in wt)
        parts.append(f"gblur=sigma={wh['sigma']}:sigmaV=0:steps=2:enable='{en}'")
    pz, sk, fl = fx.get("punch"), fx.get("shake"), fx.get("flash")
    base = 1.0 + (sk["amp"] * 2.2 / W if sk else 0.0) + 0.02
    z_terms, sx_terms, sy_terms = [], [], []
    if pz:
        for t in _times(plan, events, pz["on"]):
            z_terms.append(f"between(t,{t:.3f},{t + pz['dur']:.3f})*{pz['zoom']}*exp(-(t-{t:.3f})/{pz['tau']})")
    if sk:
        for t in _times(plan, events, sk["on"]):
            env = f"between(t,{t:.3f},{t + sk['dur']:.3f})*exp(-(t-{t:.3f})*9)"
            sx_terms.append(f"{env}*{sk['amp']}*sin(t*{sk['freq']})")
            sy_terms.append(f"{env}*{sk['amp'] * 0.7:.2f}*cos(t*{sk['freq'] * 1.3:.1f})")
    z = f"{base:.3f}" + "".join(f"+{x}" for x in z_terms)
    sx = "0" + "".join(f"+{x}" for x in sx_terms)
    sy = "0" + "".join(f"+{x}" for x in sy_terms)
    parts.append(f"scale=w='trunc(iw*({z})/2)*2':h='trunc(ih*({z})/2)*2':eval=frame:flags=bicubic")
    parts.append(f"crop=w={W}:h={H}:x='(iw-ow)/2+({sx})':y='(ih-oh)/2+({sy})'")
    if fl:
        ft = _times(plan, events, fl["on"])
        if ft:
            b = "+".join(f"between(t,{t:.3f},{t + fl['dur']:.3f})*{fl['amount']}*(1-(t-{t:.3f})/{fl['dur']})" for t in ft)
            parts.append(f"eq=brightness='{b}':eval=frame")
    parts.append("setsar=1")
    return ",".join(parts)


def sfx_events(plan, preset, events, sfx_dir):
    """Evenements -> [(temps_sortie, fichier_wav, gain)] selon la table sfx.map du preset."""
    cfg = preset.get("sfx", {})
    if not cfg.get("enabled") or not sfx_dir:
        return []
    m, g = cfg["map"], cfg.get("gain", 0.5)
    out = []
    for e in events:
        key = {"badge": f"badge:{e.get('color', 'yellow')}", "counter": "counter", "cut": "cut",
               "pop": "pop", "milestone": "milestone"}.get(e["type"])
        key = key or {"riser": "riser", "impact": "impact"}.get(e["type"])
        names = m.get(key) or []
        for name in ([names] if isinstance(names, str) else names):
            if os.path.exists(os.path.join(sfx_dir, name + ".wav")):
                out.append((e["t"], os.path.join(sfx_dir, name + ".wav"), g))
    if plan["outro"] > 0 and "outro" in m:
        out.append((plan["content_duration"], os.path.join(sfx_dir, m["outro"] + ".wav"), g))
    return [x for x in out if x[0] < plan["output_duration"]]


def _audio_graph(shots, main_idx, plan, a, music_idx, sfx):
    """Graphe audio seul: prises + carton de fin silencieux, musique (ducking), bruitages. -> (parties, label_final)."""
    parts, labels = [], []
    for i, s in enumerate(shots):
        fade = ""
        if not s["contiguous"]:
            d = s["src_out"] - s["src_in"]
            fade = f",afade=t=in:d=0.008,afade=t=out:st={max(0.0, d - 0.008):.3f}:d=0.008"
        parts.append(f"[{main_idx}:a]atrim=start={s['src_in']}:end={s['src_out']},asetpts=PTS-STARTPTS,"
                     f"aformat=sample_rates=48000:channel_layouts=stereo{fade}[a{i}]")
        labels.append(f"[a{i}]")
    pad = f",apad=pad_dur={plan['outro']}" if plan["outro"] > 0 else ""
    parts.append("".join(labels) + f"concat=n={len(shots)}:v=0:a=1{pad}[ac]")
    src = "ac"
    if music_idx is not None:
        parts.append("[ac]asplit[av][ak]")
        parts.append(f"[{music_idx}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={a['music_gain']}[mu]")
        parts.append("[mu][ak]sidechaincompress=threshold=0.04:ratio=10:attack=20:release=500[duck]")
        parts.append("[av][duck]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[mx]")
        src = "mx"
    if sfx:
        labs = []
        for k, (idx, t, gain) in enumerate(sfx):
            ms = int(t * 1000)
            parts.append(f"[{idx}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={gain},adelay={ms}|{ms}[s{k}]")
            labs.append(f"[s{k}]")
        parts.append(f"[{src}]" + "".join(labs) + f"amix=inputs={len(sfx) + 1}:duration=first:dropout_transition=0:normalize=0[sx]")
        src = "sx"
    return parts, src


def render(plan, source, out_path, preset, ass_path=None, music=None, has_audio=True,
           voice=None, events=None, sfx_dir=None, fonts_dir=None):
    t, a = preset["target"], preset["audio"]
    W, H, fps = t["width"], t["height"], t["fps"]
    shots = plan["shots"]

    vparts, vlabels = _video_chain(shots, W, H, fps)
    vgraph = list(vparts) + ["".join(vlabels) + f"concat=n={len(shots)}:v=1:a=0[vc]"]
    last_v = "vc"
    if plan["outro"] > 0:
        vgraph.append(f"[vc]tpad=stop_mode=clone:stop_duration={plan['outro']}[vp]")
        last_v = "vp"
    fxc = fx_chain(plan, preset, events, W, H)
    if fxc:
        vgraph.append(f"[{last_v}]{fxc}[vf]")
        last_v = "vf"
    if ass_path:
        fd = f":fontsdir={_q(fonts_dir)}" if fonts_dir else ""
        vgraph.append(f"[{last_v}]ass={_q(ass_path)}{fd}[vs]")
        last_v = "vs"

    inputs = ["-i", str(source)]
    n_in = 1

    def add_input(path, loop=False):
        nonlocal n_in
        inputs.extend((["-stream_loop", "-1"] if loop else []) + ["-i", str(path)])
        n_in += 1
        return n_in - 1

    voice_idx = add_input(voice) if voice else None
    music_idx = add_input(music, loop=True) if music else None
    mapped = []
    for ev_t, path, gain in sfx_events(plan, preset, [dict(e, t=map_time(plan, e["t"]) if map_time(plan, e["t"]) is not None else e["t"]) for e in (events or [])], sfx_dir):
        mapped.append((add_input(path), ev_t, gain))

    graph, amap = list(vgraph), []
    main_idx = voice_idx if voice_idx is not None else (0 if has_audio else None)
    if main_idx is not None:
        aparts, src = _audio_graph(shots, main_idx, plan, a, music_idx, mapped)
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
           "-r", str(fps), "-movflags", "+faststart", "-t", f"{plan['output_duration']:.3f}", str(out_path)]
    run(cmd)
    return out_path


def _q(p):
    p = os.path.abspath(str(p)).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
    return f"'{p}'"


def _measure(inputs, aparts, src, a):
    """Passe 1 loudnorm sur le mixage final (graphe audio seul, sans video)."""
    g = ";".join(aparts) + f";[{src}]loudnorm=I={a['lufs']}:TP={a['true_peak']}:LRA={a['lra']}:print_format=json[ao]"
    p = run(["ffmpeg", "-hide_banner"] + inputs + ["-filter_complex", g, "-map", "[ao]", "-f", "null", "-"])
    return json.loads(p.stderr[p.stderr.rfind("{"):p.stderr.rfind("}") + 1])
