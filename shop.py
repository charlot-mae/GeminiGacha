# shop.py - Coin Shop Module
# Import this into main.py and call show_shop(data, girls_data, get_current_time, is_available, save_game, SAVE_FILE) from main menu

import json
import os
import time

def show_shop(data, girls_data, get_current_time, is_available, save_game, SAVE_FILE):
    while True:
        print("\n=== COIN SHOP ===")
        print(f"Coins: {data['coins']}")
        print("\nFood (Healing):")
        print("1. Healing Potion (Full heal a recovering girl) - 200 coins")
        print("\nWeapons (Boosts):")
        print("2. Attack Booster (+5 permanent ATK to a girl) - 1000 coins")
        print("\nMaterials (Resources):")
        print("3. Shard Bundle (10 shards for training) - 2000 coins")
        print("4. Back to Menu")
        
        choice = input("Choose: ").strip()
        
        if choice == '1':
            if data['coins'] < 200:
                print("Not enough coins!")
                input("Press Enter to continue...")
                continue
            
            recovering_girls = [g for g, gdata in data["inventory"].items() if not is_available(gdata)]
            if not recovering_girls:
                print("No girls are recovering!")
                input("Press Enter to continue...")
                continue
            
            print("\nSelect girl to heal:")
            for i, girl in enumerate(recovering_girls, 1):
                gdata = data["inventory"][girl]
                elapsed = get_current_time() - gdata["recovery_start"]
                left_min = max(0, (600 - elapsed) / 60)
                print(f"{i}. {girl} (Recovering: {left_min:.1f} min left)")
            
            try:
                idx = int(input("Choose: ")) - 1
                girl = recovering_girls[idx]
                data["inventory"][girl]["recovery_start"] = None
                data["inventory"][girl]["hp_at_start"] = None
                data['coins'] -= 200
                print(f"{girl} fully healed!")
            except (ValueError, IndexError):
                print("Invalid choice!")
            
            input("Press Enter to continue...")
            save_game(data)
        
        elif choice == '2':
            if data['coins'] < 1000:
                print("Not enough coins!")
                input("Press Enter to continue...")
                continue
            
            print("\nSelect girl to boost:")
            girls_list = list(data["inventory"].keys())
            for i, girl in enumerate(girls_list, 1):
                gdata = data["inventory"][girl]
                level = gdata["level"]
                print(f"{i}. {girl} (Lv. {level})")
            
            try:
                idx = int(input("Choose: ")) - 1
                girl = girls_list[idx]
                if 'attack_bonus' not in data["inventory"][girl]:
                    data["inventory"][girl]['attack_bonus'] = 0
                data["inventory"][girl]['attack_bonus'] += 5
                data['coins'] -= 1000
                print(f"{girl}'s attack boosted by 5!")
            except (ValueError, IndexError):
                print("Invalid choice!")
            
            input("Press Enter to continue...")
            save_game(data)
        
        elif choice == '3':
            if data['coins'] < 2000:
                print("Not enough coins!")
                input("Press Enter to continue...")
                continue
            
            data['shards'] += 10
            data['coins'] -= 2000
            print("Bought 10 shards!")
            input("Press Enter to continue...")
            save_game(data)
        
        elif choice == '4':
            break
        else:
            print("Invalid choice!")
            input("Press Enter to continue...")