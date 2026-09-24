# weather_dashboard

A weather kiosk on a 1280x720 canvas: the current conditions with an
animated icon, the readings, a five-day forecast and the next eight hours
as bars, under a sky that follows the clock. Everything on it is a
variable a host would feed from a weather service; the driver plays a
whole day in two minutes so nothing stands still.

| Part | How it works |
| --- | --- |
| Icons | SVG files in `assets/`, drawn as `vector` layers: flat fills and strokes, sized into the layer. The parts that move are separate files |
| The animated "now" icon | one group per condition, its `opacity` a mapped binding on `condition` with a `transition`, so one crossfades into the next. Inside: sun rays that pulse (`scale` on a center-anchored vector), clouds that drift, rain and snow that move inside a clipped group. Their drops sit on a lattice, a column every 20 units with each column starting 12 lower, so one step of a column left and 48 down lands every drop where another one was: the rain travels exactly that step, which is also the way its drops lean, and repeats without a seam. Its clip is a leaning `path`, a parallelogram on the same angle, so drops only ever appear at its top under the cloud and never slide in from a side. Snow is symmetric, so it falls straight through a rect, sways on a period that does not divide the fall, and never repeats mechanically, a bolt that flashes on `step` keys, fog banks sliding past each other, a moon that floats |
| Clear at night | the clear icon holds a day group and a night group whose opacities are mapped from `sky`; opacity multiplies down the tree, so the condition picks the icon and the sky picks its face |
| Sky | three canvas-sized rects filled with vertical gradients, the night one at the bottom, dusk and day above it with opacities mapped from `sky` (`night`, `dawn`, `day`, `dusk`) through a 2.5 s `transition`: sunrise and sunset are crossfades. Stars twinkle on looping timelines, each with its own `delay` |
| Sun | `x` and `y` bound to `sun_x` and `sun_y`, with a `linear` transition as long as the feed interval, so a position posted every two seconds moves continuously. The host computes the arc; the show only follows |
| Temperature and readings | `text` bindings with a `transition`, so a new reading counts to its value. Units are separate texts next to right-aligned number boxes |
| Wind direction | an arrow `path` before the direction, pointing where the wind blows: its `rotation` is bound to `wind_deg` (where it comes from) with `offset` 180, on a 360 ring (`wrap`) taking the short way round with a `transition`; the sun's rays turn on a slow looping `rotation` as well as pulse |
| Forecast | five identical slots: a name, seven stacked icons with opacities mapped from `dN_cond`, and hi and lo texts the host formats (`14°`) |
| Hourly bars | a bar per hour inside a clipped group, its `y` bound to `hN` with `scale` and `offset` (84 pixels for -5 to 25 C) and a transition; the value label's `y` is bound the same way, so it rides on the bar |
| Cards | rounded rectangles as `path` shapes with arcs, translucent over the sky. The hills are one path |

It needs cuelight `main` with vector artwork and path shapes.

## Running

```sh
cd ../../cuelight
cargo run -p cuelight-player -- ../cuelight-examples/weather_dashboard
```

`test-driver.json` is picked up automatically and plays a day from 04:00 in
two minutes: a clear night, dawn, a sunny morning that clouds over, rain,
a thunderstorm, a clear sunset, fog and snow, with the sun on its arc,
the readings drifting and the forecast and hourly bars refreshing. It is
written by
[`tools/weather_dashboard_day.py`](../tools/weather_dashboard_day.py);
the show document is generated too, since its forecast slots, bars and
stars repeat. You can also set a variable from the player's prompt:
`condition=storm`, `sky=night`.

## Assets

Everything under `assets/` is committed and free to redistribute. Licenses
were checked at the linked sources on 2026-09-20; the license texts that
have to travel with the files are in [`licenses/`](licenses/).

| Asset | Origin | License |
| --- | --- | --- |
| `*.svg` | Made for this show, written by [`tools/weather_dashboard_assets.py`](../tools/weather_dashboard_assets.py) | MIT, as this repository |
| `fonts/Oxanium-Bold.ttf`, `fonts/Oxanium-SemiBold.ttf` | [Oxanium](https://github.com/sevmeyer/oxanium) by The Oxanium Project Authors, the unmodified static files from [`fonts/ttf`](https://github.com/sevmeyer/oxanium/tree/a8f39e0c71186190027a093e9001459410192d1e/fonts/ttf). Its digits all have the same width, so the readings keep their place while they count | [OFL-1.1](licenses/Oxanium-OFL.txt), no reserved font name |

The weather is made up; the city is real.

## What would make it better

- Gradients in SVGs: an icon's gradient still paints as its first stop,
  so the icons are flat.
- Layer templates or repeaters: the five forecast slots and the eight
  bars are the same block with another number in the variable names,
  which is why the document is generated.
- Text with a unit: `18°` and `36 km/h` from one binding and a format,
  instead of a number box and a unit text placed next to it.
- Bindable vector choice: one forecast icon layer picking its file from a
  map, instead of seven stacked layers per slot.
- A day that keeps time itself: the sun arc and the clock are host data
  here, which is right for a kiosk, but a demo would like a clock source.
