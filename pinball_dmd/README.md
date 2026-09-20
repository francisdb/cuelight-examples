# pinball_dmd

A pinball dot-matrix display: six switchable scenes on a 128x32 DMD. It
started as a port of
[FlexDemo](https://github.com/vbousquet/flexdmd/tree/master/FlexDemo),
FlexDMD's own demo table, and covers everything its DMD script does.

| Scene | What it shows |
| --- | --- |
| `welcome` | Title, two-line info text, blinking `<` `>` arrows |
| `stern` | Four player scores (active one highlighted), separator line, clipped content area with a scrolling title |
| `williams` | Four corner scores, active player in a big font |
| `colors` | Full-color mode: bordered title over an 8-frame lightning flipbook |
| `graveyard` | Video mode: parallax scrolling, sprite-sheet runner that jumps, falls and dies |
| `alphanum` | 2x16 alphanumeric segment display |

Everything the show uses is in cuelight `main`.

## Running

```sh
cd ../../cuelight
cargo run --example player -- ../cuelight-examples/pinball_dmd
```

`test-driver.json` is picked up automatically. It stands in for the table
script: it walks through all scenes (the Magna Save buttons), rotates the
active player and posts scores, and plays the video mode with three jumps, a
death and a fall.

## Assets

Everything under `assets/` is committed and free to redistribute. Licenses
were checked at the linked sources on 2026-09-20; the license texts that
have to travel with the files are in [`licenses/`](licenses/).

| Asset | Origin | License |
| --- | --- | --- |
| `fonts/tiny5-8.*` | [Tiny5](https://github.com/Gissio/font_tiny5) by The Tiny5 Project Authors, `Tiny5-Regular.ttf` from [Google Fonts](https://github.com/google/fonts/tree/b2723573ff4dd21b37158d1d549269e21a559df9/ofl/tiny5) rasterized at 8px with [`tools/ttf2bmfont.py`](../tools/ttf2bmfont.py) | [OFL-1.1](licenses/Tiny5-OFL.txt), no reserved font name |
| `fonts/jersey20-20.*` | [Jersey 20](https://github.com/scfried/soft-type-jersey) by The Soft Type Project Authors, `Jersey20-Regular.ttf` from [Google Fonts](https://github.com/google/fonts/tree/064d437c73364b35a95e42bad4621e25c8014e1e/ofl/jersey20) rasterized at 20px with [`tools/ttf2bmfont.py`](../tools/ttf2bmfont.py) | [OFL-1.1](licenses/Jersey20-OFL.txt), no reserved font name |
| `lightning.png` | Made for this show, drawn by [`tools/pinball_dmd_lightning.py`](../tools/pinball_dmd_lightning.py) | MIT, as this repository |
| `gy_girl.png` | [Adventurer Girl](https://opengameart.org/content/adventurer-girl-free-sprite) by pzUH (GameArt2D), scaled down and packed into a sprite sheet for [FlexDemo](https://github.com/vbousquet/flexdmd/tree/master/FlexDemo) | CC0-1.0; the FlexDMD repository the sheet was taken from is Apache-2.0 |
| `gy_background.png`, `gy_graveyard.png` | [Free Graveyard Platformer Tileset](https://www.gameart2d.com/free-graveyard-platformer-tileset.html) by GameArt2D ([freebies license](https://www.gameart2d.com/license.html)), composed for [FlexDemo](https://github.com/vbousquet/flexdmd/tree/master/FlexDemo) | CC0-1.0; the FlexDMD repository the images were taken from is Apache-2.0 |

The `gy_*` images were extracted from `FlexDemo/FlexDemo.vpx` at FlexDMD
commit `6357c18` with [vpxtool](https://github.com/francisdb/vpxtool).

The bitmap fonts are modified versions in OFL terms (a format conversion),
so they stay under the OFL; neither font reserves its name. A font with a
reserved name would have to be renamed.

## Implementation checklist

Every feature the show uses, and the cuelight PR that added it.

Engine / show format:

- [x] **Scenes** (cuelight #6): top-level `scenes`, each with a `trigger` that enters it; the first is active at load; entering a scene restarts its autoplay timelines (FlexDMD rebuilds the scene each time).
- [x] **Text layers with bitmap fonts** (cuelight #8): `type: "text"`, multi-line `text`; a top-level `fonts` table of styles (BMFont file, `color`, optional `border`). With `size` the text is aligned inside that box, centered by default (FlexDMD `SetBounds`).
- [x] **Text bindings** (cuelight #8): `{ "property": "text", "variable": ..., "format": "thousands" }` (FlexDMD script uses `FormatNumber`).
- [x] **Anchor** (cuelight #11): optional `anchor` (`top_left`, `top`, `top_right`, `left`, `center`, `right`, `bottom_left`, `bottom`, `bottom_right`) places that point of the layer's box at x/y (FlexDMD `SetAlignedPosition`). Also replaces the beacon show's counter-animation workaround.
- [x] **Mapped bindings** (cuelight #9): `map` + `default` pick a value by variable, used to swap the active player's font.
- [x] **Group clipping** (cuelight #12): `clip: { "rect": [x, y, w, h] }` on a group.
- [x] **Sprite sheets** (cuelight #13): `sheet: { cell, columns }` on an image plus an animatable/bindable `frame` property (floored, clamped).
- [x] **Timeline `delay`, `repeat`, `on_end`** (cuelight #14): a start offset that a `loop` does not repeat, a (fractional) play count, and a trigger fired at the end (restart the video mode after a fall).
- [x] **Output modes** (cuelight #7): show or scene `output: { "mode": "gray4", "tint": ... }` or `"rgb"` (FlexDMD `RenderMode` plus `DotMatrix.color`).
- [x] **Segment displays** (cuelight #17): `type: "digits"` rows with a `segments` display (`alpha14`).
- [x] **Pixel-perfect scaling** (cuelight #16): show-level `output: { "scaling": "pixel_perfect" }`, nearest-neighbor whole-number scaling of the canvas; scenes only override the output fields they set.

Host / player:

- [x] Load `assets/fonts/*.fnt` (BMFont text format plus page PNG) and register them with the engine (cuelight #8).
- [x] Accept 16-bit PNGs, `gy_girl.png` is one (cuelight #15).
- [x] List scene triggers in the player's action menu (cuelight #6).

## Mapping from the FlexDemo script

| FlexDMD script | Show |
| --- | --- |
| `NewGroup` + `Stage.RemoveAll` / `AddActor` | a scene, entered by its trigger |
| `NewLabel` + `NewFont(file, tint, borderTint, borderSize)` | text layer + `fonts` entry |
| `SetBounds` on a label | x/y + `size` |
| `SetAlignedPosition(x, y, align)` | x/y + `anchor` |
| `NewFrame` (1px separator) | rect shape |
| `Group.Clip` | `clip` |
| `NewImage("VPX.img&region=...")` frames | one image with `sheet` + `frame` timeline |
| `Show(True/False)` + `Wait` sequences | `opacity` keys with `step` ease |
| `MoveTo(x, y, duration)` | x/y keys |
| `Sequence(Wait, Repeat(...))` | `delay` + `loop` |
| `RenderMode`, `DotMatrix.color` | scene `output` |
| second FlexDMD in `SEG_2x16Alpha` mode | `digits` layers with a `segments` display |
| `label.Font = ...` on the active player | mapped `font` binding |
| `label.Text = FormatNumber(...)` | `text` binding, `thousands` format |
| `CreateGraveyardVideoMode()` after fall/die | `on_end: "graveyard"` |
| `DMDTimer` game logic (random scores, player rotation, hole/jump collisions) | host side: the test driver scripts it |

Deliberate differences from the original:

- Fonts, the lightning flipbook and the title texts are this show's own; FlexDemo's fonts are not free to redistribute and its lightning image has no stated origin.
- `Show(False)` becomes opacity 0 rather than a visibility toggle.
- The alphanumeric display is drawn on the DMD canvas; the original shows it on a separate segment display and hides the DMD (whose labels are left out here).
- Collision detection is not simulated; the driver fires `jump`, `fall` and `die` at times matching the scroll position of the holes and gravestones.
