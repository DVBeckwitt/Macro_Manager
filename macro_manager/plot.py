import datetime
import csv
from pathlib import Path
from typing import Dict, Union
import pandas as pd

import matplotlib.pyplot as plt

from .models import Meal

_pale = {
    "orange": "#FFE0B2",
    "green": "#C8E6C9",
    "red": "#FFCDD2",
    "protein": "#3E7FBA",
    "fat": "#E59728",
    "carb": "#9C27B0",
    "calorie": "#EC407A",
    "burned": "#26C6DA",
}


def _bar_colour(r: float) -> str:
    if r >= 1.5:
        return "#D50000"
    if r >= 1.25:
        return "#FF5252"
    if r >= 1.0:
        return "#FF8A65"
    if r >= 0.9:
        return "#FFB74D"
    return "#81C784"


def _plot_macros(ax, pct: Dict[str, float], totals: Dict[str, float]) -> None:
    for lbl, tgt, col, left in [
        ("Protein", 35, _pale["protein"], 0),
        ("Fat", 30, _pale["fat"], 35),
        ("Carbs", 35, _pale["carb"], 65),
    ]:
        ax.barh(0, tgt, left=left, height=0.45, color=col, alpha=0.18, edgecolor=col, lw=0.6)
        ax.text(left + tgt / 2, -0.25, f"Target {tgt}%", ha="center", va="center", fontsize=6, color="white")
    left = 0
    for key, lbl, col in [
        ("protein", "Protein", _pale["protein"]),
        ("fat", "Fat", _pale["fat"]),
        ("carb", "Carbs", _pale["carb"]),
    ]:
        pc = pct[key]
        val = totals[key]
        ax.barh(0, pc, left=left, height=0.30, color=col)
        extra = (
            f" ({totals['carb']-totals['fiber']:.0f} net)" if key == "carb" else ""
        )
        ax.text(
            left + pc / 2,
            0,
            f"{lbl} {val:.0f} g{extra}",
            ha="center",
            va="center",
            fontsize=8 if pc >= 15 else 6,
            color="white",
            weight="bold",
        )
        left += pc
    ax.axis('off')
    ax.set_xlim(0, 100)
    ax.set_ylim(-1.35, 1)


def _plot_calorie_bar(ax, kcal: float, y: float, color: str, label: str) -> None:
    cal_h, scale = 0.13, 2400
    ax.barh(y, 100, height=cal_h, color="#888", alpha=0.20, edgecolor="#AAA", lw=0.6)
    for s, e, c in [
        (1600, 1800, _pale["orange"]),
        (1800, 2200, _pale["green"]),
        (2200, 2400, _pale["red"]),
    ]:
        ax.barh(y, (e - s) / scale * 100, left=s / scale * 100, height=cal_h, color=c, alpha=0.15)
    ax.barh(y, min(kcal / scale, 1) * 100, height=cal_h, left=0, color=color, alpha=0.70)
    for v in [1600, 1800, 2000, 2200, 2400]:
        ax.vlines(
            v / scale * 100,
            y - cal_h / 2,
            y + cal_h / 2,
            colors="white",
            linestyles=(0, (4, 2)),
            lw=1,
        )
    ax.text(
        min(kcal / scale, 1) * 50,
        y,
        f"{kcal:.0f} kcal",
        ha="center",
        va="center",
        fontsize=9,
        weight="bold",
        color="white",
    )
    ax.text(
        0,
        y + cal_h / 2 + 0.03,
        label,
        ha="left",
        va="bottom",
        fontsize=7,
        weight="bold",
        color="white",
    )


def _plot_calories(ax, intake_kcal: float, burned_kcal: float) -> None:
    burned_y = 0.78
    intake_y = 0.55
    _plot_calorie_bar(ax, max(burned_kcal, 0), burned_y, _pale["burned"], "Burned")
    _plot_calorie_bar(ax, max(intake_kcal, 0), intake_y, _pale["calorie"], "Intake")


