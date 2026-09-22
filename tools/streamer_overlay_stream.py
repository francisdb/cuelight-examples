#!/usr/bin/env python3
"""Write streamer_overlay's test driver: a short stream in about 80 seconds.

    tools/streamer_overlay_stream.py > streamer_overlay/test-driver.json

The overlay starts on its starting-soon screen with a countdown, goes
live, and then gets what a stream gets: the viewer count drifting, follow
alerts, a lower third for the host, a subscription, a raid that brings a
crowd, a run of follows that reaches the follower goal, a short break and
one more alert before it all loops. All of it is variables set and
triggers fired by this script; the show decides what each one looks like.
"""

import json
import random

FOLLOWS = [
    ("pixel_pete", "welcome aboard"),
    ("moss_and_fern", "thanks for the follow"),
    ("kattegat_kid", "welcome to the channel"),
    ("late_night_lu", "glad you are here"),
    ("dmd_enjoyer", "one of us now"),
    ("okonomi_yaki", "thanks for following"),
    ("tarmac_tess", "welcome, take a seat"),
    ("bram_the_brave", "welcome in"),
]


class Stream:
    def __init__(self):
        self.steps = []
        self.viewers = 0
        self.followers = 0
        self.follow_at = 0

    def set(self, **variables):
        self.steps.append({"set": variables})

    def trigger(self, name):
        self.steps.append({"trigger": name})

    def wait(self, seconds):
        """Wait, while the viewer count drifts a little every two seconds."""
        while seconds > 0:
            step = min(2.0, seconds)
            self.steps.append({"wait": step})
            seconds -= step
            if step == 2.0:
                self.viewers = max(1, self.viewers + random.randint(-3, 5))
                self.set(viewers=self.viewers)

    def follow(self):
        name, detail = FOLLOWS[self.follow_at % len(FOLLOWS)]
        self.follow_at += 1
        self.followers += 1
        self.set(alert_kind="follow", alert_name=name, alert_detail=detail, followers=self.followers)
        self.trigger("alert")

    def alert(self, kind, name, detail):
        self.set(alert_kind=kind, alert_name=name, alert_detail=detail)
        self.trigger("alert")

    def lower_third(self, name, title):
        self.set(lt_name=name, lt_title=title)
        self.trigger("lower_third")


def main():
    random.seed(3)
    s = Stream()
    s.viewers, s.followers = 84, 992
    s.set(viewers=s.viewers, followers=s.followers, countdown=5)
    s.trigger("starting_soon")
    for n in range(5, 0, -1):
        s.set(countdown=n)
        s.steps.append({"wait": 1.0})
    s.trigger("live")
    s.wait(1.5)
    s.follow()
    s.wait(1.5)
    s.lower_third("SOMATIK", "Any% backlog speedrun, day 12")
    s.wait(8)
    s.alert("sub", "lena_plays", "Tier 1, 3 months in a row")
    s.wait(7)
    s.follow()
    s.wait(6)
    s.alert("raid", "gizmo_tv", "with 128 viewers")
    s.viewers += 128
    s.set(viewers=s.viewers)
    s.wait(6)
    # The raid brings follows; the goal is reached on the last one.
    for _ in range(6):
        s.follow()
        s.wait(2.5)
    s.wait(2)
    s.lower_third("1,000 FOLLOWERS", "thank you all, next stop 1,500")
    s.wait(9)
    s.trigger("brb")
    s.wait(6)
    s.trigger("live")
    s.wait(2)
    s.alert("sub", "orbital_ollie", "gifted 5 subs to the chat")
    s.wait(6)
    print(json.dumps({"loop": True, "steps": s.steps}, indent=2))


if __name__ == "__main__":
    main()
