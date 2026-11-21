#!/usr/bin/env bash
# Néon Bay - assemble les plans Veo (+ la vraie capture du jeu) en une vidéo verticale 1080x1920.
#
# Usage : bash tools/veo/assemble.sh [options]
#   -i <dossier>   plans MP4 (défaut : marketing/veo)
#   -g <fichier>   capture de gameplay à ajouter (défaut : marketing/bande-annonce-verticale.mp4)
#   -G             ne pas ajouter la capture de gameplay
#   -m <fichier>   musique (libre de droits) : remplace le son des plans
#   -t <secondes>  garde au plus N secondes par plan IA (ex. 3 pour un format court)
#   -o <fichier>   sortie (défaut : marketing/bande-annonce-veo.mp4)
#   -T <texte>     titre du carton d'ouverture (défaut : NÉON BAY)
#   -S <texte>     sous-titre du carton d'ouverture
#   -E <texte>     texte du carton de fin
#   -L             retire les mentions « Images générées par IA » / « Gameplay réel » (déconseillé)
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"

IN="$ROOT/marketing/veo"
GAME="$ROOT/marketing/bande-annonce-verticale.mp4"
USE_GAME=1
MUSIC=""
TRIM=0
OUT="$ROOT/marketing/bande-annonce-veo.mp4"
TITLE="NÉON BAY"
SUB="4 pays. 30 missions."
END_TXT="Le niveau 1 est gratuit"
LABELS=1

while getopts "i:g:Gm:t:o:T:S:E:Lh" opt; do
  case "$opt" in
    i) IN="$(realpath "$OPTARG")" ;;
    g) GAME="$(realpath "$OPTARG")" ;;
    G) USE_GAME=0 ;;
    m) MUSIC="$(realpath "$OPTARG")" ;;
    t) TRIM="$OPTARG" ;;
    o) OUT="$(realpath -m "$OPTARG")" ;;
    T) TITLE="$OPTARG" ;;
    S) SUB="$OPTARG" ;;
    E) END_TXT="$OPTARG" ;;
    L) LABELS=0 ;;
    h|*) sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
  esac
done

command -v ffmpeg >/dev/null || { echo "Erreur : ffmpeg introuvable (sudo apt install ffmpeg)." >&2; exit 1; }
[[ -n "$MUSIC" && ! -f "$MUSIC" ]] && { echo "Erreur : musique introuvable : $MUSIC" >&2; exit 1; }

# Police : Inter Bold si présente, sinon DejaVu Sans Bold.
FONT="$(fc-match -f '%{file}' 'Inter:style=Bold' 2>/dev/null || true)"
[[ -f "$FONT" ]] || FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
[[ -f "$FONT" ]] || { echo "Erreur : aucune police trouvée." >&2; exit 1; }

