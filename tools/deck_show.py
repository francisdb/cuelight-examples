#!/usr/bin/env python3
"""Write the deck: deck/show.json and deck/test-driver.json.

    tools/deck_show.py

A slide deck about cuelight, made in cuelight. Every slide is a scene,
and every slide shows its point rather than only saying it: the code on
the declarative slide is the JSON of the bar drawn beside it, the
determinism slide keeps a frame and meets it again, the scrub slide
drives a small scene from one time value that plays and rewinds.

The host only says `next` and `prev` (and `slide_1` to jump home); each
slide knows which slide comes before and after it, so a keyboard or a
click maps straight onto those two events. The events slide also listens
for `coin` and `jackpot` and reads the `credits` variable.

Needs the fonts from tools/deck_fetch.sh, the sounds from
tools/deck_sounds.py, and the gallery's thumbnails in site/thumbnails.
"""

import json
import shutil
from pathlib import Path

from fontTools.ttLib import TTFont
from PIL import Image

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "deck"
SCHEMA = "https://raw.githubusercontent.com/francisdb/cuelight/main/crates/cuelight/schemas/show.schema.json"
W, H = 1280, 720
M = 80                                  # the page margin

PAPER, INK, SOFT, MUTED, RULE = "#F4EFE6", "#1C1B22", "#4A4740", "#8A857C", "#DDD6C8"
CORAL, COBALT, SUN, MINT = "#FF5A3C", "#2D5BFF", "#FFC21A", "#1FBF8F"
LIGHT = "#FFB000"                       # the "light" of cuelight, as the examples site writes it
NIGHT = "#1C1B22"                       # the code panels
ACCENTS = [CORAL, COBALT, SUN, MINT]

FILES = {
    "ArchivoBlack-Regular": "archivo", "AtkinsonHyperlegible-Regular": "atkinson",
    "AtkinsonHyperlegible-Bold": "atkinson_bold", "DMMono-Regular": "mono", "DMMono-Medium": "mono_medium",
}
_metrics = {}


def advance(file, size, text):
    """How wide a line sets: glyph advances alone, as the engine places them."""
    if file not in _metrics:
        font = TTFont(OUT / "assets/fonts" / f"{file}.ttf")
        _metrics[file] = (font.getBestCmap(), font["hmtx"], font["head"].unitsPerEm)
    cmap, hmtx, em = _metrics[file]
    return sum(hmtx[cmap[ord(c)]][0] for c in text) * size / em


def style(file, size, color, **extra):
    return {"file": file, "size": size, "color": color, **extra}


FONTS = {
    "hero": style("ArchivoBlack-Regular", 140, INK),
    "hero_light": style("ArchivoBlack-Regular", 140, LIGHT),
    "h1": style("ArchivoBlack-Regular", 52, INK),
    "h2": style("ArchivoBlack-Regular", 28, INK),
    "end": style("ArchivoBlack-Regular", 96, INK),
    "readout": style("ArchivoBlack-Regular", 60, INK),
    "jackpot": style("ArchivoBlack-Regular", 44, CORAL, border={"color": INK, "width": 3}),
    "lead": style("AtkinsonHyperlegible-Regular", 30, SOFT),
    "claim": style("AtkinsonHyperlegible-Bold", 42, SOFT),
    "body": style("AtkinsonHyperlegible-Regular", 25, INK),
    "body_bold": style("AtkinsonHyperlegible-Bold", 25, INK),
    "small": style("AtkinsonHyperlegible-Regular", 19, MUTED),
    "label": style("AtkinsonHyperlegible-Bold", 19, INK),
    "brand": style("AtkinsonHyperlegible-Bold", 19, MUTED),
    "brand_light": style("AtkinsonHyperlegible-Bold", 19, LIGHT),
    "label_paper": style("AtkinsonHyperlegible-Bold", 19, PAPER),
    "tag": style("AtkinsonHyperlegible-Bold", 15, MUTED),
    "chip": style("DMMono-Medium", 19, INK),
    "chip_paper": style("DMMono-Medium", 19, PAPER),
    "equation": style("DMMono-Medium", 36, INK),
    "mono_small": style("DMMono-Regular", 15, MUTED),
    "link": style("DMMono-Medium", 30, INK),
}

# Code on a night panel, coloured by what each piece is. A line of code
# is one piece of SVG artwork, its text in DM Mono from the show's own
# fonts with a tspan per coloured word, rather than a text layer per word.
CODE_SIZE = 18
CODE = {    # weight and colour
    "plain": (400, PAPER), "key": (400, "#9DB8FF"), "string": (400, "#FFC857"), "number": (400, "#5EE0B0"),
    "punct": (400, "#8E8A80"), "prompt": (500, CORAL), "out": (400, "#8E8A80"),
}
SVGS = {}


def width(font, text):
    return advance(FONTS[font]["file"], FONTS[font]["size"], text)


# ---------------------------------------------------------------- pieces

def text(name, words, x, y, font, anchor="top_left", **extra):
    return {"name": name, "type": "text", "text": words, "font": font, "x": x, "y": y, "anchor": anchor, **extra}


def rect(name, x, y, w, h, fill, radius=None, **extra):
    shape = {"rect": [0, 0, w, h]} | ({"radius": radius} if radius else {})
    return {"name": name, "type": "shape", "x": x, "y": y, "shape": shape, "fill": fill, **extra}


def centred_rect(name, x, y, w, h, fill, radius=None, **extra):
    """A rect around its layer's origin, so it scales and turns in place."""
    shape = {"rect": [-w / 2, -h / 2, w, h]} | ({"radius": radius} if radius else {})
    return {"name": name, "type": "shape", "x": x, "y": y, "shape": shape, "fill": fill, **extra}


def circle(name, x, y, r, fill, **extra):
    return {"name": name, "type": "shape", "x": x, "y": y, "shape": {"circle": [0, 0, r]}, "fill": fill, **extra}


def path(name, x, y, d, fill, **extra):
    return {"name": name, "type": "shape", "x": x, "y": y, "shape": {"path": d}, "fill": fill, **extra}


def group(name, children, x=0, y=0, **extra):
    return {"name": name, "type": "group", "x": x, "y": y, "children": children, **extra}


def timeline(layer, **spec):
    layer.setdefault("timelines", []).append(spec)
    return layer


