# cheats.py - Fixed version
import json
import os
import random

# Full girls_data (must match main.py exactly)
girls_data = {
    "Tama": {"rarity": "Common", "base_attack": 10, "base_defense": 8, "base_hp": 100, "base_speed": 12, "catchline": "I am the jewel that lights your path!", "skills": ["Basic Attack", "Jewel Slash", "Defend"], "element": "Earth"},
    "Houseki": {"rarity": "Common", "base_attack": 12, "base_defense": 10, "base_hp": 110, "base_speed": 10, "catchline": "Treasures await in my sparkling gaze!", "skills": ["Basic Attack", "Gem Burst", "Defend"], "element": "Earth"},
    "Ri": {"rarity": "Common", "base_attack": 9, "base_defense": 9, "base_hp": 105, "base_speed": 11, "catchline": "Clear as glass, sharp as my will!", "skills": ["Basic Attack", "Crystal Shard", "Defend"], "element": "Earth"},
    "Rin": {"rarity": "Common", "base_attack": 11, "base_defense": 7, "base_hp": 95, "base_speed": 13, "catchline": "A gem of rarity in your collection!", "skills": ["Basic Attack", "Jade Spark", "Defend"], "element": "Earth"},
    "Hishouseki": {"rarity": "Common", "base_attack": 10, "base_defense": 9, "base_hp": 100, "base_speed": 11, "catchline": "Malachite transform, evolve with me!", "skills": ["Basic Attack", "Malachite Strike", "Defend"], "element": "Earth"},
    "Kohaku-iro": {"rarity": "Common", "base_attack": 11, "base_defense": 10, "base_hp": 105, "base_speed": 12, "catchline": "Amber hue, warm embrace!", "skills": ["Basic Attack", "Amber Glow", "Defend"], "element": "Fire"},
    "Tamaki": {"rarity": "Common", "base_attack": 9, "base_defense": 11, "base_hp": 110, "base_speed": 10, "catchline": "Jewel tree, roots of power!", "skills": ["Basic Attack", "Jade Bind", "Defend"], "element": "Earth"},
    "Ryu": {"rarity": "Uncommon", "base_attack": 15, "base_defense": 12, "base_hp": 120, "base_speed": 14, "catchline": "Precious stone, unbreakable bond!", "skills": ["Basic Attack", "Lapis Bond", "Defend"], "element": "Water"},
    "Riko": {"rarity": "Uncommon", "base_attack": 14, "base_defense": 13, "base_hp": 115, "base_speed": 12, "catchline": "Child of glass, reflecting your dreams!", "skills": ["Basic Attack", "Crystal Mirror", "Defend"], "element": "Water"},
    "Kotouseki": {"rarity": "Uncommon", "base_attack": 16, "base_defense": 11, "base_hp": 125, "base_speed": 13, "catchline": "Music in stone, harmony in battle!", "skills": ["Basic Attack", "Jade Wave", "Defend"], "element": "Water"},
    "Kohaku": {"rarity": "Uncommon", "base_attack": 13, "base_defense": 14, "base_hp": 118, "base_speed": 11, "catchline": "Amber warmth, eternal flame within!", "skills": ["Basic Attack", "Amber Burst", "Defend"], "element": "Fire"},
    "Seiyou": {"rarity": "Uncommon", "base_attack": 17, "base_defense": 15, "base_hp": 130, "base_speed": 15, "catchline": "Turquoise fortune, luck by my side!", "skills": ["Basic Attack", "Turquoise Luck", "Defend"], "element": "Water"},
    "Hekigyoku": {"rarity": "Uncommon", "base_attack": 16, "base_defense": 14, "base_hp": 125, "base_speed": 13, "catchline": "Beryl healing, mending wounds!", "skills": ["Basic Attack", "Beryl Mend", "Defend"], "element": "Water"},
    "Sango": {"rarity": "Rare", "base_attack": 20, "base_defense": 16, "base_hp": 140, "base_speed": 15, "catchline": "Coral waves crash with my power!", "skills": ["Basic Attack", "Coral Crash", "Defend"], "element": "Fire"},
    "Suigyoku": {"rarity": "Rare", "base_attack": 18, "base_defense": 18, "base_hp": 135, "base_speed": 16, "catchline": "Jade purity, guardian of the pure!", "skills": ["Basic Attack", "Jade Guard", "Defend"], "element": "Fire"},
    "Kougyoku": {"rarity": "Rare", "base_attack": 22, "base_defense": 15, "base_hp": 130, "base_speed": 17, "catchline": "Ruby passion, igniting victory!", "skills": ["Basic Attack", "Ruby Passion", "Defend"], "element": "Fire"},
    "Hisui": {"rarity": "Rare", "base_attack": 19, "base_defense": 17, "base_hp": 145, "base_speed": 14, "catchline": "Emerald rebirth, rising anew!", "skills": ["Basic Attack", "Emerald Rise", "Defend"], "element": "Earth"},
    "Kongouseki": {"rarity": "Rare", "base_attack": 21, "base_defense": 19, "base_hp": 140, "base_speed": 16, "catchline": "Diamond resilience, forever shining!", "skills": ["Basic Attack", "Diamond Shine", "Defend"], "element": "Wind"},
    "Kinryokuseki": {"rarity": "Rare", "base_attack": 20, "base_defense": 20, "base_hp": 150, "base_speed": 18, "catchline": "Peridot joy, prosperity blooms!", "skills": ["Basic Attack", "Peridot Bloom", "Defend"], "element": "Earth"},
    "Akasango": {"rarity": "Rare", "base_attack": 22, "base_defense": 17, "base_hp": 135, "base_speed": 17, "catchline": "Red coral, protective waves!", "skills": ["Basic Attack", "Red Wave", "Defend"], "element": "Fire"},
    "Suishou": {"rarity": "Epic", "base_attack": 25, "base_defense": 20, "base_hp": 160, "base_speed": 18, "catchline": "Crystal clarity, shattering illusions!", "skills": ["Basic Attack", "Quartz Shatter", "Defend"], "element": "Wind"},
    "Murasakisuishou": {"rarity": "Epic", "base_attack": 24, "base_defense": 22, "base_hp": 155, "base_speed": 19, "catchline": "Amethyst peace, calming the storm!", "skills": ["Basic Attack", "Amethyst Calm", "Defend"], "element": "Wind"},
    "Kokuyouseki": {"rarity": "Epic", "base_attack": 26, "base_defense": 19, "base_hp": 150, "base_speed": 20, "catchline": "Obsidian shadow, devouring light!", "skills": ["Basic Attack", "Obsidian Devour", "Defend"], "element": "Earth"},
    "Keiseki": {"rarity": "Epic", "base_attack": 23, "base_defense": 21, "base_hp": 165, "base_speed": 17, "catchline": "Fluorite glow, vibrant and wild!", "skills": ["Basic Attack", "Fluorite Glow", "Defend"], "element": "Wind"},
    "Akadama": {"rarity": "Epic", "base_attack": 27, "base_defense": 18, "base_hp": 145, "base_speed": 21, "catchline": "Carnelian fire, burning bright!", "skills": ["Basic Attack", "Carnelian Burn", "Defend"], "element": "Fire"},
    "Shinju": {"rarity": "Epic", "base_attack": 28, "base_defense": 24, "base_hp": 170, "base_speed": 20, "catchline": "Pearl purity, elegance in fight!", "skills": ["Basic Attack", "Pearl Elegance", "Defend"], "element": "Water"},
    "Murasaki-dama": {"rarity": "Epic", "base_attack": 25, "base_defense": 23, "base_hp": 160, "base_speed": 19, "catchline": "Purple jewel, noble spirit!", "skills": ["Basic Attack", "Amethyst Noble", "Defend"], "element": "Wind"},
    "Benitama": {"rarity": "Legendary", "base_attack": 35, "base_defense": 25, "base_hp": 200, "base_speed": 25, "catchline": "Garnet strength, unyielding force!", "skills": ["Basic Attack", "Garnet Force", "Defend"], "element": "Fire"},
    "Aotama": {"rarity": "Legendary", "base_attack": 32, "base_defense": 28, "base_hp": 190, "base_speed": 22, "catchline": "Beryl calm, soothing the chaos!", "skills": ["Basic Attack", "Aquamarine Soothe", "Defend"], "element": "Water"},
    "Ruri": {"rarity": "Legendary", "base_attack": 34, "base_defense": 26, "base_hp": 195, "base_speed": 24, "catchline": "Lapis wisdom, truth unveiled!", "skills": ["Basic Attack", "Lapis Truth", "Defend"], "element": "Water"}
}

