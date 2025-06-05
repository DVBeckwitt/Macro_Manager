"""
nutrition.py (completed)
========================
Core utilities for the Streamlit macro dashboard.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple, Union
import matplotlib.pyplot as plt
import datetime, csv, pathlib

# ─────────────────────────── Data models ────────────────────────────
@dataclass(frozen=True)
class Food:
    name: str
    protein: float
    fat: float
    carb: float
    fiber: float = 0
    add_sugar: float = 0
    sodium: float = 0
    potassium: float = 0

class Meal:
    def __init__(self, name: str = "Meal") -> None:
        self.name = name
        self.items: List[Tuple[Food, float]] = []

    def add(self, food: Food, servings: float = 1) -> None:
        self.items.append((food, servings))

    @property
    def totals(self) -> Dict[str, float]:
        t = {k: 0.0 for k in ("protein", "fat", "carb", "fiber", "add_sugar", "sodium", "potassium")}
        for food, n in self.items:
            for k in t:
                t[k] += getattr(food, k) * n
        return t

    @property
    def calories(self) -> float:
        t = self.totals
        return t["protein"] * 4 + t["fat"] * 9 + t["carb"] * 4

# ─────────────────────────── Food database ──────────────────────────
FOOD_DB: Dict[str, Food] = {}

def _add(name: str, *args, **kwargs):
    FOOD_DB[name] = Food(name, *args, **kwargs)

_add("egg", 6, 5, 0.6, sodium=70, potassium=70)
_add("pep_mix¼", 1.75, 0, 7.0, fiber=1.75, sodium=8.75, potassium=154.5)
_add("guac", 1, 10, 5, fiber=3, sodium=270, potassium=280)
_add("whey", 30, 4, 8, add_sugar=1, sodium=150)
_add("banana", 1, 0, 27, fiber=3, add_sugar=14, sodium=1, potassium=422)
_add("rice½", 2, 0, 23, potassium=17)
_add("beans", 28, 0, 77, fiber=31.5, sodium=360, potassium=243)
_add("tuna", 25, 0, 0, sodium=360, potassium=243)


def combo(name: str, parts: List[Tuple[str, float]]):
    d = {k: 0.0 for k in ("protein", "fat", "carb", "fiber", "add_sugar", "sodium", "potassium")}
    for key, n in parts:
        f = FOOD_DB[key]
        for k in d:
            d[k] += getattr(f, k) * n
    FOOD_DB[name] = Food(name, **d)
    return FOOD_DB[name]

combo("omelet", [("egg", 4), ("pep_mix¼", 1), ("guac", 1)])
FOOD_DB["tequila_sunrise"] = Food("tequila sunrise", 1.3, 0.37, 71.8, fiber=0.4, add_sugar=19.8, sodium=14, potassium=384)
FOOD_DB["turkey_wrap"] = Food("turkey wrap", 32, 34, 67, fiber=3, add_sugar=5, sodium=2500, potassium=930)
FOOD_DB["peanut"] = Food("peanut (1)", 0.16, 0.30, 0.10, fiber=0.05, sodium=0, potassium=4)
_add("chicken_breast", 53, 6, 0, sodium=150, potassium=440)
_add("hashbrowns", 4, 22, 29, fiber=3, sodium=600, potassium=550)
_add("white_toast", 2.6, 1, 12, fiber=0.7, sodium=127, potassium=45)
_add("iced_matcha", 3, 1, 24, fiber=1, add_sugar=19, sodium=35, potassium=60)
combo("Ernies #9", [("chicken_breast", 1), ("hashbrowns", 1), ("white_toast", 2), ("egg", 2)])

# ─────────────────────────── Plot helpers ──────────────────────────
_pale = {"orange": "#FFE0B2", "green": "#C8E6C9", "red": "#FFCDD2",
         "protein": "#3E7FBA", "fat": "#E59728", "carb": "#9C27B0", "calorie": "#EC407A"}

def _bar_colour(r: float):
    if r >= 1.5: return "#D50000"
    if r >= 1.25: return "#FF5252"
    if r >= 1.0: return "#FF8A65"
    if r >= 0.9: return "#FFB74D"
    return "#81C784"

def build_dashboard_figure(meal: Meal):
    tot = meal.totals
    kcal = meal.calories or 1e-6
    pct = {k: (tot[k]*4 if k != "fat" else tot[k]*9) / kcal * 100 for k in ("protein", "fat", "carb")}

    fig, ax = plt.subplots(figsize=(7,3)); ax.patch.set_alpha(0)
    for lbl, tgt, col, left in [("Protein", 35, _pale["protein"], 0),
                                ("Fat", 30, _pale["fat"], 35),
                                ("Carbs", 35, _pale["carb"], 65)]:
        ax.barh(0, tgt, left=left, height=0.45, color=col, alpha=0.18, edgecolor=col, lw=0.6)
        ax.text(left + tgt/2, -0.25, f"Target {tgt}%", ha="center", va="center", fontsize=6, color="white")
    left = 0
    for key, lbl, col in [("protein", "Protein", _pale["protein"]),
                            ("fat", "Fat", _pale["fat"]),
                            ("carb", "Carbs", _pale["carb"])]:
        pc = pct[key]; val = tot[key]
        ax.barh(0, pc, left=left, height=0.30, color=col)
        extra = f"\n({tot['carb']-tot['fiber']:.0f} net)" if key == "carb" else ""
        ax.text(left + pc/2, 0, f"{lbl} {val:.0f} g{extra}", ha="center", va="center",
                fontsize=8 if pc >= 15 else 6, color="white", weight="bold")
        left += pc
    ax.axis('off'); ax.set_xlim(0,100); ax.set_ylim(-1.35,1)

    cal_y, cal_h, scale = 0.55, 0.15, 2400
    ax.barh(cal_y, 100, height=cal_h, color="#888", alpha=0.20, edgecolor="#AAA", lw=0.6)
    for s, e, c in [(1600,1800,_pale["orange"]),(1800,2200,_pale["green"]),(2200,2400,_pale["red"])]:
        ax.barh(cal_y, (e-s)/scale*100, left=s/scale*100, height=cal_h, color=c, alpha=0.15)
    ax.barh(cal_y, min(kcal/scale,1)*100, height=cal_h, left=0, color=_pale["calorie"], alpha=0.70)
    for v in [1600,1800,2000,2200,2400]:
        ax.vlines(v/scale*100, cal_y-cal_h/2, cal_y+cal_h/2,
                  colors="#FFC107" if v==2000 else "white",
                  linestyles="-" if v==2000 else (0,(4,2)), lw=1)
        if v==2000:
            ax.text(v/scale*100, cal_y+cal_h/2+0.05, "Target 2000", ha="center", va="bottom",
                    fontsize=7, weight="bold", color="#FFC107")
    ax.text(min(kcal/scale,1)*50, cal_y, f"{kcal:.0f} kcal", ha="center", va="center",
            fontsize=9, weight="bold", color="white" if kcal>=1600 else "white")

    row_y, bar_h, slot = -0.75, 0.24, 23
    for i, (lbl, tgt, val, unit, scale_n) in enumerate([
            ("Sodium", 2300, tot["sodium"], "mg", 4000),
            ("Fiber", 28, tot["fiber"], "g", 50),
            ("Sugar", 50, tot["add_sugar"], "g", 75),
            ("Potassium", 3400, tot["potassium"], "mg", 5000)
    ]):
        x = i*slot + (i+1)*2
        ax.barh(row_y, slot, left=x, height=bar_h, color="white", alpha=0.10, edgecolor="#AAA", lw=0.6)
        ratio = val/tgt
        ax.barh(row_y, min(ratio,1)*slot, left=x, height=bar_h, color=_bar_colour(ratio), alpha=0.90)
        ax.vlines(x + tgt/scale_n*slot, row_y-bar_h/2, row_y+bar_h/2,
                  colors="white", linestyles=(0,(4,2)), lw=1)
        ax.text(x+slot/2, row_y+bar_h/2+0.06, lbl, ha="center", va="bottom", fontsize=7, color="white", weight="bold")
        ax.text(x+slot/2, row_y-bar_h/2-0.03, f"{val:.0f}/{tgt}{unit}", ha="center", va="top", fontsize=7, color="white")

    plt.tight_layout(pad=0.25)
    return fig, tot, kcal


def save_dashboard(meal: Meal, directory: Union[str, pathlib.Path] = None):
    if directory is None:
        directory = pathlib.Path(__file__).resolve().parent
    directory = pathlib.Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    fig, tot, kcal = build_dashboard_figure(meal)

    png_path = directory / "macro_dashboard.png"
    fig.savefig(png_path, dpi=200, transparent=True)

    csv_path = directory / "macro_log.csv"
    row = [
        datetime.datetime.now().isoformat(timespec="seconds"),
        kcal,
        tot["protein"], tot["fat"], tot["carb"], tot["fiber"], tot["add_sugar"], tot["sodium"], tot["potassium"]
    ]
    header = [
        "datetime", "calories", "protein_g", "fat_g", "carb_g",
        "fiber_g", "added_sugar_g", "sodium_mg", "potassium_mg"
    ]
    write_header = not csv_path.exists() or csv_path.stat().st_size == 0
    with csv_path.open("a", newline="") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(header)
        w.writerow(row)

    return {"png": png_path, "csv": csv_path}
