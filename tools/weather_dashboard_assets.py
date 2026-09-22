#!/usr/bin/env python3
"""Write the artwork of weather_dashboard: SVG icons and sky gradients.

    tools/weather_dashboard_assets.py weather_dashboard/assets

The icons are SVG files in a 100x100 viewBox, built from a few primitives
(a disc, rays, a cloud, drops, flakes, a bolt, fog banks, a crescent,
wind streaks) as flat fills and strokes, which is what cuelight keeps of
an SVG. The parts the big "now" icon animates are separate files (sun,
sun_rays, cloud, cloud_dark, rain, snow, bolt, fog, moon, wind); the
forecast row shows one composed icon per condition (icon_sun, icon_partly,
icon_cloud, icon_rain, icon_storm, icon_snow, icon_fog).

rain.svg and snow.svg are 140x120 tiles of drops on a lattice: one column
every 20 units, each starting 12 lower than the one before. Shifting a
tile one column left and 48 down lands every drop where another one was,
so a layer moving that way in a clipped group falls forever without a
seam, and that step is the direction the drops lean.

sky_day.png, sky_dusk.png and sky_night.png are 8x360 vertical gradients,
stretched over the canvas: the only way to a gradient, since an SVG
gradient paints as its first stop.

Needs Pillow.
"""

import math
import sys
from pathlib import Path

from PIL import Image

SUN = "#FFD166"
CLOUD = "#F1F5F9"
CLOUD_DARK = "#94A3B8"
RAIN = "#60A5FA"
SNOW = "#E0F2FE"
BOLT = "#FDE047"
FOG = "#CBD5E1"
MOON = "#FDE68A"
WIND = "#E2E8F0"


def svg(body, width=100, height=100):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}">\n{body}\n</svg>\n'
    )


def disc(cx, cy, r, color):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}"/>'


def rays(cx, cy, inner, outer, width, color):
    out = []
    for i in range(8):
        out.append(
            f'<rect x="{cx - width / 2}" y="{cy - outer}" width="{width}" height="{outer - inner}" '
            f'rx="{width / 2}" fill="{color}" transform="rotate({i * 45} {cx} {cy})"/>'
        )
    return "\n".join(out)


def cloud(x, y, w, color):
    """A cloud w wide with its base at y, three lobes on a rounded bar."""
    h = w * 0.36
    return "\n".join(
        [
            f'<rect x="{x}" y="{y - h}" width="{w}" height="{h}" rx="{h / 2}" fill="{color}"/>',
            disc(x + w * 0.32, y - h * 1.15, w * 0.24, color),
            disc(x + w * 0.6, y - h * 1.35, w * 0.3, color),
        ]
    )


def drop(x, y, color, length=12):
    # A capsule leaning along SLANT, the way the tile travels.
    return (
        f'<rect x="{x - 2}" y="{y}" width="4" height="{length}" rx="2" fill="{color}" '
        f'transform="rotate({SLANT} {x} {y})"/>'
    )


def flake(x, y, r, color):
    return "\n".join(
        f'<rect x="{x - 1.2}" y="{y - r}" width="2.4" height="{2 * r}" rx="1.2" fill="{color}" '
        f'transform="rotate({a} {x} {y})"/>'
        for a in (0, 60, 120)
    )


def bolt(x, y, w, h, color):
    p = [
        (0.62, 0.0), (0.18, 0.56), (0.46, 0.56), (0.34, 1.0),
        (0.82, 0.4), (0.54, 0.4), (0.7, 0.0),
    ]
    points = " ".join(f"{x + px * w},{y + py * h}" for px, py in p)
    return f'<polygon points="{points}" fill="{color}"/>'


def fog(x, y, w, color):
    return "\n".join(
        f'<rect x="{x + dx}" y="{y + i * 14}" width="{w - dx - ex}" height="7" rx="3.5" '
        f'fill="{color}" opacity="{op}"/>'
        for i, (dx, ex, op) in enumerate([(0, 10, 0.9), (12, 0, 0.7), (4, 16, 0.5)])
    )


def moon(cx, cy, r, color):
    # Outer arc down the left, then back up along a wider circle that bulges
    # less: a crescent open to the right.
    x = cx + r * 0.25
    return (
        f'<path d="M {x} {cy - r} A {r} {r} 0 1 0 {x} {cy + r} '
        f'A {r * 1.3} {r * 1.3} 0 0 1 {x} {cy - r} Z" fill="{color}"/>'
    )


