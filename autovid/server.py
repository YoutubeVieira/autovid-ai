"""Plateforme web locale : envoie une vidéo depuis ton téléphone, récupère le montage fini.

  python -m autovid serve            → http://<ip-du-pc>:8765/?k=<jeton>  (QR code affiché sur la page du PC)
  python -m autovid watch IN/ OUT/   → traite chaque nouvelle vidéo déposée (Google Drive, iCloud, Syncthing…)

Le jeton dans l'URL empêche les autres appareils du réseau d'utiliser ta machine.
"""
import json
import re
import secrets
import socket
import subprocess
import sys
import threading
import time
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse

ROOT = Path(__file__).resolve().parent.parent
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi"}
JOBS = {}
LOCK = threading.Lock()


def lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))     # aucun paquet n'est envoyé : sert juste à connaître l'interface
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def command(mode, video, out, opts):
    cmd = [sys.executable, "-m", "autovid", mode, str(video), "-o", str(out)]
    if mode == "combat":
        if opts.get("music"):
            cmd += ["--music", opts["music"]]
        if opts.get("handle"):
            cmd += ["--handle", opts["handle"]]
        cmd += ["--resolution", opts.get("resolution", "1080"), "--max-impacts", str(opts.get("max_impacts", 6))]
        if opts.get("ai"):
            cmd += ["--ai", "claude"]
    elif mode == "talk":
        cmd += ["--language", opts.get("language", "fra")]
    return cmd


