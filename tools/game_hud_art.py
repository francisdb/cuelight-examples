#!/usr/bin/env python3
"""Draw the pictures of the game_hud show.

    tools/game_hud_art.py

- dusk.png: the stand-in for the game behind the HUD, 960x540: a dusk
  sky from deep teal to amber, layers of mountains fading into mist, a
  ruined chapel on a hill and dark pines in front.
- map.png: the minimap's ground, 256x256: parchment with a river, a
  road, woods and the chapel, drawn to be turned under a fixed arrow.
- glow.png: a white disc fading to nothing, 128x128, for glows drawn
  with the add blend and tinted.
- orb_shade.png: 128x128, clear in the middle and dark towards the rim,
  laid over an orb's liquid so it reads as a glass ball.
- vignette.png: 320x180, white at the edges and clear in the middle, for
  the damage flash, tinted.
- icons: strike.svg, fireball.svg, ward.svg, heal.svg, frost.svg,
  potion.svg and crest.svg, flat shapes with no text in them.

Pictures are drawn at four times their size and scaled down, which is
all the antialiasing they get. Needs Pillow.
"""

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

UP = 4
OUT = Path(__file__).resolve().parent.parent / "game_hud" / "assets"

GOLD = "#C9A45C"
GOLD_DARK = "#7A5A24"
PARCHMENT = "#E9DDBF"


def lerp(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def ridge(width, base, rough, seed, points=9):
    """A mountain ridge by midpoint displacement: heights across the width."""
    random.seed(seed)
    heights = [base + random.uniform(-rough, rough) for _ in range(2)]
    spread = rough
    for _ in range(points):
        spread *= 0.55
        out = []
        for a, b in zip(heights, heights[1:]):
            out += [a, (a + b) / 2 + random.uniform(-spread, spread)]
        heights = out + [heights[-1]]
    return [heights[min(len(heights) - 1, int(x * (len(heights) - 1) / (width - 1)))] for x in range(width)]


def dusk():
    w, h = 960 * UP, 540 * UP
    image = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(image)
    stops = [(0.0, (16, 30, 44)), (0.45, (74, 58, 84)), (0.72, (196, 116, 86)), (0.82, (236, 172, 104)), (1.0, (236, 172, 104))]
    for y in range(h):
        t = y / h
        for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
            if t0 <= t <= t1:
                draw.line([(0, y), (w, y)], fill=lerp(c0, c1, (t - t0) / (t1 - t0)))
                break
    # A low sun behind the far range.
    sun = Image.new("L", (w, h), 0)
    ImageDraw.Draw(sun).ellipse([w * 0.62 - 90 * UP, h * 0.60 - 90 * UP, w * 0.62 + 90 * UP, h * 0.60 + 90 * UP], fill=255)
    sun = sun.filter(ImageFilter.GaussianBlur(60 * UP))
    image = Image.composite(Image.new("RGB", (w, h), (255, 214, 150)), image, sun.point(lambda v: v * 0.8))
    # Ranges from far to near, each darker and bluer, with mist between.
    ranges = [
        (0.62, 40, 11, (112, 84, 104)),
        (0.68, 55, 12, (84, 62, 86)),
        (0.76, 60, 13, (56, 42, 64)),
        (0.86, 45, 14, (34, 26, 42)),
    ]
    for i, (base, rough, seed, color) in enumerate(ranges):
        heights = ridge(w, base * h, rough * UP, seed)
        layer = Image.new("L", (w, h), 0)
        ld = ImageDraw.Draw(layer)
        ld.polygon([(0, h)] + [(x, heights[x]) for x in range(0, w, UP)] + [(w, h)], fill=255)
        image = Image.composite(Image.new("RGB", (w, h), color), image, layer)
        mist = Image.new("L", (w, h), 0)
        md = ImageDraw.Draw(mist)
        top = base * h + 10 * UP
        for d in range(40 * UP):
            md.line([(0, top + d), (w, top + d)], fill=round(70 * math.sin(math.pi * d / (40 * UP))))
        image = Image.composite(Image.new("RGB", (w, h), (200, 150, 140)), image, mist.filter(ImageFilter.GaussianBlur(8 * UP)))
        if i == 2:
            chapel(ImageDraw.Draw(image), w * 0.40, min(heights[int(w * 0.38):int(w * 0.46)]) + 6 * UP, color)
    # Pines in front, in the darkest color.
    random.seed(21)
    draw = ImageDraw.Draw(image)
    for _ in range(38):
        x = random.choice([random.uniform(0, w * 0.3), random.uniform(w * 0.7, w)])
        base = h - random.uniform(0, 30 * UP)
        tall = random.uniform(70, 150) * UP
        pine(draw, x, base, tall, (18, 14, 24))
    return image.resize((960, 540), Image.LANCZOS)


def chapel(draw, x, ground, color):
    """A ruined chapel: a nave with a broken roof and a bell tower."""
    s = UP
    draw.polygon([(x, ground), (x, ground - 34 * s), (x + 30 * s, ground - 52 * s), (x + 44 * s, ground - 40 * s),
                  (x + 52 * s, ground - 44 * s), (x + 60 * s, ground - 30 * s), (x + 60 * s, ground)], fill=color)
    draw.rectangle([x - 16 * s, ground - 70 * s, x, ground], fill=color)
    draw.polygon([(x - 18 * s, ground - 70 * s), (x - 8 * s, ground - 90 * s), (x + 2 * s, ground - 70 * s)], fill=color)
    window = lerp(color, (255, 190, 110), 0.6)
    draw.ellipse([x - 11 * s, ground - 60 * s, x - 5 * s, ground - 52 * s], fill=window)


def pine(draw, x, base, tall, color):
    trunk = tall * 0.12
    draw.rectangle([x - trunk * 0.12, base - trunk, x + trunk * 0.12, base], fill=color)
    tiers = 5
    for k in range(tiers):
        top = base - trunk - tall * (k + 1) / tiers * 0.95
        half = tall * 0.28 * (1 - k / tiers * 0.8)
        draw.polygon([(x, top - tall * 0.12), (x - half, top + tall * 0.18), (x + half, top + tall * 0.18)], fill=color)


def minimap():
    size = 256 * UP
    image = Image.new("RGB", (size, size), (222, 206, 168))
    draw = ImageDraw.Draw(image)
    random.seed(5)
    # Stains, so the parchment is not flat.
    for _ in range(60):
        r = random.uniform(10, 50) * UP
        cx, cy = random.uniform(0, size), random.uniform(0, size)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=lerp((222, 206, 168), (196, 172, 128), random.uniform(0.2, 0.6)))
    image = image.filter(ImageFilter.GaussianBlur(10 * UP))
    draw = ImageDraw.Draw(image)
    # Woods: clusters of little trees.
    for cx, cy, n in [(60, 70, 18), (190, 60, 14), (70, 200, 16), (200, 190, 10)]:
        for _ in range(n):
            x = (cx + random.uniform(-26, 26)) * UP
            y = (cy + random.uniform(-20, 20)) * UP
            draw.polygon([(x, y - 7 * UP), (x - 4 * UP, y + 3 * UP), (x + 4 * UP, y + 3 * UP)], fill=(96, 110, 70))
    # A river and a road.
    river = [(0, 150), (60, 140), (110, 160), (160, 130), (210, 150), (256, 120)]
    draw.line([(x * UP, y * UP) for x, y in river], fill=(92, 130, 150), width=7 * UP, joint="curve")
    road = [(128, 256), (126, 200), (140, 150), (132, 100), (150, 60), (170, 0)]
    draw.line([(x * UP, y * UP) for x, y in road], fill=(150, 116, 80), width=3 * UP, joint="curve")
    # The chapel the quest leads to.
    draw.rectangle([146 * UP, 52 * UP, 158 * UP, 62 * UP], fill=(70, 50, 44))
    draw.polygon([(144 * UP, 52 * UP), (152 * UP, 44 * UP), (160 * UP, 52 * UP)], fill=(70, 50, 44))
    return image.resize((256, 256), Image.LANCZOS)


