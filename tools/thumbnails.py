#!/usr/bin/env python3
"""Render one thumbnail per show listed in examples.json.

Each show is rendered by cuelight-render at its entry's `thumbnail_at`
seconds (2 by default), with its driver playing, as a host would show it
about 640 pixels wide, and written to site/thumbnails/<path>.png.

    tools/thumbnails.py [path ...]

Without paths every show is rendered. Needs a cuelight checkout next to
this repository (or at $CUELIGHT) and a GPU adapter.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

WIDTH = 640

repo = Path(__file__).resolve().parent.parent
cuelight = Path(os.environ.get("CUELIGHT", repo.parent / "cuelight")).resolve()


def main():
    catalog = json.loads((repo / "examples.json").read_text())
    examples = [e for c in catalog["categories"] for e in c["examples"]]
    wanted = set(sys.argv[1:])
    unknown = wanted - {e["path"] for e in examples}
    if unknown:
        sys.exit(f"not in examples.json: {', '.join(sorted(unknown))}")

    subprocess.run(
        ["cargo", "build", "-q", "--release", "--manifest-path", cuelight / "Cargo.toml",
         "-p", "cuelight-loader", "--features", "render-cli", "--bin", "cuelight-render"],
        check=True,
    )
    target = Path(os.environ.get("CARGO_TARGET_DIR", cuelight / "target"))
    render = target / "release" / "cuelight-render"

    for example in examples:
        path = example["path"]
        if wanted and path not in wanted:
            continue
        at = example.get("thumbnail_at", 2.0)
        out = repo / "site/thumbnails" / f"{path}.png"
        with tempfile.TemporaryDirectory() as frames:
            subprocess.run(
                [render, repo / path, "--at", str(at), "--width", str(WIDTH), "-o", frames],
                check=True, stdout=subprocess.DEVNULL,
            )
            [frame] = Path(frames).glob("*.png")
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(frame, out)
        print(f"{path}: at {at} s")


if __name__ == "__main__":
    main()
