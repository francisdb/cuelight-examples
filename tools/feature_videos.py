#!/usr/bin/env python3
"""Generate the clips of the feature examples under features/video/.

    tools/feature_videos.py

Drawn frame by frame and synthesized from sines, so there is nothing to
license, then encoded with ffmpeg as WebM (VP9 and Opus): 192x108 at 30
frames a second, mono sound, a few kilobytes a second. Every clip has a
soundtrack whose notes sit above 300 Hz. Each example gets its own copy
of the clips it uses, so a folder plays on its own.

- sweep.webm: 1.6 seconds of a bar sweeping left to right over eight
  marks that light as it passes, so how far a play has got can be read
  at a glance, over a tone rising an octave.
- orbit.webm: two seconds of a dot circling with a fading trail, over a
  soft pulsing chord. Both end where they began, so it loops without a
  seam.
- pop_c.webm, pop_e.webm, pop_g.webm: 0.8 seconds each of a shape
  popping in and out, an orange circle, a green triangle and a blue
  square, over a plucked C, E and G.

Needs Pillow, and ffmpeg with libvpx-vp9 and libopus.
"""

import math
import struct
import subprocess
import tempfile
import wave
from pathlib import Path

from PIL import Image, ImageDraw

W, H = 192, 108
FPS = 30
RATE = 48000
SS = 4  # drawn at four times the size and scaled down, for smooth edges

ROOT = Path(__file__).resolve().parent.parent / "features/video"
# Which examples use which clip; each example keeps its own copy, so a
# folder plays on its own.
USERS = {
    "sweep": ["video_layer", "retrigger"],
    "orbit": ["video_layer", "masked"],
    "pop_c": ["video_layer", "pick"],
    "pop_e": ["pick"],
    "pop_g": ["pick"],
}


def encode(name, frames, samples):
    with tempfile.TemporaryDirectory() as tmp:
        sound = Path(tmp) / "sound.wav"
        with wave.open(str(sound), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(RATE)
            peak = max(1e-9, max(abs(s) for s in samples))
            w.writeframes(b"".join(struct.pack("<h", round(s / peak * 0.9 * 32767)) for s in samples))
        out = Path(tmp) / f"{name}.webm"
        ffmpeg = subprocess.Popen(
            ["ffmpeg", "-v", "error", "-y",
             "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
             "-i", sound,
             "-c:v", "libvpx-vp9", "-crf", "40", "-b:v", "0", "-pix_fmt", "yuv420p",
             "-row-mt", "1", "-deadline", "good",
             "-c:a", "libopus", "-b:a", "24k", "-ac", "1",
             "-shortest", out],
            stdin=subprocess.PIPE,
        )
        for frame in frames:
            ffmpeg.stdin.write(frame.convert("RGB").tobytes())
        ffmpeg.stdin.close()
        if ffmpeg.wait():
            raise SystemExit(f"ffmpeg failed on {name}")
        data = out.read_bytes()
    for example in USERS[name]:
        folder = ROOT / example / "assets/videos"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{name}.webm").write_bytes(data)
    print(f"{name}.webm: {len(data)} bytes, for {', '.join(USERS[name])}")


def canvas(color):
    image = Image.new("RGB", (W * SS, H * SS), color)
    return image, ImageDraw.Draw(image)


def done(image):
    return image.resize((W, H), Image.LANCZOS)


def tone(seconds, pitch, partials=((1, 1.0),), envelope=lambda t: 1.0):
    """A sum of sines whose pitch may move: `pitch(t)` in Hz."""
    out, phase = [], 0.0
    for i in range(round(seconds * RATE)):
        t = i / RATE
        phase += 2 * math.pi * pitch(t) / RATE
        out.append(envelope(t) * sum(a * math.sin(phase * n) for n, a in partials))
    return out


def sweep():
    seconds = 1.6
    frames = []
    for i in range(round(seconds * FPS)):
        p = i / (seconds * FPS - 1)
        image, d = canvas((16, 42, 48))
        x = (12 + p * (W - 24)) * SS
        for m in range(8):
            mx = (12 + (m + 0.5) / 8 * (W - 24)) * SS
            lit = x >= mx
            d.rectangle([mx - 5 * SS, (H - 18) * SS, mx + 5 * SS, (H - 10) * SS],
                        fill=(250, 200, 80) if lit else (40, 76, 84))
        d.rectangle([x - 3 * SS, 10 * SS, x + 3 * SS, (H - 26) * SS], fill=(240, 250, 250))
        frames.append(done(image))
    samples = tone(seconds, lambda t: 523.25 * 2 ** (t / seconds),
                   ((1, 1.0), (2, 0.35), (3, 0.15)),
                   lambda t: min(1, t / 0.02) * min(1, (seconds - t) / 0.08))
    encode("sweep", frames, samples)


def orbit():
    seconds = 2.0
    frames = []
    count = round(seconds * FPS)
    for i in range(count):
        image, d = canvas((34, 22, 52))
        cx, cy, r = W / 2 * SS, H / 2 * SS, 32 * SS
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(70, 52, 96), width=2 * SS)
        for k in range(12, -1, -1):
            a = 2 * math.pi * ((i - k * 0.6) / count)
            x, y = cx + r * math.cos(a), cy + r * math.sin(a)
            size = (7 - k * 0.4) * SS
            shade = 1 - k / 13
            d.ellipse([x - size, y - size, x + size, y + size],
                      fill=(round(34 + 206 * shade), round(22 + 118 * shade), round(52 + 188 * shade)))
        frames.append(done(image))
    # Two pulses a second over whole cycles of every note: seamless.
    pulse = lambda t: 0.55 + 0.45 * math.cos(2 * math.pi * 2 * t)
    samples = [a + b for a, b in zip(tone(seconds, lambda t: 659.0, ((1, 1.0), (2, 0.2)), pulse),
                                      tone(seconds, lambda t: 988.0, ((1, 0.6),), pulse))]
    encode("orbit", frames, samples)


def pop(name, note, color, shape):
    seconds = 0.8
    frames = []
    for i in range(round(seconds * FPS)):
        t = i / FPS
        # In with an overshoot, hold, then out.
        if t < 0.25:
            u = t / 0.25
            s = 1 + 2.7 * (u - 1) ** 3 + 1.7 * (u - 1) ** 2
        elif t < 0.6:
            s = 1.0
        else:
            s = max(0.0, 1 - (t - 0.6) / 0.2)
        image, d = canvas((22, 24, 30))
        cx, cy, r = W / 2 * SS, H / 2 * SS, 34 * max(0.0, s) * SS
        if r < 1:
            pass
        elif shape == "circle":
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
        elif shape == "triangle":
            d.polygon([(cx, cy - r), (cx + r * 0.95, cy + r * 0.75), (cx - r * 0.95, cy + r * 0.75)], fill=color)
        else:
            q = r * 0.85
            d.rectangle([cx - q, cy - q, cx + q, cy + q], fill=color)
        frames.append(done(image))
    samples = tone(seconds, lambda t: note, ((1, 1.0), (2, 0.5), (3, 0.25), (4, 0.12)),
                   lambda t: min(1, t / 0.005) * math.exp(-t * 6))
    encode(name, frames, samples)


def main():
    sweep()
    orbit()
    pop("pop_c", 523.25, (245, 140, 50), "circle")
    pop("pop_e", 659.26, (80, 200, 110), "triangle")
    pop("pop_g", 783.99, (70, 130, 240), "square")


if __name__ == "__main__":
    main()
