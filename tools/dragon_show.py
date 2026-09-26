#!/usr/bin/env python3
"""Write the dragon backglass: dragon/show.json and dragon/test-driver.json.

    tools/dragon_show.py

A backglass as solid-state machines had them around 1980: the painting
fills the glass, four 7-digit score displays and two small ones sit in
black windows cut into it, and lamps behind the glass light parts of the
picture and the lettering printed on it. The painting is Hokusai's
Dragon; the lamps light its eye, its head, its four claws and its tail.

Every lamp is a filament, so it comes up fast and dies away slowly. The
glass is dark where nothing lights it: the general illumination brings
the whole picture up while the machine is on, and a tilt takes it away.

The game only says what it knows: whether a game is on, how many play,
who is up, the ball, the scores, the credits, the feature lamps it
lights, tilt and shoot again. The attract show is the backglass's own.
"""

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "dragon"
W, H = 1000, 900
ART = 1000                 # the painting, square, cropped top and bottom
TOP = (H - ART) / 2        # where it starts: -50
SCHEMA = "https://raw.githubusercontent.com/francisdb/cuelight/main/crates/cuelight/schemas/show.schema.json"

GOLD = "#E2B862"
LAMP = {"model": "incandescent"}
SLOW = {"model": "incandescent", "kelvin": 2500, "heating": 0.02, "cooling": 0.2}  # the bigger bulbs behind the art


def at(fx, fy):
    """A point of the painting, from its share across and down."""
    return round(fx * ART, 1), round(fy * ART + TOP, 1)


# The parts of the dragon a lamp lights: where, how big. The game drives
# each with a variable of the same name. The eyes are two lights on one
# lamp, so they light together.
FEATURES = {
    "eye": [(0.638, 0.312, 0.03), (0.597, 0.305, 0.025)],
    "head": (0.635, 0.34, 0.14),
    "claw_1": (0.36, 0.33, 0.09),
    "claw_2": (0.21, 0.43, 0.09),
    "claw_3": (0.87, 0.43, 0.09),
    "claw_4": (0.13, 0.77, 0.09),
    "tail": (0.62, 0.83, 0.13),
}


def power(variable, transition=LAMP, **mapping):
    return {"variable": variable, **mapping, "transition": transition}


POOL, BULB = 0.6, 0.35   # how strongly a lit lamp shows through the art, and its bulb


def light(name, x, y, radius, source, color="#FFB45A"):
    """Light behind the glass: a soft warm pool that brightens the picture
    under it (screen), and the bulb's glow on top (add), both kept below
    full so the picture shows through."""
    return {"name": name, "type": "group", "children": [
        {"name": "pool", "type": "shape", "shape": {"circle": [x, y, radius]}, "blend": "screen", "opacity": 0,
         "fill": {"radial": {"center": [x, y], "radius": radius,
                             "stops": [{"at": 0, "color": color}, {"at": 1, "color": color + "00"}]}},
         "bindings": [{"property": "opacity", **source, "scale": POOL}]},
        {"name": "glow", "type": "image", "image": "glow", "x": x, "y": y, "size": [radius * 0.8, radius * 0.8],
         "anchor": "center", "blend": "add", "opacity": 0,
         "bindings": [{"property": "opacity", **source, "scale": BULB}, {"property": "tint", **source}]},
    ]}


def features(prefix, source_for):
    out = []
    for n, spots in FEATURES.items():
        spots = spots if isinstance(spots, list) else [spots]
        lights = [light(f"spot_{i}", *at(fx, fy), r * ART, source_for(n)) for i, (fx, fy, r) in enumerate(spots)]
        out.append(lights[0] | {"name": f"{prefix}_{n}"} if len(lights) == 1
                   else {"name": f"{prefix}_{n}", "type": "group", "children": lights})
    return out


def lettering(name, text, x, y, font, source=None, dark=0.18, **extra):
    """Printed on the glass, lit from behind when `source` says so."""
    layer = {"name": name, "type": "text", "text": text, "font": font, "x": x, "y": y, "anchor": "center", **extra}
    if source:
        layer["opacity"] = dark
        layer["bindings"] = [{"property": "opacity", **source, "scale": 1 - dark, "offset": dark}]
    return layer


INSERT_SIZES = (20, 24, 30, 34)


def insert(name, lines, x, y, source, size=24):
    """Words a lamp lights. They are painted on the art itself with no
    frame: unlit, dark ink that barely shows against the picture; lit,
    the letters shine through with a soft halo round them."""
    step = size * 1.2
    top = y - step * len(lines) / 2
    words = lambda f: [{"name": f"line_{i}", "type": "text", "text": text, "font": f, "x": x,
                        "y": round(top + step * (i + 0.5), 1), "anchor": "center"}
                       for i, text in enumerate(lines)]
    wide = max(len(t) for t in lines) * size * 0.8
    return {"name": name, "type": "group", "children": [
        {"name": "ink", "type": "group", "children": words(f"insert_unlit_{size}")},
        {"name": "halo", "type": "image", "image": "glow", "x": x, "y": y, "size": [wide, step * len(lines) * 2.2],
         "anchor": "center", "blend": "add", "opacity": 0,
         "bindings": [{"property": "opacity", **source, "scale": 0.35}, {"property": "tint", **source}]},
        {"name": "lit", "type": "group", "children": words(f"insert_{size}"), "opacity": 0,
         "bindings": [{"property": "opacity", **source}]},
    ]}


