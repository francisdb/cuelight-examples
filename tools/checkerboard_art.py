#!/usr/bin/env python3
"""Draw the artwork of checkerboard.

    tools/checkerboard_art.py checkerboard/assets

board.svg is a 17 by 17 checkerboard of 100 unit squares, 1700 across,
which is wider than the canvas's diagonal so it still covers the screen
when it is turned and zoomed out. The count is odd on purpose: it puts
the middle of a square at the centre the board turns about, and the four
neighbours of a square are all the same colour, so a quarter turn leaves
the same picture. With an even count the centre lands where four squares
meet, colours alternate around it, and every square changes colour on a
quarter turn. The squares are written out one by one:
cuelight has no way to tile a pattern, so a board is as many rectangles
as it has dark squares.

knight.svg is the piece that stands in front of it, a flat silhouette
with a lighter face, drawn as paths so it stays sharp at any size.
shadow.svg is the same outline in one dark colour, which the show lays
flat on the board as the piece's shadow.

vignette.png darkens the corners of the canvas, which a show cannot do
with shapes: it is a 160x90 image of an ellipse fading out, stretched
over the whole canvas.

Needs Pillow.
"""

import math
import sys
from pathlib import Path

from PIL import Image

LIGHT = "#D9D2BE"
DARK = "#252C3B"
PIECE = "#161C2B"
PIECE_FACE = "#38445C"
PIECE_EDGE = "#0A0D14"
SHADOW = "#05070C"

SQUARE = 100
SQUARES = 17
BOARD = SQUARE * SQUARES


def board():
    rects = [f'<rect x="0" y="0" width="{BOARD}" height="{BOARD}" fill="{LIGHT}"/>']
    for row in range(SQUARES):
        for col in range(SQUARES):
            if (row + col) % 2:
                rects.append(
                    f'<rect x="{col * SQUARE}" y="{row * SQUARE}" '
                    f'width="{SQUARE}" height="{SQUARE}" fill="{DARK}"/>'
                )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {BOARD} {BOARD}" '
        f'width="{BOARD}" height="{BOARD}">\n' + "\n".join(rects) + "\n</svg>\n"
    )


# The piece is a stack that shares its edges: the head's neck ends exactly
# where the collar begins, the collar where the base begins, and all three
# are centred on the same line.
HEAD = (
    "M 18 54 C 12 47 15 38 24 31 C 33 24 43 19 50 15 "
    "C 52 9 56 4 60 4 C 64 7 64 14 62 19 "
    "C 71 24 80 35 85 49 C 90 64 88 80 82 96 "
    "L 28 96 C 25 82 28 69 34 61 C 28 60 22 58 18 54 Z"
)
COLLAR = "M 22 106 H 88 L 82 96 H 28 Z"
BASE = "M 14 120 H 96 L 88 106 H 22 Z"
MANE = "M 62 19 C 72 26 81 37 85 49 C 77 45 70 43 63 42 C 64 34 64 26 62 19 Z"
EAR = "M 50 15 C 52 9 56 4 60 4 C 60 9 58 13 55 16 Z"


def piece_svg(body):
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 110 130" '
        'width="110" height="130">\n' + "\n".join(body) + "\n</svg>\n"
    )


def knight():
    """A knight facing left: base, collar, neck, head, muzzle, ear and
    mane, as flat shapes with a dark edge. It casts no shadow of its own;
    the show lays one on the board."""
    return piece_svg([
        f'<path d="{BASE}" fill="{PIECE}" stroke="{PIECE_EDGE}" stroke-width="3"/>',
        f'<path d="{COLLAR}" fill="{PIECE}" stroke="{PIECE_EDGE}" stroke-width="3"/>',
        f'<path d="{HEAD}" fill="{PIECE}" stroke="{PIECE_EDGE}" stroke-width="3"/>',
        f'<path d="{MANE}" fill="{PIECE_FACE}"/>',
        f'<path d="{EAR}" fill="{PIECE_FACE}"/>',
        f'<circle cx="41" cy="36" r="3.6" fill="{PIECE_FACE}"/>',
        f'<circle cx="21" cy="47" r="2.4" fill="{PIECE_FACE}"/>',
        f'<path d="M 20 55 C 26 57 31 58 36 58" fill="none" stroke="{PIECE_FACE}" stroke-width="2.5"/>',
        f'<path d="M 33 27 C 40 23 46 20 51 17" fill="none" stroke="{PIECE_FACE}" stroke-width="2.5" opacity="0.7"/>',
    ])


def shadow():
    """The same piece as one flat dark shape, for the show to lay on the
    board: flattened and scaled with it, it reads as the piece's shadow."""
    return piece_svg([
        f'<path d="{BASE}" fill="{SHADOW}"/>',
        f'<path d="{COLLAR}" fill="{SHADOW}"/>',
        f'<path d="{HEAD}" fill="{SHADOW}"/>',
    ])


def vignette(width=160, height=90):
    """Clear in the middle, dark towards the corners."""
    image = Image.new("RGBA", (width, height))
    pixels = image.load()
    for y in range(height):
        for x in range(width):
            dx = (x + 0.5 - width / 2) / (width / 2)
            dy = (y + 0.5 - height / 2) / (height / 2)
            d = min(1.0, math.hypot(dx, dy) / 1.25)
            pixels[x, y] = (4, 6, 12, int(255 * d ** 2.2))
    return image


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    (out / "board.svg").write_text(board())
    (out / "knight.svg").write_text(knight())
    (out / "shadow.svg").write_text(shadow())
    vignette().save(out / "vignette.png", optimize=True)
    print(f"board, knight, shadow and vignette in {out}")


if __name__ == "__main__":
    main()
