#!/usr/bin/env python3
"""Write boardwalk's show.json.

    tools/boardwalk_show.py > boardwalk/show.json

The show is written out by a script because most of it is lamps at
positions tools/boardwalk_layout.py shares with the painting: sixty-odd
bulbs whose places have to match the lettering and the bulbs painted on
the glass.

From back to front:

1. The light behind the glass: a dim room light, the GI lamps behind the
   scene, a mask that keeps them off the title and a lamp the shape of
   each of its letters, the bulbs of the Ferris wheel (the bonus in a
   game) and of the marquee, and the light boxes: every sign, wedge, car
   or banner that shows the state of the game has one the shape of the
   thing itself, masked from the GI and evenly lit by a lamp of its own,
   all lit by the B2S data the table script sets. In attract the bulbs
   and the title chase.
2. The glass, multiplied over that light: the paint only glows where a
   lamp burns, in its own colours, as a translite does.
3. The score reels, behind their windows.
4. A little light spilling through the glass round the boxes that are
   lit, a faint reflection, and dust, scratches and pinholes on the
   glass.
"""

import json
import sys
from pathlib import Path

TITLE = json.loads((Path(__file__).resolve().parent / "boardwalk_title.json").read_text())

sys.path.insert(0, str(Path(__file__).resolve().parent))
from boardwalk_layout import (CREDIT_H, CREDIT_W, CREDITS, GI_BULBS, HEIGHT, LAMPS, MARQUEE_BULBS,  # noqa: E402
                              PLAYERS, REEL_COUNT, REEL_H, REEL_W, WHEEL_BULBS, WIDTH)

WARM = "#FFE2B0"
LAMP_ON = {"duration": 0.08, "ease": "quad_out"}


def track(prop, keys):
    return {"property": prop, "keys": [dict(t=k[0], v=k[1], **({"ease": k[2]} if len(k) > 2 else {})) for k in keys]}


def glow(name, x, y, w, h, tint=WARM, **kw):
    d = {"name": name, "type": "image", "image": "bulb", "x": round(x, 1), "y": round(y, 1), "size": [round(w), round(h)],
         "anchor": "center", "tint": tint, "blend": "add"}
    d.update(kw)
    return d


def lit_by(variable, value, scale=1.0):
    """A lamp's opacity binding: on while `variable` equals `value`, or
    while it is 1 or more when `value` is None."""
    if value is None:
        b = {"property": "opacity", "variable": variable, "threshold": 1}
    else:
        b = {"property": "opacity", "variable": variable, "map": {str(value): 1}, "default": 0}
    if scale != 1:
        b["scale"] = scale
    b["transition"] = LAMP_ON
    return b


# Attract mode is the game-over lamp: the bulbs chase while it is on.
ATTRACT = {"property": "visible", "variable": "data_35", "threshold": 1}
IN_GAME = {"property": "visible", "variable": "data_35", "threshold": 1, "scale": -1, "offset": 1}


def marquee():
    chase, steady = [], []
    # Three bulbs in a group, one lit at a time, the light running round
    # clockwise: each bulb loops the same blink, started a third of a
    # period after its neighbour.
    period = 0.6
    for k, (x, y) in enumerate(MARQUEE_BULBS):
        chase.append(glow(f"bulb_{k + 1}", x, y, 46, 46, opacity=0, timelines=[{
            "name": "chase", "autoplay": True, "loop": True, "delay": round((2 - k % 3) * period / 3, 3), "tracks": [
                track("opacity", [(0, 1), (period / 3 - 0.04, 1), (period / 3, 0.08), (period - 0.04, 0.08), (period, 1)])]}]))
        steady.append(glow(f"bulb_{k + 1}", x, y, 46, 46))
    return [
        {"name": "marquee_chase", "type": "group", "bindings": [ATTRACT], "children": chase},
        {"name": "marquee_steady", "type": "group", "bindings": [IN_GAME], "children": steady},
    ]


def wheel():
    chase, bonus = [], []
    # In attract, a tail of light running round the wheel, one turn every
    # 1.6 seconds. In a game the bulbs are the bonus: bulb k burns while
    # the bonus (data_40) is k or more.
    period, n = 1.6, len(WHEEL_BULBS)
    for k, (x, y) in enumerate(WHEEL_BULBS):
        chase.append(glow(f"bulb_{k + 1}", x, y, 44, 44, opacity=0.1, timelines=[{
            "name": "chase", "autoplay": True, "loop": True, "delay": round(k * period / n, 3), "tracks": [
                track("opacity", [(0, 1), (0.08, 1), (0.45, 0.1, "quad_out"), (period, 0.1)])]}]))
        bonus.append(glow(f"bulb_{k + 1}", x, y, 44, 44, opacity=0,
                          bindings=[{"property": "opacity", "variable": "data_40", "threshold": k + 1,
                                     "transition": LAMP_ON}]))
    return [
        {"name": "wheel_chase", "type": "group", "bindings": [ATTRACT], "children": chase},
        {"name": "wheel_bonus", "type": "group", "bindings": [IN_GAME], "children": bonus},
    ]