def glow():
    size = 128
    image = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    pixels = image.load()
    for y in range(size):
        for x in range(size):
            r = math.hypot(x + 0.5 - size / 2, y + 0.5 - size / 2) / (size / 2)
            pixels[x, y] = (255, 255, 255, round(255 * max(0.0, 1 - r) ** 2))
    return image


def orb_shade():
    size = 128
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    pixels = image.load()
    for y in range(size):
        for x in range(size):
            r = math.hypot(x + 0.5 - size / 2, y + 0.5 - size / 2) / (size / 2)
            if r <= 1:
                pixels[x, y] = (8, 4, 10, round(235 * min(1.0, max(0.0, (r - 0.45) / 0.55)) ** 1.8))
    return image


def vignette():
    w, h = 320, 180
    image = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    pixels = image.load()
    for y in range(h):
        for x in range(w):
            dx = abs(x + 0.5 - w / 2) / (w / 2)
            dy = abs(y + 0.5 - h / 2) / (h / 2)
            d = max(dx, dy) * 0.6 + math.hypot(dx, dy) * 0.4
            pixels[x, y] = (255, 255, 255, round(255 * min(1.0, max(0.0, (d - 0.55) / 0.5)) ** 1.6))
    return image


def svg(body, size=64):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{size}" height="{size}">\n'
            + body + "\n</svg>\n")


