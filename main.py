import random
import json
import os
import time
from shop import show_shop  # shop.py must be in same directory
from bosses import boss_menu, normal_victory_hook

# Elemental advantages: (attacker, defender) -> multiplier
ELEMENTAL_ADVANTAGES = {
    ("Fire", "Wind"): 1.5,
    ("Wind", "Earth"): 1.5,
    ("Earth", "Water"): 1.5,
    ("Water", "Fire"): 1.5,
    ("Wind", "Fire"): 0.5,
    ("Earth", "Wind"): 0.5,
    ("Water", "Earth"): 0.5,
    ("Fire", "Water"): 0.5,
}

def elemental_multiplier(attacker_elem, defender_elem):
    return ELEMENTAL_ADVANTAGES.get((attacker_elem, defender_elem), 1.0)

# Girl Classes
class GirlClass:
    HEALER = "Healer"
    ATTACKER = "Attacker"
    LEADER = "Leader"
    MORALE = "Morale"
    TANK = "Tank"

# Full girls data with class
girls_data = {
    "Tama": {"rarity": "Common", "base_attack": 10, "base_defense": 8, "base_hp": 100, "base_speed": 12, 
             "catchline": "I am the jewel that lights your path!", "skills": ["Basic Attack", "Jewel Slash", "Defend"], 
             "element": "Earth", "class": GirlClass.ATTACKER},
    "Houseki": {"rarity": "Common", "base_attack": 12, "base_defense": 10, "base_hp": 110, "base_speed": 10, 
                "catchline": "Treasures await in my sparkling gaze!", "skills": ["Basic Attack", "Gem Burst", "Defend"], 
                "element": "Earth", "class": GirlClass.ATTACKER},
    "Ri": {"rarity": "Common", "base_attack": 9, "base_defense": 9, "base_hp": 105, "base_speed": 11, 
           "catchline": "Clear as glass, sharp as my will!", "skills": ["Basic Attack", "Crystal Shard", "Defend"], 
           "element": "Earth", "class": GirlClass.TANK},
    "Rin": {"rarity": "Common", "base_attack": 11, "base_defense": 7, "base_hp": 95, "base_speed": 13, 
            "catchline": "A gem of rarity in your collection!", "skills": ["Basic Attack", "Jade Spark", "Defend"], 
            "element": "Earth", "class": GirlClass.MORALE},
    "Hishouseki": {"rarity": "Common", "base_attack": 10, "base_defense": 9, "base_hp": 100, "base_speed": 11, 
                   "catchline": "Malachite transform, evolve with me!", "skills": ["Basic Attack", "Malachite Strike", "Defend"], 
                   "element": "Earth", "class": GirlClass.ATTACKER},
    "Kohaku-iro": {"rarity": "Common", "base_attack": 11, "base_defense": 10, "base_hp": 105, "base_speed": 12, 
                   "catchline": "Amber hue, warm embrace!", "skills": ["Basic Attack", "Amber Glow", "Defend"], 
                   "element": "Fire", "class": GirlClass.HEALER},
    "Tamaki": {"rarity": "Common", "base_attack": 9, "base_defense": 11, "base_hp": 110, "base_speed": 10, 
               "catchline": "Jewel tree, roots of power!", "skills": ["Basic Attack", "Jade Bind", "Defend"], 
               "element": "Earth", "class": GirlClass.TANK},
    "Ryu": {"rarity": "Uncommon", "base_attack": 15, "base_defense": 12, "base_hp": 120, "base_speed": 14, 
            "catchline": "Precious stone, unbreakable bond!", "skills": ["Basic Attack", "Lapis Bond", "Defend"], 
            "element": "Water", "class": GirlClass.LEADER},
    "Riko": {"rarity": "Uncommon", "base_attack": 14, "base_defense": 13, "base_hp": 115, "base_speed": 12, 
             "catchline": "Child of glass, reflecting your dreams!", "skills": ["Basic Attack", "Crystal Mirror", "Defend"], 
             "element": "Water", "class": GirlClass.MORALE},
    "Kotouseki": {"rarity": "Uncommon", "base_attack": 16, "base_defense": 11, "base_hp": 125, "base_speed": 13, 
                 "catchline": "Music in stone, harmony in battle!", "skills": ["Basic Attack", "Jade Wave", "Defend"], 
                 "element": "Water", "class": GirlClass.ATTACKER},
    "Kohaku": {"rarity": "Uncommon", "base_attack": 13, "base_defense": 14, "base_hp": 118, "base_speed": 11, 
               "catchline": "Amber warmth, eternal flame within!", "skills": ["Basic Attack", "Amber Burst", "Defend"], 
               "element": "Fire", "class": GirlClass.ATTACKER},
    "Seiyou": {"rarity": "Uncommon", "base_attack": 17, "base_defense": 15, "base_hp": 130, "base_speed": 15, 
               "catchline": "Turquoise fortune, luck by my side!", "skills": ["Basic Attack", "Turquoise Luck", "Defend"], 
               "element": "Water", "class": GirlClass.LEADER},
    "Hekigyoku": {"rarity": "Uncommon", "base_attack": 16, "base_defense": 14, "base_hp": 125, "base_speed": 13, 
                  "catchline": "Beryl healing, mending wounds!", "skills": ["Basic Attack", "Beryl Mend", "Defend"], 
                  "element": "Water", "class": GirlClass.HEALER},
    "Sango": {"rarity": "Rare", "base_attack": 20, "base_defense": 16, "base_hp": 140, "base_speed": 15, 
              "catchline": "Coral waves crash with my power!", "skills": ["Basic Attack", "Coral Crash", "Defend"], 
              "element": "Fire", "class": GirlClass.ATTACKER},
    "Suigyoku": {"rarity": "Rare", "base_attack": 18, "base_defense": 18, "base_hp": 135, "base_speed": 16, 
                 "catchline": "Jade purity, guardian of the pure!", "skills": ["Basic Attack", "Jade Guard", "Defend"], 
                 "element": "Fire", "class": GirlClass.TANK},
    "Kougyoku": {"rarity": "Rare", "base_attack": 22, "base_defense": 15, "base_hp": 130, "base_speed": 17, 
                 "catchline": "Ruby passion, igniting victory!", "skills": ["Basic Attack", "Ruby Passion", "Defend"], 
                 "element": "Fire", "class": GirlClass.ATTACKER},
    "Hisui": {"rarity": "Rare", "base_attack": 19, "base_defense": 17, "base_hp": 145, "base_speed": 14, 
              "catchline": "Emerald rebirth, rising anew!", "skills": ["Basic Attack", "Emerald Rise", "Defend"], 
              "element": "Earth", "class": GirlClass.HEALER},
    "Kongouseki": {"rarity": "Rare", "base_attack": 21, "base_defense": 19, "base_hp": 140, "base_speed": 16, 
                   "catchline": "Diamond resilience, forever shining!", "skills": ["Basic Attack", "Diamond Shine", "Defend"], 
                   "element": "Wind", "class": GirlClass.TANK},
    "Kinryokuseki": {"rarity": "Rare", "base_attack": 20, "base_defense": 20, "base_hp": 150, "base_speed": 18, 
                     "catchline": "Peridot joy, prosperity blooms!", "skills": ["Basic Attack", "Peridot Bloom", "Defend"], 
                     "element": "Earth", "class": GirlClass.MORALE},
    "Akasango": {"rarity": "Rare", "base_attack": 22, "base_defense": 17, "base_hp": 135, "base_speed": 17, 
                 "catchline": "Red coral, protective waves!", "skills": ["Basic Attack", "Red Wave", "Defend"], 
                 "element": "Fire", "class": GirlClass.ATTACKER},
    "Suishou": {"rarity": "Epic", "base_attack": 25, "base_defense": 20, "base_hp": 160, "base_speed": 18, 
                "catchline": "Crystal clarity, shattering illusions!", "skills": ["Basic Attack", "Quartz Shatter", "Defend"], 
                "element": "Wind", "class": GirlClass.ATTACKER},
    "Murasakisuishou": {"rarity": "Epic", "base_attack": 24, "base_defense": 22, "base_hp": 155, "base_speed": 19, 
                        "catchline": "Amethyst peace, calming the storm!", "skills": ["Basic Attack", "Amethyst Calm", "Defend"], 
                        "element": "Wind", "class": GirlClass.HEALER},
    "Kokuyouseki": {"rarity": "Epic", "base_attack": 26, "base_defense": 19, "base_hp": 150, "base_speed": 20, 
                    "catchline": "Obsidian shadow, devouring light!", "skills": ["Basic Attack", "Obsidian Devour", "Defend"], 
                    "element": "Earth", "class": GirlClass.TANK},
    "Keiseki": {"rarity": "Epic", "base_attack": 23, "base_defense": 21, "base_hp": 165, "base_speed": 17, 
                "catchline": "Fluorite glow, vibrant and wild!", "skills": ["Basic Attack", "Fluorite Glow", "Defend"], 
                "element": "Wind", "class": GirlClass.MORALE},
    "Akadama": {"rarity": "Epic", "base_attack": 27, "base_defense": 18, "base_hp": 145, "base_speed": 21, 
                "catchline": "Carnelian fire, burning bright!", "skills": ["Basic Attack", "Carnelian Burn", "Defend"], 
                "element": "Fire", "class": GirlClass.ATTACKER},
    "Shinju": {"rarity": "Epic", "base_attack": 28, "base_defense": 24, "base_hp": 170, "base_speed": 20, 
               "catchline": "Pearl purity, elegance in fight!", "skills": ["Basic Attack", "Pearl Elegance", "Defend"], 
               "element": "Water", "class": GirlClass.LEADER},
    "Murasaki-dama": {"rarity": "Epic", "base_attack": 25, "base_defense": 23, "base_hp": 160, "base_speed": 19, 
                      "catchline": "Purple jewel, noble spirit!", "skills": ["Basic Attack", "Amethyst Noble", "Defend"], 
                      "element": "Wind", "class": GirlClass.LEADER},
    "Benitama": {"rarity": "Legendary", "base_attack": 35, "base_defense": 25, "base_hp": 200, "base_speed": 25, 
                 "catchline": "Garnet strength, unyielding force!", "skills": ["Basic Attack", "Garnet Force", "Defend"], 
                 "element": "Fire", "class": GirlClass.ATTACKER},
    "Aotama": {"rarity": "Legendary", "base_attack": 32, "base_defense": 28, "base_hp": 190, "base_speed": 22, 
               "catchline": "Beryl calm, soothing the chaos!", "skills": ["Basic Attack", "Aquamarine Soothe", "Defend"], 
               "element": "Water", "class": GirlClass.HEALER},
    "Ruri": {"rarity": "Legendary", "base_attack": 34, "base_defense": 26, "base_hp": 195, "base_speed": 24, 
             "catchline": "Lapis wisdom, truth unveiled!", "skills": ["Basic Attack", "Lapis Truth", "Defend"], 
             "element": "Water", "class": GirlClass.LEADER}
}

