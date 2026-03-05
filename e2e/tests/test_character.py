from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:3000"


def test_character_not_found_page(page: Page) -> None:
    """Navigating to a non-existent character shows the not-found page."""
    page.goto(f"{BASE_URL}/character/faerlina/nonexistentchar12345")
    expect(page.locator("text=Character Not Found")).to_be_visible(timeout=10000)


def test_character_page_structure(page: Page) -> None:
    """Character page route exists and renders without crash."""
    resp = page.goto(f"{BASE_URL}/character/faerlina/testchar")
    # Page should load (200 or 404 not-found page — both are valid)
    assert resp is not None
    status = resp.status
    assert status in (200, 404)


def test_character_not_found_has_home_link(page: Page) -> None:
    """Not-found page has a link back to home."""
    page.goto(f"{BASE_URL}/character/faerlina/nonexistentchar12345")
    expect(page.locator("text=Character Not Found")).to_be_visible(timeout=10000)
    page.click("text=Back to Home")
    expect(page).to_have_url(f"{BASE_URL}/", timeout=5000)
