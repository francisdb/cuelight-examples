#!/usr/bin/env python3
"""Paint the boardwalk backglass.

    tools/boardwalk_art.py

- glass.png: the translite, 960x720, one picture in the manner of a
  seventies electromechanical game: a low sun throwing its rays over the
  sea, a roller coaster, a Ferris wheel, a lifeguard tower, people on
  the boardwalk, a biplane towing a banner, and along the front a row of
  arcade boards and a ticket booth with windows for the score reels.
  Flat, angular shapes with dark keylines in a silk-screen palette, the
  keylines a hair off register as on a screen-printed glass, and saved
  in a palette of 96 colours with a dither, which is both the grain of
  the print and what keeps the file small. Opaque except for the reel windows: the show
  multiplies it over the light behind it, so it only glows where a lamp
  burns.
- bulb.png: a lamp's light as it falls on the back of the glass, 128x128,
  white so the show tints it.
- reel_shade.png: 34x52, dark at the top and bottom, laid over a reel so
  it reads as a drum.
- sheen.png: 480x360, a faint diagonal reflection on the glass.
- mottle.png: 240x180, soft light and dark patches, multiplied into the
  light behind the glass: paint is never laid on evenly, so the same
  colour glows unevenly.
- wear.png: 960x720, dust, fine scratches and a few pinholes where the
  paint has flaked, on the front of the glass.
- title_mask.png and title_1.png to title_9.png: the title's letters as
  silhouettes, for the light behind the glass: the mask keeps the GI off
  the letters, and each letter has a lamp of its own shape. Where they
  sit is written to tools/boardwalk_title.json for tools/boardwalk_show.py.

The title is set in Shrikhand and the lettering in League Gothic
(boardwalk/assets/fonts, fetched by tools/boardwalk_fetch.sh). Shrikhand
is only needed here, so it is downloaded to a temporary folder; both are
OFL 1.1 with no reserved font name. Drawn at twice the size and scaled
down. Needs Pillow.
"""

import json
import math
import sys
import tempfile
import urllib.request
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from boardwalk_layout import (BALLOON, BANNER, BOARD_BOTTOM, BOARD_TOP, BOARD_W, BOARDS, BOOTH, CAPTIONS,  # noqa: E402
                              COASTER_CARS, CREAM, CREDIT_H, CREDIT_W, CREDITS, DECK, HEIGHT, HORIZON, INK, LAMPS,
                              MARQUEE_BULBS, MATCH_WHEEL, MUSTARD, ORANGE, PLANE, PLAYERS, RED, REEL_COUNT, REEL_H,
                              REEL_W, TEAL, TOWER, WHEEL_BULBS, WHEEL_CENTER, WHEEL_RADIUS, WIDTH)

UP = 2
ROOT = Path(__file__).resolve().parent.parent / "boardwalk"
OUT = ROOT / "assets"
GOTHIC = ROOT / "assets" / "fonts" / "LeagueGothic-Regular.ttf"
SHRIKHAND = "https://raw.githubusercontent.com/google/fonts/main/ofl/shrikhand/Shrikhand-Regular.ttf"

SKY = [(58, 118, 140), (86, 150, 164), (128, 176, 170), (196, 196, 160), (232, 206, 150)]
SEA = (22, 98, 108)
SEA_LIGHT = (70, 150, 150)
SAND = (226, 196, 140)
PLANK = (140, 92, 54)
PLANK_DARK = (106, 66, 38)
BROWN = (92, 58, 34)
SKIN = (232, 176, 128)

TITLE = "Boardwalk"
TITLE_AT = (34, 26)
TITLE_SIZE = 104
TITLE_STROKE = 6


def s(v):
    return v * UP


def sp(points):
    return [(s(x), s(y)) for x, y in points]


