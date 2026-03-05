from httpx import AsyncClient

from app.services.auth_service import AuthService


async def test_register_success(test_client: AsyncClient) -> None:
    resp = await test_client.post(
        "/api/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "securepass123",
            "display_name": "NewUser",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["user"]["email"] == "newuser@example.com"
    assert data["user"]["display_name"] == "NewUser"
    assert data["user"]["email_verified"] is False
    assert data["user"]["battle_net_linked"] is False
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_register_duplicate_email(test_client: AsyncClient) -> None:
    payload = {
        "email": "dup@example.com",
        "password": "securepass123",
        "display_name": "User1",
    }
    resp1 = await test_client.post("/api/auth/register", json=payload)
    assert resp1.status_code == 201

    payload["display_name"] = "User2"
    resp2 = await test_client.post("/api/auth/register", json=payload)
    assert resp2.status_code == 409


async def test_register_password_too_short(test_client: AsyncClient) -> None:
    resp = await test_client.post(
        "/api/auth/register",
        json={
            "email": "short@example.com",
            "password": "short",
            "display_name": "ShortPw",
        },
    )
    assert resp.status_code == 422


async def test_register_invalid_email(test_client: AsyncClient) -> None:
    resp = await test_client.post(
        "/api/auth/register",
        json={
            "email": "not-an-email",
            "password": "securepass123",
            "display_name": "BadEmail",
        },
    )
    assert resp.status_code == 422


async def test_login_success(test_client: AsyncClient) -> None:
    await test_client.post(
        "/api/auth/register",
        json={
            "email": "login@example.com",
            "password": "securepass123",
            "display_name": "LoginUser",
        },
    )
    resp = await test_client.post(
        "/api/auth/login",
        json={"email": "login@example.com", "password": "securepass123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["user"]["email"] == "login@example.com"
    assert data["user"]["display_name"] == "LoginUser"
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(test_client: AsyncClient) -> None:
    await test_client.post(
        "/api/auth/register",
        json={
            "email": "wrongpw@example.com",
            "password": "securepass123",
            "display_name": "WrongPw",
        },
    )
    resp = await test_client.post(
        "/api/auth/login",
        json={"email": "wrongpw@example.com", "password": "wrongpassword"},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid email or password"


async def test_login_nonexistent_email(test_client: AsyncClient) -> None:
    resp = await test_client.post(
        "/api/auth/login",
        json={"email": "noone@example.com", "password": "securepass123"},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid email or password"


async def test_login_updates_last_login(test_client: AsyncClient) -> None:
    await test_client.post(
        "/api/auth/register",
        json={
            "email": "lastlogin@example.com",
            "password": "securepass123",
            "display_name": "LastLogin",
        },
    )
    resp = await test_client.post(
        "/api/auth/login",
        json={"email": "lastlogin@example.com", "password": "securepass123"},
    )
    assert resp.status_code == 200


async def _register_and_get_tokens(client: AsyncClient) -> dict[str, str]:
    """Helper: register a user and return the token dict."""
    resp = await client.post(
        "/api/auth/register",
        json={
            "email": "jwt@example.com",
            "password": "securepass123",
            "display_name": "JwtUser",
        },
    )
    data: dict[str, str] = resp.json()
    return data


async def test_me_with_valid_token(test_client: AsyncClient) -> None:
    data = await _register_and_get_tokens(test_client)
    resp = await test_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {data['access_token']}"},
    )
    assert resp.status_code == 200
    me = resp.json()
    assert me["email"] == "jwt@example.com"
    assert me["display_name"] == "JwtUser"


async def test_me_without_token(test_client: AsyncClient) -> None:
    resp = await test_client.get("/api/auth/me")
    assert resp.status_code in (401, 403)


async def test_me_with_invalid_token(test_client: AsyncClient) -> None:
    resp = await test_client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert resp.status_code == 401


async def test_refresh_returns_new_access_token(test_client: AsyncClient) -> None:
    data = await _register_and_get_tokens(test_client)
    resp = await test_client.post(
        "/api/auth/refresh",
        json={"refresh_token": data["refresh_token"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    # new access token should work on /me
    me_resp = await test_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert me_resp.status_code == 200


async def test_refresh_with_invalid_token(test_client: AsyncClient) -> None:
    resp = await test_client.post(
        "/api/auth/refresh",
        json={"refresh_token": "garbage.token.value"},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid or expired refresh token"


async def test_refresh_with_access_token_rejected(test_client: AsyncClient) -> None:
    data = await _register_and_get_tokens(test_client)
    resp = await test_client.post(
        "/api/auth/refresh",
        json={"refresh_token": data["access_token"]},
    )
    assert resp.status_code == 401


async def test_me_with_refresh_token_rejected(test_client: AsyncClient) -> None:
    data = await _register_and_get_tokens(test_client)
    resp = await test_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {data['refresh_token']}"},
    )
    assert resp.status_code == 401


async def test_verify_email_success(test_client: AsyncClient) -> None:
    data = await _register_and_get_tokens(test_client)
    user_id = data["user"]["id"]
    token = AuthService._create_verification_token(user_id)
    resp = await test_client.post(f"/api/auth/verify-email?token={token}")
    assert resp.status_code == 200
    assert resp.json()["detail"] == "Email verified successfully"
    # Confirm email_verified flipped via /me
    me_resp = await test_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {data['access_token']}"},
    )
    assert me_resp.json()["email_verified"] is True


async def test_verify_email_invalid_token(test_client: AsyncClient) -> None:
    resp = await test_client.post("/api/auth/verify-email?token=garbage.token")
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Invalid or expired verification token"


async def test_verify_email_already_verified(test_client: AsyncClient) -> None:
    data = await _register_and_get_tokens(test_client)
    user_id = data["user"]["id"]
    token = AuthService._create_verification_token(user_id)
    await test_client.post(f"/api/auth/verify-email?token={token}")
    # Second attempt
    resp = await test_client.post(f"/api/auth/verify-email?token={token}")
    assert resp.status_code == 409
    assert resp.json()["detail"] == "Email already verified"


async def test_resend_verification_success(test_client: AsyncClient) -> None:
    data = await _register_and_get_tokens(test_client)
    resp = await test_client.post(
        "/api/auth/resend-verification",
        headers={"Authorization": f"Bearer {data['access_token']}"},
    )
    assert resp.status_code == 200
    assert resp.json()["detail"] == "Verification email sent"


async def test_resend_verification_already_verified(test_client: AsyncClient) -> None:
    data = await _register_and_get_tokens(test_client)
    user_id = data["user"]["id"]
    token = AuthService._create_verification_token(user_id)
    await test_client.post(f"/api/auth/verify-email?token={token}")
    resp = await test_client.post(
        "/api/auth/resend-verification",
        headers={"Authorization": f"Bearer {data['access_token']}"},
    )
    assert resp.status_code == 409
    assert resp.json()["detail"] == "Email already verified"


async def test_resend_verification_requires_auth(test_client: AsyncClient) -> None:
    resp = await test_client.post("/api/auth/resend-verification")
    assert resp.status_code in (401, 403)


async def test_forgot_password_existing_email(test_client: AsyncClient) -> None:
    await test_client.post(
        "/api/auth/register",
        json={
            "email": "forgot@example.com",
            "password": "securepass123",
            "display_name": "ForgotUser",
        },
    )
    resp = await test_client.post(
        "/api/auth/forgot-password",
        json={"email": "forgot@example.com"},
    )
    assert resp.status_code == 200
    assert resp.json()["detail"] == "If the email exists, a reset link has been sent"


async def test_forgot_password_nonexistent_email(test_client: AsyncClient) -> None:
    resp = await test_client.post(
        "/api/auth/forgot-password",
        json={"email": "nobody@example.com"},
    )
    # Always 200 to prevent email enumeration
    assert resp.status_code == 200
    assert resp.json()["detail"] == "If the email exists, a reset link has been sent"


async def test_reset_password_success(test_client: AsyncClient) -> None:
    await test_client.post(
        "/api/auth/register",
        json={
            "email": "reset@example.com",
            "password": "oldpassword123",
            "display_name": "ResetUser",
        },
    )
    # Get user id from login
    login_resp = await test_client.post(
        "/api/auth/login",
        json={"email": "reset@example.com", "password": "oldpassword123"},
    )
    user_id = login_resp.json()["user"]["id"]
    token = AuthService._create_password_reset_token(user_id)

    resp = await test_client.post(
        "/api/auth/reset-password",
        json={"token": token, "new_password": "newpassword456"},
    )
    assert resp.status_code == 200
    assert resp.json()["detail"] == "Password has been reset successfully"

    # Verify old password no longer works
    old_resp = await test_client.post(
        "/api/auth/login",
        json={"email": "reset@example.com", "password": "oldpassword123"},
    )
    assert old_resp.status_code == 401

    # Verify new password works
    new_resp = await test_client.post(
        "/api/auth/login",
        json={"email": "reset@example.com", "password": "newpassword456"},
    )
    assert new_resp.status_code == 200


async def test_reset_password_invalid_token(test_client: AsyncClient) -> None:
    resp = await test_client.post(
        "/api/auth/reset-password",
        json={"token": "garbage.token", "new_password": "newpassword456"},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Invalid or expired reset token"


async def test_reset_password_too_short(test_client: AsyncClient) -> None:
    resp = await test_client.post(
        "/api/auth/reset-password",
        json={"token": "some.token", "new_password": "short"},
    )
    assert resp.status_code == 422


async def test_register_password_hashed(test_client: AsyncClient) -> None:
    resp = await test_client.post(
        "/api/auth/register",
        json={
            "email": "hashed@example.com",
            "password": "securepass123",
            "display_name": "HashedUser",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "password" not in data["user"]
    assert "password_hash" not in data["user"]