def title():
    """The title in light boxes of its own: a mask the shape of the
    letters keeps the GI off them, and each letter has a lamp of its own
    shape, lit by data_1 to data_9 as the player spells the name. In
    attract they light one after another, then flash together."""
    x, y, w, h = TITLE["mask"]
    out = [{"name": "title_mask", "type": "image", "image": "title_mask", "x": x, "y": y, "size": [w, h], "tint": "#2A2119"}]
    spelled, attract = [], []
    step, hold = 0.22, 2.4
    for i, (x, y, w, h) in enumerate(TITLE["letters"], 1):
        letter = {"type": "image", "image": f"title_{i}", "x": x, "y": y, "size": [w, h], "tint": WARM, "blend": "add"}
        spelled.append(dict(letter, name=f"letter_{i}", opacity=0,
                            bindings=[{"property": "opacity", "variable": f"data_{i}", "threshold": 1, "transition": LAMP_ON}]))
        on = round((i - 1) * step, 2)
        attract.append(dict(letter, name=f"letter_{i}", opacity=0, timelines=[{
            "name": "spell", "autoplay": True, "loop": True, "tracks": [track("opacity", [
                (0, 0), (on, 0), (on + 0.02, 1), (hold, 1), (hold + 0.02, 0), (hold + 0.25, 0), (hold + 0.27, 1),
                (hold + 0.5, 1), (hold + 0.52, 0), (hold + 0.75, 0), (hold + 0.77, 1), (hold + 1.4, 1), (hold + 1.42, 0),
                (hold + 1.9, 0)])]}]))
    out.append({"name": "title_spelled", "type": "group", "bindings": [IN_GAME], "children": spelled})
    out.append({"name": "title_attract", "type": "group", "bindings": [ATTRACT], "children": attract})
    return out


def path(polygon):
    return " ".join(f"{'M' if i == 0 else 'L'} {x:.1f} {y:.1f}" for i, (x, y) in enumerate(polygon)) + " Z"