# Monsters
monsters = [
    {"name": "Slime", "hp": 80, "atk": 8, "defense": 5, "speed": 10, "shards": 5, "element": "Water"},
    {"name": "Goblin", "hp": 120, "atk": 15, "defense": 10, "speed": 12, "shards": 10, "element": "Earth"},
    {"name": "Wolf", "hp": 100, "atk": 18, "defense": 8, "speed": 16, "shards": 8, "element": "Fire"},
    {"name": "Orc", "hp": 150, "atk": 20, "defense": 15, "speed": 11, "shards": 15, "element": "Earth"},
    {"name": "Harpy", "hp": 130, "atk": 22, "defense": 12, "speed": 20, "shards": 12, "element": "Wind"}
]

rarity_order = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
rarity_rates = [0.70, 0.20, 0.05, 0.04, 0.01]

SAVE_FILE = "gacha_save.json"
SINGLE_PULL_COST = 100
TEN_PULL_COST = 900

def get_current_time():
    return time.time()

def load_save():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, 'r') as f:
            data = json.load(f)
    else:
        data = {
            "inventory": {},
            "dupes": {},
            "coins": 1000,
            "shards": 200,
            "pull_count": 0,
            "rare_pity": 0,
            "legendary_pity": 0
        }
    
    # Migrate old saves
    for girl in list(data["inventory"].keys()):
        gdata = data["inventory"][girl]
        if isinstance(gdata, int):
            data["inventory"][girl] = {"level": gdata, "recovery_start": None, "hp_at_start": None, "attack_bonus": 0}
        if "attack_bonus" not in gdata:
            gdata["attack_bonus"] = 0
        if "scavenge_end" not in gdata:
            gdata["scavenge_end"] = None
        if "scavenge_result" not in gdata:
            gdata["scavenge_result"] = None
    
    return data

