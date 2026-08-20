from dataclasses import dataclass

from piano_app.application.errors import (
    IdentityAlreadyLinkedError,
    InvalidAccessTokenError,
    InvalidExternalCredentialError,
    InvalidRefreshTokenError,
    UsernameConflictError,
    UsernameRequiredError,
)
from piano_app.application.ports.auth import (
    AccessToken,
    AccessTokenService,
    AccessTokenVerificationError,
    AuthUoWFactory,
    ExternalCredentialVerificationError,
    ExternalIdentityVerifier,
    IdentityLinkConflictError,
    RotatedRefreshSession,
    UsernameAlreadyExistsError,
    UserProfile,
    VerifiedIdentity,
)


@dataclass(frozen=True, slots=True)
class AuthSession:
    access_token: AccessToken
    refresh_credential: str


class AuthService:
    def __init__(
        self,
        *,
        identity_verifier: ExternalIdentityVerifier,
        access_tokens: AccessTokenService,
        auth_uow_factory: AuthUoWFactory,
    ) -> None:
        self._identity_verifier: ExternalIdentityVerifier = identity_verifier
        self._access_tokens: AccessTokenService = access_tokens
        self._auth_uow_factory: AuthUoWFactory = auth_uow_factory

    # If the identity already resolves to a user, `username` is intentionally
    # ignored — signing in as an existing account never renames it.
    async def sign_in(
        self,
        *,
        credential: str,
        username: str | None,
    ) -> AuthSession:
        try:
            identity: VerifiedIdentity = await self._identity_verifier.verify(credential=credential)
        except ExternalCredentialVerificationError as error:
            raise InvalidExternalCredentialError from error

        async with self._auth_uow_factory() as uow:
            user_id: str | None = await uow.identity_repository.find_user_id(identity=identity)

            if user_id is None:
                if username is None:
                    raise UsernameRequiredError

                # Concurrent sign-in (e.g. a double-tapped button) can lose a race
                # here: another request created the account between our find and our
                # create. On the resulting constraint violation we roll back the
                # poisoned tx and re-resolve by identity:
                #   - IdentityLinkConflictError: the winner linked OUR identity, so
                #     the re-read always finds it -> we sign in as that user.
                #   - UsernameAlreadyExistsError: if the re-read finds our identity it was
                #     the same race (same username) -> sign in; if not, the username
                #     is genuinely taken by someone else -> translate -> 409.
                try:
                    user: UserProfile = await uow.identity_repository.create_user(username=username)
                    user_id = user.user_id

                    await uow.identity_repository.add_identity(user_id=user_id, identity=identity)
                except (IdentityLinkConflictError, UsernameAlreadyExistsError) as error:
                    await uow.rollback()
                    user_id = await uow.identity_repository.find_user_id(identity=identity)
                    if user_id is None:
                        if isinstance(error, UsernameAlreadyExistsError):
                            raise UsernameConflictError(username=error.username) from error
                        raise IdentityAlreadyLinkedError from error

            refresh_credential: str = await uow.refresh_session_repository.create(user_id=user_id)

            await uow.commit()

        return AuthSession(
            access_token=self._access_tokens.issue(user_id=user_id),
            refresh_credential=refresh_credential,
        )

    def authenticate_access_token(self, *, token: str | None) -> str:
        if token is None:
            raise InvalidAccessTokenError

        try:
            return self._access_tokens.verify(token=token)
        except AccessTokenVerificationError as error:
            raise InvalidAccessTokenError from error

    async def refresh(self, *, credential: str) -> AuthSession:
        async with self._auth_uow_factory() as uow:
            rotated: RotatedRefreshSession | None = await uow.refresh_session_repository.rotate(
                credential=credential
            )
            if rotated is None:
                raise InvalidRefreshTokenError

            await uow.commit()

        return AuthSession(
            access_token=self._access_tokens.issue(user_id=rotated.user_id),
            refresh_credential=rotated.credential,
        )

    async def get_current_user(self, *, user_id: str) -> UserProfile:
        async with self._auth_uow_factory() as uow:
            user: UserProfile | None = await uow.identity_repository.find_user(user_id=user_id)

            if user is None:
                raise InvalidAccessTokenError

        return user

    async def logout(self, *, credential: str) -> None:
        async with self._auth_uow_factory() as uow:
            await uow.refresh_session_repository.revoke(credential=credential)
            await uow.commit()