class Painter:
    """Two layers, as a screen printer would lay them down: flat colour,
    and the dark keylines on top, printed a hair off register."""

    def __init__(self, size):
        self.colour = Image.new("RGBA", size, (0, 0, 0, 255))
        self.lines = Image.new("RGBA", size, (0, 0, 0, 0))
        self.c = ImageDraw.Draw(self.colour)
        self.k = ImageDraw.Draw(self.lines)

    def poly(self, points, fill, line=3):
        pts = sp(points)
        self.c.polygon(pts, fill=fill)
        if line:
            self.k.line(pts + pts[:1], fill=INK, width=s(line), joint="curve")

    def rect(self, x, y, w, h, fill, line=3):
        self.poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], fill, line)

    def circle(self, cx, cy, r, fill, line=3):
        self.c.ellipse([s(cx - r), s(cy - r), s(cx + r), s(cy + r)], fill=fill)
        if line:
            self.k.ellipse([s(cx - r), s(cy - r), s(cx + r), s(cy + r)], outline=INK, width=s(line))

    def line(self, points, width=3, fill=INK):
        self.k.line(sp(points), fill=fill, width=s(width), joint="curve")

    def stroke(self, points, fill, width):
        self.c.line(sp(points), fill=fill, width=round(s(width)), joint="curve")

    def text(self, box, text, fill, font_path=GOTHIC):
        x, y, w, h = box
        lines = text.split("\n")
        size = s(h / len(lines) * 1.05)
        font = ImageFont.truetype(str(font_path), int(size))
        while max(font.getbbox(t)[2] - font.getbbox(t)[0] for t in lines) > s(w) * 0.92 and size > s(6):
            size -= 1
            font = ImageFont.truetype(str(font_path), int(size))
        line_h = s(h) / len(lines)
        for i, t in enumerate(lines):
            b = font.getbbox(t)
            tx = s(x) + (s(w) - (b[2] - b[0])) / 2 - b[0]
            ty = s(y) + i * line_h + (line_h - (b[3] - b[1])) / 2 - b[1]
            self.c.text((tx, ty), t, font=font, fill=fill)

    def finish(self):
        # The keylines a hair off register.
        return Image.alpha_composite(self.colour, ImageChops.offset(self.lines, UP // 2 + 1, UP // 2))


def sky(p):
    # Flat bands, as silk-screen colours are, darkest at the top.
    bands = [0, 90, 170, 250, 330, HORIZON]
    for k in range(len(bands) - 1):
        p.c.rectangle([0, s(bands[k]), s(WIDTH), s(bands[k + 1])], fill=SKY[k])
    # A dot screen where one band meets the next, so they blend in print.
    for k in range(1, len(bands) - 1):
        y0 = bands[k] - 22
        for row, y in enumerate(range(y0, bands[k], 5)):
            size = 0.4 + 1.8 * (y - y0) / 22
            for x in range((row % 2) * 3, WIDTH, 6):
                p.c.ellipse([s(x - size), s(y - size), s(x + size), s(y + size)], fill=SKY[k])
    # The sun's rays: long thin wedges from the horizon, a shade lighter.
    sun = (330, HORIZON)
    rays = Image.new("L", p.colour.size, 0)
    d = ImageDraw.Draw(rays)
    for k in range(-9, 10):
        a0, a1 = math.radians(k * 10 - 2.6), math.radians(k * 10 + 2.6)
        far = 1400
        d.polygon(sp([sun, (sun[0] + far * math.sin(a0), sun[1] - far * math.cos(a0)),
                      (sun[0] + far * math.sin(a1), sun[1] - far * math.cos(a1))]), fill=48)
    p.colour.paste(Image.new("RGBA", p.colour.size, (255, 236, 190, 255)), (0, 0), rays)
    # The sun itself, half set, in rings.
    for r, colour in [(96, ORANGE), (74, MUSTARD), (50, (246, 214, 120))]:
        p.c.pieslice([s(sun[0] - r), s(sun[1] - r), s(sun[0] + r), s(sun[1] + r)], 180, 360, fill=colour)
    p.k.arc([s(sun[0] - 96), s(sun[1] - 96), s(sun[0] + 96), s(sun[1] + 96)], 180, 360, fill=INK, width=s(3))


def clouds(p):
    for cx, cy, w in [(150, 176, 150), (520, 214, 120), (560, 280, 80), (250, 300, 90)]:
        p.poly([(cx - w / 2, cy), (cx - w / 4, cy - 16), (cx + w / 6, cy - 22), (cx + w / 2, cy),
                (cx + w / 4, cy + 7), (cx - w / 4, cy + 7)], CREAM, 2)


def sea(p):
    p.c.rectangle([0, s(HORIZON), s(WIDTH), s(470)], fill=SEA)
    # Angular waves in rows, closer together towards the horizon.
    for row, y in enumerate([412, 422, 436, 452]):
        step = 18 + row * 8
        pts = [(x, y + (0 if (x // step) % 2 else -3 - row)) for x in range(-step + row * 7, WIDTH + step, step)]
        p.stroke(pts, SEA_LIGHT, 2)
    # The sun's reflection, broken on the water.
    for k, y in enumerate(range(410, 468, 7)):
        w = 70 - k * 7
        p.c.rectangle([s(330 - w / 2), s(y), s(330 + w / 2), s(y + 3)], fill=MUSTARD)
    p.c.rectangle([0, s(470), s(WIDTH), s(DECK)], fill=SAND)
    p.line([(0, HORIZON), (WIDTH, HORIZON)], 2)


def coaster(p):
    track = [(12, 404), (44, 300), (82, 222), (100, 206)] + list(COASTER_CARS) + \
            [(292, 330), (322, 372), (352, 350), (388, 402)]
    # The trestle: straight posts and diagonal braces.
    for x, y in track[1:-1]:
        p.stroke([(x, y + 8), (x, 470)], CREAM, 3)
    for (x0, y0), (x1, y1) in zip(track[1:-1], track[2:-1]):
        p.stroke([(x0, y0 + 10), (x1, 470)], CREAM, 2)
    p.stroke([(x, y + 12) for x, y in track], INK, 9)
    p.stroke([(x, y + 12) for x, y in track], RED, 5)


def lifeguard_tower(p):
    x, y = TOWER
    for dx0, dx1 in [(-26, -40), (26, 40)]:
        p.stroke([(x + dx0, y + 20), (x + dx1, 470)], BROWN, 5)
    p.stroke([(x - 34, y + 90), (x + 34, y + 90)], BROWN, 4)
    p.poly([(x - 34, y + 20), (x + 34, y + 20), (x + 30, y - 20), (x - 30, y - 20)], CREAM)
    p.poly([(x - 42, y - 20), (x + 42, y - 20), (x, y - 50)], RED)


def ferris_wheel(p):
    cx, cy, r = WHEEL_CENTER[0], WHEEL_CENTER[1], WHEEL_RADIUS
    for dx in (-0.6, 0.6):
        p.stroke([(cx, cy), (cx + dx * r, DECK)], (200, 190, 170), 7)
        p.line([(cx, cy), (cx + dx * r, DECK)], 1)
    for k in range(16):
        a = 2 * math.pi * k / 16
        p.stroke([(cx, cy), (cx + r * math.sin(a), cy - r * math.cos(a))], CREAM, 2)
    p.c.ellipse([s(cx - r - 3), s(cy - r - 3), s(cx + r + 3), s(cy + r + 3)], outline=INK, width=s(9))
    p.c.ellipse([s(cx - r), s(cy - r), s(cx + r), s(cy + r)], outline=RED, width=s(4))
    p.c.ellipse([s(cx - r * 0.7), s(cy - r * 0.7), s(cx + r * 0.7), s(cy + r * 0.7)], outline=CREAM, width=s(3))
    p.circle(cx, cy, 14, RED)
    colours = [ORANGE, MUSTARD, TEAL, CREAM]
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        gx, gy = cx + r * math.sin(a), cy - r * math.cos(a)
        p.line([(gx, gy), (gx, gy + 10)], 2)
        p.poly([(gx - 14, gy + 10), (gx + 14, gy + 10), (gx + 10, gy + 30), (gx - 10, gy + 30)], colours[k % 4], 2)
    for x, y in WHEEL_BULBS:
        p.circle(x, y, 6, (250, 240, 214), 2)


def biplane(p):
    x, y = PLANE
    bx, by, bw, bh = BANNER
    p.line([(bx + bw, by + bh / 2), (x - 30, y)], 2)
    p.poly([(x - 30, y - 4), (x + 30, y - 6), (x + 38, y + 2), (x + 30, y + 8), (x - 30, y + 6)], RED)
    p.poly([(x - 8, y - 22), (x + 16, y - 22), (x + 14, y - 16), (x - 10, y - 16)], MUSTARD, 2)
    p.poly([(x - 10, y + 6), (x + 18, y + 6), (x + 16, y + 12), (x - 12, y + 12)], MUSTARD, 2)
    p.line([(x - 2, y - 16), (x - 2, y + 6)], 2)
    p.line([(x + 10, y - 16), (x + 10, y + 6)], 2)
    p.poly([(x + 30, y - 6), (x + 42, y - 18), (x + 44, y - 4)], RED, 2)
    p.poly([(x - 34, y - 12), (x - 30, y - 4), (x - 30, y + 6), (x - 34, y + 14)], CREAM, 2)
    p.circle(x + 4, y - 10, 5, TEAL, 2)


def person(p, x, y, height, shirt, legs, hat=None, arm_up=False):
    """An angular figure, feet at (x, y): a head, a trapeze of a body and
    straight limbs, as the stylized people of the time were drawn."""
    h = height
    head = h * 0.13
    p.stroke([(x - h * 0.06, y), (x - h * 0.05, y - h * 0.42)], legs, h * 0.07)
    p.stroke([(x + h * 0.06, y), (x + h * 0.05, y - h * 0.42)], legs, h * 0.07)
    p.poly([(x - h * 0.13, y - h * 0.42), (x + h * 0.13, y - h * 0.42), (x + h * 0.1, y - h * 0.78),
            (x - h * 0.1, y - h * 0.78)], shirt, 2)
    p.stroke([(x - h * 0.1, y - h * 0.74), (x - h * 0.2, y - h * 0.5)], SKIN, h * 0.05)
    if arm_up:
        p.stroke([(x + h * 0.1, y - h * 0.74), (x + h * 0.22, y - h * 0.98)], SKIN, h * 0.05)
    else:
        p.stroke([(x + h * 0.1, y - h * 0.74), (x + h * 0.2, y - h * 0.5)], SKIN, h * 0.05)
    p.poly([(x - head * 0.8, y - h * 0.8), (x + head * 0.8, y - h * 0.8), (x + head * 0.9, y - h * 0.8 - head * 1.5),
            (x - head * 0.7, y - h * 0.8 - head * 1.6)], SKIN, 2)
    if hat:
        top = y - h * 0.8 - head * 1.5
        p.poly([(x - head * 1.8, top + 2), (x + head * 1.8, top), (x + head, top - head * 0.8),
                (x - head, top - head * 0.7)], hat, 2)


def people(p):
    # A couple walking in front of the sea, a man in a boater, and a child
    # holding the balloon beside the Ferris wheel.
    person(p, 262, 508, 92, ORANGE, BROWN, hat=MUSTARD)
    person(p, 300, 510, 84, TEAL, CREAM, hat=CREAM)
    person(p, 584, 506, 88, CREAM, RED, hat=RED)
    person(p, 636, 508, 58, MUSTARD, TEAL, arm_up=True)
    p.line([(BALLOON[0], BALLOON[1] + BALLOON[3]), (648, 452)], 2)


def boardwalk(p):
    p.c.rectangle([0, s(DECK), s(WIDTH), s(HEIGHT)], fill=PLANK)
    for y in range(DECK, HEIGHT, 9):
        p.c.line([(0, s(y)), (s(WIDTH), s(y))], fill=PLANK_DARK, width=UP)
    p.rect(0, 490, WIDTH, 5, CREAM, 2)
    for x in range(0, WIDTH, 36):
        p.rect(x, 490, 5, DECK - 490, CREAM, 1)


def arcade(p):
    """The boards along the front, each a player's score, and the ticket
    booth with the fortune wheel on its roof."""
    for player, x in BOARDS:
        p.rect(x, BOARD_TOP, BOARD_W, BOARD_BOTTOM - BOARD_TOP, TEAL, 3)
        p.rect(x + 6, BOARD_TOP + 6, BOARD_W - 12, BOARD_BOTTOM - BOARD_TOP - 12, (26, 96, 98), 1)
        for k in range(8):
            w = BOARD_W / 8
            p.poly([(x + k * w, BOARD_TOP - 14), (x + (k + 1) * w, BOARD_TOP - 14), (x + (k + 1) * w, BOARD_TOP),
                    (x + k * w, BOARD_TOP)], RED if k % 2 else CREAM, 1)
    bx, by, bw = BOOTH
    p.rect(bx, by, bw, HEIGHT - by + 4, RED, 3)
    p.poly([(bx - 10, by), (bx + bw + 10, by), (bx + bw - 4, by - 26), (bx + 4, by - 26)], MUSTARD, 3)
    cx, cy, r, r0 = MATCH_WHEEL
    p.stroke([(cx, cy), (cx, by - 26)], BROWN, 6)
    p.circle(cx, cy, r + 6, INK, 0)
    p.circle(cx, cy, r0, RED, 2)
    p.text((cx - r0 + 2, cy - 8, 2 * r0 - 4, 16), "MATCH", CREAM)
    p.poly([(cx - 6, cy - r - 12), (cx + 6, cy - r - 12), (cx, cy - r + 2)], CREAM, 2)
    windows = [(x, y, REEL_W * REEL_COUNT, REEL_H) for _, x, y in PLAYERS] + \
              [(CREDITS[0], CREDITS[1], CREDIT_W * 2, CREDIT_H)]
    for x, y, w, h in windows:
        p.rect(x - 5, y - 5, w + 10, h + 10, MUSTARD, 2)


def marquee(p):
    p.c.rectangle([0, 0, s(WIDTH), s(32)], fill=RED)
    for k in range(0, WIDTH, 24):
        p.c.polygon(sp([(k, 32), (k + 24, 32), (k + 12, 44)]), fill=[CREAM, RED][(k // 24) % 2])
    p.line([(0, 32), (WIDTH, 32)], 2)
    for x, y in MARQUEE_BULBS:
        p.circle(x, y, 6, (250, 240, 214), 2)


def lamp_faces(p):
    for name, poly, text, face, ink, box, _, _ in LAMPS:
        p.poly(poly, face, 2)
        p.text(box, text, ink)
    for text, x, y, w, h in CAPTIONS:
        p.text((x, y, w, h), text, CREAM)


def title(p, font_path):
    font = ImageFont.truetype(str(font_path), s(TITLE_SIZE))
    x, y = s(TITLE_AT[0]), s(TITLE_AT[1])
    # A solid drop shadow, as a second screen, not a blur.
    p.c.text((x + s(7), y + s(7)), TITLE, font=font, fill=INK, stroke_width=s(TITLE_STROKE), stroke_fill=INK)
    p.c.text((x, y), TITLE, font=font, fill=ORANGE, stroke_width=s(TITLE_STROKE), stroke_fill=CREAM)
    # A lighter band through the letters, the way sign painters lit them.
    band = Image.new("L", p.colour.size, 0)
    ImageDraw.Draw(band).text((x, y), TITLE, font=font, fill=255)
    stripe = Image.new("L", p.colour.size, 0)
    ImageDraw.Draw(stripe).rectangle([0, y + s(TITLE_SIZE * 0.52), p.colour.size[0], y + s(TITLE_SIZE * 0.7)], fill=255)
    p.colour.paste(Image.new("RGBA", p.colour.size, MUSTARD + (255,)), (0, 0), ImageChops.multiply(band, stripe))


def glass(shrikhand):
    size = (s(WIDTH), s(HEIGHT))
    p = Painter(size)
    sky(p)
    clouds(p)
    sea(p)
    coaster(p)
    lifeguard_tower(p)
    ferris_wheel(p)
    biplane(p)
    boardwalk(p)
    people(p)
    arcade(p)
    marquee(p)
    title(p, shrikhand)
    lamp_faces(p)
    image = p.finish()
    # The reel windows are clear glass.
    d = ImageDraw.Draw(image)
    for x, y, w, h in [(x, y, REEL_W * REEL_COUNT, REEL_H) for _, x, y in PLAYERS] + \
                      [(CREDITS[0], CREDITS[1], CREDIT_W * 2, CREDIT_H)]:
        d.rectangle([s(x), s(y), s(x + w) - 1, s(y + h) - 1], fill=(0, 0, 0, 0))
    image = image.resize((WIDTH, HEIGHT), Image.LANCZOS)
    return image.quantize(96, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.FLOYDSTEINBERG)


def silhouettes(font_path):
    """The title's letters as white shapes, outline included: one image
    for the whole title and one per letter, cropped, with where they sit
    on the canvas."""
    font = ImageFont.truetype(str(font_path), s(TITLE_SIZE))
    x, y = s(TITLE_AT[0]), s(TITLE_AT[1])
    size = (s(WIDTH), s(HEIGHT))

    def shape(text, at):
        layer = Image.new("L", size, 0)
        ImageDraw.Draw(layer).text(at, text, font=font, fill=255, stroke_width=s(TITLE_STROKE), stroke_fill=255)
        box = layer.getbbox()
        box = [box[0] // UP * UP, box[1] // UP * UP, -(-box[2] // UP) * UP, -(-box[3] // UP) * UP]
        crop = layer.crop(box).resize(((box[2] - box[0]) // UP, (box[3] - box[1]) // UP), Image.LANCZOS)
        white = Image.new("RGBA", crop.size, (255, 255, 255, 0))
        white.putalpha(crop)
        return white, [box[0] // UP, box[1] // UP, crop.size[0], crop.size[1]]

    whole, whole_box = shape(TITLE, (x, y))
    letters = [shape(ch, (x + font.getlength(TITLE[:i]), y)) for i, ch in enumerate(TITLE)]
    return whole, whole_box, letters


def bulb_light():
    size = 128
    image = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    pixels = image.load()
    for y in range(size):
        for x in range(size):
            r = math.hypot(x + 0.5 - size / 2, y + 0.5 - size / 2) / (size / 2)
            # A hot core and a long soft shoulder: light through frosted glass.
            a = 0.65 * math.exp(-(r / 0.16) ** 2) + 0.55 * max(0.0, 1 - r) ** 2.2
            pixels[x, y] = (255, 255, 255, round(255 * min(1.0, a)))
    return image


def reel_shade():
    image = Image.new("RGBA", (REEL_W, REEL_H), (0, 0, 0, 0))
    pixels = image.load()
    for y in range(REEL_H):
        t = abs(y + 0.5 - REEL_H / 2) / (REEL_H / 2)
        a = round(235 * t ** 2.4)
        for x in range(REEL_W):
            edge = 1 if x in (0, REEL_W - 1) else 0
            pixels[x, y] = (20, 12, 6, min(255, a + edge * 120))
    return image


def sheen():
    w, h = 480, 360
    image = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    pixels = image.load()
    for y in range(h):
        for x in range(w):
            d = (x * 0.55 - y + 40) / 60
            pixels[x, y] = (255, 255, 255, round(22 * math.exp(-d * d)))
    return image


def mottle():
    """Low-frequency patches between about 0.75 and 1: smooth noise, made
    by blowing up a few random values and blurring them."""
    import random
    random.seed(12)
    small = Image.new("L", (12, 9))
    small.putdata([random.randint(190, 255) for _ in range(12 * 9)])
    big = small.resize((240, 180), Image.BICUBIC).filter(ImageFilter.GaussianBlur(10))
    return Image.merge("RGBA", [big, big, big, Image.new("L", big.size, 255)])


def wear():
    """Dust and scratches on the front of the glass, and pinholes where the
    paint has flaked and light gets through."""
    import random
    random.seed(21)
    image = Image.new("RGBA", (WIDTH, HEIGHT), (255, 255, 255, 0))
    d = ImageDraw.Draw(image)
    for _ in range(900):
        x, y = random.uniform(0, WIDTH), random.uniform(0, HEIGHT)
        r = random.uniform(0.3, 1.1)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 250, 240, random.randint(10, 40)))
    for _ in range(40):
        x, y = random.uniform(0, WIDTH), random.uniform(0, HEIGHT)
        a = random.uniform(-0.5, 0.5)
        length = random.uniform(20, 120)
        d.line([(x, y), (x + length * math.cos(a), y + length * math.sin(a))], fill=(255, 250, 240, random.randint(8, 22)),
               width=1)
    for _ in range(26):
        x, y = random.uniform(0, WIDTH), random.uniform(40, HEIGHT)
        r = random.uniform(0.6, 1.6)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 236, 200, 160))
    return image


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        shrikhand = Path(tmp) / "Shrikhand-Regular.ttf"
        urllib.request.urlretrieve(SHRIKHAND, shrikhand)
        glass(shrikhand).save(OUT / "glass.png", optimize=True)
        whole, whole_box, letters = silhouettes(shrikhand)
    whole.save(OUT / "title_mask.png", optimize=True)
    places = {"mask": whole_box, "letters": []}
    for i, (letter, box) in enumerate(letters, 1):
        letter.save(OUT / f"title_{i}.png", optimize=True)
        places["letters"].append(box)
    (Path(__file__).resolve().parent / "boardwalk_title.json").write_text(json.dumps(places, indent=2) + "\n")
    bulb_light().save(OUT / "bulb.png", optimize=True)
    reel_shade().save(OUT / "reel_shade.png", optimize=True)
    sheen().save(OUT / "sheen.png", optimize=True)
    mottle().save(OUT / "mottle.png", optimize=True)
    wear().save(OUT / "wear.png", optimize=True)


if __name__ == "__main__":
    main()
