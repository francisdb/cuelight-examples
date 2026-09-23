#!/usr/bin/env python3
"""Synthesize the magic of the game_hud show.

    tools/game_hud_sounds.py

The physical sounds (a blade, armour, blows, coins, a bell) are
recordings, fetched by tools/game_hud_fetch.sh. What no recording has is
made here from sines and noise, each in layers and put in a small room
with a reverb, so it has a tail instead of stopping dead:

- fireball.ogg: a rush of air that swells and brightens, with crackle.
- frost.ogg: glassy chimes tumbling down over an icy hiss.
- ward.ogg: a bright ping, then a shimmering chord that swells.
- heal.ogg: a rising arpeggio of soft bells over an airy swell.
- ignite.ogg: a brazier catching: a soft whump and a crackle of flame.
- potion.ogg: a cork, then a few gulps.
- dissolve.ogg: the wraith coming apart: a breathy rush that sinks and
  thins out, with no pitch to it, under its weapon and body falling.
- level_up.ogg: a fanfare of bells, ringing out.

Everything sits above 400 Hz, where small speakers still play it. Mono
at 22.05 kHz, encoded to Ogg Vorbis with ffmpeg, which keeps a reverb
tail cheap.
"""

import math
import random
import struct
import subprocess
import tempfile
import wave
from pathlib import Path

RATE = 22050
OUT = Path(__file__).resolve().parent.parent / "game_hud" / "assets" / "sounds"


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


def silence(seconds):
    return [0.0] * int(RATE * seconds)


def mix(length, *parts):
    out = silence(length)
    for start, samples, level in parts:
        offset = int(start * RATE)
        for i, s in enumerate(samples):
            if offset + i < len(out):
                out[offset + i] += level * s
    return out


def normalize(samples, level):
    peak = max(abs(s) for s in samples) or 1.0
    return [level * s / peak for s in samples]


def fade_out(samples, seconds):
    n = int(seconds * RATE)
    return [s * min(1.0, (len(samples) - i) / n) for i, s in enumerate(samples)]


def reverb(samples, seconds, wet):
    """A small Schroeder room: four combs in parallel, two allpasses in
    series, and a tail of `seconds` added after the dry sound."""
    dry = samples + silence(seconds)
    n = len(dry)
    out = [0.0] * n
    for delay_ms, feedback in [(29.7, 0.80), (37.1, 0.78), (41.1, 0.76), (43.7, 0.74)]:
        d = int(delay_ms * RATE / 1000)
        buf = [0.0] * n
        damp = 0.0
        for i in range(n):
            back = buf[i - d] if i >= d else 0.0
            damp = back * 0.6 + damp * 0.4  # the walls soak up the highs
            buf[i] = dry[i] + damp * feedback
            out[i] += buf[i] * 0.25
    for delay_ms, g in [(5.0, 0.7), (1.7, 0.7)]:
        d = int(delay_ms * RATE / 1000)
        buf = [0.0] * n
        res = [0.0] * n
        for i in range(n):
            back = buf[i - d] if i >= d else 0.0
            buf[i] = out[i] + g * back
            res[i] = back - g * buf[i]
        out = res
    return fade_out([dry[i] * (1 - wet) + out[i] * wet for i in range(n)], min(0.4, seconds))


def tone(frequency, seconds, attack, decay, harmonics=(1.0,), glide=1.0, vibrato=0.0):
    """A tone that may glide to frequency * glide and waver."""
    out = []
    phase = 0.0
    for i in range(int(RATE * seconds)):
        t = i / RATE
        f = frequency * glide ** (t / seconds) * (1 + vibrato * math.sin(2 * math.pi * 6 * t))
        phase += 2 * math.pi * f / RATE
        envelope = min(t / attack, 1.0) * math.exp(-t * decay)
        out.append(envelope * sum(a * math.sin(k * phase) for k, a in enumerate(harmonics, 1) if f * k < RATE / 2))
    return out


def bell(frequency, seconds, decay):
    """A struck bell: partials at a bell's ratios, the high ones dying first."""
    out = []
    partials = [(1.0, 1.0), (2.0, 0.5), (2.76, 0.35), (5.4, 0.15)]
    for i in range(int(RATE * seconds)):
        t = i / RATE
        attack = min(t / 0.003, 1.0)
        out.append(attack * sum(a * math.sin(2 * math.pi * frequency * r * t) * math.exp(-t * decay * r)
                                for r, a in partials if frequency * r < RATE / 2))
    return out


def noise(seconds, seed, cutoff_from, cutoff_to, envelope):
    """Noise through a band that moves: a one-pole low pass whose cutoff
    goes from cutoff_from to cutoff_to Hz, minus a low pass at a fifth of
    it, so the band stays narrow. envelope(t) shapes the level."""
    random.seed(seed)
    out = []
    low = high = 0.0
    total = int(RATE * seconds)
    for i in range(total):
        t = i / RATE
        c = cutoff_from * (cutoff_to / cutoff_from) ** (i / total)
        a = 1 - math.exp(-2 * math.pi * c / RATE)
        b = 1 - math.exp(-2 * math.pi * c / 5 / RATE)
        v = random.uniform(-1, 1)
        low += (v - low) * a
        high += (v - high) * b
        out.append((low - high) * envelope(t))
    return out


