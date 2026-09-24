#!/usr/bin/env python3
"""Write the artwork of red_riding_hood: the pictures, the book and the paper.

    tools/red_riding_hood_art.py red_riding_hood/assets

The pictures are flat shapes in a few inks with a dark outline, the way
an old picture book was printed from a handful of plates. Every part
that moves is a file of its own, drawn so that the point it turns around
sits on an edge or corner of its box, where a layer's `anchor` can reach
it: a head turns at its neck (bottom), a basket swings from its handle
(top), a jaw opens at its hinge (top right), a tail wags from its root
(left), a flower sways from its stem (bottom).

The backdrops are 470x520, the size of the picture plate on the right
page. The book is PNG: the table under it, and the paper's texture,
which is multiplied over both pages (a warm grain, darker edges, a few
foxing spots and the shadow of the spine).

Needs numpy and Pillow.
"""

import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

INK = "#2B211C"
PAPER = "#EFE3C6"
RED = "#A8322A"
RED_DARK = "#7C2420"
SKIN = "#F2D2B0"
BLUSH = "#E4A08C"
HAIR = "#6B4428"
WOLF = "#7D7166"
WOLF_DARK = "#5B5249"
WOLF_LIGHT = "#C3B6A2"
GREEN = "#55704A"
GREEN_LIGHT = "#86995F"
GREEN_DARK = "#384D33"
GREEN_FAR = "#A9B48E"
TRUNK = "#6E4C31"
OCHRE = "#C99A45"
OCHRE_DARK = "#9C7433"
BLUE = "#5E7A93"
BLUE_LIGHT = "#A9BBC4"
WHITE = "#F8F0DE"
PLUM = "#7A5C74"
SKY = "#D8D8C0"
WALL = "#E3C99A"
FLOOR = "#9C7650"

W, H = 470, 520  # the picture plate


def svg(body, width, height):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
            f'width="{width}" height="{height}">\n{body}\n</svg>\n')


def p(d, fill, stroke=INK, width=2.5):
    s = f' stroke="{stroke}" stroke-width="{width}"' if stroke else ""
    return f'<path d="{d}" fill="{fill}"{s}/>'


def c(cx, cy, r, fill, stroke=INK, width=2.5):
    s = f' stroke="{stroke}" stroke-width="{width}"' if stroke else ""
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"{s}/>'


def e(cx, cy, rx, ry, fill, stroke=INK, width=2.5):
    s = f' stroke="{stroke}" stroke-width="{width}"' if stroke else ""
    return f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{fill}"{s}/>'


def line(d, color=INK, width=2.5):
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"/>'


# -- Red ---------------------------------------------------------------------

def red_body():
    """Cape, dress and legs, the neck at the top centre (60, 0). Her hand is
    left to the show, which only draws it where it holds the basket."""
    return svg("".join([
        line("M 50 126 L 48 146", INK, 5), line("M 70 126 L 72 146", INK, 5),
        e(46, 148, 8, 4, INK, None), e(75, 148, 8, 4, INK, None),
        p("M 34 100 L 86 100 L 92 128 L 28 128 Z", BLUE),
        p("M 44 4 Q 60 -2 76 4 L 98 112 Q 60 124 22 112 Z", RED),
        line("M 60 8 L 60 108", RED_DARK, 2),
    ]), 120, 152)


