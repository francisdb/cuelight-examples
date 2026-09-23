# boardwalk

A backglass for a four-player electromechanical pinball machine of the
seventies, on a 960x720 canvas: one picture of a sunny pier painted on
glass, with the score reels looking through windows in arcade boards
along the boardwalk and every light of the game painted into the scene.
It is driven the way a Visual Pinball table drives its backglass: by the
same data a table script sends the B2S server.

## How the light works

A backglass is lit from behind, so the show builds the light first and
lays the painting over it:

| Part | How it works |
| --- | --- |
| The light behind the glass | a dim room light, a few large GI bulbs so the scene is lit a little unevenly with hotspots, and a mottle multiplied in, since paint is never laid on evenly |
| The glass | one picture multiplied over that light (`"blend": "multiply"`): the ink decides the colour and how much gets through, so the scene glows where lamps burn and stays dark ink elsewhere |
| Light boxes | everything that shows the state of the game sits in a box of its own, the shape of the thing itself (a sign, a wedge of the fortune wheel, a coaster car, the balloon, the banner): a path shape in the room's colour keeps the GI out, and a path shape lit with `add` lights it evenly, edge to edge, when its data says so |
| The title | the same, letter by letter: a mask the shape of the title keeps the GI off it, and each letter has a lamp of its own shape, so the name is spelled out as it is earned |
| Bulbs | the Ferris wheel and the marquee: a tail of light running round the wheel and a chase along the top in attract (looping timelines, each bulb started a little after its neighbour with a `delay`), and in a game the wheel's bulbs are the bonus, bulb k lit while the bonus is k or more (`threshold`) |
| The reels | a `digits` row with a `reel` display per player, stepping forward one digit per score pulse, with a small settle (`offset`); a shaded overlay makes each a drum |
| The front of the glass | a faint spill round lit boxes, a soft reflection, and dust, scratches and pinholes |
| Sound | the backbox's mechanics: a reel's clack on every pulse, three chimes for tens, hundreds and thousands, a coin, and the knocker for a replay |

It needs cuelight `main` with blend modes, path shapes, bindable
`visible` with `threshold`, reel rows, and sound with `pick`.

## Driving it

The variables are named after the B2S data ids a table script sets with
`B2SSetData id, value`, so a host passes them straight through:

| Variable | B2S | Lights |
| --- | --- | --- |
| `data_1` to `data_9` | `B2SSetData 1..9` | the letters of BOARDWALK spelled so far |
| `data_25` to `data_28` | `B2SSetScoreRolloverPlayer1..4` | 100,000 on a player's board |
| `data_30` | `B2SSetPlayerUp` | the player up (1 to 4) |
| `data_31` | `B2SSetCanPlay` | the number of players (1 to 4) |
| `data_32` | `B2SSetBallInPlay` | the ball in play (1 to 5), on the coaster cars |
| `data_33` | `B2SSetTilt` | tilt |
| `data_34` | `B2SSetMatch` | the match number, 100 for 00, on the fortune wheel |
| `data_35` | `B2SSetGameOver` | game over, and the attract chases |
| `data_36` | `B2SSetShootAgain` | shoot again |
| `data_40` | `B2SSetData 40` | the bonus, 0 to 16, on the Ferris wheel |
| `data_41` | `B2SSetData 41` | special |
| `score_1` to `score_4`, `credits` | `B2SSetScorePlayer`, `B2SSetCredits` | the reels, as digits padded with zeros |

Triggers: `chime_10`, `chime_100` and `chime_1000` for a score pulse
(the reel clacks with it), `reel_step` for a reel moving without a chime,
`start` (the lamps dip as the relays pull in), and `knocker`.

## Running

```sh
cd ../../cuelight
cargo run -p cuelight-player -- ../cuelight-examples/boardwalk
```

`test-driver.json` is picked up automatically and plays a 73 second
loop: attract, two players starting, the reels resetting to zero, three
balls each with the title spelled out and the bonus collected bulb by
bulb, a shoot again, a tilt, a special for spelling BOARDWALK, and a
match. It is written out by
[`tools/boardwalk_game.py`](../tools/boardwalk_game.py) and starts from
the scores and credits it ends with, so the loop joins up.

## How it is made

Everything is generated:

- [`tools/boardwalk_layout.py`](../tools/boardwalk_layout.py): where
  everything sits, shared by the painting and the show, so each lamp is
  behind the part of the picture it lights.
- [`tools/boardwalk_art.py`](../tools/boardwalk_art.py): paints the glass
  in the manner of the late EM era, flat angular shapes with keylines a
  hair off register, saved in 96 colours with a dither for the grain of
  the print, and the silhouettes, bulb, mottle and wear images.
- [`tools/boardwalk_show.py`](../tools/boardwalk_show.py): writes
  `show.json` from the layout.
- [`tools/boardwalk_sounds.py`](../tools/boardwalk_sounds.py):
  synthesizes the chimes.
- [`tools/boardwalk_fetch.sh`](../tools/boardwalk_fetch.sh): fetches the
  font and the recorded sounds.

## Assets

Everything under `assets/` is committed and free to redistribute.

| Asset | Origin | License |
| --- | --- | --- |
| `glass.png`, `title_*.png`, `bulb.png`, `mottle.png`, `wear.png`, `reel_shade.png`, `sheen.png` | Made for this show by `tools/boardwalk_art.py`; the title is set in [Shrikhand](https://github.com/jonpinhorn/shrikhand) (OFL 1.1, no reserved font name), which the script only uses to paint | MIT, as this repository |
| `sounds/chime_*.ogg` | Made for this show by `tools/boardwalk_sounds.py` | MIT, as this repository |
| `sounds/clack1.ogg`, `sounds/coin.ogg` | [RPG Audio](https://kenney.nl/assets/rpg-audio) by Kenney | [CC0](licenses/Kenney-RPG-Audio-CC0.txt) |
| `sounds/clack2.ogg`, `sounds/knocker.ogg` | [Impact Sounds](https://kenney.nl/assets/impact-sounds) by Kenney | [CC0](licenses/Kenney-Impact-Sounds-CC0.txt) |
| `fonts/LeagueGothic-Regular.ttf` | [League Gothic](https://github.com/theleagueof/league-gothic), the normal width cut from the variable font and trimmed to Latin-1 by `tools/boardwalk_fetch.sh` | [OFL 1.1](licenses/LeagueGothic-OFL.txt), no reserved font name |

## What would make it better

- Incandescent lamps (cuelight #95). A lamp here fades in and out in the
  same 80 ms and stays the same colour; a real bulb warms up faster than
  it cools and glows redder while dim.
- Formatting a number with leading zeros. A reel shows every digit, so
  the scores have to arrive padded (`"01740"`); a host passing on
  `B2SSetScorePlayer` has to pad them itself.
- A tone curve on light. Lit ink can only be multiplied by the light
  behind it, so the levels are kept below full to avoid clipping; a
  gentle roll-off would let the brightest lamps saturate the way lit
  paint does.
