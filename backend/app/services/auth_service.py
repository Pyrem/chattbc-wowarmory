from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User
from app.schemas.user import (
    AuthResponse,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    ResetPasswordRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
)

logger = structlog.get_logger()


class InvalidRefreshTokenError(Exception):
    pass


class EmailAlreadyExistsError(Exception):
    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"Email {email} already registered")


class InvalidCredentialsError(Exception):
    pass


class InvalidVerificationTokenError(Exception):
    pass


class EmailAlreadyVerifiedError(Exception):
    pass


class InvalidPasswordResetTokenError(Exception):
    pass


class AuthService:
    @staticmethod
    def _hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    @staticmethod
    def _verify_password(password: str, password_hash: str) -> bool:
        return bcrypt.checkpw(password.encode(), password_hash.encode())

    @staticmethod
    def _create_access_token(user_id: int) -> str:
        payload = {
            "sub": str(user_id),
            "exp": datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes),
            "type": "access",
        }
        return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    @staticmethod
    def _create_refresh_token(user_id: int) -> str:
        payload = {
            "sub": str(user_id),
            "exp": datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days),
            "type": "refresh",
        }
        return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    @staticmethod
    def _user_to_response(user: User) -> UserResponse:
        return UserResponse(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            email_verified=user.email_verified,
            battle_net_linked=user.battle_net_id is not None,
        )

    @staticmethod
    def _create_verification_token(user_id: int) -> str:
        payload = {
            "sub": str(user_id),
            "exp": datetime.now(UTC) + timedelta(hours=settings.verification_token_expire_hours),
            "type": "email_verification",
        }
        return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    @staticmethod
    def _create_password_reset_token(user_id: int) -> str:
        payload = {
            "sub": str(user_id),
            "exp": datetime.now(UTC) + timedelta(hours=settings.password_reset_token_expire_hours),
            "type": "password_reset",
        }
        return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    @staticmethod
    def _send_verification_email(email: str, token: str) -> None:
        logger.info("verification_email_stub", email=email, token=token)

    @staticmethod
    def _send_password_reset_email(email: str, token: str) -> None:
        logger.info("password_reset_email_stub", email=email, token=token)

    def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        try:
            payload = jwt.decode(
                refresh_token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
            )
        except jwt.InvalidTokenError as exc:
            raise InvalidRefreshTokenError from exc

        if payload.get("type") != "refresh":
            raise InvalidRefreshTokenError

        user_id = payload.get("sub")
        if user_id is None:
            raise InvalidRefreshTokenError

        return TokenResponse(access_token=self._create_access_token(int(user_id)))

    async def login(self, db: AsyncSession, payload: LoginRequest) -> AuthResponse:
        result = await db.execute(select(User).where(User.email == payload.email))
        user = result.scalar_one_or_none()
        if user is None or not self._verify_password(payload.password, user.password_hash):
            raise InvalidCredentialsError

        user.last_login = datetime.now(UTC)
        await db.commit()
        await db.refresh(user)

        return AuthResponse(
            user=self._user_to_response(user),
            access_token=self._create_access_token(user.id),
            refresh_token=self._create_refresh_token(user.id),
        )

    async def verify_email(self, db: AsyncSession, token: str) -> MessageResponse:
        try:
            payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        except jwt.InvalidTokenError as exc:
            raise InvalidVerificationTokenError from exc

        if payload.get("type") != "email_verification":
            raise InvalidVerificationTokenError

        user_id = payload.get("sub")
        if user_id is None:
            raise InvalidVerificationTokenError

        result = await db.execute(select(User).where(User.id == int(user_id)))
        user = result.scalar_one_or_none()
        if user is None:
            raise InvalidVerificationTokenError

        if user.email_verified:
            raise EmailAlreadyVerifiedError

        user.email_verified = True
        await db.commit()

        return MessageResponse(detail="Email verified successfully")

    async def resend_verification(self, db: AsyncSession, user: User) -> MessageResponse:
        if user.email_verified:
            raise EmailAlreadyVerifiedError

        token = self._create_verification_token(user.id)
        self._send_verification_email(user.email, token)

        return MessageResponse(detail="Verification email sent")

    async def forgot_password(
        self, db: AsyncSession, payload: ForgotPasswordRequest
    ) -> MessageResponse:
        result = await db.execute(select(User).where(User.email == payload.email))
        user = result.scalar_one_or_none()
        if user is not None:
            token = self._create_password_reset_token(user.id)
            self._send_password_reset_email(user.email, token)
        # Always return success to prevent email enumeration
        return MessageResponse(detail="If the email exists, a reset link has been sent")

    async def reset_password(
        self, db: AsyncSession, payload: ResetPasswordRequest
    ) -> MessageResponse:
        try:
            decoded = jwt.decode(
                payload.token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
            )
        except jwt.InvalidTokenError as exc:
            raise InvalidPasswordResetTokenError from exc

        if decoded.get("type") != "password_reset":
            raise InvalidPasswordResetTokenError

        user_id = decoded.get("sub")
        if user_id is None:
            raise InvalidPasswordResetTokenError

        result = await db.execute(select(User).where(User.id == int(user_id)))
        user = result.scalar_one_or_none()
        if user is None:
            raise InvalidPasswordResetTokenError

        user.password_hash = self._hash_password(payload.new_password)
        await db.commit()

        return MessageResponse(detail="Password has been reset successfully")

    async def register(self, db: AsyncSession, payload: UserCreate) -> AuthResponse:
        result = await db.execute(select(User).where(User.email == payload.email))
        if result.scalar_one_or_none() is not None:
            raise EmailAlreadyExistsError(payload.email)

        user = User(
            email=payload.email,
            password_hash=self._hash_password(payload.password),
            display_name=payload.display_name,
            email_verified=False,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        verification_token = self._create_verification_token(user.id)
        self._send_verification_email(user.email, verification_token)

        return AuthResponse(
            user=self._user_to_response(user),
            access_token=self._create_access_token(user.id),
            refresh_token=self._create_refresh_token(user.id),
        )
