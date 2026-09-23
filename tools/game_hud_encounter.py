#!/usr/bin/env python3
"""Write game_hud's test driver: a scripted encounter.

    tools/game_hud_encounter.py > game_hud/test-driver.json

The driver plays the game: it walks the hero towards the chapel, fights
a Bog Wraith with all six skills, drinks a potion when health runs low,
takes the loot, lights the last brazier, finishes the quest, levels up
and fights a second, weaker foe. It tells the HUD what happened the way
a game would, with a few variables and triggers. Everything the HUD then
does, the orbs, the cooldowns, the numbers, the banners and the sounds,
is the show's.

The encounter is written out rather than rolled, so the demo is the same
every run.
"""

import json

HP_MAX = 240
MANA_MAX = 160
XP_PER_LEVEL = 1000
MANA_REGEN = 2  # every half second

# Skill slot -> (name, mana cost). Damage and healing are in the script.
SKILLS = {1: ("strike", 0), 2: ("fireball", 30), 3: ("ward", 25), 4: ("heal", 35), 5: ("frost", 20), 6: ("potion", 0)}

# (time, what, argument)
ENCOUNTER = [
    (0.6, "turn", (20, 70, 3.0)),
    (3.4, "target", ("Bog Wraith", 1000)),
    (4.0, "cast", (1, 42, False)),
    (4.8, "cast", (2, 118, True)),
    (5.6, "cast", (1, 45, False)),
    (6.3, "hurt", 28),
    (7.0, "cast", (5, 76, False)),
    (7.7, "cast", (1, 39, False)),
    (8.4, "hurt", 34),
    (9.0, "cast", (3, 0, False)),
    (9.8, "cast", (1, 44, True)),
    (10.6, "cast", (2, 124, False)),
    (11.4, "hurt", 22),
    (12.0, "heal", (4, 64)),
    (12.8, "cast", (1, 41, False)),
    (13.6, "hurt", 46),
    (14.4, "cast", (5, 80, False)),
    (15.2, "hurt", 64),
    (15.9, "heal", (6, 90)),
    (16.6, "cast", (1, 44, False)),
    (17.4, "cast", (2, 125, True)),
    (18.2, "kill", (240, 35)),
    (20.0, "turn", (70, 150, 4.0)),
    (24.4, "objective", None),
    (25.8, "quest", 300),
    (29.0, "turn", (150, 110, 2.0)),
    (31.0, "target", ("Marsh Ghoul", 300)),
    (31.6, "cast", (1, 47, False)),
    (32.4, "cast", (5, 82, False)),
    (33.1, "hurt", 18),
    (33.8, "cast", (1, 43, True)),
    (34.6, "cast", (2, 131, False)),
    (35.4, "kill", (90, 12)),
]
END = 40.0


def main():
    state = {"hp": 196, "mana": MANA_MAX, "xp": 610, "level": 7, "gold": 1280,
             "target": "", "target_hp": 100, "damage": 0, "crit": "false",
             "healed": 0, "heading": 20, "braziers": 2, "loot": ""}
    foe_max = 1
    foe_hp = 0
    events = [(0.0, {"set": dict(state)})]
    spends = []

    def at(t, step):
        events.append((round(t, 3), step))

    def gain_xp(t, amount):
        state["xp"] += amount
        if state["xp"] >= XP_PER_LEVEL:
            # Fill the bar, then level up and start the next one.
            at(t, {"set": {"xp": XP_PER_LEVEL}})
            state["level"] += 1
            state["xp"] -= XP_PER_LEVEL
            at(t + 0.9, {"set": {"level": state["level"], "xp": state["xp"]}})
            at(t + 0.9, {"trigger": "level_up"})
        else:
            at(t, {"set": {"xp": state["xp"]}})

    for t, what, arg in ENCOUNTER:
        if what == "turn":
            start, end, seconds = arg
            steps = int(seconds / 0.25)
            for k in range(steps + 1):
                at(t + k * 0.25, {"set": {"heading": round(start + (end - start) * k / steps)}})
        elif what == "target":
            name, foe_max = arg
            foe_hp = foe_max
            at(t, {"set": {"target": name, "target_hp": 100}})
        elif what == "cast":
            slot, damage, crit = arg
            name, cost = SKILLS[slot]
            spends.append((round(t, 3), cost))
            at(t, {"trigger": f"skill_{slot}"})
            if damage:
                damage = damage * 2 if crit else damage
                foe_hp = max(0, foe_hp - damage)
                # A spell lands a moment after it is cast.
                land = t + (0.35 if name in ("fireball", "frost") else 0.12)
                at(land, {"set": {"damage": damage, "crit": "true" if crit else "false",
                                  "target_hp": round(100 * foe_hp / foe_max)}})
                at(land, {"trigger": "hit"})
        elif what == "hurt":
            state["hp"] = max(1, state["hp"] - arg)
            at(t, {"set": {"hp": state["hp"]}})
            at(t, {"trigger": "hurt"})
        elif what == "heal":
            slot, amount = arg
            name, cost = SKILLS[slot]
            spends.append((round(t, 3), cost))
            state["hp"] = min(HP_MAX, state["hp"] + amount)
            at(t, {"trigger": f"skill_{slot}"})
            at(t + 0.2, {"set": {"hp": state["hp"], "healed": amount}})
            at(t + 0.2, {"trigger": "healed"})
        elif what == "kill":
            xp, gold = arg
            at(t, {"set": {"target_hp": 0}})
            at(t, {"trigger": "enemy_die"})
            at(t + 1.2, {"set": {"target": ""}})
            state["gold"] += gold
            at(t + 1.0, {"set": {"gold": state["gold"], "loot": f"+{gold} gold"}})
            at(t + 1.0, {"trigger": "loot"})
            gain_xp(t + 0.4, xp)
        elif what == "objective":
            state["braziers"] = 3
            at(t, {"set": {"braziers": 3}})
            at(t, {"trigger": "objective"})
        elif what == "quest":
            at(t, {"trigger": "quest_complete"})
            gain_xp(t + 0.6, arg)

    # Mana: spent by casts, and coming back a little every half second,
    # as a game ticks it.
    mana = MANA_MAX
    ticks = [round(0.5 * k, 3) for k in range(1, int((END - 1) / 0.5))]
    for t, cost in sorted(spends + [(tick, None) for tick in ticks], key=lambda e: (e[0], e[1] is None)):
        if cost is not None:
            mana -= cost
        elif mana < MANA_MAX:
            mana = min(MANA_MAX, mana + MANA_REGEN)
        else:
            continue
        at(t, {"set": {"mana": mana}})

    # Back to the start before the loop comes round.
    at(END - 0.6, {"set": {"hp": 196, "mana": MANA_MAX, "xp": 610, "level": 7, "gold": 1280,
                            "braziers": 2, "heading": 20}})

    events.sort(key=lambda e: e[0])
    steps = []
    now = 0.0
    for t, step in events:
        if t > now:
            steps.append({"wait": round(t - now, 3)})
            now = t
        if "set" in step and steps and "set" in steps[-1]:
            steps[-1]["set"].update(step["set"])
        else:
            steps.append(step)
    steps.append({"wait": round(END - now, 3)})
    print(json.dumps({"loop": True, "steps": steps}, indent=2))


if __name__ == "__main__":
    main()
