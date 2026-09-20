# space_crawl

A film-style opening crawl on a 1280x720 canvas, in one scene: a line of
blue text fades in and out over a star field, the logo falls away into the
distance, then yellow text crawls up the screen and shrinks towards a
vanishing point.

cuelight has no perspective transform, so the crawl fakes one. Every line
is its own text layer with a `y`, a `scale` and an `opacity` track, started
one after the other with `delay`. The logo is an image doing the same with
`scale` around a `center` anchor. `show.json` is generated:
[`tools/space_crawl.py`](../tools/space_crawl.py) holds the text, the
timing and the depth curve, and explains the math.

## Running

```sh
cd ../../cuelight
cargo run --example player -- ../cuelight-examples/space_crawl
```

`test-driver.json` is picked up automatically and restarts the crawl when
it is over; entering the scene again restarts its timelines.

To change the text or the timing, edit the constants in the script and
regenerate:

```sh
tools/space_crawl.py space_crawl
```

That rewrites `show.json`, `test-driver.json` and the stars; the logo is
only redrawn with `--logo-font ArchivoBlack-Regular.ttf`.

## Assets

Everything under `assets/` is committed and free to redistribute. Licenses
were checked at the linked sources on 2026-09-20; the license texts that
have to travel with the files are in [`licenses/`](licenses/).

| Asset | Origin | License |
| --- | --- | --- |
| `fonts/libre_franklin_bold-56.*` | [Libre Franklin](https://github.com/googlefonts/Libre-Franklin) by The Libre Franklin Project Authors, `LibreFranklin[wght].ttf` from [Google Fonts](https://github.com/google/fonts/tree/e2332cf862ac3145c0ee5f24f04f4c1819b2410b/ofl/librefranklin) rasterized at weight 700, 56px, antialiased, with [`tools/ttf2bmfont.py`](../tools/ttf2bmfont.py) | [OFL-1.1](licenses/LibreFranklin-OFL.txt), no reserved font name |
| `logo.png` | Made for this show, drawn by [`tools/space_crawl.py`](../tools/space_crawl.py) with [Archivo Black](https://github.com/Omnibus-Type/ArchivoBlack) from [Google Fonts](https://github.com/google/fonts/tree/94a7d81318e438525a5285e07ab72c050fdfeb44/ofl/archivoblack) (OFL-1.1, which leaves images made with a font alone) | MIT, as this repository |
| `stars.png` | Made for this show, drawn by [`tools/space_crawl.py`](../tools/space_crawl.py) | MIT, as this repository |

The texts are this show's own.

## What would make it better

- A perspective (or at least non-uniform scale) transform: real
  perspective also squashes distant lines vertically. With a uniform
  scale they would overlap, so the depth curve is flattened instead and
  the edges of the text block are slightly curved.
- Outline fonts: the text is a 56px bitmap that is only ever scaled
  down, which holds up at 720p but not on a much larger canvas.
- Justified text, which the original style uses.
