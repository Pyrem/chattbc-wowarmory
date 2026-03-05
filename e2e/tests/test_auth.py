from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:3000"


def _register_user(
    page: Page,
    email: str = "e2e@example.com",
    password: str = "securepass123",
    display_name: str = "E2EUser",
) -> None:
    """Helper to register a user via the UI."""
    page.goto(f"{BASE_URL}/register")
    page.fill('input[id="email"]', email)
    page.fill('input[id="displayName"]', display_name)
    page.fill('input[id="password"]', password)
    page.click('button[type="submit"]')
    # Wait for client-side navigation (Next.js soft nav)
    expect(page).to_have_url(f"{BASE_URL}/", timeout=10000)


def test_register_happy_path(page: Page) -> None:
    """Register a new user and verify redirect to home."""
    page.goto(f"{BASE_URL}/register")
    expect(page.locator('[data-slot="card-title"]')).to_contain_text("Create Account")

    page.fill('input[id="email"]', "reg@example.com")
    page.fill('input[id="displayName"]', "RegUser")
    page.fill('input[id="password"]', "securepass123")
    page.click('button[type="submit"]')

    expect(page).to_have_url(f"{BASE_URL}/", timeout=10000)


def test_register_duplicate_email(page: Page) -> None:
    """Attempting to register with an existing email shows an error."""
    _register_user(page, email="dup-e2e@example.com")

    page.evaluate("localStorage.clear()")
    page.goto(f"{BASE_URL}/register")
    page.fill('input[id="email"]', "dup-e2e@example.com")
    page.fill('input[id="displayName"]', "DupUser2")
    page.fill('input[id="password"]', "securepass123")
    page.click('button[type="submit"]')

    expect(page.locator("text=already exists")).to_be_visible(timeout=5000)


def test_register_validation_short_password(page: Page) -> None:
    """Client-side validation rejects short passwords."""
    page.goto(f"{BASE_URL}/register")
    page.fill('input[id="email"]', "short@example.com")
    page.fill('input[id="displayName"]', "ShortPw")
    page.fill('input[id="password"]', "short")
    page.click('button[type="submit"]')

    # Should stay on register page (not redirect)
    expect(page).to_have_url(f"{BASE_URL}/register")


def test_login_happy_path(page: Page) -> None:
    """Register, logout (clear storage), then login successfully."""
    _register_user(page, email="login-e2e@example.com")

    page.evaluate("localStorage.clear()")

    page.goto(f"{BASE_URL}/login")
    expect(page.locator('[data-slot="card-title"]')).to_contain_text("Sign In")

    page.fill('input[id="email"]', "login-e2e@example.com")
    page.fill('input[id="password"]', "securepass123")
    page.click('button[type="submit"]')

    expect(page).to_have_url(f"{BASE_URL}/", timeout=10000)


def test_login_invalid_credentials(page: Page) -> None:
    """Wrong password shows an error message."""
    _register_user(page, email="badinv-e2e@example.com")
    page.evaluate("localStorage.clear()")

    page.goto(f"{BASE_URL}/login")
    page.fill('input[id="email"]', "badinv-e2e@example.com")
    page.fill('input[id="password"]', "wrongpassword")
    page.click('button[type="submit"]')

    expect(page.locator("text=Invalid email or password")).to_be_visible(timeout=5000)


def test_login_link_to_register(page: Page) -> None:
    """Login page has a link to register."""
    page.goto(f"{BASE_URL}/login")
    page.click("text=Sign up")
    expect(page).to_have_url(f"{BASE_URL}/register")


def test_register_link_to_login(page: Page) -> None:
    """Register page has a link to login."""
    page.goto(f"{BASE_URL}/register")
    page.click("text=Sign in")
    expect(page).to_have_url(f"{BASE_URL}/login")


def test_forgot_password_page(page: Page) -> None:
    """Forgot password form submits and shows confirmation."""
    page.goto(f"{BASE_URL}/forgot-password")
    expect(page.locator('[data-slot="card-title"]')).to_contain_text("Forgot Password")

    page.fill('input[id="email"]', "forgot-e2e@example.com")
    page.click('button[type="submit"]')

    expect(page.locator("text=reset link")).to_be_visible(timeout=5000)


def test_login_forgot_password_link(page: Page) -> None:
    """Login page has a link to forgot password."""
    page.goto(f"{BASE_URL}/login")
    page.click("text=Forgot password?")
    expect(page).to_have_url(f"{BASE_URL}/forgot-password")


def test_reset_password_page_renders(page: Page) -> None:
    """Reset password page renders with a token param."""
    page.goto(f"{BASE_URL}/reset-password?token=test-token")
    expect(page.locator('[data-slot="card-title"]')).to_contain_text("Reset Password")
    expect(page.locator('input[id="password"]')).to_be_visible()
    expect(page.locator('input[id="confirmPassword"]')).to_be_visible()


def test_reset_password_mismatch(page: Page) -> None:
    """Mismatched passwords show validation error."""
    page.goto(f"{BASE_URL}/reset-password?token=test-token")
    page.fill('input[id="password"]', "newpassword123")
    page.fill('input[id="confirmPassword"]', "differentpass")
    page.click('button[type="submit"]')

    expect(page.locator("text=do not match")).to_be_visible(timeout=5000)
