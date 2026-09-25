#!/bin/sh
# Fetch the dragon backglass's fonts and its painting, with their licenses.
#
#     tools/dragon_fetch.sh
#
# Font: Dela Gothic One for all the lettering, OFL 1.1 with no reserved
# font name. It is a Japanese font of several megabytes, so it is cut to
# Latin with fontTools (pip install fonttools).
#
# The painting is Katsushika Hokusai's Dragon, public domain, from
# Wikimedia Commons; tools/dragon_art.py brings it down to the size the
# show draws it at.
set -eu

out=$(dirname "$0")/../dragon
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
mkdir -p "$out/assets/fonts" "$out/licenses"

latin="U+0020-007E,U+00A0-00FF,U+2013,U+2014,U+2018,U+2019,U+201C,U+201D,U+2022,U+2026"
fonts=https://raw.githubusercontent.com/google/fonts/main/ofl
curl -sfL -o "$tmp/DelaGothicOne-Regular.ttf" "$fonts/delagothicone/DelaGothicOne-Regular.ttf"
pyftsubset "$tmp/DelaGothicOne-Regular.ttf" --unicodes="$latin" --layout-features='kern,liga' \
  --output-file="$out/assets/fonts/DelaGothicOne-Regular.ttf"
curl -sfL -o "$out/licenses/DelaGothicOne-OFL.txt" "$fonts/delagothicone/OFL.txt"

python3 "$(dirname "$0")/dragon_art.py"
