# flexdemo

A port of [FlexDemo](https://github.com/vbousquet/flexdmd/tree/master/FlexDemo),
FlexDMD's own demo table, covering everything its DMD script does: six
switchable scenes on a 128x32 DMD.

| Scene | What it shows |
| --- | --- |
| `welcome` | Title, two-line info text, blinking `<` `>` arrows |
| `stern` | Four player scores (active one highlighted), separator line, clipped content area with a scrolling title |
| `williams` | Four corner scores, active player in a big font |
| `colors` | Full-color mode: bordered title over an 8-frame lightning flipbook |
| `graveyard` | Video mode: parallax scrolling, sprite-sheet runner that jumps, falls and dies |
| `alphanum` | 2x16 alphanumeric segment display |

Everything the show uses is in cuelight `main` except segment displays
(the `alphanum` scene), which are still in progress: until they land the
show fails to load with `unknown variant segments`. Remove that scene to
play the other five.

## Running

The assets are not committed (the bitmap font licenses forbid
redistribution, see [Assets](#assets)); fetch them first:

```sh
./fetch-assets.sh        # needs curl and vpxtool
cd ../../cuelight
cargo run --example player -- ../cuelight-examples/flexdemo
```

`test-driver.json` is picked up automatically. It stands in for the table
script: it walks through all scenes (the Magna Save buttons), rotates the
active player and posts scores, and plays the video mode with three jumps, a
death and a fall.

## Assets

Nothing below is committed; `fetch-assets.sh` downloads it from the
[FlexDMD repository](https://github.com/vbousquet/flexdmd) (Apache-2.0) at
commit `6357c18`. Every asset keeps its original license:

| Asset | Origin | License |
| --- | --- | --- |
| `gy_girl.png` | [Adventurer Girl](https://opengameart.org/content/adventurer-girl-free-sprite) by GameArt2D, packed into a sprite sheet for [FlexDemo](https://github.com/vbousquet/flexdmd/tree/master/FlexDemo) | CC0 |
| `gy_background.png`, `gy_graveyard.png` | [Free Graveyard Platformer Tileset](https://www.gameart2d.com/free-graveyard-platformer-tileset.html) by GameArt2D, composed for [FlexDemo](https://github.com/vbousquet/flexdmd/tree/master/FlexDemo) | CC0 |
| `lightning.png` | [FlexDemo](https://github.com/vbousquet/flexdmd/tree/master/FlexDemo) table | Apache-2.0 (as the FlexDMD repository; no separate credit given) |
| `fonts/teeny_tiny_pixls-5.*` | Teeny Tiny Pixls by Chequered Ink, [bitmap version from FlexDMD](https://github.com/vbousquet/flexdmd/tree/master/FlexDMD/Resources) | Free for all use, but the font file may not be redistributed without permission ([license](https://github.com/vbousquet/flexdmd/blob/master/FlexDMD/Fonts/TTF%20Fonts/5px%20-%20teeny_tiny_pixls/License.txt)) |
| `fonts/bm_army-12.*` | BM army by BitmapMania, [bitmap version from FlexDMD](https://github.com/vbousquet/flexdmd/tree/master/FlexDMD/Resources) | Freeware, no sale or bundling with commercial products ([read me](https://github.com/vbousquet/flexdmd/blob/master/FlexDMD/Fonts/TTF%20Fonts/12px%20-%20bm_army/read%20me.txt)) |
| `fonts/udmd-f7by13.*` | UltraDMD font, [bitmap version from FlexDMD](https://github.com/vbousquet/flexdmd/tree/master/FlexDMD/Resources) | Not stated |

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
- [ ] **Segment displays** (in progress): `type: "segments"`, `style: "alpha14"`, `digits`, `text`.
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
| second FlexDMD in `SEG_2x16Alpha` mode | `segments` layers |
| `label.Font = ...` on the active player | mapped `font` binding |
| `label.Text = FormatNumber(...)` | `text` binding, `thousands` format |
| `CreateGraveyardVideoMode()` after fall/die | `on_end: "graveyard"` |
| `DMDTimer` game logic (random scores, player rotation, hole/jump collisions) | host side: the test driver scripts it |

Deliberate differences from the original:

- `Show(False)` becomes opacity 0 rather than a visibility toggle.
- The alphanumeric display is drawn on the DMD canvas; the original shows it on a separate segment display and hides the DMD (whose labels are left out here).
- Collision detection is not simulated; the driver fires `jump`, `fall` and `die` at times matching the scroll position of the holes and gravestones.
