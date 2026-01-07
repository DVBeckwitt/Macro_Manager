import os
import streamlit as st
from pathlib import Path

from macro_manager.models import Food, Meal
from macro_manager.db import load_foods, save_foods, load_profile, save_profile
from macro_manager.plot import build_dashboard_figure, save_dashboard
import pandas as pd
from streamlit.runtime import runtime

# ────────────────────────── YAML Helpers ──────────────────────
# Functions now live in macro_manager.db

_SHUTDOWN_HOOK_INSTALLED = False


def install_session_shutdown_hook() -> None:
    global _SHUTDOWN_HOOK_INSTALLED
    if _SHUTDOWN_HOOK_INSTALLED or not runtime.Runtime.exists():
        return
    rt = runtime.Runtime.instance()
    if getattr(rt, "_macro_manager_shutdown_hook", False):
        _SHUTDOWN_HOOK_INSTALLED = True
        return
    original = rt._on_session_disconnected

    def _wrapped_on_disconnect() -> None:
        original()
        if rt._session_mgr.num_active_sessions() == 0:
            os._exit(0)

    rt._on_session_disconnected = _wrapped_on_disconnect
    rt._macro_manager_shutdown_hook = True
    _SHUTDOWN_HOOK_INSTALLED = True


def rerun_app() -> None:
    rerun = getattr(st, "rerun", None)
    if rerun is None:
        rerun = st.experimental_rerun
    rerun()


def parse_logged_foods(foods_str: str) -> dict[str, float]:
    parsed: dict[str, float] = {}
    for item in foods_str.split("; "):
        if not item:
            continue
        name_part, qty_part = item.rsplit("x", 1)
        try:
            parsed[name_part] = float(qty_part)
        except ValueError:
            continue
    return parsed


def calculate_bmr(sex: str, weight_kg: float, height_cm: float, age: float) -> float:
    if not all([sex, weight_kg, height_cm, age]):
        return 0.0
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    if sex == "Male":
        base += 5
    elif sex == "Female":
        base -= 161
    return max(base, 0.0)


# ────────────────────────── Sidebar CRUD UI ───────────────────

def manage_foods_ui(foods: dict[str, Food]) -> dict[str, Food]:
    """Render UI to add/edit/delete foods. Return potentially mutated dict."""
    with st.sidebar.expander("🛠️ Manage Foods", expanded=False):
        action = st.radio("Select action", ["Add", "Edit", "Delete", "None"], index=3)

    def food_form(defaults: dict | None = None):
        defaults = defaults or {}
        name = st.text_input("Food name", value=defaults.get("name", ""), disabled=bool(defaults))
        cols = st.columns(3)
        fields = [
            ("protein", "Protein (g)"),
            ("fat", "Fat (g)"),
            ("carb", "Carb (g)"),
            ("fiber", "Fiber (g)"),
            ("add_sugar", "Added sugar (g)"),
            ("sodium", "Sodium (mg)"),
            ("potassium", "Potassium (mg)"),
        ]
        values = {}
        for idx, (field, label) in enumerate(fields):
            col = cols[idx % 3]
            values[field] = col.number_input(label, 0.0, value=float(defaults.get(field, 0)))
        values["name"] = name.strip()
        return values

    if action == "Add":
        with st.form("add_form"):
            vals = food_form()
            if st.form_submit_button("➕ Add Food"):
                if not vals["name"]:
                    st.warning("Food name required.")
                elif vals["name"] in foods:
                    st.error("Food already exists – try Edit instead.")
                else:
                    foods[vals["name"]] = Food(**vals)
                    save_foods(foods)
                    st.success(f"Added {vals['name']}")
                    rerun_app()

    elif action == "Edit":
        target = st.selectbox("Select food to edit", sorted(foods.keys()))
        with st.form("edit_form"):
            vals = food_form({**foods[target].__dict__})
            if st.form_submit_button("💾 Save Changes"):
                foods[target] = Food(**vals)
                save_foods(foods)
                st.success(f"Updated {target}")
                rerun_app()

    elif action == "Delete":
        victims = st.multiselect("Select foods to delete", sorted(foods.keys()))
        if st.button("🗑️ Delete Selected", disabled=not victims):
            for v in victims:
                foods.pop(v, None)
            save_foods(foods)
            st.success(f"Deleted {', '.join(victims)}")
            rerun_app()

    return foods

# ────────────────────────── Main App ─────────────────────────