# Ordre des plans : celui de shots.json, puis les autres MP4 du dossier par ordre alphabétique.
CLIPS=()
if [[ -d "$IN" ]]; then
  if [[ -f "$HERE/shots.json" ]] && command -v node >/dev/null; then
    while IFS= read -r id; do
      [[ -f "$IN/$id.mp4" ]] && CLIPS+=("$IN/$id.mp4")
    done < <(node -e 'for (const s of require(process.argv[1]).shots) console.log(s.id)' "$HERE/shots.json")
  fi
  for f in "$IN"/*.mp4; do
    [[ -f "$f" ]] || continue
    [[ " ${CLIPS[*]-} " == *" $f "* ]] || CLIPS+=("$f")
  done
fi
if [[ ${#CLIPS[@]} -eq 0 ]]; then
  echo "Aucun plan Veo trouvé dans $IN (lance d'abord : node tools/veo/veo.js)." >&2
  [[ $USE_GAME -eq 1 && -f "$GAME" ]] || exit 1
  echo "On continue avec la seule capture du jeu." >&2
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
printf '%s' "$TITLE"   > "$TMP/title.txt"
printf '%s' "$SUB"     > "$TMP/sub.txt"
printf '%s' "$END_TXT" > "$TMP/end.txt"
printf '%s' "Images générées par IA, pas du gameplay" > "$TMP/ia.txt"
printf '%s' "Gameplay réel" > "$TMP/real.txt"
printf '%s' "Néon Bay - jeu d'action en monde ouvert" > "$TMP/end2.txt"

V="-c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p -r 30"
A="-c:a aac -b:a 160k -ar 48000 -ac 2"
FIT="scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30"
dt() { # dt <fichier-texte> <taille> <y> [couleur]
  echo "drawtext=fontfile=$FONT:textfile=$1:fontsize=$2:fontcolor=${4:-white}:x=(w-text_w)/2:y=$3:borderw=4:bordercolor=black@0.7"
}
LABEL_IA=""; LABEL_REAL=""
if [[ $LABELS -eq 1 ]]; then
  LABEL_IA=",drawtext=fontfile=$FONT:textfile=$TMP/ia.txt:fontsize=34:fontcolor=white@0.9:x=(w-text_w)/2:y=h-150:box=1:boxcolor=black@0.45:boxborderw=14"
  LABEL_REAL=",drawtext=fontfile=$FONT:textfile=$TMP/real.txt:fontsize=40:fontcolor=white:x=(w-text_w)/2:y=h-150:box=1:boxcolor=0xff2e93@0.8:boxborderw=14"
fi

has_audio() { [[ -n "$(ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 "$1")" ]]; }

# Normalise un plan : 1080x1920, 30 i/s, son stéréo (silence ajouté si le plan est muet).
segment() { # segment <entrée> <sortie> <filtre-texte> <durée-max>
  local in="$1" out="$2" label="$3" max="$4" tlim=()
  [[ "$max" != "0" ]] && tlim=(-t "$max")
  if has_audio "$in"; then
    ffmpeg -nostdin -v error -y -i "$in" "${tlim[@]}" -vf "$FIT$label" -map 0:v:0 -map 0:a:0 $V $A "$out"
  else
    ffmpeg -nostdin -v error -y -i "$in" -f lavfi -i anullsrc=r=48000:cl=stereo "${tlim[@]}" \
      -vf "$FIT$label" -map 0:v:0 -map 1:a:0 -shortest $V $A "$out"
  fi
}

LIST="$TMP/list.txt"; : > "$LIST"
n=0
add() { echo "file '$1'" >> "$LIST"; }

echo "Carton titre…"
ffmpeg -nostdin -v error -y -f lavfi -i "color=c=0x0d0b1a:s=1080x1920:r=30:d=2.5" -f lavfi -i anullsrc=r=48000:cl=stereo -t 2.5 \
  -vf "$(dt "$TMP/title.txt" 150 '(h/2)-170' 0xff2e93),$(dt "$TMP/sub.txt" 56 '(h/2)+30'),fade=t=in:st=0:d=0.4,fade=t=out:st=2.1:d=0.4" \
  $V $A "$TMP/00-title.mp4"
add "$TMP/00-title.mp4"

for c in "${CLIPS[@]}"; do
  n=$((n+1)); printf 'Plan IA %d/%d : %s\n' "$n" "${#CLIPS[@]}" "$(basename "$c")"
  segment "$c" "$TMP/$(printf '%02d' "$n")-ia.mp4" "$LABEL_IA" "$TRIM"
  add "$TMP/$(printf '%02d' "$n")-ia.mp4"
done

if [[ $USE_GAME -eq 1 ]]; then
  if [[ -f "$GAME" ]]; then
    echo "Capture du jeu : $(basename "$GAME")"
    segment "$GAME" "$TMP/90-game.mp4" "$LABEL_REAL" 0
    add "$TMP/90-game.mp4"
  else
    echo "Capture du jeu absente ($GAME) : ignorée."
  fi
fi

echo "Carton de fin…"
ffmpeg -nostdin -v error -y -f lavfi -i "color=c=0x0d0b1a:s=1080x1920:r=30:d=3" -f lavfi -i anullsrc=r=48000:cl=stereo -t 3 \
  -vf "$(dt "$TMP/end.txt" 84 '(h/2)-120' 0x21e6ff),$(dt "$TMP/end2.txt" 44 '(h/2)+20'),fade=t=in:st=0:d=0.4" \
  $V $A "$TMP/99-end.mp4"
add "$TMP/99-end.mp4"

echo "Concaténation…"
ffmpeg -nostdin -v error -y -f concat -safe 0 -i "$LIST" -c copy "$TMP/concat.mp4"
DUR="$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$TMP/concat.mp4")"
FADE_ST="$(awk -v d="$DUR" 'BEGIN{s=d-2; if(s<0)s=0; printf "%.2f", s}')"

mkdir -p "$(dirname "$OUT")"
if [[ -n "$MUSIC" ]]; then
  echo "Musique + normalisation -16 LUFS…"
  ffmpeg -nostdin -v error -y -i "$TMP/concat.mp4" -stream_loop -1 -i "$MUSIC" -map 0:v -map 1:a -t "$DUR" \
    -af "afade=t=in:d=0.5,afade=t=out:st=$FADE_ST:d=2,loudnorm=I=-16:TP=-1.5:LRA=11" \
    -c:v copy $A -movflags +faststart "$OUT"
else
  echo "Normalisation du son -16 LUFS…"
  ffmpeg -nostdin -v error -y -i "$TMP/concat.mp4" -af "loudnorm=I=-16:TP=-1.5:LRA=11" \
    -c:v copy $A -movflags +faststart "$OUT"
fi

echo "OK : $OUT ($(printf '%.1f' "$DUR") s, 1080x1920, 30 i/s)"
