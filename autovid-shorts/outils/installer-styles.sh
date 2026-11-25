#!/usr/bin/env bash
# Installe les 7 styles de création MP4 (vidéo « Compétences » : Motion, Claymation, Explainer, Singing,
# Commercial, Animation, Cartoon) pour ce projet, sur votre PC (Mac / Linux). Windows : installer-styles.ps1.
# Catalogue et coûts : styles/STYLES.md. Rien de ce qui est téléchargé ici n'est versionné dans git.
#
#   bash outils/installer-styles.sh               # skills + OpenMontage (sans ses dépendances)
#   bash outils/installer-styles.sh --setup       # + « make setup » d'OpenMontage (Python, Node, TTS gratuite)
#   bash outils/installer-styles.sh --sans-openmontage
set -euo pipefail
cd "$(dirname "$0")/.."
SETUP=0; OM=1
for a in "$@"; do
  case "$a" in --setup) SETUP=1 ;; --sans-openmontage) OM=0 ;; *) echo "option inconnue : $a" >&2; exit 2 ;; esac
done

# Versions testées (dépôt  commit)
OPENMONTAGE="https://github.com/calesthio/OpenMontage 2e003e65fa99a0f329478a2c1cdcf26bc481933a"
CLAYMATION="https://github.com/mikefutia/claymation-ads-claude-skill 5c88eea9b63d425ca444e1123dbfac8f93b193b3"
SEEDANCE="https://github.com/robonuggets/seedance-skill e513cc85ae2f9e8c8045b9581389cb8f8daddda9"
TALKING="https://github.com/brewed-ops/talking-explainer 3a19bbce0c97dcdd3120c7e3c4b10ddc3e13f1d5"

fetch() {  # fetch <url> <commit> <dossier>
  if [ -d "$3/.git" ]; then git -C "$3" fetch -q --depth 1 origin "$2"; else rm -rf "$3"; git clone -q --filter=blob:none "$1" "$3"; fi
  git -C "$3" checkout -q "$2"
}
mkdir -p externes .claude/skills

echo "1/4 Claymation (claymation-ads)"
read -r u c <<<"$CLAYMATION"; fetch "$u" "$c" externes/claymation-ads
rm -rf .claude/skills/claymation-ads; cp -r externes/claymation-ads/claymation-ads .claude/skills/claymation-ads

echo "2/4 Commercial / Motion (seedance)"
read -r u c <<<"$SEEDANCE"; fetch "$u" "$c" externes/seedance
rm -rf .claude/skills/seedance; mkdir -p .claude/skills/seedance
cp externes/seedance/SKILL.md externes/seedance/README.md .claude/skills/seedance/

echo "3/4 Explainer / Cartoon (talking-explainer : 3 skills)"
read -r u c <<<"$TALKING"; fetch "$u" "$c" externes/talking-explainer
for sk in talking-explainer explainer-kit spatial-film; do
  rm -rf ".claude/skills/$sk"; cp -r "externes/talking-explainer/skills/$sk" ".claude/skills/$sk"
done
command -v npx >/dev/null && npx -y hyperframes skills update general-video hyperframes-animation media-use || \
  echo "   ⚠ npx absent : installez Node.js puis lancez « npx hyperframes skills update general-video hyperframes-animation media-use »"

if [ "$OM" = 1 ]; then
  echo "4/4 Animation 3D / Explainer / Cinematic / Singing (OpenMontage, ~165 Mo)"
  read -r u c <<<"$OPENMONTAGE"; fetch "$u" "$c" externes/OpenMontage
  if [ "$SETUP" = 1 ]; then (cd externes/OpenMontage && make setup); else echo "   (dépendances non installées : relancez avec --setup)"; fi
fi

[ -f .env ] || cp outils/env.exemple .env
echo
echo "✔ Styles installés. Clés à renseigner dans .env (jamais dans git) : voir styles/STYLES.md."
echo "  Relancez Claude Code dans ce dossier pour charger les nouvelles skills, puis demandez à l'agent directeur-creatif."
