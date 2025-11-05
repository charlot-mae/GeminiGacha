# bosses.py  (NO import from main!)
import random
import time

# ----------------------------------------------------------------------
# BOSS DATA
# ----------------------------------------------------------------------
BOSS_POOL = [
    ("Viktor",   "Rare",      45, 30, 300, 20, "Fire",  "Inferno Blast"),
    ("Selene",   "Rare",      40, 35, 320, 22, "Water", "Tidal Surge"),
    ("Darius",   "Rare",      50, 28, 280, 18, "Earth", "Rockfall"),
    ("Liora",    "Epic",      65, 45, 450, 25, "Wind",  "Tempest Fury"),
    ("Kael",     "Epic",      70, 40, 430, 27, "Fire",  "Hellfire Storm"),
    ("Nyra",     "Epic",      60, 50, 470, 24, "Water", "Abyssal Wave"),
    ("Thorne",   "Epic",      68, 42, 440, 26, "Earth", "Earthquake"),
    ("Zephyr",   "Legendary", 90, 55, 600, 30, "Wind",  "Cyclone Annihilation"),
    ("Ignis",    "Legendary", 95, 50, 580, 32, "Fire",  "Apocalypse Flame"),
    ("Maelis",   "Legendary", 85, 60, 620, 28, "Water", "Oceanic Cataclysm"),
    ("Grom",     "Legendary", 88, 58, 610, 29, "Earth", "Continental Crush"),
    ("Aether",   "Legendary", 92, 52, 590, 31, "Wind",  "Void Tempest"),
    ("Ragnar",   "Legendary",100, 48, 570, 33, "Fire",  "Doomsday Ember"),
]

def _make_boss(t):
    name, rarity, atk, def_, hp, spd, elem, spec = t
    return {
        "name": name, "rarity": rarity, "atk": atk, "defense": def_,
        "hp": hp, "max_hp": hp, "speed": spd, "element": elem,
        "special_name": spec, "special_cd": 0,
    }

# ----------------------------------------------------------------------
# PUBLIC API – called from main.py
# ----------------------------------------------------------------------
def maybe_unlock_cave(data):
    if "boss_defeat_counter" not in data:
        data["boss_defeat_counter"] = 0
        data["cave_unlocked"] = False
        data["active_boss"] = None
        data["boss_fight_state"] = None

    if data["boss_defeat_counter"] >= 5 and not data["cave_unlocked"]:
        data["cave_unlocked"] = True
        print("\n=== CAVE UNLOCKED! ===")
        print("Defeat 5 more monsters to open another boss gate.")
        input("Press Enter…")
        return True
    return False

def normal_victory_hook(data):
    data["boss_defeat_counter"] = data.get("boss_defeat_counter", 0) + 1
    maybe_unlock_cave(data)

def boss_menu(data, funcs):
    """
    funcs = {
        "girls_data": girls_data,
        "elemental_multiplier": elemental_multiplier,
        "get_girl_stats": get_girl_stats,
        "get_current_hp": get_current_hp,
        "is_available": is_available,
        "get_current_time": get_current_time,
        "save_game": save_game,
    }
    """
    if not data.get("cave_unlocked"):
        print("The cave is still sealed…")
        input("Press Enter…")
        return

    while True:
        print("\n=== DARK CAVE ===")
        if data.get("active_boss"):
            print(f"Ongoing: {data['active_boss']['name']} ({data['active_boss']['rarity']})")
            print("1. Resume boss fight")
        else:
            print("1. Enter cave (new boss)")
        print("2. Leave")
        ch = input("Choose: ").strip()
        if ch == "1":
            if data.get("active_boss"):
                _resume_boss_fight(data, funcs)
            else:
                _start_new_boss_fight(data, funcs)
            break
        if ch == "2":
            break

# ----------------------------------------------------------------------
# INTERNAL BATTLE LOGIC (no direct main imports)
# ----------------------------------------------------------------------
def _select_team(data, funcs):
    avail = [g for g, gd in data["inventory"].items() if funcs["is_available"](gd)]
    if not avail:
        print("No girls ready!")
        input("Press Enter…")
        return []
    selected = []
    while len(selected) < 3 and avail:
        print(f"\nTeam ({len(selected)}/3): {', '.join(selected) or '---'}")
        for i, g in enumerate(avail, 1):
            lv = data["inventory"][g]["level"]
            el = funcs["girls_data"][g]["element"]
            cl = funcs["girls_data"][g]["class"]
            print(f"{i}. {g} (Lv.{lv}) [{el}/{cl}]")
        print(f"{len(avail)+1}. Done")
        try:
            c = int(input("Pick: "))
            if c == len(avail) + 1:
                break
            if 1 <= c <= len(avail):
                selected.append(avail.pop(c - 1))
        except:
            pass
    if not selected:
        print("Need at least one girl!")
        input("Press Enter…")
        return []

    team = []
    for g in selected:
        gd = data["inventory"][g]
        stats = funcs["get_girl_stats"](g, gd["level"], data)
        team.append({
            "name": g,
            "stats": stats,
            "hp": funcs["get_current_hp"](g, gd, data),
            "max_hp": stats["hp"],
            "special_cd": 0,
            "defending": False,
            "shield": False,
        })
    return team

def _start_new_boss_fight(data, funcs):
    weights = [3 if r == "Rare" else 2 if r == "Epic" else 1 for _, r, *_ in BOSS_POOL]
    boss_t = random.choices(BOSS_POOL, weights=weights, k=1)[0]
    boss = _make_boss(boss_t)

    team = _select_team(data, funcs)
    if not team:
        return

    state = {"boss": boss, "team": team, "turn": 0}
    data["active_boss"] = boss
    data["boss_fight_state"] = state
    funcs["save_game"](data)

    _run_boss_turn(state, data, funcs)

