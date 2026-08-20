from datetime import UTC, datetime, timedelta
from typing import Final
from uuid import uuid4

import jwt

from piano_app.application.ports.auth import AccessToken, AccessTokenVerificationError


class JWTAccessTokenService:
    _ALGORITHM: Final[str] = "HS256"
    _MIN_SECRET_LENGTH: Final[int] = 64

    def __init__(
        self,
        *,
        secret: str,
        issuer: str,
        audience: str,
        ttl: timedelta,
    ) -> None:
        if len(secret.encode()) < self._MIN_SECRET_LENGTH:
            raise ValueError(f"JWT secret must contain at least {self._MIN_SECRET_LENGTH} bytes.")

        self._secret: str = secret
        self._issuer: str = issuer
        self._audience: str = audience
        self._ttl: timedelta = ttl

    # TODO use 'jti' claim to blacklist by token ID and not by user ID
    def issue(self, *, user_id: str) -> AccessToken:
        issued_at: datetime = datetime.now(UTC)
        expires_at: datetime = issued_at + self._ttl
        token: str = jwt.encode(
            {
                "sub": user_id,
                "iss": self._issuer,
                "aud": self._audience,
                "iat": issued_at,
                "exp": expires_at,
                "jti": str(uuid4()),
            },
            self._secret,
            algorithm=self._ALGORITHM,
        )

        return AccessToken(
            value=token,
            expires_in_seconds=int(self._ttl.total_seconds()),
        )

    def verify(self, *, token: str) -> str:
        try:
            claims: dict[str, object] = jwt.decode(
                token,
                self._secret,
                algorithms=[self._ALGORITHM],
                issuer=self._issuer,
                audience=self._audience,
            )
        except jwt.InvalidTokenError:
            raise AccessTokenVerificationError from None

        # check for a correct subject
        subject: object = claims.get("sub")
        if not isinstance(subject, str) or not subject:
            raise AccessTokenVerificationError

        return subject
