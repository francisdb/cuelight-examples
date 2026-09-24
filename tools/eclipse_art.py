#!/usr/bin/env python3
"""Write the artwork of eclipse: the corona.

    tools/eclipse_art.py eclipse/assets

corona.png is the sun's outer atmosphere around a hole the size of the
moon: long streamers near the equator, short plumes at the poles and fine
rays everywhere, falling off with the distance from the limb. It is drawn
with `screen` over the dark sky. The skies and the glows are gradients in
the show itself.

Needs numpy and Pillow.
"""

import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

# Sun radius in the sky window, as in tools/eclipse_show.py.
SUN_R = 100


def corona(size=560):
    rng = np.random.default_rng(7)
    c = (size - 1) / 2
    y, x = np.mgrid[0:size, 0:size]
    dx, dy = x - c, y - c
    r = np.hypot(dx, dy) / SUN_R
    a = np.arctan2(dy, dx)
    # Streamers: broad lobes near the equator (left and right), slightly
    # tilted, with a few narrower ones in between.
    lobes = np.zeros_like(a)
    for centre, width, strength in [
        (0.12, 0.28, 1.0), (math.pi + 0.1, 0.32, 0.9), (0.55, 0.14, 0.55),
        (-0.42, 0.16, 0.6), (math.pi - 0.5, 0.15, 0.5), (math.pi + 0.62, 0.12, 0.45),
        (2.1, 0.2, 0.25), (-2.2, 0.18, 0.3),
    ]:
        d = np.angle(np.exp(1j * (a - centre)))
        lobes += strength * np.exp(-((d / width) ** 2))
    # Fine rays: a sum of thin random spokes.
    rays = np.zeros_like(a)
    for _ in range(90):
        centre = rng.uniform(-math.pi, math.pi)
        d = np.angle(np.exp(1j * (a - centre)))
        rays += rng.uniform(0.05, 0.25) * np.exp(-((d / rng.uniform(0.01, 0.04)) ** 2))
    reach = 0.9 + 1.6 * lobes + 0.5 * rays
    over = np.clip(r - 1, 0, None)
    intensity = np.exp(-over / (0.22 * reach)) * (0.55 + 0.45 * np.clip(lobes + rays, 0, 1.4) / 1.4)
    # Brighter right at the limb, the inner corona.
    intensity += 0.6 * np.exp(-over / 0.05)
    intensity[r < 1] = 0
    # Fade out before the edge of the image so no square shows.
    edge = np.clip((c - np.hypot(dx, dy)) / 30, 0, 1)
    intensity = np.clip(intensity * edge, 0, 1)
    rgb = np.empty((size, size, 3))
    rgb[..., 0], rgb[..., 1], rgb[..., 2] = 236, 240, 255
    alpha = (intensity**0.9) * 255
    return Image.fromarray(np.dstack([rgb, alpha]).round().astype(np.uint8), "RGBA")


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    corona().save(out / "corona.png")


if __name__ == "__main__":
    main()
