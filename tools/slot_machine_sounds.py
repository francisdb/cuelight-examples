#!/usr/bin/env python3
"""Synthesize the sounds of slot_machine.

    tools/slot_machine_sounds.py slot_machine/assets/sounds

Four WAV files, 44.1 kHz mono 16-bit, all made from sines, noise and
envelopes, so there is nothing to license:

- whir.wav: half a second of the reels turning, a rattle of clicks over a
  low hum, made to loop without a seam while the wheels are moving.
- clunk.wav: a reel dropping onto its stop, a short knock with a click on
  top; one plays as each wheel lands.
- win.wav: a rising three note arpeggio with a shimmer, for a line that pays.
- lose.wav: two low notes falling away, for one that does not.
"""

import math
import random
import struct
import sys
import wave
from pathlib import Path

RATE = 44100


def write(path, samples):
    frames = b"".join(struct.pack("<h", int(max(-1.0, min(1.0, s)) * 32767)) for s in samples)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(frames)


def tone(frequency, seconds, attack, decay, level, start=0.0):
    """A sine with a fast attack and an exponential decay, at an offset."""
    out = [0.0] * int(RATE * (start + seconds))
    begin = int(RATE * start)
    for n in range(int(RATE * seconds)):
        t = n / RATE
        envelope = min(t / attack, 1.0) * math.exp(-t * decay)
        out[begin + n] = level * envelope * math.sin(2 * math.pi * frequency * t)
    return out


def mix(*parts):
    out = [0.0] * max(len(p) for p in parts)
    for part in parts:
        for i, s in enumerate(part):
            out[i] += s
    return out


def whir(seconds=0.5, clicks=9):
    """A hum with evenly spaced clicks: the ring passing its detent.

    Both the hum and the clicks fit the loop a whole number of times, so
    the file joins to itself without a click at the seam.
    """
    random.seed(17)
    hum_cycles = round(70 * seconds)          # a whole number of cycles
    frequency = hum_cycles / seconds
    period = seconds / clicks
    out = []
    for n in range(int(RATE * seconds)):
        t = n / RATE
        value = 0.12 * math.sin(2 * math.pi * frequency * t)
        value += 0.05 * math.sin(2 * math.pi * frequency * 2 * t)
        # each click is a short burst of filtered noise, one per period
        age = t % period
        if age < 0.012:
            value += 0.5 * math.exp(-age * 420) * random.uniform(-1, 1)
        out.append(value)
    return out


def clunk():
    random.seed(5)
    seconds = 0.28
    out = []
    low = 0.0
    for n in range(int(RATE * seconds)):
        t = n / RATE
        low += (random.uniform(-1, 1) - low) * 0.06
        body = 0.8 * low * math.exp(-t * 26)
        knock = 0.5 * math.sin(2 * math.pi * 120 * t) * math.exp(-t * 30)
        click = 0.35 * random.uniform(-1, 1) * math.exp(-t * 500)
        out.append(body + knock + click)
    return out


def win():
    notes = [(0.0, 523.25), (0.12, 659.25), (0.24, 783.99), (0.36, 1046.5)]
    parts = [tone(f, 1.1 - start, 0.004, 4.5, 0.32, start) for start, f in notes]
    # a shimmer on top of the last note
    parts.append(tone(2093.0, 0.7, 0.01, 6.0, 0.10, 0.36))
    return mix(*parts)


def lose():
    return mix(
        tone(196.0, 0.5, 0.006, 6.0, 0.35, 0.0),
        tone(155.6, 0.8, 0.006, 5.0, 0.35, 0.18),
    )


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    for name, samples in (("whir", whir()), ("clunk", clunk()), ("win", win()), ("lose", lose())):
        write(out / f"{name}.wav", samples)
        print(out / f"{name}.wav")


if __name__ == "__main__":
    main()
