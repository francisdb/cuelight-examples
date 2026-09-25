#!/usr/bin/env python3
"""Draw the images of the feature examples under features/images/.

    tools/feature_assets.py

badge.png is a star on a disc, coin.png a sprite sheet of a coin turning
once in eight 64x64 cells, four per row. Both are drawn at four times
their size and scaled down, which is all the antialiasing they get.

reel.png is a score reel for features/bindings/transitions: 160 cells of
48x64, ten per row, sixteen per digit, so frame 16 * d shows the digit d
and the fifteen after it show it rolling on to the next one. The window
looks at a drum: digits are squashed and darker towards its top and bottom. The digits are set
in the Oxanium of features/text/outline_font.

glow.png is a lamp glow for features/layers/blend_modes: an amber disc,
112x112, dense in the middle and fading to nothing at the rim.

badge.png, bulb.png and white_glow.png are for features/images/tint, both white so a
tint decides their color: a bulb in its socket, and the same disc as
glow.png without the amber. features/bindings/incandescent has its own
bulb.png and white_glow.png, for lamps whose filament decides the color. worn.png is a grey speckle, a grimy overlay
to multiply over clean art.

tile.png is a 48x48 floor tile for features/images/tile, a rounded
square with a dot that repeats without a seam.

For features/images/asset_paths, two skies both called sky.png, a day in
art/day/ and a night in art/night/, which the show names by
path, and moon.png in its assets/, which it names by stem.

Needs Pillow.
"""

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

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


