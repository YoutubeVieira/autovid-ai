"""Telecharge les modeles de voix francaises libres (sherpa-onnx / Piper).
Usage: python3 download_voices.py [siwis tom upmc] [--dest dossier]"""
import json
import os
import sys
import tarfile
import urllib.request

here = os.path.dirname(os.path.abspath(__file__))
args = [a for a in sys.argv[1:] if not a.startswith("--")]
dest = sys.argv[sys.argv.index("--dest") + 1] if "--dest" in sys.argv else os.path.join(here, "models")
if "--dest" in sys.argv:
    args = [a for a in args if a != dest]
cfg = json.load(open(os.path.join(here, "voices.json"), encoding="utf-8"))["voices"]
os.makedirs(dest, exist_ok=True)
for name in args or ["siwis"]:
    v = cfg[name]
    folder = os.path.join(dest, v["archive"])
    if os.path.isdir(folder):
        print(name, "deja present")
        continue
    url = f"https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/{v['archive']}.tar.bz2"
    tmp = os.path.join(dest, v["archive"] + ".tar.bz2")
    print("telechargement", url)
    urllib.request.urlretrieve(url, tmp)
    with tarfile.open(tmp) as t:
        t.extractall(dest, filter="data")
    os.remove(tmp)
    print(name, "ok ->", folder, "|", v["credit"])
