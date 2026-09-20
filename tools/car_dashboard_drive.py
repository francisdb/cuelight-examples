#!/usr/bin/env python3
"""Write car_dashboard's test-driver.json: a short simulated drive.

A driver script sets variables instantly, so a smooth speedometer needs
many small steps. This plays the host: a crude car model sampled ten
times a second, writing only the variables that changed.

    tools/car_dashboard_drive.py car_dashboard/test-driver.json
"""

import json
import sys

TICK = 0.1
IDLE = 850
RPM_PER_KMH = [0, 110, 65, 45, 34, 27, 22]  # per gear
SHIFT = {"comfort": (3200, 1500), "sport": (6900, 3600)}  # up, down


class Drive:
    def __init__(self):
        self.steps = []
        self.sent = {}
        self.state = {
            "speed": 0.0,
            "rpm": 0.0,
            "gear": 0,
            "mode": "comfort",
            "fuel": 0.24,
            "temp": 50.0,
            "trip": 0.0,
            "odo": 48215.0,
        }
        self.lamps = {"lamp_oil": 0, "lamp_battery": 0, "lamp_check": 0, "lamp_fuel": 0, "lamp_beam": 0}

    def variables(self):
        s = self.state
        return {
            "speed": round(s["speed"]),
            "rpm": round(s["rpm"], -1),
            "gear": s["gear"],
            "mode": s["mode"],
            "fuel": round(s["fuel"], 3),
            "temp": round(s["temp"]),
            "range": round(s["fuel"] * 700, -1),
            "trip": round(s["trip"], 1),
            "odo": int(s["odo"]),
            **self.lamps,
        }

    def emit(self):
        changed = {k: v for k, v in self.variables().items() if self.sent.get(k) != v}
        if changed:
            self.sent.update(changed)
            self.steps.append({"set": {k: int(v) if isinstance(v, float) and v.is_integer() else v for k, v in changed.items()}})

    def trigger(self, name):
        self.steps.append({"trigger": name})

    def wait(self, seconds):
        self.emit()
        if self.steps and "wait" in self.steps[-1]:
            self.steps[-1]["wait"] = round(self.steps[-1]["wait"] + seconds, 3)
        else:
            self.steps.append({"wait": round(seconds, 3)})

    def run(self, seconds, target=None, accel=0.0):
        """Advance the car model, moving the speed towards `target`."""
        s = self.state
        for _ in range(round(seconds / TICK)):
            if target is not None:
                pull = accel * (1.0 if target < s["speed"] else 1.4 / (0.4 + max(s["gear"], 1)))
                step = pull * TICK
                s["speed"] += max(-step, min(step, target - s["speed"]))
            if s["gear"] > 0:
                up, down = SHIFT[s["mode"]]
                wanted = s["speed"] * RPM_PER_KMH[s["gear"]]
                if wanted > up and s["gear"] < 6:
                    s["gear"] += 1
                elif wanted < down and s["gear"] > 1:
                    s["gear"] -= 1
            wanted = max(IDLE, s["speed"] * RPM_PER_KMH[s["gear"]]) if s["rpm"] or s["gear"] else s["rpm"]
            s["rpm"] += (wanted - s["rpm"]) * 0.45
            km = s["speed"] * TICK / 3600
            s["trip"] += km
            s["odo"] += km
            s["fuel"] = max(0.0, s["fuel"] - km * 0.06 - s["rpm"] * 2e-8)
            s["temp"] += ((104 if s["mode"] == "sport" else 90) - s["temp"]) * 0.006
            self.lamps["lamp_fuel"] = int(s["fuel"] < 0.15)
            self.wait(TICK)


def main():
    d = Drive()
    # Key on: lamp test and gauge sweep, then the engine catches.
    d.lamps.update(lamp_oil=1, lamp_battery=1)
    d.emit()
    d.trigger("ignition")
    d.wait(2.2)
    d.state["rpm"] = 1400.0
    d.run(0.8)
    d.lamps.update(lamp_oil=0, lamp_battery=0)
    d.run(1.0)

    d.state["gear"] = 1
    d.run(9.0, target=100, accel=22)
    d.trigger("turn_left")
    d.run(3.0, target=100, accel=22)
    d.lamps["lamp_beam"] = 1
    d.run(5.0, target=130, accel=22)

    d.state["mode"] = "sport"
    d.run(9.0, target=205, accel=34)
    d.run(2.0, target=205, accel=34)
    d.lamps["lamp_beam"] = 0
    d.run(5.0, target=70, accel=30)

    d.state["mode"] = "comfort"
    d.trigger("turn_right")
    d.run(4.0, target=50, accel=12)
    d.lamps["lamp_check"] = 1
    d.run(5.0, target=0, accel=14)
    d.state["gear"] = 0
    d.trigger("hazard")
    d.run(4.0)

    # Key off.
    d.state["rpm"] = 0.0
    d.lamps.update(lamp_check=0, lamp_fuel=0)
    d.state.update(fuel=0.24, trip=0.0, temp=50.0)
    d.wait(2.0)

    with open(sys.argv[1], "w") as out:
        out.write('{\n  "loop": true,\n  "steps": [\n')
        out.write(",\n".join("    " + json.dumps(step) for step in d.steps))
        out.write("\n  ]\n}\n")


if __name__ == "__main__":
    main()