def centre(polygon):
    xs, ys = [x for x, _ in polygon], [y for _, y in polygon]
    return (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, max(xs) - min(xs), max(ys) - min(ys)


def light_boxes():
    """The light boxes: a mask the shape of each keeps the GI out, the room
    light stays, and its own lamp lights it evenly, edge to edge."""
    masks, lamps = [], []
    for name, polygon, text, face, ink, box, variable, value in LAMPS:
        masks.append({"name": name, "type": "shape", "shape": {"path": path(polygon)}, "fill": "#2A2119"})
        lamps.append({"name": name, "type": "shape", "shape": {"path": path(polygon)}, "fill": WARM, "blend": "add",
                      "opacity": 0, "bindings": [lit_by(variable, value)]})
    return [{"name": "light_box_masks", "type": "group", "children": masks},
            {"name": "light_box_lamps", "type": "group", "children": lamps}]


def halation():
    """Light spilling through the glass round a lit box: soft and faint,
    on top of everything."""
    out = []
    for name, polygon, text, face, ink, box, variable, value in LAMPS:
        x, y, w, h = centre(polygon)
        out.append(glow(name, x, y, w * 1.4 + 30, h * 1.4 + 30, opacity=0, bindings=[lit_by(variable, value, 0.15)]))
    return out


def reels(name, x, y, digits, w, h, variable, font):
    shade = [{"name": f"shade_{k + 1}", "type": "image", "image": "reel_shade", "x": x + k * w, "y": y, "size": [w, h]}
             for k in range(digits)]
    return {
        "name": name, "type": "group", "children": [
            {"name": "drum", "type": "shape", "shape": {"rect": [x, y, w * digits, h]}, "fill": "#EFE2C4"},
            {"name": "digits", "type": "digits", "digits": digits, "x": x, "y": y, "size": [w * digits, h],
             "justify": "right", "text": "0" * digits,
             "display": {"reel": {"font": font, "charset": "0123456789", "duration": 0.06, "ease": "quad_in",
                                  "direction": "forward",
                                  "offset": [{"t": 0.06, "v": 0}, {"t": 0.09, "v": 0.1}, {"t": 0.13, "v": 0}]}},
             "bindings": [{"property": "text", "variable": variable}]},
        ] + shade,
    }


def show():
    light = [
        # The room: enough to make out the unlit lettering, as in an arcade.
        {"name": "room", "type": "shape", "shape": {"rect": [0, 0, WIDTH, HEIGHT]}, "fill": "#2A2119"},
        {"name": "gi", "type": "group",
         "bindings": [{"property": "opacity", "variable": "gi", "transition": {"duration": 0.1}}],
         # Relays pulling in on a new game make the lamps dip.
         "timelines": [{"name": "flicker", "trigger": "start", "tracks": [
             track("opacity", [(0, 1), (0.04, 0.35), (0.1, 1), (0.16, 0.55), (0.26, 1)])]}],
         "children": [
             {"name": "scene", "type": "shape", "shape": {"rect": [0, 0, WIDTH, HEIGHT]}, "fill": "#FFEBD0", "opacity": 0.55},
         ] + [glow(f"gi_{k + 1}", x, y, size, size, "#FFE7C4", opacity=0.55) for k, (x, y, size) in enumerate(GI_BULBS)]},
    ] + title() + marquee() + wheel() + light_boxes()

    # Paint is never laid on evenly: the light that gets through is patchy.
    light.append({"name": "paint", "type": "image", "image": "mottle", "size": [WIDTH, HEIGHT], "blend": "multiply"})
    layers = [{"name": "behind_the_glass", "type": "group", "children": light},
              {"name": "glass", "type": "image", "image": "glass", "blend": "multiply"}]

    for player, x, y in PLAYERS:
        layers.append(reels(f"player_{player}", x, y, REEL_COUNT, REEL_W, REEL_H, f"score_{player}", "reel"))
    layers.append(reels("credits", CREDITS[0], CREDITS[1], 2, CREDIT_W, CREDIT_H, "credits", "credit_reel"))

    layers.append({"name": "halation", "type": "group", "children": halation()})
    layers.append({"name": "sheen", "type": "image", "image": "sheen", "size": [WIDTH, HEIGHT], "blend": "add"})
    layers.append({"name": "wear", "type": "image", "image": "wear", "size": [WIDTH, HEIGHT], "blend": "screen"})

    layers.append({"name": "sounds", "type": "group", "children": [
        {"name": "clack", "type": "audio", "sound": ["clack1", "clack2"], "pick": "random",
         "trigger": ["chime_10", "chime_100", "chime_1000", "reel_step"], "retrigger": "overlap", "voices": 6, "gain": 0.5},
        {"name": "chime_10", "type": "audio", "sound": "chime_10", "trigger": "chime_10", "retrigger": "overlap", "gain": 0.7},
        {"name": "chime_100", "type": "audio", "sound": "chime_100", "trigger": "chime_100", "retrigger": "overlap", "gain": 0.7},
        {"name": "chime_1000", "type": "audio", "sound": "chime_1000", "trigger": "chime_1000", "retrigger": "overlap", "gain": 0.7},
        {"name": "coin", "type": "audio", "sound": "coin", "trigger": "coin", "gain": 0.8},
        {"name": "knocker", "type": "audio", "sound": "knocker", "trigger": "knocker", "gain": 0.9},
    ]})

    variables = {"gi": 1, "credits": "00", **{f"data_{i}": 0 for i in range(1, 10)}, "data_40": 0, "data_30": 0, "data_31": 0, "data_32": 0, "data_33": 0, "data_34": 0,
                 "data_35": 1, "data_36": 0, "data_41": 0}
    for player, _, _ in PLAYERS:
        variables[f"score_{player}"] = "0" * REEL_COUNT
        variables[f"data_{24 + player}"] = 0

    return {
        "$schema": "https://raw.githubusercontent.com/francisdb/cuelight/main/crates/cuelight/schemas/show.schema.json",
        "format": 1,
        "name": "boardwalk",
        "size": [WIDTH, HEIGHT],
        "background": "#000000",
        "fonts": {
            "reel": {"file": "LeagueGothic-Regular", "size": 50, "color": "#1C140E"},
            "credit_reel": {"file": "LeagueGothic-Regular", "size": 38, "color": "#1C140E"},
        },
        "variables": variables,
        "layers": layers,
    }


def compact(value, indent=0, width=150):
    """JSON with small objects and arrays on one line, like the hand-written shows."""
    flat = json.dumps(value, separators=(", ", ": "))
    if len(flat) + indent <= width or not isinstance(value, (dict, list)):
        return flat
    pad = " " * (indent + 2)
    if isinstance(value, dict):
        items = [f"{pad}{json.dumps(k)}: {compact(v, indent + 2, width)}" for k, v in value.items()]
        return "{\n" + ",\n".join(items) + "\n" + " " * indent + "}"
    items = [pad + compact(v, indent + 2, width) for v in value]
    return "[\n" + ",\n".join(items) + "\n" + " " * indent + "]"


if __name__ == "__main__":
    sys.stdout.write(compact(show()) + "\n")