def enter(layer, delay, rise=22, length=0.55):
    """Fade in while rising into place, `delay` seconds into the slide."""
    y = layer.get("y", 0)
    layer["opacity"] = 0
    return timeline(layer, name="enter", autoplay=True, delay=round(delay, 2), hold=True, tracks=[
        {"property": "opacity", "keys": [{"t": 0, "v": 0}, {"t": round(length * 0.7, 2), "v": 1, "ease": "quad_out"}]},
        {"property": "y", "keys": [{"t": 0, "v": y + rise}, {"t": length, "v": y, "ease": "cubic_out"}]},
    ])


def pop(layer, delay, length=0.5):
    """Grow from nothing with a small overshoot."""
    layer["scale"] = 0
    return timeline(layer, name="pop", autoplay=True, delay=round(delay, 2), hold=True, tracks=[
        {"property": "scale", "keys": [{"t": 0, "v": 0}, {"t": length, "v": 1, "ease": "back_out"}]},
    ])


def idle(layer, prop, low, high, period, delay=0.0):
    """A slow swing between two values, forever, starting at `low`."""
    return timeline(layer, name=f"idle_{prop}", autoplay=True, loop=True, delay=delay, tracks=[
        {"property": prop, "keys": [{"t": 0, "v": low}, {"t": period / 2, "v": high, "ease": "quad_in_out"},
                                    {"t": period, "v": low, "ease": "quad_in_out"}]},
    ])


def lines(name, rows, x, y, font, step, delay=None, gap=0.12):
    """A column of lines, each a layer, optionally entering one by one."""
    out = []
    for i, row in enumerate(rows):
        layer = text(f"{name}_{i}", row, x, y + i * step, font)
        out.append(enter(layer, delay + i * gap) if delay is not None else layer)
    return out


def bullets(name, rows, x, y, color, delay, step=46):
    """Lines each led by a small square in the slide's colour."""
    out = []
    for i, row in enumerate(rows):
        out.append(enter(group(f"{name}_{i}", [
            centred_rect("dot", 7, 16, 10, 10, color, radius=2),
            text("words", row, 28, 0, "body"),
        ], x, y + i * step), delay + i * 0.15))
    return out


def wordmark(name, x, y, font, anchor="top_left", **extra):
    """cuelight as the examples site writes it: "light" in its own colour,
    set right after "cue" so the two read as one word."""
    return group(name, [text("cue", "cue", 0, 0, font, anchor=anchor),
                        text("light", "light", round(width(font, "cue"), 1), 0, f"{font}_light", anchor=anchor)],
                 x, y, **extra)


def chip(name, words, x, y, fill, font="chip", pad=14, h=34, **extra):
    """A pill with a word in it, its left edge at x, centred on y."""
    w = width(font, words) + 2 * pad
    return group(name, [
        rect("pill", 0, -h / 2, w, h, fill, radius=h / 2),
        text("words", words, pad, 0, font, anchor="left"),
    ], x, y, **extra)


def arrow(name, x, y, color, size=18, left=False):
    """An arrow drawn as a shape: none of the text fonts has one."""
    s, d = size, (-1 if left else 1)
    points = [(0, -s * 0.12), (s * 0.55, -s * 0.12), (s * 0.55, -s * 0.45), (s, 0),
              (s * 0.55, s * 0.45), (s * 0.55, s * 0.12), (0, s * 0.12)]
    data = "M " + " L ".join(f"{round(px * d, 1)} {round(py, 1)}" for px, py in points) + " Z"
    return path(name, x, y, data, color)


def tick(name, x, y, color, size=22):
    s = size
    return path(name, x, y, f"M {-s * 0.5} 0 L {-s * 0.15} {s * 0.35} L {s * 0.5} {-s * 0.4}", "#00000000",
                stroke={"color": color, "width": s * 0.18})


# ---------------------------------------------------------------- code

TOKENS = [("string", r'"(?:[^"\\]|\\.)*"'), ("quoted", r"'[^']*'"), ("number", r"-?\d+(?:\.\d+)?"), ("punct", r"[{}\[\],:]"),
          ("space", r"\s+"), ("word", r"[^\s{}\[\],:\"]+")]


