#!/usr/bin/env python3
"""Write eclipse's show.json.

    tools/eclipse_show.py > eclipse/show.json

The show plays a total solar eclipse on its own, with no driver. The
moon's distance to the sun is a value of the show's own (`values`),
played as a chain of timelines, one per stretch between two contacts,
and each one's `on_end` fires the next contact as a trigger (`c1`,
`beads`, `c2`, `c3`, `emerged`, `c4`, and `cycle` to go round again).

Two kinds of listener:

- Things that change continuously with the moon's position bind to
  values. The moon and its disc read `distance` itself; the sky's
  darkness, the sun's glare, the sunlight left, the side diagram's two
  turns and the progress dot are values of their own, with the same
  stretches and keys computed here from the distance, since a binding
  can only scale and offset what it reads. This is the only place the
  physics lives, and each quantity is written once however many layers
  read it.
- Things that happen at a contact (captions, the corona, stars, the
  beads and the diamond ring, the contact marks) only know the name of
  the contact that starts them and of the one that ends them. They fade
  in on a timeline that holds its last value when it ends (`hold`) and
  fade out on a second one started later, which wins because of two held
  timelines the one started later owns the property. Their timing does
  not depend on how long a stretch is.

The layers sit in one scene whose trigger is `cycle`: re-entering the
scene stops every held timeline, so the loop starts clean. The values
live outside it, so their first stretch listens for `cycle` too.
"""

import json
import math
import sys

W, H = 1280, 720
PAPER = "#F3EDE0"
INK = "#1F2533"
MUTED = "#6B6F7A"
RULE = "#D3C9B5"
VERMILION = "#D2452C"
OCHRE = "#E9A72E"

# The sky window and the sun in it, in the window's own coordinates.
SKY_X, SKY_Y, SKY_W, SKY_H = 48, 104, 600, 568
SUN_X, SUN_Y = 300, 226
SUN_R, MOON_R = 100, 106
C1 = SUN_R + MOON_R  # centre distance at first and fourth contact
C2 = MOON_R - SUN_R  # at second and third
BEADS = 22  # where the last sliver starts breaking up

# The moon's distance to the sun (positive: to the sun's right) at the start
# and end of each stretch, how long it takes, which trigger starts it and
# which one it fires at its end. The moon moves right to left, as it does
# in the sky of the northern hemisphere, facing south.
STRETCHES = [
    ("approach", None, 4.0, C1 + 64, C1, "c1"),
    ("partial_in", "c1", 14.0, C1, BEADS, "beads"),
    ("beads", "beads", 1.6, BEADS, C2, "c2"),
    ("totality", "c2", 10.0, C2, -C2, "c3"),
    ("emerge", "c3", 1.6, -C2, -BEADS, "emerged"),
    ("partial_out", "emerged", 14.0, -BEADS, -C1, "c4"),
    ("depart", "c4", 6.0, -C1, -C1 - 64, "cycle"),
]
# The depart stretch moves for this long, then waits.
DEPART_MOVE = 4.0

# The side diagram: sun, moon and shadows turn together around the sun's
# centre, so the shadow sweeps over the observer on the Earth's edge.
DIA_SUN_X, DIA_SUN_Y, DIA_SUN_R = 736, 222, 46
DIA_MOON = 170  # moon's distance from the sun in the diagram
DIA_MOON_R = 9
EARTH_X, EARTH_R = 1330, 126
YOU_X = EARTH_X - EARTH_R
DIA_EARTH = YOU_X - DIA_SUN_X  # the observer's distance from the sun
ORBIT_R = EARTH_X - DIA_SUN_X - DIA_MOON  # the moon's orbit around the Earth
PENUMBRA_AT_EARTH = 62  # half-widths of the shadows where they reach the Earth
UMBRA_AT_EARTH = 3

# The contact track and the sunlight bar.
TRACK_Y = 440
TRACK = {"c1": 716, "c2": 916, "c3": 996, "c4": 1196}
BAR_X, BAR_Y, BAR_W = 800, 492, 396

CAPTION_X, CAPTION_Y = 716, 546


def overlap(d):
    """How much of the sun the moon covers at centre distance d, 0 to 1."""
    d = abs(d)
    r, R = SUN_R, MOON_R
    if d >= r + R:
        return 0.0
    if d <= R - r:
        return 1.0
    a = r * r * math.acos((d * d + r * r - R * R) / (2 * d * r))
    b = R * R * math.acos((d * d + R * R - r * r) / (2 * d * R))
    c = 0.5 * math.sqrt((-d + r + R) * (d + r - R) * (d - r + R) * (d + r + R))
    return (a + b - c) / (math.pi * r * r)


