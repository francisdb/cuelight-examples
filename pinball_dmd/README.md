# pinball_dmd

A pinball dot-matrix display: six switchable scenes on a 128x32 DMD, shown
in whole pixels (`scaling: pixel_perfect`). The score layouts are the ones
pinball machines have always used. Three scenes are `gray4` with a tint,
the way a monochrome DMD shows them: orange, and red for `williams`, since
the tint is the scene's. The jackpot and the video mode switch the output
to `rgb`.

| Scene | What it shows | How it works |
| --- | --- | --- |
| `welcome` | Title and a two-line info text | text layers centered in a `size` box, in two bitmap fonts |
| `stern` | Four player scores (active one highlighted), separator line, a content area with a title that gives way to a scrolling text | `text` bindings with `thousands`, a mapped `font` binding on `player`, a group `clip` |
| `williams` | Four corner scores, the active player in a big font | `anchor` on text, the same mapped `font` binding |
| `jackpot` | A bordered, flashing title under fireworks | font `border`, five layers of one sprite sheet with a row per color, each looping on its own `delay` and period |
| `night_drive` | Video mode: a road to the horizon, traffic, a car that changes lanes, a crash | see [below](#the-night-drive) |
| `alphanum` | 2x14 alphanumeric segment display, the second line blinking | `digits` rows with an `alpha14` display, in 9 pixel cells so that the characters stand apart |

## Running

```sh
cd ../../cuelight
cargo run -p cuelight-player -- ../cuelight-examples/pinball_dmd
```

`test-driver.json` is picked up automatically. It stands in for the table
script: it walks through all scenes, rotates the active player and posts
scores, and plays the video mode: it steers around four cars, runs into
the fifth and leaves for the last scene before the crash restarts the
run.

## The night drive

The host owns the game, the show only draws it:

| Host | Show |
| --- | --- |
| sets `lane` (0 to 2, fractions while changing lanes) | the player's `x` is bound to it, and so is the fireball's |
| fires `car_left`, `car_center`, `car_right` | one car per lane plays its `approach`: `x`, `y` and `scale` keyed along 1 / distance, anchored at its wheels, so it grows out of the vanishing point |
| fires `pass` when a car is behind | a bonus text pops up and fades |
| fires `crash` when it finds the player in a car's lane | the world group shakes, a still road covers the rolling one, the fireball flipbook plays, a title comes up, and the fireball's `on_end` restarts the scene for the next run |
| sets `speed` and `video_score` | text bindings in the HUD, which the intro keeps hidden |

The road itself is an 8-frame flipbook whose stripes are one step closer
in every frame; [`tools/pinball_dmd_night_drive.py`](../tools/pinball_dmd_night_drive.py)
draws it and documents the perspective rule, and its `--keys` prints the
keys of a car's approach.

## Assets

Everything under `assets/` is committed and free to redistribute. Licenses
were checked at the linked sources on 2026-09-20; the license texts that
have to travel with the files are in [`licenses/`](licenses/).

| Asset | Origin | License |
| --- | --- | --- |
| `fonts/tiny5-8.*` | [Tiny5](https://github.com/Gissio/font_tiny5) by The Tiny5 Project Authors, `Tiny5-Regular.ttf` from [Google Fonts](https://github.com/google/fonts/tree/b2723573ff4dd21b37158d1d549269e21a559df9/ofl/tiny5) rasterized at 8px with [`tools/ttf2bmfont.py`](../tools/ttf2bmfont.py) | [OFL-1.1](licenses/Tiny5-OFL.txt), no reserved font name |
| `fonts/jersey20-20.*` | [Jersey 20](https://github.com/scfried/soft-type-jersey) by The Soft Type Project Authors, `Jersey20-Regular.ttf` from [Google Fonts](https://github.com/google/fonts/tree/064d437c73364b35a95e42bad4621e25c8014e1e/ofl/jersey20) rasterized at 20px with [`tools/ttf2bmfont.py`](../tools/ttf2bmfont.py) | [OFL-1.1](licenses/Jersey20-OFL.txt), no reserved font name |
| `fireworks.png` | Made for this show, drawn by [`tools/pinball_dmd_fireworks.py`](../tools/pinball_dmd_fireworks.py) | MIT, as this repository |
| `nd_sky.png`, `nd_road.png`, `nd_traffic.png`, `nd_player.png`, `nd_crash.png` | Made for this show, drawn by [`tools/pinball_dmd_night_drive.py`](../tools/pinball_dmd_night_drive.py) | MIT, as this repository |

The bitmap fonts are modified versions in OFL terms (a format conversion),
so they stay under the OFL; neither font reserves its name. A font with a
reserved name would have to be renamed.

## What would make it better

- Segment displays that hold up at small cells. A cell's padding is a
  share of its width, which at 8 pixels rounds to nothing: the characters
  of a 2x16 display touch, and the unlit segments fill the cells into a
  mesh. So the `alphanum` scene has 14 cells of 9 pixels and no unlit
  segments; a padding of at least one pixel would give it its 16.
- Crisp diagonal segments: straight segments keep to whole pixels, the
  diagonal ones are antialiased and come out as a smear of half-lit
  pixels at this size, as the N, M and R of `ALPHANUMERIC` show. A score
  display cannot avoid them: 0, 1 and 7 have one too.
- A tint for images: the fireworks sheet repeats the same burst in four
  colors, and the traffic is three drawings of one car.
- A way for one timeline to stop or pause another: the road cannot be
  halted in a crash, so a still copy of it is faded in on top.
- A documented rule for two running timelines on the same property. The
  player car has an intro and a crash timeline on `opacity`; they never
  overlap here, but nothing says what would happen if they did.
- Polygon shapes: the road could be drawn instead of being a flipbook, and
  perspective stripes could be layers moving along it.
- A keyed path shared by several properties: a car's approach is the same
  eleven times in three tracks (`x`, `y`, `scale`), times three lanes.
- Collision detection stays with the host, as it should, but reading a
  layer's resolved position would let the host check where things are
  instead of mirroring the show's timing.
