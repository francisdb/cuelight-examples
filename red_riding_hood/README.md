# red_riding_hood

A picture book for children learning to read, on a 1280x720 canvas:
Little Red Riding Hood told in short lines of large type, an open book
on a wooden table, the story on the left page and a picture on the right.
The pictures never stand quite still: grass and flowers sway, the girl's
head bobs, smoke rises, a bird hops on the roof, the wolf blinks and wags
its tail.

One word on every page is printed red, and it makes the picture do
something: the girl twirls in her red hood, the basket swings, the wolf
hops, the flowers bob, Grandma peeks out of the cupboard, the wolf's eyes
grow and it shows its teeth, the candles on the cake flare up. Pressing
the word does it, and the driver plays the words too.

| Part | How it works |
| --- | --- |
| Pages | every spread is a scene (`cover`, `page_1` ... `page_8`), entered by its trigger. The table, the cover boards and the edges of the pages are the show's own layers and stay put; everything printed on the pages belongs to the scene |
| Page turn | entering a scene plays it: a blank leaf over the right page turns on the spine (`scale_x` from 1 to -1), shading as it lifts, lands on the left page and fades into the new text, which only appears then. The sound of a page turning plays with it, one of two takes in turn (`pick`) |
| Paper | one PNG multiplied over both pages and the turning leaf: grain, darker edges, foxing and a deep crease where the pages bend into the binding, so the ink and the pictures look printed on it |
| Story | IM Fell English at 40 pixels, a line per layer; a page that starts with a letter gets a red initial in IM Fell French Canon, with the first two lines indented beside it |
| Red words | the lines are laid out by the script, word by word, with the font's advance widths, which is how the engine places glyphs, so each red word is a text layer of its own at a known place. It is anchored at its centre and jumps when its trigger fires; a press on it fires the same trigger (`press`) |
| Pictures | a group clipped to the plate, drawn from SVG parts in a few flat inks with a dark outline. A part that moves is its own file, drawn so that the point it turns around is on its box's edge: a head turns at its neck (`anchor: bottom`), a basket swings from its handle (`top`), the wolf's jaw opens at its hinge (`top_right`), a tail wags from its root (`left`), a flower sways from its stem |
| Idle motion | looping timelines, each with its own period and delay, so nothing moves in step with anything else |
| Characters | the girl, the wolf and the wolf's head are groups of parts built by one function each and reused on every page: the wolf in Grandma's bed is the same head, mirrored, with a nightcap over its ears |

## Running

```sh
cd ../../cuelight
cargo run -p cuelight-player -- ../cuelight-examples/red_riding_hood
```

`test-driver.json` is picked up automatically and reads the book: the
cover, then every page for nine seconds, firing the page's red word
halfway. Click a red word to fire it yourself. Turn to a page from the
player's prompt with `page_6`.

The show, the driver and the artwork are written by
[`tools/red_riding_hood_show.py`](../tools/red_riding_hood_show.py) and
[`tools/red_riding_hood_art.py`](../tools/red_riding_hood_art.py); the
page turns by
[`tools/red_riding_hood_sounds.py`](../tools/red_riding_hood_sounds.py);
the fonts are fetched by
[`tools/red_riding_hood_fetch.sh`](../tools/red_riding_hood_fetch.sh).

## Assets

Everything under `assets/` is committed and free to redistribute. Licenses
were checked at the linked sources on 2026-09-24; the license texts that
have to travel with the files are in [`licenses/`](licenses/).

| Asset | Origin | License |
| --- | --- | --- |
| `*.svg`, `table.png`, `paper.png` | Made for this show, written by [`tools/red_riding_hood_art.py`](../tools/red_riding_hood_art.py) | MIT, as this repository |
| `sounds/turn1.ogg`, `sounds/turn2.ogg` | Synthesized from noise by [`tools/red_riding_hood_sounds.py`](../tools/red_riding_hood_sounds.py) | MIT, as this repository |
| `fonts/IMFellEnglish-Regular.ttf`, `fonts/IMFellEnglish-Italic.ttf`, `fonts/IMFellFrenchCanon-Regular.ttf` | [IM Fell Types](https://iginomarini.com/fell/) by Igino Marini, revivals of the Fell types of the 1680s, the unmodified files from [google/fonts](https://github.com/google/fonts/tree/8d618a0e96499047423510abb2c5ee9f475b987a/ofl/imfellenglish) and [IM Fell French Canon](https://github.com/google/fonts/tree/3b3145a92153418d09d62971e8238ad5bec48ca3/ofl/imfellfrenchcanon) | [OFL-1.1](licenses/IMFell-OFL.txt), no reserved font name |

The story is the folk tale, retold for young readers; in this telling
Grandma hides in the cupboard and nobody gets eaten.

## What would make it better

- Turning the page by pressing its corner, and back with the other one.
- Reading along: narration whose sound carries a marker per word that
  fires a trigger, so each word lights up as it is read aloud.
- Transitions between scenes: the page turn is played by the new scene
  over its own content, so the old page cannot be seen turning away.
- Laying out text in the engine: to know where a word lands, the script
  measures the font itself, and a line with a red word in it is several
  layers.
- Styles and repeated layers (cuelight#99): every page repeats the same
  paper, frame, leaf and rustle, and the characters are copied onto every
  page they appear on.
