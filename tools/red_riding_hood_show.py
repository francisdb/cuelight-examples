#!/usr/bin/env python3
"""Write red_riding_hood's show.json and test-driver.json.

    tools/red_riding_hood_show.py red_riding_hood

An open picture book: the story on the left page, a picture on the
right. Every page is a scene (`cover`, `page_1` ... `page_8`), entered by
its trigger, and entering one turns the page: a blank leaf lifts off the
right page, swings over the spine and settles on the left, where it
fades into the new text, with a rustle.

Each page has one word printed in red, and a trigger named after it
(`tap_hood`, `tap_basket`, ...) that makes the picture do something: the
wolf shows its teeth, the flowers bob, Grandma peeks out. The driver
fires them for now; once shows can be touched, tapping the word will.
For that the red word is a text layer of its own: lines are laid out
here, word by word, with the font's advance widths, which is exactly how
the engine places glyphs (no kerning), so every word's box is known.

The pictures are built from the parts tools/red_riding_hood_art.py
draws. Small things move all the time, on looping timelines with their
own periods and delays so nothing moves in step: grass and flowers
sway, the girl's head bobs, the wolf blinks and wags, smoke rises.
"""

import json
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

W, H = 1280, 720
INK = "#2B211C"
PAPER = "#EFE3C6"
RED = "#A8322A"
MUTED = "#7A6A58"
BOOK = (70, 48, 1210, 680)  # left, top, right, bottom of the open book
SPINE = 640
PLATE = (690, 96, 470, 520)  # the picture on the right page: x, y, width, height
TEXT_X, TEXT_W = 124, 472
TEXT_Y = 150
BODY_SIZE, LINE = 40, 64
CAP_SIZE = 138

FONTS = Path(__file__).resolve().parent.parent / "red_riding_hood" / "assets" / "fonts"


class Measure:
    """Advance widths, as the engine places glyphs."""

    def __init__(self, name):
        font = TTFont(FONTS / f"{name}.ttf")
        self.cmap = font.getBestCmap()
        self.hmtx = font["hmtx"]
        self.upem = font["head"].unitsPerEm
        hhea = font["hhea"]
        self.ascent, self.descent = hhea.ascent, hhea.descent

    def width(self, text, size):
        return sum(self.hmtx[self.cmap[ord(ch)]][0] for ch in text) * size / self.upem

    def height(self, size):
        return (self.ascent - self.descent) * size / self.upem


BODY = Measure("IMFellEnglish-Regular")
CAP = Measure("IMFellFrenchCanon-Regular")


def r(v, digits=2):
    v = round(v, digits)
    return int(v) if v == int(v) else v


# -- Timelines ---------------------------------------------------------------

def tl(name, prop, keys, trigger=None, autoplay=False, loop=False, delay=None, hold=False):
    t = {"name": name}
    if trigger:
        t["trigger"] = trigger
    if autoplay:
        t["autoplay"] = True
    if loop:
        t["loop"] = True
    if delay:
        t["delay"] = delay
    if hold:
        t["hold"] = True
    out = []
    for k in keys:
        key = {"t": r(k[0], 3), "v": r(k[1], 3)}
        if len(k) > 2:
            key["ease"] = k[2]
        out.append(key)
    t["tracks"] = [{"property": prop, "keys": out}]
    return t


def swing(name, prop, low, high, period, delay=0, ease="quad_in_out"):
    """Back and forth between low and high, forever."""
    return tl(name, prop, [(0, low), (period / 2, high, ease), (period, low, ease)], autoplay=True, loop=True,
              delay=delay or None)


def blink(name, every, delay=0):
    return tl(name, "scale_y", [(0, 1), (every - 0.16, 1), (every - 0.08, 0.1), (every, 1)],
              autoplay=True, loop=True, delay=delay or None)


def vec(name, vector, x, y, anchor=None, scale=None, timelines=None, **extra):
    layer = {"name": name, "type": "vector", "vector": vector, "x": r(x), "y": r(y)}
    if anchor:
        layer["anchor"] = anchor
    if scale:
        layer["scale"] = scale
    layer.update(extra)
    if timelines:
        layer["timelines"] = timelines
    return layer


def group(name, x, y, children, timelines=None, **extra):
    layer = {"name": name, "type": "group", "x": r(x), "y": r(y)}
    layer.update(extra)
    if timelines:
        layer["timelines"] = timelines
    layer["children"] = children
    return layer


