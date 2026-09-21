# cuelight-examples

Example shows for [cuelight](https://github.com/francisdb/cuelight), the
embeddable engine for trigger- and variable-driven displays. Each show is a
folder you can play directly with the cuelight player, and they all play
in the browser on the [website](https://francisdb.github.io/cuelight-examples/).

## Shows

| Show | Description |
| --- | --- |
| [car_dashboard](car_dashboard/) | A digital instrument cluster driven by variables: bars, shift lights, gear, warning lamps, turn signals |

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
