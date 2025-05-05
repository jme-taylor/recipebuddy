import os
from unittest.mock import MagicMock, patch

import pytest

from recipe_buddy.notion import (
    NotionAPIDatabaseResponse,
    NotionDatabase,
    Page,
    parse_ingredient_data,
    parse_ingredient_page,
)
from recipe_buddy.schemas import Ingredient, IngredientType, UnitOfMeasurement


@pytest.fixture
def mock_notion_response():
    """Return a mock response for testing."""
    return {
        "object": "list",
        "results": [
            {
                "object": "page",
                "id": "page_id_1",
                "created_time": "2023-01-01T00:00:00.000Z",
                "last_edited_time": "2023-01-01T00:00:00.000Z",
                "created_by": {"object": "user", "id": "user_id_1"},
                "last_edited_by": {"object": "user", "id": "user_id_1"},
                "parent": {"type": "database_id", "database_id": "database_id_1"},
                "archived": False,
                "in_trash": False,
                "properties": {
                    "Name": {"title": [{"text": {"content": "Chicken"}}]},
                    "Type": {"select": {"name": "Protein"}},
                    "Units of Measurement": {"select": {"name": "grams"}},
                    "Calories per 100g": {"number": 165},
                    "Protein per 100g": {"number": 31},
                    "Fat per 100g": {"number": 3.6},
                    "Carbohydrate per 100g": {"number": 0},
                    "Shelf life room": {"number": 1},
                    "Shelf life fridge": {"number": 3},
                    "Shelf life freezer": {"number": 90},
                    "Substitutions": {
                        "rich_text": [{"text": {"content": "Turkey, Tofu"}}]
                    },
                },
                "url": "https://www.notion.so/page_id_1",
            },
            {
                "object": "page",
                "id": "page_id_2",
                "created_time": "2023-01-01T00:00:00.000Z",
                "last_edited_time": "2023-01-01T00:00:00.000Z",
                "created_by": {"object": "user", "id": "user_id_1"},
                "last_edited_by": {"object": "user", "id": "user_id_1"},
                "parent": {"type": "database_id", "database_id": "database_id_1"},
                "archived": False,
                "in_trash": False,
                "properties": {
                    "Name": {"title": [{"text": {"content": "Rice"}}]},
                    "Type": {"select": {"name": "Grain"}},
                    "Units of Measurement": {"select": {"name": "grams"}},
                    "Calories per 100g": {"number": 130},
                    "Protein per 100g": {"number": 2.7},
                    "Fat per 100g": {"number": 0.3},
                    "Carbohydrate per 100g": {"number": 28},
                    "Shelf life room": {"number": 365},
                    "Shelf life fridge": {"number": None},
                    "Shelf life freezer": {"number": None},
                    # No substitutions field
                },
                "url": "https://www.notion.so/page_id_2",
            },
        ],
        "next_cursor": None,
        "has_more": False,
        "type": "page",
        "page_or_database": {},
        "request_id": "request_id_1",
    }


@pytest.fixture
def notion_database():
    """Create a NotionDatabase instance for testing."""
    with patch.dict(os.environ, {"NOTION_TOKEN": "mock_token"}):
        return NotionDatabase("mock_database_id")


def test_parse_ingredient_page(mock_notion_response):
    """Test the parse_ingredient_page function."""
    page = Page(**mock_notion_response["results"][0])
    ingredient = parse_ingredient_page(page)

    assert isinstance(ingredient, Ingredient)
    assert ingredient.name == "Chicken"
    assert ingredient.type == IngredientType.PROTEIN
    assert ingredient.units_of_measurement == UnitOfMeasurement.GRAMS
    assert ingredient.calories_per_100g == 165
    assert ingredient.protein_per_100g == 31
    assert ingredient.fat_per_100g == 3.6
    assert ingredient.carbs_per_100g == 0
    assert ingredient.shelf_life_room == 1
    assert ingredient.shelf_life_fridge == 3
    assert ingredient.shelf_life_freezer == 90


def test_parse_ingredient_page_missing_substitutions(mock_notion_response):
    """Test the parse_ingredient_page function with missing substitutions."""
    page = Page(**mock_notion_response["results"][1])
    ingredient = parse_ingredient_page(page)

    assert isinstance(ingredient, Ingredient)
    assert ingredient.name == "Rice"
    assert ingredient.type == IngredientType.GRAIN


def test_parse_ingredient_data(mock_notion_response):
    """Test the parse_ingredient_data function."""
    pages = [Page(**page) for page in mock_notion_response["results"]]
    ingredients = parse_ingredient_data(pages)

    assert len(ingredients) == 2
    assert all(isinstance(ingredient, Ingredient) for ingredient in ingredients)
    assert ingredients[0].name == "Chicken"
    assert ingredients[1].name == "Rice"


def test_parse_ingredient_data_with_invalid_page(mock_notion_response):
    """Test the parse_ingredient_data function with an invalid page."""
    # Create a valid page and an invalid page with missing required fields
    valid_page = Page(**mock_notion_response["results"][0])
    invalid_page_data = mock_notion_response["results"][0].copy()
    invalid_page_data["properties"]["Calories per 100g"] = {
        "number": None
    }  # Make calories None
    invalid_page = Page(**invalid_page_data)

    pages = [valid_page, invalid_page]

    # Should only return the valid ingredient
    with patch("recipe_buddy.notion.logger") as mock_logger:
        ingredients = parse_ingredient_data(pages)
        assert len(ingredients) == 1
        assert ingredients[0].name == "Chicken"
        mock_logger.info.assert_called()


@patch("requests.post")
def test_notion_database_get_database_page(
    mock_post, notion_database, mock_notion_response
):
    """Test the _get_database_page method."""
    mock_response = MagicMock()
    mock_response.json.return_value = mock_notion_response
    mock_post.return_value = mock_response

    response = notion_database._get_database_page()

    mock_post.assert_called_once()
    assert isinstance(response, NotionAPIDatabaseResponse)
    assert len(response.results) == 2


@patch("recipe_buddy.notion.NotionDatabase._get_database_page")
def test_get_ingredients_data_single_page(
    mock_get_database_page, notion_database, mock_notion_response
):
    """Test the get_ingredients_data method with a single page."""
    mock_get_database_page.return_value = NotionAPIDatabaseResponse(
        **mock_notion_response
    )

    ingredients = notion_database.get_ingredients_data()

    mock_get_database_page.assert_called_once()
    assert len(ingredients) == 2
    assert all(isinstance(ingredient, Ingredient) for ingredient in ingredients)


@patch("recipe_buddy.notion.NotionDatabase._get_database_page")
def test_get_ingredients_data_multiple_pages(
    mock_get_database_page, notion_database, mock_notion_response
):
    """Test the get_ingredients_data method with multiple pages."""
    # First response has more pages
    first_response = mock_notion_response.copy()
    first_response["has_more"] = True
    first_response["next_cursor"] = "next_page_cursor"

    # Second response has no more pages
    second_response = mock_notion_response.copy()
    second_response["has_more"] = False
    second_response["next_cursor"] = None

    mock_get_database_page.side_effect = [
        NotionAPIDatabaseResponse(**first_response),
        NotionAPIDatabaseResponse(**second_response),
    ]

    ingredients = notion_database.get_ingredients_data()

    assert mock_get_database_page.call_count == 2
    assert len(ingredients) == 4  # 2 from first page, 2 from second page