def circle(name, x, y, radius, fill, **extra):
    return {"name": name, "type": "shape", "x": r(x), "y": r(y), "shape": {"circle": [0, 0, radius]},
            "fill": fill, **extra}


# -- Characters, built from their parts ---------------------------------------

def red(x, y, scale=1.0, facing=1, tap=None, bob_delay=0.0, basket=True):
    """The girl, her feet at (x, y). A tap on "red hood" makes her twirl."""
    twirl = []
    if tap:
        twirl = [tl("twirl", "scale_x", [(0, facing), (0.35, -facing, "quad_in_out"), (0.7, facing, "quad_in_out")],
                    trigger=tap)]
    parts = [
        vec("body", "red_body", -60, -152),
        vec("head", "red_head", 2, -146, anchor="bottom",
            timelines=[swing("bob", "rotation", -3, 4, 3.2, bob_delay)]),
    ]
    if basket:
        parts += [
            vec("basket", "basket", 36, -88, anchor="top",
                timelines=[swing("sway", "rotation", -5, 5, 2.4, bob_delay + 0.4)]),
            circle("hand", 36, -86, 6, "#F2D2B0", stroke={"color": INK, "width": 2.5}),
        ]
    return group("red", x, y, parts, timelines=twirl, scale=scale, scale_x=facing)


def wolf_head(x, y, eye_scale=1.0, cap=False, tilt=True, jaw_tap=None, eyes_tap=None, grin_tap=None):
    """The head, its neck at (x, y); an eye that blinks, a jaw that can open."""
    jaw = []
    if jaw_tap:
        jaw.append(tl("teeth", "rotation", [(0, 0), (0.25, -20, "back_out"), (1.8, -20), (2.2, 0, "quad_in")],
                      trigger=jaw_tap))
    if grin_tap:
        jaw.append(tl("grin", "rotation", [(0, 0), (0.2, -9, "quad_out"), (1.0, -9), (1.3, 0)], trigger=grin_tap))
    eye_grow = []
    if eyes_tap:
        eye_grow = [tl("grow", "scale", [(0, eye_scale), (0.4, eye_scale * 2.6, "back_out"), (2.0, eye_scale * 2.6),
                                          (2.5, eye_scale, "quad_in")], trigger=eyes_tap)]
    children = [
        # The inside of the mouth, under the jaw, seen when it opens.
        {"name": "mouth", "type": "shape", "fill": "#6A1D1A",
         "shape": {"path": "M -112 -29 L -44 -29 L -56 -13 L -104 -16 Z"}},
        vec("jaw", "wolf_jaw", -38, -38, anchor="top_right", timelines=jaw),
        vec("head", "wolf_head", 0, 0, anchor="bottom_right"),
        group("eye", -54, -58, [
            circle("white", 0, 0, 6.5, "#F2D27A", stroke={"color": INK, "width": 1.8}),
            # Towards the snout: the head is drawn facing left, so it looks ahead.
            circle("pupil", -1.8, 0, 3, INK),
        ], timelines=eye_grow + [blink("blink", 4.4, 1.3)], scale=eye_scale),
    ]
    if cap:
        children.append(vec("nightcap", "nightcap", -104, -110, scale=0.74))
    timelines = [swing("tilt", "rotation", -2, 3, 3.6, 0.5)] if tilt else []
    return group("wolf_head", x, y, children, timelines=timelines)


def wolf(x, y, scale=1.0, tap=None, grin=None):
    """Standing, facing left, its feet at (x, y). A tap wags its tail fast
    and tilts its head."""
    tail = [swing("wag", "rotation", -10, 12, 1.6)]
    head_tilt = []
    if tap:
        tail.append(tl("happy", "rotation", [(0, 0), (0.15, 20), (0.3, -12), (0.45, 20), (0.6, -12), (0.75, 20),
                                             (0.9, 0)], trigger=tap))
        head_tilt = [tl("look", "rotation", [(0, 0), (0.3, 10, "quad_out"), (1.4, 10), (1.8, 0, "quad_in")],
                        trigger=tap)]
    head = wolf_head(72, -96, grin_tap=grin)
    head["timelines"] = head["timelines"] + head_tilt
    hop = [tl("hop", "y", [(0, y), (0.2, y - 24, "quad_out"), (0.4, y, "quad_in"), (0.55, y - 10, "quad_out"),
                           (0.7, y, "quad_in")], trigger=tap)] if tap else []
    return group("wolf", x, y, [
        vec("tail", "wolf_tail", 212, -104, anchor="left", timelines=tail),
        vec("body", "wolf_body", 0, -150),
        head,
    ], timelines=hop, scale=scale)