def save_game(data):
    with open(SAVE_FILE, 'w') as f:
        json.dump(data, f)

def get_pull_rarity(data):
    if data["legendary_pity"] >= 100:
        return "Legendary"
    if data["rare_pity"] >= 50:
        return "Rare"
    rand = random.random()
    cumulative = 0
    for i, rate in enumerate(rarity_rates):
        cumulative += rate
        if rand <= cumulative:
            return rarity_order[i]
    return "Common"

def get_girl_by_rarity(rarity):
    candidates = [name for name, gdata in girls_data.items() if gdata["rarity"] == rarity]
    return random.choice(candidates) if candidates else "Tama"

def perform_pull(data, show_output=True):
    data["pull_count"] += 1
    data["rare_pity"] += 1
    data["legendary_pity"] += 1
    rarity = get_pull_rarity(data)
    girl = get_girl_by_rarity(rarity)
    
    if show_output:
        print(f"\n*** You pulled: {girl} ({rarity})! ***")
        print(f"Element: {girls_data[girl]['element']} | Class: {girls_data[girl]['class']}")
        print(f"Catchline: {girls_data[girl]['catchline']}")
    
    if rarity in ["Rare", "Epic", "Legendary"]:
        data["rare_pity"] = 0
    if rarity == "Legendary":
        data["legendary_pity"] = 0
    
    if girl not in data["inventory"]:
        data["inventory"][girl] = {"level": 1, "recovery_start": None, "hp_at_start": None, "attack_bonus": 0, "scavenge_end": None, "scavenge_result": None}
        if show_output:
            print("New girl added to inventory!")
    else:
        data["dupes"].setdefault(girl, 0)
        data["dupes"][girl] += 1
        if show_output:
            print(f"Duplicate! Now {data['dupes'][girl]} dupes.")

