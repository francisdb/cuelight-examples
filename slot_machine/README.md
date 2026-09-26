# slot_machine

A fruit machine on a 960x600 canvas: three reels of drawn symbols that
spin whole turns and stop one after another, a payline, rolling credits,
and a cabinet that flashes when a line pays. The host plays the game; the
show only knows how to spin, land and celebrate.

| Part | How it works |
| --- | --- |
| The reels | three `digits` rows of one cell each, so every wheel moves on its own. Each is bound to its own variable and carries `cells` artwork, one SVG per character of its ring. All three take the `spin` trigger the host fires for the lever, so a wheel asked for the symbol it already carries still takes its turns instead of standing still |
| The ring | `charset` is `CLOPGBA7`, one character per symbol: cherry, lemon, orange, plum, grapes, bell, bar, seven. The charset stays the ring's identity, so the host says `reel_2 = B` and the wheel lands on the bell; the artwork only decides what that looks like |
| Spinning | `turns` of 6, 8 and 10 send each wheel that many times round before it lands, and `step` of `null` makes the whole trip one move, so the symbols fly past and the `quad_out` ease bleeds the speed off the way friction does. An `offset` carries each wheel an eighth of a symbol past its mark while it is still arriving and eases it back, which is the stop lever catching it just short of rest; the keys start before the move ends, so the wheel never stops and then hops |
| Staggered stops | nothing sequences them: the three wheels simply take 3.5, 4.0 and 4.5 seconds for the same change, so they settle left to right, each a full turn or more after the one before |
| The window | `window` of 3 shows the symbol above and below the one on the line, clipped to the cell, and a `drum` image over each window darkens the top and bottom so the strip looks wrapped rather than flat, the same trick as the drum in [`features/bindings/transitions`](../features/bindings/transitions) |
| The strip | the reel behind the symbols is the cream of a paper reel strip, and each symbol is one flat saturated colour under a heavy dark outline with a single highlight, which is what printing on such a strip allowed |
| Credits and win | `reel` rows again, this time drawn in a font, so the figures roll like an odometer. The host pads them, since a blank is not on their ring |
| Pulling the lever | a press on the SPIN button, or Space or Enter, fires `spin` (`press`, `input.keys`). Where the reels land is still the host's to say, so a press on its own spins them to the symbols they already show |
| Bet | a `numeric7` segment display, for the one readout on the machine that never rolls |
| Sound | an `audio` layer per event, all on the same `spin` trigger the wheels take: one spin sound per reel, each as long as that reel's spin, and three clunks with a `delay` matching each wheel's stop. A chime or a thud on `win` and `lose` |
| A wheel running down | nothing in a show can follow a reel's speed, so the deceleration is baked into the sound: [`tools/slot_machine_sounds.py`](../tools/slot_machine_sounds.py) reads each reel's `duration` and `turns` out of this file and ticks wherever the ease says a symbol passes the line, so the ticks land on the symbols the eye sees. It is the same tick every time: thirty identical ticks a second fuse into a buzz that falls in pitch with the wheel and comes apart into single ticks as it arrives, where thirty different ones would only hiss |
| Celebration | `win` flashes the cabinet's stroked outline, pulses the payline and pops a banner in with a `back_out` ease, below the line so the winning symbols stay visible |

It needs cuelight `main` with reel rows, reel artwork, path shapes and
audio layers.

## Running

```sh
cd ../../cuelight
cargo run -p cuelight-player -- ../cuelight-examples/slot_machine
```

`test-driver.json` is picked up automatically and plays eight rounds in
about a minute: three misses, two cherries, a miss, three bells, a near
miss on sevens and the jackpot. Two of those lines repeat a symbol in
the same place as the line before them, the first round and the jackpot,
which is the case the `spin` trigger exists for. The rounds are written out by
[`tools/slot_machine_rounds.py`](../tools/slot_machine_rounds.py) rather
than drawn at random, so the demo is the same every time. You can also
play from the player's prompt: `reel_1=7`, `reel_2=7`, `reel_3=7`, then
`spin` and `win`.

The host owns the game. It takes the bet, says which symbol each reel
lands on, fires `spin`, waits for the last wheel, then fires `win` or
`lose` and settles the credits. Saying where they land and pulling the
lever in the same breath is one journey per wheel, not two. The show has
no idea what pays.

## Where the timings come from

The wheels are as slow as real ones, which is slower than it feels like
they should be. A stepper machine spins its three reels for roughly 3.5
to 4.5 seconds, stopping left to right, and the usual design adds whole
extra revolutions to each reel so that every one lands at least a full
turn after the one before it; 3.52, 4.07 and 4.49 seconds are the
figures a patent on emulating reel hardware gives for one spin. Reels
turn at over 100 revolutions per minute, so a four second spin is eight
or ten turns, not three.

A purely mechanical machine gets there differently. The handle releases
a brake and winds a governor, letting go fires a kicker that flings the
reels, and from then on they simply run down against brake wires, with a
timing bar indexing each reel into its stop one after another. A reel is
meant to be *almost* stopped when its stop lever drops against the reel
stop star; a reel still travelling hits its stop with a jarring bounce.
That is the shape this show copies: a hard throw, a long run down, and a
small bounce as the lever catches it.

## Assets

Everything under `assets/` is committed and free to redistribute. Licenses
were checked at the linked sources on 2026-09-20; the license texts that
have to travel with the files are in [`licenses/`](licenses/).

| Asset | Origin | License |
| --- | --- | --- |
| `*.svg`, `drum.png` | Made for this show, drawn by [`tools/slot_machine_art.py`](../tools/slot_machine_art.py) | MIT, as this repository |
| `sounds/*.ogg` | Made for this show, synthesized from sines and noise by [`tools/slot_machine_sounds.py`](../tools/slot_machine_sounds.py) | MIT, as this repository |
| `fonts/Oxanium-Bold.ttf` | [Oxanium](https://github.com/sevmeyer/oxanium) by The Oxanium Project Authors, the unmodified static file from [`fonts/ttf`](https://github.com/sevmeyer/oxanium/tree/a8f39e0c71186190027a093e9001459410192d1e/fonts/ttf) | [OFL-1.1](licenses/Oxanium-OFL.txt), no reserved font name |

The game, its odds and its name are made up.

## What would make it better

- Reel cells centre the font's line box rather than the characters
  (cuelight #60), which is why the credits sit slightly high in their
  window.
- A blur or a squash on a spinning wheel: at speed the symbols step from
  frame to frame rather than smearing, which is what sells a real reel.
- Sound that follows the wheel while it turns. The spin sounds are baked
  from the reel's own numbers, so they cannot drift, but they are fixed
  recordings: a held or nudged reel, or a wheel the host stops early,
  would still be heard running. A reel reporting the steps it took this
  frame, the way the design notes suggest for mechanical sound, would
  make the click the wheel's rather than a copy of it. The clunks have
  the same trouble, placed by hand at each wheel's duration.
- A held or nudged reel, which is most of what a real fruit machine does
  and needs nothing new: the host would simply leave one variable alone.