# -- Pictures (in plate coordinates, 470x520) ---------------------------------

def smoke(x, y):
    puffs = []
    for i in range(3):
        puffs.append(circle(f"puff_{i}", x, y, 9, "#E8E1D2", stroke={"color": INK, "width": 1.5}, opacity=0,
                            timelines=[
                                {"name": "rise", "autoplay": True, "loop": True, "delay": i * 1.2, "tracks": [
                                    {"property": "y", "keys": [{"t": 0, "v": y}, {"t": 3.6, "v": y - 70}]},
                                    {"property": "x", "keys": [{"t": 0, "v": x}, {"t": 3.6, "v": x + 24, "ease": "quad_in"}]},
                                    {"property": "scale", "keys": [{"t": 0, "v": 0.6}, {"t": 3.6, "v": 1.6}]},
                                    {"property": "opacity", "keys": [{"t": 0, "v": 0}, {"t": 0.5, "v": 0.9},
                                                                     {"t": 3.6, "v": 0}]},
                                ]}]))
    return puffs


def clouds(ys=(40, 90)):
    return [vec(f"cloud_{i}", "cloud", 40 + 200 * i, y, scale=0.8 + 0.2 * i,
                timelines=[swing("drift", "x", 20 + 200 * i, 70 + 200 * i, 24 + 7 * i, ease="quad_in_out")])
            for i, y in enumerate(ys)]


def flowers(spots, tap=None):
    out = []
    for i, (x, y, color, s) in enumerate(spots):
        timelines = [swing("sway", "rotation", -6, 6, 2.2 + 0.37 * (i % 5), 0.3 * i)]
        if tap:
            timelines.append(tl("bob", "scale", [(0, s), (0.25, s * 1.35, "back_out"), (0.8, s, "quad_in")],
                                trigger=tap, delay=0.06 * i))
        out.append(vec(f"flower_{i}", f"flower_{color}", x, y, anchor="bottom", scale=s, timelines=timelines))
    return out


def butterfly(x, y, span=60, period=7.0, delay=0.0):
    return group("butterfly", x, y, [
        vec("wings", "butterfly", 0, 0, anchor="center", scale=1.4,
            timelines=[swing("flap", "scale_x", 1, 0.2, 0.32)]),
    ], timelines=[
        swing("wander_x", "x", x, x + span, period, delay),
        swing("wander_y", "y", y, y - 30, period * 0.63, delay),
    ])


def picture_cover():
    return [
        vec("backdrop", "bg_woods", 0, 0),
        *clouds(),
        vec("pine", "tree_pine", -10, 150, scale=1.05),
        vec("oak", "tree_round", 316, 170, scale=1.1),
        vec("bush", "bush", 20, 360),
        *flowers([(300, 470, "red", 1.0), (330, 480, "white", 0.9), (420, 460, "blue", 1.0)]),
        red(200, 470, scale=1.25),
        butterfly(80, 250),
    ]


def picture_1():
    return [
        vec("backdrop", "bg_cottage", 0, 0),
        *clouds((50, 20)),
        vec("cottage", "cottage", 180, 160),
        *smoke(373, 170),
        # On the roof's ridge.
        vec("bird", "bird", 312, 184, anchor="bottom",
            timelines=[tl("hop", "y", [(0, 184), (2.6, 184), (2.75, 172, "quad_out"), (2.9, 184, "quad_in"),
                                       (3.05, 176, "quad_out"), (3.2, 184, "quad_in"), (4.4, 184)],
                          autoplay=True, loop=True)]),
        vec("fence", "fence", 250, 400),
        *flowers([(210, 400, "red", 0.8), (236, 404, "white", 0.7), (440, 470, "blue", 0.9)]),
        red(110, 490, scale=1.35, tap="tap_hood"),
    ]


