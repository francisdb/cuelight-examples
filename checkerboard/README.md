# checkerboard

A checkerboard on a 960x540 canvas that turns and breathes endlessly
behind a chess piece that does not move at all. Two copies of the same
board rotate against each other at different rates, and the host decides
how close the camera is.

| Part | How it works |
| --- | --- |
| The board | one `vector` of a 16 by 16 board, 1600 units across, drawn twice. It is wider than the canvas's diagonal, so however far it turns or zooms out there is no corner to see past |
| Turning | each copy carries a looping `rotation` timeline, one going 0 to 90 degrees over 23 seconds and the other 90 to 0 over 37. A quarter turn maps a checkerboard onto itself, so those loops have no seam, and the two periods do not divide each other, so the pair never quite repeats |
| Breathing | the near copy also loops its own `scale` between 1 and 1.35, which multiplies with everything above it |
| The second board | drawn over the first with `"blend": "multiply"` and a bound opacity, so it darkens the light squares and leaves the dark ones alone. The two boards cut triangles out of each other as they turn |
| The zoom | the group around both loops its own `scale` between 0.85 and 1.45 over 29 seconds, a period none of the turns divides, so the camera never arrives anywhere twice the same way. A group's transform reaches its whole subtree, so that one timeline scales two boards that are separately rotating and scaling |
| Two copies of the zoom | the shadow lies on the boards, so it has to breathe with them, and it carries a second timeline with the same keys. **They have to stay identical.** A show cannot name a value and have several layers read it, and the shadow cannot simply live inside the boards' group, since a group scales positions too and the shadow would slide off the piece. They keep together only because both start at load (cuelight #74) |
| The piece | a `vector` in front, still, apart from a slow float |
| Its shadow | the same outline again as one flat dark shape, squashed with `scale_y` and turned, lying on the board rather than under the piece. It grows and shrinks with the squares it falls across while the piece itself never changes size |
| The corners | a stretched image, since a show has no gradients: the alternative is a stack of translucent shapes, and one small picture is cheaper and softer |

It needs cuelight `main` with rotation, uneven scale, inherited group
transforms, blend modes and vector artwork.

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
| `board.svg`, `knight.svg`, `shadow.svg`, `vignette.png` | Made for this show, drawn by [`tools/checkerboard_art.py`](../tools/checkerboard_art.py) | MIT, as this repository |

## What would make it better

- A way to tile a pattern. The board is 128 rectangles written out one by
  one, because a show cannot say "this square, repeated". A tiling fill,
  or a layer that repeats its child on a grid, would make it four lines
  and would serve star fields and backgrounds as well.
- Gradients in shapes, so the corners would not need an image.
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
- A value the show can name and animate, that several layers read the way
  they read a variable (cuelight #74). The zoom is one value with two
  readers, and it has to be written twice because there is no way to say
  so. Nothing in the document records that the two sets of keys are meant
  to agree; they do because both start at load.
