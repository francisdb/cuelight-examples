#!/usr/bin/env python3
"""Draw pinball_dmd's fireworks: four bursts of 8 frames, 32x32 each.

One row per color (gold, magenta, cyan, green), so a burst of color `row`
plays frames row * 8 to row * 8 + 7. Every burst throws the same sparks
from a fixed seed: they slow down, sag and fade, each with a dimmer pixel
where it was a moment ago, and the first frames have a white flash in the
middle.

    tools/pinball_dmd_fireworks.py pinball_dmd/assets/fireworks.png

Needs Pillow.
"""

import math
import random
import sys

from PIL import Image

FRAMES, CELL, SPARKS = 8, 32, 34
COLORS = [(255, 200, 40), (255, 60, 200), (60, 220, 255), (90, 255, 90)]


def spark_paths():
    rng = random.Random(11)
    paths = []
    for i in range(SPARKS):
        angle = 2 * math.pi * i / SPARKS + rng.uniform(-0.12, 0.12)
        reach = rng.choice([1.0, 1.0, 0.72, 0.45]) * rng.uniform(0.9, 1.05)
        paths.append((angle, reach))
    return paths


def position(angle, reach, t):
    out = 1 - (1 - t) ** 2.2  # fast at first, then slowing down
    return (
        CELL / 2 + math.cos(angle) * reach * 14.5 * out,
        CELL / 2 - 1 + math.sin(angle) * reach * 12.5 * out + 4.5 * t * t,
    )


def plot(image, x, y, color, level):
    """Fading is alpha, so a dim spark does not darken what is behind it."""
    x, y = int(round(x)), int(round(y))
    if 0 <= x < CELL and 0 <= y < CELL and level > 0.04:
        alpha = int(255 * min(level, 1.0))
        if alpha > image.getpixel((x, y))[3]:
            image.putpixel((x, y), (*color, alpha))


def burst(color, paths):
    frames = []
    for frame in range(FRAMES):
        image = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
        t = (frame + 1) / FRAMES
        fade = 1.0 if t < 0.5 else max(0.0, 1 - (t - 0.5) / 0.55)
        for angle, reach in paths:
            plot(image, *position(angle, reach, max(0.0, t - 0.1)), color, 0.4 * fade)
            head = tuple(min(255, c + 90) for c in color) if t < 0.4 else color
            plot(image, *position(angle, reach, t), head, fade)
        if frame < 2:
            for dx, dy in [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)][: 5 - 4 * frame]:
                plot(image, CELL / 2 + dx, CELL / 2 - 1 + dy, (255, 255, 255), 1.0)
        frames.append(image)
    return frames


def main():
    paths = spark_paths()
    sheet = Image.new("RGBA", (CELL * FRAMES, CELL * len(COLORS)), (0, 0, 0, 0))
    for row, color in enumerate(COLORS):
        for column, image in enumerate(burst(color, paths)):
            sheet.paste(image, (column * CELL, row * CELL))
    sheet.save(sys.argv[1], optimize=True)
    print(f"{sys.argv[1]} {sheet.size}")


if __name__ == "__main__":
    main()
