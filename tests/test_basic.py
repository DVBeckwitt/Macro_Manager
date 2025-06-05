import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from macro_manager.models import Food, Meal
from macro_manager.db import load_foods
from pytest import approx


def test_food_loading(tmp_path):
    sample = tmp_path / "foods.yaml"
    sample.write_text("""banana:\n  protein: 1\n  carb: 27\n""")
    foods = load_foods(sample)
    assert "banana" in foods
    assert isinstance(foods["banana"], Food)
    assert foods["banana"].carb == 27


def test_meal_totals():
    f1 = Food("egg", 6, 5, 0.6)
    meal = Meal()
    meal.add(f1, 2)
    totals = meal.totals
    assert totals["protein"] == 12
    assert totals["fat"] == 10
    assert totals["carb"] == 1.2
    assert meal.calories == approx(12*4 + 10*9 + 1.2*4, rel=1e-3)