def red_head():
    """Head in its hood, turned a little to the right; the neck at the
    bottom centre (40, 80). A round picture-book face: no nose, round eyes
    with a highlight, cheeks under the eyes, a small smile."""
    blush = "#EDB0A0"
    return svg("".join([
        p("M 40 3 C 15 3 3 22 3 44 C 3 64 17 79 40 79 C 63 79 77 64 77 44 C 77 22 65 3 40 3 Z", RED),
        e(43, 46, 25, 27, RED_DARK, None),
        # Hair around the face, falling in two locks beside it.
        p("M 22 44 C 20 58 22 68 28 74 L 32 60 Z M 64 44 C 66 58 64 68 58 74 L 54 60 Z", HAIR, INK, 1.2),
        e(43, 45, 21, 21, HAIR, None),
        e(43, 49, 17, 18, SKIN, INK, 2),
        p("M 25.5 46 C 26 31 36 27 45 27 C 55 27 62 34 60.5 46 C 55 39 49 37.5 42 38.5 C 36 39 30 41 25.5 46 Z",
          HAIR, INK, 1.2),
        c(37.5, 50, 2.5, INK, None), c(49, 50, 2.5, INK, None),
        c(38.4, 49.1, 0.9, WHITE, None), c(49.9, 49.1, 0.9, WHITE, None),
        e(34.5, 56, 3.2, 2, blush, None), e(52.5, 56, 3.2, 2, blush, None),
        line("M 40 58 Q 43.5 61 47 58", "#9C3A40", 1.5),
        # The bow of her hood, under her chin.
        p("M 43 72 L 34 67 L 35 77 Z M 43 72 L 52 67 L 51 77 Z", RED, INK, 1.5),
        c(43, 72, 2.4, RED_DARK, INK, 1.2),
    ]), 80, 80)


def basket():
    """A basket hanging from its handle, the top centre (30, 0)."""
    return svg("".join([
        line("M 10 26 C 10 -4 50 -4 50 26", TRUNK, 4),
        p("M 4 24 L 56 24 L 50 54 L 10 54 Z", OCHRE),
        line("M 7 34 L 53 34 M 9 44 L 51 44", OCHRE_DARK, 2),
        line("M 18 24 L 20 54 M 30 24 L 30 54 M 42 24 L 40 54", OCHRE_DARK, 1.5),
        p("M 8 24 Q 30 12 52 24 Q 30 30 8 24 Z", RED, INK, 2),
        c(22, 21, 2, WHITE, None), c(34, 19, 2, WHITE, None), c(44, 22, 2, WHITE, None),
    ]), 60, 58)


# -- Mother, Grandma, the woodcutter -------------------------------------------

def mother():
    return svg("".join([
        p("M 30 90 L 80 90 L 100 250 L 10 250 Z", BLUE),
        p("M 40 100 L 70 100 L 78 236 L 32 236 Z", WHITE),
        p("M 34 88 Q 55 76 76 88 L 80 110 L 30 110 Z", BLUE),
        c(55, 56, 24, SKIN),
        p("M 30 50 C 30 22 80 22 80 50 Q 70 36 55 38 Q 40 36 30 50 Z", HAIR),
        c(55, 26, 11, HAIR),
        c(47, 56, 2.4, INK, None), c(63, 56, 2.4, INK, None),
        line("M 49 67 Q 55 71 61 67", INK, 1.8),
        c(84, 132, 7, SKIN),
        p("M 72 92 Q 92 104 86 128", BLUE, INK, 2.5),
    ]), 110, 252)


def grandma():
    return svg("".join([
        p("M 24 80 L 76 80 L 92 186 L 8 186 Z", PLUM),
        p("M 20 76 Q 50 60 80 76 L 88 120 Q 50 104 12 120 Z", BLUE_LIGHT),
        c(50, 46, 24, SKIN),
        p("M 26 42 C 26 16 74 16 74 42 Q 64 30 50 32 Q 36 30 26 42 Z", WHITE),
        c(50, 18, 10, WHITE),
        c(42, 48, 6, "none", INK, 1.8), c(58, 48, 6, "none", INK, 1.8), line("M 48 48 L 52 48", INK, 1.8),
        c(42, 48, 2, INK, None), c(58, 48, 2, INK, None),
        line("M 44 60 Q 50 65 56 60", INK, 1.8),
        c(40, 56, 4, BLUSH, None), c(60, 56, 4, BLUSH, None),
    ]), 100, 188)