def single_pull(data):
    if data['coins'] < SINGLE_PULL_COST:
        print(f"Not enough coins! Need {SINGLE_PULL_COST}, have {data['coins']}.")
        input("Press Enter to continue...")
        return
    data['coins'] -= SINGLE_PULL_COST
    perform_pull(data)
    input("\nPress Enter to continue...")

def ten_pull(data):
    if data['coins'] < TEN_PULL_COST:
        print(f"Not enough coins! Need {TEN_PULL_COST}, have {data['coins']}.")
        input("Press Enter to continue...")
        return
    data['coins'] -= TEN_PULL_COST
    print(f"Spent {TEN_PULL_COST} coins for 10 pulls!")
    for _ in range(10):
        perform_pull(data)
    input("\nPress Enter to continue...")

def get_girl_stats(girl, level, data):
    base = girls_data[girl]
    multiplier = 1 + (level - 1) * 0.2
    stats = {
        "attack": int(base["base_attack"] * multiplier),
        "defense": int(base["base_defense"] * multiplier),
        "hp": int(base["base_hp"] * multiplier),
        "speed": int(base["base_speed"] * multiplier)
    }
    gdata = data["inventory"][girl]
    if 'attack_bonus' in gdata:
        stats["attack"] += gdata['attack_bonus']
    return stats

def is_available(gdata):
    if gdata["recovery_start"] is not None:
        if get_current_time() - gdata["recovery_start"] < 600:
            return False
    if gdata.get("scavenge_end") and get_current_time() < gdata["scavenge_end"]:
        return False
    return True

def get_current_hp(girl, gdata, data):
    if gdata["recovery_start"] is None:
        return get_girl_stats(girl, gdata["level"], data)["hp"]
    elapsed = get_current_time() - gdata["recovery_start"]
    max_hp = get_girl_stats(girl, gdata["level"], data)["hp"]
    hp_at_start = gdata["hp_at_start"]
    if hp_at_start is None:
        return max_hp
    if elapsed >= 600:
        return max_hp
    recovered = (elapsed / 600.0) * (max_hp - hp_at_start)
    return max(1, min(max_hp, hp_at_start + recovered))

def show_inventory(data):
    if not data["inventory"]:
        print("Inventory is empty!")
        input("Press Enter to continue...")
        return
    
    while True:
        print("\n=== INVENTORY ===")
        girls_list = list(data["inventory"].keys())
        for i, girl in enumerate(girls_list, 1):
            gdata = data["inventory"][girl]
            level = gdata["level"]
            stats = get_girl_stats(girl, level, data)
            curr_hp = get_current_hp(girl, gdata, data)
            info = girls_data[girl]
            print(f"{i}. {girl} (Lv.{level}) - {info['rarity']} ({info['element']}) [{info['class']}] - HP: {int(curr_hp)}/{stats['hp']}")
            print(f"  Stats: ATK {stats['attack']}, DEF {stats['defense']}, SPD {stats['speed']}")
            print(f"  {info['catchline']}")
            if not is_available(gdata):
                if gdata.get("scavenge_end"):
                    elapsed = get_current_time() - (gdata["scavenge_end"] - 300)
                    left = max(0, 300 - elapsed)
                    print(f"  Status: Scavenging ({left/60:.1f} min remaining)")
                else:
                    elapsed = get_current_time() - gdata["recovery_start"]
                    left = max(0, 600 - elapsed)
                    print(f"  Status: Recovering ({left/60:.1f} min remaining)")
        
        print(f"\nSelect number (1-{len(girls_list)}) to view details, or 'back': ", end="")
        choice = input().strip().lower()
        if choice == 'back':
            break
        try:
            idx = int(choice)
            if 1 <= idx <= len(girls_list):
                girl = girls_list[idx - 1]
                show_girl_details(girl, data["inventory"][girl], data)
            else:
                print("Invalid number!")
        except ValueError:
            print("Invalid input!")

