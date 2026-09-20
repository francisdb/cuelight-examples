#!/usr/bin/env python3
"""Draw pinball_dmd's lightning flipbook: 8 frames of 128x24, stacked.

Each frame is a bolt from a fixed seed (midpoint displacement), a white
core inside a cyan glow, so the sheet is reproducible.

    tools/pinball_dmd_lightning.py pinball_dmd/assets/lightning.png

Needs Pillow.
"""

import random
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter

FRAMES = 8
WIDTH, HEIGHT = 128, 24
GLOW = (64, 224, 255)


def bolt(rng):
    points = [(-2.0, HEIGHT / 2), (WIDTH + 2.0, HEIGHT / 2)]
    spread = HEIGHT / 2.5
    while len(points) < 33:
        jagged = [points[0]]
        for (x0, y0), (x1, y1) in zip(points, points[1:]):
            y = (y0 + y1) / 2 + rng.uniform(-spread, spread)
            jagged += [((x0 + x1) / 2, min(max(y, 3), HEIGHT - 4)), (x1, y1)]
        points = jagged
        spread /= 1.5
    return points


def frame(rng):
    core = Image.new("L", (WIDTH, HEIGHT), 0)
    ImageDraw.Draw(core).line(bolt(rng), fill=255, width=1)
    glow = core.filter(ImageFilter.GaussianBlur(1.6)).point(lambda v: min(255, v * 4))
    alpha = ImageChops.lighter(core, glow)
    image = Image.new("RGBA", (WIDTH, HEIGHT), GLOW + (0,))
    image.putalpha(alpha)
    image.paste((255, 255, 255, 255), (0, 0), core)
    return image


def main():
    rng = random.Random(1)
    sheet = Image.new("RGBA", (WIDTH, HEIGHT * FRAMES), (0, 0, 0, 0))
    for index in range(FRAMES):
        sheet.paste(frame(rng), (0, index * HEIGHT))
    sheet.save(sys.argv[1], optimize=True)


if __name__ == "__main__":
    main()
