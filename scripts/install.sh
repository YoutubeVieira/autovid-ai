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

# Motion design : HyperFrames (intro 3D) + Remotion (carte de fin), Node.js 22+ requis
if command -v npm >/dev/null; then
  (cd motion && npm install --no-fund --no-audit && npx hyperframes browser ensure \
     && npx hyperframes skills update motion-graphics && npx remotion skills add) \
     || echo "⚠ motion design non installé (Node 22+ requis) : les montages se feront sans intro/outro animées"
else
  echo "⚠ Node.js absent : installe Node 22+ (https://nodejs.org) pour l'intro HyperFrames et la carte de fin Remotion"
fi

# Skills : Claude Code les lit dans .claude/skills ; on les copie aussi pour Google Antigravity.
mkdir -p .agent/skills && cp -r .claude/skills/* .agent/skills/

cat <<'MSG'

✔ AutoVid installé. Active l'environnement : source .venv/bin/activate

Optionnel :
  export ELEVENLABS_API_KEY=...     # sous-titres + coupe des « euh » (mode talk)
  export ANTHROPIC_API_KEY=...      # explications rédigées par Claude (combat --ai claude)
  Video-Use (montage par transcription) :
     git clone https://github.com/browser-use/video-use ~/video-use && ln -sfn ~/video-use ~/.claude/skills/video-use

  Un skill reçu en .zip :  python -m autovid skills install skill-montage-video.zip
  Partager nos skills :    python -m autovid skills pack -o dist/skill-montage-video.zip

Lancer la plateforme : python -m autovid serve
MSG