def darkness(d):
    """How dark the sky is: the eye hardly notices until the last few per
    cent, then night falls in seconds."""
    if abs(d) < C2:
        return 1.0
    covered = overlap(d)
    last = max(0.0, 1 - (abs(d) - C2) / (BEADS - C2))
    return min(0.9, 0.5 * covered**8 + 0.4 * last * last)


def shadow_offset(d):
    """Where the shadow's centre is from the observer, in diagram pixels:
    the penumbra's edge reaches them at first contact and the umbra's at
    second, and it moves evenly in between. Before and after the eclipse
    it hardly moves, so the wide penumbra stays inside the diagram."""
    s = min(abs(d), C1 + 16)
    if s <= C2:
        off = s * UMBRA_AT_EARTH / C2
    else:
        off = UMBRA_AT_EARTH + (s - C2) * (PENUMBRA_AT_EARTH - UMBRA_AT_EARTH) / (C1 - C2)
    return math.copysign(off, d)


def on_orbit(d):
    """The diagram's moon on its orbit, placed so that the line from the
    sun through it lands shadow_offset(d) from the observer. Returns the
    turn of the orbit around the Earth and the direction of the shadow,
    both in degrees clockwise."""
    goal = shadow_offset(d) / DIA_EARTH
    earth = EARTH_X - DIA_SUN_X

    def slope(phi):
        return ORBIT_R * math.sin(phi) / (earth - ORBIT_R * math.cos(phi))

    lo, hi = -0.6, 0.6
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if slope(mid) < goal else (lo, mid)
    phi = (lo + hi) / 2
    # Turning the orbit clockwise moves the moon, which sits on its sun
    # side, up; the shadow points along the line from the sun.
    return -math.degrees(phi), math.degrees(math.atan(goal))


def track_x(d):
    """The progress dot: first to fourth contact along the track, the
    totality stretched out so it can be seen."""
    if d >= C2:
        return TRACK["c1"] + (C1 - d) / (C1 - C2) * (TRACK["c2"] - TRACK["c1"])
    if d >= -C2:
        return TRACK["c2"] + (C2 - d) / (2 * C2) * (TRACK["c3"] - TRACK["c2"])
    return TRACK["c3"] + (-C2 - d) / (C1 - C2) * (TRACK["c4"] - TRACK["c3"])


def r(v, digits=3):
    v = round(v, digits)
    return int(v) if v == int(v) else v


def stretch_keys(stretch, value, step=None):
    """Keys for one stretch: value(d) at its ends, or sampled every `step`
    seconds for something that does not follow the distance linearly."""
    _, _, duration, d0, d1, _ = stretch
    moving = DEPART_MOVE if stretch[0] == "depart" else duration
    times = [0.0, moving]
    if step:
        n = max(1, round(moving / step))
        times = [moving * i / n for i in range(n + 1)]
    keys = [{"t": r(t), "v": r(value(d0 + (d1 - d0) * t / moving))} for t in times]
    if moving < duration:
        keys.append({"t": r(duration), "v": keys[-1]["v"]})
    return keys


def stretches(value, step=None, fire=False):
    """A value of the show's own that follows the moon: one timeline per
    stretch, started by the stretch's trigger and as long as it. The first
    starts at load and again on `cycle`, since values live outside the
    scene that `cycle` restarts. With `fire` it is the moon's distance
    itself, the show's clock, and fires the next cue."""
    timelines = []
    for stretch in STRETCHES:
        name, trigger, *_rest, on_end = stretch
        tl = {"name": name}
        if trigger is None:
            tl["autoplay"] = True
            tl["trigger"] = "cycle"
        else:
            tl["trigger"] = trigger
        if fire:
            tl["on_end"] = on_end
        tl["keys"] = stretch_keys(stretch, value, step)
        timelines.append(tl)
    return {"timelines": timelines}


def values():
    """Everything that moves with the moon, each as a number of its own;
    layers only bind to them."""
    return {
        "distance": stretches(lambda d: d, fire=True),
        "darkness": stretches(darkness, step=0.4),
        "glare": stretches(lambda d: 0.95 * (1 - overlap(d)) ** 0.7, step=0.5),
        "sunlight": stretches(lambda d: 1 - overlap(d), step=0.5),
        "orbit": stretches(lambda d: on_orbit(d)[0], step=0.5),
        "shadow": stretches(lambda d: on_orbit(d)[1] - on_orbit(d)[0], step=0.5),
        "progress": stretches(lambda d: min(TRACK["c4"], max(TRACK["c1"], track_x(d)))),
    }


