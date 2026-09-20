#!/usr/bin/env python3
"""Generate the space_crawl show: show.json, the star field and the logo.

cuelight has no perspective transform, so the crawl fakes one line by
line. Every line of text is its own layer moving away from the viewer at
a constant speed: at depth z (1 at the bottom edge of the screen) it is
scaled by `1 / z` and sits at `HORIZON + (BOTTOM - HORIZON) / z ** FLATTEN`.
True perspective would be FLATTEN = 1, but it also squashes distant lines
vertically, which a uniform scale cannot do: they would run into each
other. A smaller exponent keeps them apart, for slightly curved edges.
Each timeline samples these curves with a handful of keys, evenly spaced
on screen rather than in time.

    tools/space_crawl.py space_crawl --logo-font ArchivoBlack-Regular.ttf

Without --logo-font only show.json and the stars are written. Needs Pillow.
"""

import argparse
import json
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

WIDTH, HEIGHT = 1280, 720
YELLOW = "#FFD23F"
BLUE = "#4FC3E8"

INTRO = "Somewhere between two frames,\nnot very long ago...."
INTRO_IN, INTRO_HOLD, INTRO_OUT = 1.0, 3.5, 1.0

LOGO = ["CUE", "LIGHT"]
LOGO_START = 6.5
LOGO_TIME = 9.0
LOGO_FAR = 14.0  # depth at which the logo is gone

CRAWL = """\
Chapter 1
THE FIRST FRAME

Every display tells a story:
a score climbing, a door
opening, a machine waking up.

Too often that story is buried
in code, one hand-written
animation at a time.

cuelight keeps it in a single
document. Layers, timelines,
triggers and variables describe
the show; the host only says
what happened.

This crawl is such a document.
Each line is a text layer
with one timeline, shrinking
towards a point it will
never quite reach....
"""
CRAWL_START = 11.0
BOTTOM = HEIGHT + 20.0  # y where a line enters, at depth 1
TOP = 190.0  # y where a line is gone, at depth FADE_TO
FADE_FROM, FADE_TO = 2.6, 3.5  # depth range over which a line fades out
FLATTEN = 0.25
HORIZON = BOTTOM - (BOTTOM - TOP) / (1 - FADE_TO**-FLATTEN)  # y of the vanishing point
LINE_DEPTH = 0.165  # depth between two lines
SPEED = 0.11  # depth per second
KEYS = 12


def depth_keys(start, end, count=KEYS):
    """Depths from start to end, evenly spaced in 1/z: evenly in scale."""
    return [1 / (1 / start + (1 / end - 1 / start) * i / (count - 1)) for i in range(count)]


def screen_y(z):
    return HORIZON + (BOTTOM - HORIZON) / z**FLATTEN


def key(t, v):
    return {"t": round(t, 3), "v": round(v, 4)}


def crawl_line(index, text):
    depths = depth_keys(1.0, FADE_TO)
    times = [(z - 1.0) / SPEED for z in depths]
    return {
        "name": f"line_{index + 1}",
        "type": "text",
        "font": "crawl",
        "text": text,
        "x": WIDTH / 2,
        "y": BOTTOM,
        "anchor": "top",
        "timelines": [
            {
                "name": "recede",
                "autoplay": True,
                "delay": round(CRAWL_START + index * LINE_DEPTH / SPEED, 3),
                "tracks": [
                    {
                        "property": "y",
                        "keys": [key(t, screen_y(z)) for t, z in zip(times, depths)],
                    },
                    {"property": "scale", "keys": [key(t, 1 / z) for t, z in zip(times, depths)]},
                    {
                        "property": "opacity",
                        "keys": [
                            key(0, 1),
                            key((FADE_FROM - 1.0) / SPEED, 1),
                            key((FADE_TO - 1.0) / SPEED, 0),
                        ],
                    },
                ],
            }
        ],
    }


def logo_layer():
    depths = depth_keys(1.0, LOGO_FAR)
    times = [LOGO_TIME * (z - 1.0) / (LOGO_FAR - 1.0) for z in depths]
    return {
        "name": "logo",
        "type": "image",
        "image": "logo",
        "x": WIDTH / 2,
        "y": HEIGHT / 2,
        "anchor": "center",
        "opacity": 0,
        "timelines": [
            {
                "name": "recede",
                "autoplay": True,
                "delay": LOGO_START,
                "tracks": [
                    {"property": "scale", "keys": [key(t, 1 / z) for t, z in zip(times, depths)]},
                    {
                        "property": "opacity",
                        "keys": [
                            key(0, 1),
                            key(LOGO_TIME * 0.8, 1),
                            key(LOGO_TIME, 0),
                        ],
                    },
                ],
            }
        ],
    }