def woodcutter():
    return svg("".join([
        p("M 40 150 L 36 236 L 58 236 L 62 160 Z M 70 160 L 74 236 L 96 236 L 92 150 Z", TRUNK),
        e(46, 238, 14, 6, INK, None), e(88, 238, 14, 6, INK, None),
        p("M 28 78 Q 66 64 104 78 L 108 160 L 24 160 Z", GREEN),
        p("M 24 142 L 108 142 L 108 152 L 24 152 Z", TRUNK),
        c(66, 48, 24, SKIN),
        p("M 44 52 Q 66 96 88 52 Q 80 70 66 68 Q 52 70 44 52 Z", HAIR),
        p("M 38 34 Q 66 0 94 34 L 98 38 L 34 38 Z", RED_DARK),
        c(58, 46, 2.5, INK, None), c(74, 46, 2.5, INK, None),
        c(34, 108, 8, SKIN),
    ]), 132, 246)


def axe():
    """The axe, held at the bottom of its handle (bottom centre)."""
    return svg("".join([
        p("M 18 20 L 24 20 L 24 120 L 18 120 Z", TRUNK, INK, 2),
        p("M 24 14 Q 50 6 52 30 Q 50 50 24 44 Z", BLUE_LIGHT),
    ]), 56, 122)


# -- The wolf ----------------------------------------------------------------

def wolf_body():
    """Standing, facing left; the head sits at the top left, the tail's root
    at (214, 44)."""
    return svg("".join([
        p("M 58 100 L 52 146 L 64 146 L 74 104 Z M 92 104 L 90 146 L 102 146 L 106 104 Z", WOLF_DARK),
        p("M 168 100 L 164 146 L 176 146 L 184 100 Z M 196 96 L 200 146 L 212 146 L 210 92 Z", WOLF_DARK),
        p("M 40 60 C 40 30 70 24 110 32 C 150 38 200 26 218 50 C 232 72 214 108 190 108 "
          "C 150 112 110 108 80 110 C 54 112 40 90 40 60 Z", WOLF),
        p("M 60 92 C 90 104 150 104 190 100 C 170 110 110 112 80 110 C 64 110 58 100 60 92 Z", WOLF_LIGHT, None),
        line("M 110 40 Q 130 46 150 40 M 120 52 Q 140 58 160 50", WOLF_DARK, 2),
    ]), 240, 150)


def wolf_tail():
    """A bushy tail, its root at the middle of the left edge."""
    return svg(p("M 2 30 C 18 24 36 14 56 8 C 70 2 86 4 90 12 C 94 22 84 30 72 30 "
                 "C 62 40 42 50 22 46 C 12 44 6 38 2 30 Z", WOLF) +
               p("M 74 8 C 84 6 90 10 90 14 C 90 22 84 26 76 26 Q 82 16 74 8 Z", WOLF_LIGHT, None) +
               line("M 30 32 Q 50 26 64 18 M 34 40 Q 52 36 66 26", WOLF_DARK, 1.5), 96, 52)


def wolf_head():
    """Facing left; the neck at the bottom right. Its eye is left to the
    show, so it can blink and grow, and so is the inside of its mouth,
    which has to lie under the jaw."""
    return svg("".join([
        p("M 96 4 L 118 38 L 90 34 Z", WOLF_DARK),
        # The head closes under the jaw's hinge; the mouth is only at the front.
        p("M 8 56 Q 30 44 60 40 C 70 18 110 18 122 44 C 132 70 118 96 100 98 C 88 90 78 76 66 71 L 12 70 Q 2 64 8 56 Z", WOLF),
        p("M 12 68 L 64 70 L 64 73 L 14 72 Z", RED_DARK, INK, 1.2),
        p("M 18 71 L 21 78 L 24 71 Z M 34 71.5 L 38 80 L 42 71.5 Z M 50 72 L 53 78 L 56 72 Z", WHITE, INK, 1.5),
        p("M 72 26 L 86 6 L 96 30 Z", WOLF_LIGHT, INK, 2),
        c(9, 58, 6, INK, None),
        p("M 30 52 Q 44 46 58 50", "none", WOLF_DARK, 2),
    ]), 132, 100)


