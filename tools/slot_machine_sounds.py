#!/usr/bin/env python3
"""Synthesize the sounds of slot_machine.

    tools/slot_machine_sounds.py slot_machine/assets/sounds

WAV files, 44.1 kHz mono 16-bit, all made from sines, noise and
envelopes, so there is nothing to license:

- spin_1.wav, spin_2.wav, spin_3.wav: one wheel running down, one file
  per reel. Each is as long as that reel's spin and slows the way the
  reel does, so the rattle thins out into separate ticks as the wheel
  arrives. The timings are read out of the show rather than written
  here, so a reel and its sound cannot drift apart.
- clunk.wav: a reel dropping onto its stop, a short knock with a click on
  top; one plays as each wheel lands.
- win.wav: a rising three note arpeggio with a shimmer, for a line that pays.
- lose.wav: two low notes falling away, for one that does not.

Needs nothing outside the standard library.
"""

import json
import math
import random
import struct
import sys
import wave
from pathlib import Path

RATE = 44100
SHOW = Path(__file__).resolve().parent.parent / "slot_machine" / "show.json"


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


def normalize(samples, peak=0.9):
    loudest = max(abs(s) for s in samples) or 1.0
    return [s * peak / loudest for s in samples]


def reels(show=SHOW):
    """Every reel row the show spins, in order: (name, duration, turns,
    symbols). The sound has to follow the wheel, so it reads the wheel."""
    found = []

    def walk(layers):
        for layer in layers:
            reel = layer.get("display", {}).get("reel")
            if reel and "turns" in reel:
                found.append((layer["name"], reel["duration"], reel["turns"],
                              len(reel["charset"])))
            walk(layer.get("children", []))

    walk(json.loads(show.read_text())["layers"])
    return found


def detent(seconds=0.012, seed=1):
    """One detent passing: a wooden tick, not a snare.

    The same take serves every symbol, and that is the point. A reel at
    speed passes thirty symbols a second, far too fast to hear apart, so
    what the ear gets is the waveform those ticks make together: identical
    ticks thirty a second are a pitched buzz that glides down as the wheel
    slows, which is a machine; a fresh noise burst each time is a hiss,
    which is not. White noise is rolled off into a knock and given a short
    ring, the sound of a pawl on a metal star.
    """
    random.seed(seed)
    low, out = 0.0, []
    for n in range(int(RATE * seconds)):
        t = n / RATE
        low += (random.uniform(-1, 1) - low) * 0.25
        knock = 2.2 * low * math.exp(-t * 300)
        ring = 0.5 * math.sin(2 * math.pi * 820 * t) * math.exp(-t * 340)
        out.append(knock + ring)
    loudest = max(abs(v) for v in out) or 1.0
    return [v / loudest for v in out]


def spin(duration, turns, symbols, seed=0, kick=False):
    """A wheel thrown hard and left to run down against its brake.

    The reel moves `turns` whole revolutions plus wherever it lands, on a
    `quad_out` ease, so after a fraction `u` of its spin it has travelled
    `journey * (1 - (1 - u)^2)` symbols and is still moving at
    `2 * journey * (1 - u) / duration` symbols a second, and it ticks as
    symbols pass, so the ticks are that curve heard: a rattle at the
    throw thinning out into single ticks as it arrives. The bearing
    rumble under them follows the same speed and dies with it, and is
    kept well under the ticks: level with them it is only hiss.

    Every symbol ticks, the same tick each time, because the wheel is in
    sight: the symbols the ear counts as the reel arrives have to be the
    symbols the eye sees pass the line. Thirty a second at the throw is
    not a rate anyone counts, and that is fine; it fuses into a buzz an
    octave and a half below the ring, and that buzz falls in pitch with
    the wheel until it comes apart into ticks. Leaving symbols out to
    keep the rate countable costs the sync and sounds ragged.

    The levels are fixed rather than normalized: three of these play at
    once, and each has to know how loud it is against the others and
    against the clunk.

    One wheel carries the kicker as well: the handle flings all three at
    once, so that throw is one sound, not three on the same sample.
    """
    random.seed(seed)
    take = detent()
    # Where it lands is the host's business and changes every round; half
    # a ring is the average, and a symbol either way is inaudible.
    journey = turns * symbols + symbols / 2
    total = int(RATE * duration)
    out = [0.0] * (total + int(RATE * 0.06))
    rumble = 0.0
    passed = 0
    for n in range(total):
        t = n / RATE
        u = t / duration
        speed = 1.0 - u                      # fraction of the throw's speed
        rumble += (random.uniform(-1, 1) - rumble) * (0.008 + 0.025 * speed)
        out[n] += 0.18 * speed * speed * rumble
        out[n] += 0.06 * speed * math.sin(2 * math.pi * (40 + 70 * speed) * t)
        symbol = int(journey * (1 - speed * speed))
        if symbol > passed:
            passed = symbol
            level = 0.15 + 0.22 * u
            for m, v in enumerate(take):
                out[n + m] += level * v
    if kick:
        # The kicker is a heavy thing let go, not a hit: no crack on top.
        for n in range(int(RATE * 0.09)):
            t = n / RATE
            rumble += (random.uniform(-1, 1) - rumble) * 0.04
            out[n] += 0.35 * rumble * math.exp(-t * 40)
            out[n] += 0.18 * math.sin(2 * math.pi * 74 * t) * min(t / 0.004, 1.0) * math.exp(-t * 26)
    # ease the very first samples in, so the file does not begin on a step
    for n in range(int(RATE * 0.008)):
        out[n] *= n / (RATE * 0.008)
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
    sounds = [(f"spin_{i}", spin(duration, turns, symbols, seed=i, kick=i == 1))
              for i, (_, duration, turns, symbols) in enumerate(reels(), start=1)]
    sounds += [("clunk", clunk()), ("win", win()), ("lose", lose())]
    for name, samples in sounds:
        write(out / f"{name}.wav", samples)
        print(out / f"{name}.wav")


if __name__ == "__main__":
    main()