def show():
    lines = CRAWL.rstrip("\n").split("\n")
    end = CRAWL_START + (len(lines) * LINE_DEPTH + FADE_TO - 1.0) / SPEED
    layers = [
        {"name": "stars", "type": "image", "image": "stars"},
        {
            "name": "intro",
            "type": "text",
            "font": "intro",
            "text": INTRO,
            "x": WIDTH / 2,
            "y": HEIGHT / 2,
            "anchor": "center",
            "scale": 0.75,
            "opacity": 0,
            "timelines": [
                {
                    "name": "fade",
                    "autoplay": True,
                    "tracks": [
                        {
                            "property": "opacity",
                            "keys": [
                                key(0, 0),
                                key(INTRO_IN, 1),
                                key(INTRO_IN + INTRO_HOLD, 1),
                                key(INTRO_IN + INTRO_HOLD + INTRO_OUT, 0),
                            ],
                        }
                    ],
                }
            ],
        },
        logo_layer(),
    ]
    # Blank lines take their place in the crawl but need no layer.
    layers += [crawl_line(i, text) for i, text in enumerate(lines) if text.strip()]
    document = {
        "$schema": "https://raw.githubusercontent.com/francisdb/cuelight/main/crates/cuelight/schemas/show.schema.json",
        "format": 1,
        "name": "space_crawl",
        "size": [WIDTH, HEIGHT],
        "background": "#000000",
        "fonts": {
            "crawl": {"file": "libre_franklin_bold-56", "color": YELLOW},
            "intro": {"file": "libre_franklin_bold-56", "color": BLUE},
        },
        "scenes": [{"name": "crawl", "trigger": "crawl", "layers": layers}],
    }
    driver = {"loop": True, "steps": [{"trigger": "crawl"}, {"wait": round(end + 2.0, 1)}]}
    return document, driver


def stars():
    rng = random.Random(7)
    image = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
    draw = ImageDraw.Draw(image)
    for _ in range(900):
        x, y = rng.randrange(WIDTH), rng.randrange(HEIGHT)
        level = int(200 * rng.random() ** 2) + 55
        warmth = rng.uniform(-25, 25)
        color = tuple(max(0, min(255, int(c))) for c in (level + warmth, level, level - warmth))
        if rng.random() < 0.06:
            draw.ellipse((x - 1, y - 1, x + 1, y + 1), fill=color)
        else:
            draw.point((x, y), fill=color)
    glow = image.filter(ImageFilter.GaussianBlur(1.5))
    return ImageChops.add(image, glow)


def logo(font_path):
    """The logo as outlined letters, both rows stretched to the same width."""
    width, row_height, gap, stroke = 1100, 250, 30, 14
    rows = []
    for word in LOGO:
        font = ImageFont.truetype(str(font_path), 400)
        box = font.getbbox(word, stroke_width=stroke)
        row = Image.new("L", (box[2] - box[0], box[3] - box[1]), 0)
        ImageDraw.Draw(row).text((-box[0], -box[1]), word, font=font, fill=0, stroke_width=stroke, stroke_fill=255)
        rows.append(row.resize((width, row_height), Image.LANCZOS))
    alpha = Image.new("L", (width, 2 * row_height + gap), 0)
    for index, row in enumerate(rows):
        alpha.paste(row, (0, index * (row_height + gap)))
    image = Image.new("RGBA", alpha.size, YELLOW)
    image.putalpha(alpha)
    return image


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("show", type=Path, help="the show folder")
    parser.add_argument("--logo-font", type=Path, help="TrueType font to draw the logo with")
    args = parser.parse_args()

    document, driver = show()
    (args.show / "show.json").write_text(json.dumps(document, indent=2) + "\n")
    (args.show / "test-driver.json").write_text(json.dumps(driver, indent=2) + "\n")
    assets = args.show / "assets"
    assets.mkdir(exist_ok=True)
    stars().save(assets / "stars.png", optimize=True)
    if args.logo_font:
        logo(args.logo_font).save(assets / "logo.png", optimize=True)


if __name__ == "__main__":
    main()