def bind(prop, value, **extra):
    return [{"property": prop, "variable": value, **extra}]


def fade(name, keys, trigger=None, delay=None, prop="opacity", hold=False):
    """A timeline started by a cue (or with the scene when trigger is None).
    keys: [(t, v)] or [(t, v, ease)]."""
    tl = {"name": name}
    if trigger is None:
        tl["autoplay"] = True
    else:
        tl["trigger"] = trigger
    if delay:
        tl["delay"] = delay
    if hold:
        tl["hold"] = True
    out = []
    for k in keys:
        key = {"t": k[0], "v": k[1]}
        if len(k) > 2:
            key["ease"] = k[2]
        out.append(key)
    tl["tracks"] = [{"property": prop, "keys": out}]
    return tl


def shown(on, off, on_delay=None, off_delay=None, rise=0.6, fall=0.5, level=1):
    """Fade in on one cue and hold; fade out on another. The second timeline
    starts later, so it owns the opacity from then on. Without an end cue it
    holds until the scene starts over."""
    timelines = [fade("in", [(0, 0), (rise, level, "quad_out")], on, on_delay, hold=True)]
    if off is not None:
        timelines.append(fade("out", [(0, level), (fall, 0, "quad_in")], off, off_delay, hold=True))
    return timelines


def text(name, x, y, font, value, size=None, align=None, opacity=None):
    layer = {"name": name, "type": "text", "x": x, "y": y, "font": font, "text": value}
    if size:
        layer["size"] = size
    if align:
        layer["align"] = align
    if opacity is not None:
        layer["opacity"] = opacity
    return layer


def stops(*pairs):
    return [{"at": at, "color": color} for at, color in pairs]


def glow(name, radius, color, **extra):
    """A soft round glow: a circle whose radial gradient fades from its
    color at the centre to nothing at the edge, as (1 - r)^2.4."""
    fade = [(0, "FF"), (0.25, "80"), (0.5, "30"), (0.75, "09"), (1, "00")]
    return {"name": name, "type": "shape", "shape": {"circle": [0, 0, radius]},
            "fill": {"radial": {"center": [0, 0], "radius": radius,
                                "stops": stops(*[(at, color + alpha) for at, alpha in fade])}}, **extra}


def vertical(height, *pairs):
    """A vertical gradient over a box of this height, stops top to bottom."""
    return {"linear": {"from": [0, 0], "to": [0, height], "stops": stops(*pairs)}}


def circle(name, x, y, radius, fill, **extra):
    return {"name": name, "type": "shape", "x": x, "y": y, "shape": {"circle": [0, 0, radius]}, "fill": fill, **extra}


def rounded_rect(w, h, rad):
    return (
        f"M {rad} 0 H {w - rad} A {rad} {rad} 0 0 1 {w} {rad} V {h - rad} "
        f"A {rad} {rad} 0 0 1 {w - rad} {h} H {rad} A {rad} {rad} 0 0 1 0 {h - rad} "
        f"V {rad} A {rad} {rad} 0 0 1 {rad} 0 Z"
    )


def limb(angle_deg, radius=SUN_R):
    a = math.radians(angle_deg)
    return SUN_X + radius * math.cos(a), SUN_Y + radius * math.sin(a)


def beads(side, trigger, flicker):
    """Baily's beads on the limb where the last (or first) light is: side
    180 is the sun's left edge, 0 its right."""
    layers = []
    for i, (da, rad) in enumerate([(0, 2.6), (-7, 2.0), (6, 2.2), (-14, 1.6), (13, 1.8), (-21, 1.3)]):
        x, y = limb(side + da, SUN_R - 1.2)
        keys = flicker(i)
        layers.append(circle(f"bead_{i}", r(x, 2), r(y, 2), rad, "#FFFFFF", opacity=0,
                             timelines=[fade("flicker", keys, trigger)]))
    return layers


def diamond(name, side, trigger, keys):
    """The diamond ring: a glare and a four-pointed flare on the limb."""
    x, y = limb(side, SUN_R - 2)
    spikes = "M 0 -46 L 2 -2 L 58 0 L 2 2 L 0 46 L -2 2 L -58 0 L -2 -2 Z"
    return {
        "name": name, "type": "group", "x": r(x, 2), "y": r(y, 2), "opacity": 0, "blend": "screen",
        "timelines": [fade("flash", keys, trigger)],
        "children": [
            glow("glare", 75, "#FFF4DA"),
            glow("core", 20, "#FFFFFF"),
            {"name": "flare", "type": "shape", "shape": {"path": spikes}, "fill": "#FFFFFFD0"},
        ],
    }