def picture_2():
    mother = vec("mother", "mother", 350, 490, anchor="bottom", scale_x=-1,
                 timelines=[swing("lean", "rotation", -1.5, 1.5, 3.8)])
    return [
        vec("backdrop", "bg_cottage", 0, 0),
        *clouds((30, 70)),
        vec("cottage", "cottage", 150, 130, scale=0.85),
        *smoke(323, 136),
        mother,
        red(140, 490, scale=1.25, basket=False),
        # Hanging from Mother's hand; it swings, and a tap makes it swing wide.
        vec("big_basket", "basket", 322, 364, anchor="top", scale=1.2,
            timelines=[swing("sway", "rotation", -6, 6, 2.2),
                       tl("swing", "rotation", [(0, 0), (0.3, 28, "quad_out"), (0.8, -24, "quad_in_out"),
                                                (1.3, 16, "quad_in_out"), (1.8, -8, "quad_in_out"), (2.2, 0)],
                          trigger="tap_basket")]),
    ]


def picture_3():
    return [
        vec("backdrop", "bg_woods", 0, 0),
        vec("pine_back", "tree_pine", 180, 110, scale=0.9),
        vec("oak", "tree_round", 330, 120, scale=1.05),
        red(96, 480, scale=1.15, bob_delay=0.7),
        wolf(250, 430, scale=0.95, tap="tap_wolf"),
        vec("pine", "tree_pine", 390, 240, scale=1.0),
        vec("bush", "bush", -20, 440, scale=0.9),
    ]


def picture_4():
    spots = [(30, 500, "red", 1.1), (70, 470, "white", 0.9), (110, 505, "blue", 1.0), (150, 460, "red", 0.8),
             (250, 500, "white", 1.1), (290, 470, "red", 0.9), (330, 505, "blue", 1.0), (370, 460, "white", 0.8),
             (410, 495, "red", 1.1), (450, 470, "blue", 0.9), (200, 440, "blue", 0.7), (340, 420, "red", 0.6)]
    # The wolf runs off over the hill, once, then is gone: it rests where the
    # run ends, far enough right that none of it shows (mirrored, it reaches
    # 75 pixels to the left of its x).
    small = wolf(0, 0, scale=0.3)
    small["scale_x"] = -1
    runner = group("runner", 600, 290, [small], timelines=[{"name": "run", "autoplay": True, "delay": 0.8, "tracks": [
        {"property": "x", "keys": [{"t": 0, "v": 170}, {"t": 3.8, "v": 600}]},
        {"property": "y", "keys": [{"t": 0, "v": 318}, {"t": 0.25, "v": 306, "ease": "quad_out"},
                                   {"t": 0.5, "v": 318, "ease": "quad_in"}, {"t": 0.75, "v": 306, "ease": "quad_out"},
                                   {"t": 1.0, "v": 318, "ease": "quad_in"}, {"t": 1.25, "v": 304, "ease": "quad_out"},
                                   {"t": 1.5, "v": 314, "ease": "quad_in"}, {"t": 1.75, "v": 300, "ease": "quad_out"},
                                   {"t": 2.0, "v": 308, "ease": "quad_in"}, {"t": 2.5, "v": 296}, {"t": 3.8, "v": 290}]},
    ]}])
    return [
        vec("backdrop", "bg_meadow", 0, 0),
        *clouds((40, 100)),
        runner,
        vec("oak", "tree_round", 330, 140, scale=0.8),
        red(180, 470, scale=1.2, bob_delay=0.3),
        *flowers(spots, tap="tap_flowers"),
        butterfly(60, 300, span=90, period=8.0),
        butterfly(300, 240, span=-70, period=6.5, delay=1.1),
    ]


def grandma_peeking(x, y, tap=None):
    """Two eyes behind her spectacles in the cupboard's gap."""
    pop = [tl("peek", "y", [(0, y), (0.2, y - 8, "quad_out"), (1.2, y - 8), (1.5, y, "quad_in")], trigger=tap)] if tap else []
    return group("peeking", x, y, [
        group("eyes", 0, 0, [
            circle("left", -6, 0, 3.5, "#F4ECDA", stroke={"color": INK, "width": 1.2}),
            circle("right", 6, 0, 3.5, "#F4ECDA", stroke={"color": INK, "width": 1.2}),
            circle("left_pupil", -5, 0.5, 1.6, INK), circle("right_pupil", 7, 0.5, 1.6, INK),
        ], timelines=[blink("blink", 3.1, 0.6)]),
    ], timelines=pop)


