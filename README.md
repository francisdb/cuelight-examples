# cuelight-examples

Example shows for [cuelight](https://github.com/francisdb/cuelight), the
embeddable engine for trigger- and variable-driven displays. Each show is a
folder you can play directly with the cuelight player.

## Shows

| Show | Description |
| --- | --- |
| [car_dashboard](car_dashboard/) | A digital instrument cluster driven by variables: bars, shift lights, gear, warning lamps, turn signals |

Every show folder has its own README describing what it shows, how to run
it, and where its assets come from.

Shows are self-contained: every asset is committed, so only assets whose
license allows redistribution get in. `tools/` holds the scripts that
generated assets, such as bitmap fonts rasterized from OFL TrueType fonts.

## Running a show

From a [cuelight](https://github.com/francisdb/cuelight) checkout next to
this repository:

```sh
cargo run -p cuelight-player -- ../cuelight-examples/<show>
```

## Licenses

The show documents and driver files in this repository are licensed as
stated in [LICENSE](LICENSE). Assets (images, fonts, sounds, videos) keep
their original licenses: each show's README lists every asset with its
license and a link to its source, and keeps the license texts that must
accompany the files in its `licenses/` folder. Check those terms before
reusing an asset elsewhere.