def crackle(seconds, seed, rate, level_at):
    random.seed(seed)
    out = silence(seconds)
    for i in range(len(out)):
        if random.random() < rate / RATE:
            size = random.uniform(0.3, 1.0) * level_at(i / RATE)
            for k in range(int(0.004 * RATE)):
                if i + k < len(out):
                    out[i + k] += size * random.uniform(-1, 1) * math.exp(-k / (0.001 * RATE))
    return out


def fireball():
    whoosh = noise(1.0, 4, 500, 3000, lambda t: math.sin(math.pi * min(1.0, t / 1.0)) ** 1.5)
    roar = noise(1.0, 5, 700, 1400, lambda t: math.sin(math.pi * min(1.0, t / 1.0)) ** 2)
    sparks = crackle(1.0, 6, 60, lambda t: math.sin(math.pi * min(1.0, t)))
    return normalize(reverb(mix(1.0, (0, whoosh, 1.0), (0, roar, 0.7), (0, sparks, 0.5)), 0.6, 0.3), 0.85)


def frost():
    notes = [3136.0, 2637.0, 2349.3, 1975.5, 1568.0, 1318.5]
    chimes = [(i * 0.06, bell(f, 0.7, 6), 0.6) for i, f in enumerate(notes)]
    hiss = noise(1.0, 9, 5000, 3000, lambda t: math.exp(-t * 3))
    return normalize(reverb(mix(1.0, *chimes, (0, hiss, 0.35)), 1.0, 0.45), 0.8)


def ward():
    ping = bell(2637.0, 0.5, 9)
    chord = [(0.05, tone(f, 1.1, 0.35, 1.8, (1.0, 0.3), vibrato=0.004), 0.5) for f in (880.0, 1108.7, 1318.5, 1760.0)]
    air = noise(1.1, 12, 3000, 6000, lambda t: math.sin(math.pi * min(1.0, t / 1.1)) * 0.5)
    return normalize(reverb(mix(1.2, (0, ping, 0.8), *chord, (0, air, 0.3)), 1.0, 0.4), 0.75)


def heal():
    notes = [(0.0, 784.0), (0.09, 987.8), (0.18, 1174.7), (0.27, 1568.0), (0.36, 1975.5)]
    bells = [(s, bell(f, 1.0, 3.5), 0.6) for s, f in notes]
    swell = noise(1.2, 14, 2000, 5000, lambda t: math.sin(math.pi * min(1.0, t / 1.2)) * 0.6)
    return normalize(reverb(mix(1.3, *bells, (0, swell, 0.4)), 1.2, 0.45), 0.8)


def ignite():
    whump = noise(0.5, 15, 400, 1500, lambda t: min(1.0, t / 0.03) * math.exp(-t * 7))
    flame = noise(1.2, 16, 900, 2400, lambda t: min(1.0, t / 0.1) * math.exp(-t * 1.6))
    sparks = crackle(1.2, 17, 40, lambda t: math.exp(-t * 1.5))
    return normalize(reverb(mix(1.2, (0, whump, 1.0), (0.05, flame, 0.6), (0.05, sparks, 0.7)), 0.5, 0.25), 0.85)


def potion():
    cork = noise(0.05, 18, 1500, 800, lambda t: math.exp(-t * 90))
    pop = tone(900, 0.06, 0.001, 50, (1.0, 0.4), glide=0.6)
    gulps = [(0.25 + k * 0.17, tone(f, 0.1, 0.005, 22, (1.0, 0.5, 0.2), glide=1.5), 0.8)
             for k, f in enumerate([520, 600, 560, 660])]
    return normalize(reverb(mix(1.0, (0, cork, 0.8), (0, pop, 0.8), *gulps), 0.3, 0.2), 0.8)


def dissolve():
    # Two bands of noise sinking at different speeds, so the rush has a
    # shape but no note: a voice without a pitch sounds like wind, a pitch
    # sounds like a synthesizer.
    rush = noise(1.4, 19, 3200, 700, lambda t: min(1.0, t / 0.04) * math.exp(-t * 2.2))
    hollow = noise(1.4, 21, 1800, 500, lambda t: min(1.0, t / 0.15) * math.exp(-t * 1.6))
    breath = noise(0.6, 22, 5000, 2500, lambda t: min(1.0, t / 0.01) * math.exp(-t * 9))
    return normalize(reverb(mix(1.4, (0, rush, 1.0), (0, hollow, 0.8), (0, breath, 0.5)), 1.1, 0.5), 0.8)


def level_up():
    notes = [(0.0, 523.25), (0.11, 659.25), (0.22, 783.99), (0.33, 1046.5), (0.55, 1318.5), (0.55, 1568.0), (0.55, 2093.0)]
    bells = [(s, bell(f, 1.6, 2.2), 0.5) for s, f in notes]
    shimmer = noise(1.8, 20, 3000, 7000, lambda t: min(1.0, t / 0.6) * math.exp(-t * 1.2) * 0.5)
    return normalize(reverb(mix(2.0, *bells, (0.5, shimmer, 0.35)), 1.4, 0.4), 0.85)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    sounds = {
        "fireball": fireball(), "frost": frost(), "ward": ward(), "heal": heal(),
        "ignite": ignite(), "potion": potion(), "dissolve": dissolve(), "level_up": level_up(),
    }
    for name, samples in sounds.items():
        encode(OUT / f"{name}.ogg", samples)


if __name__ == "__main__":
    main()