def number(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


DM_MONO = TTFont(OUT / "assets/fonts/DMMono-Regular.ttf") if (OUT / "assets/fonts/DMMono-Regular.ttf").exists() else None


def mono_text(pieces, size, y):
    """A line of DM Mono in SVG: `pieces` are (column, text, weight,
    colour), each a tspan on the font's fixed advance."""
    from xml.sax.saxutils import escape
    cell = DM_MONO["hmtx"][DM_MONO.getBestCmap()[ord("0")]][0] * size / DM_MONO["head"].unitsPerEm
    spans = "".join(f'<tspan x="{number(column * cell)}" fill="{color}"'
                    + (f' font-weight="{weight}"' if weight != 400 else "") + f">{escape(words)}</tspan>"
                    for column, words, weight, color in pieces)
    return (f'<text xml:space="preserve" font-family="DM Mono" font-size="{size}" y="{number(y)}">'
            f"{spans}</text>"), cell


def code_line(pieces):
    """SVG artwork of one line of code: `pieces` are (column, text, kind)."""
    scale = CODE_SIZE / DM_MONO["head"].unitsPerEm
    ascent, descent = DM_MONO["hhea"].ascent * scale, -DM_MONO["hhea"].descent * scale
    body, cell = mono_text([(c, t, *CODE[k]) for c, t, k in pieces], CODE_SIZE, ascent)
    w = number(max((c + len(t)) * cell for c, t, _ in pieces)) if pieces else "1"
    h = number(ascent + descent)
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{body}</svg>\n'


def code_block(name, rows, x, y, step=27, delay=None, shell=False, output=False):
    """Lines of code on DM Mono's fixed advance, each line one piece of
    vector art. JSON keys and values get their own colours; in a shell
    block the prompt is red and quoted words yellow, and output is grey."""
    import re
    pattern = re.compile("|".join(f"(?P<{k}>{p})" for k, p in TOKENS))
    layers = []
    for i, row in enumerate(rows):
        pieces, column = [], 0
        if output:
            pieces.append((0, row, "out"))
        else:
            for m in pattern.finditer(row):
                kind, piece = m.lastgroup, m.group()
                if kind != "space":
                    look = {"string": "string", "number": "number", "punct": "punct"}.get(kind, "plain")
                    if kind == "string" and row[m.end():].lstrip().startswith(":"):
                        look = "key"
                    if shell:
                        look = "prompt" if piece == "$" and column == 0 else \
                            "string" if piece.startswith("'") else "plain"
                    pieces.append((column, piece, look))
                column += len(piece)
        stem = f"code_{len(SVGS):02d}"
        SVGS[stem] = code_line(pieces)
        line = group(f"{name}_{i}", [{"name": "code", "type": "vector", "vector": stem, "x": 0, "y": 0}],
                     x, y + i * step)
        layers.append(enter(line, delay + i * 0.06, rise=10) if delay is not None else line)
    return layers


def pretty(value, indent=0, width=50, lead=0):
    """JSON as a person lays it out: what fits on a line stays on one.
    `lead` is how much of the line a key already takes."""
    one = json.dumps(value)
    if indent + lead + len(one) <= width or not isinstance(value, (dict, list)):
        return [" " * indent + one]
    open_, close = ("{", "}") if isinstance(value, dict) else ("[", "]")
    items = list(value.items()) if isinstance(value, dict) else [(None, v) for v in value]
    out = [" " * indent + open_]
    for n, (k, v) in enumerate(items):
        comma = "," if n < len(items) - 1 else ""
        head = f"{json.dumps(k)}: " if k is not None else ""
        inner = pretty(v, indent + 2, width, len(head))
        out.append(" " * (indent + 2) + head + inner[0].lstrip() + (comma if len(inner) == 1 else ""))
        if len(inner) > 1:
            out.extend(inner[1:-1])
            out.append(inner[-1] + comma)
    out.append(" " * indent + close)
    return out


# ---------------------------------------------------------------- a small scene as a function of time

HOPS = 4          # the ball hops once a second for four seconds


def motion(w, h):
    """The little scene's geometry and its curves against time."""
    r = round(h * 0.1, 1)
    floor = h - 18
    top = round(h * 0.28, 1)
    x_curve = [{"t": 0, "v": round(w * 0.1, 1)}, {"t": HOPS, "v": round(w * 0.78, 1)}]
    y_curve = [{"t": 0, "v": floor - r}]
    shadow_curve = [{"t": 0, "v": 1}]
    for k in range(HOPS):
        y_curve += [{"t": k + 0.5, "v": top, "ease": "quad_out"}, {"t": k + 1, "v": floor - r, "ease": "quad_in"}]
        shadow_curve += [{"t": k + 0.5, "v": 0.45, "ease": "quad_out"}, {"t": k + 1, "v": 1, "ease": "quad_in"}]
    spin = [{"t": 0, "v": 0}, {"t": HOPS, "v": 360}]
    return r, floor, x_curve, y_curve, shadow_curve, spin


def pose(name, variable, w, h, x=0, y=0, clip=True, fixed=None):
    """A ball hopping across a stage, a shadow under it and a square
    turning above: every property bound to one time value through a
    curve, so whatever that value does, play, jump or rewind, the
    picture is the one for that time."""
    r, floor, x_curve, y_curve, shadow_curve, spin = motion(w, h)

    def follow(layer, **curves):
        """Bind each property to the time value through its curve, or, for
        a frame at a fixed time, set it to the curve's value there."""
        for prop, keys in curves.items():
            if fixed is None:
                layer.setdefault("bindings", []).append({"property": prop, "variable": variable, "curve": keys})
            else:
                layer[prop] = round(at(keys, fixed), 2)
        return layer

    children = [
        rect("floor", 0, floor, w, 3, RULE),
        follow(centred_rect("spinner", round(w * 0.86, 1), round(h * 0.3, 1), round(h * 0.22, 1),
                            round(h * 0.22, 1), SUN, radius=6), rotation=spin),
        follow({"name": "shadow", "type": "shape", "shape": {"rect": [-r, -4, 2 * r, 8], "radius": 4},
                "fill": "#1C1B2233", "y": floor + 1}, x=x_curve, scale=shadow_curve),
        follow(circle("ball", 0, 0, r, CORAL), x=x_curve, y=y_curve),
    ]
    extra = {"clip": {"rect": [0, 0, w, h], "radius": 14}} if clip else {}
    return group(name, [rect("stage", 0, 0, w, h, "#FFFFFF", radius=14)] + children, x, y, **extra)


def bounce_out(u):
    n, d = 7.5625, 2.75
    if u < 1 / d:
        return n * u * u
    if u < 2 / d:
        return n * (u - 1.5 / d) ** 2 + 0.75
    if u < 2.5 / d:
        return n * (u - 2.25 / d) ** 2 + 0.9375
    return n * (u - 2.625 / d) ** 2 + 0.984375


def ease(kind, u):
    return {"linear": u, "quad_in": u * u, "quad_out": 1 - (1 - u) ** 2, "bounce_out": bounce_out(u)}[kind]


def at(keys, t):
    """A curve's value at t, the way the engine reads one (for the film
    strip, which shows frames of the same scene at fixed times)."""
    if t <= keys[0]["t"]:
        return keys[0]["v"]
    for a, b in zip(keys, keys[1:]):
        if t <= b["t"]:
            u = (t - a["t"]) / (b["t"] - a["t"])
            return a["v"] + (b["v"] - a["v"]) * ease(b.get("ease", "linear"), u)
    return keys[-1]["v"]


# ---------------------------------------------------------------- slides

slides = []


def slide(title, color, body, subtitle=None):
    """A slide: its own layers under a title, an underline in its colour,
    the page number and the progress bar along the foot."""
    n = len(slides) + 1
    chrome = []
    if title:
        chrome += [enter(text("title", title, M, 56, "h1"), 0.0),
                   timeline(rect("underline", M, 132, 72, 8, color, radius=4, scale_x=0), name="grow",
                            autoplay=True, delay=0.2, hold=True, tracks=[
                                {"property": "scale_x", "keys": [{"t": 0, "v": 0}, {"t": 0.5, "v": 1, "ease": "back_out"}]}])]
    if subtitle:
        chrome.append(enter(text("subtitle", subtitle, M, 158, "lead"), 0.15))
    slides.append({"title": title, "color": color, "layers": chrome + body})
    return n


def finish(total):
    scenes = []
    for n, s in enumerate(slides, 1):
        was, now = (n - 1) / total, n / total
        foot = [
            rect("progress_track", 0, H - 6, W, 6, RULE),
            timeline(rect("progress", 0, H - 6, W, 6, s["color"], scale_x=now), name="advance", autoplay=True,
                     hold=True, tracks=[{"property": "scale_x", "keys": [{"t": 0, "v": was}, {"t": 0.6, "v": now,
                                                                                     "ease": "cubic_out"}]}]),
            text("page", f"{n:02d} / {total:02d}", W - M, H - 34, "mono_small", anchor="right"),
        ]
        # What `next` and `prev` mean on this slide: a timeline of no
        # length whose end fires the slide to go to.
        routes = []
        if n < total:
            routes.append({"name": "next", "trigger": "next", "on_end": f"slide_{n + 1}",
                           "tracks": [{"property": "opacity", "keys": [{"t": 0, "v": 0}]}]})
        if n > 1:
            routes.append({"name": "prev", "trigger": "prev", "on_end": f"slide_{n - 1}",
                           "tracks": [{"property": "opacity", "keys": [{"t": 0, "v": 0}]}]})
        nav = {"name": "nav", "type": "shape", "shape": {"rect": [0, 0, 1, 1]}, "fill": "#00000000",
               "timelines": routes}
        scenes.append({"name": f"slide_{n}", "trigger": f"slide_{n}", "layers": s["layers"] + foot + [nav]})
    return scenes


# 1 -------------------------------------------------------------- title
shapes = [
    (circle, dict(name="circle", x=1010, y=250, r=92, fill=CORAL), 0.2, ("y", 250, 232, 3.4)),
    (centred_rect, dict(name="square", x=870, y=430, w=150, h=150, fill=COBALT, radius=18), 0.35,
     ("rotation", -8, 8, 5.2)),
    (path, dict(name="triangle", x=1110, y=470, d="M 0 -84 L 80 58 L -80 58 Z", fill=SUN), 0.5,
     ("rotation", 4, -6, 4.4)),
    (centred_rect, dict(name="pill", x=1000, y=600, w=210, h=56, fill=MINT, radius=28), 0.65,
     ("x", 1000, 1024, 3.8)),
]


def shape_set(prefix, delay=0.0):
    """The four shapes, each popping in and then swinging gently: the pop
    scales a holder at the shape's place, the swing moves the shape in it."""
    out = []
    for make, spec, wait, (prop, low, high, period) in shapes:
        spec = dict(spec, name=f"{prefix}_{spec['name']}")
        home = {"x": spec["x"], "y": spec["y"]}
        shape = make(**dict(spec, x=0, y=0))
        base = home.get(prop, 0)
        idle(shape, prop, low - base, high - base, period, delay=wait)
        out.append(pop(group(spec["name"] + "_holder", [shape], home["x"], home["y"]), delay + wait))
    return out


slide(None, CORAL, shape_set("title") + [
    enter(wordmark("name", M - 6, 190, "hero"), 0.1),
    enter(text("claim", "Motion you write down.", M, 360, "claim"), 0.35),
    *lines("pitch", ["A small engine for screens that react to a program:",
                     "explainers, game HUDs, overlays, backglasses."], M, 440, "body", 36, delay=0.6),
    enter(group("hint", [
        chip("key", "next", 0, 0, INK, font="chip_paper"),
        arrow("arrow", 76, 0, INK, size=20),
        text("words", "This deck is a cuelight show.", 112, 0, "small", anchor="left"),
    ], M, 620), 1.1),
])

# 2 -------------------------------------------------------------- where it fits
EXAMPLES = [("game_hud", "Game HUDs"), ("streamer_overlay", "Stream overlays"), ("boardwalk", "Pinball backglasses"),
            ("eclipse", "Explainers"), ("weather_dashboard", "Kiosks and dashboards"), ("red_riding_hood", "Picture books")]
CARD_W, CARD_H, THUMB_W, THUMB_H = 352, 214, 336, 172
cards = []
for i, (show, label) in enumerate(EXAMPLES):
    col, row = i % 3, i // 3
    source = REPO / "site/thumbnails" / f"{show}.png"
    iw, ih = Image.open(source).size
    fit = max(THUMB_W / iw, THUMB_H / ih)           # cover the window, centred
    size = [round(iw * fit, 1), round(ih * fit, 1)]
    cards.append(enter(group(f"card_{show}", [
        rect("card", 0, 0, CARD_W, CARD_H, "#FFFFFF", radius=14),
        group("window", [{"name": "shot", "type": "image", "image": show, "x": THUMB_W / 2, "y": THUMB_H / 2,
                          "anchor": "center", "size": size}],
              8, 8, clip={"rect": [0, 0, THUMB_W, THUMB_H], "radius": 9}),
        centred_rect("mark", 20, 197, 10, 10, ACCENTS[i % 4], radius=2),
        text("label", label, 34, 197, "label", anchor="left"),
    ], M + col * (CARD_W + 32), 212 + row * (CARD_H + 18)), 0.3 + i * 0.12))
slide("Where it fits", COBALT, cards,
      subtitle="Wherever a program knows what is happening and a screen should show it.")

# 3 -------------------------------------------------------------- declarative
FUEL = {"name": "fuel", "type": "shape", "shape": {"rect": [0, 0, 440, 40]}, "fill": MINT,
        "bindings": [{"property": "scale_x", "variable": "fuel", "scale": 0.01,
                      "transition": {"duration": 0.5, "ease": "back_out"}}]}
fuel_code = pretty(FUEL)
# The chip says what the host sent: its words follow the value.
host_chip = chip("host", "fuel = 72", 736, 424, SUN)
host_chip["children"][1]["bindings"] = [{"property": "text", "variable": "fuel", "decimals": 0, "prefix": "fuel = "}]
slide("Describe it. Don't program it.", MINT, [
    enter(rect("panel", M, 180, 600, 28 + 25 * len(fuel_code), NIGHT, radius=16), 0.2),
    *code_block("fuel_code", fuel_code, M + 26, 194, step=25, delay=0.35),
    enter(group("gauge", [
        text("label", "FUEL", 0, 0, "tag"),
        text("readout", "", 440, -20, "readout", anchor="top_right",
             bindings=[{"property": "text", "variable": "fuel", "decimals": 0, "suffix": "%",
                        "transition": {"duration": 0.5}}]),
        group("track", [rect("track", 0, 0, 440, 40, RULE), FUEL], 0, 60,
              clip={"rect": [0, 0, 440, 40], "radius": 20}),
    ], 736, 270), 0.5),
    enter(host_chip, 0.7),
    enter(text("host_note", "The host sets one number. The show does the rest.", 736, 456, "small"), 0.8),
    *bullets("points", ["No draw loop and no callbacks.",
                        "One file to edit, diff and review.",
                        "Tools can write it too. It is only JSON."], 736, 510, MINT, 1.0, step=42),
])

# 4 -------------------------------------------------------------- deterministic
RULER_X, RULER_W = M, 520


def ruler(name, x, y, w, variable, color, span=HOPS):
    """A time axis with a marker riding on `variable`."""
    marks = [rect("line", 0, 0, w, 3, INK)]
    for k in range(span + 1):
        marks += [rect(f"tick_{k}", round(k * w / span, 1) - 1, -8, 2, 16, INK),
                  text(f"label_{k}", f"{k}s", round(k * w / span, 1), 18, "mono_small", anchor="top")]
    marker = group("marker", [
        path("head", 0, -12, "M -9 -14 L 9 -14 L 0 0 Z", color),
        rect("stem", -1.5, -12, 3, 24, color),
    ], bindings=[{"property": "x", "variable": variable, "scale": w / span}])
    return group(name, marks + [marker], x, y)


SNAP_T = 2.8
PROBE = [(0.0, 0.6), (1.6, SNAP_T), (3.2, 1.4), (4.8, SNAP_T), (6.4, 3.6), (8.0, 0.6)]
slide("Same inputs, same frames.", CORAL, [
    enter(text("equation", "frame = show(inputs, t)", M, 196, "equation"), 0.25),
    enter(ruler("probe_ruler", M + 10, 300, RULER_W, "probe_t", CORAL), 0.4),
    enter(text("probe_readout", "", M + 10, 346, "chip", bindings=[
        {"property": "text", "variable": "probe_t", "decimals": 1, "prefix": "t = ", "suffix": " s"}]), 0.45),
    *bullets("points", ["Time is an input like any other: nothing reads the clock.",
                        "Random picks count plays, so every run picks alike.",
                        "Screenshot tests that do not flake, replays that match."], M, 420, CORAL, 0.8),
    enter(text("footnote", "Across GPUs a pixel may differ by one level; the engine's state never does.",
               M, 584, "small"), 1.3),
    enter(group("live", [text("tag", "LIVE, AT t", 0, 0, "tag"),
                         pose("scene", "probe_t", 380, 190, 0, 26)], 780, 186), 0.5),
    enter(group("kept", [text("tag", "KEPT AT t = 2.8 s", 0, 0, "tag"),
                         dict(pose("scene", "snap_t", 380, 190, 0, 26),
                              bindings=[{"property": "visible", "variable": "snap_t", "threshold": 0}])],
                780, 430), 0.6),
    group("same", [chip("badge", "same t, same frame", 0, 0, MINT)], M + 150, 358, opacity=0, timelines=[
        {"name": "flash", "trigger": "slide_4", "loop": True, "tracks": [{"property": "opacity", "keys": [
            {"t": 0, "v": 0}, {"t": 4.8, "v": 0, "ease": "step"}, {"t": 5.0, "v": 1, "ease": "quad_out"},
            {"t": 6.2, "v": 1}, {"t": 6.4, "v": 0, "ease": "quad_in"}, {"t": 8.0, "v": 0}]}]}]),
])

# 5 -------------------------------------------------------------- scrub
# One round outlasts the driver's 13 s on the slide, so it never starts
# over while the slide is up.
SCRUB = [(0, 0, "linear"), (4.0, 4.0, "linear"), (4.9, 1.2, "quad_in_out"), (6.9, 2.6, "quad_in_out"),
         (7.5, 0.5, "quad_in_out"), (8.1, 0.5, "linear"), (11.6, 4.0, "linear"), (14.0, 4.0, "linear")]
MODE = [(0, 0), (4.0, 1), (8.1, 0)]
TRACK_X, TRACK_Y, TRACK_W = 200, 544, 880
slide("Play it live. Scrub it like video.", SUN, [
    enter(pose("stage", "scrub", TRACK_W, 250, TRACK_X, 212), 0.2),
    enter(group("timeline", [
        rect("bar", 0, -26, TRACK_W, 52, "#FFFFFF", radius=12),
        rect("line", 20, -1, TRACK_W - 40, 2, RULE),
        *[path(f"key_{k}", round(20 + k * (TRACK_W - 40) / HOPS, 1), 0, "M 0 -9 L 9 0 L 0 9 L -9 0 Z", INK)
          for k in range(HOPS + 1)],
        group("playhead", [rect("line", -1.5, -34, 3, 68, CORAL), circle("knob", 0, -34, 8, CORAL)],
              20, 0, bindings=[{"property": "x", "variable": "scrub", "scale": (TRACK_W - 40) / HOPS, "offset": 20}]),
    ], TRACK_X, TRACK_Y), 0.35),
    enter(group("status", [
        chip("playing", "PLAYING", 0, 0, INK, font="chip_paper",
             bindings=[{"property": "visible", "variable": "scrub_mode", "map": {"0": 1}, "default": 0}]),
        chip("scrubbing", "SCRUBBING", 0, 0, CORAL, font="chip_paper",
             bindings=[{"property": "visible", "variable": "scrub_mode", "map": {"1": 1}, "default": 0}]),
        text("t", "", 150, 0, "chip", anchor="left", bindings=[
            {"property": "text", "variable": "scrub", "decimals": 2, "prefix": "t = ", "suffix": " s"}]),
    ], TRACK_X, 612), 0.45),
    enter(text("note", "Pause, drag, play on: every frame is one you can get back to.", TRACK_X, 164, "body"),
          0.3),
])

# 6 -------------------------------------------------------------- render
# What `--events` prints for the deck: the driver's first `next`, and
# the slide it leads to a frame later (checked by running it).
EVENTS = ['   7.000  driver Trigger { trigger: "next" }', '   7.017  Trigger("slide_2")']
RUN = [("in", "$ cuelight-render deck/ --every 0.04 --until 12 \\"),
       ("in", "    -o frames/"),
       ("in", "$ ffmpeg -framerate 25 -pattern_type glob \\"),
       ("in", "    -i 'frames/*.png' deck.mp4"),
       (None, ""),
       ("in", "$ cuelight-render deck/ --until 20 --events"),
       ("out", EVENTS[0]),
       ("out", EVENTS[1])]
typed, start = [], 0.6
cell = advance("DMMono-Regular", CODE_SIZE, "0")
for i, (kind, row) in enumerate(RUN):
    if not kind:
        start += 0.4
        continue
    words = code_block(f"run_{i}", [row], M + 26, 214 + i * 30, shell=True, output=kind == "out")[0]
    words["clip"] = {"rect": [-6, -8, 680, 34]}
    # A night strip over the line slides off it at typing speed; output
    # appears at once.
    cover = rect("cover", -4, -6, 690, 32, NIGHT)
    if kind == "in":
        keys = [{"t": 0, "v": -4}, {"t": round(len(row) * 0.018, 2), "v": round(len(row) * cell + 1, 1)}]
        took = len(row) * 0.018 + 0.2
    else:
        keys = [{"t": 0, "v": -4}, {"t": 0.05, "v": 690, "ease": "step"}]
        took = 0.15
    timeline(cover, name="type", autoplay=True, delay=round(start, 2), hold=True,
             tracks=[{"property": "x", "keys": keys}])
    words["children"].append(cover)
    typed.append(words)
    start += took

FRAME_W, FRAME_H, STRIP_X = 250, 131, 900
FRAME_STEP = FRAME_H + 24


def film():
    """The film strip: the same little scene at every half second, drawn
    once as artwork, and the eight frames twice so it rolls without a
    seam."""
    r, floor, x_curve, y_curve, shadow_curve, spin = motion(FRAME_W, FRAME_H)
    side = round(FRAME_H * 0.22, 1)
    parts = []
    for k in range(16):
        t = (k % 8) * 0.5
        top = 8 + k * FRAME_STEP
        x, y, grow, turn = (round(at(c, t), 2) for c in (x_curve, y_curve, shadow_curve, spin))
        label, _ = mono_text([(0, f"{t:.1f} s", 400, MUTED)], 15, 22)
        parts.append(
            f'<g transform="translate(8 {top})">'
            f'<rect x="-8" y="-8" width="{FRAME_W + 16}" height="{FRAME_H + 16}" rx="6" fill="{INK}"/>'
            f'<rect width="{FRAME_W}" height="{FRAME_H}" rx="14" fill="#FFFFFF"/>'
            f'<rect y="{floor}" width="{FRAME_W}" height="3" fill="{RULE}"/>'
            f'<rect x="{-side / 2}" y="{-side / 2}" width="{side}" height="{side}" rx="6" fill="{SUN}" '
            f'transform="translate({round(FRAME_W * 0.86, 1)} {round(FRAME_H * 0.3, 1)}) rotate({turn})"/>'
            f'<rect x="{-r}" y="-4" width="{2 * r}" height="8" rx="4" fill="{INK}" fill-opacity="0.2" '
            f'transform="translate({x} {floor + 1}) scale({grow})"/>'
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="{CORAL}"/>'
            f'<g transform="translate(10 0)">{label}</g>'
            f'</g>')
    height = 16 * FRAME_STEP
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{FRAME_W + 16}" height="{height}" '
            f'viewBox="0 0 {FRAME_W + 16} {height}">{"".join(parts)}</svg>\n')


