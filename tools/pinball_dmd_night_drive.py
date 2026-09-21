#!/usr/bin/env python3
"""Draw the images of pinball_dmd's night drive video mode.

    tools/pinball_dmd_night_drive.py            # writes pinball_dmd/assets/nd_*.png
    tools/pinball_dmd_night_drive.py --keys     # prints the keys of a car's approach

- nd_sky.png     136x12, what is above the horizon: stars, a moon, a skyline
- nd_road.png    8 frames of 136x20 (4 per row): the road below the horizon.
                 Its stripes are one period further in every frame, so playing
                 the frames in a loop drives down the road
- nd_traffic.png 3 cars of 22x12 seen from behind, one per lane
- nd_player.png  the player's car, 24x12
- nd_crash.png   8 frames of 32x24 (4 per row): a fireball from a fixed seed

Sky and road are MARGIN pixels wider than the display on both sides, so
the show can shake them in a crash without baring an edge.

The road is the classic scanline trick: a scanline `d` of the way from the
horizon (0) to the bottom (1) is at distance z = 1 / d, the road is
`ROAD * d` wide there, and a stripe is what floor(z * STRIPES + phase) says.
A car follows the same rule, which is where --keys gets its numbers from:
at distance z its wheels are at y = HORIZON + 20 / z, it is 1 / z of its
size and its lane is LANE / z from the middle.

Needs Pillow.
"""

import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ASSETS = Path(__file__).resolve().parent.parent / "pinball_dmd" / "assets"
WIDTH, HORIZON, BELOW = 128, 12, 20
MARGIN = 4
FULL = WIDTH + 2 * MARGIN
ROAD = 70  # half the road's width at the bottom
LANE = 44  # a side lane's distance from the middle, at the bottom
STRIPES = 2.4
FRAMES = 8


def sky():
    image = Image.new("RGBA", (FULL, HORIZON), "#02030A")
    draw = ImageDraw.Draw(image)
    for y in range(HORIZON):
        glow = y / HORIZON
        draw.line([(0, y), (FULL, y)], fill=(int(4 + 22 * glow), int(4 + 10 * glow), int(16 + 40 * glow)))
    rng = random.Random(7)
    for _ in range(26):
        x, y = rng.randrange(FULL), rng.randrange(HORIZON - 4)
        level = rng.choice([90, 140, 220])
        image.putpixel((x, y), (level, level, min(255, level + 30), 255))
    draw.ellipse([50, 1, 56, 7], fill="#F2EBC0")
    draw.ellipse([48, 0, 53, 5], fill=(6, 5, 20))  # a crescent
    x = 0
    while x < FULL:
        width, height = rng.choice([3, 4, 5, 6]), rng.choice([2, 3, 4, 5, 6])
        if not 56 < x + width / 2 < 80:  # the road runs into a gap
            draw.rectangle([x, HORIZON - height, x + width - 1, HORIZON], fill="#0A0C1C")
            for wy in range(HORIZON - height + 1, HORIZON - 1, 2):
                for wx in range(x + 1, x + width - 1, 2):
                    if rng.random() < 0.4:
                        image.putpixel((wx, wy), (255, 196, 64, 255))
        x += width + rng.choice([0, 1])
    return image