def wind(color):
    return "\n".join(
        f'<path d="{d}" fill="none" stroke="{color}" stroke-width="3.5"/>'
        for d in ("M 4 7 Q 40 7 66 4", "M 10 17 Q 46 17 92 11", "M 4 27 Q 34 27 58 24")
    )


# Drops every 20 units down a column and every 20 units across, each
# column starting 12 lower than the one before: a lattice, not a grid, so
# nothing lines up by eye. Shifting it by one column left and 48 down
# lands every drop where another one was, so a layer moving that way in a
# clipped group falls forever without a seam. That step is also the
# direction the drops lean.
PERIOD = 20
PHASE_STEP = 12
STEP = (-20, 48)
SLANT = round(math.degrees(math.atan2(-STEP[0], STEP[1])), 2)
TILE = (140, 120)


def falling(columns=7, rows=range(-1, 6)):
    """A drop per lattice point, covering the tile and the way it travels."""
    return [
        (10 + 20 * c, PERIOD * r + PHASE_STEP * c % PERIOD)
        for c in range(columns)
        for r in rows
    ]


def icons():
    files = {
        "sun": disc(50, 50, 30, SUN),
        "sun_rays": rays(50, 50, 36, 48, 7, SUN),
        "cloud": cloud(4, 82, 92, CLOUD),
        "cloud_dark": cloud(4, 82, 92, CLOUD_DARK),
        "bolt": bolt(0, 0, 100, 100, BOLT),
        "fog": fog(6, 30, 88, FOG),
        "moon": moon(50, 50, 40, MOON),
    }
    files["rain"] = "\n".join(
        drop(x, y, RAIN) for x, y in falling()
    )
    files["snow"] = "\n".join(
        flake(x, y, 5, SNOW) for x, y in falling()
    )
    files["wind"] = wind(WIND)

    # Composed icons for the forecast row.
    small_sun = disc(66, 34, 16, SUN) + "\n" + rays(66, 34, 20, 28, 4.5, SUN)
    files["icon_sun"] = disc(50, 50, 24, SUN) + "\n" + rays(50, 50, 30, 42, 6, SUN)
    files["icon_partly"] = small_sun + "\n" + cloud(6, 84, 70, CLOUD)
    files["icon_cloud"] = cloud(30, 58, 60, CLOUD_DARK) + "\n" + cloud(6, 84, 70, CLOUD)
    files["icon_rain"] = cloud(8, 62, 84, CLOUD_DARK) + "\n" + "\n".join(
        drop(x, 70, RAIN) for x in (30, 50, 70)
    )
    files["icon_storm"] = cloud(8, 62, 84, CLOUD_DARK) + "\n" + bolt(36, 62, 26, 34, BOLT)
    files["icon_snow"] = cloud(8, 62, 84, CLOUD) + "\n" + "\n".join(
        flake(x, 80, 6, SNOW) for x in (28, 50, 72)
    )
    files["icon_fog"] = cloud(14, 52, 72, CLOUD_DARK) + "\n" + fog(6, 60, 88, FOG)
    # The falling tiles are taller: a whole number of periods.
    return {
        name: svg(body, *TILE) if name in ("rain", "snow") else svg(body)
        for name, body in files.items()
    }


def gradient(stops, height=360):
    """A vertical gradient through (position 0..1, rgb) stops."""
    image = Image.new("RGB", (8, height))
    pixels = image.load()
    for y in range(height):
        f = y / (height - 1)
        for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
            if p0 <= f <= p1:
                t = (f - p0) / (p1 - p0) if p1 > p0 else 0
                color = tuple(int(a + (b - a) * t) for a, b in zip(c0, c1))
                break
        for x in range(8):
            pixels[x, y] = color
    return image


SKIES = {
    "sky_day": [(0.0, (46, 110, 190)), (0.6, (110, 170, 230)), (1.0, (168, 214, 245))],
    "sky_dusk": [(0.0, (24, 20, 70)), (0.5, (110, 50, 140)), (0.85, (235, 120, 70)), (1.0, (250, 180, 90))],
    "sky_night": [(0.0, (3, 7, 18)), (1.0, (18, 30, 62))],
}


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    for name, text in icons().items():
        (out / f"{name}.svg").write_text(text)
    for name, stops in SKIES.items():
        gradient(stops).save(out / f"{name}.png", optimize=True)


if __name__ == "__main__":
    main()