SVGS["film"] = film()
strip = {"name": "reel", "type": "vector", "vector": "film", "x": -8, "timelines": [
    {"name": "roll", "autoplay": True, "loop": True, "tracks": [
        {"property": "y", "keys": [{"t": 0, "v": 0}, {"t": 12, "v": -8 * FRAME_STEP}]}]}]}
slide("Render it to frames or to video.", COBALT, [
    enter(rect("panel", M, 196, 720, 262, NIGHT, radius=16), 0.1),
    *typed,
    *bullets("points", ["The same engine with no window, in fixed steps.",
                        "Inputs on the command line: --trigger, --set.",
                        "Stills, strips for video, --events for tests."], M, 500, COBALT, 1.0, step=42),
    enter(group("film", [rect("base", -18, -8, FRAME_W + 36, 470, INK, radius=12),
                         group("window", [strip], 0, 12, clip={"rect": [-10, 0, FRAME_W + 20, 446]})],
                STRIP_X, 196), 0.3),
])

# 7 -------------------------------------------------------------- events
HOST_X, SHOW_X, WIRE_Y = M, 800, 330


def travel(name, words, fill, trigger, delay=0.0, font="chip"):
    """A chip that runs along the wire from host to show when `trigger`
    fires, and fades as it arrives."""
    layer = chip(name, words, HOST_X + 330, WIRE_Y, fill, font=font)
    layer["opacity"] = 0
    return timeline(layer, name="send", trigger=trigger, delay=delay, tracks=[
        {"property": "x", "keys": [{"t": 0, "v": HOST_X + 330}, {"t": 0.7, "v": SHOW_X - 130, "ease": "quad_in_out"}]},
        {"property": "opacity", "keys": [{"t": 0, "v": 1}, {"t": 0.6, "v": 1}, {"t": 0.75, "v": 0}]},
    ])