def wolf_jaw():
    """The lower jaw, hinged far back under the cheek (near the top right),
    where the head covers it; shorter than the snout, its fangs stand up."""
    return svg("".join([
        p("M 38 11 L 42 3 L 46 11 Z M 54 11 L 58 1 L 62 11 Z M 70 11 L 73 4 L 76 11 Z", WHITE, INK, 1.5),
        p("M 102 10 L 34 11 Q 24 15 30 23 Q 58 35 102 28 Z", WOLF),
    ]), 104, 36)


def nightcap():
    """Grandma's nightcap, pulled over the wolf's ears; its brim at the bottom."""
    return svg("".join([
        p("M 6 64 C 10 20 50 0 100 18 C 120 26 132 40 140 56 C 110 48 90 44 70 50 Q 30 56 6 64 Z", WHITE),
        c(142, 58, 9, RED),
        p("M 2 60 Q 60 44 112 56 L 112 68 Q 60 58 4 72 Z", RED),
    ]), 152, 76)


# -- Scenery -----------------------------------------------------------------

def tree_pine():
    return svg("".join([
        p("M 54 220 L 66 220 L 66 256 L 54 256 Z", TRUNK),
        p("M 60 4 L 104 90 L 16 90 Z", GREEN),
        p("M 60 50 L 112 150 L 8 150 Z", GREEN),
        p("M 60 110 L 118 222 L 2 222 Z", GREEN_DARK),
    ]), 120, 258)


def tree_round():
    return svg("".join([
        p("M 70 150 L 90 150 L 94 236 L 66 236 Z", TRUNK),
        line("M 80 170 L 104 146 M 80 190 L 58 164", TRUNK, 5),
        c(80, 70, 56, GREEN), c(40, 110, 36, GREEN), c(120, 110, 38, GREEN_DARK), c(80, 126, 40, GREEN),
        c(64, 56, 14, GREEN_LIGHT, None), c(100, 90, 10, GREEN_LIGHT, None),
    ]), 160, 238)


def bush():
    return svg(c(30, 40, 26, GREEN_DARK) + c(64, 32, 30, GREEN) + c(96, 42, 24, GREEN_DARK) +
               p("M 4 50 L 120 50 L 120 66 L 4 66 Z", GREEN_DARK, None), 124, 66)


def flower(color):
    """A flower on its stem, swaying from the bottom centre."""
    petals = "".join(c(20 + 8 * math.cos(a), 16 + 8 * math.sin(a), 6.5, color, INK, 1.5)
                     for a in [i * 2 * math.pi / 5 - math.pi / 2 for i in range(5)])
    return svg(line("M 20 20 Q 16 44 20 70", GREEN_DARK, 3) +
               p("M 20 50 Q 30 40 38 46 Q 30 54 20 50 Z", GREEN_LIGHT, INK, 1.5) +
               petals + c(20, 16, 4.5, OCHRE, INK, 1.5), 40, 72)


def butterfly():
    return svg(p("M 20 16 C 6 0 0 10 4 18 C 0 28 10 34 20 22 Z", OCHRE, INK, 1.5) +
               p("M 20 16 C 34 0 40 10 36 18 C 40 28 30 34 20 22 Z", OCHRE, INK, 1.5) +
               line("M 20 10 L 20 28", INK, 2.5), 40, 36)


def bird():
    return svg(p("M 4 22 Q 14 6 30 12 L 40 8 L 34 18 Q 30 30 14 28 Z", BLUE) +
               p("M 14 18 Q 22 10 28 18 Z", BLUE_LIGHT, INK, 1.5) + c(31, 14, 1.5, INK, None) +
               line("M 16 28 L 14 34 M 22 28 L 22 34", INK, 1.5), 44, 36)