def sky():
    """The sky window: what an observer sees."""
    sun_glare = glow("sun_glare", 210, "#FFF6DA", x=SUN_X, y=SUN_Y, blend="screen",
                     bindings=bind("opacity", "glare"))
    sky_total = {
        "name": "sky_total", "type": "shape", "shape": {"rect": [0, 0, SKY_W, SKY_H]}, "opacity": 0,
        "fill": vertical(SKY_H, (0, "#070B1E"), (0.55, "#18203F"), (0.85, "#3B3452"), (1, "#5A4455")),
        "bindings": bind("opacity", "darkness"),
    }
    stars = []
    for i, (x, y, rad) in enumerate([(70, 250, 1.6), (180, 64, 1.2), (540, 250, 1.4), (548, 188, 1.1), (410, 40, 1.0), (40, 300, 1.2), (560, 330, 1.3), (240, 36, 1.0)]):
        stars.append(circle(f"star_{i}", x, y, rad, "#E8ECFF", opacity=0,
                            timelines=shown("c2", "c3", on_delay=0.4 + 0.35 * i, rise=1.2, fall=0.4, level=0.9)))
    venus = circle("venus", 118, 372, 2.8, "#FFF7E0", opacity=0,
                   timelines=shown("beads", "emerged", off_delay=3, rise=1.4, fall=1.5))
    corona = {
        "name": "corona", "type": "group", "x": SUN_X, "y": SUN_Y, "opacity": 0, "blend": "screen",
        "timelines": [
            fade("inner", [(0, 0), (1.2, 0.35, "quad_out")], "beads", hold=True),
            fade("full", [(0, 0.35), (0.9, 1, "quad_out")], "c2", hold=True),
            fade("out", [(0, 1), (0.3, 0.35, "quad_out"), (2.2, 0, "quad_in")], "c3", hold=True),
        ],
        "children": [{"name": "streamers", "type": "image", "image": "corona", "anchor": "center"}],
    }
    # Prominences: pink flames just past the limb, uncovered where the moon
    # leaves a gap, first on the left, later on the right.
    proms = []
    for i, (angle, height, width) in enumerate([(196, 20, 9), (170, 15, 7), (214, 14, 8), (-16, 19, 8), (8, 15, 9), (30, 14, 6)]):
        a = math.radians(angle)
        cx, cy = SUN_X + (SUN_R + height / 2) * math.cos(a), SUN_Y + (SUN_R + height / 2) * math.sin(a)
        proms.append({
            "name": f"prominence_{i}", "type": "shape", "x": r(cx, 2), "y": r(cy, 2),
            "rotation": r(angle + 90, 1), "shape": {"path": f"M {-width / 2} {height / 2 + 2} Q {-width / 2} {-height / 2} 0 {-height / 2} Q {width / 2} {-height / 2} {width / 2} {height / 2 + 2} Z"},
            "fill": "#FF6F8E",
        })
    corona_group = {
        "name": "atmosphere", "type": "group", "opacity": 0,
        "timelines": [
            fade("in", [(0, 0), (0.8, 1, "quad_out")], "beads", 0.6, hold=True),
            fade("out", [(0, 1), (1.4, 0, "quad_in")], "emerged", hold=True),
        ],
        "children": proms,
    }
    # The part of the moon in front of the sun: a dark disc clipped to the
    # sun, so it only shows where it covers it.
    sun_face = {
        "name": "sun_face", "type": "group", "x": SUN_X, "y": SUN_Y,
        "clip": {"circle": [0, 0, SUN_R]},
        "children": [
            circle("photosphere", 0, 0, SUN_R, "#FFF7E2"),
            circle("moon_disc", C1 + 64, 0, MOON_R, "#262B38", bindings=bind("x", "distance")),
        ],
    }
    left_beads = beads(180, "beads", lambda i: [(0, 0), (0.7 + 0.08 * i, 0), (0.85 + 0.08 * i, 1, "quad_out"), (1.25 + 0.05 * (5 - i), 0.9), (1.45 + 0.03 * (5 - i), 0, "quad_in")])
    right_beads = beads(0, "c3", lambda i: [(0, 0), (0.1 + 0.07 * (5 - i), 1, "quad_out"), (0.9 + 0.06 * i, 1), (1.3 + 0.06 * i, 0, "quad_in")])
    beads_group = {"name": "beads", "type": "group", "x": 0, "y": 0, "children": left_beads + right_beads}
    # The moon itself, which is what drives the show: its timelines fire
    # the contacts. A dark silhouette unclipped, seen against the corona
    # around totality, and a faint outline the rest of the time, since a
    # new moon cannot be seen in daylight.
    moon = {
        "name": "moon", "type": "group", "x": SUN_X + C1 + 64, "y": SUN_Y,
        "bindings": bind("x", "distance", offset=SUN_X),
        "children": [
            circle("silhouette", 0, 0, MOON_R, "#0B0E18", opacity=0,
                   timelines=shown("beads", "emerged", rise=0.5, fall=0.9)),
            {"name": "outline", "type": "shape", "shape": {"circle": [0, 0, MOON_R]}, "fill": "#00000000",
             "stroke": {"color": "#FFFFFF", "width": 1.5}, "opacity": 0.55,
             "timelines": [
                 fade("hide", [(0, 0.55), (0.6, 0)], "beads", hold=True),
                 fade("show", [(0, 0), (1.5, 0.55)], "emerged", hold=True),
             ]},
        ],
    }
    horizon = {
        # Sunset all around: transparent at the top, deepening towards the land.
        "name": "horizon_glow", "type": "shape", "y": SKY_H - 200, "shape": {"rect": [0, 0, SKY_W, 150]},
        "fill": vertical(150, (0, "#E8785A00"), (0.5, "#F3955B38"), (0.75, "#F9A35B87"), (1, "#FFB25CFF")),
        "opacity": 0,
        "timelines": [
            fade("dusk", [(0, 0), (1.6, 0.35)], "beads", hold=True),
            fade("round", [(0, 0.35), (2.0, 1, "quad_out")], "c2", hold=True),
            fade("out", [(0, 1), (2.5, 0, "quad_in")], "c3", hold=True),
        ],
    }
    land = (
        f"M 0 {SKY_H - 70} C 60 {SKY_H - 84} 120 {SKY_H - 92} 190 {SKY_H - 80} "
        f"C 260 {SKY_H - 68} 300 {SKY_H - 62} 360 {SKY_H - 72} C 430 {SKY_H - 84} 520 {SKY_H - 96} {SKY_W} {SKY_H - 78} "
        f"V {SKY_H} H 0 Z"
    )
    # A tree on the left hill and two people on the right one, looking up.
    tree = (
        f"M 96 {SKY_H - 84} V {SKY_H - 110} "
        f"C 70 {SKY_H - 112} 66 {SKY_H - 142} 84 {SKY_H - 150} C 84 {SKY_H - 172} 112 {SKY_H - 176} 118 {SKY_H - 158} "
        f"C 138 {SKY_H - 156} 140 {SKY_H - 124} 120 {SKY_H - 112} C 112 {SKY_H - 108} 104 {SKY_H - 108} 102 {SKY_H - 110} V {SKY_H - 84} Z"
    )

    def person(x, base, height, lean):
        head = height * 0.16
        top = base - height
        return [
            circle(f"head_{x}", r(x + lean, 1), r(top + head, 1), r(head, 1), "#151924"),
            {"name": f"body_{x}", "type": "shape", "fill": "#151924", "shape": {"path": (
                f"M {x - height * 0.13} {base} L {x - height * 0.11 + lean * 0.5} {top + head * 2.2} "
                f"Q {x + lean * 0.5} {top + head * 1.7} {x + height * 0.11 + lean * 0.5} {top + head * 2.2} "
                f"L {x + height * 0.13} {base} Z")}},
        ]

    ground = [
        {"name": "land", "type": "shape", "shape": {"path": land}, "fill": "#1B2230"},
        {"name": "tree", "type": "shape", "shape": {"path": tree}, "fill": "#1B2230"},
        *person(452, SKY_H - 82, 34, -3),
        *person(476, SKY_H - 84, 28, -2),
    ]
    chips = [
        text("scale_normal", 18, 14, "chip", "1 second here \u2248 5 minutes", opacity=0) | {"timelines": [
                 fade("in", [(0, 0), (0.6, 1)], hold=True),
                 fade("out", [(0, 1), (0.4, 0)], "c2", hold=True),
                 fade("back", [(0, 0), (0.6, 1)], "c3", 1.0, hold=True),
             ]},
        text("scale_slow", 18, 14, "chip", "slowed down: 1 second here \u2248 15 seconds", opacity=0) | {
            "timelines": shown("c2", "c3", rise=0.6, fall=0.4)},
    ]
    # What the eye finds around the black disc, labelled while it lasts.
    callouts = []
    for name, (x, y), label, line, delay in [
        ("corona", (432, 58), "the corona: the sun's\nouter atmosphere", "M 470 106 L 424 136", 1.2),
        ("prominences", (24, 104), "prominences: glowing\ngas on the sun's edge", "M 120 152 L 182 188", 2.6),
    ]:
        callouts.append({
            "name": f"{name}_callout", "type": "group", "opacity": 0,
            "timelines": shown("c2", "c3", on_delay=delay, rise=0.8, fall=0.3),
            "children": [
                text("label", x, y, "callout", label, size=[160, 44], align="top_left"),
                {"name": "leader", "type": "shape", "shape": {"path": line}, "fill": "#00000000",
                 "stroke": {"color": "#FFFFFFB0", "width": 1}},
            ],
        })
    return {
        "name": "sky", "type": "group", "x": SKY_X, "y": SKY_Y,
        "clip": {"path": rounded_rect(SKY_W, SKY_H, 14)},
        "children": [
            {"name": "sky_day", "type": "shape", "shape": {"rect": [0, 0, SKY_W, SKY_H]},
             "fill": vertical(SKY_H, (0, "#4F8FCC"), (0.6, "#8DBDE6"), (1, "#CFE4F2"))},
            sky_total,
            *stars,
            venus,
            horizon,
            sun_glare,
            corona,
            corona_group,
            sun_face,
            beads_group,
            moon,
            diamond("ring_before", 180, "beads", [(0, 0), (0.9, 0), (1.3, 1, "quad_out"), (1.48, 0.8), (1.6, 0, "quad_in")]),
            diamond("ring_after", 0, "c3", [(0, 0), (0.25, 0.5), (0.8, 1, "quad_out"), (1.4, 0.9), (2.4, 0, "quad_in")]),
            *ground,
            *chips,
            *callouts,
        ],
    }


