#!/usr/bin/env python3
"""Write boardwalk's test driver: a two-player game, as an EM table's
script would drive its backglass.

    tools/boardwalk_game.py > boardwalk/test-driver.json

What the table sends is what a VPX EM script sends the B2S server, with
the same ids (B2SSetData id, value):

- `data_1` to `data_9`: the letters of BOARDWALK spelled so far.
- `data_40`: the bonus, 0 to 16, shown on the Ferris wheel.
- `data_30` player up, `data_31` players in the game, `data_32` ball in
  play, `data_33` tilt, `data_34` match (100 for 00), `data_35` game
  over, `data_36` shoot again, `data_41` special.
- `score_1` to `score_4` and `credits` (B2SSetScorePlayer,
  B2SSetCredits), padded with zeros for the reels.

Scores come the way an EM machine makes them: in pulses. Every pulse
adds 10, 100 or 1000, steps a reel and rings that chime (`chime_10`,
`chime_100`, `chime_1000`). A drained ball collects its bonus one bulb
at a time, a thousand each. Spelling BOARDWALK wins a special.

The game is written out rather than played at random, so the demo is
the same every run, and it starts from the scores and credits the game
ends with, so the loop joins up.
"""

import json

PULSE = 0.13      # seconds between score pulses, as a score motor turns
BONUS_PULSE = 0.16
PLAYERS = 2
BALLS = 3
LETTERS = 9
LETTER_POINTS = 500

# What each ball does, in order: a number scores that many points in
# pulses; "L" lights the next letter (and scores 500); "B" advances the
# bonus (and scores 100); "shoot_again" and "tilt" are what they say.
PLAY = {
    (1, 1): [10, "B", 10, "L", 100, "B", 1000, 10, "B", "L", 10],
    (2, 1): [100, "B", 10, 1000, "L", "B", 10, 10, "L", 200],
    (1, 2): [10, "B", 1000, "L", 10, "shoot_again", "B", "B", 100, "L", 10],
    (1, 2, "again"): [10, "B", 300, 1000, 10],
    (2, 2): [100, "B", 10, "L", "B", 500, "tilt"],
    (1, 3): [1000, "B", 10, "L", "B", 100, "B", "L", 10, 10],
    (2, 3): [10, "B", 1000, 100, "B", 500, 10, "B", 1000, 10, 300],
}


def padded(score, width=5):
    return f"{score:0{width}d}"


def game(start_scores, start_credits):
    """Play the game; return the steps and where it ends."""
    t = 0.0
    events = []
    score = [0] * (PLAYERS + 1)
    credits = start_credits
    letters = 0

    def at(step):
        events.append((round(t, 3), step))

    def wait(seconds):
        nonlocal t
        t += seconds

    def pulses(player, points):
        for unit in (1000, 100, 10):
            while points >= unit:
                points -= unit
                score[player] += unit
                at({"set": {f"score_{player}": padded(score[player])}})
                at({"trigger": f"chime_{unit}"})
                wait(PULSE)

    at({"set": {"gi": 1, "credits": padded(credits, 2), "data_35": 1, "data_31": 0, "data_30": 0,
                "data_32": 0, "data_33": 0, "data_36": 0, "data_41": 0, "data_40": 0,
                **{f"data_{i}": 0 for i in range(1, LETTERS + 1)},
                **{f"score_{p}": padded(start_scores[p] if p <= PLAYERS else 0) for p in range(1, 5)}}})
    wait(6.0)  # attract: the bulbs and the title chase

    # Two presses of the start button.
    for players in range(1, PLAYERS + 1):
        credits -= 1
        at({"set": {"credits": padded(credits, 2), "data_31": players}})
        at({"trigger": "start"})
        at({"trigger": "reel_step"})
        wait(0.7)
    at({"set": {"data_35": 0, "data_34": 0}})
    # The reels reset to zero, stepping forward, with the clatter of it.
    at({"set": {f"score_{p}": padded(0) for p in range(1, 5)}})
    for _ in range(8):
        at({"trigger": "reel_step"})
        wait(0.07)
    wait(0.6)

    for ball in range(1, BALLS + 1):
        for player in range(1, PLAYERS + 1):
            turns = [PLAY[(player, ball)]]
            if (player, ball, "again") in PLAY:
                turns.append(PLAY[(player, ball, "again")])
            for moves in turns:
                bonus = 0
                at({"set": {"data_30": player, "data_32": ball, "data_33": 0, "data_40": 0}})
                wait(0.9)
                tilted = False
                for move in moves:
                    if move == "shoot_again":
                        at({"set": {"data_36": 1}})
                        wait(0.4)
                    elif move == "tilt":
                        at({"set": {"data_33": 1, "data_40": 0}})
                        tilted = True
                        wait(2.0)
                        break
                    elif move == "B":
                        bonus = min(16, bonus + 1)
                        at({"set": {"data_40": bonus}})
                        pulses(player, 100)
                        wait(0.25)
                    elif move == "L":
                        letters += 1
                        at({"set": {f"data_{letters}": 1}})
                        pulses(player, LETTER_POINTS)
                        wait(0.3)
                        if letters == LETTERS:
                            credits += 1
                            at({"set": {"data_41": 1, "credits": padded(credits, 2)}})
                            at({"trigger": "knocker"})
                            wait(0.8)
                    else:
                        pulses(player, move)
                        wait(0.35)
                wait(0.8)
                # The ball drains: the bonus is collected bulb by bulb.
                if not tilted:
                    while bonus > 0:
                        bonus -= 1
                        at({"set": {"data_40": bonus}})
                        pulses(player, 1000)
                        wait(BONUS_PULSE - PULSE)
                    wait(0.3)
                at({"set": {"data_36": 0, "data_41": 0, "data_33": 0}})
                wait(0.5)

    # Game over, and the match: it lands on the second player's score.
    match = score[2] % 100
    at({"set": {"data_30": 0, "data_32": 0, "data_35": 1}})
    wait(1.0)
    at({"set": {"data_34": match or 100}})
    wait(0.8)
    if any(score[p] % 100 == match for p in range(1, PLAYERS + 1)):
        credits += 1
        at({"set": {"credits": padded(credits, 2)}})
        at({"trigger": "knocker"})
    wait(5.0)
    return events, t, score, credits


def main():
    # Play once to learn how the game ends, then again starting from it.
    _, _, final, _ = game([0] * (PLAYERS + 1), 2)
    events, end, score, credits = game(final, 2)
    assert credits == 2, f"credits end at {credits}, the loop would jump"
    assert score == final, "the scores must end where the demo starts"
    # The attract lamps before the game show the match of the game before.
    events[0][1]["set"]["data_34"] = final[2] % 100 or 100

    steps = []
    now = 0.0
    for when, step in events:
        if when > now:
            steps.append({"wait": round(when - now, 3)})
            now = when
        if "set" in step and steps and "set" in steps[-1]:
            steps[-1]["set"].update(step["set"])
        else:
            steps.append(step)
    steps.append({"wait": round(end - now, 3)})
    print(json.dumps({"loop": True, "steps": steps}, indent=2))


if __name__ == "__main__":
    main()
