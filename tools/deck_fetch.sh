#!/bin/sh
# Fetch the deck's fonts, with their licenses.
#
#     tools/deck_fetch.sh
#
# Archivo Black for the headings, Atkinson Hyperlegible for the text and
# DM Mono for code, all OFL 1.1 with no reserved font name, from
# google/fonts, as they come.
set -eu

out=$(dirname "$0")/../deck
mkdir -p "$out/assets/fonts" "$out/licenses"
fonts=https://raw.githubusercontent.com/google/fonts/main/ofl

fetch() {
  curl -sfL -o "$out/assets/fonts/$2" "$fonts/$1/$2"
}
fetch archivoblack ArchivoBlack-Regular.ttf
fetch atkinsonhyperlegible AtkinsonHyperlegible-Regular.ttf
fetch atkinsonhyperlegible AtkinsonHyperlegible-Bold.ttf
fetch dmmono DMMono-Regular.ttf
fetch dmmono DMMono-Medium.ttf

curl -sfL -o "$out/licenses/ArchivoBlack-OFL.txt" "$fonts/archivoblack/OFL.txt"
curl -sfL -o "$out/licenses/AtkinsonHyperlegible-OFL.txt" "$fonts/atkinsonhyperlegible/OFL.txt"
curl -sfL -o "$out/licenses/DMMono-OFL.txt" "$fonts/dmmono/OFL.txt"
