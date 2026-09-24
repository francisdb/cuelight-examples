# eclipse

A total solar eclipse explained on a 1280x720 page: on the left the sky as
an observer sees it, darkening into totality; on the right a side view of
the sun, the moon and the shadow crossing the Earth, the four contacts on a
track, how much sunlight is left, and a caption for every phase.

There is no driver. The show plays itself, in a loop of about 51 seconds.

## How it drives itself

The moon is the clock. Its journey across the sun is a chain of timelines
on the `moon` layer, one per stretch between two contacts, and each one's
`on_end` fires the next contact as a trigger:

```text
(scene start) -> c1 -> beads -> c2 -> c3 -> emerged -> c4 -> cycle
```

Everything else listens to those names, in one of two ways:

| Kind | How it works |
| --- | --- |
| Follows the moon | The moon's disc, the sky's darkness, the sun's glare, the side diagram, the progress dot and the sunlight bar change continuously with how far the moon is from the sun. Each has one timeline per stretch, started by the same trigger as the moon's and as long as it, so they all start each stretch together. The keys come from the moon's distance: the covered share of the sun is the overlap of two circles, the sky only darkens in the last few per cent, and the shadow's place in the diagram follows the distance |
| Reacts to a contact | Captions, the corona, the stars and Venus, the beads and the diamond ring, and the contact marks only know the cue that starts them and the cue that ends them, with an optional `delay`. A fade-in timeline holds its value far longer than any stretch; a fade-out timeline, started later by the ending cue, wins because a timeline started later owns the property. Nothing here depends on how long a stretch lasts |

Everything sits in one scene whose trigger is `cycle`. The last stretch's
`on_end` fires it, re-entering the scene stops every held timeline, and the
loop starts clean.

| Part | How it works |
| --- | --- |
| Sky | a rect filled with a day gradient, and one with a totality gradient over it whose opacity follows the moon; the horizon glows orange all around during totality, and the sun's glare and the diamond ring are radial gradients |
| Moon | a dark disc inside a group clipped to the sun, so it only shows where it covers it. Outside the sun, a faint outline marks where the new moon is, and a silhouette appears around totality, against the corona |
| Corona | one PNG, drawn with `screen`, faint from the beads on and full at second contact. Pink prominences sit just past the limb: the moon is a little larger than the sun, so they show at the side it is leaving |
| Beads and diamond ring | a few small discs on the limb that flicker out one by one, then a glare and a flare, on the left before totality and on the right after it |
| Callouts | during totality the corona and the prominences are labelled, each a text and a leader line in a group that fades in on `c2` with its own `delay` and out on `c3` |
| Side view | the moon rides on its orbit, drawn as a grey circle around the Earth: a group turning around the Earth's centre carries it, and the moon's own group inside turns its two shadow cones to point away from the sun. The script solves where on the orbit the moon must be for its shadow to land where the sky view says. The cones are clipped to the space in front of the Earth; the same cones, moved the same way and clipped to the Earth's disc, show where the shadow falls on it |

## Running

```sh
cd ../../cuelight
cargo run -p cuelight-player -- ../cuelight-examples/eclipse
```

`show.json` is written by [`tools/eclipse_show.py`](../tools/eclipse_show.py),
where the stretches, the geometry and the captions are defined in one
place; the artwork by [`tools/eclipse_art.py`](../tools/eclipse_art.py).

## Assets

Everything under `assets/` is committed and free to redistribute. Licenses
were checked at the linked sources on 2026-09-24; the license texts that
have to travel with the files are in [`licenses/`](licenses/).

| Asset | Origin | License |
| --- | --- | --- |
| `corona.png` | Made for this show, written by [`tools/eclipse_art.py`](../tools/eclipse_art.py) | MIT, as this repository |
| `fonts/Spectral-Regular.ttf`, `fonts/Spectral-Italic.ttf`, `fonts/Spectral-SemiBold.ttf`, `fonts/SpectralSC-SemiBold.ttf` | [Spectral](https://github.com/productiontype/Spectral) by Production Type, the unmodified static files from [google/fonts](https://github.com/google/fonts/tree/8b0a1d0f5983c89bc2b93f1b5fb55f9e252744b5/ofl/spectral) | [OFL-1.1](licenses/Spectral-OFL.txt), no reserved font name |

## What would make it better

- A value of the show's own, animated by keys and read by bindings
  (cuelight #74). The moon's distance to the sun is the one number
  everything that moves depends on, but a timeline can only animate its
  own layer, so each of those layers repeats the moon's stretches with
  keys computed by the script. With a named value started by the same
  triggers, one value would move and everything else would bind to it.
- A binding that maps a number through a curve, not only `scale` and
  `offset` (cuelight #109): how much of the sun is covered, and how
  dark the sky gets, are not straight lines in the distance.
- Timeline `hold` (cuelight #88): the fade-ins hold with a key ten minutes
  away so they outlast any stretch.