def bedroom(scale=1.0, x=0.0, y=0.0, cupboard=True, eyes_tap=None, jaw_tap=None, eye_scale=1.0):
    """The bed with the wolf in it; the cupboard beside it."""
    s = scale
    parts = []
    if cupboard:
        rattle = [tl("rattle", "rotation", [(0, 0), (0.08, -2), (0.16, 2), (0.24, -2), (0.32, 2), (0.4, 0)],
                     trigger="tap_cupboard")]
        parts += [
            vec("cupboard", "cupboard", 30, 180, timelines=rattle),
            grandma_peeking(91, 300, tap="tap_cupboard"),
        ]
    bed_x, bed_y = x + 140 * s, y + 240 * s
    parts += [
        vec("bed", "bed", bed_x, bed_y, scale=s),
        # A hump under the quilt where the wolf lies, breathing.
        {"name": "hump", "type": "shape", "x": r(bed_x + 170 * s), "y": r(bed_y + 106 * s), "scale": s,
         "shape": {"path": "M -90 4 C -60 -30 40 -34 90 4 Z"}, "fill": RED, "stroke": {"color": INK, "width": 2.5},
         "timelines": [swing("breathe", "scale_y", 1, 1.12, 3.0)]},
        # Facing the room, his neck on the pillow.
        group("wolf_in_bed", bed_x + 40 * s, bed_y + 104 * s, [
            wolf_head(0, 0, cap=True, eyes_tap=eyes_tap, jaw_tap=jaw_tap, eye_scale=eye_scale),
        ], scale=0.72 * s, scale_x=-1),
    ]
    return parts


def room(outside=()):
    """The room, with whatever passes outside seen through the glass,
    under the window's frame and curtains."""
    layers = [vec("backdrop", "bg_room", 0, 0)]
    if outside:
        layers.append(group("outside", 0, 0, list(outside), clip={"rect": [290, 70, 120, 130]}))
    return layers + [vec("window", "window_front", 0, 0)]


def picture_5():
    return [*room(), *bedroom()]


def picture_close(tap_eyes=None, tap_teeth=None):
    """The bed close up, Red at its foot looking at 'Grandma'."""
    return [
        *room(),
        *bedroom(scale=1.5, x=-240, y=-150, cupboard=False, eyes_tap=tap_eyes, jaw_tap=tap_teeth),
        red(410, 540, scale=1.3, facing=-1),
    ]


def picture_8():
    candles = []
    for i, cx in enumerate((168, 188, 208)):
        candles += [
            {"name": f"candle_{i}", "type": "shape", "x": cx - 3, "y": 334, "shape": {"rect": [0, 0, 6, 20]},
             "fill": "#F4ECDA", "stroke": {"color": INK, "width": 1.5}},
            {"name": f"flame_{i}", "type": "shape", "x": cx, "y": 332, "anchor": "bottom",
             "shape": {"path": "M 0 -14 Q 6 -4 0 0 Q -6 -4 0 -14 Z"}, "fill": "#F2B640",
             "timelines": [swing("flicker", "scale_y", 0.85, 1.15, 0.5 + 0.13 * i),
                           tl("flare", "scale", [(0, 1), (0.2, 2.0, "back_out"), (1.2, 2.0), (1.6, 1)],
                              trigger="tap_cake", delay=0.1 * i)]},
        ]
    # The wolf running off outside, seen through the window, once.
    bounce = [(i * 0.2, 196 - (10 if i % 2 else 0), "quad_out" if i % 2 else "quad_in") for i in range(13)]
    # The same wolf as everywhere, mirrored whole, so it runs to the right.
    small = wolf(0, 0, scale=0.3)
    small["scale_x"] = -1
    runner = group("runner", 260, 196, [small], timelines=[{"name": "flee", "autoplay": True, "delay": 1.0, "tracks": [
        {"property": "x", "keys": [{"t": 0, "v": 250}, {"t": 2.4, "v": 520}]},
        {"property": "y", "keys": [{"t": t, "v": v, "ease": ease} for t, v, ease in bounce]},
    ]}])
    return [
        *room([runner]),
        {"name": "table", "type": "shape", "x": 110, "y": 380,
         "shape": {"path": "M 0 0 L 170 0 L 170 12 L 0 12 Z M 16 12 L 28 12 L 28 110 L 16 110 Z "
                            "M 142 12 L 154 12 L 154 110 L 142 110 Z"},
         "fill": "#8A6440", "stroke": {"color": INK, "width": 2.5}},
        vec("cake", "cake", 128, 312),
        *candles,
        vec("grandma", "grandma", 70, 500, anchor="bottom",
            timelines=[swing("nod", "rotation", -2, 2, 2.8)]),
        group("woodcutter", 410, 500, [
            # Across his back, its blade over his far shoulder.
            vec("axe", "axe", 10, -70, anchor="bottom",
                timelines=[swing("rest", "rotation", 24, 27, 3.4)]),
            vec("man", "woodcutter", 0, 0, anchor="bottom"),
        ], scale=0.95),
        red(320, 500, scale=1.0, facing=-1, bob_delay=0.5, basket=False),
    ]