def _plot_micros(ax, totals: Dict[str, float]) -> None:
    row_y, bar_h, slot = -0.75, 0.24, 23
    for i, (lbl, tgt, val, unit, scale_n) in enumerate([
        ("Sodium", 2300, totals["sodium"], "mg", 4000),
        ("Fiber", 28, totals["fiber"], "g", 50),
        ("Sugar", 50, totals["add_sugar"], "g", 75),
        ("Potassium", 3400, totals["potassium"], "mg", 5000),
    ]):
        x = i * slot + (i + 1) * 2
        ax.barh(row_y, slot, left=x, height=bar_h, color="white", alpha=0.10, edgecolor="#AAA", lw=0.6)
        ratio = val / tgt
        ax.barh(row_y, min(ratio, 1) * slot, left=x, height=bar_h, color=_bar_colour(ratio), alpha=0.90)
        ax.vlines(x + tgt / scale_n * slot, row_y - bar_h / 2, row_y + bar_h / 2, colors="white", linestyles=(0, (4, 2)), lw=1)
        ax.text(x + slot / 2, row_y + bar_h / 2 + 0.06, lbl, ha='center', va='bottom', fontsize=7, color='white', weight='bold')
        ax.text(x + slot / 2, row_y - bar_h / 2 - 0.03, f"{val:.0f}/{tgt}{unit}", ha='center', va='top', fontsize=7, color='white')


def build_dashboard_figure(meal: Meal, burned_kcal: float):
    totals = meal.totals
    kcal = meal.calories or 1e-6
    pct = {k: (totals[k]*4 if k != 'fat' else totals[k]*9) / kcal * 100 for k in ('protein', 'fat', 'carb')}

    fig, ax = plt.subplots(figsize=(7, 3))
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)
    _plot_macros(ax, pct, totals)
    _plot_calories(ax, kcal, burned_kcal)
    _plot_micros(ax, totals)
    plt.tight_layout(pad=0.25)
    return fig, totals, kcal


def save_dashboard(
    meal: Meal,
    burned_kcal: float,
    base_burn_kcal: float,
    workout_adjust_kcal: float,
    weight_kg: float | None = None,
    directory: Union[str, Path] = None,
):
    if directory is None:
        directory = Path(__file__).resolve().parent
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    fig, totals, kcal = build_dashboard_figure(meal, burned_kcal)
    png_path = directory / "macro_dashboard.png"
    fig.savefig(png_path, dpi=200, transparent=True)

    csv_path = directory / "macro_log.csv"
    foods_str = "; ".join(f"{f.name}x{q}" for f, q in meal.items)
    row = {
        "datetime": datetime.datetime.now().isoformat(timespec="seconds"),
        "calories": kcal,
        "burned_calories": burned_kcal,
        "base_burn_calories": base_burn_kcal,
        "workout_adjust_calories": workout_adjust_kcal,
        "net_calories": kcal - burned_kcal,
        "weight_kg": weight_kg,
        "protein_g": totals["protein"],
        "fat_g": totals["fat"],
        "carb_g": totals["carb"],
        "fiber_g": totals["fiber"],
        "added_sugar_g": totals["add_sugar"],
        "sodium_mg": totals["sodium"],
        "potassium_mg": totals["potassium"],
        "foods": foods_str,
    }

    df_new = pd.DataFrame([row])
    replaced = False
    if csv_path.exists() and csv_path.stat().st_size > 0:
        df = pd.read_csv(csv_path)
        df["date"] = pd.to_datetime(df["datetime"]).dt.date
        today = pd.to_datetime(row["datetime"]).date()
        replaced = today in df["date"].values
        df = df[df["date"] != today].drop(columns=["date"])
        df = pd.concat([df, df_new], ignore_index=True)
    else:
        df = df_new
    df.to_csv(csv_path, index=False)
    return {"png": png_path, "csv": csv_path, "replaced": replaced}
