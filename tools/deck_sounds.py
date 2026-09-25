#!/usr/bin/env python3
"""Synthesize the deck's sounds into deck/assets/sounds/.

    tools/deck_sounds.py

Ogg Vorbis, mono, made from sines so there is nothing to license, every
note above 300 Hz:

- slide.ogg: a soft wooden tick as a slide comes in, 0.25 seconds.
- coin.ogg: the classic two-note coin, B then E, 0.5 seconds.
- jackpot.ogg: a quick rising arpeggio with a shimmer on top, 1.2 seconds.
"""

import math
import struct
import subprocess
import tempfile
import wave
from pathlib import Path

RATE = 44100
OUT = Path(__file__).resolve().parent.parent / "deck/assets/sounds"


def write(name, samples):
    peak = max(1e-9, max(abs(s) for s in samples))
    frames = b"".join(struct.pack("<h", round(s / peak * 0.8 * 32767)) for s in samples)
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        with wave.open(tmp.name, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(RATE)
            w.writeframes(frames)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp.name, "-c:a", "libvorbis", "-q:a", "4",
                        "-map_metadata", "-1", "-fflags", "+bitexact", "-flags:a", "+bitexact",
                        str(OUT / f"{name}.ogg")], check=True)


def note(frequency, seconds, decay, partials=((1, 1.0),), attack=0.004):
    out = []
    for n in range(int(RATE * seconds)):
        t = n / RATE
        envelope = min(t / attack, 1.0) * math.exp(-t * decay)
        out.append(envelope * sum(a * math.sin(2 * math.pi * frequency * k * t) for k, a in partials))
    return out


def mix(seconds, *parts):
    out = [0.0] * int(RATE * seconds)
    for start, level, samples in parts:
        offset = int(start * RATE)
        for i, s in enumerate(samples[: len(out) - offset]):
            out[offset + i] += level * s
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    wood = ((1, 1.0), (2.76, 0.35), (5.4, 0.12))
    write("slide", mix(0.25, (0, 1.0, note(1320, 0.25, 38, wood)), (0.012, 0.5, note(1760, 0.2, 45, wood))))
    bright = ((1, 1.0), (2, 0.25), (3, 0.1))
    write("coin", mix(0.5, (0, 0.8, note(988, 0.09, 6, bright)), (0.08, 1.0, note(1319, 0.42, 7, bright))))
    arpeggio = [(i * 0.07, 0.9, note(f, 0.9, 5, bright)) for i, f in enumerate((784, 988, 1175, 1568, 1976))]
    shimmer = [(0.35 + i * 0.05, 0.25, note(f, 0.5, 9)) for i, f in enumerate((2637, 3136, 2637, 3520, 3136, 3951))]
    write("jackpot", mix(1.2, *arpeggio, *shimmer))
    for name in ("slide", "coin", "jackpot"):
        print(f"deck/assets/sounds/{name}.ogg: {(OUT / f'{name}.ogg').stat().st_size} bytes")


if __name__ == "__main__":
    main()
