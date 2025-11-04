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
from bosses import boss_menu

# ----------------------------------------------------------------------
# DARK BLUE + PINK THEME
# ----------------------------------------------------------------------
BG_DARK = "#0A1A2F"          # window bg
BG_CARD = "#112240"          # frames, cards
BG_BTN  = "#1E3A5F"          # button normal
BG_BTN_HOVER = "#2A5588"     # button hover
ACCENT  = "#FF6BC1"          # pink highlights
TEXT_FG = "#E0E7FF"          # main text
TEXT_SUB = "#A0B8E0"         # secondary text
SUCCESS = "#66FFB3"
WARN    = "#FFB366"
ERROR   = "#FF6B6B"

# Element colours
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

    # ------------------------------------------------------------------
    # Portrait – now a *rounded* image that fits the dark theme
    # ------------------------------------------------------------------
def create_portrait(self, parent, girl_name, size=70):
    info = girls_data[girl_name]
    # element colour → fill, rarity colour → border
    fill  = ELEMENT_COLORS.get(info["element"], "#666666")
    border = RARITY_COLORS[info["rarity"]]

    canvas = tk.Canvas(parent, width=size, height=size,
        bg=BG_CARD, highlightthickness=0)
    # dark‑card background for the circle
    canvas.create_oval(4, 4, size-4, size-4, fill=fill, outline=border, width=3)
    # first 3 letters – big, white, bold
    canvas.create_text(size//2, size//2,
        text=girl_name[:3].upper(),
        fill="white", font=("Segoe UI", 12, "bold"))
    return canvas

