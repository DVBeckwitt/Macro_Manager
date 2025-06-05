import streamlit as st
import yaml
from nutrition import Food, Meal, build_dashboard_figure, save_dashboard
from pathlib import Path

# ────────────────────────── Constants ─────────────────────────
YAML_FILE = Path("foods.yaml")

# ────────────────────────── YAML Helpers ──────────────────────

def load_foods(path: Path = YAML_FILE) -> dict[str, Food]:
    """Return a dict of Food objects keyed by name."""
    if not path.exists():
        path.write_text("{}")  # start empty
    data = yaml.safe_load(path.read_text()) or {}
    foods: dict[str, Food] = {}
    for name, attrs in data.items():
        foods[name] = Food(
            name=name,
            protein=float(attrs.get("protein", 0)),
            fat=float(attrs.get("fat", 0)),
            carb=float(attrs.get("carb", 0)),
            fiber=float(attrs.get("fiber", 0)),
            add_sugar=float(attrs.get("add_sugar", 0)),
            sodium=float(attrs.get("sodium", 0)),
            potassium=float(attrs.get("potassium", 0)),
        )
    return foods


def foods_to_yaml_dict(foods: dict[str, Food]) -> dict:
    """Convert Food objects to plain dict ready for YAML dump, omitting zeros."""
    out = {}
    for f in foods.values():
        attrs = {
            k: getattr(f, k)
            for k in ("protein", "fat", "carb", "fiber", "add_sugar", "sodium", "potassium")
        }
        # drop zero entries for cleaner YAML
        out[f.name] = {k: v for k, v in attrs.items() if v}
    return out


def save_foods(foods: dict[str, Food], path: Path = YAML_FILE) -> None:
    """Persist current foods dict to YAML file."""
    with path.open("w") as f:
        yaml.safe_dump(foods_to_yaml_dict(foods), f, sort_keys=True)

# ────────────────────────── Sidebar CRUD UI ───────────────────

def manage_foods_ui(foods: dict[str, Food]) -> dict[str, Food]:
    """Render UI to add/edit/delete foods. Return potentially mutated dict."""
    st.sidebar.header("🛠️ Manage Foods")
    action = st.sidebar.radio("Select action", ["Add", "Edit", "Delete", "None"], index=3)

    def food_form(defaults: dict | None = None):
        defaults = defaults or {}
        name = st.text_input("Food name", value=defaults.get("name", ""), disabled=bool(defaults))
        cols = st.columns(3)
        protein = cols[0].number_input("Protein (g)", 0.0, value=float(defaults.get("protein", 0)))
        fat = cols[1].number_input("Fat (g)", 0.0, value=float(defaults.get("fat", 0)))
        carb = cols[2].number_input("Carb (g)", 0.0, value=float(defaults.get("carb", 0)))
        fiber = cols[0].number_input("Fiber (g)", 0.0, value=float(defaults.get("fiber", 0)))
        add_sugar = cols[1].number_input("Added sugar (g)", 0.0, value=float(defaults.get("add_sugar", 0)))
        sodium = cols[2].number_input("Sodium (mg)", 0.0, value=float(defaults.get("sodium", 0)))
        potassium = cols[0].number_input("Potassium (mg)", 0.0, value=float(defaults.get("potassium", 0)))
        return {
            "name": name.strip(),
            "protein": protein,
            "fat": fat,
            "carb": carb,
            "fiber": fiber,
            "add_sugar": add_sugar,
            "sodium": sodium,
            "potassium": potassium,
        }

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
                    st.experimental_rerun()

    elif action == "Edit":
        target = st.sidebar.selectbox("Select food to edit", sorted(foods.keys()))
        with st.sidebar.form("edit_form"):
            vals = food_form({**foods[target].__dict__})
            if st.form_submit_button("💾 Save Changes"):
                foods[target] = Food(**vals)
                save_foods(foods)
                st.success(f"Updated {target}")
                st.experimental_rerun()

    elif action == "Delete":
        victims = st.sidebar.multiselect("Select foods to delete", sorted(foods.keys()))
        if st.sidebar.button("🗑️ Delete Selected", disabled=not victims):
            for v in victims:
                foods.pop(v, None)
            save_foods(foods)
            st.success(f"Deleted {', '.join(victims)}")
            st.experimental_rerun()

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
