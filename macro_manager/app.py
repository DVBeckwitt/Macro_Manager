import streamlit as st


from macro_manager.models import Food, Meal
from macro_manager.db import load_foods, save_foods
from macro_manager.plot import build_dashboard_figure, save_dashboard

# ────────────────────────── YAML Helpers ──────────────────────
# Functions now live in macro_manager.db

# ────────────────────────── Sidebar CRUD UI ───────────────────


def manage_foods_ui(foods: dict[str, Food]) -> dict[str, Food]:
    """Render UI to add/edit/delete foods. Return potentially mutated dict."""
    st.sidebar.header("🛠️ Manage Foods")
    action = st.sidebar.radio(
        "Select action", ["Add", "Edit", "Delete", "None"], index=3
    )

    def food_form(defaults: dict | None = None):
        defaults = defaults or {}
        name = st.text_input(
            "Food name", value=defaults.get("name", ""), disabled=bool(defaults)
        )
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
            values[field] = col.number_input(
                label, 0.0, value=float(defaults.get(field, 0))
            )
        values["name"] = name.strip()
        return values

    if action == "Add":
        with st.sidebar.form("add_form"):
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
                    st.rerun()

    elif action == "Edit":
        target = st.sidebar.selectbox("Select food to edit", sorted(foods.keys()))
        with st.sidebar.form("edit_form"):
            vals = food_form({**foods[target].__dict__})
            if st.form_submit_button("💾 Save Changes"):
                foods[target] = Food(**vals)
                save_foods(foods)
                st.success(f"Updated {target}")
                st.rerun()

    elif action == "Delete":
        victims = st.sidebar.multiselect("Select foods to delete", sorted(foods.keys()))
        if st.sidebar.button("🗑️ Delete Selected", disabled=not victims):
            for v in victims:
                foods.pop(v, None)
            save_foods(foods)
            st.success(f"Deleted {', '.join(victims)}")
            st.rerun()

    return foods


# ────────────────────────── Main App ─────────────────────────


def main():
    st.set_page_config(page_title="Macro Dashboard", page_icon="📊", layout="wide")

    foods = load_foods()
    foods = manage_foods_ui(foods)  # May mutate dict via sidebar

    st.title("Daily Macro Dashboard 📊")
    st.caption("⬅️ Use the sidebar to build your meal and manage foods.")

    # --- Meal builder ---
    st.sidebar.header("🥗 Build Your Meal")
    selected = st.sidebar.multiselect("Select foods", sorted(foods.keys()))
    servings = {
        name: st.sidebar.number_input(f"{name} servings", 0.0, value=1.0, step=0.25)
        for name in selected
    }

    meal = Meal("Today's Intake")
    for name, qty in servings.items():
        if qty:
            meal.add(foods[name], qty)

    fig, totals, total_kcal = build_dashboard_figure(meal)
    paths = save_dashboard(meal)

    st.image(str(paths["png"]), use_container_width=True)

    with st.expander("Nutrient Totals", expanded=True):
        stats = {"Calories (kcal)": f"{total_kcal:.0f}"}
        stats.update({k: f"{v:.1f}" for k, v in totals.items()})
        st.table(stats)


if __name__ == "__main__":
    main()
