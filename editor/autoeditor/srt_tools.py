"""Outils de traduction de sous-titres: export des repliques en JSON (a traduire par l'agent `translator`),
puis reimport en SRT avec les MEMES horodatages."""
import json
from pathlib import Path

from .transcribe import _ts, parse_srt

MAX_RATIO = 1.35  # un texte traduit > 135 % de l'original sera signale (lecture trop rapide)


def export_cues(srt_path, out_json, target_lang="en"):
    cues = [{"id": i, "start": a, "end": b, "text": t, "chars": len(t)} for i, (a, b, t) in enumerate(parse_srt(srt_path), 1)]
    Path(out_json).write_text(json.dumps({"target_lang": target_lang, "cues": cues,
                                          "instructions": "Ajouter 'translation' a chaque cue. Garder le sens, le ton et un texte court (<= 135 % de 'chars')."},
                                         indent=2, ensure_ascii=False), encoding="utf-8")
    return len(cues)


def import_translations(cues_json, out_srt):
    data = json.loads(Path(cues_json).read_text(encoding="utf-8"))
    lines, warnings = [], []
    for c in data["cues"]:
        tr = (c.get("translation") or "").strip()
        if not tr:
            raise ValueError(f"cue {c['id']} sans traduction")
        if len(tr) > c["chars"] * MAX_RATIO + 8:
            warnings.append(f"cue {c['id']}: {len(tr)} caracteres pour {c['chars']} d'origine (trop long)")
        lines += [str(c["id"]), f"{_ts(c['start'])} --> {_ts(c['end'])}", tr, ""]
    Path(out_srt).write_text("\n".join(lines), encoding="utf-8")
    return len(data["cues"]), warnings
