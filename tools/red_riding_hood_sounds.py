#!/usr/bin/env python3
"""Synthesize red_riding_hood's page turns.

    tools/red_riding_hood_sounds.py

Two takes of a page turning, turn1.ogg and turn2.ogg, played one after
the other so two turns in a row do not sound the same. Each has two
parts: a soft scrape as the page lifts, then a swing through the air
whose band opens and closes with the page's speed and whose level
flutters as the paper flexes, with crinkles on top, dying away as the
leaf lands on the left page (0.72 s). No landing knock: paper does not
make one. All of it above 400 Hz. Made from noise only, so there is
nothing to license; encoded to Ogg Vorbis with ffmpeg, bit-exactly.
"""

import math
import random
import struct
import subprocess
import tempfile
import wave
from pathlib import Path

RATE = 22050
OUT = Path(__file__).resolve().parent.parent / "red_riding_hood" / "assets" / "sounds"


def encode(path, samples):
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        frames = b"".join(struct.pack("<h", int(max(-1.0, min(1.0, s)) * 32767)) for s in samples)
        with wave.open(tmp.name, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(RATE)
            w.writeframes(frames)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp.name, "-c:a", "libvorbis", "-q:a", "3",
                        "-map_metadata", "-1", "-fflags", "+bitexact", "-flags:a", "+bitexact", str(path)], check=True)


def lowpass(samples, cutoff):
    """One pole; cutoff may be a number or a function of the sample index."""
    out, y = [], 0.0
    for i, v in enumerate(samples):
        c = cutoff(i) if callable(cutoff) else cutoff
        y += (v - y) * (1 - math.exp(-2 * math.pi * c / RATE))
        out.append(y)
    return out


def band(samples, low, high):
    """A crude band pass: a low pass at high minus a low pass at low."""
    a, b = lowpass(samples, high), lowpass(samples, low)
    return [x - y for x, y in zip(a, b)]


def turn(seed, lands=0.72, seconds=0.95):
    """A page turning: it lifts with a soft scrape and swings through the
    air with the paper fluttering and crinkling as it flexes, dying away as
    it lands on the other side at `lands` seconds, when the leaf does."""
    random.seed(seed)
    total = int(RATE * seconds)
    noise = [random.uniform(-1, 1) for _ in range(total)]

    # The swing: a band that opens up as the page speeds through the air
    # and closes again, its level fluttering as the paper flexes.
    def centre(i):
        t = i / RATE
        return 900 + 2600 * math.sin(math.pi * min(1.0, t / lands)) ** 1.5
    air = [x - y for x, y in zip(lowpass(noise, centre), lowpass(noise, lambda i: centre(i) / 3))]
    flutter = lowpass([random.uniform(-1, 1) for _ in range(total)], 35)
    peak = max(abs(f) for f in flutter) or 1.0
    swing = []
    for i, v in enumerate(air):
        t = i / RATE
        lift = 0.25 * min(1.0, t / 0.04) if t < 0.12 else 0.0
        body = math.sin(math.pi * min(1.0, max(0.0, (t - 0.05) / (lands - 0.02)))) ** 1.2 if t < lands + 0.03 else 0.0
        swing.append(v * (lift + body) * (0.45 + 0.55 * abs(flutter[i]) / peak))

    # Crinkles: short clicks while the paper bends, brightest mid-swing.
    crinkle = [0.0] * total
    for _ in range(70):
        t = random.uniform(0.02, lands - 0.05)
        at = int(t * RATE)
        size = random.uniform(0.15, 0.5) * math.sin(math.pi * t / lands)
        for k in range(int(0.004 * RATE)):
            if at + k < total:
                crinkle[at + k] += size * random.uniform(-1, 1) * math.exp(-k / (0.0008 * RATE))
    crinkle = band(crinkle, 1500, 6000)

    def norm(xs):
        m = max(abs(x) for x in xs) or 1.0
        return [x / m for x in xs]

    swing, crinkle = norm(swing), norm(crinkle)
    mix = [0.7 * a + 0.35 * b for a, b in zip(swing, crinkle)]
    # A small room: one early reflection.
    d = int(0.021 * RATE)
    mix = [v + (0.25 * mix[i - d] if i >= d else 0.0) for i, v in enumerate(mix)]
    fade = int(0.05 * RATE)
    mix = [v * min(1.0, (total - i) / fade) for i, v in enumerate(mix)]
    m = max(abs(v) for v in mix) or 1.0
    return [0.85 * v / m for v in mix]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    encode(OUT / "turn1.ogg", turn(1))
    encode(OUT / "turn2.ogg", turn(2, lands=0.74))


if __name__ == "__main__":
    main()