def road():
    sheet = Image.new("RGBA", (FULL * 4, BELOW * 2), (0, 0, 0, 0))
    for frame in range(FRAMES):
        phase = 2 * frame / FRAMES
        for y in range(BELOW):
            d = (y + 0.5) / BELOW
            band = math.floor(STRIPES / d + phase) % 2
            half = ROAD * d + 1.5
            for x in range(FULL):
                off = abs(x + 0.5 - FULL / 2)
                if off > half + max(1.0, 3 * d):
                    color = (5, 26, 12) if band else (3, 16, 8)
                elif off > half:
                    color = (230, 230, 230) if band else (200, 30, 30)
                elif band and abs(off - half / 3) < max(0.5, 1.2 * d):
                    color = (235, 235, 200)
                else:
                    shade = int(34 + 22 * d)
                    color = (shade, shade, shade + 6)
                sheet.putpixel((frame % 4 * FULL + x, frame // 4 * BELOW + y), (*color, 255))
    return sheet


def car(draw, x, body, dark, width=22, lights="#FF2818"):
    right = x + width - 1
    draw.rectangle([x + 2, 9, x + 5, 11], fill="#08080A")  # wheels
    draw.rectangle([right - 5, 9, right - 2, 11], fill="#08080A")
    draw.rectangle([x + 4, 0, right - 4, 4], fill=body)  # cabin
    draw.rectangle([x + 6, 1, right - 6, 3], fill="#1A2A44")  # rear window
    draw.rectangle([x + 1, 4, right - 1, 10], fill=body)
    draw.rectangle([x + 1, 8, right - 1, 10], fill=dark)  # bumper
    draw.rectangle([x + 2, 5, x + 5, 6], fill=lights)
    draw.rectangle([right - 5, 5, right - 2, 6], fill=lights)
    draw.rectangle([x + 9, 6, right - 9, 7], fill="#D8D8C8")  # plate


def traffic():
    image = Image.new("RGBA", (22 * 3, 12), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    for i, (body, dark) in enumerate([("#2E6FD8", "#1A3F80"), ("#C8C8D0", "#70707A"), ("#2FA860", "#1A6038")]):
        car(draw, i * 22, body, dark)
    return image


def player():
    image = Image.new("RGBA", (24, 12), (0, 0, 0, 0))
    car(ImageDraw.Draw(image), 0, "#FFB000", "#9A5A00", width=24, lights="#FF5040")
    return image


def crash():
    cell = (32, 24)
    sheet = Image.new("RGBA", (cell[0] * 4, cell[1] * 2), (0, 0, 0, 0))
    rng = random.Random(3)
    sparks = [(rng.uniform(0, 2 * math.pi), rng.uniform(6, 15)) for _ in range(14)]
    for frame in range(FRAMES):
        image = Image.new("RGBA", cell, (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        t = (frame + 1) / FRAMES
        cx, cy = cell[0] / 2, cell[1] / 2 + 2
        for color, size in [("#C02808", 1.0), ("#FF8A10", 0.72), ("#FFE890", 0.4)]:
            r = 11 * math.sin(math.pi * min(t * 1.15, 1) ** 0.7) * size * (1 - 0.35 * t)
            if r > 0.6:
                draw.ellipse([cx - r * 1.2, cy - r, cx + r * 1.2, cy + r], fill=color)
        for angle, reach in sparks:
            x, y = cx + math.cos(angle) * reach * t * 1.3, cy + math.sin(angle) * reach * t - 3 * t
            if 0 <= x < cell[0] and 0 <= y < cell[1]:
                image.putpixel((int(x), int(y)), (255, 230, 120, int(255 * (1 - t * 0.7))))
        sheet.paste(image, (frame % 4 * cell[0], frame // 4 * cell[1]))
    return sheet


def keys(seconds=3.0, far=6.0, near=0.62):
    """A car coming closer at a steady speed, sampled where it matters."""
    print(f"lane offset {LANE}: x = 64 + offset / z, left lane -{LANE}, right lane +{LANE}")
    for z in [far, 4.5, 3.5, 2.7, 2.1, 1.7, 1.35, 1.1, 0.9, 0.75, near]:
        t = seconds * (far - z) / (far - near)
        print(f"t {t:5.2f}  y {HORIZON + BELOW / z:5.1f}  scale {1 / z:5.3f}  x offset {LANE / z:5.1f}")


def main():
    if "--keys" in sys.argv:
        return keys()
    for name, image in [("nd_sky", sky()), ("nd_road", road()), ("nd_traffic", traffic()), ("nd_player", player()), ("nd_crash", crash())]:
        image.save(ASSETS / f"{name}.png", optimize=True)
        print(f"pinball_dmd/assets/{name}.png {image.size}")


if __name__ == "__main__":
    main()