def reel(cell=(48, 64), steps=16, half_angle=55):
    """The window shows a drum, not a flat strip: a row `y` from the middle
    is at the angle asin(y / radius) and shows what is `radius * angle`
    along the strip, so digits are squashed towards the top and the bottom
    and a little more than one digit's height is in view."""
    width, height = cell
    w, h = width * SS, height * SS
    font = ImageFont.truetype(str(ROOT / "features/text/outline_font/assets/fonts/Oxanium-Bold.ttf"), 50 * SS)
    # One tall strip: 9, then 0 to 9, then 0 and 1, a digit every `h`.
    strip = Image.new("RGBA", (w, h * 13), "#F2EEE0")
    draw = ImageDraw.Draw(strip)
    for i in range(13):
        draw.text((w / 2, (i + 0.5) * h), str((i - 1) % 10), font=font, fill="#15171C", anchor="mm")

    radius = h / 2 / math.sin(math.radians(half_angle))
    along = lambda y: radius * math.asin(max(-1.0, min(1.0, (y - h / 2) / radius)))
    bands = 64
    shade = Image.new("RGBA", cell, (0, 0, 0, 0))
    for y in range(height):  # the drum turns away from the light as well
        facing = math.cos(math.asin((y + 0.5 - height / 2) / (radius / SS)))
        ImageDraw.Draw(shade).line([(0, y), (width, y)], fill=(0, 0, 0, int(235 * (1 - facing**1.4))))

    sheet = Image.new("RGBA", (width * 10, height * steps), (0, 0, 0, 0))
    for frame in range(10 * steps):
        center = (frame / steps + 1.5) * h
        mesh = []
        for band in range(bands):
            y0, y1 = band * h / bands, (band + 1) * h / bands
            s0, s1 = center + along(y0), center + along(y1)
            mesh.append(((0, round(y0), w, round(y1)), (0, s0, 0, s1, w, s1, w, s0)))
        window = strip.transform((w, h), Image.MESH, mesh, Image.BILINEAR).resize(cell, Image.LANCZOS)
        window.alpha_composite(shade)
        sheet.paste(window, (frame % 10 * width, frame // 10 * height))
    # Cream to black takes few colors: a palette keeps the file small.
    return sheet.convert("RGB").quantize(128, dither=Image.Dither.NONE)


def glow(size=112):
    return disc(size, (255, 176, 0))


def bulb(size=96):
    """A white bulb in a socket, drawn big and scaled down."""
    s = size * SS
    image = Image.new("RGBA", (s, s), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse([0.16 * s, 0.04 * s, 0.84 * s, 0.72 * s], fill="#FFFFFF")
    draw.polygon(
        [(0.34 * s, 0.62 * s), (0.66 * s, 0.62 * s), (0.60 * s, 0.78 * s), (0.40 * s, 0.78 * s)],
        fill="#FFFFFF",
    )
    for i in range(3):
        y = (0.78 + i * 0.07) * s
        draw.rounded_rectangle(
            [0.38 * s, y, 0.62 * s, y + 0.045 * s], radius=0.02 * s, fill="#D0D0D0"
        )
    return image.resize((size, size), Image.LANCZOS)


def disc(size, color):
    """A soft disc: dense in the middle, gone at the rim."""
    image = Image.new("RGBA", (size, size), color + (0,))
    pixels = image.load()
    for y in range(size):
        for x in range(size):
            d = math.hypot(x + 0.5 - size / 2, y + 0.5 - size / 2) / (size / 2)
            pixels[x, y] = color + (int(255 * max(0.0, 1.0 - d * d) ** 2),)
    return image


def worn(size=128):
    """Grey speckle and streaks: clean where it is white, dirty where dark."""
    random.seed(21)
    image = Image.new("RGBA", (size, size), (255, 255, 255, 255))
    draw = ImageDraw.Draw(image)
    for _ in range(420):
        x, y = random.randint(0, size), random.randint(0, size)
        r = random.randint(1, 5)
        grey = random.randint(70, 190)
        draw.ellipse([x - r, y - r, x + r, y + r], fill=(grey, grey, grey, 255))
    for _ in range(14):
        y = random.randint(0, size)
        grey = random.randint(120, 200)
        draw.line([(0, y), (size, y + random.randint(-6, 6))], fill=(grey, grey, grey, 255), width=2)
    return image.filter(ImageFilter.GaussianBlur(0.6))


def sky(night, size=(176, 110)):
    """A small sky for features/images/asset_paths: a day with a sun, or a
    night with stars. Both are saved as sky.png, in different folders."""
    w, h = size
    top, bottom = ((14, 24, 58), (38, 52, 96)) if night else ((70, 140, 220), (170, 214, 245))
    image = Image.new("RGB", (w * SS, h * SS))
    draw = ImageDraw.Draw(image)
    for y in range(h * SS):
        f = y / (h * SS - 1)
        draw.line([(0, y), (w * SS, y)], fill=tuple(int(a + (b - a) * f) for a, b in zip(top, bottom)))
    if night:
        random.seed(5)
        for _ in range(30):
            x, y, r = random.uniform(0, w), random.uniform(0, h), random.uniform(0.6, 1.4)
            draw.ellipse([(x - r) * SS, (y - r) * SS, (x + r) * SS, (y + r) * SS], fill=(230, 236, 255))
    else:
        draw.ellipse([118 * SS, 18 * SS, 150 * SS, 50 * SS], fill=(255, 214, 102))
    return image.resize(size, Image.LANCZOS)


def moon(size=64):
    """A crescent moon on nothing, kept in assets/ and named by its stem."""
    image = Image.new("RGBA", (size * SS, size * SS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse([6 * SS, 6 * SS, 58 * SS, 58 * SS], fill=(253, 230, 138, 255))
    draw.ellipse([22 * SS, 0, 72 * SS, 50 * SS], fill=(0, 0, 0, 0))
    return image.resize((size, size), Image.LANCZOS)


def tile(size=48):
    """A floor tile for features/images/tile: a rounded square with a dot,
    its edges meeting the next tile's, so it repeats without a seam."""
    image = Image.new("RGBA", (size * SS, size * SS), (30, 38, 52, 255))
    draw = ImageDraw.Draw(image)
    m = 3 * SS
    draw.rounded_rectangle([m, m, size * SS - m, size * SS - m], radius=8 * SS, fill=(62, 201, 240, 255))
    c = size * SS / 2
    draw.ellipse([c - 7 * SS, c - 7 * SS, c + 7 * SS, c + 7 * SS], fill=(255, 176, 0, 255))
    return image.resize((size, size), Image.LANCZOS)


def main():
    for path, image in [
        ("features/images/image/assets/badge.png", badge()),
        ("features/images/sprite_sheet/assets/coin.png", coin_sheet()),
        ("features/bindings/transitions/assets/reel.png", reel()),
        ("features/layers/blend_modes/assets/glow.png", glow()),
        ("features/images/tint/assets/badge.png", badge()),
        ("features/images/tint/assets/bulb.png", bulb()),
        ("features/images/tint/assets/white_glow.png", disc(112, (255, 255, 255))),
        ("features/images/tint/assets/worn.png", worn()),
        ("features/bindings/incandescent/assets/bulb.png", bulb()),
        ("features/bindings/incandescent/assets/white_glow.png", disc(112, (255, 255, 255))),
        ("features/images/tile/assets/tile.png", tile()),
        ("features/images/asset_paths/art/day/sky.png", sky(False)),
        ("features/images/asset_paths/art/night/sky.png", sky(True)),
        ("features/images/asset_paths/assets/moon.png", moon()),
    ]:
        out = ROOT / path
        out.parent.mkdir(parents=True, exist_ok=True)
        image.save(out, optimize=True)
        print(out.relative_to(ROOT))


if __name__ == "__main__":
    main()
