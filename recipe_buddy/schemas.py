from enum import StrEnum

from pydantic import BaseModel


class IngredientType(StrEnum):
    PROTEIN = "Protein"
    DAIRY = "Dairy"
    FRUIT = "Fruit"
    VEGETABLE = "Vegetable"
    GRAIN = "Grain"
    LEGUME_PULSE = "Legume/Pulse"
    BAKING_INGREDIENT = "Baking Ingredient"
    CONDIMENT_SAUCE = "Condiment/Sauce"
    NUT_SEED = "Nuts/Seeds"
    HERB_SPICE = "Herb/Spice"
    OIL_FAT = "Oil/Fat"
    OTHER = "Other"

    def __str__(self) -> str:
        return self.value


class UnitOfMeasurement(StrEnum):
    GRAMS = "grams"


class Ingredient(BaseModel):
    name: str
    type: IngredientType
    units_of_measurement: UnitOfMeasurement
    calories_per_100g: float
    protein_per_100g: float
    fat_per_100g: float
    carbs_per_100g: float
    shelf_life_room: int | None = None
    shelf_life_fridge: int | None = None
    shelf_life_freezer: int | None = None
