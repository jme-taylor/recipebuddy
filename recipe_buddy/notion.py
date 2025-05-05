import os
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError
import requests

from recipe_buddy.logging_config import logger
from recipe_buddy.schemas import Ingredient

load_dotenv()

NOTION_HEADERS = {
    "Authorization": f"Bearer {os.getenv('NOTION_TOKEN')}",
    "Notion-Version": "2022-06-28",
}


class User(BaseModel):
    object: str
    id: str


class Parent(BaseModel):
    type: str
    database_id: str


class Page(BaseModel):
    object: str
    id: str
    created_time: str
    last_edited_time: str
    created_by: User
    last_edited_by: User
    cover: Any | None = None
    icon: Any | None = None
    parent: Parent
    archived: bool
    in_trash: bool
    properties: dict[str, dict[str, Any]]
    url: str
    public_url: str | None = None


class NotionAPIDatabaseResponse(BaseModel):
    object: str
    results: list[Page]
    next_cursor: str | None = None
    has_more: bool
    type: str
    page_or_database: dict[str, Any]
    request_id: str


class NotionDatabase:
    """A class for interacting with Notion databases.

    Parameters
    ----------
    database_id: str
        The ID of the Notion database to interact with.

    Attributes
    ----------
    database_id: str
        The ID of the Notion database to interact with.
    base_url: str
        The base URL for the Notion API.

    Methods
    -------
    get_ingredients_data: list[Ingredient]
        Get the ingredients data from the Notion database.
    """

    def __init__(self, database_id: str):
        self.database_id = database_id
        self.base_url = f"https://api.notion.com/v1/databases/{database_id}"

    def _get_database_page(
        self, page_size: int | None = None, start_cursor: str | None = None
    ) -> NotionAPIDatabaseResponse:
        url = f"{self.base_url}/query"
        if page_size is None:
            page_size = 100
        if start_cursor is None:
            payload = {
                "page_size": page_size,
            }
        else:
            payload = {
                "page_size": page_size,
                "start_cursor": start_cursor,
            }
        response = requests.post(url, headers=NOTION_HEADERS, json=payload)
        return NotionAPIDatabaseResponse(**response.json())

    def get_ingredients_data(self) -> list[Ingredient]:
        """Parse a notion ingredient database to ingredient objects.

        This method gets all pages from the databas recursively, and
        parses them into ingredient objects. Any ingredients that are
        missing required attributes are skipped.

        Returns
        -------
        list[Ingredient]
            A list of ingredient objects.
        """
        pages = []
        has_more = True
        start_cursor = None
        while has_more:
            page_data = self._get_database_page(start_cursor=start_cursor)
            pages.extend(page_data.results)
            has_more = page_data.has_more
            start_cursor = page_data.next_cursor
        return parse_ingredient_data(pages)


def parse_ingredient_data(database_data: list[Page]) -> list[Ingredient]:
    """Parse a list of Notion pages into ingredient objects.

    This method parses a list of Notion pages into ingredient objects.
    Any ingredients that are missing required attributes are skipped.

    Parameters
    ----------
    database_data: list[Page]
        A list of Notion pages to parse.

    Returns
    -------
    list[Ingredient]
        A list of ingredient objects.
    """
    ingredients = []
    for page in database_data:
        page_name = (
            page.properties.get("Name", {})
            .get("title", [{}])[0]
            .get("text", {})
            .get("content")
        )
        try:
            ingredient = parse_ingredient_page(page)
            ingredients.append(ingredient)
        except (AttributeError, ValidationError) as e:
            logger.info(f"Skipping ingredient {page_name} due to missing attributes")
            logger.info(e)
            continue
    return ingredients


def parse_ingredient_page(page: Page) -> Ingredient:
    """
    Parse a Notion page into an ingredient object.

    Parameters
    ----------
    page : Page
        A Notion page to parse.

    Returns
    -------
    Ingredient
        An ingredient object for that page.
    """
    properties = page.properties
    name = (
        properties.get("Name", {}).get("title", [{}])[0].get("text", {}).get("content")
    )
    type = properties.get("Type", {}).get("select", {}).get("name")
    units_of_measurement = (
        properties.get("Units of Measurement", {}).get("select", {}).get("name")
    )
    calories_per_100g = properties.get("Calories per 100g", {}).get("number")
    protein_per_100g = properties.get("Protein per 100g", {}).get("number")
    fat_per_100g = properties.get("Fat per 100g", {}).get("number")
    carbs_per_100g = properties.get("Carbohydrate per 100g", {}).get("number")
    shelf_life_room = properties.get("Shelf life room", {}).get("number")
    shelf_life_fridge = properties.get("Shelf life fridge", {}).get("number")
    shelf_life_freezer = properties.get("Shelf life freezer", {}).get("number")
    return Ingredient(
        name=name,
        type=type,
        units_of_measurement=units_of_measurement.lower(),
        calories_per_100g=calories_per_100g,
        protein_per_100g=protein_per_100g,
        fat_per_100g=fat_per_100g,
        carbs_per_100g=carbs_per_100g,
        shelf_life_room=shelf_life_room,
        shelf_life_fridge=shelf_life_fridge,
        shelf_life_freezer=shelf_life_freezer,
    )
