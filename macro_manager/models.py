from dataclasses import dataclass
from typing import Dict, List, Tuple

@dataclass
class Food:
    name: str
    protein: float
    fat: float
    carb: float
    fiber: float = 0
    add_sugar: float = 0
    sodium: float = 0
    potassium: float = 0

    @classmethod
    def from_dict(cls, name: str, data: Dict) -> "Food":
        return cls(
            name=name,
            protein=float(data.get("protein", 0)),
            fat=float(data.get("fat", 0)),
            carb=float(data.get("carb", 0)),
            fiber=float(data.get("fiber", 0)),
            add_sugar=float(data.get("add_sugar", 0)),
            sodium=float(data.get("sodium", 0)),
            potassium=float(data.get("potassium", 0)),
        )

class Meal:
    def __init__(self, name: str = "Meal") -> None:
        self.name = name
        self.items: List[Tuple[Food, float]] = []

    def add(self, food: Food, servings: float = 1.0) -> None:
        self.items.append((food, servings))

    @property
    def totals(self) -> Dict[str, float]:
        totals = {
            "protein": 0.0,
            "fat": 0.0,
            "carb": 0.0,
            "fiber": 0.0,
            "add_sugar": 0.0,
            "sodium": 0.0,
            "potassium": 0.0,
        }
        for food, n in self.items:
            for k in totals:
                totals[k] += getattr(food, k) * n
        return totals

    @property
    def calories(self) -> float:
        t = self.totals
        return t["protein"] * 4 + t["fat"] * 9 + t["carb"] * 4