def _resume_boss_fight(data, funcs):
    state = data.get("boss_fight_state")
    if not state:
        print("No saved fight!")
        input("Press Enter…")
        return
    _run_boss_turn(state, data, funcs)

def _run_boss_turn(state, data, funcs):
    boss = state["boss"]
    team = state["team"]
    turn = state["turn"]

    while boss["hp"] > 0 and any(g["hp"] > 0 for g in team):
        turn += 1
        state["turn"] = turn
        print(f"\n=== BOSS TURN {turn} ===")
        print(f"{boss['name']} HP: {int(boss['hp'])}/{boss['max_hp']}")

        # PLAYER PHASE
        for girl in team:
            if girl["hp"] <= 0:
                continue
            print(f"\n{girl['name']} (HP {int(girl['hp'])}/{girl['max_hp']})")
            skills = funcs["girls_data"][girl["name"]]["skills"]
            for i, s in enumerate(skills, 1):
                cd = girl["special_cd"] if i == 2 else 0
                print(f"{i}. {s}" + (f" (CD:{cd})" if cd else ""))

            try:
                ch = int(input("Skill: "))
                idx = ch - 1
                if idx == 1 and girl["special_cd"] > 0:
                    print("On CD → Basic Attack")
                    idx = 0
            except:
                idx = 0

            girl["defending"] = False
            if turn % 6 == 0:
                girl["shield"] = False

            if idx == 0:                     # BASIC
                base = girl["stats"]["attack"]
                multi = funcs["elemental_multiplier"](
                    funcs["girls_data"][girl["name"]]["element"], boss["element"]
                ) or 1.0
                dmg = max(1, int(base * multi) - boss["defense"])
                boss["hp"] -= dmg
                note = " (SUPER EFFECTIVE)" if multi > 1 else " (not very effective)" if multi < 1 else ""
                print(f"{girl['name']} deals {dmg} damage!{note}")
            elif idx == 1:                   # SPECIAL
                cls = funcs["girls_data"][girl["name"]]["class"]
                if cls == "Healer":
                    for g in team:
                        g["shield"] = True
                    girl["special_cd"] = 6
                    print(f"{girl['name']} casts GROUP SHIELD! (6-turn CD)")
                else:
                    base = int(girl["stats"]["attack"] * 2.5)
                    multi = funcs["elemental_multiplier"](
                        funcs["girls_data"][girl["name"]]["element"], boss["element"])
                    dmg = max(1, int(base * multi) - boss["defense"])
                    boss["hp"] -= dmg
                    girl["special_cd"] = 6
                    eff = "SUPER EFFECTIVE" if multi > 1 else "not very effective" if multi < 1 else ""
                    print(f"{girl['name']} → {dmg} dmg {eff}")
            else:                            # DEFEND
                girl["defending"] = True
                print(f"{girl['name']} DEFENDS!")

            girl["special_cd"] = max(0, girl["special_cd"] - 1)
            if boss["hp"] <= 0:
                break

        if boss["hp"] <= 0:
            break

        # BOSS PHASE
        print("\n--- BOSS TURN ---")
        boss["special_cd"] = max(0, boss["special_cd"] - 1)

        if boss["special_cd"] == 0:
            print(f"{boss['name']} unleashes {boss['special_name']}!")
            for g in team:
                if g["hp"] <= 0:
                    continue
                if g["defending"]:
                    print(f"  → {g['name']} blocked!")
                    continue
                if g["shield"]:
                    print(f"  → {g['name']}'s shield absorbed!")
                    g["shield"] = False
                    continue
                multi = funcs["elemental_multiplier"](boss["element"], funcs["girls_data"][g["name"]]["element"]) or 1.0
                dmg = max(1, int(boss["atk"] * 2 * multi) - g["stats"]["defense"]) 
                g["hp"] -= dmg
                note = " (SUPER EFFECTIVE)" if multi > 1 else " (not very effective)" if multi < 1 else ""
                print(f"  → {g['name']} takes {dmg}{note} ({int(g['hp'])} left)")
            boss["special_cd"] = 3
        else:
            alive = [g for g in team if g["hp"] > 0]
            if alive:
                tgt = random.choice(alive)
                if tgt["defending"]:
                    print(f"{boss['name']} attacks {tgt['name']} → BLOCKED")
                elif tgt["shield"]:
                    print(f"{boss['name']} hits {tgt['name']}'s shield → absorbed")
                    tgt["shield"] = False
                else:
                    multi = funcs["elemental_multiplier"](boss["element"], funcs["girls_data"][tgt["name"]]["element"]) or 1.0
                    dmg = max(1, int(boss["atk"] * multi) - tgt["stats"]["defense"])
                    tgt["hp"] -= dmg
                    note = " (SUPER EFFECTIVE)" if multi > 1 else " (not very effective)" if multi < 1 else ""
                    print(f"{boss['name']} hits {tgt['name']} for {dmg}{note} ({int(tgt['hp'])} left)")

        # SAVE AFTER EACH ROUND
        data["boss_fight_state"] = state
        funcs["save_game"](data)

        # ALLOW QUIT
        if input("\nContinue? (enter = yes, 'q' = quit & save): ").strip().lower() == 'q':
            print("Fight saved – return via the cave menu.")
            return
