#!/bin/sh
# Fetch red_riding_hood's fonts, with their license.
#
#     tools/red_riding_hood_fetch.sh
#
# Fonts: IM Fell English (regular and italic) and IM Fell French Canon,
# the unmodified files from google/fonts at a fixed commit. OFL 1.1 with
# no reserved font name.
#
# The page turns are synthesized by tools/red_riding_hood_sounds.py.
set -eu

out=$(dirname "$0")/../red_riding_hood
mkdir -p "$out/assets/fonts" "$out/licenses"

fonts=https://raw.githubusercontent.com/google/fonts
english=$fonts/8d618a0e96499047423510abb2c5ee9f475b987a/ofl/imfellenglish
canon=$fonts/3b3145a92153418d09d62971e8238ad5bec48ca3/ofl/imfellfrenchcanon
curl -sfL -o "$out/assets/fonts/IMFellEnglish-Regular.ttf" "$english/IMFeENrm28P.ttf"
curl -sfL -o "$out/assets/fonts/IMFellEnglish-Italic.ttf" "$english/IMFeENit28P.ttf"
curl -sfL -o "$out/assets/fonts/IMFellFrenchCanon-Regular.ttf" "$canon/IMFeFCrm28P.ttf"
curl -sfL -o "$out/licenses/IMFell-OFL.txt" "$english/OFL.txt"

