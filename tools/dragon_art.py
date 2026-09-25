#!/usr/bin/env python3
"""Prepare the dragon backglass's images.

    tools/dragon_art.py

dragon.png is Katsushika Hokusai's Dragon, a ceiling painting now in the
public domain, fetched from Wikimedia Commons and brought down to the
1000 pixels square the show fills its canvas with. Its colours are flat, as a
painting for a ceiling is, so a palette of 128 keeps it close to the
original at a fraction of the size.

glow.png is a white glow, dense in the middle and gone at the rim: every
lamp behind the glass is one, tinted and dimmed by its filament.

Run by tools/dragon_fetch.sh. Needs Pillow.
"""

import io
import json
import math
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

OUT = Path(__file__).resolve().parent.parent / "dragon"
TITLE = "File:Hokusai Dragon.jpg"
SIZE = 1000
AGENT = {"User-Agent": "cuelight-examples (https://github.com/francisdb/cuelight-examples)"}


def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=AGENT)) as response:
        return response.read()


def painting():
    query = urllib.parse.urlencode({
        "action": "query", "format": "json", "titles": TITLE, "prop": "imageinfo",
        "iiprop": "url|extmetadata", "iiextmetadatafilter": "LicenseShortName|Artist|ObjectName",
    })
    page = next(iter(json.loads(fetch(f"https://commons.wikimedia.org/w/api.php?{query}"))["query"]["pages"].values()))
    info = page["imageinfo"][0]
    licence = info["extmetadata"]["LicenseShortName"]["value"]
    if "public domain" not in licence.lower():
        raise SystemExit(f"{TITLE} is no longer marked public domain: {licence}")
    image = Image.open(io.BytesIO(fetch(info["url"]))).convert("RGB")
    image = image.resize((SIZE, SIZE), Image.LANCZOS)
    image = image.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    image.save(OUT / "assets" / "dragon.png", optimize=True)
    (OUT / "licenses" / "Hokusai-Dragon.txt").write_text(
        f"Dragon, by Katsushika Hokusai (1760-1849).\n\n"
        f"Public domain: the painter died more than a hundred years ago, and the\n"
        f"reproduction is marked \"{licence}\" on Wikimedia Commons:\n"
        f"{info['descriptionurl']}\n\n"
        f"assets/dragon.png is that image brought down to {SIZE} pixels square\n"
        f"with a palette of 128 colours, by tools/dragon_art.py.\n")


def glow(size=128):
    image = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    pixels = image.load()
    for y in range(size):
        for x in range(size):
            d = math.hypot(x + 0.5 - size / 2, y + 0.5 - size / 2) / (size / 2)
            pixels[x, y] = (255, 255, 255, int(255 * max(0.0, 1.0 - d) ** 2))
    image.save(OUT / "assets" / "glow.png", optimize=True)


def main():
    (OUT / "assets").mkdir(parents=True, exist_ok=True)
    (OUT / "licenses").mkdir(parents=True, exist_ok=True)
    painting()
    glow()
    for name in ("dragon.png", "glow.png"):
        print(f"dragon/assets/{name}: {(OUT / 'assets' / name).stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
