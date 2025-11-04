# gui.py
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import random
import json
import os
import time
from main import (
    girls_data, elemental_multiplier, get_girl_stats, get_current_hp,
    is_available, get_current_time, save_game, load_save,
    GirlClass, monsters
)

# ----------------------------------------------------------------------
# DARK BLUE + PINK THEME
# ----------------------------------------------------------------------
BG_DARK = "#0A1A2F"
BG_CARD = "#112240"
BG_BTN  = "#1E3A5F"
BG_BTN_HOVER = "#2A5588"
ACCENT  = "#FF6BC1"
TEXT_FG = "#E0E7FF"
TEXT_SUB = "#A0B8E0"
SUCCESS = "#66FFB3"
WARN    = "#FFB366"
ERROR   = "#FF6B6B"

ELEMENT_COLORS = {
    "Fire":  "#FF5555",
    "Water": "#5555FF",
    "Earth": "#8B6F47",
    "Wind":  "#55AA55"
}

RARITY_COLORS = {
    "Common":     "#888888",
    "Uncommon":   "#55AA55",
    "Rare":       "#5555FF",
    "Epic":       "#AA00AA",
    "Legendary":  "#FFAA00"
}

# ----------------------------------------------------------------------
# MAIN APP
# ----------------------------------------------------------------------
class GachaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gemstone Gacha")
        self.root.geometry("1080x720")  # ← CHANGED
        self.root.configure(bg=BG_DARK)
        self.root.resizable(True, True)  # ← Optional: lock size

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton', background=BG_BTN, foreground=TEXT_FG, font=('Segoe UI', 10), padding=8)
        style.map('TButton',
                  background=[('active', BG_BTN_HOVER), ('pressed', ACCENT)],
                  foreground=[('active', TEXT_FG)])
        style.configure('TLabel', background=BG_DARK, foreground=TEXT_FG, font=('Segoe UI', 10))
        style.configure('Card.TFrame', background=BG_CARD, relief='flat', borderwidth=1)

        self.data = load_save()
        self.ensure_boss_state()
        self.resource_label = None
        self.create_main_menu()

    def update_resources(self):
        if self.resource_label is not None:
            self.resource_label.configure(
                text=f"Coins: {self.data['coins']} | Shards: {self.data['shards']}"
            )

    def ensure_boss_state(self):
        self.data.setdefault("boss_defeat_counter", 0)
        self.data.setdefault("cave_unlocked", False)
        self.data.setdefault("active_boss", None)
        self.data.setdefault("boss_fight_state", None)

    def handle_normal_victory(self):
        self.ensure_boss_state()
        self.data["boss_defeat_counter"] += 1
        if self.data["boss_defeat_counter"] >= 5 and not self.data["cave_unlocked"]:
            self.data["cave_unlocked"] = True
            messagebox.showinfo(
                "Dark Cave Unlocked",
                "Defeat 5 more monsters to open the next boss gate!"
            )

    # ------------------------------------------------------------------
    # UTILS
    # ------------------------------------------------------------------
    def clear_frame(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def save_and_quit(self):
        save_game(self.data)
        self.root.quit()

    def open_window(self, title, width=1080, height=720):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry(f"{width}x{height}")
        win.configure(bg=BG_DARK)
        win.resizable(False, False)
        
        # Center on screen
        win.update_idletasks()
        x = (win.winfo_screenwidth() // 2) - (width // 2)
        y = (win.winfo_screenheight() // 2) - (height // 2)
        win.geometry(f"+{x}+{y}")
        
        return win

    # ------------------------------------------------------------------
    # PORTRAIT
    # ------------------------------------------------------------------
    def create_portrait(self, parent, girl_name, size=70):
        info = girls_data[girl_name]
        fill = ELEMENT_COLORS.get(info["element"], "#666666")
        border = RARITY_COLORS[info["rarity"]]
        canvas = tk.Canvas(parent, width=size, height=size, bg=BG_CARD, highlightthickness=0)
        canvas.create_oval(4, 4, size-4, size-4, fill=fill, outline=border, width=3)
        canvas.create_text(size//2, size//2, text=girl_name[:3].upper(),
                           fill="white", font=("Segoe UI", 12, "bold"))
        return canvas

    # ------------------------------------------------------------------
    # MAIN MENU
    # ------------------------------------------------------------------
    def create_main_menu(self):
        self.clear_frame()

        # === CANVAS SETUP ===
        canvas = tk.Canvas(self.root, bg=BG_DARK, highlightthickness=0)
        vbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas, style='Card.TFrame', padding=25)

        # Dynamic resize
        def _resize(event):
            canvas.itemconfig(inner_id, width=event.width - 20)
        inner_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=vbar.set)
        canvas.bind("<Configure>", _resize)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.pack(side="left", fill="both", expand=True)
        vbar.pack(side="right", fill="y")

        # === CONTENT ===
        ttk.Label(inner, text="GEMSTONE GACHA", font=("Segoe UI", 22, "bold"), foreground=ACCENT).pack(pady=12)
        self.resource_label = ttk.Label(inner,
                                        text=f"Coins: {self.data['coins']} | Shards: {self.data['shards']}",
                                        font=("Segoe UI", 11), foreground=TEXT_SUB)
        self.resource_label.pack(pady=5)

        buttons = [
            ("Single Pull", self.single_pull),
            ("10 Pull", self.ten_pull),
            ("Inventory", self.gui_inventory),
            ("Dupes", self.gui_dupes),
            ("Battle", self.gui_battle),
            ("Training", self.gui_training),
            ("Shop", self.gui_shop),
            ("Scavenging", self.gui_scavenging),
            ("Healing Session", self.gui_healing),
            ("Dark Cave", self.gui_boss),
            ("Save & Quit", self.save_and_quit),
        ]

        for text, cmd in buttons:
            ttk.Button(inner, text=text, command=cmd).pack(pady=6, fill=tk.X, padx=50)

    # ------------------------------------------------------------------
    # PULLS
    # ------------------------------------------------------------------
    def single_pull(self):
        if self.data["coins"] < 100:
            messagebox.showerror("Error", "Not enough coins!")
            return
        self.data["coins"] -= 100
        self.update_resources()
        self.perform_pull_gui()

    def ten_pull(self):
        if self.data["coins"] < 900:
            messagebox.showerror("Error", "Not enough coins!")
            return
        self.data["coins"] -= 900
        self.update_resources()
        results = [self.perform_pull_core() for _ in range(10)]
        self.show_pull_results(results)

    def perform_pull_gui(self):
        result = self.perform_pull_core()
        self.show_pull_results([result])

    def perform_pull_core(self):
        self.data["pull_count"] = self.data.get("pull_count", 0) + 1
        self.data["rare_pity"] = self.data.get("rare_pity", 0) + 1
        self.data["legendary_pity"] = self.data.get("legendary_pity", 0) + 1
        rarity = self.get_pull_rarity()
        girl = self.get_girl_by_rarity(rarity)

        if rarity in ["Rare", "Epic", "Legendary"]:
            self.data["rare_pity"] = 0
        if rarity == "Legendary":
            self.data["legendary_pity"] = 0

        if girl not in self.data["inventory"]:
            self.data["inventory"][girl] = {
                "level": 1, "recovery_start": None, "hp_at_start": None,
                "attack_bonus": 0, "scavenge_end": None, "scavenge_result": None
            }
            new = True
        else:
            self.data["dupes"][girl] = self.data["dupes"].get(girl, 0) + 1
            new = False
        return {"girl": girl, "rarity": rarity, "new": new}

    def show_pull_results(self, results):
        win = self.open_window("Pull Results")
        win.geometry("520x640")
        win.configure(bg=BG_DARK)

        for res in results:
            frame = ttk.Frame(win, padding=12, style='Card.TFrame')
            frame.pack(fill=tk.X, pady=6, padx=12)

            canvas = self.create_portrait(frame, res["girl"], 70)
            canvas.pack(side=tk.LEFT, padx=8)

            info = girls_data[res["girl"]]
            ttk.Label(frame, text=f"{res['girl']} ({res['rarity']})", font=("Segoe UI", 13, "bold"), foreground=TEXT_FG).pack(anchor="w")
            ttk.Label(frame, text=f"{info['element']} | {info['class']}", foreground=TEXT_SUB).pack(anchor="w")
            ttk.Label(frame, text=info['catchline'], foreground="#BBBBBB", font=("Segoe UI", 9, "italic")).pack(anchor="w")
            if res["new"]:
                ttk.Label(frame, text="NEW!", foreground=SUCCESS, font=("Segoe UI", 10, "bold")).pack(anchor="w")
            else:
                ttk.Label(frame, text="Duplicate", foreground=WARN).pack(anchor="w")

        ttk.Button(win, text="Close", command=win.destroy).pack(pady=12)

    def get_pull_rarity(self):
        if self.data.get("legendary_pity", 0) >= 100: return "Legendary"
        if self.data.get("rare_pity", 0) >= 50: return "Rare"
        return random.choices(
            ["Common", "Uncommon", "Rare", "Epic", "Legendary"],
            weights=[0.70, 0.20, 0.05, 0.04, 0.01]
        )[0]

    def get_girl_by_rarity(self, rarity):
        candidates = [g for g, d in girls_data.items() if d["rarity"] == rarity]
        return random.choice(candidates) if candidates else "Tama"

    # ------------------------------------------------------------------
    # INVENTORY – PERFECT
    # ------------------------------------------------------------------
    def gui_inventory(self):
        win = self.open_window("Inventory")
        win.geometry("840x640")
        win.configure(bg=BG_DARK)

        # === MAIN FRAME ===
        main = tk.Frame(win, bg=BG_DARK)
        main.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # === CANVAS + SCROLLBAR ===
        canvas = tk.Canvas(main, bg=BG_DARK, highlightthickness=0)
        vbar = ttk.Scrollbar(main, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=BG_DARK)  # ← tk.Frame, not ttk!

        # Dynamic resize
        def resize(event):
            canvas.itemconfig(inner_id, width=event.width - 20)
        inner_id = canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=vbar.set)
        canvas.bind("<Configure>", resize)
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.pack(side="left", fill="both", expand=True)
        vbar.pack(side="right", fill="y")

        # === POPULATE ===
        for girl, gdata in self.data["inventory"].items():
            # DARK CARD
            card = tk.Frame(scrollable, bg=BG_CARD, relief='flat', bd=1)
            card.pack(fill=tk.X, pady=6, padx=10)

            # Portrait
            portrait = self.create_portrait(card, girl, 70)
            portrait.pack(side=tk.LEFT, padx=(0, 14))

            # Text
            txt = tk.Frame(card, bg=BG_CARD)
            txt.pack(side=tk.LEFT, fill=tk.X, expand=True)

            stats = get_girl_stats(girl, gdata["level"], self.data)
            hp = int(get_current_hp(girl, gdata, self.data))
            info = girls_data[girl]

            tk.Label(txt, text=f"{girl} Lv.{gdata['level']}", font=("Segoe UI", 13, "bold"), fg=TEXT_FG, bg=BG_CARD).pack(anchor="w")
            tk.Label(txt, text=f"{info['rarity']} | {info['element']} | {info['class']}", fg=TEXT_SUB, bg=BG_CARD, font=("Segoe UI", 10)).pack(anchor="w")
            hp_ratio = hp / stats['hp']
            hp_col = ERROR if hp_ratio <= 0.3 else WARN if hp_ratio <= 0.7 else SUCCESS
            tk.Label(txt, text=f"HP: {hp}/{stats['hp']}", fg=hp_col, bg=BG_CARD).pack(anchor="w")
            tk.Label(txt, text=f"ATK {stats['attack']} | DEF {stats['defense']} | SPD {stats['speed']}", fg=TEXT_SUB, bg=BG_CARD).pack(anchor="w")
            tk.Label(txt, text=info['catchline'], fg="#999999", bg=BG_CARD, font=("Segoe UI", 9, "italic")).pack(anchor="w")

            if not is_available(gdata):
                if gdata.get("scavenge_end"):
                    left = max(0, 300 - (get_current_time() - (gdata["scavenge_end"] - 300))) / 60
                    status, col = f"Scavenging ({left:.1f} min)", WARN
                else:
                    left = max(0, 600 - (get_current_time() - gdata["recovery_start"])) / 60
                    status, col = f"Recovering ({left:.1f} min)", ERROR
                tk.Label(txt, text=status, fg=col, bg=BG_CARD, font=("Segoe UI", 9)).pack(anchor="w")

            ttk.Button(txt, text="Details", command=lambda g=girl: self.show_girl_detail(g)).pack(anchor="w", pady=6)

        ttk.Button(main, text="Close", command=win.destroy).pack(pady=12)

    # ------------------------------------------------------------------
    # GIRL DETAIL
    # ------------------------------------------------------------------
    def show_girl_detail(self, girl):
        gdata = self.data["inventory"][girl]
        stats = get_girl_stats(girl, gdata["level"], self.data)
        hp = int(get_current_hp(girl, gdata, self.data))
        info = girls_data[girl]

        win = self.open_window(f"{girl} - Details")
        win.geometry("400x500")
        win.configure(bg=BG_DARK)

        self.create_portrait(win, girl, 100).pack(pady=10)
        ttk.Label(win, text=f"{girl} Lv.{gdata['level']}", font=("Segoe UI", 14, "bold"), foreground=TEXT_FG).pack()
        ttk.Label(win, text=f"{info['rarity']} | {info['element']} | {info['class']}", foreground=TEXT_SUB).pack()
        ttk.Label(win, text=f"HP: {hp}/{stats['hp']}").pack()
        ttk.Label(win, text=f"ATK: {stats['attack']} | DEF: {stats['defense']} | SPD: {stats['speed']}").pack()
        ttk.Label(win, text=f"Skills: {', '.join(info['skills'])}").pack()
        ttk.Label(win, text=info['catchline'], foreground="#AAAAAA", font=("Segoe UI", 9, "italic")).pack(pady=10)
        ttk.Button(win, text="Close", command=win.destroy).pack(pady=10)

    # ------------------------------------------------------------------
    # DUPES
    # ------------------------------------------------------------------
    def gui_dupes(self):
        win = self.open_window("Dupes")
        win.geometry("500x500")
        win.configure(bg=BG_DARK)

        if not self.data.get("dupes"):
            ttk.Label(win, text="No dupes!", foreground=TEXT_SUB).pack(pady=20)
            ttk.Button(win, text="Close", command=win.destroy).pack()
            return

        for girl, count in self.data["dupes"].items():
            frame = ttk.Frame(win, padding=10, style='Card.TFrame')
            frame.pack(fill=tk.X, pady=2, padx=10)
            ttk.Label(frame, text=f"{girl}: {count}", foreground=TEXT_FG).pack(side=tk.LEFT)
            ttk.Button(
                frame,
                text="Sell 1",
                command=lambda g=girl, w=win: self.sell_dupe(g, 1, w)
            ).pack(side=tk.RIGHT, padx=5)
            ttk.Button(
                frame,
                text="Sell All",
                command=lambda g=girl, c=count, w=win: self.sell_dupe(g, c, w)
            ).pack(side=tk.RIGHT)

        ttk.Button(win, text="Close", command=win.destroy).pack(pady=10)

    def sell_dupe(self, girl, amt, window=None):
        current = self.data["dupes"][girl]
        sell_amt = min(amt, current)
        self.data["coins"] += sell_amt * 100
        self.data["dupes"][girl] -= sell_amt
        if self.data["dupes"][girl] == 0:
            del self.data["dupes"][girl]
        save_game(self.data)
        self.update_resources()
        messagebox.showinfo("Sold", f"Sold {sell_amt} dupe(s) of {girl} for {sell_amt*100} coins!")
        if window is not None and window.winfo_exists():
            window.destroy()
        self.gui_dupes()

    # ------------------------------------------------------------------
    # BATTLE
    # ------------------------------------------------------------------
    def gui_battle(self):
        available = [g for g, gd in self.data["inventory"].items() if is_available(gd)]
        if not available:
            messagebox.showinfo("Battle", "No girls available for battle!")
            return

        win = self.open_window("Battle")
        win.geometry("780x640")
        win.configure(bg=BG_DARK)

        ttk.Label(win, text="Select up to 3 girls", foreground=TEXT_SUB).pack(pady=5)
        listbox = tk.Listbox(
            win,
            selectmode=tk.MULTIPLE,
            bg=BG_CARD,
            fg=TEXT_FG,
            selectbackground=ACCENT,
            activestyle='dotbox',
            exportselection=False
        )
        for girl in available:
            level = self.data["inventory"][girl]["level"]
            elem = girls_data[girl]["element"]
            cls = girls_data[girl]["class"]
            listbox.insert(tk.END, f"{girl} (Lv.{level}) [{elem}/{cls}]")
        listbox.pack(fill=tk.X, padx=12, pady=8)

        ttk.Label(win, text="Choose a monster", foreground=TEXT_SUB).pack(pady=5)
        monster_names = [m["name"] for m in monsters]
        monster_var = tk.StringVar(value=monster_names[0])
        monster_combo = ttk.Combobox(win, values=monster_names, textvariable=monster_var, state="readonly")
        monster_combo.pack(padx=12, pady=5, fill=tk.X)

        log = scrolledtext.ScrolledText(win, wrap=tk.WORD, font=("Consolas", 10), bg=BG_CARD, fg=TEXT_FG)
        log.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        log.config(state=tk.DISABLED)

        def start_battle():
            selection = listbox.curselection()
            if not selection:
                messagebox.showerror("Battle", "Please select at least one girl.")
                return
            if len(selection) > 3:
                messagebox.showerror("Battle", "You can only send up to 3 girls.")
                return
            chosen_girls = [available[i] for i in selection]
            monster_name = monster_var.get()
            monster_template = next((m for m in monsters if m["name"] == monster_name), None)
            if not monster_template:
                messagebox.showerror("Battle", "Invalid monster selection.")
                return
            log.configure(state=tk.NORMAL)
            log.delete("1.0", tk.END)
            battle_log = self.simulate_battle(chosen_girls, monster_template)
            log.insert(tk.END, battle_log)
            log.configure(state=tk.DISABLED)
            self.update_resources()

        ttk.Button(win, text="Start Battle", command=start_battle).pack(pady=8)
        ttk.Button(win, text="Close", command=win.destroy).pack(pady=5)

    # ------------------------------------------------------------------
    # TRAINING
    # ------------------------------------------------------------------
    def gui_training(self):
        win = self.open_window("Training")
        win.geometry("500x500")
        win.configure(bg=BG_DARK)
        girls = list(self.data["inventory"].keys())
        if not girls:
            ttk.Label(win, text="No girls!", foreground=TEXT_SUB).pack()
            return
        for girl in girls:
            gdata = self.data["inventory"][girl]
            level = gdata["level"]
            cost = 10 * (level + 1) ** 2
            frame = ttk.Frame(win, padding=5, style='Card.TFrame')
            frame.pack(fill=tk.X, pady=2, padx=10)
            ttk.Label(frame, text=f"{girl} Lv.{level} (Cost: {cost})", foreground=TEXT_FG).pack(side=tk.LEFT)
            ttk.Button(
                frame,
                text="Train",
                command=lambda g=girl, c=cost, w=win: self.train_girl(g, c, w)
            ).pack(side=tk.RIGHT)
        ttk.Button(win, text="Close", command=win.destroy).pack(pady=10)

    def train_girl(self, girl, cost, window=None):
        if self.data["shards"] < cost:
            messagebox.showerror("Error", "Not enough shards!")
            return
        self.data["shards"] -= cost
        self.data["inventory"][girl]["level"] += 1
        save_game(self.data)
        self.update_resources()
        messagebox.showinfo("Success", f"{girl} is now Lv.{self.data['inventory'][girl]['level']}!")
        if window is not None and window.winfo_exists():
            window.destroy()
        self.gui_training()

    # ------------------------------------------------------------------
    # SHOP
    # ------------------------------------------------------------------
    def gui_shop(self):
        win = self.open_window("Coin Shop")
        win.geometry("520x420")
        win.configure(bg=BG_DARK)

        coins_var = tk.StringVar(value=f"Coins: {self.data['coins']}")
        ttk.Label(win, textvariable=coins_var, foreground=TEXT_SUB).pack(pady=6)

        ttk.Label(win, text="Food (Healing)", foreground=TEXT_FG, font=("Segoe UI", 11, "bold")).pack(pady=(10, 4))

        def buy_healing_potion():
            if self.data["coins"] < 200:
                messagebox.showerror("Shop", "Not enough coins for a Healing Potion!")
                return
            recovering = [
                (f"{girl} ({max(0, (600 - (get_current_time() - gd['recovery_start']))/60):.1f} min left)"
                 if gd["recovery_start"] is not None else girl,
                 girl)
                for girl, gd in self.data["inventory"].items()
                if gd["recovery_start"] is not None and not is_available(gd)
            ]
            if not recovering:
                messagebox.showinfo("Shop", "No girls are currently recovering!")
                return
            choice = self.select_from_list("Healing Potion", "Select a girl to fully heal:", recovering)
            if not choice:
                return
            gdata = self.data["inventory"][choice]
            self.data["coins"] -= 200
            gdata["recovery_start"] = None
            gdata["hp_at_start"] = None
            save_game(self.data)
            coins_var.set(f"Coins: {self.data['coins']}")
            self.update_resources()
            messagebox.showinfo("Shop", f"{choice} has been fully healed!")

        ttk.Button(win, text="Healing Potion - 200 coins", command=buy_healing_potion).pack(fill=tk.X, padx=20, pady=4)

        ttk.Label(win, text="Weapons (Boosts)", foreground=TEXT_FG, font=("Segoe UI", 11, "bold")).pack(pady=(16, 4))

        def buy_attack_boost():
            if self.data["coins"] < 1000:
                messagebox.showerror("Shop", "Not enough coins for an Attack Booster!")
                return
            girls_list = [(f"{girl} (Lv.{gd['level']})", girl) for girl, gd in self.data["inventory"].items()]
            if not girls_list:
                messagebox.showinfo("Shop", "You have no girls to boost!")
                return
            choice = self.select_from_list("Attack Booster", "Select a girl to boost attack:", girls_list)
            if not choice:
                return
            self.data["coins"] -= 1000
            gdata = self.data["inventory"][choice]
            gdata["attack_bonus"] = gdata.get("attack_bonus", 0) + 5
            save_game(self.data)
            coins_var.set(f"Coins: {self.data['coins']}")
            self.update_resources()
            messagebox.showinfo("Shop", f"{choice}'s attack increased by 5!")

        ttk.Button(win, text="Attack Booster - 1000 coins", command=buy_attack_boost).pack(fill=tk.X, padx=20, pady=4)

        ttk.Label(win, text="Materials", foreground=TEXT_FG, font=("Segoe UI", 11, "bold")).pack(pady=(16, 4))

        def buy_shard_bundle():
            if self.data["coins"] < 2000:
                messagebox.showerror("Shop", "Not enough coins for a Shard Bundle!")
                return
            self.data["coins"] -= 2000
            self.data["shards"] += 10
            save_game(self.data)
            coins_var.set(f"Coins: {self.data['coins']}")
            self.update_resources()
            messagebox.showinfo("Shop", "Purchased 10 shards!")

        ttk.Button(win, text="Shard Bundle - 2000 coins", command=buy_shard_bundle).pack(fill=tk.X, padx=20, pady=4)

        ttk.Button(win, text="Close", command=win.destroy).pack(pady=18)

    # ------------------------------------------------------------------
    # SCAVENGING
    # ------------------------------------------------------------------
    def gui_scavenging(self):
        win = self.open_window("Scavenging")
        win.geometry("500x400")
        win.configure(bg=BG_DARK)
        avail = [g for g, gd in self.data["inventory"].items() if is_available(gd)]
        if not avail:
            ttk.Label(win, text="No girls available!", foreground=TEXT_SUB).pack(pady=20)
            ttk.Button(win, text="Close", command=win.destroy).pack()
            return
        for girl in avail:
            frame = ttk.Frame(win, padding=5, style='Card.TFrame')
            frame.pack(fill=tk.X, pady=2, padx=10)
            ttk.Label(frame, text=f"{girl} Lv.{self.data['inventory'][girl]['level']}", foreground=TEXT_FG).pack(side=tk.LEFT)
            ttk.Button(frame, text="Send", command=lambda g=girl: self.send_scavenge(g)).pack(side=tk.RIGHT)
        ttk.Button(win, text="Close", command=win.destroy).pack(pady=10)

    def send_scavenge(self, girl):
        now = get_current_time()
        self.data["inventory"][girl]["scavenge_end"] = now + 300
        self.data["inventory"][girl]["scavenge_result"] = None
        save_game(self.data)
        messagebox.showinfo("Sent", f"{girl} sent scavenging for 5 minutes!")
        self.gui_scavenging()

    # ------------------------------------------------------------------
    # HEALING
    # ------------------------------------------------------------------
    def gui_healing(self):
        recovering = [g for g, gd in self.data["inventory"].items() if gd["recovery_start"] is not None and not is_available(gd)]
        if not recovering:
            messagebox.showinfo("Healing Session", "No girls are currently recovering!")
            return

        healers = [g for g, gd in self.data["inventory"].items()
                   if is_available(gd) and girls_data[g]["class"] == GirlClass.HEALER]
        if not healers:
            messagebox.showinfo("Healing Session", "No healers are available right now!")
            return

        win = self.open_window("Healing Session")
        win.geometry("520x320")
        win.configure(bg=BG_DARK)

        ttk.Label(win, text="Select recovering girl", foreground=TEXT_SUB).pack(pady=(12, 4))
        target_var = tk.StringVar(value=recovering[0])
        target_combo = ttk.Combobox(win, values=recovering, textvariable=target_var, state="readonly")
        target_combo.pack(fill=tk.X, padx=20)

        ttk.Label(win, text="Select healer", foreground=TEXT_SUB).pack(pady=(16, 4))
        healer_var = tk.StringVar(value=healers[0])
        healer_combo = ttk.Combobox(win, values=healers, textvariable=healer_var, state="readonly")
        healer_combo.pack(fill=tk.X, padx=20)

        def start_healing():
            target = target_var.get()
            healer = healer_var.get()
            if not target or not healer:
                messagebox.showerror("Healing Session", "Please select both a target and a healer.")
                return
            if target == healer:
                messagebox.showerror("Healing Session", "A girl cannot heal herself.")
                return
            now = get_current_time()
            fast_start = now - 420  # Jump ahead so only 3 minutes remain
            target_data = self.data["inventory"][target]
            healer_data = self.data["inventory"][healer]
            if target_data.get("hp_at_start") is None:
                target_stats = get_girl_stats(target, target_data["level"], self.data)
                target_data["hp_at_start"] = target_stats["hp"]
            if healer_data.get("hp_at_start") is None:
                healer_stats = get_girl_stats(healer, healer_data["level"], self.data)
                healer_data["hp_at_start"] = healer_stats["hp"]
            target_data["recovery_start"] = fast_start
            healer_data["recovery_start"] = fast_start
            save_game(self.data)
            messagebox.showinfo("Healing Session", f"{healer} is tending to {target}! They'll be back in ~3 minutes.")
            win.destroy()
            self.update_resources()

        ttk.Button(win, text="Start Healing", command=start_healing).pack(pady=18)
        ttk.Button(win, text="Close", command=win.destroy).pack()

    # ------------------------------------------------------------------
    # BOSS
    # ------------------------------------------------------------------
    def gui_boss(self):
        self.ensure_boss_state()

        if not self.data.get("cave_unlocked"):
            messagebox.showinfo("Dark Cave", "The cave is still sealed… Defeat more monsters to unlock it!")
            return

        win = self.open_window("Dark Cave")
        win.geometry("520x300")
        win.configure(bg=BG_DARK)

        ttk.Label(win, text="The Dark Cave is open!", font=("Segoe UI", 14, "bold"), foreground=ACCENT).pack(pady=12)
        ttk.Label(win,
                  text=f"Bosses defeated: {self.data['boss_defeat_counter']}",
                  foreground=TEXT_SUB).pack(pady=4)

        if self.data.get("active_boss"):
            boss = self.data["active_boss"]
            ttk.Label(win, text=f"Active Boss: {boss['name']} ({boss['rarity']})",
                      foreground=TEXT_FG).pack(pady=6)
            ttk.Label(win, text="Resume boss fights from the command-line version.",
                      foreground=TEXT_SUB).pack(pady=6)
        else:
            ttk.Label(win, text="Boss battles are not yet available in the GUI.",
                      foreground=TEXT_SUB).pack(pady=12)
            ttk.Label(win, text="Use the command-line mode for Dark Cave fights.",
                      foreground=TEXT_SUB).pack(pady=4)

        ttk.Button(win, text="Close", command=win.destroy).pack(pady=18)

    def select_from_list(self, title, prompt, options):
        """Display a modal selection dialog.

        options should be a list of (label, value) pairs.
        Returns the chosen value or None if cancelled.
        """
        if not options:
            return None

        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.configure(bg=BG_DARK)
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text=prompt, wraplength=320, foreground=TEXT_FG).pack(pady=12, padx=12)

        listbox = tk.Listbox(
            dialog,
            bg=BG_CARD,
            fg=TEXT_FG,
            selectbackground=ACCENT,
            activestyle='dotbox',
            height=min(10, len(options)),
            exportselection=False
        )
        for label, _ in options:
            listbox.insert(tk.END, label)
        listbox.pack(padx=12, pady=8, fill=tk.BOTH, expand=True)

        result = {"value": None}

        def confirm():
            sel = listbox.curselection()
            if not sel:
                return
            result["value"] = options[sel[0]][1]
            dialog.destroy()

        def cancel():
            dialog.destroy()

        ttk.Button(dialog, text="Select", command=confirm).pack(pady=(4, 2))
        ttk.Button(dialog, text="Cancel", command=cancel).pack(pady=(0, 10))

        dialog.wait_window()
        return result["value"]

    def simulate_battle(self, selected_girls, monster_template):
        monster = monster_template.copy()
        monster_max_hp = monster["hp"]
        team = []
        for girl in selected_girls:
            gdata = self.data["inventory"][girl]
            stats = get_girl_stats(girl, gdata["level"], self.data)
            team.append({
                "name": girl,
                "stats": stats,
                "hp": get_current_hp(girl, gdata, self.data),
                "max_hp": stats["hp"],
                "special_cd": 0,
                "defending": False,
                "shield": False,
                "class": girls_data[girl]["class"],
                "element": girls_data[girl]["element"]
            })

        log_lines = []
        turn = 0
        while monster["hp"] > 0 and any(g["hp"] > 0 for g in team):
            turn += 1
            log_lines.append(f"--- TURN {turn} ---")
            log_lines.append(f"{monster['name']} HP: {int(monster['hp'])}/{monster_max_hp}")

            for girl in team:
                if girl["hp"] <= 0:
                    continue
                log_lines.append(f"{girl['name']} ({int(girl['hp'])}/{girl['max_hp']}) takes action")
                action = self.choose_battle_action(girl, team)
                if action == "basic":
                    damage = max(1, girl["stats"]["attack"] - monster["defense"])
                    monster["hp"] -= damage
                    log_lines.append(f"  Basic attack deals {damage} damage")
                elif action == "special":
                    base = int(girl["stats"]["attack"] * 2.0)
                    multi = elemental_multiplier(girl["element"], monster["element"])
                    damage = max(1, int(base * multi) - monster["defense"])
                    monster["hp"] -= damage
                    girl["special_cd"] = 6
                    if multi > 1:
                        log_lines.append(f"  Special is super effective! {damage} damage")
                    elif multi < 1:
                        log_lines.append(f"  Special is not very effective… {damage} damage")
                    else:
                        log_lines.append(f"  Special deals {damage} damage")
                elif action == "shield":
                    for ally in team:
                        if ally["hp"] > 0:
                            ally["shield"] = True
                    girl["special_cd"] = 6
                    log_lines.append("  Casts a protective shield over the team")
                else:  # defend
                    girl["defending"] = True
                    log_lines.append("  Braces for impact")

                girl["special_cd"] = max(0, girl["special_cd"] - 1)
                if monster["hp"] <= 0:
                    break

            if monster["hp"] <= 0:
                break

            log_lines.append("--- Monster Turn ---")
            alive = [g for g in team if g["hp"] > 0]
            if not alive:
                break
            target = random.choice(alive)
            if target["defending"]:
                log_lines.append(f"{monster['name']} attacks {target['name']} but the attack is blocked!")
            elif target["shield"]:
                log_lines.append(f"{monster['name']}'s attack is absorbed by {target['name']}'s shield!")
                target["shield"] = False
            else:
                damage = max(1, monster["atk"] - target["stats"]["defense"])
                target["hp"] -= damage
                log_lines.append(f"{monster['name']} hits {target['name']} for {damage} damage ({int(max(0, target['hp']))} HP left)")
            for girl in team:
                girl["defending"] = False

        if monster["hp"] <= 0:
            log_lines.append("")
            log_lines.append(f"{monster['name']} defeated! +{monster['shards']} shards")
            self.data["shards"] += monster["shards"]
            self.handle_normal_victory()
        else:
            log_lines.append("")
            log_lines.append("The team was defeated…")

        now = get_current_time()
        for girl in selected_girls:
            gdata = self.data["inventory"][girl]
            final_hp = next((member["hp"] for member in team if member["name"] == girl), 1)
            gdata["recovery_start"] = now
            gdata["hp_at_start"] = max(1, int(final_hp))
            log_lines.append(f"{girl} is recovering with {int(max(1, final_hp))} HP")

        save_game(self.data)
        return "\n".join(log_lines)

    def choose_battle_action(self, girl, team):
        if girl["class"] == GirlClass.HEALER and girl["special_cd"] == 0:
            shields_active = all(ally["shield"] for ally in team if ally["hp"] > 0)
            if not shields_active:
                return "shield"
        if girl["special_cd"] == 0:
            return "special"
        if girl["hp"] / girl["max_hp"] < 0.35:
            return "defend"
        return "basic"

# ----------------------------------------------------------------------
# LAUNCH
# ----------------------------------------------------------------------
def run_gui():
    root = tk.Tk()
    app = GachaApp(root)
    root.mainloop()
