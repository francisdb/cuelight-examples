#!/bin/sh
# Fetch game_hud's fonts and recorded sounds, with their licenses.
#
#     tools/game_hud_fetch.sh
#
# Fonts: Cinzel Bold as its authors publish it. Alegreya only comes as a
# variable font, which is 425 KB, so it is cut to a static Regular and to
# Latin-1 with fontTools (pip install fonttools): 34 KB. Both are OFL 1.1;
# Cinzel's license reserves only the name "Cinzel Decorative", which is
# not used here, and Alegreya's reserves nothing.
#
# Sounds: a few recordings from Kenney's RPG Audio and Impact Sounds
# packs, which are CC0, copied as they are (Ogg Vorbis, 7 to 25 KB each)
# under names that say what they are for. The rest of the sounds are
# synthesized by tools/game_hud_sounds.py.
set -eu

out=$(dirname "$0")/../game_hud
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
mkdir -p "$out/assets/fonts" "$out/assets/sounds" "$out/licenses"

cinzel=https://raw.githubusercontent.com/NDISCOVER/Cinzel/master
curl -sfL -o "$out/assets/fonts/Cinzel-Bold.ttf" "$cinzel/fonts/ttf/Cinzel-Bold.ttf"
curl -sfL -o "$out/licenses/Cinzel-OFL.txt" "$cinzel/OFL.txt"

alegreya=https://raw.githubusercontent.com/google/fonts/main/ofl/alegreya
curl -sfL -o "$tmp/Alegreya.ttf" "$alegreya/Alegreya%5Bwght%5D.ttf"
curl -sfL -o "$out/licenses/Alegreya-OFL.txt" "$alegreya/OFL.txt"
fonttools varLib.instancer "$tmp/Alegreya.ttf" wght=400 -o "$tmp/Alegreya-Regular.ttf" -q
pyftsubset "$tmp/Alegreya-Regular.ttf" \
  --unicodes="U+0020-007E,U+00A0-00FF,U+2013,U+2014,U+2018,U+2019,U+201C,U+201D,U+2022,U+2026" \
  --layout-features='kern,liga' --output-file="$out/assets/fonts/Alegreya-Regular.ttf"

kenney=https://kenney.nl/media/pages/assets
curl -sfL -o "$tmp/rpg.zip" "$kenney/rpg-audio/8e99002d76-1677590336/kenney_rpg-audio.zip"
curl -sfL -o "$tmp/impact.zip" "$kenney/impact-sounds/87b4ddecda-1677589768/kenney_impact-sounds.zip"
unzip -qo "$tmp/rpg.zip" -d "$tmp/rpg"
unzip -qo "$tmp/impact.zip" -d "$tmp/impact"
cp "$tmp/rpg/License.txt" "$out/licenses/Kenney-RPG-Audio-CC0.txt"
cp "$tmp/impact/License.txt" "$out/licenses/Kenney-Impact-Sounds-CC0.txt"
sounds="$out/assets/sounds"
cp "$tmp/rpg/Audio/knifeSlice.ogg" "$sounds/swing1.ogg"
cp "$tmp/rpg/Audio/knifeSlice2.ogg" "$sounds/swing2.ogg"
cp "$tmp/impact/Audio/impactPlate_medium_000.ogg" "$sounds/clang1.ogg"
cp "$tmp/impact/Audio/impactPlate_medium_001.ogg" "$sounds/clang2.ogg"
cp "$tmp/impact/Audio/impactPlate_medium_002.ogg" "$sounds/clang3.ogg"
cp "$tmp/impact/Audio/impactPunch_heavy_000.ogg" "$sounds/hurt1.ogg"
cp "$tmp/impact/Audio/impactPunch_heavy_001.ogg" "$sounds/hurt2.ogg"
cp "$tmp/impact/Audio/impactSoft_heavy_000.ogg" "$sounds/fall.ogg"
cp "$tmp/impact/Audio/impactMetal_heavy_001.ogg" "$sounds/clatter1.ogg"
cp "$tmp/impact/Audio/impactMetal_heavy_002.ogg" "$sounds/clatter2.ogg"
cp "$tmp/impact/Audio/impactBell_heavy_000.ogg" "$sounds/bell.ogg"
cp "$tmp/rpg/Audio/handleCoins.ogg" "$sounds/coins.ogg"
