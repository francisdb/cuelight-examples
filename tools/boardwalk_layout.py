"""Where everything sits on the boardwalk backglass, shared by
tools/boardwalk_art.py (which paints it) and tools/boardwalk_show.py
(which puts the lamps and reels behind it), so a lamp is always behind
the part of the picture it lights.

One picture fills the 960x720 glass, as on the electromechanical games
of the late sixties and seventies: the score reels look through windows
in boards along the boardwalk, and everything a lamp lights (game over,
ball in play, match, tilt, shoot again, the players' turns) is painted
into the scene, each in a light box of its own.
"""

import math

WIDTH, HEIGHT = 960, 720
HORIZON = 404       # where the sea meets the sky
DECK = 520          # the front edge of the boardwalk's planks

# Score reels: five wheels per player on the arcade boards, two for the
# credits in the ticket booth.
REEL_W, REEL_H = 34, 52
REEL_COUNT = 5
BOARD_W, BOARD_TOP, BOARD_BOTTOM = 196, 552, 704
BOARDS = [(1, 14), (2, 216), (3, 552), (4, 754)]   # player, left edge
BOOTH = (422, 548, 116)                            # left, top, width
PLAYERS = [(p, x + (BOARD_W - REEL_W * REEL_COUNT) // 2, 604) for p, x in BOARDS]
CREDIT_W, CREDIT_H = 30, 42
CREDITS = (BOOTH[0] + (BOOTH[2] - 2 * CREDIT_W) // 2, 636)

CREAM = (244, 228, 194)
MUSTARD = (227, 170, 50)
ORANGE = (214, 98, 44)
RED = (196, 54, 42)
TEAL = (32, 122, 124)
INK = (30, 22, 18)


def rect(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def wedge(cx, cy, r0, r1, a0, a1, steps=6):
    """A ring segment between angles a0 and a1 (degrees, clockwise from
    the top), as a polygon."""
    pts = []
    for k in range(steps + 1):
        a = math.radians(a0 + (a1 - a0) * k / steps)
        pts.append((cx + r1 * math.sin(a), cy - r1 * math.cos(a)))
    for k in range(steps, -1, -1):
        a = math.radians(a0 + (a1 - a0) * k / steps)
        pts.append((cx + r0 * math.sin(a), cy - r0 * math.cos(a)))
    return pts


def ellipse(cx, cy, rx, ry, steps=28):
    return [(cx + rx * math.sin(2 * math.pi * k / steps), cy - ry * math.cos(2 * math.pi * k / steps))
            for k in range(steps)]


# Every lamp: a light box the shape of what it lights, painted with its
# lettering. (name, polygon, text, face colour, text colour, text box
# (x, y, w, h), variable, value). The lamp is lit while `variable`
# equals `value`, or while it is 1 or more when `value` is None. The
# variables are named after what they mean, as the table sets them.
LAMPS = []

for _player, _x in BOARDS:
    LAMPS.append((f"player_{_player}_up", rect(_x + 14, BOARD_TOP + 12, BOARD_W - 28, 30), f"PLAYER {_player} UP",
                  MUSTARD, INK, (_x + 14, BOARD_TOP + 12, BOARD_W - 28, 30), "player_up", _player))
    LAMPS.append((f"rollover_{_player}", rect(_x + 48, BOARD_BOTTOM - 38, BOARD_W - 96, 26), "100,000",
                  CREAM, RED, (_x + 48, BOARD_BOTTOM - 38, BOARD_W - 96, 26), f"rollover_{_player}", None))

# The ticket booth: a SPECIAL sign over the credit window.
LAMPS.append(("special", rect(BOOTH[0] + 10, BOOTH[1] + 20, BOOTH[2] - 20, 30), "SPECIAL", RED, CREAM,
              (BOOTH[0] + 10, BOOTH[1] + 20, BOOTH[2] - 20, 30), "special", None))

# The fortune wheel on the booth: its ten wedges are the match numbers.
MATCH_WHEEL = (480, 458, 58, 22)   # centre, outer and inner radius
for _k in range(10):
    _a0, _a1 = _k * 36 - 18 + 1.5, _k * 36 + 18 - 1.5
    _mid = math.radians(_k * 36)
    _tx = MATCH_WHEEL[0] + 41 * math.sin(_mid)
    _ty = MATCH_WHEEL[1] - 41 * math.cos(_mid)
    LAMPS.append((f"match_{_k * 10:02d}", wedge(MATCH_WHEEL[0], MATCH_WHEEL[1], MATCH_WHEEL[3], MATCH_WHEEL[2], _a0, _a1),
                  f"{_k * 10:02d}", [CREAM, MUSTARD][_k % 2], INK, (_tx - 12, _ty - 8, 24, 16), "match",
                  f"{_k * 10:02d}"))

# The coaster's five cars on the first hill: the ball in play.
COASTER_CARS = []
for _ball in range(1, 6):
    _x, _y = 116 + (_ball - 1) * 36, 214 + (_ball - 1) * 18
    COASTER_CARS.append((_x, _y))
    LAMPS.append((f"ball_{_ball}", rect(_x - 15, _y - 13, 30, 24), str(_ball), CREAM, INK, (_x - 15, _y - 13, 30, 24),
                  "ball_in_play", _ball))

# A biplane towing the game-over banner across the sky.
PLANE = (910, 96)
BANNER = (672, 76, 196, 42)
LAMPS.append(("game_over", rect(*BANNER), "GAME OVER", CREAM, RED, BANNER, "game_over", None))

# Tilt on the lifeguard tower's board, shoot again on a child's balloon.
TOWER = (424, 312)
LAMPS.append(("tilt", rect(TOWER[0] - 38, TOWER[1] - 14, 76, 30), "TILT", RED, CREAM,
              (TOWER[0] - 38, TOWER[1] - 14, 76, 30), "tilt", None))
BALLOON = (618, 344, 46, 56)   # centre and radii
LAMPS.append(("shoot_again", ellipse(*BALLOON), "SHOOT\nAGAIN", ORANGE, CREAM,
              (BALLOON[0] - 38, BALLOON[1] - 30, 76, 60), "shoot_again", None))

# Players in the game: four pennants on the booth's roof.
for _n in range(1, 5):
    _x = BOOTH[0] + 10 + (_n - 1) * 26
    LAMPS.append((f"can_play_{_n}", [(_x, 526), (_x + 22, 526), (_x + 11, 548)], str(_n), TEAL, CREAM,
                  (_x, 526, 22, 15), "players", _n))

# Captions painted on the scene that no lamp lights.
CAPTIONS = [
    ("CREDITS", BOOTH[0] + 10, 682, BOOTH[2] - 20, 16),
]

# The Ferris wheel and its bulbs (the bonus in a game), and the marquee
# bulbs along the top.
WHEEL_CENTER = (806, 262)
WHEEL_RADIUS = 136
WHEEL_BULBS = [
    (WHEEL_CENTER[0] + WHEEL_RADIUS * math.sin(2 * math.pi * k / 16),
     WHEEL_CENTER[1] - WHEEL_RADIUS * math.cos(2 * math.pi * k / 16)) for k in range(16)
]
MARQUEE_BULBS = [(24 + k * (WIDTH - 48) / 20, 16) for k in range(21)]

# The lamps that light the painting itself (GI): large bulbs behind the
# scene, so the light is a little uneven, as on a real glass.
GI_BULBS = [(140, 120, 460), (480, 110, 460), (820, 130, 460), (160, 400, 440), (480, 380, 440),
            (820, 420, 440), (240, 640, 420), (720, 640, 420)]
