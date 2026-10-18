"""Skills en .zip : installer un pack reçu (ex. skill-montage-video.zip) sans risque, ou exporter les nôtres.

Installer ne lance rien : le zip est vérifié (chemins, liens, taille), chaque dossier doit avoir un SKILL.md avec
`name` et `description`, et les scripts qu'il contient sont listés pour que tu les relises avant usage.
"""
import re
import shutil
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / ".claude" / "skills"
MAX_BYTES = 50 * 1024 * 1024
SCRIPT_EXT = {".py", ".sh", ".js", ".mjs", ".ts", ".ps1", ".bat", ".rb"}


def _frontmatter(text):
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def _safe_extract(zf, dest):
    total = 0
    for info in zf.infolist():
        name = info.filename
        if name.startswith("/") or ".." in Path(name).parts or "\\" in name:
            raise ValueError(f"chemin refusé dans le zip : {name}")
        if (info.external_attr >> 16) & 0o170000 == 0o120000:
            raise ValueError(f"lien symbolique refusé : {name}")
        total += info.file_size
        if total > MAX_BYTES:
            raise ValueError("zip trop gros (> 50 Mo décompressés)")
    zf.extractall(dest)


def inspect(zip_path):
    """Liste les skills contenus : [{name, description, dir, scripts}]."""
    with tempfile.TemporaryDirectory() as tmp, zipfile.ZipFile(zip_path) as zf:
        _safe_extract(zf, tmp)
        return _find(Path(tmp), keep=False)


def _find(base, keep=True):
    found = []
    for md in sorted(base.rglob("SKILL.md")):
        meta = _frontmatter(md.read_text(encoding="utf-8", errors="replace"))
        if not meta.get("name") or not meta.get("description"):
            continue
        d = md.parent
        scripts = sorted(str(p.relative_to(d)) for p in d.rglob("*") if p.suffix.lower() in SCRIPT_EXT)
        found.append({"name": meta["name"], "description": meta["description"][:160], "dir": d if keep else None,
                      "scripts": scripts})
    return found


def install(zip_path, dest=SKILLS, also_antigravity=True, overwrite=False):
    dest = Path(dest)
    with tempfile.TemporaryDirectory() as tmp, zipfile.ZipFile(zip_path) as zf:
        _safe_extract(zf, tmp)
        skills = _find(Path(tmp))
        if not skills:
            raise ValueError("aucun SKILL.md valide (frontmatter name + description) dans ce zip")
        installed = []
        for sk in skills:
            if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", sk["name"]):
                raise ValueError(f"nom de skill invalide : {sk['name']!r}")
            targets = [dest / sk["name"]]
            if also_antigravity:
                targets.append(ROOT / ".agent" / "skills" / sk["name"])
            for t in targets:
                if t.exists() and not overwrite:
                    raise FileExistsError(f"{t} existe déjà (relance avec --overwrite)")
                if t.exists():
                    shutil.rmtree(t)
                shutil.copytree(sk["dir"], t)
            installed.append({k: v for k, v in sk.items() if k != "dir"})
        return installed


def pack(out, src=SKILLS, names=None):
    """Exporte nos skills dans un zip partageable (un dossier par skill)."""
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for d in sorted(Path(src).iterdir()):
            if not (d / "SKILL.md").exists() or (names and d.name not in names):
                continue
            for p in sorted(d.rglob("*")):
                if p.is_file() and not p.is_symlink():
                    zf.write(p, Path(d.name) / p.relative_to(d))
            count += 1
    return out, count