def flash(layer, trigger):
    """Light a line of the host's code as it runs."""
    return timeline(layer, name="run", trigger=trigger, tracks=[
        {"property": "opacity", "keys": [{"t": 0, "v": 1}, {"t": 0.9, "v": 0, "ease": "quad_in"}]}])


rays = [centred_rect(f"ray_{k}", 0, 0, 16, 140, SUN, radius=8, rotation=k * 30) for k in range(6)]
host_code = ['fire("coin")', 'set("credits", n)', 'fire("jackpot")']
slide("Events in, motion out.", SUN, [
    enter(group("host", [
        rect("box", 0, 0, 330, 250, NIGHT, radius=16),
        text("tag", "YOUR PROGRAM", 24, 22, "label_paper"),
        *[group(f"line_{i}", [flash(rect("glow", -8, -4, 290, 30, "#FFFFFF22", radius=6, opacity=0),
                                     ["coin", "coin", "jackpot"][i]),
                              *code_block("code", [row], 0, 0)], 24, 76 + i * 50)
          for i, row in enumerate(host_code)],
    ], HOST_X, WIRE_Y - 125), 0.2),
    enter(rect("wire", HOST_X + 330, WIRE_Y - 1.5, SHOW_X - HOST_X - 330, 3, INK), 0.3),
    enter(group("show", [
        rect("box", 0, 0, 400, 250, "#FFFFFF", radius=16),
        text("tag", "THE SHOW", 24, 22, "label"),
        group("burst", [*rays], 200, 140, opacity=0, timelines=[{"name": "burst", "trigger": "jackpot", "tracks": [
            {"property": "scale", "keys": [{"t": 0, "v": 0.3}, {"t": 0.8, "v": 1.6, "ease": "quad_out"}]},
            {"property": "rotation", "keys": [{"t": 0, "v": 0}, {"t": 0.8, "v": 40, "ease": "quad_out"}]},
            {"property": "opacity", "keys": [{"t": 0, "v": 0.9}, {"t": 0.8, "v": 0, "ease": "quad_in"}]}]}]),
        circle("coin", 110, 130, 34, SUN, stroke={"color": INK, "width": 4}, opacity=0, timelines=[
            {"name": "drop", "trigger": "coin", "tracks": [
                {"property": "y", "keys": [{"t": 0, "v": 40}, {"t": 0.6, "v": 150, "ease": "bounce_out"}]},
                {"property": "opacity", "keys": [{"t": 0, "v": 1}, {"t": 0.9, "v": 1}, {"t": 1.2, "v": 0}]}]}]),
        text("credits_tag", "CREDITS", 290, 70, "tag", anchor="top"),
        text("credits", "0", 290, 88, "readout", anchor="top", bindings=[
            {"property": "text", "variable": "credits", "decimals": 0, "transition": {"duration": 0.4}}]),
        text("jackpot", "JACKPOT!", 200, 206, "jackpot", anchor="center", scale=0, timelines=[
            {"name": "pop", "trigger": "jackpot", "tracks": [{"property": "scale", "keys": [
                {"t": 0, "v": 0}, {"t": 0.45, "v": 1, "ease": "back_out"}, {"t": 1.8, "v": 1},
                {"t": 2.1, "v": 0, "ease": "quad_in"}]}]}]),
    ], SHOW_X, WIRE_Y - 125), 0.4),
    travel("send_coin", "coin", SUN, "coin"),
    travel("send_credits", "credits", MINT, "coin", delay=0.15),
    travel("send_jackpot", "jackpot", CORAL, "jackpot"),
    *bullets("points", ["Triggers for moments, variables for state.",
                        "The program never says how anything looks."], M, 500, SUN, 0.8, step=42),
    enter(text("try", "Fire them yourself: coin, jackpot, or set credits.", SHOW_X, 504, "small"), 1.2),
    {"name": "coin_sound", "type": "audio", "sound": "coin", "trigger": "coin", "retrigger": "overlap"},
    {"name": "jackpot_sound", "type": "audio", "sound": "jackpot", "trigger": "jackpot"},
], subtitle=None)

