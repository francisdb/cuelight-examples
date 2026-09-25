#!/bin/sh
# Build the website into _site/: the gallery pages, the cuelight player
# compiled to WebAssembly, and every show of examples.json with the
# manifest a browser needs to fetch it. Serve it with any static file
# server, e.g. `python3 -m http.server -d _site`.
#
#   site/build.sh
#
# Needs a cuelight checkout next to this repository (or at $CUELIGHT), the
# wasm32 target (`rustup target add wasm32-unknown-unknown`), a
# wasm-bindgen CLI of the version in cuelight's Cargo.lock and python3.
# wasm-opt (binaryen) shrinks the player when it is installed.
#
# Thumbnails are not built here, they are committed: render them with
# `tools/thumbnails.py`, which needs a GPU.
set -eu

site=$(cd "$(dirname "$0")" && pwd)
repo=$(cd "$site/.." && pwd)
cuelight=$(cd "${CUELIGHT:-$repo/../cuelight}" && pwd)
out="$repo/_site"

# The shows of the catalog, which has to list every show in the repository.
shows=$(python3 - "$repo" <<'PY'
import json, pathlib, sys
repo = pathlib.Path(sys.argv[1])
catalog = json.loads((repo / "examples.json").read_text())
listed = [e["path"] for c in catalog["categories"] for e in c["examples"]]
found = {str(p.parent.relative_to(repo)) for p in repo.glob("**/show.json") if "_site" not in p.parts}
problems = [f"{p}: listed twice" for p in set(listed) if listed.count(p) > 1]
problems += [f"{p}: in examples.json, but there is no show.json" for p in listed if p not in found]
problems += [f"{p}: not in examples.json" for p in sorted(found - set(listed))]
problems += [f"{p}: no thumbnail, render them first" for p in listed if not (repo / "site/thumbnails" / f"{p}.png").is_file()]
if problems:
    sys.exit("\n".join(problems))
print("\n".join(listed))
PY
)

rm -rf "$out"
mkdir -p "$out"
cp "$site"/*.html "$site"/*.css "$repo/examples.json" "$out"
cp -r "$site/thumbnails" "$out/thumbnails"
touch "$out/.nojekyll"

cargo build --manifest-path "$cuelight/Cargo.toml" -p cuelight-web \
    --target wasm32-unknown-unknown --release
wasm-bindgen --target web --no-typescript --out-dir "$out/pkg" \
    "${CARGO_TARGET_DIR:-$cuelight/target}/wasm32-unknown-unknown/release/cuelight_web.wasm"
if command -v wasm-opt >/dev/null; then
    wasm-opt -Os "$out/pkg/cuelight_web_bg.wasm" -o "$out/pkg/cuelight_web_bg.wasm"
fi

# Only what a player loads: the whole folder, since a show may name files
# by path anywhere in it, but no READMEs and no license texts (those stay
# with the repository, which every example page links to).
for show in $shows; do
    mkdir -p "$out/shows/$show"
    cp -r "$repo/$show/." "$out/shows/$show"
    rm -rf "$out/shows/$show/README.md" "$out/shows/$show/licenses"
done
# shellcheck disable=SC2046 # show paths have no spaces
cargo run --manifest-path "$cuelight/Cargo.toml" -q -p cuelight-loader \
    --bin cuelight-manifest -- $(for show in $shows; do echo "$out/shows/$show"; done)
