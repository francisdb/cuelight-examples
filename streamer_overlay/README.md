# streamer_overlay

A live stream overlay on a 1920x1080 canvas: alerts that pop in with a
chime, a lower third for the host, a follower goal bar, a live badge with
the viewer count, a webcam frame, and a starting-soon and a be-right-back
screen. It sits on a stand-in for the game capture; in a real setup the
host renders the show over the capture instead.

| Part | How it works |
| --- | --- |
| Alerts | one group with `opacity` 0 and a `pop` timeline on the `alert` trigger that drops it in with `back_out` and takes it out again; when the timeline ends the group falls back to its base opacity, so it needs no trigger to hide |
| Alert kinds | `alert_kind` is a text variable: a mapped `text` binding turns it into the headline, a mapped `frame` binding picks the icon from a sprite sheet (heart, star, bolt) |
| The flash | a circle filled with a radial gradient, lavender fading to nothing at its rim, drawn with `"blend": "add"` and scaled up around its centre while it fades, so it adds light to the footage instead of covering it |
| The chime | an `audio` layer on the same `alert` trigger as the timelines; a new alert restarts it |
| Lower third | a group with a `clip` rect and, inside it, a panel that slides in and out on `lower_third`; the clip is what makes it appear from the edge instead of over the footage. Name and title are `text` bindings on `lt_name` and `lt_title` |
| Follower goal | a bar inside a clipped group: its `x` is bound to `followers` with `scale` 0.48 (480 pixels for 1,000 followers) and a `transition`, so it grows smoothly. The count is a `text` binding with the `thousands` format and the same transition, so it counts up |
| Goal reached | bindings with `"threshold": 1000`: 0 until the last follower and 1 at 1,000, so a gold bar and a `GOAL REACHED` label light up; the plain label takes the same threshold through `scale` -1 and `offset` 1, so it goes out |
| Viewer count | a `text` binding with a slow `transition`: the driver posts a new count every two seconds, the display rolls there |
| Live badge | a blinking dot, an `autoplay`, `loop` timeline with a `step` key |
| Starting soon, be right back | `scenes` entered by the `starting_soon` and `brb` triggers, painted on top of the overlay; `live` is the empty first scene. The countdown is a `text` binding, the loading bar a looping timeline in a clipped group, the title breathes with a looping opacity timeline |

It needs cuelight `main` with blend modes and audio layers.

## Running

```sh
cd ../../cuelight
cargo run -p cuelight-player -- ../cuelight-examples/streamer_overlay
```

`test-driver.json` is picked up automatically and plays a short stream in
about 75 seconds: a countdown, going live, a first follow, the host's
lower third, a subscription, a raid that brings a crowd, a run of follows
that reaches the goal, a break and one more alert before it loops. The
script lives in
[`tools/streamer_overlay_stream.py`](../tools/streamer_overlay_stream.py);
the show itself is written by hand. You can also drive it from the
player's prompt: `alert_kind=raid`, `alert_name=someone`, then `alert`.

The chime plays in the native player only: the web player does not play
sound yet, so the website shows the alerts silently.

## Assets

Everything under `assets/` is committed and free to redistribute. Licenses
were checked at the linked sources on 2026-09-20; the license texts that
have to travel with the files are in [`licenses/`](licenses/).

| Asset | Origin | License |
| --- | --- | --- |
| `footage.png`, `alert_icons.png`, `sounds/chime.ogg` | Made for this show, drawn and synthesized by [`tools/streamer_overlay_assets.py`](../tools/streamer_overlay_assets.py) | MIT, as this repository |
| `fonts/Oxanium-Bold.ttf`, `fonts/Oxanium-SemiBold.ttf` | [Oxanium](https://github.com/sevmeyer/oxanium) by The Oxanium Project Authors, the unmodified static files from [`fonts/ttf`](https://github.com/sevmeyer/oxanium/tree/a8f39e0c71186190027a093e9001459410192d1e/fonts/ttf). Its digits all have the same width, so the counts keep their place while they change | [OFL-1.1](licenses/Oxanium-OFL.txt), no reserved font name |

The names in the driver are made up.

## What would make it better

- A transparent output: an overlay wants an alpha channel under OBS
  (a transparent window, or Spout, Syphon or NDI texture sharing), so the
  footage layer could go. The show format already takes a `#RRGGBBAA`
  background.
- Rounded rectangles, or paths: every panel here has square corners.
- `scale` inherited by group children: the alert card cannot pop by
  scaling as a whole, so it drops in instead.
- A drop shadow or blur, as a layer effect or an output pass: overlays
  lift off the footage with them.
- Text measured by the engine: the viewer count and its label are placed
  by hand, a pill that fits its text needs the text's width.
- Sound in the web player, so the chime reaches the website.
