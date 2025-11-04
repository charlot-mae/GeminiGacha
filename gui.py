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
    single_pull, ten_pull, show_inventory, show_dupes, turn_based_battle,
    training, healing_session, check_scavenging_results, scavenging,
    normal_victory_hook
)
from shop import show_shop
from bosses import boss_menu, normal_victory_hook as boss_victory_hook

# ----------------------------------------------------------------------
# Helper – color rectangles as placeholders for future portraits
# ----------------------------------------------------------------------
ELEMENT_COLORS = {
    "Fire": "#FF5555",
    "Water": "#5555FF",
    "Earth": "#8B4513",
    "Wind": "#55FF55"
}

RARITY_COLORS = {
    "Common": "#CCCCCC",
    "Uncommon": "#55AA55",
    "Rare": "#5555FF",
    "Epic": "#AA00AA",
    "Legendary": "#FFAA00"
}

def create_portrait(parent, girl_name, size=80):
    info = girls_data[girl_name]
    color = ELEMENT_COLORS.get(info["element"], "#888888")
    canvas = tk.Canvas(parent, width=size, height=size, bg=color, highlightthickness=0)
    canvas.create_oval(5, 5, size-5, size-5, fill=color, outline=RARITY_COLORS[info["rarity"]])
    canvas.create_text(size//2, size//2, text=girl_name[:2], fill="white", font=("Arial", 12, "bold"))
    return canvas

# ----------------------------------------------------------------------
# Main GUI Application
# ----------------------------------------------------------------------
class GachaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gemini Gacha")
        self.root.geometry("900x650")
        self.root.configure(bg="#222222")

        self.data = load_save()
        self.funcs = {
            "girls_data": girls_data,
            "elemental_multiplier": elemental_multiplier,
            "get_girl_stats": get_girl_stats,
            "get_current_hp": get_current_hp,
            "is_available": is_available,
            "get_current_time": get_current_time,
            "save_game": save_game,
        }

        self.create_main_menu()

    # ------------------------------------------------------------------
    # Main Menu
    # ------------------------------------------------------------------
    def create_main_menu(self):
        self.clear_frame()
        frame = ttk.Frame(self.root, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="GEMINI GACHA", font=("Arial", 20, "bold")).pack(pady=10)
        ttk.Label(frame, text=f"Coins: {self.data['coins']} | Shards: {self.data['shards']}").pack()

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
            ttk.Button(frame, text=text, command=cmd).pack(pady=5, fill=tk.X)

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------
    def clear_frame(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def save_and_quit(self):
        save_game(self.data)
        self.root.quit()

    # ------------------------------------------------------------------
    # Pulls
    # ------------------------------------------------------------------
    def single_pull(self):
        if self.data["coins"] < 100:
            messagebox.showerror("Error", "Not enough coins!")
            return
        self.data["coins"] -= 100
        self.perform_pull_gui()

    def ten_pull(self):
        if self.data["coins"] < 900:
            messagebox.showerror("Error", "Not enough coins!")
            return
        self.data["coins"] -= 900
        results = []
        for _ in range(10):
            results.append(self.perform_pull_core())
        self.show_pull_results(results)

    def perform_pull_gui(self):
        result = self.perform_pull_core()
        self.show_pull_results([result])

    def perform_pull_core(self):
        self.data["pull_count"] += 1
        self.data["rare_pity"] += 1
        self.data["legendary_pity"] += 1
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
        win = tk.Toplevel(self.root)
        win.title("Pull Results")
        win.geometry("500x600")
        win.configure(bg="#111111")

        for res in results:
            frame = ttk.Frame(win, padding=10)
            frame.pack(fill=tk.X, pady=5)

            canvas = create_portrait(frame, res["girl"], 70)
            canvas.pack(side=tk.LEFT)

            info = girls_data[res["girl"]]
            ttk.Label(frame, text=f"{res['girl']} ({res['rarity']})", font=("Arial", 12, "bold")).pack(anchor="w")
            ttk.Label(frame, text=f"{info['element']} | {info['class']}").pack(anchor="w")
            ttk.Label(frame, text=info['catchline'], foreground="#AAAAAA").pack(anchor="w")
            if res["new"]:
                ttk.Label(frame, text="NEW!", foreground="#00FF00", font=("Arial", 10, "bold")).pack(anchor="w")
            else:
                ttk.Label(frame, text="Duplicate", foreground="#FF5555").pack(anchor="w")

        ttk.Button(win, text="Close", command=win.destroy).pack(pady=10)

    def get_pull_rarity(self):
        if self.data["legendary_pity"] >= 100:
            return "Legendary"
        if self.data["rare_pity"] >= 50:
            return "Rare"
        return random.choices(
            ["Common", "Uncommon", "Rare", "Epic", "Legendary"],
            weights=[0.70, 0.20, 0.05, 0.04, 0.01]
        )[0]

    def get_girl_by_rarity(self, rarity):
        candidates = [g for g, d in girls_data.items() if d["rarity"] == rarity]
        return random.choice(candidates) if candidates else "Tama"

    # ------------------------------------------------------------------
    # Inventory
    # ------------------------------------------------------------------
    def gui_inventory(self):
        win = tk.Toplevel(self.root)
        win.title("Inventory")
        win.geometry("800x600")

        canvas = tk.Canvas(win)
        scrollbar = ttk.Scrollbar(win, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)

        scrollable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for girl, gdata in self.data["inventory"].items():
            frame = ttk.Frame(scrollable, relief="groove", padding=10)
            frame.pack(fill=tk.X, pady=5)

            portrait = create_portrait(frame, girl, 60)
            portrait.pack(side=tk.LEFT, padx=10)

            stats = get_girl_stats(girl, gdata["level"], self.data)
            hp = int(get_current_hp(girl, gdata, self.data))
            info = girls_data[girl]

            ttk.Label(frame, text=f"{girl} Lv.{gdata['level']}", font=("Arial", 12, "bold")).pack(anchor="w")
            ttk.Label(frame, text=f"{info['rarity']} | {info['element']} | {info['class']}").pack(anchor="w")
            ttk.Label(frame, text=f"HP: {hp}/{stats['hp']}").pack(anchor="w")
            ttk.Label(frame, text=f"ATK {stats['attack']} | DEF {stats['defense']} | SPD {stats['speed']}").pack(anchor="w")
            ttk.Label(frame, text=info['catchline'], foreground="#888888").pack(anchor="w")

            if not is_available(gdata):
                if gdata.get("scavenge_end"):
                    left = max(0, 300 - (get_current_time() - (gdata["scavenge_end"] - 300))) / 60
                    ttk.Label(frame, text=f"Scavenging ({left:.1f} min)", foreground="#FFAA00").pack()
                else:
                    left = max(0, 600 - (get_current_time() - gdata["recovery_start"])) / 60
                    ttk.Label(frame, text=f"Recovering ({left:.1f} min)", foreground="#FF5555").pack()

            ttk.Button(frame, text="Details", command=lambda g=girl: self.show_girl_detail(g)).pack(pady=5)

    def show_girl_detail(self, girl):
        gdata = self.data["inventory"][girl]
        stats = get_girl_stats(girl, gdata["level"], self.data)
        hp = int(get_current_hp(girl, gdata, self.data))
        info = girls_data[girl]

        win = tk.Toplevel(self.root)
        win.title(f"{girl} - Details")
        win.geometry("400x500")

        create_portrait(win, girl, 100).pack(pady=10)

        ttk.Label(win, text=f"{girl} Lv.{gdata['level']}", font=("Arial", 14, "bold")).pack()
        ttk.Label(win, text=f"{info['rarity']} | {info['element']} | {info['class']}").pack()
        ttk.Label(win, text=f"HP: {hp}/{stats['hp']}").pack()
        ttk.Label(win, text=f"ATK: {stats['attack']} | DEF: {stats['defense']} | SPD: {stats['speed']}").pack()
        ttk.Label(win, text=f"Skills: {', '.join(info['skills'])}").pack()
        ttk.Label(win, text=info['catchline'], foreground="#AAAAAA").pack(pady=10)

        ttk.Button(win, text="Close", command=win.destroy).pack(pady=10)

    # ------------------------------------------------------------------
    # Dupes
    # ------------------------------------------------------------------
    def gui_dupes(self):
        win = tk.Toplevel(self.root)
        win.title("Dupes")
        win.geometry("500x500")

        if not self.data["dupes"]:
            ttk.Label(win, text="No dupes!").pack(pady=20)
            ttk.Button(win, text="Close", command=win.destroy).pack()
            return

        for girl, count in self.data["dupes"].items():
            frame = ttk.Frame(win, padding=10)
            frame.pack(fill=tk.X)

            ttk.Label(frame, text=f"{girl}: {count}").pack(side=tk.LEFT)
            ttk.Button(frame, text="Sell 1", command=lambda g=girl: self.sell_dupe(g, 1)).pack(side=tk.RIGHT, padx=5)
            ttk.Button(frame, text="Sell All", command=lambda g=girl: self.sell_dupe(g, count)).pack(side=tk.RIGHT)

        ttk.Button(win, text="Close", command=win.destroy).pack(pady=10)

    def sell_dupe(self, girl, amt):
        current = self.data["dupes"][girl]
        sell_amt = min(amt, current)
        self.data["coins"] += sell_amt * 100
        self.data["dupes"][girl] -= sell_amt
        if self.data["dupes"][girl] == 0:
            del self.data["dupes"][girl]
        save_game(self.data)
        messagebox.showinfo("Sold", f"Sold {sell_amt} dupe(s) of {girl} for {sell_amt*100} coins!")
        self.gui_dupes()

    # ------------------------------------------------------------------
    # Battle (simplified – uses text log)
    # ------------------------------------------------------------------
    def gui_battle(self):
        # Reuse console logic but capture output
        import io
        from contextlib import redirect_stdout

        log = io.StringIO()
        with redirect_stdout(log):
            turn_based_battle(self.data)

        win = tk.Toplevel(self.root)
        win.title("Battle Log")
        win.geometry("700x600")

        text = scrolledtext.ScrolledText(win, wrap=tk.WORD, font=("Courier", 10))
        text.pack(fill=tk.BOTH, expand=True)
        text.insert(tk.END, log.getvalue())
        text.config(state=tk.DISABLED)

        ttk.Button(win, text="Close", command=win.destroy).pack(pady=5)

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------
    def gui_training(self):
        win = tk.Toplevel(self.root)
        win.title("Training")
        win.geometry("500x500")

        girls = list(self.data["inventory"].keys())
        if not girls:
            ttk.Label(win, text="No girls!").pack()
            return

        for girl in girls:
            gdata = self.data["inventory"][girl]
            level = gdata["level"]
            cost = 10 * (level + 1) ** 2
            frame = ttk.Frame(win, padding=5)
            frame.pack(fill=tk.X)

            ttk.Label(frame, text=f"{girl} Lv.{level} (Cost: {cost})").pack(side=tk.LEFT)
            ttk.Button(frame, text="Train", command=lambda g=girl: self.train_girl(g, cost)).pack(side=tk.RIGHT)

        ttk.Button(win, text="Close", command=win.destroy).pack(pady=10)

    def train_girl(self, girl, cost):
        if self.data["shards"] < cost:
            messagebox.showerror("Error", "Not enough shards!")
            return
        self.data["shards"] -= cost
        self.data["inventory"][girl]["level"] += 1
        save_game(self.data)
        messagebox.showinfo("Success", f"{girl} is now Lv.{self.data['inventory'][girl]['level']}!")
        self.gui_training()

    # ------------------------------------------------------------------
    # Shop
    # ------------------------------------------------------------------
    def gui_shop(self):
        import io
        from contextlib import redirect_stdout, redirect_stderr

        log = io.StringIO()
        with redirect_stdout(log), redirect_stderr(log):
            show_shop(self.data, girls_data, get_current_time, is_available, save_game, "gacha_save.json")

        win = tk.Toplevel(self.root)
        win.title("Shop Log")
        win.geometry("700x500")

        text = scrolledtext.ScrolledText(win, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True)
        text.insert(tk.END, log.getvalue())
        text.config(state=tk.DISABLED)

        ttk.Button(win, text="Close", command=win.destroy).pack(pady=5)

    # ------------------------------------------------------------------
    # Scavenging
    # ------------------------------------------------------------------
    def gui_scavenging(self):
        win = tk.Toplevel(self.root)
        win.title("Scavenging")
        win.geometry("500x400")

        avail = [g for g, gd in self.data["inventory"].items() if is_available(gd)]
        if not avail:
            ttk.Label(win, text="No girls available!").pack(pady=20)
            ttk.Button(win, text="Close", command=win.destroy).pack()
            return

        for girl in avail:
            frame = ttk.Frame(win, padding=5)
            frame.pack(fill=tk.X)
            ttk.Label(frame, text=f"{girl} Lv.{self.data['inventory'][girl]['level']}").pack(side=tk.LEFT)
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
    # Healing
    # ------------------------------------------------------------------
    def gui_healing(self):
        import io
        from contextlib import redirect_stdout

        log = io.StringIO()
        with redirect_stdout(log):
            healing_session(self.data)

        win = tk.Toplevel(self.root)
        win.title("Healing Session")
        win.geometry("600x400")

        text = scrolledtext.ScrolledText(win, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True)
        text.insert(tk.END, log.getvalue())
        text.config(state=tk.DISABLED)

        ttk.Button(win, text="Close", command=win.destroy).pack(pady=5)

    # ------------------------------------------------------------------
    # Boss Cave
    # ------------------------------------------------------------------
    def gui_boss(self):
        boss_menu(self.data, self.funcs)

# ----------------------------------------------------------------------
# Launch GUI from main.py
# ----------------------------------------------------------------------
def run_gui():
    root = tk.Tk()
    app = GachaApp(root)
    root.mainloop()