ICONS = {
    # A sword, point up.
    "strike": svg(
        f'<path d="M 32 4 L 37 12 L 37 40 L 27 40 L 27 12 Z" fill="#D8DEE6"/>'
        f'<path d="M 32 6 L 32 40" stroke="#8A96A6" stroke-width="2"/>'
        f'<rect x="18" y="40" width="28" height="5" rx="2" fill="{GOLD}"/>'
        f'<rect x="29" y="45" width="6" height="11" fill="#6B4226"/>'
        f'<circle cx="32" cy="58" r="4" fill="{GOLD}"/>'),
    # A fireball with a tail.
    "fireball": svg(
        '<path d="M 50 12 C 40 18 30 16 22 24 C 12 34 14 50 28 54 C 44 58 54 44 48 32 C 46 26 48 18 50 12 Z" fill="#E8641E"/>'
        '<path d="M 40 26 C 34 28 26 30 24 38 C 22 46 30 50 36 46 C 42 42 42 34 40 26 Z" fill="#FFB43C"/>'
        '<circle cx="31" cy="42" r="5" fill="#FFF0B0"/>'),
    # A round shield with a boss.
    "ward": svg(
        f'<path d="M 32 6 L 54 14 C 54 36 46 50 32 58 C 18 50 10 36 10 14 Z" fill="#2E5FA8"/>'
        f'<path d="M 32 6 L 54 14 C 54 36 46 50 32 58 C 18 50 10 36 10 14 Z" fill="none" stroke="{GOLD}" stroke-width="4"/>'
        f'<circle cx="32" cy="28" r="7" fill="{GOLD}"/>'),
    # A leaf over a cross of light.
    "heal": svg(
        '<rect x="27" y="10" width="10" height="44" rx="3" fill="#7FE0A0"/>'
        '<rect x="10" y="27" width="44" height="10" rx="3" fill="#7FE0A0"/>'
        '<circle cx="32" cy="32" r="8" fill="#E8FFF0"/>'),
    # A six-pointed snowflake.
    "frost": svg("".join(
        f'<path d="M 32 32 L {32 + 24 * math.sin(math.radians(a)):.1f} {32 - 24 * math.cos(math.radians(a)):.1f}" '
        f'stroke="#BFE8FF" stroke-width="4" stroke-linecap="round"/>'
        f'<path d="M {32 + 14 * math.sin(math.radians(a)) - 6 * math.cos(math.radians(a)):.1f} '
        f'{32 - 14 * math.cos(math.radians(a)) - 6 * math.sin(math.radians(a)):.1f} '
        f'L {32 + 20 * math.sin(math.radians(a)):.1f} {32 - 20 * math.cos(math.radians(a)):.1f} '
        f'L {32 + 14 * math.sin(math.radians(a)) + 6 * math.cos(math.radians(a)):.1f} '
        f'{32 - 14 * math.cos(math.radians(a)) + 6 * math.sin(math.radians(a)):.1f}" '
        f'fill="none" stroke="#BFE8FF" stroke-width="3" stroke-linecap="round"/>'
        for a in range(0, 360, 60)) + '<circle cx="32" cy="32" r="5" fill="#FFFFFF"/>'),
    # A round flask of red potion.
    "potion": svg(
        '<rect x="26" y="6" width="12" height="6" rx="2" fill="#8A6A44"/>'
        '<path d="M 27 12 L 37 12 L 37 22 C 48 26 54 34 54 42 C 54 52 44 58 32 58 C 20 58 10 52 10 42 C 10 34 16 26 27 22 Z" fill="#CFD8E0" opacity="0.6"/>'
        '<path d="M 12 42 C 12 38 20 36 32 38 C 44 40 52 38 52 42 C 52 52 44 56 32 56 C 20 56 12 52 12 42 Z" fill="#C0283C"/>'
        '<circle cx="22" cy="32" r="3" fill="#FFFFFF" opacity="0.8"/>'),
    # The hero's crest: a gold lion-less heraldic star on a shield.
    "crest": svg(
        f'<path d="M 32 4 L 58 12 C 58 38 48 52 32 60 C 16 52 6 38 6 12 Z" fill="#6E1A26"/>'
        f'<path d="M 32 4 L 58 12 C 58 38 48 52 32 60 C 16 52 6 38 6 12 Z" fill="none" stroke="{GOLD}" stroke-width="3"/>'
        '<path d="' + " ".join(
            f'{"M" if k == 0 else "L"} {32 + (14 if k % 2 == 0 else 6) * math.sin(math.radians(k * 36)):.1f} '
            f'{30 - (14 if k % 2 == 0 else 6) * math.cos(math.radians(k * 36)):.1f}' for k in range(10)) + f' Z" fill="{GOLD}"/>'),
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    dusk().save(OUT / "dusk.png", optimize=True)
    minimap().save(OUT / "map.png", optimize=True)
    glow().save(OUT / "glow.png", optimize=True)
    orb_shade().save(OUT / "orb_shade.png", optimize=True)
    vignette().save(OUT / "vignette.png", optimize=True)
    for name, text in ICONS.items():
        (OUT / f"{name}.svg").write_text(text)


if __name__ == "__main__":
    main()
