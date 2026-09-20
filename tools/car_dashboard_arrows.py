#!/usr/bin/env python3
"""Draw car_dashboard's turn signal arrows: arrow_left.png and arrow_right.png.

cuelight shapes are rects and circles, and images are not tinted, so the
arrows are green images. They are drawn four times larger than the 72x56
they are shown at, so that they stay sharp when the player scales the
show up to a large window.

    tools/car_dashboard_arrows.py car_dashboard/assets

Needs Pillow.
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

WIDTH, HEIGHT = 288, 224
GREEN = (61, 220, 132)
SUPERSAMPLE = 4


def main():
    out = Path(sys.argv[1])
    w, h = WIDTH * SUPERSAMPLE, HEIGHT * SUPERSAMPLE
    # Pointing left: a triangular head and a shaft half as high.
    arrow = [
        (0, h / 2),
        (w * 0.5, 0),
        (w * 0.5, h * 0.27),
        (w, h * 0.27),
        (w, h * 0.73),
        (w * 0.5, h * 0.73),
        (w * 0.5, h),
    ]
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).polygon(arrow, fill=255)
    mask = mask.resize((WIDTH, HEIGHT), Image.LANCZOS)
    left = Image.new("RGBA", (WIDTH, HEIGHT), GREEN + (0,))
    left.putalpha(mask)
    left.save(out / "arrow_left.png", optimize=True)
    ImageOps.mirror(left).save(out / "arrow_right.png", optimize=True)


if __name__ == "__main__":
    main()
