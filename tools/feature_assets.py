#!/usr/bin/env python3
"""Draw the images of the feature examples under features/images/.

    tools/feature_assets.py

badge.png is a star on a disc, coin.png a sprite sheet of a coin turning
once in eight 64x64 cells, four per row. Both are drawn at four times
their size and scaled down, which is all the antialiasing they get.

Needs Pillow.
"""

import math
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SS = 4  # supersampling factor


def star(cx, cy, outer, inner, points=5):
    step = math.pi / points
    return [
        (cx + math.sin(i * step) * (inner if i % 2 else outer), cy - math.cos(i * step) * (inner if i % 2 else outer))
        for i in range(2 * points)
    ]


def badge(size=128):
    s = size * SS
    image = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse([2 * SS, 2 * SS, s - 2 * SS, s - 2 * SS], fill="#1B6CA8")
    draw.ellipse([10 * SS, 10 * SS, s - 10 * SS, s - 10 * SS], fill="#3EC9F0")
    draw.polygon(star(s / 2, s / 2 + 2 * SS, 0.36 * s, 0.15 * s), fill="#FFF4C2")
    return image.resize((size, size), Image.LANCZOS)


def coin_sheet(cell=64, frames=8, columns=4):
    rows = -(-frames // columns)
    sheet = Image.new("RGBA", (cell * columns, cell * rows), (0, 0, 0, 0))
    s = cell * SS
    for frame in range(frames):
        image = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        # Half a turn is enough: both faces look the same.
        turn = math.cos(math.pi * frame / frames)
        radius = 0.44 * s
        half = max(abs(turn) * radius, 0.05 * s)
        shade = "#FFB000" if turn >= 0 else "#D98E00"
        draw.ellipse([s / 2 - half, s / 2 - radius, s / 2 + half, s / 2 + radius], fill="#8A5A00")
        rim = 0.12
        draw.ellipse(
            [s / 2 - half * (1 - rim), s / 2 - radius * (1 - rim), s / 2 + half * (1 - rim), s / 2 + radius * (1 - rim)],
            fill=shade,
        )
        bar = half * 0.22
        draw.rectangle([s / 2 - bar, s / 2 - 0.5 * radius, s / 2 + bar, s / 2 + 0.5 * radius], fill="#FFE08A")
        small = image.resize((cell, cell), Image.LANCZOS)
        sheet.paste(small, ((frame % columns) * cell, (frame // columns) * cell))
    return sheet


def main():
    for path, image in [
        ("features/images/image/assets/badge.png", badge()),
        ("features/images/sprite_sheet/assets/coin.png", coin_sheet()),
    ]:
        out = ROOT / path
        out.parent.mkdir(parents=True, exist_ok=True)
        image.save(out, optimize=True)
        print(out.relative_to(ROOT))


if __name__ == "__main__":
    main()
