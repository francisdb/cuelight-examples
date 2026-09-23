#!/bin/sh
# Fetch boardwalk's font and recorded sounds, with their licenses.
#
#     tools/boardwalk_fetch.sh
#
# Sounds: the backbox's mechanics (a reel stepping, a coin, the knocker)
# are recordings from Kenney's RPG Audio and Impact Sounds packs, which are
# CC0, copied as they are. The chimes are synthesized by
# tools/boardwalk_sounds.py.
#
# League Gothic, for the reels (and the lettering tools/boardwalk_art.py
# paints on the glass), only comes as a variable font, so its normal
# width is cut out and trimmed to Latin-1 with fontTools (pip install
# fonttools). OFL 1.1 with no reserved font name.
set -eu

out=$(dirname "$0")/../boardwalk
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
mkdir -p "$out/assets/fonts" "$out/licenses"

ofl=https://raw.githubusercontent.com/google/fonts/main/ofl
curl -sfL -o "$tmp/LeagueGothic.ttf" "$ofl/leaguegothic/LeagueGothic%5Bwdth%5D.ttf"
curl -sfL -o "$out/licenses/LeagueGothic-OFL.txt" "$ofl/leaguegothic/OFL.txt"
fonttools varLib.instancer "$tmp/LeagueGothic.ttf" wdth=100 -o "$tmp/LeagueGothic-Regular.ttf" -q
pyftsubset "$tmp/LeagueGothic-Regular.ttf" \
  --unicodes="U+0020-007E,U+00A0-00FF,U+2013,U+2014,U+2018,U+2019,U+201C,U+201D,U+2022,U+2026" \
  --layout-features='kern,liga' --output-file="$out/assets/fonts/LeagueGothic-Regular.ttf"

kenney=https://kenney.nl/media/pages/assets
curl -sfL -o "$tmp/rpg.zip" "$kenney/rpg-audio/8e99002d76-1677590336/kenney_rpg-audio.zip"
curl -sfL -o "$tmp/impact.zip" "$kenney/impact-sounds/87b4ddecda-1677589768/kenney_impact-sounds.zip"
unzip -qo "$tmp/rpg.zip" -d "$tmp/rpg"
unzip -qo "$tmp/impact.zip" -d "$tmp/impact"
cp "$tmp/rpg/License.txt" "$out/licenses/Kenney-RPG-Audio-CC0.txt"
cp "$tmp/impact/License.txt" "$out/licenses/Kenney-Impact-Sounds-CC0.txt"
sounds="$out/assets/sounds"
mkdir -p "$sounds"
cp "$tmp/rpg/Audio/metalLatch.ogg" "$sounds/clack1.ogg"
cp "$tmp/impact/Audio/impactTin_medium_000.ogg" "$sounds/clack2.ogg"
cp "$tmp/rpg/Audio/handleCoins2.ogg" "$sounds/coin.ogg"
cp "$tmp/impact/Audio/impactWood_heavy_000.ogg" "$sounds/knocker.ogg"
