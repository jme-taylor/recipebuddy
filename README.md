# RecipeBuddy

A Python application to manage and organize recipes and ingredients.

## Development

### Setup

1. Clone the repository
2. Create a virtual environment: `python -m venv .venv`
3. Activate the environment: 
   - Windows: `.venv\Scripts\activate`
   - Unix/Mac: `source .venv/bin/activate`
4. Install dependencies: `pip install -e .`
5. For development, install test dependencies: `pip install -e ".[test]"`

### Environment Variables

Create a `.env` file with the following variables:
```
NOTION_TOKEN=your_notion_token
```

### Running Tests

Run tests with pytest:
```
python -m pytest
```

Or use the convenience script:
```
python run_tests.py
```

To include coverage report:
```
python -m pytest --cov=recipe_buddy
```