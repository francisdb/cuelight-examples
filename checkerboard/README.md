# checkerboard

A checkerboard on a 960x540 canvas that turns and breathes endlessly
behind a chess piece that does not move at all. Two copies of the same
board rotate against each other at different rates, and the host decides
how close the camera is.

| Part | How it works |
| --- | --- |
| The board | a two-by-two SVG tile repeated across 1700 units (`repeat`), 17 squares a side, drawn twice. It is wider than the canvas's diagonal, so however far it turns or zooms out there is no corner to see past, and being vector artwork its squares stay sharp at every zoom |
| Turning | each copy carries a looping `rotation` timeline, one going 0 to 90 degrees over 23 seconds and the other 90 to 0 over 37. A quarter turn maps a checkerboard onto itself, so those loops have no seam, and the two periods do not divide each other, so the pair never quite repeats |
| Breathing | the near copy also loops its own `scale` between 1 and 1.35, which multiplies with everything above it |
| The second board | drawn over the first with `"blend": "multiply"` and a bound opacity, so it darkens the light squares and leaves the dark ones alone. The two boards cut triangles out of each other as they turn |
| The zoom | one value of the show's own, `zoom`, loops between 0.85 and 1.45 over 29 seconds, a period none of the turns divides, so the camera never arrives anywhere twice the same way. The group around both boards binds its `scale` to it, and a group's transform reaches its whole subtree, so that one value scales two boards that are separately rotating and scaling |
| The shadow | lies on the boards, so it breathes with them: it binds its `scale` to the same `zoom`. It cannot simply live inside the boards' group, since a group scales positions too and the shadow would slide off the piece |
| The piece | a `vector` in front, still, apart from a slow float |
| Its shadow | the same outline again as one flat dark shape, squashed with `scale_y` and turned, lying on the board rather than under the piece. It grows and shrinks with the squares it falls across while the piece itself never changes size |
| The corners | a square filled with a radial gradient from clear to dark, squashed to the canvas with `scale_y`, so the dark follows an ellipse into the corners. It and the board reach past the canvas (`overflow`): the board was already drawn far larger than the canvas, and the vignette, four canvases wide, holds its darkest colour past its edge, so a screen of another shape shows the board fading into the dark instead of flat bars |

It needs cuelight `main` with rotation, uneven scale, inherited group
transforms, blend modes and tiled vector artwork.

## Running

```sh
cd ../../cuelight
cargo run -p cuelight-player -- ../cuelight-examples/checkerboard
```

`test-driver.json` is picked up automatically and only fades the second
board in and out. Everything else, the turning, the breathing and the
camera, runs on its own, so the show plays exactly the same with
`--no-driver`. You can also set it from the player's prompt: `depth=0.8`.

## Assets

Everything under `assets/` is committed and free to redistribute.

| Asset | Origin | License |
| --- | --- | --- |
| `checker.svg`, `knight.svg`, `shadow.svg` | Made for this show, drawn by [`tools/checkerboard_art.py`](../tools/checkerboard_art.py) | MIT, as this repository |

## What would make it better

- Perspective, so the board could lie flat and recede instead of facing
  the viewer. Rotation and scale are affine, so the board can only spin
  in its own plane.
- A shear. A shadow thrown across a surface is sheared, not merely
  squashed and turned, and a shear is affine like the transforms that are
  already there.
- A rate rather than a loop: the turning is authored as a keyframe at 23
  seconds because a looping timeline restarts from its first key. Saying
  "90 degrees every 23 seconds" would be plainer, and a host could then
  change the speed.