def cloud():
    return svg(p("M 14 40 C 0 40 0 22 16 22 C 18 6 44 4 50 18 C 60 4 86 10 84 26 C 100 26 100 40 86 40 Z", WHITE, INK, 2),
               100, 44)


def cottage():
    """A cottage whose open door is on the left, where Mother stands."""
    return svg("".join([
        p("M 180 12 L 206 12 L 206 70 L 180 70 Z", RED_DARK),
        p("M 20 100 L 240 100 L 240 226 L 20 226 Z", WHITE),
        line("M 20 140 L 240 140 M 20 186 L 240 186 M 130 100 L 130 226 M 20 100 L 60 140 M 240 100 L 200 140",
             TRUNK, 4),
        p("M 0 106 L 130 20 L 260 106 Z", OCHRE),
        line("M 30 96 L 130 32 L 230 96", OCHRE_DARK, 2), line("M 60 90 L 130 46 L 200 90", OCHRE_DARK, 2),
        p("M 44 150 L 98 150 L 98 226 L 44 226 Z", INK),
        p("M 160 150 L 214 150 L 214 196 L 160 196 Z", "#F2C766"),
        line("M 187 150 L 187 196 M 160 173 L 214 173", TRUNK, 3),
    ]), 260, 228)


def fence():
    posts = "".join(p(f"M {x} 14 L {x + 8} 4 L {x + 16} 14 L {x + 16} 60 L {x} 60 Z", WHITE, INK, 2)
                    for x in range(4, 220, 30))
    return svg(p("M 0 24 L 230 24 L 230 32 L 0 32 Z M 0 44 L 230 44 L 230 52 L 0 52 Z", WHITE, INK, 2) + posts,
               232, 62)


def bed():
    """A bed seen from the side, its pillow on the left."""
    return svg("".join([
        p("M 6 20 L 34 20 L 34 196 L 6 196 Z", TRUNK),
        c(20, 22, 14, TRUNK),
        p("M 290 86 L 312 86 L 312 196 L 290 196 Z", TRUNK),
        p("M 30 104 L 296 104 L 296 150 L 30 150 Z", WHITE),
        e(74, 98, 44, 16, WHITE),
        p("M 70 108 C 120 70 250 80 294 104 L 300 172 L 70 172 Z", RED),
        "".join(p(f"M {x} {y} l 24 0 l 0 22 l -24 0 Z", color, INK, 1.5)
                for x, y, color in [(110, 110, OCHRE), (170, 104, BLUE), (230, 108, OCHRE),
                                    (140, 140, BLUE), (200, 138, OCHRE), (258, 140, BLUE)]),
    ]), 316, 198)


def cupboard():
    """A cupboard with its doors ajar: the gap is where Grandma looks out."""
    return svg("".join([
        p("M 4 10 L 116 10 L 116 226 L 4 226 Z", TRUNK),
        p("M 0 2 L 120 2 L 120 14 L 0 14 Z", OCHRE_DARK),
        p("M 14 22 L 56 22 L 56 214 L 14 214 Z", OCHRE_DARK),
        p("M 66 22 L 106 22 L 106 214 L 66 214 Z", OCHRE_DARK),
        p("M 56 22 L 66 22 L 66 214 L 56 214 Z", INK, None),
        c(50, 118, 3, INK, None), c(72, 118, 3, INK, None),
    ]), 120, 228)


def cake():
    return svg("".join([
        e(60, 70, 58, 10, WHITE),
        p("M 14 38 L 106 38 L 106 66 L 14 66 Z", OCHRE),
        p("M 14 38 Q 60 26 106 38 Q 100 50 92 42 Q 84 52 74 42 Q 66 52 56 42 Q 46 52 38 42 Q 28 52 14 44 Z", WHITE),
        c(40, 34, 5, RED), c(60, 30, 5, RED), c(80, 34, 5, RED),
    ]), 120, 82)


# -- Backdrops (470x520) -------------------------------------------------------

