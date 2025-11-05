import tkinter as tk
from tkinter import ttk, messagebox
import random
import os
import json
from bosses import BOSS_POOL


# Color theme: dark blue base with pink accents
BG_DARK = "#0A1A2F"
BG_CARD = "#112240"
BG_BTN = "#1E3A5F"
BG_BTN_HOVER = "#2A5588"
ACCENT = "#FF6BC1"
TEXT_FG = "#E0E7FF"
TEXT_SUB = "#A0B8E0"
SUCCESS = "#66FFB3"
WARN = "#FFB366"
ERROR = "#FF6B6B"

ELEMENT_COLORS = {
    "Fire": "#FF5555",
    "Water": "#4D7CFF",
    "Earth": "#8B6F47",
    "Wind": "#55AA55",
}

RARITY_COLORS = {
    "Common": "#888888",
    "Uncommon": "#55AA55",
    "Rare": "#4D7CFF",
    "Epic": "#AA00AA",
    "Legendary": "#FFAA00",
}


class GachaApp:
    def __init__(self, root, data, api):
        self.root = root
        self.data = data
        self.api = api

        # Extract frequently used items from api
        self.girls_data = api["girls_data"]
        self.get_girl_stats = api["get_girl_stats"]
        self.get_current_hp = api["get_current_hp"]
        self.is_available = api["is_available"]
        self.get_current_time = api["get_current_time"]
        self.save_game = api["save_game"]
        self.SINGLE_PULL_COST = api["SINGLE_PULL_COST"]
        self.TEN_PULL_COST = api["TEN_PULL_COST"]
        self.monsters = api.get("monsters", [])
        self.normal_victory_hook = api.get("normal_victory_hook")
        self.elemental_multiplier = api.get("elemental_multiplier", lambda a,b: 1.0)

        self.CLASS_HEALER = "Healer"

        self.root.title("Gemstone Gacha")
        self.root.configure(bg=BG_DARK)
        self.root.geometry("1000x680")
        self.root.minsize(860, 560)
        self.root.protocol("WM_DELETE_WINDOW", self._quit)

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TButton", background=BG_BTN, foreground=TEXT_FG, padding=8, font=("Segoe UI", 10))
        style.map(
            "TButton",
            background=[("active", BG_BTN_HOVER), ("pressed", ACCENT)],
            foreground=[("active", TEXT_FG)],
        )
        style.configure("TLabel", background=BG_DARK, foreground=TEXT_FG, font=("Segoe UI", 10))
        style.configure("Card.TFrame", background=BG_CARD)

        self.header = None
        self._ensure_boss_state()
        self._build_main()
        # periodic tick to process scavenging results
        self.root.after(3000, self._tick)
        # periodic header refresh to reflect unsaved status
        self.root.after(2000, self._refresh_header_loop)

    def _element_badge(self, parent, element, size=14, bg=None):
        bg = bg or BG_CARD
        color = ELEMENT_COLORS.get(element, "#666666")
        cv = tk.Canvas(parent, width=size, height=size, bg=bg, highlightthickness=0)
        cv.create_oval(1, 1, size - 1, size - 1, fill=color, outline="#000000", width=1)
        if size >= 14:
            try:
                cv.create_text(size // 2, size // 2, text=element[0], fill="white", font=("Segoe UI", 8, "bold"))
            except Exception:
                pass
        return cv

    def _ensure_boss_state(self):
        self.data.setdefault("boss_defeat_counter", 0)
        self.data.setdefault("cave_unlocked", False)
        self.data.setdefault("active_boss", None)
        self.data.setdefault("boss_fight_state", None)

    # UI builders
    def _build_main(self):
        container = ttk.Frame(self.root, style="Card.TFrame", padding=16)
        container.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(container, text="GEMSTONE GACHA", font=("Segoe UI", 22, "bold"))
        title.configure(foreground=ACCENT)
        title.pack(anchor="w")

        self.header = ttk.Label(
            container,
            text=self._status_text(),
            font=("Segoe UI", 11),
            foreground=TEXT_SUB,
        )
        self.header.pack(anchor="w", pady=(2, 12))

        # Buttons row
        grid = ttk.Frame(container)
        grid.pack(fill=tk.BOTH, expand=False)

        def add_btn(r, c, text, cmd, width=22):
            b = ttk.Button(grid, text=text, command=cmd)
            b.grid(row=r, column=c, padx=6, pady=6, sticky="ew")
            grid.grid_columnconfigure(c, weight=1, minsize=160)
            return b

        add_btn(0, 0, f"Single Pull (-{self.SINGLE_PULL_COST})", self.single_pull)
        add_btn(0, 1, f"10 Pull (-{self.TEN_PULL_COST})", self.ten_pull)
        add_btn(0, 2, "Save", self._save)

        add_btn(1, 0, "Inventory", self.open_inventory)
        add_btn(1, 1, "Dupes", self.open_dupes)
        add_btn(1, 2, "Shop", self.open_shop)

        add_btn(2, 0, "Training", self.open_training)
        add_btn(2, 1, "Scavenging", self.open_scavenging)
        add_btn(2, 2, "Healing Session", self.open_healing)

        add_btn(3, 0, "Battle", self.open_battle)
        add_btn(3, 1, "Dark Cave", self.open_boss)
        add_btn(3, 2, "Quit", self._quit)

        # Info
        hint = ttk.Label(
            container,
            text="Tip: Use Inventory to view stats and recovery/scavenge status.",
            foreground=TEXT_SUB,
        )
        hint.pack(anchor="w", pady=(16, 0))

        ttk.Button(container, text="Element Guide", command=self.open_element_guide).pack(anchor="w", pady=(8, 0))

    def open_element_guide(self):
        win = tk.Toplevel(self.root)
        win.title("Element Guide")
        win.configure(bg=BG_DARK)
        win.geometry("520x340")

        box = ttk.Frame(win, style="Card.TFrame", padding=12)
        box.pack(fill=tk.BOTH, expand=True)

        ttk.Label(box, text="Elemental Effectiveness", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        ttk.Label(box, text="Damage multipliers by attacker vs defender.", foreground=TEXT_SUB).pack(anchor="w")

        grid = ttk.Frame(box, style="Card.TFrame")
        grid.pack(pady=8)

        elements = list(ELEMENT_COLORS.keys())
        header_font = ("Segoe UI", 10, "bold")

        ttk.Label(grid, text="Att \\ Def", font=header_font).grid(row=0, column=0, padx=6, pady=4)
        for j, de in enumerate(elements, start=1):
            ttk.Label(grid, text=de, font=header_font).grid(row=0, column=j, padx=6, pady=4)

        for i, at in enumerate(elements, start=1):
            ttk.Label(grid, text=at, font=header_font).grid(row=i, column=0, padx=6, pady=4)
            for j, de in enumerate(elements, start=1):
                multi = self.elemental_multiplier(at, de) or 1.0
                col = SUCCESS if multi > 1 else WARN if multi < 1 else TEXT_SUB
                ttk.Label(grid, text=f"{multi:.1f}x", foreground=col).grid(row=i, column=j, padx=6, pady=4)

        ttk.Label(
            box,
            text=(
                "Super effective > 1.0x  |  Not very effective < 1.0x.\n"
                "Applies to basic attacks and relevant specials for both sides."
            ),
            foreground=TEXT_SUB,
            wraplength=480,
        ).pack(anchor="w", pady=(8, 0))

        ttk.Button(box, text="Close", command=win.destroy).pack(pady=8)

    def _status_text(self):
        txt = (
            f"Coins: {self.data.get('coins', 0)} | "
            f"Shards: {self.data.get('shards', 0)} | "
            f"Pulls: {self.data.get('pull_count', 0)} | "
            f"Pity: Rare {self.data.get('rare_pity', 0)}/50, "
            f"Legendary {self.data.get('legendary_pity', 0)}/100"
        )
        try:
            if self._has_unsaved_changes():
                txt += "  • unsaved"
        except Exception:
            pass
        return txt

    def _refresh_header(self):
        if self.header is not None:
            self.header.configure(text=self._status_text())

    def _refresh_header_loop(self):
        try:
            self._refresh_header()
        finally:
            self.root.after(2000, self._refresh_header_loop)

    def _save(self):
        self.save_game(self.data)
        messagebox.showinfo("Saved", "Progress saved.")
        self._refresh_header()

    def _quit(self):
        try:
            has_changes = self._has_unsaved_changes()
        except Exception:
            has_changes = True

        if has_changes:
            resp = messagebox.askyesnocancel(
                "Quit",
                "You have unsaved changes. Save before quitting?",
                icon=messagebox.WARNING,
                default=messagebox.YES,
            )
            if resp is None:
                return
            if resp is True:
                self.save_game(self.data)
                self.root.destroy()
            else:
                self.root.destroy()
        else:
            self.root.destroy()

    def _has_unsaved_changes(self):
        path = "gacha_save.json"
        if not os.path.exists(path):
            return True
        try:
            with open(path, "r", encoding="utf-8") as f:
                on_disk = json.load(f)
        except Exception:
            return True
        return on_disk != self.data

    # Drawing helpers
    def _portrait(self, parent, girl_name, size=64):
        info = self.girls_data[girl_name]
        fill = ELEMENT_COLORS.get(info["element"], "#666666")
        border = RARITY_COLORS.get(info["rarity"], "#777777")
        cv = tk.Canvas(parent, width=size, height=size, bg=BG_CARD, highlightthickness=0)
        cv.create_oval(4, 4, size - 4, size - 4, fill=fill, outline=border, width=3)
        cv.create_text(
            size // 2,
            size // 2,
            text=girl_name[:3].upper(),
            fill="white",
            font=("Segoe UI", 11, "bold"),
        )
        return cv

    # Gacha core
    def _get_pull_rarity(self):
        if self.data.get("legendary_pity", 0) >= 100:
            return "Legendary"
        if self.data.get("rare_pity", 0) >= 50:
            return "Rare"
        return random.choices(
            ["Common", "Uncommon", "Rare", "Epic", "Legendary"],
            weights=[0.70, 0.20, 0.05, 0.04, 0.01],
        )[0]

    def _get_girl_by_rarity(self, rarity):
        candidates = [g for g, d in self.girls_data.items() if d["rarity"] == rarity]
        return random.choice(candidates) if candidates else "Tama"

    def _perform_pull_core(self):
        self.data["pull_count"] = self.data.get("pull_count", 0) + 1
        self.data["rare_pity"] = self.data.get("rare_pity", 0) + 1
        self.data["legendary_pity"] = self.data.get("legendary_pity", 0) + 1
        rarity = self._get_pull_rarity()
        girl = self._get_girl_by_rarity(rarity)

        if rarity in ("Rare", "Epic", "Legendary"):
            self.data["rare_pity"] = 0
        if rarity == "Legendary":
            self.data["legendary_pity"] = 0

        new = False
        inv = self.data.setdefault("inventory", {})
        dup = self.data.setdefault("dupes", {})
        if girl not in inv:
            inv[girl] = {
                "level": 1,
                "recovery_start": None,
                "hp_at_start": None,
                "attack_bonus": 0,
                "stars": 0,
                "scavenge_end": None,
                "scavenge_result": None,
            }
            new = True
        else:
            dup[girl] = dup.get(girl, 0) + 1

        return {"girl": girl, "rarity": rarity, "new": new}

    # Background processing
    def _tick(self):
        # process scavenging completions
        completed_msgs = []
        now = self.get_current_time()
        for girl, gdata in list(self.data.get("inventory", {}).items()):
            end_time = gdata.get("scavenge_end")
            if end_time and now >= end_time and gdata.get("scavenge_result") is None:
                success = random.random() < 0.30
                shards = random.randint(15, 35) if success else 0
                gdata["scavenge_result"] = {"success": success, "shards": shards}
                if success:
                    self.data["shards"] = self.data.get("shards", 0) + shards
                    completed_msgs.append(f"{girl} found {shards} shards")
                else:
                    completed_msgs.append(f"{girl} returned empty-handed")
                gdata["scavenge_end"] = None
                gdata["scavenge_result"] = None
        if completed_msgs:
            self._refresh_header()
            self.save_game(self.data)
            messagebox.showinfo("Scavenging", "\n".join(completed_msgs))
        # reschedule
        self.root.after(5000, self._tick)

    # Actions
    def single_pull(self):
        if self.data.get("coins", 0) < self.SINGLE_PULL_COST:
            messagebox.showerror("Not enough coins", f"Need {self.SINGLE_PULL_COST} coins.")
            return
        coins_before = self.data.get("coins", 0)
        rare_before = self.data.get("rare_pity", 0)
        leg_before = self.data.get("legendary_pity", 0)
        self.data["coins"] -= self.SINGLE_PULL_COST
        res = self._perform_pull_core()
        self._refresh_header()
        summary = {
            "coins_before": coins_before,
            "coins_after": self.data.get("coins", 0),
            "rare_before": rare_before,
            "rare_after": self.data.get("rare_pity", 0),
            "legendary_before": leg_before,
            "legendary_after": self.data.get("legendary_pity", 0),
        }
        self._show_pull_results([res], summary)

    def ten_pull(self):
        if self.data.get("coins", 0) < self.TEN_PULL_COST:
            messagebox.showerror("Not enough coins", f"Need {self.TEN_PULL_COST} coins.")
            return
        coins_before = self.data.get("coins", 0)
        rare_before = self.data.get("rare_pity", 0)
        leg_before = self.data.get("legendary_pity", 0)
        self.data["coins"] -= self.TEN_PULL_COST
        results = [self._perform_pull_core() for _ in range(10)]
        self._refresh_header()
        summary = {
            "coins_before": coins_before,
            "coins_after": self.data.get("coins", 0),
            "rare_before": rare_before,
            "rare_after": self.data.get("rare_pity", 0),
            "legendary_before": leg_before,
            "legendary_after": self.data.get("legendary_pity", 0),
        }
        self._show_pull_results(results, summary)

    def _show_pull_results(self, results, summary=None):
        win = tk.Toplevel(self.root)
        win.title("Pull Results")
        win.configure(bg=BG_DARK)
        win.geometry("520x640")

        wrapper = ttk.Frame(win, style="Card.TFrame", padding=12)
        wrapper.pack(fill=tk.BOTH, expand=True)

        # Summary header (coins + pity deltas)
        if summary:
            coins_b = summary.get("coins_before", 0)
            coins_a = summary.get("coins_after", coins_b)
            delta_c = coins_a - coins_b
            pity_row = ttk.Frame(wrapper, style="Card.TFrame")
            pity_row.pack(fill=tk.X, pady=(0, 8))
            ttk.Label(
                pity_row,
                text=f"Coins: {coins_a} ({delta_c:+d})",
                foreground=(WARN if delta_c < 0 else SUCCESS if delta_c > 0 else TEXT_SUB),
            ).pack(anchor="w")
            rb = summary.get("rare_before", 0)
            ra = summary.get("rare_after", rb)
            lb = summary.get("legendary_before", 0)
            la = summary.get("legendary_after", lb)
            ttk.Label(
                pity_row,
                text=f"Pity → Rare {rb} → {ra}, Legendary {lb} → {la}",
                foreground=TEXT_SUB,
            ).pack(anchor="w")

        # New vs Dupes summary
        try:
            new_count = sum(1 for r in results if r.get("new"))
            dup_count = max(0, len(results) - new_count)
            ttk.Label(
                wrapper,
                text=f"New: {new_count}  |  Dupes: {dup_count}",
                foreground=TEXT_SUB,
            ).pack(anchor="w", pady=(0, 6))
        except Exception:
            pass

        for res in results:
            card = ttk.Frame(wrapper, style="Card.TFrame", padding=10)
            card.pack(fill=tk.X, pady=6)

            tk.Frame(card, bg=(SUCCESS if res["new"] else WARN), width=6, height=1).pack(
                side=tk.LEFT, fill=tk.Y, padx=(0, 8)
            )

            self._portrait(card, res["girl"], 64).pack(side=tk.LEFT, padx=(0, 12))
            info = self.girls_data[res["girl"]]

            txt = ttk.Frame(card, style="Card.TFrame")
            txt.pack(side=tk.LEFT, fill=tk.X, expand=True)

            name_row = ttk.Frame(txt, style="Card.TFrame")
            name_row.pack(anchor="w")
            ttk.Label(
                name_row,
                text=f"{res['girl']} ({res['rarity']})",
                font=("Segoe UI", 12, "bold"),
            ).pack(side=tk.LEFT)
            try:
                stars = self.data.get("inventory", {}).get(res["girl"], {}).get("stars", 0)
                if stars > 0:
                    ttk.Label(name_row, text=f" ★x{stars}", foreground=ACCENT).pack(side=tk.LEFT, padx=(6, 0))
            except Exception:
                pass
            line = ttk.Frame(txt, style="Card.TFrame")
            line.pack(anchor="w")
            self._element_badge(line, info['element'], size=14, bg=BG_CARD).pack(side=tk.LEFT, padx=(0,6))
            ttk.Label(line, text=f"{info['element']} | {info['class']}", foreground=TEXT_SUB).pack(side=tk.LEFT)
            ttk.Label(
                txt,
                text=info["catchline"],
                foreground="#BBBBBB",
                font=("Segoe UI", 9, "italic"),
            ).pack(anchor="w")
            ttk.Label(
                txt,
                text=("NEW!" if res["new"] else "Duplicate"),
                foreground=(SUCCESS if res["new"] else WARN),
                font=("Segoe UI", 10, "bold"),
            ).pack(anchor="w")

        ttk.Button(win, text="Close", command=win.destroy).pack(pady=10)

    # Windows
    def open_inventory(self):
        win = tk.Toplevel(self.root)
        win.title("Inventory")
        win.configure(bg=BG_DARK)
        win.geometry("860x600")

        main = tk.Frame(win, bg=BG_DARK)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        canvas = tk.Canvas(main, bg=BG_DARK, highlightthickness=0)
        vbar = ttk.Scrollbar(main, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG_DARK)

        inner_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=vbar.set)
        canvas.bind(
            "<Configure>", lambda e: canvas.itemconfig(inner_id, width=e.width - 20)
        )
        inner.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.pack(side="left", fill=tk.BOTH, expand=True)
        vbar.pack(side="right", fill="y")

        inv = self.data.get("inventory", {})
        if not inv:
            ttk.Label(inner, text="Inventory is empty.", foreground=TEXT_SUB).pack()
            return

        for girl, gdata in inv.items():
            card = tk.Frame(inner, bg=BG_CARD)
            card.pack(fill=tk.X, pady=6, padx=6)

            self._portrait(card, girl, 64).pack(side=tk.LEFT, padx=(6, 12), pady=6)

            stats = self.get_girl_stats(girl, gdata["level"], self.data)
            hp_now = int(self.get_current_hp(girl, gdata, self.data))
            info = self.girls_data[girl]

            txt = tk.Frame(card, bg=BG_CARD)
            txt.pack(side=tk.LEFT, fill=tk.X, expand=True)

            stars = gdata.get("stars", 0)
            tk.Label(
                txt,
                text=(f"{girl} Lv.{gdata['level']}" + (f"  ★x{stars}" if stars > 0 else "")),
                font=("Segoe UI", 12, "bold"),
                fg=TEXT_FG,
                bg=BG_CARD,
            ).pack(anchor="w")
            row_meta = tk.Frame(txt, bg=BG_CARD)
            row_meta.pack(anchor="w")
            self._element_badge(row_meta, info['element'], size=14, bg=BG_CARD).pack(side=tk.LEFT, padx=(0,6))
            tk.Label(
                row_meta,
                text=f"{info['rarity']} | {info['element']} | {info['class']}",
                fg=TEXT_SUB,
                bg=BG_CARD,
            ).pack(side=tk.LEFT)

            hp_ratio = hp_now / max(1, stats["hp"])
            hp_col = ERROR if hp_ratio <= 0.3 else WARN if hp_ratio <= 0.7 else SUCCESS
            tk.Label(
                txt,
                text=f"HP: {hp_now}/{stats['hp']}",
                fg=hp_col,
                bg=BG_CARD,
            ).pack(anchor="w")
            tk.Label(
                txt,
                text=f"ATK {stats['attack']} | DEF {stats['defense']} | SPD {stats['speed']}",
                fg=TEXT_SUB,
                bg=BG_CARD,
            ).pack(anchor="w")
            tk.Label(
                txt, text=info["catchline"], fg="#BBBBBB", bg=BG_CARD, font=("Segoe UI", 9, "italic")
            ).pack(anchor="w", pady=(2, 6))

            # Status line
            if not self.is_available(gdata):
                if gdata.get("scavenge_end"):
                    left = max(
                        0.0,
                        300 - (self.get_current_time() - (gdata["scavenge_end"] - 300)),
                    ) / 60.0
                    status = f"Scavenging ({left:.1f} min remaining)"
                else:
                    left = max(0.0, 600 - (self.get_current_time() - (gdata["recovery_start"] or 0))) / 60.0
                    status = f"Recovering ({left:.1f} min remaining)"
                tk.Label(txt, text=status, fg=TEXT_SUB, bg=BG_CARD).pack(anchor="w")

    def open_dupes(self):
        win = tk.Toplevel(self.root)
        win.title("Dupes")
        win.configure(bg=BG_DARK)
        win.geometry("520x520")

        wrapper = ttk.Frame(win, style="Card.TFrame", padding=12)
        wrapper.pack(fill=tk.BOTH, expand=True)

        dupe_items = list(self.data.get("dupes", {}).items())
        if not dupe_items:
            ttk.Label(wrapper, text="No dupes.", foreground=TEXT_SUB).pack()
            return

        lst = tk.Listbox(wrapper, bg=BG_CARD, fg=TEXT_FG, selectbackground=ACCENT, activestyle="none")
        for name, count in dupe_items:
            lst.insert(tk.END, f"{name} — {count}")
        lst.pack(fill=tk.BOTH, expand=True)

        row = ttk.Frame(wrapper, style="Card.TFrame")
        row.pack(fill=tk.X, pady=8)
        amt_var = tk.IntVar(value=1)
        ttk.Label(row, text="Amount (for Sell/Ascend):").pack(side=tk.LEFT)
        amt_entry = ttk.Entry(row, width=8, textvariable=amt_var)
        amt_entry.pack(side=tk.LEFT, padx=6)

        def sell_selected():
            idx = lst.curselection()
            if not idx:
                messagebox.showerror("Select", "Select a dupe to sell.")
                return
            name, current = dupe_items[idx[0]]
            amt = amt_var.get()
            if amt <= 0 or amt > current:
                messagebox.showerror("Invalid", f"Enter 1..{current}.")
                return
            # 100 coins per dupe (same as CLI)
            if not messagebox.askyesno(
                "Confirm Sell",
                f"Sell {amt} {name} dupe(s) for {amt * 100} coins?",
            ):
                return
            self.data["coins"] = self.data.get("coins", 0) + amt * 100
            new_count = current - amt
            if new_count <= 0:
                del self.data["dupes"][name]
            else:
                self.data["dupes"][name] = new_count
            self._refresh_header()
            messagebox.showinfo("Sold", f"Sold {amt} {name} dupe(s) for {amt * 100} coins.")
            win.destroy()

        def ascend_selected():
            idx = lst.curselection()
            if not idx:
                messagebox.showerror("Select", "Select a dupe to use for Ascend.")
                return
            name, current = dupe_items[idx[0]]
            if name not in self.data.get("inventory", {}):
                messagebox.showerror("Ascend", "You don't own this girl.")
                return
            stars = self.data["inventory"][name].get("stars", 0)
            if stars >= 5:
                messagebox.showinfo("Ascend", f"{name} is at max stars.")
                return
            # Support multiple ascensions based on Amount
            requested = amt_var.get()
            if requested <= 0:
                requested = 1
            performed = 0
            consumed = 0
            new_stars = stars
            while performed < requested and new_stars < 5:
                step_cost = new_stars + 1
                if current - consumed < step_cost:
                    break
                consumed += step_cost
                new_stars += 1
                performed += 1
            if performed == 0:
                need = stars + 1
                messagebox.showerror("Ascend", f"Need {need} dupes (have {current}).")
                return
            if not messagebox.askyesno(
                "Confirm Ascend",
                f"Ascend {name} by {performed}★ to {new_stars}★ using {consumed} dupes?",
            ):
                return
            self.data["inventory"][name]["stars"] = new_stars
            remaining = current - consumed
            if remaining <= 0:
                del self.data["dupes"][name]
            else:
                self.data["dupes"][name] = remaining
            self._refresh_header()
            self.save_game(self.data)
            messagebox.showinfo("Ascended", f"{name} ascended to {new_stars}★ (used {consumed} dupes). Stats increased.")
            win.destroy()

        buttons = ttk.Frame(wrapper, style="Card.TFrame")
        buttons.pack(fill=tk.X, pady=6)
        ttk.Button(buttons, text="Sell Selected", command=sell_selected).pack(side=tk.LEFT, padx=4)
        ttk.Button(buttons, text="Ascend Selected", command=ascend_selected).pack(side=tk.LEFT, padx=4)

    # ---------------- Shop ----------------
    def open_shop(self):
        win = tk.Toplevel(self.root)
        win.title("Coin Shop")
        win.configure(bg=BG_DARK)
        win.geometry("520x520")

        box = ttk.Frame(win, style="Card.TFrame", padding=12)
        box.pack(fill=tk.BOTH, expand=True)

        ttk.Label(box, text=f"Coins: {self.data.get('coins',0)}", foreground=TEXT_SUB).pack(anchor="w")
        ttk.Separator(box).pack(fill=tk.X, pady=8)

        def buy_heal():
            if self.data.get("coins", 0) < 200:
                messagebox.showerror("Coins", "Need 200 coins.")
                return
            recovering = [
                g for g, gd in self.data.get("inventory", {}).items()
                if gd.get("recovery_start") is not None and not self.is_available(gd)
            ]
            if not recovering:
                messagebox.showinfo("Heal", "No girls are recovering.")
                return
            pick = tk.Toplevel(win)
            pick.title("Heal Target")
            pick.configure(bg=BG_DARK)
            lst = tk.Listbox(pick, bg=BG_CARD, fg=TEXT_FG)
            for g in recovering:
                gd = self.data["inventory"][g]
                left = max(0, 600 - (self.get_current_time() - (gd.get("recovery_start") or 0))) / 60
                lst.insert(tk.END, f"{g} — {left:.1f} min left")
            lst.pack(fill=tk.BOTH, expand=True)

            def do_heal():
                if not lst.curselection():
                    return
                name = recovering[lst.curselection()[0]]
                self.data["inventory"][name]["recovery_start"] = None
                self.data["inventory"][name]["hp_at_start"] = None
                self.data["coins"] -= 200
                self._refresh_header()
                self.save_game(self.data)
                messagebox.showinfo("Healed", f"{name} fully healed.")
                pick.destroy()
                win.destroy()

            ttk.Button(pick, text="Heal", command=do_heal).pack(pady=6)

        def buy_attack():
            if self.data.get("coins", 0) < 1000:
                messagebox.showerror("Coins", "Need 1000 coins.")
                return
            girls = list(self.data.get("inventory", {}).keys())
            if not girls:
                messagebox.showinfo("Boost", "No girls owned.")
                return
            pick = tk.Toplevel(win)
            pick.title("Attack Booster")
            pick.configure(bg=BG_DARK)
            lst = tk.Listbox(pick, bg=BG_CARD, fg=TEXT_FG)
            for g in girls:
                lv = self.data["inventory"][g]["level"]
                lst.insert(tk.END, f"{g} Lv.{lv}")
            lst.pack(fill=tk.BOTH, expand=True)

            def do_boost():
                if not lst.curselection():
                    return
                name = girls[lst.curselection()[0]]
                self.data["inventory"][name]["attack_bonus"] = self.data["inventory"][name].get("attack_bonus", 0) + 5
                self.data["coins"] -= 1000
                self._refresh_header()
                self.save_game(self.data)
                messagebox.showinfo("Boosted", f"{name} +5 ATK")
                pick.destroy()
                win.destroy()

            ttk.Button(pick, text="Apply +5 ATK", command=do_boost).pack(pady=6)

        def buy_shards():
            if self.data.get("coins", 0) < 2000:
                messagebox.showerror("Coins", "Need 2000 coins.")
                return
            self.data["coins"] -= 2000
            self.data["shards"] = self.data.get("shards", 0) + 10
            self._refresh_header()
            self.save_game(self.data)
            messagebox.showinfo("Shop", "Bought 10 shards.")
            win.destroy()

        ttk.Button(box, text="Healing Potion (200)", command=buy_heal).pack(fill=tk.X, pady=6)
        ttk.Button(box, text="Attack Booster +5 (1000)", command=buy_attack).pack(fill=tk.X, pady=6)
        ttk.Button(box, text="Shard Bundle +10 (2000)", command=buy_shards).pack(fill=tk.X, pady=6)

    # ---------------- Training ----------------
    def open_training(self):
        girls = list(self.data.get("inventory", {}).keys())
        if not girls:
            messagebox.showinfo("Training", "No girls to train.")
            return
        win = tk.Toplevel(self.root)
        win.title("Training")
        win.configure(bg=BG_DARK)
        win.geometry("560x520")

        box = ttk.Frame(win, style="Card.TFrame", padding=12)
        box.pack(fill=tk.BOTH, expand=True)

        lst = tk.Listbox(box, bg=BG_CARD, fg=TEXT_FG)
        for g in girls:
            lv = self.data["inventory"][g]["level"]
            cost = 10 * (lv + 1) ** 2
            lst.insert(tk.END, f"{g} Lv.{lv} — Cost {cost} shards")
        lst.pack(fill=tk.BOTH, expand=True)

        def do_train():
            if not lst.curselection():
                return
            name = girls[lst.curselection()[0]]
            lv = self.data["inventory"][name]["level"]
            cost = 10 * (lv + 1) ** 2
            if self.data.get("shards", 0) < cost:
                messagebox.showerror("Shards", f"Need {cost} shards.")
                return
            self.data["shards"] -= cost
            self.data["inventory"][name]["level"] = lv + 1
            self._refresh_header()
            self.save_game(self.data)
            messagebox.showinfo("Training", f"{name} is now Lv.{lv+1}.")
            win.destroy()

        ttk.Button(box, text="Train Selected", command=do_train).pack(pady=8)

    # ---------------- Scavenging ----------------
    def open_scavenging(self):
        available = [g for g, gd in self.data.get("inventory", {}).items() if self.is_available(gd)]
        if not available:
            messagebox.showinfo("Scavenging", "No available girls.")
            return
        win = tk.Toplevel(self.root)
        win.title("Scavenging")
        win.configure(bg=BG_DARK)
        win.geometry("520x500")

        box = ttk.Frame(win, style="Card.TFrame", padding=12)
        box.pack(fill=tk.BOTH, expand=True)
        ttk.Label(box, text="30% success, 5 minutes.", foreground=TEXT_SUB).pack(anchor="w")

        lst = tk.Listbox(box, bg=BG_CARD, fg=TEXT_FG)
        for g in available:
            lv = self.data["inventory"][g]["level"]
            info = self.girls_data[g]
            lst.insert(tk.END, f"{g} Lv.{lv} — {info['element']} [{info['class']}]")
        lst.pack(fill=tk.BOTH, expand=True)

        def send():
            if not lst.curselection():
                return
            name = available[lst.curselection()[0]]
            now = self.get_current_time()
            self.data["inventory"][name]["scavenge_end"] = now + 300
            self.data["inventory"][name]["scavenge_result"] = None
            self.save_game(self.data)
            messagebox.showinfo("Scavenging", f"{name} sent for 5 minutes.")
            win.destroy()

        ttk.Button(box, text="Send Selected", command=send).pack(pady=8)

    # ---------------- Healing Session ----------------
    def open_healing(self):
        inv = self.data.get("inventory", {})
        recovering = [g for g, gd in inv.items() if gd.get("recovery_start") is not None and not self.is_available(gd)]
        if not recovering:
            messagebox.showinfo("Healing", "No girls are recovering.")
            return
        healers = [g for g, gd in inv.items() if self.is_available(gd) and self.girls_data[g]["class"] == self.CLASS_HEALER]
        if not healers:
            messagebox.showinfo("Healing", "No available healers.")
            return
        win = tk.Toplevel(self.root)
        win.title("Healing Session")
        win.configure(bg=BG_DARK)
        win.geometry("640x520")

        row = ttk.Frame(win, style="Card.TFrame", padding=12)
        row.pack(fill=tk.BOTH, expand=True)

        ttk.Label(row, text="Recovering:").grid(row=0, column=0, sticky="w")
        lst_target = tk.Listbox(row, bg=BG_CARD, fg=TEXT_FG, height=8)
        for g in recovering:
            gd = inv[g]
            left = max(0, 600 - (self.get_current_time() - (gd.get("recovery_start") or 0))) / 60
            lst_target.insert(tk.END, f"{g} — {left:.1f} min left")
        lst_target.grid(row=1, column=0, sticky="nsew", padx=(0, 8))

        ttk.Label(row, text="Healers:").grid(row=0, column=1, sticky="w")
        lst_healer = tk.Listbox(row, bg=BG_CARD, fg=TEXT_FG, height=8)
        for g in healers:
            lv = inv[g]["level"]
            lst_healer.insert(tk.END, f"{g} Lv.{lv}")
        lst_healer.grid(row=1, column=1, sticky="nsew")

        row.grid_columnconfigure(0, weight=1)
        row.grid_columnconfigure(1, weight=1)
        row.grid_rowconfigure(1, weight=1)

        def start_heal():
            if not lst_target.curselection() or not lst_healer.curselection():
                return
            tname = recovering[lst_target.curselection()[0]]
            hname = healers[lst_healer.curselection()[0]]
            if tname == hname:
                messagebox.showerror("Healing", "Healer cannot heal herself.")
                return
            now = self.get_current_time()
            inv[tname]["recovery_start"] = None
            inv[tname]["hp_at_start"] = None
            inv[tname]["recovery_start"] = now
            inv[hname]["recovery_start"] = now
            self.save_game(self.data)
            messagebox.showinfo("Healing", f"{hname} heals {tname}. Both busy 3 minutes.")
            win.destroy()

        ttk.Button(win, text="Start Session", command=start_heal).pack(pady=8)

    # ---------------- Battle (Auto) ----------------
    def open_battle(self):
        inv = self.data.get("inventory", {})
        available = [g for g, gd in inv.items() if self.is_available(gd)]
        if not available:
            messagebox.showinfo("Battle", "No available girls.")
            return
        if not self.monsters:
            messagebox.showinfo("Battle", "No monsters defined.")
            return
        win = tk.Toplevel(self.root)
        win.title("Battle (Auto)")
        win.configure(bg=BG_DARK)
        win.geometry("720x560")

        box = ttk.Frame(win, style="Card.TFrame", padding=12)
        box.pack(fill=tk.BOTH, expand=True)

        ttk.Label(box, text="Pick up to 3 girls").pack(anchor="w")
        lst = tk.Listbox(box, selectmode=tk.MULTIPLE, bg=BG_CARD, fg=TEXT_FG, height=8)
        for g in available:
            lv = inv[g]["level"]
            info = self.girls_data[g]
            lst.insert(tk.END, f"{g} Lv.{lv} — {info['element']} [{info['class']}]")
        lst.pack(fill=tk.X)

        sel_mon = tk.StringVar()
        names = [m["name"] for m in self.monsters]
        ttk.Label(box, text="Monster:").pack(anchor="w", pady=(10, 0))
        mon_combo = ttk.Combobox(box, values=names, textvariable=sel_mon, state="readonly")
        mon_combo.current(0)
        mon_combo.pack(fill=tk.X)

        # Mode selection
        mode_var = tk.StringVar(value="auto")
        mode_row = ttk.Frame(box, style="Card.TFrame")
        mode_row.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(mode_row, text="Mode:").pack(side=tk.LEFT)
        ttk.Radiobutton(mode_row, text="Autoplay", value="auto", variable=mode_var).pack(side=tk.LEFT, padx=6)
        ttk.Radiobutton(mode_row, text="Turn-Based", value="turn", variable=mode_var).pack(side=tk.LEFT, padx=6)

        log = tk.Text(box, bg=BG_CARD, fg=TEXT_FG, height=14)
        log.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        def writeln(s):
            log.insert(tk.END, s + "\n")
            log.see(tk.END)

        def start():
            idxs = lst.curselection()
            if not idxs or len(idxs) > 3:
                messagebox.showerror("Battle", "Select 1 to 3 girls.")
                return
            team_names = [available[i] for i in idxs]
            mon_name = sel_mon.get() or names[0]
            monster = next((m.copy() for m in self.monsters if m["name"] == mon_name), self.monsters[0].copy())
            if mode_var.get() == "auto":
                self._run_auto_battle(win, writeln, inv, team_names, monster)
            else:
                win.destroy()
                self._run_turn_battle(team_names, monster)

        ttk.Button(box, text="Start Battle", command=start).pack(pady=8)

    # ---- Auto battle core (kept) ----
    def _run_auto_battle(self, log_window, writeln, inv, team_names, monster):
        team = []
        for name in team_names:
            gd = inv[name]
            stats = self.get_girl_stats(name, gd["level"], self.data)
            team.append({
                "name": name,
                "stats": stats,
                "hp": float(self.get_current_hp(name, gd, self.data)),
                "max_hp": stats["hp"],
                "shield": False,
            })

        mon_hp = float(monster["hp"])
        turn = 0
        writeln(f"Battle begins vs {monster['name']} ({monster['element']})")
        while mon_hp > 0 and any(g["hp"] > 0 for g in team):
            turn += 1
            writeln(f"-- Turn {turn} --  Monster {int(mon_hp)}/{monster['hp']}")
            for g in team:
                if g["hp"] <= 0:
                    continue
                if self.girls_data[g["name"]]["class"] == self.CLASS_HEALER and turn % 6 == 0:
                    for t in team:
                        t["shield"] = True
                    writeln(f"{g['name']} casts group shield!")
                base = g["stats"]["attack"]
                multi = self.elemental_multiplier(
                    self.girls_data[g["name"]]["element"],
                    monster["element"],
                ) or 1.0
                dmg = max(1, int(base * multi) - monster["defense"])
                mon_hp -= dmg
                note = " (super effective)" if multi > 1 else " (not very effective)" if multi < 1 else ""
                writeln(f"{g['name']} hits for {dmg}{note}")
                if mon_hp <= 0:
                    break
            if mon_hp <= 0:
                break
            targets = [t for t in team if t["hp"] > 0]
            if not targets:
                break
            import random as _r
            target = _r.choice(targets)
            if target["shield"]:
                writeln(f"{monster['name']}'s attack is absorbed by shield on {target['name']}")
                target["shield"] = False
            else:
                # Apply elemental multiplier (monster element vs girl's element)
                m_elem = monster.get("element")
                g_elem = self.girls_data[target["name"]]["element"]
                multi = self.elemental_multiplier(m_elem, g_elem) or 1.0
                mdmg = max(1, int(monster["atk"] * multi) - target["stats"]["defense"])
                target["hp"] -= mdmg
                note = " (super effective)" if multi > 1 else " (not very effective)" if multi < 1 else ""
                writeln(f"{monster['name']} hits {target['name']} for {mdmg}{note} (HP {int(target['hp'])})")

        if mon_hp <= 0:
            reward = monster.get("shards", 0)
            self.data["shards"] = self.data.get("shards", 0) + reward
            writeln(f"Victory! +{reward} shards")
            if callable(self.normal_victory_hook):
                try:
                    self.normal_victory_hook(self.data)
                except Exception:
                    pass
        else:
            writeln("Defeat…")

        now = self.get_current_time()
        inv_local = self.data.get("inventory", {})
        for g in team:
            final_hp = max(1, int(g["hp"]))
            inv_local[g["name"]]["recovery_start"] = now
            inv_local[g["name"]]["hp_at_start"] = final_hp
        self.save_game(self.data)
        self._refresh_header()

    # ---- Turn-based battle ----
    def _run_turn_battle(self, team_names, monster):
        inv = self.data.get("inventory", {})
        team = []
        for name in team_names:
            gd = inv[name]
            stats = self.get_girl_stats(name, gd["level"], self.data)
            team.append({
                "name": name,
                "stats": stats,
                "hp": float(self.get_current_hp(name, gd, self.data)),
                "max_hp": stats["hp"],
                "special_cd": 0,
                "defending": False,
                "shield": False,
            })

        mon_hp = float(monster["hp"])
        mon_max = float(monster["hp"])
        turn_idx = 0
        turn_count = 0

        win = tk.Toplevel(self.root)
        win.title("Battle (Turn-Based)")
        win.configure(bg=BG_DARK)
        win.geometry("820x620")

        top = ttk.Frame(win, style="Card.TFrame", padding=10)
        top.pack(fill=tk.X)
        mon_icon = self._element_badge(top, monster.get("element", ""), size=14, bg=BG_DARK)
        mon_icon.pack(side=tk.LEFT, padx=(0,6))
        mon_label = ttk.Label(top, text="", font=("Segoe UI", 12, "bold"))
        mon_label.pack(side=tk.LEFT, anchor="w")

        team_frame = ttk.Frame(win, style="Card.TFrame", padding=8)
        team_frame.pack(fill=tk.X)

        action_frame = ttk.Frame(win, style="Card.TFrame", padding=8)
        action_frame.pack(fill=tk.X)
        act_label = ttk.Label(action_frame, text="")
        act_label.pack(anchor="w")
        btn_row = ttk.Frame(action_frame, style="Card.TFrame")
        btn_row.pack(anchor="w", pady=6)
        btn_basic = ttk.Button(btn_row, text="Basic Attack")
        btn_special = ttk.Button(btn_row, text="Special")
        btn_defend = ttk.Button(btn_row, text="Defend")
        btn_basic.pack(side=tk.LEFT, padx=4)
        btn_special.pack(side=tk.LEFT, padx=4)
        btn_defend.pack(side=tk.LEFT, padx=4)

        log = tk.Text(win, bg=BG_CARD, fg=TEXT_FG, height=16)
        log.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        def writeln(s):
            log.insert(tk.END, s + "\n")
            log.see(tk.END)

        def refresh():
            mon_label.configure(text=f"{monster['name']} HP {int(mon_hp)}/{int(mon_max)}  DEF {monster['defense']}  ATK {monster['atk']}")
            for child in team_frame.winfo_children():
                child.destroy()
            for g in team:
                color = SUCCESS if g["hp"] > 0 else ERROR
                row = ttk.Frame(team_frame, style="Card.TFrame")
                row.pack(anchor="w", fill=tk.X)
                self._element_badge(row, self.girls_data[g['name']]['element'], size=12, bg=BG_DARK).pack(side=tk.LEFT, padx=(0,6))
                ttk.Label(row, text=f"{g['name']} HP {int(g['hp'])}/{g['max_hp']}  CD {g['special_cd']}  {'SHIELD' if g['shield'] else ''}", foreground=color).pack(side=tk.LEFT)

        def next_turn_or_monster():
            nonlocal turn_idx, turn_count, mon_hp
            alive = [i for i, g in enumerate(team) if g["hp"] > 0]
            if not alive:
                end_battle(False)
                return
            # find next alive index
            start = turn_idx
            for _ in range(len(team)):
                turn_idx = (turn_idx) % len(team)
                if team[turn_idx]["hp"] > 0:
                    break
                turn_idx += 1
            # if we've looped all teammates (based on sentinel), run monster turn
            if start == turn_idx and turn_count > 0:
                monster_turn()
                return
            player_turn()

        def player_turn():
            nonlocal turn_idx
            g = team[turn_idx]
            g["defending"] = False
            act_label.configure(text=f"{g['name']}'s turn — choose action")
            btn_basic.configure(command=lambda: do_action("basic"))
            btn_special.configure(command=lambda: do_action("special"), state=(tk.NORMAL if g["special_cd"] == 0 else tk.DISABLED))
            btn_defend.configure(command=lambda: do_action("defend"))
            refresh()

        def do_action(kind):
            nonlocal mon_hp, turn_idx, turn_count
            g = team[turn_idx]
            if kind == "basic":
                base = g["stats"]["attack"]
                multi = self.elemental_multiplier(
                    self.girls_data[g["name"]]["element"],
                    monster["element"],
                ) or 1.0
                dmg = max(1, int(base * multi) - monster["defense"])
                mon_hp -= dmg
                note = " (super effective)" if multi > 1 else " (not very effective)" if multi < 1 else ""
                writeln(f"{g['name']} uses Basic Attack for {dmg}{note}")
            elif kind == "special":
                if self.girls_data[g["name"]]["class"] == self.CLASS_HEALER:
                    for t in team:
                        t["shield"] = True
                    g["special_cd"] = 6
                    writeln(f"{g['name']} casts Group Shield")
                else:
                    base = int(g["stats"]["attack"] * 2.0)
                    multi = self.elemental_multiplier(self.girls_data[g["name"]]["element"], monster["element"]) or 1.0
                    dmg = max(1, int(base * multi) - monster["defense"])
                    mon_hp -= dmg
                    g["special_cd"] = 6
                    note = " (super effective)" if multi > 1 else " (not very effective)" if multi < 1 else ""
                    writeln(f"{g['name']} uses Special for {dmg}{note}")
            elif kind == "defend":
                g["defending"] = True
                writeln(f"{g['name']} defends")

            g["special_cd"] = max(0, g["special_cd"] - 1)
            if mon_hp <= 0:
                end_battle(True)
                return
            # advance to next teammate; if wrapped, monster acts
            advance_and_maybe_monster()

        def advance_and_maybe_monster():
            nonlocal turn_idx, turn_count
            prev_idx = turn_idx
            cnt = 0
            while True:
                turn_idx = (turn_idx + 1) % len(team)
                cnt += 1
                if team[turn_idx]["hp"] > 0 or cnt >= len(team):
                    break
            if turn_idx <= prev_idx:
                turn_count += 1
                monster_turn()
            else:
                player_turn()

        def monster_turn():
            nonlocal mon_hp
            refresh()
            alive_targets = [t for t in team if t["hp"] > 0]
            if not alive_targets:
                end_battle(False)
                return
            import random as _r
            t = _r.choice(alive_targets)
            if t["defending"]:
                writeln(f"{monster['name']}'s attack is blocked by {t['name']}")
            elif t["shield"]:
                t["shield"] = False
                writeln(f"{monster['name']}'s attack is absorbed by shield on {t['name']}")
            else:
                # Apply elemental multiplier (monster element vs girl's element)
                m_elem = monster.get("element")
                g_elem = self.girls_data[t["name"]]["element"]
                multi = self.elemental_multiplier(m_elem, g_elem) or 1.0
                mdmg = max(1, int(monster["atk"] * multi) - t["stats"]["defense"])
                t["hp"] -= mdmg
                note = " (super effective)" if multi > 1 else " (not very effective)" if multi < 1 else ""
                writeln(f"{monster['name']} hits {t['name']} for {mdmg}{note}")
            # after monster acts, next player turn is first alive from start
            # move pointer to first alive
            for i in range(len(team)):
                if team[i]["hp"] > 0:
                    turn_idx = i
                    break
            if any(g["hp"] > 0 for g in team):
                player_turn()
            else:
                end_battle(False)

        def end_battle(victory):
            # finalize: rewards + recovery
            if victory:
                rew = monster.get("shards", 0)
                self.data["shards"] = self.data.get("shards", 0) + rew
                writeln(f"Victory! +{rew} shards")
                if callable(self.normal_victory_hook):
                    try:
                        self.normal_victory_hook(self.data)
                    except Exception:
                        pass
            else:
                writeln("Defeat…")
            now = self.get_current_time()
            inv_local = self.data.get("inventory", {})
            for g in team:
                final_hp = max(1, int(g["hp"]))
                inv_local[g["name"]]["recovery_start"] = now
                inv_local[g["name"]]["hp_at_start"] = final_hp
            self.save_game(self.data)
            self._refresh_header()
            btn_basic.configure(state=tk.DISABLED)
            btn_special.configure(state=tk.DISABLED)
            btn_defend.configure(state=tk.DISABLED)

        refresh()
        writeln(f"Battle begins vs {monster['name']} ({monster['element']})")
        player_turn()

    # ---------------- Boss (Dark Cave) ----------------
    def open_boss(self):
        # Check unlock state
        if not self.data.get("cave_unlocked"):
            need = max(0, 5 - int(self.data.get("boss_defeat_counter", 0)))
            messagebox.showinfo("Dark Cave Locked", f"Defeat {need} more monsters to unlock the cave.")
            return

        inv = self.data.get("inventory", {})
        available = [g for g, gd in inv.items() if self.is_available(gd)]
        if not available:
            messagebox.showinfo("Dark Cave", "No available girls.")
            return

        win = tk.Toplevel(self.root)
        win.title("Dark Cave — Boss Fight")
        win.configure(bg=BG_DARK)
        win.geometry("760x580")

        box = ttk.Frame(win, style="Card.TFrame", padding=12)
        box.pack(fill=tk.BOTH, expand=True)

        ttk.Label(box, text="Pick up to 3 girls (Ctrl/Shift for multi-select)").pack(anchor="w")
        lst = tk.Listbox(box, selectmode=tk.MULTIPLE, bg=BG_CARD, fg=TEXT_FG, height=8)
        for g in available:
            lv = inv[g]["level"]
            info = self.girls_data[g]
            lst.insert(tk.END, f"{g} Lv.{lv} — {info['element']} [{info['class']}]")
        lst.pack(fill=tk.X)

        # Boss selection
        boss_names = [t[0] for t in BOSS_POOL]
        sel_boss = tk.StringVar()
        ttk.Label(box, text="Boss:").pack(anchor="w", pady=(10, 0))
        boss_combo = ttk.Combobox(box, values=boss_names, textvariable=sel_boss, state="readonly")
        boss_combo.current(0)
        boss_combo.pack(fill=tk.X)

        # Mode selection
        mode_var = tk.StringVar(value="auto")
        mode_row = ttk.Frame(box, style="Card.TFrame")
        mode_row.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(mode_row, text="Mode:").pack(side=tk.LEFT)
        ttk.Radiobutton(mode_row, text="Autoplay", value="auto", variable=mode_var).pack(side=tk.LEFT, padx=6)
        ttk.Radiobutton(mode_row, text="Turn-Based", value="turn", variable=mode_var).pack(side=tk.LEFT, padx=6)

        log = tk.Text(box, bg=BG_CARD, fg=TEXT_FG, height=14)
        log.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        def writeln(s):
            log.insert(tk.END, s + "\n")
            log.see(tk.END)

        def to_boss_dict(tup):
            name, rarity, atk, def_, hp, spd, elem, spec = tup
            reward = 50 if rarity == "Rare" else 100 if rarity == "Epic" else 150
            return {
                "name": name,
                "rarity": rarity,
                "atk": atk,
                "defense": def_,
                "hp": hp,
                "max_hp": hp,
                "speed": spd,
                "element": elem,
                "special_name": spec,
                "shards": reward,
            }

        def start():
            idxs = lst.curselection()
            if not idxs or len(idxs) > 3:
                messagebox.showerror("Boss", "Select 1 to 3 girls.")
                return
            names = [available[i] for i in idxs]
            sel = sel_boss.get() or boss_names[0]
            boss_t = next((t for t in BOSS_POOL if t[0] == sel), BOSS_POOL[0])
            boss = to_boss_dict(boss_t)
            if mode_var.get() == "auto":
                self._run_auto_battle(win, writeln, inv, names, boss)
            else:
                win.destroy()
                self._run_turn_battle(names, boss)

        ttk.Button(box, text="Start Boss Fight", command=start).pack(pady=8)


def run_gui(data, api):
    root = tk.Tk()
    app = GachaApp(root, data, api)
    root.mainloop()
