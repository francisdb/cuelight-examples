#!/usr/bin/env python3
"""Draw the images and the sound of streamer_overlay.

    tools/streamer_overlay_assets.py streamer_overlay/assets

footage.png stands in for the game capture the overlay sits on: soft
colored blobs on a dark ground, 640x360, shown at four times that size,
so it looks like an out-of-focus game the way a stream preview does.

alert_icons.png is a sprite sheet of three 96x96 cells, one per alert
kind: a heart (follow), a star (subscription) and a lightning bolt (raid),
each in its own color. They are drawn four times larger and scaled down,
which is all the antialiasing they get.

sounds/chime.ogg is the alert chime: two sine notes a fifth apart, each
with a fast attack and a long decay, 0.9 seconds, mono, written as WAV
and encoded to Ogg Vorbis with ffmpeg.

Needs Pillow.
"""

import math
import random
import struct
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

SS = 4  # supersampling factor for the icons

# The overlay's own colors, kept in step with show.json.
HEART = (255, 92, 138)
STAR = (255, 200, 87)
BOLT = (77, 225, 255)


def footage(out):
    width, height = 640, 360
    random.seed(7)
    image = Image.new("RGB", (width, height))
    pixels = image.load()
    # A vertical gradient from a night blue to a deep purple.
    for y in range(height):
        f = y / (height - 1)
        pixels_row = (int(14 + 20 * f), int(18 + 6 * f), int(34 + 30 * f))
        for x in range(width):
            pixels[x, y] = pixels_row
    draw = ImageDraw.Draw(image)
    palette = [(52, 84, 160), (120, 60, 170), (40, 130, 120), (170, 80, 70), (200, 150, 60)]
    for _ in range(28):
        r = random.randint(30, 110)
        cx, cy = random.randint(-20, width + 20), random.randint(-20, height + 20)
        color = random.choice(palette)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    # Bokeh: a few small bright discs.
    for _ in range(16):
        r = random.randint(4, 12)
        cx, cy = random.randint(0, width), random.randint(0, height)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(230, 220, 200))
    image = image.filter(ImageFilter.GaussianBlur(26))
    image.save(out / "footage.png", optimize=True)


def heart(draw, size, color):
    # Two discs and a point below them.
    s = size
    r = s * 0.24
    for cx in (s * 0.32, s * 0.68):
        cy = s * 0.36
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    draw.polygon(
        [(s * 0.085, s * 0.42), (s * 0.5, s * 0.9), (s * 0.915, s * 0.42), (s * 0.5, s * 0.5)],
        fill=color,
    )


def star(draw, size, color):
    cx = cy = size / 2
    outer, inner = size * 0.46, size * 0.19
    points = []
    for i in range(10):
        radius = outer if i % 2 == 0 else inner
        angle = -math.pi / 2 + i * math.pi / 5
        points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    draw.polygon(points, fill=color)


def bolt(draw, size, color):
    s = size
    draw.polygon(
        [
            (s * 0.58, s * 0.05),
            (s * 0.22, s * 0.55),
            (s * 0.46, s * 0.55),
            (s * 0.38, s * 0.95),
            (s * 0.78, s * 0.4),
            (s * 0.53, s * 0.4),
            (s * 0.66, s * 0.05),
        ],
        fill=color,
    )


def icons(out):
    cell = 96
    big = cell * SS
    sheet = Image.new("RGBA", (cell * 3, cell), (0, 0, 0, 0))
    for i, (shape, color) in enumerate([(heart, HEART), (star, STAR), (bolt, BOLT)]):
        icon = Image.new("RGBA", (big, big), color + (0,))
        shape(ImageDraw.Draw(icon), big, color + (255,))
        sheet.paste(icon.resize((cell, cell), Image.LANCZOS), (i * cell, 0))
    sheet.save(out / "alert_icons.png", optimize=True)


def chime(out):
    rate = 44100
    seconds = 0.9
    notes = [(0.0, 880.0), (0.12, 1318.5)]  # A5, then E6
    frames = []
    for n in range(int(rate * seconds)):
        t = n / rate
        value = 0.0
        for start, frequency in notes:
            if t < start:
                continue
            age = t - start
            envelope = min(age / 0.008, 1.0) * math.exp(-age * 5.5)
            value += 0.45 * envelope * math.sin(2 * math.pi * frequency * age)
            # A quiet octave above gives it some sparkle.
            value += 0.08 * envelope * math.sin(2 * math.pi * frequency * 2 * age)
        frames.append(struct.pack("<h", int(max(-1.0, min(1.0, value)) * 32767)))
    (out / "sounds").mkdir(exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        with wave.open(tmp.name, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            w.writeframes(b"".join(frames))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp.name, "-c:a", "libvorbis", "-q:a", "4",
                        "-map_metadata", "-1", "-fflags", "+bitexact", "-flags:a", "+bitexact", str(out / "sounds" / "chime.ogg")], check=True)


def main():
    out = Path(sys.argv[1])
    footage(out)
    icons(out)
    chime(out)


if __name__ == "__main__":
    main()
