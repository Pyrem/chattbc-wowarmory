import pytest
from playwright.sync_api import Page

BASE_URL = "http://localhost:3000"
API_URL = "http://localhost:8000"


@pytest.fixture(autouse=True)
def _navigate_base(page: Page) -> None:
    """Ensure each test starts from the base URL."""
    page.goto(BASE_URL)
