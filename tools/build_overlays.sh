#!/usr/bin/env bash
#
# Build transparent-background TEXT OVERLAY assets, one per beat, so the editor
# can drop them over the footage (and keep them if they work, or swap in their
# own if they don't). Two formats per overlay:
#   - <id>.png : transparent PNG (RGBA), universal (CapCut-friendly), static.
#   - <id>.mov : ProRes 4444 with alpha + 0.3s fade in/out, per-beat duration
#                (drop-in for Premiere / Resolve / Final Cut).
#
#   bash tools/build_overlays.sh atomic-mothers-day
#
# Output: output/<campaign>/overlays/. White text, soft shadow + outline for
# legibility over any footage, centered in the 9:16 safe zone (1080x1920).
#
# Edit the OVERLAYS list to match the campaign's shot-list copy. Fields are
# "id~duration~lines", where lines uses '|' for line breaks. Text is written to
# temp files and referenced via drawtext=textfile=... so apostrophes / colons /
# punctuation need no escaping.
set -e

CAMPAIGN="${1:?usage: build_overlays.sh <campaign>}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/output/$CAMPAIGN/overlays"
BUILD="$OUT/.build"
FFMPEG="$(command -v ffmpeg || echo "/c/Users/$USER/scoop/shims/ffmpeg.exe")"
FONT_SRC="/c/Windows/Fonts/arialbd.ttf"

W=1080; H=1920; FS=76; LH=112       # canvas, font size, line height

# --- Overlay copy: "id~seconds~line1|line2|line3" ------------------------------
OVERLAYS=(
  "01~3~Mom never liked that|tattoo anyway."
  "02~2~She still doesn't."
  "03~4~Start fresh."
  "04~4~Real results.|Real removal."
  "05~4~Mother's Day specials|Free consultation"
  "06~3~Book your free|consultation today|Atomic Tattoo Removal"
)
# ------------------------------------------------------------------------------

mkdir -p "$BUILD"; cp "$FONT_SRC" "$BUILD/font.ttf"; cd "$BUILD"

for row in "${OVERLAYS[@]}"; do
  IFS='~' read -r id dur lines <<< "$row"
  IFS='|' read -ra arr <<< "$lines"
  n=${#arr[@]}
  # Alpha must be carried from the INPUT (color=#00000000,format=rgba). Tacking
  # format=rgba onto -vf yields an OPAQUE black background — verified failure.
  filter=""
  for i in "${!arr[@]}"; do
    printf '%s' "${arr[$i]}" > "line${i}.txt"
    y=$(( (H - n*LH)/2 + i*LH ))
    filter="${filter:+$filter,}drawtext=fontfile=font.ttf:textfile=line${i}.txt:fontcolor=white:fontsize=${FS}:borderw=3:bordercolor=black@0.55:shadowcolor=black@0.6:shadowx=4:shadowy=4:x=(w-text_w)/2:y=${y}"
  done

  # Transparent PNG (single frame)
  "$FFMPEG" -y -loglevel error -f lavfi -i "color=c=#00000000:s=${W}x${H},format=rgba" \
    -frames:v 1 -vf "$filter" "$OUT/${id}.png"

  # ProRes 4444 MOV with alpha + fade in/out
  fout=$(awk "BEGIN{print $dur-0.3}")
  "$FFMPEG" -y -loglevel error -f lavfi -i "color=c=#00000000:s=${W}x${H}:d=${dur}:r=30,format=rgba" \
    -vf "${filter},fade=t=in:st=0:d=0.3:alpha=1,fade=t=out:st=${fout}:d=0.3:alpha=1" \
    -c:v prores_ks -profile:v 4444 -pix_fmt yuva444p10le "$OUT/${id}.mov"

  echo "  overlay ${id}: ${n} line(s), ${dur}s  -> ${id}.png + ${id}.mov"
  rm -f line*.txt
done

cd "$OUT"; rm -rf "$BUILD"
echo "DONE -> output/$CAMPAIGN/overlays/"