def show_girl_details(girl, gdata, data):
    level = gdata["level"]
    info = girls_data[girl]
    stats = get_girl_stats(girl, level, data)
    curr_hp = get_current_hp(girl, gdata, data)
    print(f"\n=== {girl} Details ===")
    print(f"Rarity: {info['rarity']}")
    print(f"Element: {info['element']}")
    print(f"Class: {info['class']}")
    print(f"Level: {level}")
    print(f"Current HP: {int(curr_hp)} / {stats['hp']}")
    print(f"Stats: ATK {stats['attack']}, DEF {stats['defense']}, HP {stats['hp']}, SPD {stats['speed']}")
    print(f"Skills: {', '.join(info['skills'])}")
    print(f"Catchline: {info['catchline']}")
    input("\nPress Enter to return to inventory...")

def show_dupes(data):
    if not data["dupes"]:
        print("\nNo dupes!")
        input("Press Enter to continue...")
        return
    
    while True:
        print("\n=== DUPES ===")
        dupe_list = list(data["dupes"].items())
        for i, (girl, count) in enumerate(dupe_list, 1):
            print(f"{i}. {girl}: {count}")
        print("\nSell dupes? Enter 'number amount' (e.g., '1 1') or 'back': ", end="")
        choice = input().strip()
        if choice.lower() == 'back':
            break
        try:
            parts = choice.split()
            if len(parts) != 2:
                print("Invalid input! Use 'number amount'")
                continue
            idx = int(parts[0])
            amt = int(parts[1])
            if amt <= 0:
                print("Amount must be positive!")
                continue
            if 1 <= idx <= len(dupe_list):
                girl, current = dupe_list[idx - 1]
                if amt > current:
                    print(f"Only {current} available!")
                    continue
                data["coins"] += amt * 100
                data["dupes"][girl] -= amt
                if data["dupes"][girl] == 0:
                    del data["dupes"][girl]
                print(f"Sold {amt} dupe(s) of {girl} for {amt * 100} coins!")
                save_game(data)
            else:
                print("Invalid number!")
        except ValueError:
            print("Invalid input!")
    input("Press Enter to continue...")

def check_scavenging_results(data):
    completed = []
    now = get_current_time()
    for girl, gdata in data["inventory"].items():
        end_time = gdata.get("scavenge_end")
        if end_time and now >= end_time and gdata.get("scavenge_result") is None:
            success = random.random() < 0.30
            shards = random.randint(15, 35) if success else 0
            gdata["scavenge_result"] = {"success": success, "shards": shards}
            completed.append(girl)
    
    if completed:
        print("\n=== SCAVENGING RESULTS ===")
        for girl in completed:
            result = data["inventory"][girl]["scavenge_result"]
            if result["success"]:
                data["shards"] += result["shards"]
                print(f"{girl} found {result['shards']} shards!")
            else:
                print(f"{girl} returned empty-handed.")
            data["inventory"][girl]["scavenge_end"] = None
            data["inventory"][girl]["scavenge_result"] = None
        save_game(data)
        input("Press Enter to continue...")

def scavenging(data):
    if not data["inventory"]:
        print("No girls to send scavenging!")
        input("Press Enter to continue...")
        return
    
    available_girls = [g for g, gd in data["inventory"].items() if is_available(gd)]
    if not available_girls:
        print("All girls are recovering or scavenging!")
        input("Press Enter to continue...")
        return
    
    print("\n=== SCAVENGING ===")
    print("30% success rate. Takes 5 minutes.")
    print("\nSelect girl:")
    for i, girl in enumerate(available_girls, 1):
        gdata = data["inventory"][girl]
        level = gdata["level"]
        elem = girls_data[girl]["element"]
        cls = girls_data[girl]["class"]
        print(f"{i}. {girl} (Lv.{level}) - {elem} [{cls}]")
    
    try:
        choice = input("Choose (or 'back'): ").strip()
        if choice.lower() == 'back':
            return
        idx = int(choice) - 1
        if idx < 0 or idx >= len(available_girls):
            print("Invalid choice!")
            input("Press Enter to continue...")
            return
        girl = available_girls[idx]
    except ValueError:
        input("Press Enter to continue...")
        return
    
    now = get_current_time()
    data["inventory"][girl]["scavenge_end"] = now + 300
    data["inventory"][girl]["scavenge_result"] = None
    print(f"\n{girl} sent scavenging for 5 minutes...")
    input("Press Enter to continue...")
    save_game(data)

