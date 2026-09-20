#!/usr/bin/env python3
"""Rasterize a pixel TrueType font into an AngelCode BMFont (text .fnt + PNG).

cuelight reads bitmap fonts only, so the shows here commit the generated
files. Glyphs are rendered without antialiasing unless asked: for a pixel
font pick the pixel size it was drawn for, or the result will be uneven.
An outline font wants --antialias and a size at least as large as it will
be shown, since cuelight scales the glyph pixels. Every glyph keeps a
transparent margin (--padding) in the atlas: cuelight draws a font style's
border into it, so it has to be at least as wide as the widest border.

    tools/ttf2bmfont.py Tiny5-Regular.ttf 8 myshow/assets/fonts/tiny5-8

Needs Pillow.
"""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ASCII = "".join(chr(c) for c in range(32, 127))


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("ttf", type=Path)
    parser.add_argument("size", type=int, help="pixel size to rasterize at")
    parser.add_argument("out", type=Path, help="output path without extension")
    parser.add_argument("--padding", type=int, default=1, help="transparent margin around each glyph")
    parser.add_argument("--antialias", action="store_true", help="keep smooth glyph edges")
    parser.add_argument("--weight", type=int, help="weight axis value of a variable font")
    parser.add_argument("--chars", default=ASCII, help="characters to include (default: printable ASCII)")
    parser.add_argument("--tabular", action="store_true", help="give all digits the widest digit's advance")
    args = parser.parse_args()

    font = ImageFont.truetype(str(args.ttf), args.size)
    if args.weight is not None:
        font.set_variation_by_axes([args.weight])
    ascent, descent = font.getmetrics()
    cell = (args.size * 3, ascent + descent + args.size)

    # Each glyph is drawn at the same origin so its bounding box gives the
    # offsets from the pen position and the top of the ascent.
    origin = (args.size, args.size // 2)
    glyphs = []
    for char in sorted(set(args.chars)):
        image = Image.new("L", cell, 0)
        draw = ImageDraw.Draw(image)
        draw.fontmode = "L" if args.antialias else "1"
        draw.text(origin, char, font=font, fill=255)
        box = image.getbbox()
        advance = round(font.getlength(char))
        if box is None:
            glyphs.append((char, None, 0, 0, advance))
        else:
            glyphs.append((char, image.crop(box), box[0] - origin[0], box[1] - origin[1], advance))

    if args.tabular:
        # Center every digit in the widest one's advance, so that numbers
        # keep their width while they change.
        widest = max(g[4] for g in glyphs if g[0].isdigit())
        glyphs = [
            (c, image, xoffset + (widest - advance) // 2, yoffset, widest) if c.isdigit() else (c, image, xoffset, yoffset, advance)
            for c, image, xoffset, yoffset, advance in glyphs
        ]

    # The TrueType ascent and descent are usually roomier than the pixels;
    # trim the line to what the glyphs really cover.
    inked = [g for g in glyphs if g[1] is not None]
    top = min(g[3] for g in inked)
    bottom = max(g[3] + g[1].height for g in inked)
    line_height = bottom - top
    base = ascent - top

    # Shelf packing; a glyph's rectangle includes its padding.
    pad = args.padding
    atlas_width = 128
    while atlas_width < 6 * args.size:
        atlas_width *= 2
    x = y = shelf = 0
    placed = []
    for char, image, xoffset, yoffset, advance in glyphs:
        width, height = (image.width + 2 * pad, image.height + 2 * pad) if image else (0, 0)
        if x + width > atlas_width:
            x, y, shelf = 0, y + shelf, 0
        placed.append((char, image, x, y, width, height, xoffset - pad, yoffset - top - pad, advance))
        x += width
        shelf = max(shelf, height)
    atlas_height = 1
    while atlas_height < y + shelf:
        atlas_height *= 2

    atlas = Image.new("RGBA", (atlas_width, atlas_height), (255, 255, 255, 0))
    for _, image, x, y, *_ in placed:
        if image:
            white = Image.new("RGBA", image.size, (255, 255, 255, 255))
            atlas.paste(white, (x + pad, y + pad), image)
    page = args.out.with_suffix(".png")
    atlas.save(page, optimize=True)

    # A variable font reports the style of its default instance.
    family, style = font.getname()
    if args.weight is not None:
        style = f"wght {args.weight}"
    lines = [
        f'info face="{family} {style}" size={args.size} bold=0 italic=0 charset="" unicode=1 '
        f"stretchH=100 smooth={int(args.antialias)} aa={int(args.antialias)} padding={pad},{pad},{pad},{pad} spacing=0,0 outline=0",
        f"common lineHeight={line_height} base={base} scaleW={atlas_width} scaleH={atlas_height} "
        "pages=1 packed=0 alphaChnl=0 redChnl=4 greenChnl=4 blueChnl=4",
        f'page id=0 file="{page.name}"',
        f"chars count={len(placed)}",
    ]
    for char, _, x, y, width, height, xoffset, yoffset, advance in placed:
        lines.append(
            f"char id={ord(char)} x={x} y={y} width={width} height={height} "
            f"xoffset={xoffset} yoffset={yoffset} xadvance={advance} page=0 chnl=15"
        )
    args.out.with_suffix(".fnt").write_text("\n".join(lines) + "\n")
    print(f"{args.out}: {len(inked)} glyphs, line height {line_height}, base {base}")


if __name__ == "__main__":
    main()
