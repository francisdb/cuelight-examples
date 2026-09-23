#!/usr/bin/env python3
"""Synthesize car_dashboard's turn signal relay: click.ogg.

    tools/car_dashboard_sounds.py car_dashboard/assets/sounds

0.7 seconds, mono, Ogg Vorbis (written as WAV and encoded with ffmpeg): a click at 0 and a softer one at
0.35 s, the relay pulling in and dropping out, so one play covers one
blink of the arrows and a repeat of four covers the four blinks.
"""

import math
import random
import struct
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

RATE = 44100


def click(t, level):
    # A damped high tone with a touch of noise: a small relay.
    if t < 0:
        return 0.0
    envelope = math.exp(-t * 220)
    return level * envelope * (0.7 * math.sin(2 * math.pi * 2400 * t) + 0.3 * random.uniform(-1, 1))


def main():
    random.seed(4)
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    samples = []
    for n in range(int(RATE * 0.7)):
        t = n / RATE
        value = click(t, 0.8) + click(t - 0.35, 0.45)
        samples.append(struct.pack("<h", int(max(-1.0, min(1.0, value)) * 32767)))
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        with wave.open(tmp.name, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(RATE)
            w.writeframes(b"".join(samples))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp.name, "-c:a", "libvorbis", "-q:a", "4",
                        "-map_metadata", "-1", "-fflags", "+bitexact", "-flags:a", "+bitexact", str(out / "click.ogg")], check=True)


if __name__ == "__main__":
    main()
