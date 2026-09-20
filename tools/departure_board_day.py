#!/usr/bin/env python3
"""Write departure_board's test-driver.json: two hours at a small airport.

This plays the host: it keeps the schedule, decides what each of the six
rows shows and what a flight's status is, and tells the show. One minute
on the board takes half a second. When a flight leaves the board its row
stays empty for a moment, then the rows below move up one by one.

    tools/departure_board_day.py departure_board/test-driver.json
"""

import json
import sys

ROWS = 6
SECONDS_PER_MINUTE = 0.5
START, END = 6 * 60 + 10, 8 * 60 + 10

# (scheduled, destination, flight, gate, delay in minutes or "cancelled")
FLIGHTS = [
    (6 * 60 + 25, "LISBON", "CL 204", "A 3", 0),
    (6 * 60 + 40, "OSLO", "CL 871", "B12", 0),
    (6 * 60 + 50, "MARRAKECH", "QX 118", "A 7", 35),
    (7 * 60 + 5, "VIENNA", "CL 560", "B 4", 0),
    (7 * 60 + 15, "REYKJAVIK", "NV 33", "C 1", "cancelled"),
    (7 * 60 + 20, "ATHENS", "QX 402", "A 5", 0),
    (7 * 60 + 35, "EDINBURGH", "CL 919", "B 9", 0),
    (7 * 60 + 50, "PORTO", "CL 226", "A 2", 0),
    (8 * 60 + 0, "HELSINKI", "NV 47", "C 3", 0),
    (8 * 60 + 15, "VALENCIA", "QX 731", "B 6", 0),
    (8 * 60 + 30, "TALLINN", "NV 52", "C 2", 0),
    (8 * 60 + 40, "DUBROVNIK", "CL 385", "A 8", 0),
    (8 * 60 + 55, "LJUBLJANA", "QX 640", "B 2", 0),
    (9 * 60 + 5, "BERGEN", "NV 61", "C 4", 0),
]


def clock(minutes):
    return f"{minutes // 60:02d}.{minutes % 60:02d}"


def row(flight, now):
    """What a row shows for `flight`, or None once it is off the board."""
    scheduled, destination, number, gate, delay = flight
    if delay == "cancelled":
        if now > scheduled + 5:
            return None
        return clock(scheduled), destination, number, "", "CANCELLED"
    # A delay is announced 25 minutes ahead; the row then shows the new time.
    late = delay and now >= scheduled - 25
    departure = scheduled + delay if late else scheduled
    left = departure - now
    if left < -3:
        return None
    if left <= 0:
        status = "DEPARTED"
    elif left <= 4:
        status = "CLOSING"
    elif left <= 20:
        status = "BOARDING"
    elif late:
        status = "DELAYED"
    elif left <= 40:
        status = "GATE OPEN"
    else:
        status = "ON TIME"
    return clock(departure), destination, number, gate, status


FIELDS = ("time", "dest", "flight", "gate", "status")
BLANK = ("", "", "", "", "")
GAP_SECONDS = 1.0  # how long a departed flight's row stays empty
MOVE_SECONDS = 0.25  # between two rows moving up


def main():
    steps = []
    sent = {}

    def show(index, fields, flicker=True):
        """Put `fields` in a row; flicker it when that changed anything."""
        values = {f"{name}_{index + 1}": value for name, value in zip(FIELDS, fields)}
        changed = {k: v for k, v in values.items() if sent.get(k) != v}
        if changed:
            sent.update(changed)
            steps.append({"set": changed})
            if flicker:
                steps.append({"trigger": f"row_{index + 1}"})

    # The board is in schedule order; a delayed flight keeps its place.
    waiting = list(FLIGHTS)
    rows = [waiting.pop(0) for _ in range(ROWS)]
    for index, flight in enumerate(rows):
        show(index, row(flight, START), flicker=False)
    steps.append({"trigger": "refresh"})

    for now in range(START, END + 1):
        steps.append({"set": {"clock": clock(now)}})
        for index, flight in enumerate(rows):
            if flight is not None and row(flight, now) is not None:
                show(index, row(flight, now))
        # A flight that is gone leaves an empty row for a moment, then the
        # rows below move up one by one and the next flight joins at the end.
        while any(f is not None and row(f, now) is None for f in rows):
            gone = next(i for i, f in enumerate(rows) if f is not None and row(f, now) is None)
            show(gone, BLANK)
            steps.append({"wait": GAP_SECONDS})
            for index in range(gone, ROWS - 1):
                rows[index] = rows[index + 1]
                show(index + 1, BLANK, flicker=False)
                show(index, row(rows[index], now) if rows[index] else BLANK)
                steps.append({"wait": MOVE_SECONDS})
            rows[ROWS - 1] = waiting.pop(0) if waiting else None
            show(ROWS - 1, row(rows[ROWS - 1], now) if rows[ROWS - 1] else BLANK)
        steps.append({"wait": SECONDS_PER_MINUTE})

    with open(sys.argv[1], "w") as out:
        out.write('{\n  "loop": true,\n  "steps": [\n')
        out.write(",\n".join("    " + json.dumps(step) for step in steps))
        out.write("\n  ]\n}\n")


if __name__ == "__main__":
    main()