# -- The book ------------------------------------------------------------------

def text(name, x, y, font, value, **extra):
    return {"name": name, "type": "text", "x": r(x), "y": r(y), "font": font, "text": value, **extra}


def lay_out(lines, drop_cap=True):
    """The story's lines as text layers, a word in {braces} printed red.
    Returns (layers, tap) where tap is the red word's trigger."""
    layers = []
    first = lines[0]
    indent = 0.0
    if drop_cap and first[0].isalpha():
        letter, lines = first[0], [first[1:]] + lines[1:]
        cap_w = CAP.width(letter, CAP_SIZE)
        layers.append(text("initial", TEXT_X - 4, TEXT_Y - 30, "initial", letter))
        indent = cap_w + 6
    for i, line in enumerate(lines):
        x = TEXT_X + (indent if i < 2 else 0)
        y = TEXT_Y + i * LINE
        # Split into plain and {marked} runs.
        runs, word = [], False
        for part in line.replace("}", "{").split("{"):
            if part:
                runs.append((part, word))
            word = not word
        for j, (run, marked) in enumerate(runs):
            w = BODY.width(run, BODY_SIZE)
            if marked:
                h = BODY.height(BODY_SIZE)
                layers.append(text(f"word_{i}_{j}", x + w / 2, y + h / 2, "word", run, anchor="center"))
            else:
                layers.append(text(f"line_{i}_{j}", x, y, "body", run))
            x += w
    return layers


def pulse(layers, trigger):
    """The red word jumps a little when its trigger fires, and a press on
    it fires that trigger."""
    for layer in layers:
        if layer["font"] == "word":
            layer["press"] = {"trigger": trigger}
            layer["timelines"] = [tl("pulse", "scale", [(0, 1), (0.18, 1.3, "quad_out"), (0.6, 1, "back_out")],
                                     trigger=trigger)]
    return layers


def plate_frame():
    x, y, w, h = PLATE
    rule = f"M {x - 10} {y - 10} H {x + w + 10} V {y + h + 10} H {x - 10} Z"
    inner = f"M {x - 4} {y - 4} H {x + w + 4} V {y + h + 4} H {x - 4} Z"
    corners = []
    for i, (cx, cy) in enumerate([(x - 10, y - 10), (x + w + 10, y - 10), (x - 10, y + h + 10), (x + w + 10, y + h + 10)]):
        corners.append({"name": f"corner_{i}", "type": "shape", "x": cx, "y": cy,
                        "shape": {"path": "M 0 -8 L 8 0 L 0 8 L -8 0 Z"}, "fill": RED,
                        "stroke": {"color": INK, "width": 1.5}})
    return [
        {"name": "rule_outer", "type": "shape", "shape": {"path": rule}, "fill": "#00000000",
         "stroke": {"color": INK, "width": 2}},
        {"name": "rule_inner", "type": "shape", "shape": {"path": inner}, "fill": "#00000000",
         "stroke": {"color": INK, "width": 1}},
        *corners,
    ]


