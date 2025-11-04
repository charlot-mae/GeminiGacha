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

# Element colours (kept, but toned down)
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
# Portrait placeholder (now with theme)
# ----------------------------------------------------------------------
def create_portrait(parent, girl_name, size=80):
    info = girls_data[girl_name]
    elem_col = ELEMENT_COLORS.get(info["element"], "#666666")
    rar_col  = RARITY_COLORS[info["rarity"]]
    canvas = tk.Canvas(parent, width=size, height=size, bg=BG_CARD, highlightthickness=0)
    canvas.create_oval(5, 5, size-5, size-5, fill=elem_col, outline=rar_col, width=3)
    canvas.create_text(size//2, size//2, text=girl_name[:3].upper(), fill="white", font=("Arial", 11, "bold"))
    return canvas

# ----------------------------------------------------------------------
# GUI App – only colour changes
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

        # Buttons
        style.configure('TButton',
                        background=BG_BTN,
                        foreground=TEXT_FG,
                        font=('Segoe UI', 10),
                        padding=8)
        style.map('TButton',
                  background=[('active', BG_BTN_HOVER), ('pressed', ACCENT)],
                  foreground=[('active', TEXT_FG)])

        # Labels
        style.configure('TLabel',
                        background=BG_DARK,
                        foreground=TEXT_FG,
                        font=('Segoe UI', 10))

        # Frames
        style.configure('Card.TFrame',
                        background=BG_CARD,
                        relief='flat',
                        borderwidth=1)

        # Scrollable text
        style.configure('Log.TFrame', background=BG_CARD)

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
    # Main Menu – updated colours
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
    # Pull results – pink accent
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Inventory – dark cards
    # ------------------------------------------------------------------
    def gui_inventory(self):
        win = tk.Toplevel(self.root)
        win.title("Inventory")
        win.geometry("820x620")
        win.configure(bg=BG_DARK)

        canvas = tk.Canvas(win, bg=BG_DARK, highlightthickness=0)
        scrollbar = ttk.Scrollbar(win, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas, style='Card.TFrame')

        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for girl, gdata in self.data["inventory"].items():
            frame = ttk.Frame(scrollable, padding=12, style='Card.TFrame')
            frame.pack(fill=tk.X, pady=5, padx=10)

            portrait = create_portrait(frame, girl, 60)
            portrait.pack(side=tk.LEFT, padx=10)

            stats = get_girl_stats(girl, gdata["level"], self.data)
            hp = int(get_current_hp(girl, gdata, self.data))
            info = girls_data[girl]

            ttk.Label(frame, text=f"{girl} Lv.{gdata['level']}", font=("Segoe UI", 12, "bold"), foreground=TEXT_FG).pack(anchor="w")
            ttk.Label(frame, text=f"{info['rarity']} | {info['element']} | {info['class']}", foreground=TEXT_SUB).pack(anchor="w")
            ttk.Label(frame, text=f"HP: {hp}/{stats['hp']}").pack(anchor="w")
            ttk.Label(frame, text=f"ATK {stats['attack']} | DEF {stats['defense']} | SPD {stats['speed']}").pack(anchor="w")
            ttk.Label(frame, text=info['catchline'], foreground="#999999", font=("Segoe UI", 9, "italic")).pack(anchor="w")

            if not is_available(gdata):
                if gdata.get("scavenge_end"):
                    left = max(0, 300 - (get_current_time() - (gdata["scavenge_end"] - 300))) / 60
                    ttk.Label(frame, text=f"Scavenging ({left:.1f} min)", foreground=WARN).pack()
                else:
                    left = max(0, 600 - (get_current_time() - gdata["recovery_start"])) / 60
                    ttk.Label(frame, text=f"Recovering ({left:.1f} min)", foreground=ERROR).pack()

            ttk.Button(frame, text="Details", command=lambda g=girl: self.show_girl_detail(g)).pack(pady=4)

    # ------------------------------------------------------------------
    # Other windows (battle log, shop, etc.) – use same BG
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
    # All other methods (training, dupes, shop, etc.) – unchanged
    # (just inherit the style)
    # ------------------------------------------------------------------
    # ... [rest of the class – no colour changes needed] ...

    def save_and_quit(self):
        save_game(self.data)
        self.root.quit()

# ----------------------------------------------------------------------
# Launch
# ----------------------------------------------------------------------
def run_gui():
    root = tk.Tk()
    app = GachaApp(root)
    root.mainloop()