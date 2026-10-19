"""Motion design par le code : intro HyperFrames (HTML/CSS 3D + GSAP) et carte de fin Remotion (React).

Les projets vivent dans `motion/` (installer une fois : `cd motion && npm install`). Chaque rendu est paramétré
(titre de la technique, discipline, @, couleur) : aucune retouche manuelle.
"""
import json
import os
import shutil
import subprocess
from pathlib import Path

MOTION = Path(__file__).resolve().parent.parent / "motion"
INTRO_DUR, OUTRO_DUR = 2.4, 3.0


def available():
    return shutil.which("npx") is not None and (MOTION / "node_modules" / ".bin" / "hyperframes").exists()


def _env():
    return {**os.environ, "HYPERFRAMES_TELEMETRY": "0", "DO_NOT_TRACK": "1", "REMOTION_DISABLE_TELEMETRY": "1"}


def _browser():
    """Chrome headless : celui de HyperFrames (téléchargé une fois), réutilisé par Remotion."""
    r = subprocess.run(["npx", "hyperframes", "browser", "path"], cwd=MOTION, capture_output=True, text=True, env=_env())
    path = r.stdout.strip().splitlines()[-1] if r.returncode == 0 and r.stdout.strip() else ""
    if not Path(path).exists():
        subprocess.run(["npx", "hyperframes", "browser", "ensure"], cwd=MOTION, capture_output=True, env=_env())
        r = subprocess.run(["npx", "hyperframes", "browser", "path"], cwd=MOTION, capture_output=True, text=True, env=_env())
        path = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
    return path


def _run(cmd, cwd):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=_env())
    if r.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd[:3])} a échoué :\n{(r.stdout + r.stderr)[-2000:]}")


def render_intro(out, title, kicker="ANALYSE AU RALENTI", tag="COMBAT • ANATOMIE • PLACEMENT", handle="",
                 accent="#39ff14"):
    out = Path(out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    variables = {"title": title, "kicker": kicker, "tag": tag, "handle": handle, "accent": accent}
    _run(["npx", "hyperframes", "render", "--quality", "delivery", "--variables", json.dumps(variables, ensure_ascii=False),
          "--output", str(out)], MOTION / "hyperframes" / "intro")
    return out


def render_outro(out, handle="", teaser="PARTIE 2 : LA DÉFENSE", cta="ABONNE-TOI", save="",
                 accent="#39ff14"):
    out = Path(out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    props = {"handle": handle, "teaser": teaser, "cta": cta, "save": save, "accent": accent}
    cmd = ["npx", "remotion", "render", "remotion/index.jsx", "Outro", str(out), f"--props={json.dumps(props, ensure_ascii=False)}"]
    browser = _browser()
    if browser:
        cmd.append(f"--browser-executable={browser}")
    _run(cmd, MOTION)
    return out
