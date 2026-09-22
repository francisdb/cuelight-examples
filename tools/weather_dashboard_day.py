#!/usr/bin/env python3
"""Write weather_dashboard's test driver: a day in two minutes.

    tools/weather_dashboard_day.py > weather_dashboard/test-driver.json

Every two seconds is 24 minutes of the day, starting at 04:00: the sky
goes night, dawn, day, dusk and night again, the sun moves along its arc,
the temperature follows the day and the conditions run from a clear night
over a sunny morning into rain and a thunderstorm, clearing up for a
sunset, then fog and snow. The forecast row and the hourly bars refresh
now and then. All of it is variables set by this script: the sky, the sun
position, the time, the readings and the forecast are host data, the show
only decides what they look like.
"""

import json
import math
import random

STEP = 2.0  # seconds of driver time
MINUTES_PER_STEP = 24
START = 4 * 60  # 04:00
SUNRISE, SUNSET = 7 * 60, 19 * 60 + 30

# (from minute of day, condition)
CONDITIONS = [
    (0, "sun"),
    (6 * 60, "partly"),
    (7 * 60 + 30, "sun"),
    (10 * 60, "partly"),
    (12 * 60, "cloud"),
    (13 * 60 + 30, "rain"),
    (15 * 60, "storm"),
    (16 * 60 + 30, "rain"),
    (18 * 60, "partly"),
    (19 * 60, "sun"),
    (21 * 60 + 30, "fog"),
    (23 * 60, "snow"),
]

# (minute of day, temperature) the day interpolates through.
TEMPERATURES = [(0, 3), (4 * 60, 2), (7 * 60, 4), (10 * 60, 11), (13 * 60, 16), (15 * 60, 13), (17 * 60, 12), (20 * 60, 9), (22 * 60, 4), (24 * 60, 0)]

FORECAST = [
    ("WED", "partly", 14, 6),
    ("THU", "rain", 11, 7),
    ("FRI", "storm", 12, 8),
    ("SAT", "sun", 15, 5),
    ("SUN", "snow", 3, -2),
]


def sky(minute):
    if minute < 5 * 60 + 30 or minute >= 20 * 60 + 30:
        return "night"
    if minute < 7 * 60:
        return "dawn"
    if minute >= 19 * 60:
        return "dusk"
    return "day"


def condition(minute):
    current = CONDITIONS[0][1]
    for start, name in CONDITIONS:
        if minute >= start:
            current = name
    return current


def temperature(minute):
    for (m0, t0), (m1, t1) in zip(TEMPERATURES, TEMPERATURES[1:]):
        if m0 <= minute <= m1:
            return t0 + (t1 - t0) * (minute - m0) / (m1 - m0)
    return TEMPERATURES[-1][1]


def sun(minute):
    """Where the sun is: along an arc by day, waiting behind the hills at
    its rising or setting spot otherwise. Never below the canvas: what
    hangs out of it would show in the player's letterbox."""
    if minute < SUNRISE:
        return 60, 670
    if minute > SUNSET:
        return 1220, 670
    f = (minute - SUNRISE) / (SUNSET - SUNRISE)
    return round(60 + f * 1160), round(670 - math.sin(math.pi * f) * 590)


def main():
    random.seed(11)
    steps = []
    wind, wind_dir = 12, "SW"
    forecast = list(FORECAST)
    for i in range(24 * 60 // MINUTES_PER_STEP):
        minute = (START + i * MINUTES_PER_STEP) % (24 * 60)
        cond = condition(minute)
        temp = temperature(minute) + random.uniform(-0.4, 0.4)
        values = {
            "time": f"{minute // 60:02d}:{minute % 60:02d}",
            "sky": sky(minute),
            "condition": cond,
            "temp": round(temp),
            "feels": round(temp - (2 if wind > 15 else 1)),
            "humidity": {"rain": 88, "storm": 92, "fog": 96, "snow": 85}.get(cond, 55 + (minute // 60) % 9 * 3),
        }
        values["sun_x"], values["sun_y"] = sun(minute)
        if i % 4 == 0:
            wind = max(3, min(42, wind + random.randint(-6, 8) + (10 if cond == "storm" else 0)))
            wind_dir = random.choice(["SW", "W", "NW", "S"]) if random.random() < 0.3 else wind_dir
        values["wind"], values["wind_dir"] = wind, wind_dir
        values["wind_deg"] = {"S": 180, "SW": 225, "W": 270, "NW": 315}[wind_dir]
        if i % 6 == 0:
            for h in range(8):
                values[f"h{h}"] = round(temperature((minute + (h + 1) * 60) % (24 * 60)) + random.uniform(-1, 1))
        if i == 0 or minute == 12 * 60:
            if minute == 12 * 60:
                forecast[1] = ("THU", "partly", 13, 6)
                forecast[4] = ("SUN", "cloud", 5, -1)
            for d, (name, c, hi, lo) in enumerate(forecast):
                values[f"d{d}_name"], values[f"d{d}_cond"] = name, c
                values[f"d{d}_hi"], values[f"d{d}_lo"] = f"{hi}°", f"{lo}°"
        if i == 0:
            values["city"], values["date"] = "GHENT", "Tuesday 22 September"
        steps.append({"set": values})
        steps.append({"wait": STEP})
    print(json.dumps({"loop": True, "steps": steps}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
