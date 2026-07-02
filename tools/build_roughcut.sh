#!/usr/bin/env bash
#
# Stage 006 OPTIONAL rough-cut assembler.
#
# Stitches a campaign's approved AI clips + AI_IMAGE stills into a single
# 1080x1920 / 30fps timeline, inserting labeled dark slates where REAL_FOOTAGE
# will go. A scratch timing preview for the editor — NOT the final ad (no baked
# text overlays, no audio).
#
#   bash tools/build_roughcut.sh atomic-mothers-day
#
# The BEATS list below IS the timeline — edit it to match the campaign's
# shot-list (order, durations, and which beats are clips / stills / slates).
#
# Requires ffmpeg (scoop: `scoop install ffmpeg`). Two Windows/msys gotchas this
# script already handles:
#   1. drawtext can't parse the "C:" in a Windows font path -> copy the font to
#      a colon-free local path and cd there so `fontfile=font.ttf` just works.
#   2. git-bash translates POSIX paths in ARGS but not inside the concat list
#      file -> use bare relative filenames in list.txt (cwd = segments dir).
set -e

CAMPAIGN="${1:?usage: build_roughcut.sh <campaign>}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/output/$CAMPAIGN"
SEG="$OUT/.segments"
FFMPEG="$(command -v ffmpeg || echo "/c/Users/$USER/scoop/shims/ffmpeg.exe")"
FONT_SRC="/c/Windows/Fonts/arialbd.ttf"

# --- Timeline: "type|arg|duration|line1|line2|line3" ---------------------------
# type: clip  -> arg is clips/<file>.mp4  (trimmed to duration)
#       still -> arg is stills/<file>.png (held for duration)
#       slate -> arg unused; line1/2/3 are the on-slate text
BEATS=(
  "clip|clips/scene-01.mp4|3"
  "clip|clips/scene-02.mp4|2"
  "slate||4|REAL FOOTAGE (film)|Laser in action|overlay - Start fresh."
  "slate||4|REAL FOOTAGE (film)|Before / After|overlay - Real results. Real removal."
  "clip|clips/scene-05.mp4|4"
  "still|stills/scene-06.png|3"
)
# ------------------------------------------------------------------------------

[ -d "$OUT" ] || { echo "No output folder: $OUT (run build_shot_list.py first)"; exit 1; }
mkdir -p "$SEG"
cp "$FONT_SRC" "$SEG/font.ttf"
cd "$SEG"
NORM="scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30"

i=0; : > list.txt
for beat in "${BEATS[@]}"; do
  IFS='|' read -r type arg dur l1 l2 l3 <<< "$beat"
  out="$(printf '%02d' "$i").mp4"
  case "$type" in
    clip)  "$FFMPEG" -y -loglevel error -ss 0 -t "$dur" -i "$OUT/$arg" \
             -vf "$NORM" -c:v libx264 -pix_fmt yuv420p -an "$out" ;;
    still) "$FFMPEG" -y -loglevel error -loop 1 -t "$dur" -i "$OUT/$arg" \
             -vf "$NORM" -c:v libx264 -pix_fmt yuv420p -an "$out" ;;
    slate) "$FFMPEG" -y -loglevel error -f lavfi -i "color=c=0x1c1c1e:s=1080x1920:d=$dur:r=30" \
             -vf "drawtext=fontfile=font.ttf:text='$l1':fontcolor=0xE64525:fontsize=54:x=(w-text_w)/2:y=(h/2)-220,drawtext=fontfile=font.ttf:text='$l2':fontcolor=white:fontsize=76:x=(w-text_w)/2:y=(h/2)-90,drawtext=fontfile=font.ttf:text='$l3':fontcolor=0x9fb4c9:fontsize=46:x=(w-text_w)/2:y=(h/2)+70" \
             -c:v libx264 -pix_fmt yuv420p -an "$out" ;;
    *) echo "unknown beat type: $type"; exit 1 ;;
  esac
  echo "file '$out'" >> list.txt
  echo "  beat $i: $type ${arg:-slate} (${dur}s)"
  i=$((i+1))
done

"$FFMPEG" -y -loglevel error -f concat -safe 0 -i list.txt -c copy "$OUT/rough-cut.mp4"
cd "$OUT"; rm -rf "$SEG"
echo "DONE -> output/$CAMPAIGN/rough-cut.mp4"