rarity_order = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
rarity_rates = [0.70, 0.20, 0.05, 0.04, 0.01]

SAVE_FILE = "gacha_save.json"

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
    if not candidates:
        print(f"Warning: No girls found for rarity {rarity}. Using fallback.")
        return "Tama"  # Fallback to prevent crash
    return random.choice(candidates)

def perform_pull(data):
    data["pull_count"] += 1
    data["rare_pity"] += 1
    data["legendary_pity"] += 1
    
    rarity = get_pull_rarity(data)
    girl = get_girl_by_rarity(rarity)
    
    print(f"\n*** You pulled: {girl} ({rarity})! ***")
    print(f"Element: {girls_data[girl]['element']}")
    print(f"Catchline: {girls_data[girl]['catchline']}")
    
    if rarity in ["Rare", "Epic", "Legendary"]:
        data["rare_pity"] = 0
    if rarity == "Legendary":
        data["legendary_pity"] = 0
    
    if girl not in data["inventory"]:
        data["inventory"][girl] = {"level": 1, "recovery_start": None, "hp_at_start": None, "attack_bonus": 0}
        print(f"New girl added to inventory!")
    else:
        data["dupes"].setdefault(girl, 0)
        data["dupes"][girl] += 1
        print(f"Duplicate! Added to dupes. Now {data['dupes'][girl]} dupes of {girl}.")