def diagram():
    """The side view: why the shadow falls where it does."""
    # The shadows start at the moon and run well into the Earth; what shows
    # of them is clipped.
    end = DIA_EARTH - DIA_MOON + 160
    spread = PENUMBRA_AT_EARTH + 160 * (PENUMBRA_AT_EARTH - DIA_MOON_R) / (DIA_EARTH - DIA_MOON)
    penumbra = f"M 0 {-DIA_MOON_R} L {end} {-r(spread, 2)} L {end} {r(spread, 2)} L 0 {DIA_MOON_R} Z"
    tip = UMBRA_AT_EARTH - 160 * (DIA_MOON_R - UMBRA_AT_EARTH) / (DIA_EARTH - DIA_MOON)
    umbra = f"M 0 {-DIA_MOON_R} L {end} {-r(max(tip, 0.5), 2)} L {end} {r(max(tip, 0.5), 2)} L 0 {DIA_MOON_R} Z"
    # The space in front of the Earth: the diagram's area with the Earth's
    # disc cut out of its right side, so the shadows stop at its surface.
    cut = math.sqrt(EARTH_R**2 - (EARTH_X - W) ** 2)
    space = (f"M 686 90 H {W} V {r(DIA_SUN_Y - cut, 2)} A {EARTH_R} {EARTH_R} 0 0 0 {W} {r(DIA_SUN_Y + cut, 2)} "
             f"V 340 H 686 Z")
    # Two turns: the orbit around the Earth's centre carries the moon, and
    # the moon's own group turns its shadows to point away from the sun.

    def orbiting(name, children):
        return {
            "name": name, "type": "group", "bindings": bind("rotation", "orbit"),
            "children": [{"name": "moon_place", "type": "group", "x": -ORBIT_R, "bindings": bind("rotation", "shadow"),
                          "children": children}],
        }

    rig = orbiting("rig", [
        {"name": "penumbra", "type": "shape", "shape": {"path": penumbra}, "fill": "#1F253326"},
        {"name": "umbra", "type": "shape", "shape": {"path": umbra}, "fill": "#1F2533D8"},
        circle("dia_moon", 0, 0, DIA_MOON_R, "#8A8F99", stroke={"color": INK, "width": 1.5}),
        text("moon_label", -40, -36, "note", "moon", size=[80, 20]),
    ]) | {"x": EARTH_X, "y": DIA_SUN_Y}
    # The same shadows, moved the same way, clipped to the Earth: where
    # they fall on it. The Earth itself covers their ends.
    on_earth = orbiting("shadow_on_earth", [
        {"name": "penumbra", "type": "shape", "shape": {"path": penumbra}, "fill": "#1F253333"},
        {"name": "umbra", "type": "shape", "shape": {"path": umbra}, "fill": "#1F2533D8"},
    ])
    orbit = {"name": "orbit", "type": "shape", "x": EARTH_X, "y": DIA_SUN_Y, "shape": {"circle": [0, 0, ORBIT_R]},
             "fill": "#00000000", "stroke": {"color": "#BDB5A5", "width": 1.2}}
    return [
        text("how", 690, 100, "label", "how it lines up"),
        {"name": "in_front_of_earth", "type": "group", "clip": {"path": space}, "children": [orbit, rig]},
        text("orbit_label", 926, 116, "note", "the moon's orbit"),
        {"name": "earth", "type": "group", "x": EARTH_X, "y": DIA_SUN_Y, "clip": {"circle": [0, 0, EARTH_R]},
         "children": [
             circle("ocean", 0, 0, EARTH_R, "#7FA7C9"),
             {"name": "continent", "type": "shape", "fill": "#9DB98A",
              "shape": {"path": "M -126 -40 C -110 -50 -96 -30 -104 -10 C -112 10 -96 30 -110 60 L -126 60 Z"}},
             on_earth,
         ]},
        {"name": "earth_edge", "type": "shape", "x": EARTH_X, "y": DIA_SUN_Y, "shape": {"circle": [0, 0, EARTH_R]},
         "fill": "#00000000", "stroke": {"color": INK, "width": 1.5}},
        circle("dia_sun", DIA_SUN_X, DIA_SUN_Y, DIA_SUN_R, OCHRE, stroke={"color": INK, "width": 1.5}),
        text("sun_label", DIA_SUN_X - 40, DIA_SUN_Y + DIA_SUN_R + 6, "note", "sun", size=[80, 20]),
        text("earth_label", 1228, 150, "chip", "Earth"),
        circle("you", YOU_X, DIA_SUN_Y, 4, VERMILION, stroke={"color": PAPER, "width": 1.5}),
        text("you_label", YOU_X - 56, DIA_SUN_Y - 36, "you", "you", size=[50, 22], align="right"),
        {"name": "umbra_key", "type": "shape", "x": 716, "y": 358, "shape": {"rect": [0, 0, 18, 10]}, "fill": "#1F2533D8"},
        text("umbra_note", 742, 350, "note", "umbra: total eclipse"),
        {"name": "penumbra_key", "type": "shape", "x": 916, "y": 358, "shape": {"rect": [0, 0, 18, 10]}, "fill": "#1F253326"},
        text("penumbra_note", 942, 350, "note", "penumbra: partial eclipse"),
    ]