def display(name, x, y, digits, variable, cell=38):
    """A black window cut into the art with a 7-segment display in it."""
    w, h = cell * digits + 24, cell * 1.55 + 18
    return {"name": name, "type": "group", "children": [
        {"name": "window", "type": "shape", "shape": {"rect": [x, y, w, h], "radius": 6}, "fill": "#050303",
         "stroke": {"color": "#8A7A5A", "width": 2}},
        {"name": "digits", "type": "digits", "digits": digits, "size": [cell * digits, cell * 1.55], "x": x + 12,
         "y": y + 9, "justify": "right", "text": "",
         "display": {"segments": {"style": "numeric7", "fill": "#FF5A1E", "unlit": "#260904",
                                  "glow": {"size": 0.2, "strength": 0.5}}},
         "bindings": [{"property": "text", "variable": variable}]},
    ]}


# ---------------------------------------------------------------- attract
# The features light one after another round the dragon, then all flash
# twice. A value steps through them.
ORDER = ["tail", "claw_4", "claw_2", "claw_1", "head", "eye", "claw_3"]
STEP = 0.45
keys = [{"t": 0, "v": 0}] + [{"t": round(STEP * k, 2), "v": k, "ease": "step"} for k in range(1, len(ORDER))]
t = STEP * len(ORDER)
for _ in range(2):                          # all on, all off, twice
    keys += [{"t": round(t, 2), "v": 99, "ease": "step"}, {"t": round(t + 0.4, 2), "v": -1, "ease": "step"}]
    t += 0.8
keys.append({"t": round(t + 0.6, 2), "v": -1})
ATTRACT = {"timelines": [{"name": "round", "autoplay": True, "loop": True, "keys": keys}]}


def attract_source(name):
    return power("attract", SLOW, map={str(ORDER.index(name)): 1, "99": 1}, default=0)


# ---------------------------------------------------------------- the glass
players = []
for p, (x, y, nx) in {1: (58, 150, 30), 2: (652, 150, 970), 3: (58, 700, 30), 4: (652, 700, 970)}.items():
    players.append({"name": f"player_{p}", "type": "group", "children": [
        display("score", x, y, 7, f"score_{p}"),
        # The player-up number beside the window.
        insert("up", [str(p)], nx, y + 38, power("player", LAMP, map={str(p): 1}, default=0), size=34),
    ]})


def when(variable, value="true"):
    return power(variable, LAMP, map={value: 1}, default=0)


layers = [
    {"name": "art", "type": "image", "image": "dragon", "x": 0, "y": TOP, "size": [ART, ART]},
    # The foot of the glass is painted dark, for the lettering the lamps
    # light to stand on.
    {"name": "foot", "type": "shape", "shape": {"rect": [0, 660, W, H - 660]},
     "fill": {"linear": {"from": [0, 660], "to": [0, 800],
                         "stops": [{"at": 0, "color": "#0A040200"}, {"at": 1, "color": "#0A0402E8"}]}}},
    # The glass where no lamp is lit: dark, until the general illumination
    # comes on. A tilt switches it off.
    {"name": "unlit_glass", "type": "shape", "shape": {"rect": [0, 0, W, H]}, "fill": "#000000", "opacity": 0.62,
     "bindings": [{"property": "opacity", "variable": "gi", "map": {"true": 0.18}, "default": 0.62,
                   "transition": {"duration": 0.25, "ease": "quad_out"}}]},
    {"name": "attract_lamps", "type": "group", "children": features("attract", attract_source),
     "bindings": [{"property": "visible", "variable": "game_running", "map": {"false": 1}, "default": 0}]},
    {"name": "game_lamps", "type": "group", "children": features("game", when),
     "bindings": [{"property": "visible", "variable": "game_running", "map": {"true": 1}, "default": 0}]},
    # The title, printed across the waves and lit from behind.
    lettering("title", "DRAGON", W / 2, 70, "title", when("gi"), dark=0.55),
    lettering("players", "1 TO 4 CAN PLAY", W / 2, 132, "small"),
] + players + [
    display("credits", 318, 800, 2, "credits", cell=32),
    lettering("credits_label", "CREDITS", 318 + 44, 788, "small"),
    display("ball", 598, 800, 2, "ball", cell=32),
    lettering("ball_label", "BALL IN PLAY", 598 + 44, 788, "small"),
    insert("tilt", ["TILT"], 500, 190, when("tilt"), size=30),
    insert("shoot_again", ["SAME PLAYER", "SHOOTS AGAIN"], 500, 252, when("shoot_again"), size=20),
    insert("game_over", ["GAME OVER"], 160, 842, when("game_running", "false")),
    insert("match", ["MATCH"], 502, 842, when("match_lit")),
    insert("high_score", ["HIGH SCORE", "TO DATE"], 845, 842, when("high_score"), size=20),
]

