#!/usr/bin/env bash
# Rendu par lot des vidéos TikTok de Néon Bay.
#   tools/studio/tiktok/render-all.sh               toutes les vidéos manquantes
#   tools/studio/tiktok/render-all.sh 1 11 21       seulement ces numéros
#   RES=1080 tools/studio/tiktok/render-all.sh      en 1080×1920 (environ 2,2 fois plus long)
# En arrière-plan, avec journal :
#   nohup tools/studio/tiktok/render-all.sh > marketing/tiktok/render.log 2>&1 &
# Les vidéos déjà rendues (marketing/tiktok/NN-slug.mp4) sont sautées. Priorité basse (nice -n 10).
set -u
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
DIR="$ROOT/tools/studio/tiktok"
OUT="$ROOT/marketing/tiktok"
RES="${RES:-720}"
mkdir -p "$OUT/.partiel"
cd "$ROOT" || exit 1

# copie figée du studio (dist-web peut être en cours de reconstruction par quelqu'un d'autre)
if [ "${SKIP_STAGE:-0}" != "1" ] || [ ! -f "$OUT/.web/studio.html" ]; then
  nice -n 10 node "$DIR/stage-web.js" || exit 1
fi
export NB_WEB="$OUT/.web"

want=" $* "
total=0; done_n=0; skipped=0; failed=0; t_all=$(date +%s)
for json in "$DIR"/projets/*.json; do
  slug="$(basename "$json" .json)"; num=$((10#${slug%%-*}))
  if [ $# -gt 0 ] && [[ "$want" != *" $num "* ]]; then continue; fi
  total=$((total + 1))
  dest="$OUT/$slug.mp4"
  if [ -s "$dest" ]; then skipped=$((skipped + 1)); echo "[$(date +%H:%M:%S)] déjà rendue : $slug"; continue; fi
  read -r music hot dur < <(node -e "const t=require(process.argv[1]).tiktok;console.log(t.music, t.hot||'-', t.duration)" "$json")
  args=(--out "$OUT/.partiel/$slug.mp4" --res "$RES" --music "$music" --blur "${BLUR:-3}")
  [ "$hot" != "-" ] && args+=(--hot "$hot")
  echo "[$(date +%H:%M:%S)] rendu : $slug (${dur} s, musique $music)"
  t0=$(date +%s)
  if nice -n 10 node tools/studio/render.js "$json" "${args[@]}" && [ -s "$OUT/.partiel/$slug.mp4" ]; then
    mv "$OUT/.partiel/$slug.mp4" "$dest"
    done_n=$((done_n + 1)); echo; echo "[$(date +%H:%M:%S)] OK $slug en $(( $(date +%s) - t0 )) s"
  else
    failed=$((failed + 1)); echo; echo "[$(date +%H:%M:%S)] ÉCHEC $slug"
  fi
done
echo "Terminé : $done_n rendues, $skipped déjà là, $failed échecs, sur $total. Durée : $(( ($(date +%s) - t_all) / 60 )) min."