def bg_outdoors(far, ground, path_d=None, extra=""):
    body = [
        f'<rect x="0" y="0" width="{W}" height="{H}" fill="{SKY}"/>',
        p(far, GREEN_FAR, None),
        p(ground, GREEN_LIGHT, None),
    ]
    if path_d:
        body.append(p(path_d, "#D9BE8C", None))
    return svg("".join(body) + extra, W, H)


def bg_cottage():
    return bg_outdoors("M 0 300 Q 120 230 240 280 Q 360 220 470 270 L 470 520 L 0 520 Z",
                       "M 0 380 Q 240 350 470 376 L 470 520 L 0 520 Z",
                       "M 140 520 Q 180 440 150 380 L 190 380 Q 230 440 260 520 Z")


def bg_woods():
    far = "".join(p(f"M {x} {y} L {x + 36} {y + 120} L {x - 36} {y + 120} Z", GREEN_FAR, None)
                  for x, y in [(30, 170), (100, 150), (170, 180), (250, 140), (330, 170), (410, 150), (460, 180)])
    return bg_outdoors("M 0 290 L 470 290 L 470 520 L 0 520 Z",
                       "M 0 390 Q 240 370 470 392 L 470 520 L 0 520 Z",
                       "M 60 520 Q 200 470 250 400 Q 270 380 330 384 L 350 392 Q 300 400 290 420 Q 250 480 180 520 Z",
                       far)


def bg_meadow():
    tufts = "".join(line(f"M {x} {y} l -4 -12 M {x} {y} l 0 -14 M {x} {y} l 4 -12", GREEN, 2)
                    for x, y in [(40, 470), (110, 430), (200, 490), (300, 450), (390, 480), (440, 420), (250, 410)])
    return bg_outdoors("M 0 300 Q 150 250 300 290 Q 400 260 470 280 L 470 520 L 0 520 Z",
                       "M 0 350 Q 240 320 470 346 L 470 520 L 0 520 Z", None, tufts)


def bg_room():
    boards = "".join(line(f"M 0 {y} L {W} {y}", "#86633F", 2) for y in (410, 440, 474, 510))
    return svg("".join([
        f'<rect x="0" y="0" width="{W}" height="400" fill="{WALL}"/>',
        "".join(line(f"M {x} 0 L {x} 400", "#D6B983", 3) for x in range(30, W, 60)),
        f'<rect x="0" y="400" width="{W}" height="{H - 400}" fill="{FLOOR}"/>', boards,
        p("M 0 396 L 470 396 L 470 406 L 0 406 Z", TRUNK, None),
        p("M 290 70 L 410 70 L 410 200 L 290 200 Z", BLUE_LIGHT),
        # A far hill outside, under the window's frame (window_front).
        p("M 290 170 Q 340 150 410 164 L 410 200 L 290 200 Z", GREEN_FAR, None),
        p("M 70 80 L 150 80 L 150 150 L 70 150 Z", OCHRE_DARK),
        p("M 80 90 L 140 90 L 140 140 L 80 140 Z", GREEN_FAR),
        p("M 80 140 L 104 110 L 120 126 L 130 116 L 140 140 Z", GREEN, None),
    ]), W, H)


def window_front():
    """The room's window frame and curtains, drawn over whatever passes
    outside the glass; the rest is transparent."""
    return svg("".join([
        p("M 290 70 L 410 70 L 410 200 L 290 200 Z", "none", INK, 2.5),
        line("M 350 70 L 350 200 M 290 135 L 410 135", TRUNK, 4),
        p("M 276 60 L 310 60 Q 300 140 316 216 L 276 216 Z M 424 60 L 390 60 Q 400 140 384 216 L 424 216 Z", RED),
        p("M 270 56 L 430 56 L 430 64 L 270 64 Z", TRUNK),
    ]), W, H)


# -- Book and paper (PNG) -----------------------------------------------------