# Battle functions (unchanged)
def player_turn(girl, girl_stats, skills, monster, mon_hp, girl_hp, girl_max_hp, special_cd, data):
    print("\n--- Your Turn ---")
    for i, skill in enumerate(skills, 1):
        if i == 2 and special_cd > 0:
            print(f"{i}. {skill} (CD: {special_cd})")
        else:
            print(f"{i}. {skill}")
    try:
        skill_choice = int(input("Choose skill: "))
        skill_idx = skill_choice - 1
        if skill_idx == 1 and special_cd > 0:
            print("Special on cooldown! Using Basic Attack.")
            skill_idx = 0
    except:
        print("Invalid! Using Basic Attack.")
        skill_idx = 0
    
    skill = skills[skill_idx]
    damage = 0
    defended = False
    new_special_cd = special_cd
    if skill_idx == 0:
        damage = max(1, girl_stats["attack"] - monster["defense"])
        mon_hp -= damage
        print(f"{girl} uses {skill}! Deals {damage} damage!")
    elif skill_idx == 1:
        base_damage = max(1, int(girl_stats["attack"] * 2.0) - monster["defense"])
        multi = elemental_multiplier(girls_data[girl]["element"], monster["element"])
        damage = int(base_damage * multi)
        mon_hp -= damage
        new_special_cd = 6
        if multi > 1.0:
            print(f"{girl} uses {skill}! Super effective! {damage} damage!")
        elif multi < 1.0:
            print(f"{girl} uses {skill}! Not very effective... {damage} damage!")
        else:
            print(f"{girl} uses {skill}! {damage} damage!")
    elif skill_idx == 2:
        defended = True
        print(f"{girl} uses {skill}! Next attack blocked!")
    
    return mon_hp, girl_hp, defended, new_special_cd

def monster_turn(girl, girl_stats, monster, girl_hp, block_next_attack):
    print("\n--- Monster's Turn ---")
    if block_next_attack:
        print(f"{monster['name']}'s attack blocked!")
        return girl_hp, False
    mon_damage = max(1, monster["atk"] - girl_stats["defense"])
    girl_hp -= mon_damage
    print(f"{monster['name']} attacks! {mon_damage} damage!")
    return girl_hp, False