# ----------------------------------------------------------------------
# Main GUI Application
# ----------------------------------------------------------------------
class GachaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gemstone Gacha")
        self.root.geometry("920x680")
        self.root.configure(bg=BG_DARK)

        # ---- STYLE CONFIG ----
        style = ttk.Style()
        style.theme_use('clam')

        style.configure('TButton',
                        background=BG_BTN,
                        foreground=TEXT_FG,
                        font=('Segoe UI', 10),
                        padding=8)
        style.map('TButton',
                  background=[('active', BG_BTN_HOVER), ('pressed', ACCENT)],
                  foreground=[('active', TEXT_FG)])

        style.configure('TLabel',
                        background=BG_DARK,
                        foreground=TEXT_FG,
                        font=('Segoe UI', 10))

        style.configure('Card.TFrame',
                        background=BG_CARD,
                        relief='flat',
                        borderwidth=1)

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
    # Utility: Clear window
    # ------------------------------------------------------------------
    def clear_frame(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    # ------------------------------------------------------------------
    # Main Menu
    # ------------------------------------------------------------------
    def create_main_menu(self):
        self.clear_frame()
        frame = ttk.Frame(self.root, padding=25, style='Card.TFrame')
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="GEMSTONE GACHA", font=("Segoe UI", 22, "bold"), foreground=ACCENT).pack(pady=12)
        ttk.Label(frame, text=f"Coins: {self.data['coins']} | Shards: {self.data['shards']}",
                  font=("Segoe UI", 11), foreground=TEXT_SUB).pack(pady=5)

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
            btn = ttk.Button(frame, text=text, command=cmd)
            btn.pack(pady=6, fill=tk.X, padx=50)

    # ------------------------------------------------------------------
    # Save & Quit
    # ------------------------------------------------------------------
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
        win.geometry("520x640")
        win.configure(bg=BG_DARK)

        for res in results:
            frame = ttk.Frame(win, padding=12, style='Card.TFrame')
            frame.pack(fill=tk.X, pady=6, padx=12)

            canvas = create_portrait(frame, res["girl"], 70)
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
    # INVENTORY – **NO WHITE SPOTS, NO BLANK RIGHT‑SIDE**
    # ------------------------------------------------------------------
    def gui_inventory(self):
        win = tk.Toplevel(self.root)
        win.title("Inventory")
        win.geometry("840x640")
        win.configure(bg=BG_DARK)

        # ---------- MAIN container ----------
        main = ttk.Frame(win, padding=12)
        main.pack(fill=tk.BOTH, expand=True)

        # ---------- CANVAS + SCROLLBAR ----------
        canvas = tk.Canvas(main, bg=BG_DARK, highlightthickness=0)
        vbar   = ttk.Scrollbar(main, orient="vertical", command=canvas.yview)
        inner  = ttk.Frame(canvas, style='Card.TFrame')          # dark card background

        # make the inner frame fill the canvas width
        def _resize(event):
            canvas.itemconfig(inner_id, width=event.width - 20)
        inner_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=vbar.set)
        canvas.bind("<Configure>", _resize)

        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.pack(side="left", fill="both", expand=True)
        vbar.pack(side="right", fill="y")

        # ---------- POPULATE GIRLS ----------
        for girl, gdata in self.data["inventory"].items():
            # each girl = one dark card
            card = ttk.Frame(inner, padding=12, style='Card.TFrame')
            card.pack(fill=tk.X, pady=6, padx=10)

            # ---- LEFT: portrait ----
            portrait = self.create_portrait(card, girl, 70)
            portrait.pack(side=tk.LEFT, padx=(0, 14))

            # ---- RIGHT: all text (vertical stack) ----
            txt = ttk.Frame(card)
            txt.pack(side=tk.LEFT, fill=tk.X, expand=True)

            stats = get_girl_stats(girl, gdata["level"], self.data)
            hp    = int(get_current_hp(girl, gdata, self.data))
            info  = girls_data[girl]

            # name + level
            ttk.Label(txt, text=f"{girl} Lv.{gdata['level']}",
                      font=("Segoe UI", 13, "bold"), foreground=TEXT_FG).pack(anchor="w")

            # rarity | element | class
            ttk.Label(txt, text=f"{info['rarity']} | {info['element']} | {info['class']}",
                      foreground=TEXT_SUB, font=("Segoe UI", 10)).pack(anchor="w")

            # HP – colour‑coded
            hp_ratio = hp / stats['hp']
            hp_col = ERROR if hp_ratio <= 0.3 else WARN if hp_ratio <= 0.7 else SUCCESS
            ttk.Label(txt, text=f"HP: {hp}/{stats['hp']}", foreground=hp_col).pack(anchor="w")

            # ATK / DEF / SPD
            ttk.Label(txt, text=f"ATK {stats['attack']} | DEF {stats['defense']} | SPD {stats['speed']}",
                      foreground=TEXT_SUB).pack(anchor="w")

            # catchline
            ttk.Label(txt, text=info['catchline'],
                      foreground="#999999", font=("Segoe UI", 9, "italic")).pack(anchor="w")

            # status (scavenge / recover)
            if not is_available(gdata):
                if gdata.get("scavenge_end"):
                    left = max(0, 300 - (get_current_time() - (gdata["scavenge_end"] - 300))) / 60
                    status, col = f"Scavenging ({left:.1f} min)", WARN
                else:
                    left = max(0, 600 - (get_current_time() - gdata["recovery_start"])) / 60
                    status, col = f"Recovering ({left:.1f} min)", ERROR
                ttk.Label(txt, text=status, foreground=col, font=("Segoe UI", 9)).pack(anchor="w")

            # details button
            ttk.Button(txt, text="Details",
                       command=lambda g=girl: self.show_girl_detail(g)).pack(anchor="w", pady=6)

        # ---------- CLOSE ----------
        ttk.Button(main, text="Close", command=win.destroy).pack(pady=12)

    def show_girl_detail(self, girl):
        gdata = self.data["inventory"][girl]
        stats = get_girl_stats(girl, gdata["level"], self.data)
        hp = int(get_current_hp(girl, gdata, self.data))
        info = girls_data[girl]

        win = tk.Toplevel(self.root)
        win.title(f"{girl} - Details")
        win.geometry("400x500")
        win.configure(bg=BG_DARK)

        create_portrait(win, girl, 100).pack(pady=10)

        ttk.Label(win, text=f"{girl} Lv.{gdata['level']}", font=("Segoe UI", 14, "bold"), foreground=TEXT_FG).pack()
        ttk.Label(win, text=f"{info['rarity']} | {info['element']} | {info['class']}", foreground=TEXT_SUB).pack()
        ttk.Label(win, text=f"HP: {hp}/{stats['hp']}").pack()
        ttk.Label(win, text=f"ATK: {stats['attack']} | DEF: {stats['defense']} | SPD: {stats['speed']}").pack()
        ttk.Label(win, text=f"Skills: {', '.join(info['skills'])}").pack()
        ttk.Label(win, text=info['catchline'], foreground="#AAAAAA", font=("Segoe UI", 9, "italic")).pack(pady=10)

        ttk.Button(win, text="Close", command=win.destroy).pack(pady=10)

    # ------------------------------------------------------------------
    # Dupes
    # ------------------------------------------------------------------
    def gui_dupes(self):
        win = tk.Toplevel(self.root)
        win.title("Dupes")
        win.geometry("500x500")
        win.configure(bg=BG_DARK)

        if not self.data["dupes"]:
            ttk.Label(win, text="No dupes!", foreground=TEXT_SUB).pack(pady=20)
            ttk.Button(win, text="Close", command=win.destroy).pack()
            return

        for girl, count in self.data["dupes"].items():
            frame = ttk.Frame(win, padding=10, style='Card.TFrame')
            frame.pack(fill=tk.X, pady=2, padx=10)

            ttk.Label(frame, text=f"{girl}: {count}", foreground=TEXT_FG).pack(side=tk.LEFT)
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
    # Battle (log)
    # ------------------------------------------------------------------
    def gui_battle(self):
        import io
        from contextlib import redirect_stdout
        log = io.StringIO()
        with redirect_stdout(log):
            turn_based_battle(self.data)

        win = tk.Toplevel(self.root)
        win.title("Battle Log")
        win.geometry("720x620")
        win.configure(bg=BG_DARK)

        text = scrolledtext.ScrolledText(win, wrap=tk.WORD, font=("Consolas", 10), bg=BG_CARD, fg=TEXT_FG)
        text.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        text.insert(tk.END, log.getvalue())
        text.config(state=tk.DISABLED)

        ttk.Button(win, text="Close", command=win.destroy).pack(pady=8)

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------
    def gui_training(self):
        win = tk.Toplevel(self.root)
        win.title("Training")
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
        win.configure(bg=BG_DARK)

        text = scrolledtext.ScrolledText(win, wrap=tk.WORD, bg=BG_CARD, fg=TEXT_FG)
        text.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
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
        win.configure(bg=BG_DARK)

        text = scrolledtext.ScrolledText(win, wrap=tk.WORD, bg=BG_CARD, fg=TEXT_FG)
        text.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        text.insert(tk.END, log.getvalue())
        text.config(state=tk.DISABLED)

        ttk.Button(win, text="Close", command=win.destroy).pack(pady=5)

    # ------------------------------------------------------------------
    # Boss Cave
    # ------------------------------------------------------------------
    def gui_boss(self):
        boss_menu(self.data, self.funcs)

# ----------------------------------------------------------------------
# Launch
# ----------------------------------------------------------------------
def run_gui():
    root = tk.Tk()
    app = GachaApp(root)
    root.mainloop()