def progress():
    """The four contacts along a track, a dot on it and the sunlight left."""
    layers = [
        {"name": "rule_top", "type": "shape", "x": 690, "y": 384, "shape": {"rect": [0, 0, 542, 1]}, "fill": RULE},
        text("contacts", 690, 396, "label", "contacts"),
        {"name": "track", "type": "shape", "x": TRACK["c1"], "y": TRACK_Y - 1,
         "shape": {"rect": [0, 0, TRACK["c4"] - TRACK["c1"], 2]}, "fill": RULE},
        {"name": "track_total", "type": "shape", "x": TRACK["c2"], "y": TRACK_Y - 2,
         "shape": {"rect": [0, 0, TRACK["c3"] - TRACK["c2"], 4]}, "fill": INK},
        text("totality_note", TRACK["c2"] - 20, TRACK_Y - 32, "note", "totality", size=[TRACK["c3"] - TRACK["c2"] + 40, 20]),
    ]
    names = {"c1": "first", "c2": "second", "c3": "third", "c4": "fourth"}
    for cue, x in TRACK.items():
        mark = [(0, 0.3), (0.3, 1, "quad_out")]
        layers.append({"name": f"tick_{cue}", "type": "shape", "x": x - 1, "y": TRACK_Y - 7,
                       "shape": {"rect": [0, 0, 2, 14]}, "fill": INK, "opacity": 0.3,
                       "timelines": [fade("reached", mark, cue, hold=True)]})
        layers.append(text(f"tick_{cue}_label", x - 40, TRACK_Y + 10, "tick", names[cue], size=[80, 20],
                           opacity=0.3) | {"timelines": [fade("reached", mark, cue, hold=True)]})
    layers.append(circle("dot", TRACK["c1"], TRACK_Y, 6, VERMILION, stroke={"color": PAPER, "width": 2},
                         bindings=bind("x", "progress")))
    layers += [
        text("sunlight", 690, 480, "label", "sunlight"),
        {"name": "bar_back", "type": "shape", "x": BAR_X, "y": BAR_Y, "shape": {"rect": [0, 0, BAR_W, 8]}, "fill": "#E4DBC9"},
        {"name": "bar", "type": "shape", "x": BAR_X, "y": BAR_Y, "shape": {"rect": [0, 0, BAR_W, 8]}, "fill": OCHRE,
         "bindings": bind("scale_x", "sunlight")},
        {"name": "rule_bottom", "type": "shape", "x": 690, "y": 524, "shape": {"rect": [0, 0, 542, 1]}, "fill": RULE},
    ]
    return layers


