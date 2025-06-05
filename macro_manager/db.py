from pathlib import Path
import yaml
from .models import Food

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
FOODS_YAML = DATA_DIR / "foods.yaml"


def load_foods(path: Path = FOODS_YAML) -> dict[str, Food]:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}")
    data = yaml.safe_load(path.read_text()) or {}
    return {name: Food.from_dict(name, attrs) for name, attrs in data.items()}


def foods_to_yaml(foods: dict[str, Food]) -> dict:
    out = {}
    for food in foods.values():
        attrs = {
            k: getattr(food, k)
            for k in (
                "protein",
                "fat",
                "carb",
                "fiber",
                "add_sugar",
                "sodium",
                "potassium",
            )
        }
        out[food.name] = {k: v for k, v in attrs.items() if v}
    return out


def save_foods(foods: dict[str, Food], path: Path = FOODS_YAML) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        yaml.safe_dump(foods_to_yaml(foods), f, sort_keys=True)
