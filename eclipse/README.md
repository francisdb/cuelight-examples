# eclipse

A total solar eclipse explained on a 1280x720 page: on the left the sky as
an observer sees it, darkening into totality; on the right a side view of
the sun, the moon and the shadow crossing the Earth, the four contacts on a
track, how much sunlight is left, and a caption for every phase.

There is no driver. The show plays itself, in a loop of about 51 seconds.

## How it drives itself

The moon is the clock. Its distance to the sun is a value of the show's
own (`values`), played as a chain of timelines, one per stretch between
two contacts, and each one's `on_end` fires the next contact as a
trigger:

```text
(scene start) -> c1 -> beads -> c2 -> c3 -> emerged -> c4 -> cycle
```

Everything else listens to those names, in one of two ways:

| Kind | How it works |
| --- | --- |
| Follows the moon | Bindings on `distance`, the one value the show animates. The moon and its disc read it as it is. The sky's darkness, the sun's glare, the sunlight left, the side diagram's two turns and the progress dot bend it through a `curve`, keys of distance against what they show: the covered share of the sun is the overlap of two circles, the sky only darkens in the last few per cent, and the shadow's place in the diagram follows the distance |
| Reacts to a contact | Captions, the corona, the stars and Venus, the beads and the diamond ring, and the contact marks only know the cue that starts them and the cue that ends them, with an optional `delay`. A fade-in timeline holds its last value when it ends (`hold`); a fade-out timeline, started later by the ending cue, holds too, and of two held timelines the one started later owns the property. Nothing here depends on how long a stretch lasts |

The layers sit in one scene whose trigger is `cycle`. The last stretch's
`on_end` fires it, re-entering the scene stops every held timeline, and the
loop starts clean. Values live outside scenes, so their first stretch
listens for `cycle` as well as starting at load.

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

- Styles with parameters and repeated layers (cuelight #99): the
  captions, the stars, the beads and the contact marks are near-identical
  blocks written out one by one, which is most of why the document is
  still written by a script.