def main():
    st.set_page_config(page_title="Macro Dashboard", page_icon="📊", layout="wide")
    install_session_shutdown_hook()

    foods = load_foods()
    foods = manage_foods_ui(foods)  # May mutate dict via sidebar

    tab_dash, tab_trend = st.tabs(["Dashboard", "Trends"])

    with tab_dash:
        st.header("Daily Macro Dashboard 📊")
        st.caption("⬅️ Use the sidebar to build your meal and manage foods.")

        st.sidebar.header("🥗 Build Your Meal")
        log_path = Path(__file__).resolve().parent / "macro_log.csv"
        if log_path.exists():
            df_log = pd.read_csv(log_path, parse_dates=["datetime"])
            if not df_log.empty:
                df_log["date"] = df_log["datetime"].dt.date
                load_date = st.sidebar.selectbox(
                    "Load previous day",
                    sorted(df_log["date"].unique(), reverse=True),
                )
                if st.sidebar.button("📥 Load day into meal builder"):
                    row = df_log.loc[df_log["date"] == load_date].iloc[-1]
                    logged_foods = parse_logged_foods(row.get("foods", ""))
                    available_foods = [name for name in logged_foods if name in foods]
                    missing_foods = sorted(set(logged_foods) - set(available_foods))
                    st.session_state["selected_foods"] = available_foods
                    for name, qty in logged_foods.items():
                        if name in foods:
                            st.session_state[f"serving_{name}"] = qty
                    if missing_foods:
                        st.sidebar.warning(
                            "Missing foods not found in your library: "
                            f"{', '.join(missing_foods)}"
                        )

        selected = st.sidebar.multiselect(
            "Select foods",
            sorted(foods.keys()),
            key="selected_foods",
        )
        servings = {
            name: st.sidebar.number_input(
                f"{name} servings",
                0.0,
                value=st.session_state.get(f"serving_{name}", 1.0),
                step=0.25,
                key=f"serving_{name}",
            )
            for name in selected
        }

        meal = Meal("Today's Intake")
        for name, qty in servings.items():
            if qty:
                meal.add(foods[name], qty)

        st.sidebar.header("🔥 Burned Calories")
        profile = load_profile()
        with st.sidebar.expander("Profile (auto-saved)", expanded=False):
            sex_options = ["", "Female", "Male"]
            sex_default = profile.get("sex", "")
            if sex_default not in sex_options:
                sex_default = ""
            sex = st.selectbox(
                "Sex",
                sex_options,
                index=sex_options.index(sex_default),
            )
            age = st.number_input("Age", 0.0, value=float(profile.get("age", 0)))
            height_cm = st.number_input("Height (cm)", 0.0, value=float(profile.get("height_cm", 0)))
            weight_kg = st.number_input("Weight (kg)", 0.0, value=float(profile.get("weight_kg", 0)))
        profile_payload = {
            "sex": sex,
            "age": age,
            "height_cm": height_cm,
            "weight_kg": weight_kg,
        }
        if profile_payload != profile:
            save_profile(profile_payload)

        bmr = calculate_bmr(sex, weight_kg, height_cm, age)
        base_burn_kcal = bmr * 1.2
        st.sidebar.metric("Estimated base burn (sedentary TDEE)", f"{base_burn_kcal:.0f} kcal")
        st.sidebar.caption(
            "Base burn uses sedentary TDEE (BMR x 1.2). Add workout adjustments below."
        )

        if "workouts" not in st.session_state:
            st.session_state["workouts"] = []
        workout_df = st.sidebar.data_editor(
            pd.DataFrame(
                st.session_state["workouts"],
                columns=["Workout", "Calories", "Error (kcal)"],
            ),
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Workout": st.column_config.TextColumn("Workout"),
                "Calories": st.column_config.NumberColumn(
                    "Calories (kcal)",
                    step=10,
                    help="Use negative values for underestimates or rest days.",
                ),
                "Error (kcal)": st.column_config.NumberColumn(
                    "Error (kcal)",
                    step=5,
                    help="Estimated error range for this workout entry.",
                ),
            },
            key="workout_editor",
        )
        st.session_state["workouts"] = workout_df.to_dict("records")
        workout_adjust_kcal = 0.0
        workout_error_kcal = 0.0
        if not workout_df.empty and "Calories" in workout_df:
            workout_adjust_kcal = float(workout_df["Calories"].fillna(0).sum())
        if not workout_df.empty and "Error (kcal)" in workout_df:
            workout_error_kcal = float(workout_df["Error (kcal)"].fillna(0).abs().sum())

        burned_kcal = max(base_burn_kcal + workout_adjust_kcal, 0.0)
        burned_error_kcal = workout_error_kcal or None

        if st.button("💾 Save Day to Log"):
            paths = save_dashboard(
                meal,
                burned_kcal=burned_kcal,
                base_burn_kcal=base_burn_kcal,
                workout_adjust_kcal=workout_adjust_kcal,
                workout_error_kcal=burned_error_kcal or 0.0,
                weight_kg=weight_kg,
            )
            msg = "Updated" if paths.get("replaced") else "Saved"
            st.success(f"{msg} to {paths['csv']}")

        fig, totals, total_kcal = build_dashboard_figure(
            meal,
            burned_kcal,
            burned_error_kcal=burned_error_kcal,
        )
        st.pyplot(fig, use_container_width=True)

        with st.expander("Nutrient Totals", expanded=True):
            stats = {
                "Calories (kcal)": f"{total_kcal:.0f}",
                "Burned (kcal)": f"{burned_kcal:.0f}",
                "Net (kcal)": f"{total_kcal - burned_kcal:.0f}",
            }
            stats.update({k: f"{v:.1f}" for k, v in totals.items()})
            st.table(stats)

    with tab_trend:
        log_path = Path(__file__).resolve().parent / "macro_log.csv"
        if log_path.exists():
            df = pd.read_csv(log_path, parse_dates=["datetime"])
            df = df.sort_values("datetime")
            for col in [
                "burned_calories",
                "net_calories",
                "base_burn_calories",
                "workout_adjust_calories",
            ]:
                if col not in df:
                    df[col] = 0.0
            st.subheader("Macro Trends")
            metrics = {
                "Total Calories": "calories",
                "Burned Calories": "burned_calories",
                "Net Calories": "net_calories",
                "Protein (g)": "protein_g",
                "Fat (g)": "fat_g",
                "Carbs (g)": "carb_g",
            }
            selected = st.multiselect(
                "Select metrics to plot",
                list(metrics.keys()),
                default=list(metrics.keys()),
            )
            df_idx = df.set_index("datetime")
            for label in selected:
                st.line_chart(df_idx[[metrics[label]]], height=200, use_container_width=True)
        else:
            st.info("No log file found. Save your meals to start tracking.")


if __name__ == "__main__":
    main()
