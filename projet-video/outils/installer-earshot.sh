#!/usr/bin/env bash
# Installe earshot (outils 2 et 3 de la vidéo « 3 outils SFX ») pour ce projet, sur votre PC (Mac / Linux).
# Copie identique dans projet-video/outils/ et projet-senior-us/outils/. Windows : installer-earshot.ps1.
#
#   bash outils/installer-earshot.sh            # outil + serveur MCP déclaré à Claude Code pour ce projet
#   bash outils/installer-earshot.sh --ecoute   # + les modèles d'écoute (≈ 1,1 Go à télécharger)
#   bash outils/installer-earshot.sh --skills   # met aussi à jour .claude/skills/earshot et real-sound
#   bash outils/installer-earshot.sh --sans-mcp # n'enregistre pas le serveur MCP
set -euo pipefail
COMMIT=7a7f7c5c70d4a763a1eca4b3666af7c77e313f97   # version testée
REPO=https://github.com/Leonxlnx/earshot
cd "$(dirname "$0")/.."
PROJET="$(pwd)"
VENV="$PROJET/.venv-earshot"
EXTRAS="mcp"; MCP=1; SKILLS=0
for a in "$@"; do
  case "$a" in
    --ecoute) EXTRAS="mcp,listen" ;;
    --skills) SKILLS=1 ;;
    --sans-mcp) MCP=0 ;;
    *) echo "option inconnue : $a" >&2; exit 2 ;;
  esac
done

command -v python3 >/dev/null || { echo "Python 3.10+ est nécessaire." >&2; exit 1; }
command -v ffmpeg >/dev/null || echo "⚠ ffmpeg introuvable : earshot n'écrira que du wav/flac."

echo "1/3 environnement Python : $VENV"
python3 -m venv "$VENV"
"$VENV/bin/python" -m pip install -q --upgrade pip
if [ "$EXTRAS" != "mcp" ]; then
  # torch CPU : bien plus léger que la version CUDA par défaut
  "$VENV/bin/python" -m pip install -q torch --index-url https://download.pytorch.org/whl/cpu
fi
"$VENV/bin/python" -m pip install -q "earshot[$EXTRAS] @ git+$REPO@$COMMIT"
"$VENV/bin/earshot" doctor | grep -E '^(extras|problems)' || true
[ "$EXTRAS" != "mcp" ] && "$VENV/bin/earshot" doctor --fetch >/dev/null

echo "2/3 serveur MCP"
if [ "$MCP" = 1 ] && command -v claude >/dev/null; then
  # --scope local : enregistré pour ce projet sur CE PC seulement (chemin propre à la machine, rien dans git)
  claude mcp remove earshot --scope local >/dev/null 2>&1 || true
  claude mcp add earshot --scope local -e EARSHOT_THREADS=3 -- "$VENV/bin/python" -m earshot mcp
else
  echo "   (ignoré) à la main : claude mcp add earshot --scope local -e EARSHOT_THREADS=3 -- \"$VENV/bin/python\" -m earshot mcp"
fi

if [ "$SKILLS" = 1 ]; then
  echo "   mise à jour des skills…"
  TMP="$(mktemp -d)"; git clone -q "$REPO" "$TMP/earshot"; git -C "$TMP/earshot" checkout -q "$COMMIT"
  for sk in earshot real-sound; do
    rm -rf ".claude/skills/$sk"; cp -r "$TMP/earshot/skills/$sk" ".claude/skills/$sk"; cp "$TMP/earshot/LICENSE" ".claude/skills/$sk/"
  done
  rm -rf "$TMP"
fi

echo "3/3 essai"
"$VENV/bin/earshot" make "a soft UI pop" -o "$VENV/essai.wav" | head -1
echo
echo "✔ earshot est prêt. Python pour la skill real-sound ({{PY}}) : $VENV/bin/python"
echo "  Relancez Claude Code dans ce dossier pour charger le serveur MCP « earshot »."