# 8 -------------------------------------------------------------- for makers
# The dot runs along x at a steady pace and up by bounce_out, so it
# traces the plot of that easing drawn under it.
curve_path = "M 0 90 " + " ".join(f"L {x * 2} {round(90 - 90 * bounce_out(x / 100), 1)}" for x in range(1, 101))
COLUMNS = [
    ("Animators", CORAL, ["Keyframes, 13 easings", "Clips, blends, gradients", "Lamps that warm up"]),
    ("Explainer makers", COBALT, ["A story you can scrub", "Rendered to video", "Sound on the same clock"]),
    ("Game designers", MINT, ["Looks bound to state", "Attract, play, game over", "Restyle, no code change"]),
]
icons = [
    group("icon", [
        path("axes", 0, 0, "M 0 0 L 0 90 L 200 90", "#00000000", stroke={"color": RULE, "width": 3}),
        path("curve", 0, 0, curve_path, "#00000000", stroke={"color": INK, "width": 3}),
        circle("dot", 0, 90, 9, CORAL, timelines=[{"name": "trace", "autoplay": True, "loop": True, "tracks": [
            {"property": "x", "keys": [{"t": 0, "v": 0}, {"t": 1.6, "v": 200}, {"t": 2.4, "v": 200}]},
            {"property": "y", "keys": [{"t": 0, "v": 90}, {"t": 1.6, "v": 0, "ease": "bounce_out"}, {"t": 2.4, "v": 0}]}]}]),
    ], 0, 0),
    group("icon", [
        rect("frame", 0, 0, 150, 90, COBALT, radius=10),
        idle(path("play", 75, 45, "M -16 -22 L 24 0 L -16 22 Z", PAPER), "scale", 0.9, 1.15, 1.4),
        rect("bar", 0, 100, 150, 6, RULE, radius=3),
        timeline(rect("progress", 0, 100, 150, 6, COBALT, radius=3), name="play", autoplay=True, loop=True,
                 tracks=[{"property": "scale_x", "keys": [{"t": 0, "v": 0}, {"t": 4, "v": 1}]}]),
    ], 0, 0),
    group("icon", [
        rect("track", 0, 30, 200, 30, RULE, radius=15),
        group("health", [timeline(rect("fill", 0, 0, 200, 30, MINT), name="hits", autoplay=True, loop=True, tracks=[
            {"property": "scale_x", "keys": [{"t": 0, "v": 1}, {"t": 0.8, "v": 0.62, "ease": "back_out"},
                                             {"t": 1.8, "v": 0.3, "ease": "back_out"}, {"t": 3.2, "v": 1, "ease": "cubic_in_out"},
                                             {"t": 4, "v": 1}]}])], 0, 30, clip={"rect": [0, 0, 200, 30], "radius": 15}),
        text("hp", "HP", 0, 70, "tag"),
    ], 0, 0),
]
columns = []
for i, (head, color, points) in enumerate(COLUMNS):
    x = M + i * (CARD_W + 32)
    body = [rect("card", 0, 0, CARD_W, 410, "#FFFFFF", radius=16),
            group("art", [icons[i]], 28, 42),
            text("head", head, 28, 174, "h2")]
    y = 230
    for j, point in enumerate(points):
        body += [centred_rect(f"dot_{j}", 34, y + 15, 10, 10, color, radius=2), text(f"point_{j}", point, 52, y, "body")]
        y += 52
    columns.append(enter(group(f"column_{i}", body, x, 196), 0.25 + i * 0.15))