def leaf():
    """The page that turns: blank paper lifting off the right page and
    settling on the left, where it fades into the new text."""
    x0, y0, x1, y1 = BOOK
    return group("leaf", SPINE, y0, [
        {"name": "sheet", "type": "shape", "shape": {"rect": [0, 0, x1 - SPINE, y1 - y0]}, "fill": PAPER},
        {"name": "shade", "type": "shape", "shape": {"rect": [0, 0, x1 - SPINE, y1 - y0]}, "fill": INK, "opacity": 0,
         "timelines": [tl("shade", "opacity", [(0, 0), (0.35, 0.14, "quad_out"), (0.7, 0.03, "quad_in")],
                          autoplay=True)]},
    ], opacity=0, timelines=[{"name": "turn", "autoplay": True, "tracks": [
        {"property": "scale_x", "keys": [{"t": 0, "v": 1}, {"t": 0.75, "v": -1, "ease": "quad_in_out"}]},
        {"property": "opacity", "keys": [{"t": 0, "v": 1}, {"t": 0.72, "v": 1}, {"t": 1.0, "v": 0, "ease": "quad_out"}]},
    ]}])


def page_numbers(n):
    if n == 0:
        return []
    return [
        text("folio_left", 70, 632, "folio", f"{2 * n}", size=[570, 24], align="center"),
        text("folio_right", SPINE, 632, "folio", f"{2 * n + 1}", size=[570, 24], align="center"),
        text("running_title", 70, 72, "running", "Little Red Riding Hood", size=[570, 24], align="center"),
    ]


def spread(name, trigger, story, picture, tap=None, n=0, extra_left=()):
    x, y, w, h = PLATE
    left = pulse(lay_out(story), tap) if story else []
    # The left page shows up once the turning leaf has landed on it.
    left_page = group("left_page", 0, 0, [*page_numbers(n), *left, *extra_left], opacity=0,
                      timelines=[tl("appear", "opacity", [(0, 0), (0.7, 0), (0.95, 1)], autoplay=True, hold=True)])
    return {
        "name": name, "trigger": trigger,
        "layers": [
            left_page,
            group("picture", x, y, picture, clip={"rect": [0, 0, w, h]}),
            *plate_frame(),
            leaf(),
            # Over the turning leaf too, so it is the same paper.
            {"name": "paper", "type": "image", "image": "paper", "x": BOOK[0], "y": BOOK[1],
             "size": [BOOK[2] - BOOK[0], BOOK[3] - BOOK[1]], "blend": "multiply"},
            {"name": "rustle", "type": "audio", "sound": ["turn1", "turn2"], "autoplay": True, "gain": 0.3},
        ],
    }


STORY = [
    ("page_1", "tap_hood", ["Once upon a time there", "was a little girl.", "She wore a {red hood},",
                            "so everyone called her", "Little Red Riding Hood."], picture_1),
    ("page_2", "tap_basket", ["One day her mother said:", "“Take this {basket}", "to Grandma.",
                              "And stay on the path!”"], picture_2),
    ("page_3", "tap_wolf", ["In the woods, Red met", "a big grey {wolf}.", "“Where are you going?”",
                            "asked the wolf."], picture_3),
    ("page_4", "tap_flowers", ["“To Grandma’s house!”", "The wolf ran off.", "Red picked {flowers}",
                               "and forgot the path."], picture_4),
    ("page_5", "tap_cupboard", ["The wolf got there first.", "Grandma hid in the", "{cupboard}, and the wolf",
                                "jumped into her bed."], picture_5),
    ("page_6", "tap_eyes", ["“Grandma, what big {eyes}", "you have!”", "“All the better", "to see you with!”"],
     lambda: picture_close(tap_eyes="tap_eyes")),
    ("page_7", "tap_teeth", ["“Grandma, what big {teeth}", "you have!”", "“All the better", "to EAT you with!”"],
     lambda: picture_close(tap_teeth="tap_teeth")),
    ("page_8", "tap_cake", ["Red shouted for help.", "A woodcutter came and", "chased the wolf away.",
                            "Grandma came out, and", "they all had {cake}."], picture_8),
]


def cover():
    left = [
        text("title_1", 70, 170, "title", "Little Red", size=[570, 90], align="center"),
        text("title_2", 70, 262, "title", "Riding Hood", size=[570, 90], align="center"),
        {"name": "flourish", "type": "shape", "x": 355, "y": 382,
         "shape": {"path": "M -120 0 C -80 -18 -40 18 0 0 C 40 -18 80 18 120 0 M -8 0 L 0 -8 L 8 0 L 0 8 Z"},
         "fill": RED, "stroke": {"color": INK, "width": 1.5}},
        text("subtitle", 70, 420, "subtitle", "A fairy tale for young readers", size=[570, 40], align="center"),
    ]
    return spread("cover", "cover", None, picture_cover(), extra_left=left)


