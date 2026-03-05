from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:3000"


def test_settings_page_exists(page: Page) -> None:
    """Settings page route renders without crash."""
    resp = page.goto(f"{BASE_URL}/settings")
    assert resp is not None
    assert resp.status in (200, 304)


def test_settings_shows_login_prompt(page: Page) -> None:
    """Unauthenticated user sees login prompt on settings page."""
    page.goto(f"{BASE_URL}/settings")
    expect(page.locator("text=log in")).to_be_visible(timeout=10000)


def test_settings_has_nav_link(page: Page) -> None:
    """Settings link exists in the site header."""
    page.goto(BASE_URL)
    expect(page.locator("a[href='/settings']")).to_be_visible(timeout=5000)