slide("For people who make things move.", CORAL, columns)

# 9 -------------------------------------------------------------- try it
slide(None, MINT, shape_set("end", delay=0.4) + [
    enter(text("try", "Try it.", M - 4, 150, "end"), 0.1),
    enter(group("site", [text("label", "Every example plays in the browser", 0, 0, "small"),
                         text("url", "francisdb.github.io/cuelight-examples", 0, 26, "link"),
                         rect("line", 0, 68, width("link", "francisdb.github.io/cuelight-examples"), 5, CORAL)],
                M, 300), 0.3),
    enter(group("repo", [text("label", "The engine", 0, 0, "small"),
                         text("url", "github.com/francisdb/cuelight", 0, 26, "link"),
                         rect("line", 0, 68, width("link", "github.com/francisdb/cuelight"), 5, COBALT)],
                M, 410), 0.45),
    enter(text("made", "This deck is one show.json, written by tools/deck_show.py.", M, 540, "body"), 0.7),
])

TOTAL = len(slides)
scenes = finish(TOTAL)

# ---------------------------------------------------------------- values the deck animates
values = {
    # Slide 3 plays the host: a real one setting `fuel` takes over.
    "fuel": {"timelines": [{"name": "host", "trigger": "slide_3", "loop": True, "keys": [
        {"t": 0, "v": 72}, {"t": 2.2, "v": 34, "ease": "step"}, {"t": 4.4, "v": 91, "ease": "step"},
        {"t": 6.6, "v": 58, "ease": "step"}, {"t": 8.8, "v": 72, "ease": "step"}]}]},
    "probe_t": {"timelines": [{"name": "jump", "trigger": "slide_4", "loop": True,
                               "keys": [{"t": t, "v": v, **({"ease": "step"} if t else {})} for t, v in PROBE]}]},
    # The kept frame: t stands still at 2.8 once the probe has been there.
    "snap_t": {"timelines": [{"name": "keep", "trigger": "slide_4", "hold": True, "keys": [
        {"t": 0, "v": -1}, {"t": 1.6, "v": SNAP_T, "ease": "step"}]}]},
    "scrub": {"timelines": [{"name": "drag", "trigger": "slide_5", "loop": True,
                             "keys": [{"t": t, "v": v, **({"ease": e} if t else {})} for t, v, e in SCRUB]}]},
    "scrub_mode": {"timelines": [{"name": "mode", "trigger": "slide_5", "loop": True,
                                  "keys": [{"t": t, "v": v, **({"ease": "step"} if t else {})} for t, v in MODE]
                                  + [{"t": SCRUB[-1][0], "v": 0}]}]},
}