def the_end():
    return [
        text("the_end", 70, 470, "subtitle", "The End", size=[570, 40], align="center"),
        {"name": "end_flourish", "type": "shape", "x": 355, "y": 524,
         "shape": {"path": "M -60 0 C -40 -10 -20 10 0 0 C 20 -10 40 10 60 0 M -5 0 L 0 -5 L 5 0 L 0 5 Z"},
         "fill": RED, "stroke": {"color": INK, "width": 1.2}},
    ]


def show():
    x0, y0, x1, y1 = BOOK
    scenes = [cover()]
    for n, (name, tap, story, picture) in enumerate(STORY, 1):
        extra = the_end() if n == len(STORY) else ()
        scenes.append(spread(name, name, story, picture(), tap=tap, n=n, extra_left=extra))
    book = [
        {"name": "table", "type": "image", "image": "table", "size": [W, H]},
        {"name": "shadow", "type": "shape", "x": x0 + 8, "y": y0 + 12,
         "shape": {"rect": [0, 0, x1 - x0, y1 - y0]}, "fill": "#00000070"},
        {"name": "cover_board", "type": "shape", "x": x0 - 14, "y": y0 - 10,
         "shape": {"rect": [0, 0, x1 - x0 + 28, y1 - y0 + 22]}, "fill": "#5E2A22",
         "stroke": {"color": "#3A1A15", "width": 2}},
        # The edges of the pages under the open ones.
        *[{"name": f"edge_{i}", "type": "shape", "x": x0 - 2 - 2 * i, "y": y0 + 2 + i,
           "shape": {"rect": [0, 0, x1 - x0 + 4 + 4 * i, y1 - y0]}, "fill": "#E2D2B0",
           "stroke": {"color": "#B9A67F", "width": 1}} for i in (3, 2, 1)],
        {"name": "pages", "type": "shape", "x": x0, "y": y0, "shape": {"rect": [0, 0, x1 - x0, y1 - y0]},
         "fill": PAPER},
    ]
    return {
        "$schema": "https://raw.githubusercontent.com/francisdb/cuelight/main/crates/cuelight/schemas/show.schema.json",
        "format": 1,
        "name": "red_riding_hood",
        "size": [W, H],
        "background": "#2A1C14",
        "fonts": {
            "body": {"file": "IMFellEnglish-Regular", "size": BODY_SIZE, "color": INK},
            "word": {"file": "IMFellEnglish-Regular", "size": BODY_SIZE, "color": RED},
            "initial": {"file": "IMFellFrenchCanon-Regular", "size": CAP_SIZE, "color": RED},
            "title": {"file": "IMFellFrenchCanon-Regular", "size": 76, "color": INK},
            "subtitle": {"file": "IMFellEnglish-Italic", "size": 26, "color": MUTED},
            "running": {"file": "IMFellEnglish-Italic", "size": 18, "color": MUTED},
            "folio": {"file": "IMFellEnglish-Regular", "size": 18, "color": MUTED},
        },
        "layers": book,
        "scenes": scenes,
    }


def driver():
    steps = [{"trigger": "cover"}, {"wait": 5.0}]
    for name, tap, _story, _picture in STORY:
        steps += [{"trigger": name}, {"wait": 4.0}, {"trigger": tap}, {"wait": 5.0}]
    steps += [{"wait": 3.0}]
    return {"loop": True, "steps": steps}


def compact(value, indent=0, width=150):
    """JSON with small objects and arrays on one line, like the hand-written shows."""
    flat = json.dumps(value, separators=(", ", ": "), ensure_ascii=False)
    if len(flat) + indent <= width or not isinstance(value, (dict, list)):
        return flat
    pad = " " * (indent + 2)
    if isinstance(value, dict):
        items = [f"{pad}{json.dumps(k)}: {compact(v, indent + 2, width)}" for k, v in value.items()]
        return "{\n" + ",\n".join(items) + "\n" + " " * indent + "}"
    items = [pad + compact(v, indent + 2, width) for v in value]
    return "[\n" + ",\n".join(items) + "\n" + " " * indent + "]"


if __name__ == "__main__":
    out = Path(sys.argv[1])
    (out / "show.json").write_text(compact(show()) + "\n")
    (out / "test-driver.json").write_text(json.dumps(driver(), indent=2) + "\n")
