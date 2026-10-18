#!/usr/bin/env bash
# Installation d'AutoVid (Linux / macOS). Windows : utiliser WSL2 ou installer ffmpeg + Python 3.12 à la main.
set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v ffmpeg >/dev/null; then
  if command -v apt-get >/dev/null; then sudo apt-get install -y ffmpeg libegl1 libgles2
  elif command -v brew >/dev/null; then brew install ffmpeg
  else echo "Installe ffmpeg (https://ffmpeg.org/download.html) puis relance."; exit 1; fi
fi
# MediaPipe a besoin d'EGL sous Linux
if command -v apt-get >/dev/null && ! ldconfig -p | grep -q libEGL.so.1; then sudo apt-get install -y libegl1 libgles2; fi

python3 -m venv .venv
. .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
python -c "from autovid.pose import model_path; model_path()"   # télécharge le modèle de pose une fois

# Skills : Claude Code les lit dans .claude/skills ; on les copie aussi pour Google Antigravity.
mkdir -p .agent/skills && cp -r .claude/skills/* .agent/skills/

cat <<'MSG'

✔ AutoVid installé. Active l'environnement : source .venv/bin/activate

Optionnel :
  export ELEVENLABS_API_KEY=...     # sous-titres + coupe des « euh » (mode talk)
  export ANTHROPIC_API_KEY=...      # explications rédigées par Claude (combat --ai claude)
  Hyperframes (motion design HTML/GSAP) :
     claude plugin marketplace add heygen-com/hyperframes && claude plugin install hyperframes@hyperframes
  Video-Use (montage par transcription) :
     git clone https://github.com/browser-use/video-use ~/video-use && ln -sfn ~/video-use ~/.claude/skills/video-use

Lancer la plateforme : python -m autovid serve
MSG
