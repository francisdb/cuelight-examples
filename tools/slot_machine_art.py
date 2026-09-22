#!/usr/bin/env python3
"""Draw the symbols and the drum shading of slot_machine.

    tools/slot_machine_art.py slot_machine/assets

Eight SVG symbols in a 100x100 viewBox, one per character of the reel's
ring: cherry (C), lemon (L), orange (O), plum (P), grapes (G), bell (B),
bar (A) and seven (7). They are drawn the way symbols on a real reel
strip are: one flat saturated colour per shape, a heavy dark outline
around it and a single highlight, which is what printing on a paper
strip allowed. Flat fills and strokes are also what cuelight keeps of an
SVG, and there is no text in them, so they need no fonts.

drum.png is the shading of the drum the strip is wrapped around: a
vertical strip, dark at the top and bottom and clear across the middle,
laid over a reel window so the symbols look wrapped rather than flat.
The strip itself is the cream of the reel backgrounds in the show, the
same look as the drum in features/bindings/transitions.
"""

import math
import sys
from pathlib import Path

from PIL import Image

INK = "#2A2118"          # the outline around every symbol
RED = "#D62F3C"
DARK_RED = "#9E1F28"
GREEN = "#2FA855"
DARK_GREEN = "#1F7038"
YELLOW = "#F2C21C"
DEEP_YELLOW = "#D9A310"
ORANGE = "#E87A17"
DARK_ORANGE = "#C05F0A"
PURPLE = "#7A4BE0"
DARK_PURPLE = "#5B2FB8"
GOLD = "#D9932A"
DEEP_GOLD = "#A96A12"
WHITE = "#FFFFFF"


def svg(body):
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" '
        f'width="100" height="100">\n{body}\n</svg>\n'
    )


def path(d, fill, width=3.5):
    return (
        f'<path d="{d}" fill="{fill}"/>\n'
        f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{width}" />'
    )


def disc(cx, cy, r, fill, width=3.5):
    return (
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"/>\n'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{INK}" stroke-width="{width}"/>'
    )


def highlight(cx, cy, rx, ry, angle=-30):
    return (
        f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{WHITE}" opacity="0.5" '
        f'transform="rotate({angle} {cx} {cy})"/>'
    )


def leaf(d):
    return path(d, GREEN, 3)


def cherry():
    """Two cherries on a forked stem with one leaf, the oldest symbol there is."""
    return "\n".join([
        f'<path d="M 50 22 C 40 38 32 50 30 62" fill="none" stroke="{DARK_GREEN}" stroke-width="6" stroke-linecap="round"/>',
        f'<path d="M 50 22 C 60 38 70 52 72 64" fill="none" stroke="{DARK_GREEN}" stroke-width="6" stroke-linecap="round"/>',
        leaf("M 50 22 C 60 8 78 6 88 12 C 78 24 62 26 50 22 Z"),
        disc(30, 74, 18, RED),
        disc(72, 76, 18, DARK_RED),
        highlight(23, 67, 7, 4),
    ])


def lemon():
    return "\n".join([
        path("M 12 52 C 12 36 30 26 50 26 C 70 26 88 36 88 52 C 88 68 70 78 50 78 C 30 78 12 68 12 52 Z", YELLOW),
        path("M 88 52 C 94 49 97 50 98 52 C 97 54 94 55 88 52 Z", DEEP_YELLOW, 2.5),
        path("M 12 52 C 6 49 3 50 2 52 C 3 54 6 55 12 52 Z", DEEP_YELLOW, 2.5),
        highlight(36, 41, 13, 6),
    ])


def orange():
    return "\n".join([
        disc(50, 58, 31, ORANGE),
        f'<path d="M 50 27 C 50 38 50 44 50 50" fill="none" stroke="{DARK_ORANGE}" stroke-width="3"/>',
        leaf("M 48 28 C 38 16 24 14 16 18 C 24 30 38 34 48 28 Z"),
        f'<rect x="46" y="14" width="7" height="16" rx="3.5" fill="{DARK_GREEN}" stroke="{INK}" stroke-width="3"/>',
        highlight(36, 46, 10, 6),
    ])


def plum():
    return "\n".join([
        path("M 50 26 C 70 26 82 42 82 58 C 82 76 68 88 50 88 C 32 88 18 76 18 58 C 18 42 30 26 50 26 Z", PURPLE),
        f'<path d="M 50 30 C 44 44 44 62 50 84" fill="none" stroke="{DARK_PURPLE}" stroke-width="4"/>',
        leaf("M 52 27 C 60 14 76 10 86 14 C 78 26 64 30 52 27 Z"),
        highlight(35, 46, 9, 6),
    ])


def grapes():
    out = [
        f'<path d="M 50 14 C 50 22 50 26 50 32" fill="none" stroke="{DARK_GREEN}" stroke-width="5" stroke-linecap="round"/>',
        leaf("M 52 18 C 62 6 78 4 88 9 C 79 20 64 24 52 18 Z"),
    ]
    for row, count in enumerate((3, 2, 1)):
        for i in range(count):
            cx = 50 + (i - (count - 1) / 2) * 23
            cy = 44 + row * 21
            out.append(disc(cx, cy, 13, PURPLE if (row + i) % 2 else DARK_PURPLE, 3))
    out.append(highlight(40, 39, 5, 3))
    return "\n".join(out)


def bell():
    """A liberty bell: a flared body, a band, a clapper and a crown."""
    return "\n".join([
        f'<rect x="44" y="8" width="12" height="10" rx="5" fill="{DEEP_GOLD}" stroke="{INK}" stroke-width="3"/>',
        path("M 50 16 C 68 16 74 34 76 50 C 78 62 82 68 86 72 H 14 C 18 68 22 62 24 50 C 26 34 32 16 50 16 Z", GOLD),
        path("M 14 72 H 86 V 80 H 14 Z", DEEP_GOLD, 3),
        disc(50, 88, 7, DEEP_GOLD, 3),
        highlight(36, 40, 6, 13, -12),
    ])


def bar():
    """Three stacked bars, the payline symbol every machine has."""
    out = []
    for i, color in enumerate((GOLD, YELLOW, GOLD)):
        y = 24 + i * 19
        out.append(path(f"M 17 {y} H 83 A 6 6 0 0 1 83 {y + 15} H 17 A 6 6 0 0 1 17 {y} Z", color, 3))
    return "\n".join(out)


def seven():
    return "\n".join([
        path("M 18 14 H 82 L 56 90 H 32 L 58 32 H 18 Z", RED),
        f'<path d="M 24 20 H 60 L 55 30 H 24 Z" fill="{WHITE}" opacity="0.28"/>',
    ])


SYMBOLS = {
    "cherry": cherry, "lemon": lemon, "orange": orange, "plum": plum,
    "grapes": grapes, "bell": bell, "bar": bar, "seven": seven,
}


def drum(width=8, height=300):
    """Dark at the edges, clear in the middle: the strip turning away from
    the light, the way the drum in features/bindings/transitions does."""
    image = Image.new("RGBA", (width, height))
    pixels = image.load()
    for y in range(height):
        f = abs(y / (height - 1) * 2 - 1)          # 0 in the middle, 1 at the edges
        alpha = int(205 * min(1.0, f ** 1.5))
        for x in range(width):
            pixels[x, y] = (12, 9, 6, alpha)
    return image


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    for name, draw in SYMBOLS.items():
        (out / f"{name}.svg").write_text(svg(draw()))
    drum().save(out / "drum.png", optimize=True)
    print(f"{len(SYMBOLS)} symbols and the drum shading in {out}")


if __name__ == "__main__":
    main()
