import matplotlib
matplotlib.use('Agg')

from macro_manager.models import Food, Meal
from macro_manager.plot import build_dashboard_figure, save_dashboard
from pytest import approx

def sample_meal():
    meal = Meal()
    meal.add(Food('apple', 0.3, 0.2, 10), 1)
    meal.add(Food('egg', 6, 5, 0.6), 2)
    return meal

def test_build_dashboard_figure():
    meal = sample_meal()
    fig, totals, kcal = build_dashboard_figure(meal)
    assert fig is not None
    assert totals['carb'] == approx(meal.totals['carb'])
    assert kcal == approx(meal.calories)

def test_save_dashboard(tmp_path):
    meal = sample_meal()
    paths = save_dashboard(meal, tmp_path)
    assert paths['png'].exists()
    assert paths['csv'].exists()