def run_job(job_id):
    job = JOBS[job_id]
    out = Path(job["out"])
    proc = subprocess.Popen(command(job["mode"], job["video"], out, job["opts"]), cwd=ROOT,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    for line in proc.stdout:                 # le mode texte coupe aussi sur « \r » : on suit la progression
        line = line.strip()
        if not line or "W0000" in line or "I0000" in line:
            continue
        with LOCK:
            m = re.match(r"(\d)/6 (.*)", line)
            if m:
                job["step"] = line
                job["progress"] = max(job["progress"], (int(m.group(1)) - 1) / 6)
            r = re.search(r"rendu (\d+)/(\d+)", line)
            if r:
                job["progress"] = 4 / 6 + int(r.group(1)) / int(r.group(2)) / 6
            job["log"] = (job["log"] + [line])[-40:]
    proc.wait()
    with LOCK:
        job["state"] = "fini" if proc.returncode == 0 and out.exists() else "erreur"
        job["progress"] = 1.0 if job["state"] == "fini" else job["progress"]


def start_job(video, mode, opts, data_dir):
    job_id = uuid.uuid4().hex[:10]
    out_dir = Path(data_dir) / "sorties"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{Path(video).stem}_{mode}_{job_id}.mp4"
    with LOCK:
        JOBS[job_id] = {"id": job_id, "video": str(video), "mode": mode, "opts": opts, "out": str(out),
                        "state": "en cours", "progress": 0.0, "step": "en file", "log": [], "created": time.time()}
    threading.Thread(target=run_job, args=(job_id,), daemon=True).start()
    return job_id


PAGE = (Path(__file__).parent / "web" / "index.html")


class Handler(BaseHTTPRequestHandler):
    token = ""
    data_dir = Path("donnees")

    def log_message(self, *a):
        pass

    def _ok_token(self, q):
        return secrets.compare_digest(q.get("k", [""])[0], self.token)

    def _json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        if not self._ok_token(q):
            self.send_error(HTTPStatus.FORBIDDEN, "jeton manquant : utilise le lien affiché dans le terminal")
            return
        if u.path == "/":
            body = PAGE.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif u.path == "/api/info":
            self._json({"url": f"http://{lan_ip()}:{self.server.server_port}/?k={self.token}"})
        elif u.path == "/api/jobs":
            with LOCK:
                jobs = sorted(JOBS.values(), key=lambda j: -j["created"])
                self._json([{k: v for k, v in j.items() if k not in ("video", "out")} |
                            {"file": Path(j["out"]).name} for j in jobs])
        elif u.path.startswith("/fichier/"):
            self._serve_file(u.path.split("/")[-1])
        else:
            self.send_error(404)

    def _serve_file(self, name):
        with LOCK:
            job = next((j for j in JOBS.values() if Path(j["out"]).name == name and j["state"] == "fini"), None)
        if not job:
            self.send_error(404)
            return
        path = Path(job["out"])
        size = path.stat().st_size
        start, end = 0, size - 1
        rng = self.headers.get("Range")             # lecture vidéo sur iPhone/Android : il faut gérer Range
        if rng and (m := re.match(r"bytes=(\d*)-(\d*)", rng)):
            start = int(m.group(1) or 0)
            end = int(m.group(2)) if m.group(2) else size - 1
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        else:
            self.send_response(200)
        self.send_header("Content-Type", "video/mp4")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(end - start + 1))
        self.send_header("Content-Disposition", f"inline; filename*=UTF-8''{quote(name)}")
        self.end_headers()
        with open(path, "rb") as fh:
            fh.seek(start)
            left = end - start + 1
            while left > 0:
                chunk = fh.read(min(1 << 20, left))
                if not chunk:
                    break
                try:
                    self.wfile.write(chunk)
                except (BrokenPipeError, ConnectionResetError):
                    return
                left -= len(chunk)

    def do_POST(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        if not self._ok_token(q):
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        length = int(self.headers.get("Content-Length", 0))
        if u.path == "/api/upload":                 # corps brut = le fichier (pas de multipart)
            name = Path(q.get("name", ["video.mp4"])[0]).name
            if Path(name).suffix.lower() not in VIDEO_EXT | {".mp3", ".wav", ".m4a", ".aac", ".ogg"}:
                self._json({"error": "format non pris en charge"}, 400)
                return
            dest = self.data_dir / "envois" / f"{uuid.uuid4().hex[:8]}_{name}"
            dest.parent.mkdir(parents=True, exist_ok=True)
            with open(dest, "wb") as fh:
                left = length
                while left > 0:
                    chunk = self.rfile.read(min(1 << 20, left))
                    if not chunk:
                        break
                    fh.write(chunk)
                    left -= len(chunk)
            self._json({"path": str(dest)})
        elif u.path == "/api/jobs":
            body = json.loads(self.rfile.read(length) or b"{}")
            video = Path(body.get("video", ""))
            envois = (self.data_dir / "envois").resolve()
            if not video.resolve().is_relative_to(envois) or not video.exists():
                self._json({"error": "vidéo inconnue"}, 400)
                return
            music = body.get("music")
            if music and not Path(music).resolve().is_relative_to(envois):
                music = None
            opts = {"handle": str(body.get("handle", ""))[:40], "resolution": body.get("resolution", "1080"),
                    "max_impacts": int(body.get("max_impacts", 6)), "music": music, "ai": bool(body.get("ai"))}
            if opts["resolution"] not in ("1080", "1440", "4k", "8k"):
                opts["resolution"] = "1080"
            mode = body.get("mode", "combat") if body.get("mode") in ("combat", "talk") else "combat"
            self._json({"id": start_job(video, mode, opts, self.data_dir)})
        else:
            self.send_error(404)


def serve(port=8765, host="0.0.0.0", data_dir="donnees"):
    Handler.token = secrets.token_urlsafe(9)
    Handler.data_dir = Path(data_dir).resolve()
    httpd = ThreadingHTTPServer((host, port), Handler)
    url = f"http://{lan_ip()}:{port}/?k={Handler.token}"
    print(f"AutoVid est prêt.\n  Sur ce PC      : http://127.0.0.1:{port}/?k={Handler.token}\n"
          f"  Sur ton phone  : {url}\n  (même Wi-Fi ; scanne le QR code affiché sur la page du PC)")
    httpd.serve_forever()


def watch(in_dir, out_dir, mode="combat", opts=None, interval=5):
    """Dossier surveillé : idéal avec un dossier synchronisé entre téléphone et PC."""
    in_dir, out_dir = Path(in_dir), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    done_file = out_dir / ".traites.json"
    done = set(json.loads(done_file.read_text())) if done_file.exists() else set()
    sizes = {}
    print(f"Surveillance de {in_dir} → {out_dir} (Ctrl+C pour arrêter)")
    while True:
        for p in sorted(in_dir.iterdir()):
            if p.suffix.lower() not in VIDEO_EXT or p.name in done:
                continue
            size = p.stat().st_size
            if sizes.get(p.name) != size:           # on attend que la synchro soit terminée (taille stable)
                sizes[p.name] = size
                continue
            out = out_dir / f"{p.stem}_{mode}.mp4"
            print(f"→ {p.name}")
            r = subprocess.run(command(mode, p, out, opts or {}), cwd=ROOT)
            print("   ✔ fini" if r.returncode == 0 else "   ✘ erreur")
            done.add(p.name)
            done_file.write_text(json.dumps(sorted(done)))
        time.sleep(interval)