# (name, heading, body, start cue, start delay, end cue, end delay)
CAPTIONS = [
    ("new_moon", "New moon", "The moon passes between us and the sun. Its lit side\nfaces away, so in the bright sky you cannot see it.",
     None, 0, "c1", 0),
    ("first", "First contact", "The moon's edge touches the sun's. A small bite\nappears, and it grows for more than an hour.",
     "c1", 0.3, "c1", 5.0),
    ("partial", "Partial eclipse", "The eye adapts: with the sun nine tenths covered the\nday hardly looks darker, though most of its light is gone.",
     "c1", 5.6, "beads", 0),
    ("beads", "Baily's beads", "The last sunlight shines through valleys on the moon's\nedge, until one point is left: the diamond ring.",
     "beads", 0.2, "c2", 0.2),
    ("totality", "Totality", "The moon covers the whole sun. Its corona appears,\nstars and planets come out, dusk glows all around.",
     "c2", 0.5, "c2", 5.4),
    ("fit", "A perfect fit", "The sun is about 400 times wider than the moon and\nabout 400 times farther away: they look the same size.",
     "c2", 6.0, "c3", 0),
    ("third", "Third contact", "Sunlight bursts back as a diamond ring on the other\nside. From here on, only look through eclipse glasses.",
     "c3", 0.3, "emerged", 3.4),
    ("leaving", "Partial again", "The moon moves on. Its shadow races away over the\nEarth at well over a thousand kilometres an hour.",
     "emerged", 4.0, "c4", 0),
    ("fourth", "Fourth contact", "The moon leaves the sun. The same spot on Earth sees\na total eclipse only every few centuries.",
     "c4", 0.3, None, 0),
]


