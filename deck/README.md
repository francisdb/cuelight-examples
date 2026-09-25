# deck

A slide deck about cuelight, made in cuelight, on a 1280x720 canvas: when
you would reach for it, why describing a show beats programming one,
why the same inputs give the same frames, playing live and scrubbing,
rendering to frames and video, and events driving motion. Every slide
shows its point instead of only saying it.

| Slide | What it shows |
| --- | --- |
| Title | the wordmark, and four shapes popping in and swinging (`back_out`, looping timelines with their own periods) |
| Where it fits | six shows from the gallery, each a thumbnail cut to its card by a group `clip` |
| Describe it | the JSON of a fuel bar beside the bar itself: the deck plays a host setting `fuel`, the bar springs to it through a `transition` and the readout counts. Set `fuel` yourself and the host takes over from the deck |
| Same inputs, same frames | a marker jumps about a time axis; a second copy of the scene is kept at t = 2.8, and when the live one comes back to 2.8 the two are the same picture |
| Scrub | one time value plays, rewinds and drags, and a scene whose every property is bound to it through `curve`s follows, backwards as readily as forwards |
| Render | the render commands typing themselves out, with what `--events` really prints for this deck, beside a film strip of the scene at every half second |
| Events | a program sends `coin`, `credits` and `jackpot` along a wire; the show drops a coin, counts the credits and bursts, with sound |
| For makers | animators, explainer makers and game designers; the easing plot is `bounce_out`, traced by a dot eased with it |
| Try it | where to find the gallery and the engine |

| Part | How it works |
| --- | --- |
| Slides | a scene each, `slide_1` to `slide_9`. Every element enters by a held timeline with its own `delay`, so a slide builds itself |
| Navigation | the host sends `next` and `prev`. Each slide routes them: a timeline of no length whose `on_end` fires the slide before or after it, so keys or a click map straight onto two events |
| Code | each line is SVG artwork drawn from DM Mono's glyph outlines, coloured per token, one `vector` layer a line (until SVG text can use the show's own fonts, cuelight#203) |
| Chrome | the progress bar grows from the previous slide's share to this one's; the page number and the wordmark sit on every slide |

## Driving it

The host sends `next` and `prev`, and `slide_1` to go back to the start.
The events slide also listens for `coin` and `jackpot`, and reads the
`credits` variable.

## Running

```sh
cd ../../cuelight
cargo run -p cuelight-player -- ../cuelight-examples/deck
```

`test-driver.json` is picked up automatically and reads the deck in 82
seconds with `next`, firing a few coins and a jackpot on the events slide.

Rendered to a video, as its own render slide says:

```sh
cuelight-render deck/ --every 0.04 --until 82 -o frames/
ffmpeg -framerate 25 -pattern_type glob -i 'frames/*.png' deck.mp4
```

The show, the driver and the code artwork are written by
[`tools/deck_show.py`](../tools/deck_show.py), the sounds by
[`tools/deck_sounds.py`](../tools/deck_sounds.py), and the fonts are
fetched by [`tools/deck_fetch.sh`](../tools/deck_fetch.sh).

## Assets

| Asset | Origin | License |
| --- | --- | --- |
| `code_*.svg`, `film.svg` | Drawn by `tools/deck_show.py`, the code from DM Mono's outlines | MIT, as this repository |
| `sounds/*.ogg` | Synthesized from sines by `tools/deck_sounds.py` | MIT, as this repository |
| `game_hud.png` and the other thumbnails | This repository's gallery thumbnails, rendered from its shows | MIT, as this repository |
| `fonts/ArchivoBlack-Regular.ttf` | [Archivo Black](https://github.com/Omnibus-Type/ArchivoBlack), from google/fonts | [OFL-1.1](licenses/ArchivoBlack-OFL.txt) |
| `fonts/AtkinsonHyperlegible-*.ttf` | [Atkinson Hyperlegible](https://www.brailleinstitute.org/freefont/) by the Braille Institute, from google/fonts | [OFL-1.1](licenses/AtkinsonHyperlegible-OFL.txt) |
| `fonts/DMMono-*.ttf` | [DM Mono](https://github.com/googlefonts/dm-mono), from google/fonts | [OFL-1.1](licenses/DMMono-OFL.txt) |