def save_game(data):
    with open(SAVE_FILE, 'w') as f:
        json.dump(data, f)

def load_save():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, 'r') as f:
            return json.load(f)
    return {
        "inventory": {},
        "dupes": {},
        "coins": 0,
        "shards": 0,
        "pull_count": 0,
        "rare_pity": 0,
        "legendary_pity": 0
    }

def reset_saves():
    if os.path.exists(SAVE_FILE):
        os.remove(SAVE_FILE)
    print("Save file erased! All data reset.")

def ten_pull(data):
    print("\nPerforming 10 pulls...")
    for _ in range(10):
        perform_pull(data)
    save_game(data)
    print("10 pulls completed!")

def cheat_menu():
    data = load_save()
    
    while True:
        print("\n=== CHEAT MENU (Debugging) ===")
        print("1. Erase Save (Reset All)")
        print("2. 10 Pull")
        print("3. Add 1000 Shards")
        print("4. Add 1000 Coins")
        print("5. Exit")
        
        choice = input("Choose: ").strip()
        
        if choice == '1':
            print("\nWARNING: This will permanently erase your save file.")
            confirm = input("Type ERASE to confirm (or anything else to cancel): ").strip()
            if confirm == 'ERASE':
                reset_saves()
                data = load_save()
            else:
                print("Canceled. Save not erased.")
        elif choice == '2':
            ten_pull(data)
        elif choice == '3':
            data["shards"] += 1000
            save_game(data)
            print("Added 1000 shards!")
        elif choice == '4':
            data["coins"] += 1000
            save_game(data)
            print("Added 1000 coins!")
        elif choice == '5':
            break
        else:
            print("Invalid choice!")

if __name__ == "__main__":
    cheat_menu()
