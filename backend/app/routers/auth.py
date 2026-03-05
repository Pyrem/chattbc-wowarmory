from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import (
    AuthResponse,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
)
from app.services.auth_service import (
    AuthService,
    EmailAlreadyExistsError,
    EmailAlreadyVerifiedError,
    InvalidCredentialsError,
    InvalidPasswordResetTokenError,
    InvalidRefreshTokenError,
    InvalidVerificationTokenError,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


def get_auth_service() -> AuthService:
    return AuthService()


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    try:
        return await auth_service.register(db, payload)
    except EmailAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    try:
        return await auth_service.login(db, payload)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail="Invalid email or password") from exc


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: RefreshRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    try:
        return auth_service.refresh_access_token(payload.refresh_token)
    except InvalidRefreshTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token") from exc


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    try:
        return await auth_service.verify_email(db, token)
    except InvalidVerificationTokenError as exc:
        raise HTTPException(
            status_code=400, detail="Invalid or expired verification token"
        ) from exc
    except EmailAlreadyVerifiedError as exc:
        raise HTTPException(status_code=409, detail="Email already verified") from exc


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    try:
        return await auth_service.resend_verification(db, current_user)
    except EmailAlreadyVerifiedError as exc:
        raise HTTPException(status_code=409, detail="Email already verified") from exc


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    payload: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    return await auth_service.forgot_password(db, payload)


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    try:
        return await auth_service.reset_password(db, payload)
    except InvalidPasswordResetTokenError as exc:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token") from exc


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        display_name=current_user.display_name,
        email_verified=current_user.email_verified,
        battle_net_linked=current_user.battle_net_id is not None,
        battletag=current_user.battletag,
    )
