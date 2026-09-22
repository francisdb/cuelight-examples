#!/usr/bin/env python3
"""Write slot_machine's test driver: a run of rounds, some paying, most not.

    tools/slot_machine_rounds.py > slot_machine/test-driver.json

Each round is the host's job: take the bet, fire `spin`, say which symbol
each reel lands on, wait for the last one to stop, then fire `win` or
`lose` and settle the credits. The show does the rest: the wheels spin
and stop one after another, the reels whir and clunk, and a paying line
flashes the cabinet.

The rounds are written out here rather than drawn at random, so the demo
is the same every time: three misses, a pair of cherries, a miss, three
bells, a near miss on sevens, and three sevens for the jackpot.
"""

import json

# The symbols on the ring, by the character that names them.
SYMBOLS = "CLOPGBA7"
NAMES = {"C": "cherry", "L": "lemon", "O": "orange", "P": "plum",
         "G": "grapes", "B": "bell", "A": "bar", "7": "seven"}

# What each line of three pays, times the bet.
PAYS = {"777": 100, "BBB": 20, "AAA": 15, "CCC": 10}
PAIR_PAYS = 2  # two cherries on the line

BET = 5
LAST_REEL_STOPS = 5.0   # the third wheel has settled back onto its stop
# Lines may repeat a symbol in the same place as the line before: the
# reels hear the `spin` trigger, so a wheel asked for what it already
# carries still takes its turns and lands back on it. The first round
# and the jackpot both do that on purpose.
START = "CCC"
ROUNDS = ["CLO", "PGB", "A7L", "CCP", "OLG", "BBB", "77L", "777"]


def pays(line):
    if line in PAYS:
        return PAYS[line] * BET
    if line.count("C") >= 2:
        return PAIR_PAYS * BET
    return 0


def main():
    steps = []
    credits = 250
    steps.append({"set": {"credits": f"{credits:05d}", "bet": BET, "win": "0000",
                          "reel_1": START[0], "reel_2": START[1], "reel_3": START[2]}})
    steps.append({"wait": 1.5})
    for line in ROUNDS:
        credits -= BET
        steps.append({"set": {"credits": f"{credits:05d}", "win": "0000"}})
        steps.append({"set": {"reel_1": line[0], "reel_2": line[1], "reel_3": line[2]}})
        steps.append({"trigger": "spin"})
        steps.append({"wait": LAST_REEL_STOPS + 0.2})
        won = pays(line)
        if won:
            credits += won
            steps.append({"trigger": "win"})
            steps.append({"set": {"win": f"{won:04d}", "credits": f"{credits:05d}"}})
            steps.append({"wait": 3.0})
        else:
            steps.append({"trigger": "lose"})
            steps.append({"wait": 1.4})
    print(json.dumps({"loop": True, "steps": steps}, indent=2))


if __name__ == "__main__":
    main()