def captions():
    layers = []
    for name, heading, body, start, start_delay, end, end_delay in CAPTIONS:
        timelines = shown(start, end, on_delay=start_delay or None, off_delay=end_delay or None, rise=0.7, fall=0.4)
        layers.append({
            "name": f"caption_{name}", "type": "group", "x": CAPTION_X, "y": CAPTION_Y, "opacity": 0,
            "timelines": timelines,
            "children": [
                text("heading", 0, 0, "heading", heading),
                text("body", 0, 40, "body", body, size=[516, 80], align="top_left"),
            ],
        })
    return layers


def show():
    frame = {"name": "frame", "type": "shape", "x": SKY_X, "y": SKY_Y, "shape": {"path": rounded_rect(SKY_W, SKY_H, 14)},
             "fill": "#00000000", "stroke": {"color": INK, "width": 2}}
    scene_layers = [
        text("title", 46, 26, "title", "A total solar eclipse"),
        text("subtitle", 690, 44, "subtitle", "what you see, and why it happens", size=[542, 30], align="right"),
        sky(),
        frame,
        *diagram(),
        *progress(),
        *captions(),
        text("safety", SKY_X, 684, "note", "Never look at the sun without eclipse glasses, except during totality."),
        text("scale_note", 690, 684, "note", "Not to scale. Times compressed.", size=[542, 22], align="right"),
    ]
    return {
        "$schema": "https://raw.githubusercontent.com/francisdb/cuelight/main/crates/cuelight/schemas/show.schema.json",
        "format": 1,
        "name": "eclipse",
        "size": [W, H],
        "background": PAPER,
        "fonts": {
            "title": {"file": "Spectral-SemiBold", "size": 38, "color": INK},
            "subtitle": {"file": "Spectral-Italic", "size": 20, "color": MUTED},
            "heading": {"file": "Spectral-SemiBold", "size": 28, "color": INK},
            "body": {"file": "Spectral-Regular", "size": 19, "color": "#3A3F4B"},
            "label": {"file": "SpectralSC-SemiBold", "size": 17, "color": VERMILION},
            "note": {"file": "Spectral-Italic", "size": 15, "color": MUTED},
            "tick": {"file": "SpectralSC-SemiBold", "size": 15, "color": INK},
            "you": {"file": "Spectral-SemiBold", "size": 16, "color": VERMILION},
            "chip": {"file": "Spectral-Italic", "size": 17, "color": "#FFFFFFE0"},
            "callout": {"file": "Spectral-Italic", "size": 16, "color": "#FFFFFFE8"},
        },
        "values": values(),
        "layers": [],
        "scenes": [{"name": "eclipse", "trigger": "cycle", "layers": scene_layers}],
    }


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
    sys.stdout.write(compact(show()) + "\n")
