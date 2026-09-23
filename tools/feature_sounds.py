#!/usr/bin/env python3
"""Synthesize the sounds of the feature examples under features/sound/.

    tools/feature_sounds.py

WAV files, 44.1 kHz mono 16-bit, all made from sines and noise so there
is nothing to license. For audio_layers:

- bed.wav: four seconds of a soft chord that loops without a seam, every
  partial a whole number of cycles long, with a slow swell.
- coin.wav: a quarter second blip that steps up a fourth.
- thunder.wav: 1.6 seconds of low, rumbling noise that rolls in and dies
  away.
- jingle.wav: a two second three-note motif for the attract scene, looped.

For pick, three takes of one knock on a woodblock, knock1.wav to
knock3.wav, a quarter second each. Real takes would differ less: these
are a C, an E and a G, so which one plays is easy to hear.
"""

import math
import random
import struct
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


def tone(frequency, seconds, attack, decay, level):
    out = []
    for n in range(int(RATE * seconds)):
        t = n / RATE
        envelope = min(t / attack, 1.0) * math.exp(-t * decay)
        out.append(level * envelope * math.sin(2 * math.pi * frequency * t))
    return out


def mix(*parts):
    length = max(len(p[1]) + int(p[0] * RATE) for p in parts)
    out = [0.0] * length
    for start, samples in parts:
        offset = int(start * RATE)
        for i, s in enumerate(samples):
            out[offset + i] += s
    return out


def bed():
    seconds = 4.0
    # Frequencies rounded so that each fits the loop a whole number of
    # times: no click at the seam.
    notes = [round(f * seconds) / seconds for f in (110.0, 164.81, 220.0, 277.18)]
    out = []
    for n in range(int(RATE * seconds)):
        t = n / RATE
        swell = 0.75 + 0.25 * math.sin(2 * math.pi * t / seconds)  # one cycle per loop
        value = sum(math.sin(2 * math.pi * f * t) / (i + 1.5) for i, f in enumerate(notes))
        out.append(0.22 * swell * value)
    return out


def coin():
    return mix((0.0, tone(1568.0, 0.1, 0.003, 12, 0.5)), (0.08, tone(2093.0, 0.2, 0.003, 10, 0.5)))


def thunder():
    random.seed(9)
    seconds = 1.6
    out = []
    low = 0.0
    for n in range(int(RATE * seconds)):
        t = n / RATE
        # White noise through a crude one-pole low pass: a rumble.
        low += (random.uniform(-1, 1) - low) * 0.02
        envelope = min(t / 0.15, 1.0) * math.exp(-(t - 0.15) * 2.2 if t > 0.15 else 0.0)
        out.append(4.5 * low * envelope)
    return out


def jingle():
    notes = [(0.0, 523.25), (0.33, 659.25), (0.66, 783.99), (1.0, 659.25)]
    parts = [(start, tone(f, 0.45, 0.005, 6, 0.4)) for start, f in notes]
    out = mix(*parts)
    return out + [0.0] * (int(RATE * 2.0) - len(out))


def knock(pitch, seed):
    """A knock on a woodblock: a tone and the inharmonic overtone wood
    has, both dying fast, and a click of noise on top for the strike.
    Pitched up where small speakers still play it, and normalized."""
    random.seed(seed)
    seconds = 0.25
    out = []
    for n in range(int(RATE * seconds)):
        t = n / RATE
        attack = min(t / 0.001, 1.0)
        body = attack * math.exp(-t * 30) * math.sin(2 * math.pi * pitch * t)
        overtone = 0.5 * attack * math.exp(-t * 70) * math.sin(2 * math.pi * pitch * 2.76 * t)
        strike = 0.6 * math.exp(-t * 500) * random.uniform(-1, 1)
        out.append(body + overtone + strike)
    peak = max(abs(v) for v in out)
    return [0.9 * v / peak for v in out]


def main():
    root = Path(__file__).resolve().parent.parent / "features" / "sound"
    examples = {
        "audio_layers": [("bed", bed()), ("coin", coin()), ("thunder", thunder()), ("jingle", jingle())],
        "pick": [
            ("knock1", knock(523.25, 1)),
            ("knock2", knock(659.25, 2)),
            ("knock3", knock(783.99, 3)),
        ],
    }
    for example, sounds in examples.items():
        out = root / example / "assets" / "sounds"
        out.mkdir(parents=True, exist_ok=True)
        for name, samples in sounds:
            write(out / f"{name}.wav", samples)


if __name__ == "__main__":
    main()