show = {
    "$schema": SCHEMA, "format": 1, "name": "dragon", "size": [W, H], "background": "#000000",
    "fonts": {
        "title": {"file": "DelaGothicOne-Regular", "size": 92, "color": GOLD,
                  "border": {"color": "#2A1206", "width": 4}, "shadow": {"color": "#000000B0", "offset": [4, 5]}},
        # The inserts' words: printed in dark ink, bright when lit.
        **{f"insert_{n}": {"file": "DelaGothicOne-Regular", "size": n, "color": "#FFE2A0"} for n in INSERT_SIZES},
        **{f"insert_unlit_{n}": {"file": "DelaGothicOne-Regular", "size": n, "color": "#3A1C0C"} for n in INSERT_SIZES},
        "small": {"file": "DelaGothicOne-Regular", "size": 17, "color": GOLD,
                  "border": {"color": "#1A0A04", "width": 2}},
    },
    "variables": {"game_running": False, "gi": True, "players": 0, "player": 0, "ball": "", "credits": 3,
                  "score_1": "", "score_2": "", "score_3": "", "score_4": "",
                  "tilt": False, "shoot_again": False, "match_lit": False, "high_score": False,
                  **{n: False for n in FEATURES}},
    "values": {"attract": ATTRACT},
    "layers": layers,
}

# ---------------------------------------------------------------- the driver
# Only what a game knows, in about a minute: two players, a feature lamp
# lit for each claw made, a tilt that kills the lights, a shoot again, a
# match at the end.
steps = []


def state(wait, **values):
    steps.append({"set": values})
    steps.append({"wait": wait})


state(12, game_running=False, gi=True, players=0, player=0, ball="", credits=3, tilt=False, shoot_again=False,
      match_lit=False, high_score=False, score_1="", score_2="", score_3="", score_4="",
      **{n: False for n in FEATURES})
state(1.5, game_running=True, players=1, player=1, ball=1, credits=2, score_1=0)
state(2.0, players=2, score_2=0)
for score, lamp in ((3000, "claw_1"), (5500, None), (8500, "claw_2"), (12000, None), (23000, "head")):
    state(1.2, score_1=score, **({lamp: True} if lamp else {}))
state(2.0, player=2, claw_1=False, claw_2=False, head=False)
for score in (1500, 4000, 6500):
    state(1.2, score_2=score)
state(3.0, tilt=True, gi=False)
state(1.0, tilt=False, gi=True, player=1, ball=2)
for score, lamp in ((26000, "claw_3"), (29500, "claw_4"), (41000, "eye")):
    state(1.2, score_1=score, **{lamp: True})
state(1.0, shoot_again=True)
state(2.5, shoot_again=False, tail=True, score_1=66000)
state(2.0, player=2, claw_3=False, claw_4=False, eye=False, tail=False)
for score in (9000, 14500):
    state(1.2, score_2=score)
state(2.0, player=1, ball=3)
for score in (71000, 82500):
    state(1.2, score_1=score)
state(5.0, game_running=False, player=0, ball=30, match_lit=True, high_score=True)


def compact(value, indent=0, width=118):
    """JSON that reads like the hand-written examples: short objects on one line."""
    one = json.dumps(value, ensure_ascii=False)
    pad = "  " * indent
    if len(one) + len(pad) <= width or not isinstance(value, (dict, list)) or not value:
        return one
    inner = "  " * (indent + 1)
    if isinstance(value, list):
        return "[\n" + ",\n".join(inner + compact(v, indent + 1, width) for v in value) + "\n" + pad + "]"
    lines, line = [], ""
    for k, v in value.items():
        item = f"{json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}"
        if len(inner) + len(item) > width:
            if line:
                lines.append(line)
                line = ""
            lines.append(f"{json.dumps(k)}: {compact(v, indent + 1, width)}")
        elif line and len(inner) + len(line) + 2 + len(item) > width:
            lines.append(line)
            line = item
        else:
            line = f"{line}, {item}" if line else item
    if line:
        lines.append(line)
    return "{\n" + ",\n".join(inner + l for l in lines) + "\n" + pad + "}"


(OUT / "show.json").write_text(compact(show) + "\n")
(OUT / "test-driver.json").write_text(compact({"loop": True, "steps": steps}) + "\n")
print(f"dragon/show.json: {sum(1 for _ in open(OUT / 'show.json'))} lines, "
      f"a round of {sum(s.get('wait', 0) for s in steps):.1f} s")
