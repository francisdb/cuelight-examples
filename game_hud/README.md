# game_hud

A fantasy RPG interface on a 960x540 canvas, over a dusk landscape that
stands in for the game: a hero on the road to a ruined chapel, a fight
with a Bog Wraith, a quest finished and a level gained. The game tells
the HUD what happened through a few variables and triggers, and
everything the player then sees and hears, the orbs, the cooldowns, the
numbers, the banners, is the show's.

A game made in an engine usually draws its own interface, so this is
more a showcase than a use case. Its parts are the ones a pinball
machine's screen needs, though: modes with timers and goals, combos,
scores, awards and banners, driven by a game that only says what
happened. That is where cuelight is aimed.

| Part | How it works |
| --- | --- |
| Health and mana orbs | the liquid is a group inside a circular `clip`, its `y` bound to the value (`scale` and `offset` turn 0 to 240 into empty to full) with an eased `transition`. Its surface is a wave path that rolls sideways forever: a looping `x` timeline over exactly one wavelength, so the loop has no seam. A radial gradient that is dark only at its rim lies on top and makes it a glass ball, and an `add` glint catches the light |
| Orb reactions | the health orb glows red on `hurt` and green on `healed`; the mana orb glows as a spell spends it (a timeline with a list of triggers) |
| Low health | below 30% a red pulse beats round the health orb, a group whose `visible` is bound to `hp` with a `threshold` (flipped with `scale` -1 and `offset` 1, so it shows *below* the level) and a `debounce` |
| Skills | six slots of SVG icons. `skill_1` to `skill_6` flash a slot and start its cooldown, a clock wipe from two half discs of shade, each turning inside a clip over one half of the slot, so together they cover any angle. Each slot's cooldown is its own length, from one second to fifteen, and its `on_end` fires `ready_n`, which rings the frame |
| Target | a frame shown while `target` names someone (`visible` bound through a `map` that makes the empty name 0). Its bar is a shape stretched with `scale_x`, with a pale ghost behind it on a slower `cubic_in` transition, so a big hit shows what it took |
| Combat text | `hit` floats the damage up from the target. A `font` binding on `crit` swaps it to a larger orange style for critical hits. Healing floats up green beside the health orb |
| Minimap | parchment turning under a fixed arrow: its `rotation` bound to `heading`, negated. The N marker rides round the rim on the same binding, and turns back the other way itself, so the letter stays upright |
| Quest tracker | the objective count is bound to `braziers`; `objective` flashes the line and pops the count, and at 3 of 3 a `font` binding turns it green and a `threshold` shows the check |
| Hero | a portrait medallion with the crest, the name in Cinzel, gold that counts up (`format: thousands` with a transition), and a level badge that pops on `level_up` |
| Banners | Quest Complete and Level, in Cinzel between gold rules, each a group that fades and settles in on its trigger |
| Life in the scene | fireflies drifting over the meadow: glows with the `add` blend on looping timelines of different lengths, so they never line up |
| Sound | recordings for what is physical and synthesis for the magic. The sword is a swing at the cast and a clang on armour 0.12 seconds later (`delay`), each from a few takes (`pick`). A wraith's death is several layers on one trigger, each with its own `delay`: it dissolves, its weapon drops and bounces, its body falls |

It needs cuelight `main` with blend modes, rotation, vector artwork,
bindable `visible` with `threshold` and `debounce`, `font` bindings,
sound with `pick` and `delay`, and outline fonts.

## Running

```sh
cd ../../cuelight
cargo run -p cuelight-player -- ../cuelight-examples/game_hud
```

`test-driver.json` is picked up automatically and plays a 40 second
encounter: the walk towards the chapel, the fight with all six skills, a
potion when health runs low, the loot, the last brazier, the quest and
the level, and a second, shorter fight. It is written out by
[`tools/game_hud_encounter.py`](../tools/game_hud_encounter.py) rather
than rolled, so the demo is the same every time. You can also play from
the player's prompt: `skill_2`, `hp=40`, `hurt`, `damage=999`,
`crit=true`, `hit`, `heading=180`, `level_up`.

What a game sends: `hp`, `mana`, `xp`, `level`, `gold`, `target` and
`target_hp` (in percent), `damage` and `crit` (set in the same breath as
`hit`), `healed`, `heading`, `braziers` and `loot`, and the triggers
`skill_1` to `skill_6`, `hit`, `hurt`, `healed`, `enemy_die`, `loot`,
`objective`, `quest_complete` and `level_up`.

## Assets

Everything under `assets/` is committed and free to redistribute.

| Asset | Origin | License |
| --- | --- | --- |
| `dusk.png`, `map.png`, the icon SVGs | Made for this show, drawn by [`tools/game_hud_art.py`](../tools/game_hud_art.py) | MIT, as this repository |
| `fireball`, `frost`, `ward`, `heal`, `ignite`, `potion`, `dissolve`, `level_up` (`.ogg`) | Made for this show, synthesized from sines and noise with a reverb by [`tools/game_hud_sounds.py`](../tools/game_hud_sounds.py) | MIT, as this repository |
| `swing1`, `swing2`, `coins` (`.ogg`) | [RPG Audio](https://kenney.nl/assets/rpg-audio) by Kenney, fetched by [`tools/game_hud_fetch.sh`](../tools/game_hud_fetch.sh) | [CC0](licenses/Kenney-RPG-Audio-CC0.txt) |
| `clang1` to `clang3`, `hurt1`, `hurt2`, `clatter1`, `clatter2`, `fall`, `bell` (`.ogg`) | [Impact Sounds](https://kenney.nl/assets/impact-sounds) by Kenney, fetched by the same script | [CC0](licenses/Kenney-Impact-Sounds-CC0.txt) |
| `fonts/Cinzel-Bold.ttf` | [Cinzel](https://github.com/NDISCOVER/Cinzel), fetched by [`tools/game_hud_fetch.sh`](../tools/game_hud_fetch.sh) | [OFL 1.1](licenses/Cinzel-OFL.txt); the only reserved name is Cinzel Decorative, not used here |
| `fonts/Alegreya-Regular.ttf` | [Alegreya](https://github.com/huertatipografica/Alegreya), the regular weight cut from the variable font and trimmed to Latin-1 by the same script | [OFL 1.1](licenses/Alegreya-OFL.txt), no reserved font name |

## What would make it better

- Values worked out from other values. The game sends `target_hp` in
  percent next to the damage, and the orbs have their maximum written
  into the show (`scale` -104/240), because a binding cannot divide one
  variable by another. A level-up that raised the maximum health would
  need the show changed.
- A sweep angle. Each cooldown takes two half discs, two clips and two
  timelines that have to agree on their timing; a circle with a start
  and end angle, bindable like any other number, would be one layer, and
  could follow a cooldown the game reports.
- Spawning. There is one damage number, and each hit restarts it. A
  flurry of hits in an RPG leaves a spray of numbers drifting apart,
  which needs a layer the show can instantiate on a trigger and forget
  when its timeline ends.
- Setting a value without its transition. When the hero levels up, the
  XP bar is filled to the end and then set back to the new level's
  start, and its transition drains it backwards on the way. A game wants
  the bar to wrap: fill up, flash, start again from empty.
- OpenType features. Alegreya's default figures are old-style, so every
  number is set in Cinzel instead; a font style that could ask for
  lining figures (`lnum`) or small caps would let one body face do both.
- Text around a bound number. The heal needs a separate `+` layer, and
  the orbs' "of 240" is its own line, because a bound number cannot carry
  a prefix or a suffix.
