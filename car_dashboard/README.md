# car_dashboard

A digital instrument cluster on a 1280x480 canvas, driven almost entirely
by variables: the host says how fast the car goes, the show decides what
that looks like. No scenes, only shapes, text and one click.

| Part | How it works |
| --- | --- |
| Speed, range, temperature, trip, odometer | `text` bindings, the odometer with the `thousands` format |
| Gear | `text` binding with a `map`: `-1` is `R`, `0` is `N` |
| Rev bar | a bright bar inside a group with a `clip`, covered by a dark rect whose `x` is bound to `rpm` |
| Fuel and temperature gauges | a needle whose `rotation` is bound to the variable with a `transition` (`scale` and `offset` turn 50..130 C into -90..90 degrees), over a stroked arc `path` with a colored zone; the ignition sweeps them too |
| Shift lights | five circles whose `opacity` is bound to `rpm`, each with its own `offset`; opacity is clamped, so each switches on over a 100 rpm window |
| Sport mode | `mode` is a text variable: a mapped `font` binding turns the speed red, a mapped `opacity` binding shows the label |
| Warning lamps | group `opacity` bound to a 0/1 variable, from dim to lit |
| Ignition | the `ignition` trigger plays timelines that sweep the rev bar and light every lamp; a running timeline overrides a binding and hands the property back when it ends |
| Turn signals, hazard | each arrow is a `path` shape, the right one the left one with `scale_x` -1; each has one blink timeline with `repeat` and a list of triggers, `["turn_left", "hazard"]`, and an `audio` layer clicks like the relay on the same triggers, with the same `repeat`. The arrows are dim when off, like the lamps |

Everything the show uses is in cuelight `main`, including outline fonts:
the text is drawn from the TrueType outlines and the player renders at
window resolution, so the cluster stays sharp at any size.

## Running

```sh
cd ../../cuelight
cargo run -p cuelight-player -- ../cuelight-examples/car_dashboard
```

`test-driver.json` is picked up automatically and takes the car for a
50 second drive: ignition, up through the gears, a lane change, sport
mode up to the shift lights, braking, a fuel warning and a stop with the
hazards on. A driver script sets variables instantly, so the drive is ten
small steps a second, written by
[`tools/car_dashboard_drive.py`](../tools/car_dashboard_drive.py); the
show itself is written by hand. You can also set variables from the
player's prompt, `speed=88` or `mode=sport`.

## Assets

Everything under `assets/` is committed and free to redistribute. Licenses
were checked at the linked sources on 2026-09-20; the license texts that
have to travel with the files are in [`licenses/`](licenses/).

| Asset | Origin | License |
| --- | --- | --- |
| `sounds/click.ogg` | Made for this show, synthesized by [`tools/car_dashboard_sounds.py`](../tools/car_dashboard_sounds.py) | MIT, as this repository |
| `fonts/Oxanium-Bold.ttf`, `fonts/Oxanium-SemiBold.ttf` | [Oxanium](https://github.com/sevmeyer/oxanium) by The Oxanium Project Authors, the unmodified static files from [`fonts/ttf`](https://github.com/sevmeyer/oxanium/tree/a8f39e0c71186190027a093e9001459410192d1e/fonts/ttf). Its digits all have the same width, so numbers keep their place while they change | [OFL-1.1](licenses/Oxanium-OFL.txt), no reserved font name |

## What would make it better

- Bindable shape size (or a `width`/`height` property): the bars would be
  one rect each instead of a clip group with a sliding cover.
- Bindable `fill`: a lamp or a bar could change color with a mapped
  binding instead of stacking layers.
- Smoothing on bindings (follow the variable with a time constant), so a
  host can post values at its own rate and the display still moves
  smoothly; the driver here has to post ten times a second.
- Number formats with fixed decimals and units (`1.0`, `92 C`).
