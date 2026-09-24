# cuelight-examples

Example shows for [cuelight](https://github.com/francisdb/cuelight), the
embeddable engine for trigger- and variable-driven displays. Each show is a
folder you can play directly with the cuelight player, and they all play
in the browser on the [website](https://francisdb.github.io/cuelight-examples/).

## Shows

| Show | Description |
| --- | --- |
| [boardwalk](boardwalk/) | A retro electromechanical pinball backglass: one painted picture lit from behind, score reels that step and chime, and every light of the game painted into the scene |
| [car_dashboard](car_dashboard/) | A digital instrument cluster driven by variables: bars, shift lights, gear, warning lamps, turn signals |
| [checkerboard](checkerboard/) | A rotating, breathing checkerboard behind a still chess piece: nested transforms, a host-driven zoom and a squashed shadow |
| [departure_board](departure_board/) | An airport departure board made of segment displays, with no assets at all: text variables, mapped status colors, refresh triggers |
| [eclipse](eclipse/) | A total solar eclipse explained: the sky darkening into totality beside a side view of the shadow, playing itself with no driver: the moon's journey fires each contact and everything else reacts |
| [game_hud](game_hud/) | A fantasy RPG interface: health and mana orbs, a skill hotbar with clock-wipe cooldowns, a turning minimap, a quest tracker, floating damage and banners, over a dusk landscape |
| [slot_machine](slot_machine/) | A fruit machine: three reels of SVG symbols spinning to staggered stops, with sound, rolling credits and a win celebration |
| [pinball_dmd](pinball_dmd/) | A pinball dot-matrix display: score layouts, a jackpot in full color, a night drive video mode and a segment display |
| [streamer_overlay](streamer_overlay/) | A live stream overlay: alerts with a chime, a lower third, a follower goal bar, a viewer count, and starting-soon and be-right-back screens |
| [weather_dashboard](weather_dashboard/) | A weather kiosk that plays a whole day: a sky and sun that follow the clock, animated SVG icons, a forecast and hourly bars, all from variables |

Every show folder has its own README describing what it shows, how to run
it, and where its assets come from.

## Feature examples

[`features/`](features/) holds small shows that each demonstrate one thing
the format can do: layers, images, text, bindings, timelines, scenes,
output modes, events. They share [one README](features/README.md).

Shows are self-contained: every asset is committed, so only assets whose
license allows redistribution get in. `tools/` holds the scripts that
generated assets, such as bitmap fonts rasterized from OFL TrueType fonts.

## Running a show

From a [cuelight](https://github.com/francisdb/cuelight) checkout next to
this repository:

```sh
cargo run -p cuelight-player -- ../cuelight-examples/<show>
```

## Website

[`examples.json`](examples.json) is the catalog of the website: categories,
and per show a title, a description and the moment its thumbnail is taken.
A show that is not listed fails the build.

```sh
cargo run --manifest-path tools/thumbnails/Cargo.toml   # render site/thumbnails, needs a GPU
site/build.sh                                           # build _site/
python3 -m http.server -d _site
```

`site/build.sh` compiles the cuelight web player from the cuelight checkout
next to this repository; its header lists what it needs. Thumbnails are
committed because CI has no GPU to render them. The
[Site workflow](.github/workflows/site.yml) checks every show (it loads
without warnings, its assets are all there and all used, its driver only
fires triggers and sets variables the show has), checks the links of the
READMEs and pages, builds the site against cuelight `main` and deploys it
to GitHub Pages on every push to `main`. The show checks run locally with

```sh
cargo run --manifest-path tools/thumbnails/Cargo.toml --no-default-features -- --check
```

## Licenses

The show documents and driver files in this repository are licensed as
stated in [LICENSE](LICENSE). Assets (images, fonts, sounds, videos) keep
their original licenses: each show's README lists every asset with its
license and a link to its source, and keeps the license texts that must
accompany the files in its `licenses/` folder. Check those terms before
reusing an asset elsewhere.