def turn_based_battle(data):
    available_girls = [g for g, gd in data["inventory"].items() if is_available(gd)]
    if not available_girls:
        print("No girls available!")
        input("Press Enter to continue...")
        return
    
    print("\n=== SELECT UP TO 3 GIRLS FOR BATTLE ===")
    selected = []
    while len(selected) < 3 and available_girls:
        print(f"Team: {', '.join(selected) if selected else 'Empty'}")
        for i, girl in enumerate(available_girls, 1):
            level = data["inventory"][girl]["level"]
            elem = girls_data[girl]["element"]
            cls = girls_data[girl]["class"]
            print(f"{i}. {girl} (Lv.{level}, {elem}) [{cls}]")
        print(f"{len(available_girls)+1}. Done")
        
        try:
            choice = int(input("Choose: "))
            if choice == len(available_girls) + 1:
                break
            if 1 <= choice <= len(available_girls):
                girl = available_girls[choice - 1]
                selected.append(girl)
                available_girls.remove(girl)
            else:
                print("Invalid!")
        except:
            print("Invalid input!")
    
    if not selected:
        print("No team selected!")
        input("Press Enter...")
        return
    
    print("\n=== SELECT MONSTER ===")
    for i, mon in enumerate(monsters, 1):
        print(f"{i}. {mon['name']} ({mon['element']})")
    try:
        mon_idx = int(input("Choose: ")) - 1
        monster = monsters[mon_idx].copy()
    except:
        return
    
    # Setup team
    team = []
    for girl in selected:
        gdata = data["inventory"][girl]
        stats = get_girl_stats(girl, gdata["level"], data)
        team.append({
            "name": girl,
            "stats": stats,
            "hp": get_current_hp(girl, gdata, data),
            "max_hp": stats["hp"],
            "special_cd": 0,
            "defending": False,
            "shield": False
        })
    
    mon_hp = monster["hp"]
    mon_max_hp = mon_hp
    turn_count = 0
    
    print(f"\n=== BATTLE: TEAM vs {monster['name']} ===")
    
    while mon_hp > 0 and any(g["hp"] > 0 for g in team):
        turn_count += 1
        print(f"\n--- TURN {turn_count} ---")
        print(f"Monster HP: {int(mon_hp)}/{mon_max_hp}")
        
        # Player turns (in order)
        for girl in team:
            if girl["hp"] <= 0:
                continue
            print(f"\n{girl['name']}'s turn (HP: {int(girl['hp'])}/{girl['max_hp']})")
            skills = girls_data[girl["name"]]["skills"]
            for i, skill in enumerate(skills, 1):
                if i == 2 and girl["special_cd"] > 0:
                    print(f"{i}. {skill} (CD: {girl['special_cd']})")
                else:
                    print(f"{i}. {skill}")
            
            try:
                choice = int(input("Choose skill: "))
                skill_idx = choice - 1
                if skill_idx == 1 and girl["special_cd"] > 0:
                    print("On cooldown! Using Basic Attack.")
                    skill_idx = 0
            except:
                skill_idx = 0
            
            # Reset defense/shield
            girl["defending"] = False
            if turn_count % 6 == 0:
                girl["shield"] = False
            
            if skill_idx == 0:  # Basic Attack
                damage = max(1, girl["stats"]["attack"] - monster["defense"])
                mon_hp -= damage
                print(f"{girl['name']} deals {damage} damage!")
            elif skill_idx == 1:  # Special
                if girls_data[girl["name"]]["class"] == GirlClass.HEALER and skill_idx == 1:
                    # Group shield
                    for g in team:
                        g["shield"] = True
                    girl["special_cd"] = 6
                    print(f"{girl['name']} casts group shield! (6 turn CD)")
                else:
                    base = int(girl["stats"]["attack"] * 2.0)
                    multi = elemental_multiplier(girls_data[girl["name"]]["element"], monster["element"])
                    damage = max(1, int(base * multi) - monster["defense"])
                    mon_hp -= damage
                    girl["special_cd"] = 6
                    if multi > 1:
                        print(f"{girl['name']} super effective! {damage} damage!")
                    elif multi < 1:
                        print(f"{girl['name']} not very effective... {damage} damage!")
                    else:
                        print(f"{girl['name']} deals {damage} damage!")
            elif skill_idx == 2:  # Defend
                girl["defending"] = True
                print(f"{girl['name']} defends!")
            
            girl["special_cd"] = max(0, girl["special_cd"] - 1)
            if mon_hp <= 0:
                break
        
        if mon_hp <= 0:
            break
        
        # Monster turn
        print("\n--- MONSTER TURN ---")
        targets = [g for g in team if g["hp"] > 0]
        if targets:
            target = random.choice(targets)
            if target["defending"]:
                print(f"{monster['name']} attacks {target['name']} but it's blocked!")
            elif target["shield"]:
                print(f"{monster['name']} attacks {target['name']} but shield absorbs it!")
                target["shield"] = False
            else:
                damage = max(1, monster["atk"] - target["stats"]["defense"])
                target["hp"] -= damage
                print(f"{monster['name']} hits {target['name']} for {damage}! ({int(target['hp'])} HP left)")
    
    # Results
    if mon_hp <= 0:
        print(f"\n{monster['name']} defeated! +{monster['shards']} shards")
        data["shards"] += monster["shards"]
        normal_victory_hook(data)
    else:
        print(f"\nTeam defeated!")
    
    # Recovery
    for girl in selected:
        gdata = data["inventory"][girl]
        final_hp = max(1, int(next(g["hp"] for g in team if g["name"] == girl)))
        gdata["recovery_start"] = get_current_time()
        gdata["hp_at_start"] = final_hp
        print(f"{girl} recovering with {final_hp} HP (10 min)")
    
    input("Press Enter...")
    save_game(data)

def training(data):
    if not data["inventory"]:
        print("No girls!")
        return
    if data["shards"] == 0:
        print("No shards!")
        return
    
    girls_list = list(data["inventory"].keys())
    print("\n=== TRAINING ===")
    for i, girl in enumerate(girls_list, 1):
        level = data["inventory"][girl]["level"]
        elem = girls_data[girl]["element"]
        print(f"{i}. {girl} (Lv.{level}, {elem})")
    
    try:
        idx = int(input("Choose: ")) - 1
        girl = girls_list[idx]
        level = data["inventory"][girl]["level"]
        cost = 10 * (level + 1) ** 2
        if data["shards"] < cost:
            print(f"Need {cost} shards!")
            input("Press Enter...")
            return
        data["shards"] -= cost
        data["inventory"][girl]["level"] += 1
        print(f"{girl} now Lv.{data['inventory'][girl]['level']}")
        input("Press Enter...")
        save_game(data)
    except:
        print("Invalid!")

