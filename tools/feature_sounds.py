#!/usr/bin/env python3
"""Synthesize the sounds of the feature examples under features/sound/.

    tools/feature_sounds.py

WAV files, 44.1 kHz mono 16-bit, all made from sines and noise so there
is nothing to license. For audio_layers:

- music.wav: eight seconds of a plucked arpeggio over Am, F, C and G that
  loops without a seam: notes ringing past the end are mixed into the
  start. At 22.05 kHz, to keep the file small.
- zap.wav: 1.2 seconds of a tone sweeping down an octave, long enough for three
  zaps 400 ms apart to overlap.
- thunder.wav: 1.6 seconds of rumbling noise that rolls in and dies
  away, with a few cracks of brighter noise at the start.
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
# Half rate for the long music loop: half the file, and nothing in it
# comes near the 11 kHz that still leaves.
MUSIC_RATE = 22050


def write(path, samples, rate=RATE):
    frames = b"".join(struct.pack("<h", int(max(-1.0, min(1.0, s)) * 32767)) for s in samples)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
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


def midi(note):
    return 440.0 * 2 ** ((note - 69) / 12)


def pluck(frequency, seconds, decay, level, partials, rate=RATE):
    """A plucked note: a few harmonics, the higher ones dying sooner."""
    out = []
    for n in range(int(rate * seconds)):
        t = n / rate
        attack = min(t / 0.004, 1.0)
        value = sum(
            math.sin(2 * math.pi * frequency * k * t) * math.exp(-t * decay * k) / k
            for k in range(1, partials + 1)
        )
        out.append(level * attack * value)
    return out


def music():
    step = 0.25  # an eighth note at 120 bpm
    seconds = 32 * step  # four bars
    chords = [(57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62)]  # Am F C G
    pattern = [0, 1, 2, 3, 2, 1, 2, 3]  # indices into root, third, fifth, octave
    total = int(MUSIC_RATE * seconds)
    out = [0.0] * total

    def add(start, samples):
        # Wrapped round, so tails ringing past the end sound at the start
        # and the loop has no seam.
        offset = int(start * MUSIC_RATE)
        for i, v in enumerate(samples):
            out[(offset + i) % total] += v

    for bar, (root, third, fifth) in enumerate(chords):
        notes = [root + 12, third + 12, fifth + 12, root + 24]
        # The bass is low, so its upper harmonics carry it on small speakers.
        add(bar * 8 * step, pluck(midi(root - 12), 1.6, 2.5, 0.35, 6, MUSIC_RATE))
        for i, index in enumerate(pattern):
            add((bar * 8 + i) * step, pluck(midi(notes[index]), 0.9, 5.0, 0.22, 3, MUSIC_RATE))
    peak = max(abs(v) for v in out)
    return [0.6 * v / peak for v in out]


def zap():
    """A laser zap: a bright tone sweeping down from 1600 to 700 Hz. Long
    enough that a second one fired 400 ms later lands on top of it, and
    falling, so a restart is heard as the pitch jumping back up. It stays
    high throughout: overlapping tails are what tell overlap from
    restart, and small speakers drop anything low. Quiet enough that
    three at once do not clip."""
    seconds = 1.2
    out = []
    phase = 0.0
    for n in range(int(RATE * seconds)):
        t = n / RATE
        frequency = 1600.0 * (700.0 / 1600.0) ** (t / seconds)
        phase += 2 * math.pi * frequency / RATE
        envelope = min(t / 0.005, 1.0) * min((seconds - t) / 0.2, 1.0)
        out.append(0.28 * envelope * (math.sin(phase) + 0.3 * math.sin(3 * phase)))
    return out


def thunder():
    random.seed(9)
    seconds = 1.6
    # A few cracks in the first half second, each a burst of a few ms.
    cracks = sorted(random.uniform(0.0, 0.5) for _ in range(6))
    out = []
    low = 0.0
    for n in range(int(RATE * seconds)):
        t = n / RATE
        noise = random.uniform(-1, 1)
        # White noise through a crude one-pole low pass: a rumble, open
        # enough that small speakers still play some of it.
        low += (noise - low) * 0.06
        envelope = min(t / 0.15, 1.0) * math.exp(-(t - 0.15) * 2.2 if t > 0.15 else 0.0)
        # What the low pass took out: the crackle on top.
        crackle = sum(math.exp(-(t - c) * 120) for c in cracks if t >= c) * (noise - low)
        out.append(2.5 * low * envelope + 0.35 * crackle)
    peak = max(abs(v) for v in out)
    return [0.9 * v / peak for v in out]


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
        "audio_layers": [("music", music()), ("zap", zap()), ("thunder", thunder()), ("jingle", jingle())],
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
            write(out / f"{name}.wav", samples, MUSIC_RATE if name == "music" else RATE)


if __name__ == "__main__":
    main()
