#!/usr/bin/env python3
"""Write the artwork of eclipse: sky gradients, the corona and a glow.

    tools/eclipse_art.py eclipse/assets

sky_day.png and sky_total.png are 8 pixel wide vertical gradients,
stretched over the sky window: the only way to a gradient, since an SVG
gradient paints as its first stop. horizon_glow.png is the band of sunset
that runs all around the horizon during totality, opaque at the bottom and
fading upward.

corona.png is the sun's outer atmosphere around a hole the size of the
moon: long streamers near the equator, short plumes at the poles and fine
rays everywhere, falling off with the distance from the limb. It is drawn
with `screen` over the dark sky.

glow.png is a soft white disc, transparent at the edge, tinted where it
is used: the sun's glare, the diamond ring.

Needs numpy and Pillow.
"""

import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

SKY_HEIGHT = 568
# Sun radius in the sky window, as in tools/eclipse_show.py.
SUN_R = 100


def gradient(stops, height):
    """A vertical gradient through (position 0..1, "#RRGGBB") stops."""
    ys = np.linspace(0, 1, height)
    pos = [p for p, _ in stops]
    rgb = [tuple(int(c[i : i + 2], 16) for i in (1, 3, 5)) for _, c in stops]
    cols = [np.interp(ys, pos, [c[k] for c in rgb]) for k in range(3)]
    img = np.stack(cols, axis=-1)[:, None, :].repeat(8, axis=1)
    return Image.fromarray(img.round().astype(np.uint8), "RGB")


def horizon_glow(height=160):
    ys = np.linspace(0, 1, height)[:, None]
    alpha = ys**2.2
    rgb = np.empty((height, 8, 3))
    top, bottom = np.array([232, 120, 90]), np.array([255, 178, 92])
    rgb[:] = (top + (bottom - top) * ys)[:, None, :]
    a = (alpha * 255).repeat(8, axis=1)[:, :, None]
    return Image.fromarray(np.concatenate([rgb, a], axis=-1).round().astype(np.uint8), "RGBA")


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


def glow(size=256):
    c = (size - 1) / 2
    y, x = np.mgrid[0:size, 0:size]
    r = np.hypot(x - c, y - c) / c
    alpha = np.clip(1 - r, 0, 1) ** 2.4
    rgb = np.full((size, size, 3), 255.0)
    return Image.fromarray(np.dstack([rgb, alpha * 255]).round().astype(np.uint8), "RGBA")


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    gradient([(0, "#4F8FCC"), (0.6, "#8DBDE6"), (1, "#CFE4F2")], SKY_HEIGHT).save(out / "sky_day.png")
    gradient([(0, "#070B1E"), (0.55, "#18203F"), (0.85, "#3B3452"), (1, "#5A4455")], SKY_HEIGHT).save(out / "sky_total.png")
    horizon_glow().save(out / "horizon_glow.png")
    corona().save(out / "corona.png")
    glow().save(out / "glow.png")


if __name__ == "__main__":
    main()
