#!/usr/bin/env python3
"""Synthesize boardwalk's chimes.

    tools/boardwalk_sounds.py

An electromechanical game rings a chime for every score pulse: three
struck rods, high for tens, middle for hundreds and low for thousands.
Each is a rod's inharmonic partials dying away in a small wooden box,
here with a short reverb. chime_10.ogg, chime_100.ogg, chime_1000.ogg.

Mono at 22.05 kHz, encoded to Ogg Vorbis with ffmpeg. The rest of the
sounds are recordings, fetched by tools/boardwalk_fetch.sh.
"""

import math
import struct
import subprocess
import tempfile
import wave
from pathlib import Path

RATE = 22050
OUT = Path(__file__).resolve().parent.parent / "boardwalk" / "assets" / "sounds"


def encode(path, samples):
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        frames = b"".join(struct.pack("<h", int(max(-1.0, min(1.0, v)) * 32767)) for v in samples)
        with wave.open(tmp.name, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(RATE)
            w.writeframes(frames)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp.name, "-c:a", "libvorbis", "-q:a", "3",
                        "-map_metadata", "-1", str(path)], check=True)


def rod(frequency, seconds):
    """A struck metal rod: a free bar's partials (1, 2.76, 5.40, 8.93 times
    the fundamental), the higher ones dying faster, and a short knock
    where the hammer hits."""
    out = []
    partials = [(1.0, 1.0, 1.6), (2.756, 0.45, 4.0), (5.404, 0.2, 9.0), (8.933, 0.08, 16.0)]
    for i in range(int(RATE * seconds)):
        t = i / RATE
        attack = min(t / 0.001, 1.0)
        v = sum(a * math.sin(2 * math.pi * frequency * r * t) * math.exp(-t * d)
                for r, a, d in partials if frequency * r < RATE / 2)
        knock = 0.5 * math.exp(-t * 300) * math.sin(2 * math.pi * 3 * frequency * t)
        out.append(attack * (v + knock))
    return out


def box(samples, seconds):
    """The chime box: a few short reflections."""
    out = samples + [0.0] * int(RATE * seconds)
    for delay_ms, gain in [(7.3, 0.35), (11.9, 0.25), (17.1, 0.18), (23.7, 0.12)]:
        d = int(delay_ms * RATE / 1000)
        for i in range(len(out) - 1, d - 1, -1):
            out[i] += gain * out[i - d] * 0.6
    peak = max(abs(v) for v in out)
    n = len(out)
    return [0.8 * v / peak * min(1.0, (n - i) / (0.2 * RATE)) for i, v in enumerate(out)]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    # Three rods tuned a little apart from any scale, as the real ones are.
    for name, frequency in [("chime_10", 1318.0), ("chime_100", 1046.0), ("chime_1000", 784.0)]:
        encode(OUT / f"{name}.ogg", box(rod(frequency, 1.4), 0.2))


if __name__ == "__main__":
    main()