def healing_session(data):
    if not data["inventory"]:
        print("No girls to heal!")
        input("Press Enter to continue...")
        return
    
    # Find recovering girls
    recovering = [g for g, gd in data["inventory"].items() if gd["recovery_start"] is not None and not is_available(gd)]
    if not recovering:
        print("No girls are recovering!")
        input("Press Enter to continue...")
        return
    
    # Find available healers
    available_healers = [g for g, gd in data["inventory"].items() if is_available(gd) and girls_data[g]["class"] == GirlClass.HEALER]
    if not available_healers:
        print("No available healers!")
        input("Press Enter to continue...")
        return
    
    print("\n=== HEALING SESSION ===")
    print("A healer can speed up recovery. Both will be unavailable for 3 minutes.")
    print("\nSelect recovering girl to heal:")
    for i, girl in enumerate(recovering, 1):
        gdata = data["inventory"][girl]
        elapsed = get_current_time() - gdata["recovery_start"]
        left_min = max(0, (600 - elapsed) / 60)
        print(f"{i}. {girl} ({left_min:.1f} min remaining)")
    
    try:
        idx = int(input("Choose: ")) - 1
        if idx < 0 or idx >= len(recovering):
            print("Invalid choice!")
            input("Press Enter...")
            return
        target_girl = recovering[idx]
    except:
        print("Invalid input!")
        input("Press Enter...")
        return
    
    print("\nSelect healer:")
    for i, girl in enumerate(available_healers, 1):
        level = data["inventory"][girl]["level"]
        print(f"{i}. {girl} (Lv.{level})")
    
    try:
        idx = int(input("Choose: ")) - 1
        if idx < 0 or idx >= len(available_healers):
            print("Invalid choice!")
            input("Press Enter...")
            return
        healer_girl = available_healers[idx]
    except:
        print("Invalid input!")
        input("Press Enter...")
        return
    
    if healer_girl == target_girl:
        print("Can't heal self!")
        input("Press Enter...")
        return
    
    # Start healing
    now = get_current_time()
    heal_time = 180  # 3 minutes
    
    # Full heal target
    data["inventory"][target_girl]["recovery_start"] = None
    data["inventory"][target_girl]["hp_at_start"] = None
    
    # Both unavailable
    data["inventory"][target_girl]["recovery_start"] = now
    data["inventory"][healer_girl]["recovery_start"] = now
    
    print(f"\n{healer_girl} heals {target_girl}! Both unavailable for 3 minutes.")
    input("Press Enter to continue...")
    save_game(data)

def main_menu():
    data = load_save()
    
    while True:
        check_scavenging_results(data)
        print("\n=== GEMINI GACHA ===")
        print(f"Coins: {data['coins']} | Shards: {data['shards']} | Pulls: {data['pull_count']}")
        print(f"Rare Pity: {data['rare_pity']}/50 | Leg. Pity: {data['legendary_pity']}/100")
        print("1. Single Pull (100 coins)")
        print("2. 10 Pull (900 coins)")
        print("3. Inventory")
        print("4. Dupes")
        print("5. Battle")
        print("6. Training")
        print("7. Shop")
        print("8. Scavenging")
        print("9. Healing Session")
        print("10. Dark Cave (Bosses)")
        print("11. Save & Quit")
        
        choice = input("Choose: ").strip()
        
        if choice == '1':
            single_pull(data)
        elif choice == '2':
            ten_pull(data)
        elif choice == '3':
            show_inventory(data)
        elif choice == '4':
            show_dupes(data)
        elif choice == '5':
            turn_based_battle(data)
        elif choice == '6':
            training(data)
        elif choice == '7':
            show_shop(data, girls_data, get_current_time, is_available, save_game, SAVE_FILE)
        elif choice == '8':
            scavenging(data)
        elif choice == '9':
            healing_session(data)
        elif choice == '10':
            funcs = {
                "girls_data": girls_data,
            "elemental_multiplier": elemental_multiplier,
            "get_girl_stats": get_girl_stats,
            "get_current_hp": get_current_hp,
            "is_available": is_available,
            "get_current_time": get_current_time,
            "save_game": save_game,
        }
            boss_menu(data, funcs)
        elif choice == '11':
            save_game(data)
            print("Saved! Goodbye!")
            break
        else:
            print("Invalid!")

#if __name__ == "__main__":
    #main_menu()

if __name__ == "__main__":
    from gui import run_gui
    data = load_save()
    api = {
        "girls_data": girls_data,
        "get_girl_stats": get_girl_stats,
        "get_current_hp": get_current_hp,
        "is_available": is_available,
        "get_current_time": get_current_time,
        "save_game": save_game,
        "load_save": load_save,
        "monsters": monsters,
        "normal_victory_hook": normal_victory_hook,
        "elemental_multiplier": elemental_multiplier,
        "SINGLE_PULL_COST": SINGLE_PULL_COST,
        "TEN_PULL_COST": TEN_PULL_COST,
    }
    run_gui(data, api)
