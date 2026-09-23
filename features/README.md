# Feature examples

Small shows that each demonstrate one thing the show format can do, the
way the [Bevy examples](https://bevy.org/examples/) do for Bevy. They all
play on the [website](https://francisdb.github.io/cuelight-examples/),
next to their source, and in the player:

```sh
cargo run -p cuelight-player -- ../cuelight-examples/features/timelines/easing
```

| Folder | Examples |
| --- | --- |
| [layers](layers/) | `shapes`, `opacity`, `scale_anchor`, `group_clip`, `paths`, `blend_modes`, `rotation` |
| [images](images/) | `image`, `sprite_sheet`, `tint` |
| [text](text/) | `bitmap_font`, `outline_font`, `digits`, `reels` |
| [bindings](bindings/) | `scale_offset`, `text_format`, `map_default`, `font`, `transitions`, `visible_threshold_debounce` |
| [timelines](timelines/) | `easing`, `delay_repeat_loop`, `on_end`, `trigger_lists`, `precedence` |
| [scenes](scenes/) | `scenes` |
| [sound](sound/) | `audio_layers`, `pick` |
| [output](output/) | `modes`, `scaling`, `dots` |
| [events](events/) | `show_events` |

Titles and descriptions live in [`examples.json`](../examples.json), which
is what the website's gallery is built from.

## Conventions

- One feature per show, and as little else as possible. Captions are
  `digits` layers (segment displays), so most examples need no assets.
- 640x360 canvas, unless the example is about small canvases.
- A `test-driver.json` wherever the show needs a host to come alive, so
  the example plays by itself in the gallery. Visitors can pause it and
  fire the triggers and set the variables themselves.

## Assets

| Asset | Used by | Source | License |
| --- | --- | --- | --- |
| `badge.png`, `coin.png` | `images/image`, `images/sprite_sheet` | drawn by [`tools/feature_assets.py`](../tools/feature_assets.py) | same as this repository |
| `reel.png` | `bindings/transitions` | drawn by `tools/feature_assets.py`, its digits set in the Oxanium below | same as this repository |
| `logo.svg` | `layers/paths` | written by hand for the example | same as this repository |
| `glow.png` | `layers/blend_modes` | drawn by `tools/feature_assets.py` | same as this repository |
| `badge.png`, `bulb.png`, `white_glow.png`, `worn.png` | `images/tint` | drawn by `tools/feature_assets.py`, the last three white or grey so a tint decides their color | same as this repository |
| `music.wav`, `coin.wav`, `thunder.wav`, `jingle.wav` | `sound/audio_layers` | synthesized from sines and noise by [`tools/feature_sounds.py`](../tools/feature_sounds.py) | same as this repository |
| `knock1.wav`, `knock2.wav`, `knock3.wav` | `sound/pick` | synthesized by `tools/feature_sounds.py`: three takes of one knock | same as this repository |
| `tiny5-8` bitmap font | `text/bitmap_font` | [Tiny5](https://github.com/Gissio/font_tiny5), rasterized with [`tools/ttf2bmfont.py`](../tools/ttf2bmfont.py) | [OFL 1.1](text/bitmap_font/licenses/Tiny5-OFL.txt), no reserved font name |
| `silkscreen-8`, `silkscreen_bold-16` bitmap fonts | `text/bitmap_font` | [Silkscreen](https://github.com/googlefonts/silkscreen) from [Google Fonts](https://github.com/google/fonts/tree/e44c4b011a820c2cbe2fd2cfa8052037d7edb571/ofl/silkscreen), rasterized with `tools/ttf2bmfont.py` (the bold one at 16 pixels with `--padding 2`) | [OFL 1.1](text/bitmap_font/licenses/Silkscreen-OFL.txt), no reserved font name |
| `Oxanium-Bold.ttf` | `text/outline_font`, `bindings/font`, `text/reels` | [Oxanium](https://github.com/sevmeyer/oxanium) | [OFL 1.1](text/outline_font/licenses/Oxanium-OFL.txt), no reserved font name; each show keeps its own copy of the license |
