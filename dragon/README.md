# dragon

A backglass for a four-player solid-state pinball machine of around
1980, on a 1000x900 canvas: Hokusai's *Dragon* fills the glass, the
scores show on 7-segment displays in black windows cut into it, and
lamps behind the glass light parts of the dragon and the words painted
on it.

## How the light works

| Part | How it works |
| --- | --- |
| The glass | the painting, dimmed by a black layer bound to `gi`: the general illumination brings the picture up while the machine is on, and a tilt takes it away |
| Feature lamps | the eyes, the head, the four claws and the tail: a soft warm pool that brightens the picture (`"blend": "screen"`) and a bulb's glow on top (`add`), both through the `incandescent` transition, so a lamp comes up fast and dies away slowly; both eyes are one lamp |
| Attract | a looping value steps round the features one after another, then flashes them all twice |
| Lettering | GAME OVER, TILT, MATCH, SAME PLAYER SHOOTS AGAIN, HIGH SCORE TO DATE and the player-up numbers are painted on the art with no frame: dark ink that barely shows until its lamp lights the letters and a halo round them |
| Displays | `digits` with a `numeric7` segment display: four 7-digit scores, and 2-digit credits and ball in play |

## Driving it

What the game sets:

| Variable | Shows |
| --- | --- |
| `game_running` | a game is on; off, GAME OVER lights and the attract show runs |
| `gi` | the general illumination |
| `players`, `player` | how many play, and whose turn it is, 1 to 4 |
| `ball`, `credits` | the small displays; `ball` shows the match number after a game |
| `score_1` to `score_4` | the scores, empty for a player not in the game |
| `eye`, `head`, `claw_1` to `claw_4`, `tail` | the feature lamps |
| `tilt`, `shoot_again`, `match_lit`, `high_score` | the lettering lamps |

## Running

```sh
cd ../../cuelight
cargo run -p cuelight-player -- ../cuelight-examples/dragon
```

`test-driver.json` is picked up automatically and plays a 52 second
loop: attract, then two players with feature lamps lit, a tilt, a shoot
again, and game over with a match.

## Assets

Everything is made by `tools/dragon_fetch.sh`, which fetches the font
and runs `tools/dragon_art.py`; `tools/dragon_show.py` writes
`show.json` and `test-driver.json`.

- `assets/dragon.png`: *Dragon* by Katsushika Hokusai, public domain,
  from Wikimedia Commons, brought down to 1000 pixels and 128 colours
  (see `licenses/Hokusai-Dragon.txt`).
- `assets/fonts/DelaGothicOne-Regular.ttf`: Dela Gothic One, SIL Open
  Font License 1.1, cut to Latin.
- `assets/glow.png`: a generated white glow.
