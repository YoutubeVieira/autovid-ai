#!/usr/bin/env python3
"""Assemble l'application en une seule page (CSS et JS intégrés) pour un aperçu partageable.
Usage : python3 tools/build-artifact.py sortie.html
Les images restent des fichiers (img/...) à publier à côté de la page."""
import re
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
html = (root / "index.html").read_text(encoding="utf-8")
css = (root / "css" / "styles.css").read_text(encoding="utf-8")

def inline_script(match):
    src = match.group(1)
    return "<script>\n" + (root / src).read_text(encoding="utf-8") + "\n</script>"

body = re.search(r'<body>(.*)</body>', html, re.S).group(1)
body = re.sub(r'<script src="([^"]+)"></script>', inline_script, body)
fonts = re.search(r'<link rel="stylesheet" href="(https://fonts\.googleapis\.com[^"]+)">', html).group(1)

page = (
    "<title>Second Souffle Appli</title>\n"
    '<meta name="claude:viewport-fit-sides" content="cover">\n'
    '<link rel="stylesheet" href="' + fonts + '">\n'
    "<style>\n" + css + "\n</style>\n" + body
)
out = Path(sys.argv[1] if len(sys.argv) > 1 else "second-souffle-appli.html")
out.write_text(page, encoding="utf-8")
print("écrit", out, len(page), "octets")
