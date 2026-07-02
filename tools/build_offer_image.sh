#!/usr/bin/env bash
#
# Build static "offer" companion images for a Facebook campaign, in Meta's key
# sizes. Clean offer-card layout: hero photo on top + solid off-white offer panel
# on the bottom holding the brand logo and the offer text (reliable ffmpeg
# drawtext, not AI). Avoids cropping through faces or illegible scrims.
#
#   bash tools/build_offer_image.sh <campaign> [background.png]
#
# Default background: output/<campaign>/stills/scene-05.png. Output:
# output/<campaign>/offer-images/<size>.jpg
#
# Sizes: square 1080x1080 (Feed, primary), vertical 1080x1350 (4:5 Feed),
# story 1080x1920 (9:16). Edit TEXT / SIZES below.
set -e

CAMPAIGN="${1:?usage: build_offer_image.sh <campaign> [background]}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/output/$CAMPAIGN/offer-images"
BUILD="$OUT/.build"
BG="${2:-$ROOT/output/$CAMPAIGN/stills/scene-05.png}"
LOGO="$ROOT/brand/assets/logo.png"
FFMPEG="$(command -v ffmpeg || echo "/c/Users/$USER/scoop/shims/ffmpeg.exe")"
FFPROBE="$(command -v ffprobe || echo "/c/Users/$USER/scoop/shims/ffprobe.exe")"
FONT_SRC="/c/Windows/Fonts/arialbd.ttf"

# --- Offer card text (edit per campaign; '|' splits the hook into two lines) ---
HOOK="Mom never liked that|tattoo anyway."
OFFER="Free consultation + \$50 off"
URGENCY="Limited Mother's Day availability"
PANEL="0xF7F6F3"; C_HOOK="0x14263B"; C_OFFER="0xC0392B"; C_URG="0x666666"

# --- Target sizes: "name:W:H" ---
SIZES=( "square:1080:1080" "vertical:1080:1350" "story:1080:1920" )
PHOTO_FRAC=0.54     # top photo region as a fraction of height
# ------------------------------------------------------------------------------

[ -f "$BG" ] || { echo "Background not found: $BG"; exit 1; }
mkdir -p "$BUILD"; cp "$FONT_SRC" "$BUILD/font.ttf"; cd "$BUILD"
IFS='|' read -r HOOK1 HOOK2 <<< "$HOOK"
printf '%s' "$HOOK1" > h1.txt; printf '%s' "$HOOK2" > h2.txt
printf '%s' "$OFFER" > offer.txt; printf '%s' "$URGENCY" > urg.txt

i() { awk "BEGIN{printf \"%d\", $1}"; }   # float expr -> int

# Logo native aspect, so we can center it in the gap and never overlap the text.
IFS=',' read -r LOGO_WN LOGO_HN < <("$FFPROBE" -v error -select_streams v:0 \
  -show_entries stream=width,height -of csv=p=0 "$LOGO")

for spec in "${SIZES[@]}"; do
  IFS=':' read -r name W H <<< "$spec"
  REF=$(( W < H ? W : H ))
  PH=$(i "$H*$PHOTO_FRAC"); PANELH=$(( H - PH ))
  HFS=$(i "$REF*0.058"); OFS=$(i "$REF*0.045"); UFS=$(i "$REF*0.035")
  # text anchored from the bottom up so it always fits the panel
  Y_UR=$(i "$H - $PANELH*0.12")
  Y_OF=$(i "$Y_UR - $OFS*1.6")
  Y_H2=$(i "$Y_OF - $HFS*1.15")
  Y_H1=$(i "$Y_H2 - $HFS*1.15")
  # logo centered in the gap between the photo bottom (PH) and the hook top (Y_H1)
  LW=$(i "$W*0.30"); LOGOH=$(i "$LW*$LOGO_HN/$LOGO_WN")
  LOGOY=$(i "$PH + ($Y_H1 - $PH - $LOGOH)/2")

  DT="drawtext=fontfile=font.ttf:textfile=h1.txt:fontcolor=${C_HOOK}:fontsize=${HFS}:x=(w-text_w)/2:y=${Y_H1}"
  DT="${DT},drawtext=fontfile=font.ttf:textfile=h2.txt:fontcolor=${C_HOOK}:fontsize=${HFS}:x=(w-text_w)/2:y=${Y_H2}"
  DT="${DT},drawtext=fontfile=font.ttf:textfile=offer.txt:fontcolor=${C_OFFER}:fontsize=${OFS}:x=(w-text_w)/2:y=${Y_OF}"
  DT="${DT},drawtext=fontfile=font.ttf:textfile=urg.txt:fontcolor=${C_URG}:fontsize=${UFS}:x=(w-text_w)/2:y=${Y_UR}"

  "$FFMPEG" -y -loglevel error -i "$BG" -i "$LOGO" -filter_complex "\
color=c=${PANEL}:s=${W}x${H}:d=1[canvas];\
[0:v]scale=${W}:${PH}:force_original_aspect_ratio=increase,crop=${W}:${PH}:(iw-ow)/2:0,setsar=1[photo];\
[canvas][photo]overlay=0:0[base];\
[1:v]scale=${LW}:-1[logo];\
[base][logo]overlay=(W-w)/2:${LOGOY},${DT}" \
    -frames:v 1 -q:v 3 "$OUT/${name}.jpg"
  echo "  ${name}: ${W}x${H} -> ${name}.jpg"
done

cd "$OUT"; rm -rf "$BUILD"
echo "DONE -> output/$CAMPAIGN/offer-images/"
