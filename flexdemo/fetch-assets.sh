#!/usr/bin/env bash
# Fetch the flexdemo assets from the FlexDMD repository instead of committing
# them: the bitmap fonts' licenses do not allow redistribution.
#
# Needs curl and vpxtool (cargo install vpxtool).
set -euo pipefail

FLEXDMD_COMMIT=6357c1874e896777a53348094eafa86f386dd8fe
BASE="https://raw.githubusercontent.com/vbousquet/flexdmd/$FLEXDMD_COMMIT"
FONTS="bm_army-12 teeny_tiny_pixls-5 udmd-f7by13"
IMAGES="gy_background gy_girl gy_graveyard lightning"

cd "$(dirname "$0")"
mkdir -p assets/fonts
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

for font in $FONTS; do
  for ext in fnt png; do
    curl -fsSL "$BASE/FlexDMD/Resources/$font.$ext" -o "assets/fonts/$font.$ext"
  done
done

curl -fsSL "$BASE/FlexDemo/FlexDemo.vpx" -o "$tmp/FlexDemo.vpx"
vpxtool extract --force --output-dir "$tmp/extracted" --only 'images/*' "$tmp/FlexDemo.vpx" >/dev/null
for image in $IMAGES; do
  cp "$tmp/extracted/images/$image.png" "assets/$image.png"
done

echo "assets fetched into $(pwd)/assets"