def table(width=320, height=180):
    """Dark wood under the book: stretched to the canvas."""
    rng = np.random.default_rng(3)
    y = np.arange(height)[:, None]
    x = np.arange(width)[None, :]
    grain = (np.sin(y * 0.35 + np.sin(x * 0.01 + y * 0.02) * 3) * 0.5 + 0.5) * 0.12
    grain = grain + rng.normal(0, 0.02, (height, width))
    base = np.array([74, 50, 34]) / 255
    shade = 0.75 + grain
    vign = 1 - 0.35 * (((x - width / 2) / (width / 2)) ** 2 + ((y - height / 2) / (height / 2)) ** 2)
    rgb = np.clip(base[None, None, :] * (shade * vign)[..., None] * 255, 0, 255)
    return Image.fromarray(rgb.astype(np.uint8), "RGB")


def paper(w=570, h=316):
    """Grain, age and the spine's shadow, to multiply over the pages: half
    the book's size, stretched over it."""
    rng = np.random.default_rng(11)
    y = np.arange(h)[:, None]
    x = np.arange(w)[None, :]
    tone = np.ones((h, w))
    # Fine grain.
    tone -= np.abs(rng.normal(0, 0.025, (h, w)))
    # Each page darker towards its outer edges and a little at the top and bottom.
    mid = w / 2
    from_spine = np.abs(x - mid) / mid
    tone -= 0.10 * np.clip((from_spine - 0.8) / 0.2, 0, 1) ** 2
    tone -= 0.08 * (np.clip(1 - y / 20, 0, 1) ** 2 + np.clip(1 - (h - y) / 20, 0, 1) ** 2)
    # The spine: a soft shadow where the pages curve into the binding.
    # A deep crease in the middle, a wider shade around it where the pages
    # bend down into the binding, and a little light where they rise again.
    tone -= 0.55 * np.exp(-((x - mid) / 2.4) ** 2)
    tone -= 0.30 * np.exp(-((x - mid) / 16) ** 2)
    tone += 0.05 * np.exp(-((x - mid - 34) / 22) ** 2) + 0.05 * np.exp(-((x - mid + 34) / 22) ** 2)
    # Foxing: a few faint brown spots.
    for _ in range(26):
        cx, cy = rng.uniform(0, w), rng.uniform(0, h)
        r = rng.uniform(1, 4.5)
        tone -= rng.uniform(0.03, 0.08) * np.exp(-(((x - cx) ** 2 + (y - cy) ** 2) / (r * r)))
    tone = np.clip(tone, 0, 1)
    # Darker tones lean brown, as old paper does.
    tint = np.array([1.0, 0.95, 0.86])
    rgb = 255 * (1 - (1 - tone[..., None]) / tint[None, None, :])
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB")


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    art = {
        "red_body": red_body(), "red_head": red_head(), "basket": basket(),
        "mother": mother(), "grandma": grandma(), "woodcutter": woodcutter(), "axe": axe(),
        "wolf_body": wolf_body(), "wolf_tail": wolf_tail(), "wolf_head": wolf_head(), "wolf_jaw": wolf_jaw(),
        "nightcap": nightcap(),
        "tree_pine": tree_pine(), "tree_round": tree_round(), "bush": bush(),
        "flower_red": flower(RED), "flower_white": flower(WHITE), "flower_blue": flower(BLUE_LIGHT),
        "butterfly": butterfly(), "bird": bird(), "cloud": cloud(),
        "cottage": cottage(), "fence": fence(), "bed": bed(), "cupboard": cupboard(), "cake": cake(),
        "bg_cottage": bg_cottage(), "bg_woods": bg_woods(), "bg_meadow": bg_meadow(), "bg_room": bg_room(),
        "window_front": window_front(),
    }
    for name, text in art.items():
        (out / f"{name}.svg").write_text(text)
    table().save(out / "table.png")
    paper().save(out / "paper.png", optimize=True)


if __name__ == "__main__":
    main()