layers = [
    {"name": "slide_sound", "type": "audio", "sound": "slide", "gain": 0.6,
     "trigger": [f"slide_{n}" for n in range(1, TOTAL + 1)]},
    wordmark("brand", M, H - 34, "brand", anchor="left"),
]

show = {
    "$schema": SCHEMA, "format": 1, "name": "deck", "size": [W, H], "background": PAPER,
    "fonts": FONTS,
    "variables": {"credits": 0},
    "values": values,
    "layers": layers,
    "scenes": scenes,
}

# ---------------------------------------------------------------- the driver
# Reads the deck the way a presenter would, with `next`; on the events
# slide it plays a program firing its events.
DWELL = {1: 7, 2: 8, 3: 10, 4: 9, 5: 13, 6: 9, 8: 9, 9: 7}
steps = [{"trigger": "slide_1"}, {"set": {"credits": 0}}]
for n in range(1, TOTAL + 1):
    if n == 7:
        for wait, action in [(2.0, "coin"), (1.3, "coin"), (1.8, "jackpot"), (2.6, "coin"), (2.5, None)]:
            steps.append({"wait": wait})
            if action == "coin":
                steps.append({"set": {"credits": sum(1 for s in steps if s.get("trigger") == "coin") + 1}})
            if action:
                steps.append({"trigger": action})
    else:
        steps.append({"wait": DWELL[n]})
    if n < TOTAL:
        steps.append({"trigger": "next"})
driver = {"loop": True, "steps": steps}


def compact(value, indent=0, width=118):
    """JSON that reads like the hand-written examples: short objects on one line."""
    one = json.dumps(value, ensure_ascii=False)
    pad = "  " * indent
    if len(one) + len(pad) <= width or not isinstance(value, (dict, list)) or not value:
        return one
    inner = "  " * (indent + 1)
    if isinstance(value, list):
        return "[\n" + ",\n".join(inner + compact(v, indent + 1, width) for v in value) + "\n" + pad + "]"
    return "{\n" + ",\n".join(inner + json.dumps(k) + ": " + compact(v, indent + 1, width) for k, v in value.items()) \
        + "\n" + pad + "}"


DEFAULTS = {"anchor": "top_left", "x": 0, "y": 0}


def rounded(value, layer=False):
    """Numbers without float noise, and a layer without the defaults it
    would have anyway."""
    if isinstance(value, float):
        return int(value) if value == int(value) else round(value, 3)
    if isinstance(value, list):
        return [rounded(v, layer) for v in value]
    if isinstance(value, dict):
        is_layer = "type" in value and "name" in value
        return {k: rounded(v, k in ("children", "layers")) for k, v in value.items()
                if not (is_layer and DEFAULTS.get(k, object()) == v)}
    return value


def main():
    shots = OUT / "assets"
    for old in [*shots.glob("code_*.svg"), shots / "film.svg"]:
        old.unlink(missing_ok=True)
    for stem, art in SVGS.items():
        (shots / f"{stem}.svg").write_text(art)
    for show_name, _ in EXAMPLES:
        shutil.copyfile(REPO / "site/thumbnails" / f"{show_name}.png", shots / f"{show_name}.png")
    (OUT / "show.json").write_text(compact(rounded(show)) + "\n")
    (OUT / "test-driver.json").write_text(compact(driver) + "\n")
    lines_ = (OUT / "show.json").read_text().count("\n")
    length = sum(s.get("wait", 0) for s in steps)
    print(f"deck/show.json: {TOTAL} slides, {lines_} lines; the driver reads it in {length:.0f} s")


if __name__ == "__main__":
    main()
