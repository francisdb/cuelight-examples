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

Needs Pillow.
"""

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

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


def main():
    for path, image in [
        ("features/images/image/assets/badge.png", badge()),
        ("features/images/sprite_sheet/assets/coin.png", coin_sheet()),
        ("features/bindings/transitions/assets/reel.png", reel()),
    ]:
        out = ROOT / path
        out.parent.mkdir(parents=True, exist_ok=True)
        image.save(out, optimize=True)
        print(out.relative_to(ROOT))


if __name__ == "__main__":
    main()
