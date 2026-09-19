# cuelight-examples

Example shows for [cuelight](https://github.com/francisdb/cuelight), the
embeddable engine for trigger- and variable-driven displays. Each show is a
folder you can play directly with the cuelight player.

## Shows

| Show | Description |
| --- | --- |
| [flexdemo](flexdemo/) | FlexDMD's demo table as a cuelight show (work in progress, see its checklist) |

Every show folder has its own README describing what it shows, how to run
it, and where its assets come from.

## Running a show

From a [cuelight](https://github.com/francisdb/cuelight) checkout next to
this repository:

```sh
cargo run --example player -- ../cuelight-examples/<show>
```

Some shows fetch their assets with a script instead of committing them; the
show's README says so.

## Licenses

The show documents and driver files in this repository are licensed as
stated in [LICENSE](LICENSE). Assets (images, fonts, sounds, videos) keep
their original licenses: each show's README lists every asset with its
license and a link to its source. Check those terms before reusing an asset
elsewhere.
