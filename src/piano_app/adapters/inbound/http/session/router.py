from typing import Annotated, Literal

from fastapi import APIRouter, Cookie, Depends, Response

from piano_app.adapters.inbound.http.current_user import CurrentUser
from piano_app.application.errors import InvalidRefreshTokenError
from piano_app.application.ports.auth import UserProfile
from piano_app.application.use_cases.auth import AuthService, AuthSession

from .requests import GoogleSignInRequest
from .responses import AccessTokenResponse, CurrentUserResponse

_REFRESH_COOKIE_NAME: str = "piano_refresh_token"


class RefreshCookie:
    """Sets/deletes the refresh-session cookie. Config (secure/samesite/max_age) is
    captured once at construction, not re-threaded through every call site."""

    def __init__(
        self,
        *,
        secure: bool,
        samesite: Literal["lax", "strict", "none"],
        max_age: int,
    ) -> None:
        self._secure: bool = secure
        self._samesite: Literal["lax", "strict", "none"] = samesite
        self._max_age: int = max_age

    def set(self, *, response: Response, session: AuthSession) -> None:
        response.set_cookie(
            key=_REFRESH_COOKIE_NAME,
            value=session.refresh_credential,
            max_age=self._max_age,
            httponly=True,
            secure=self._secure,
            samesite=self._samesite,
            path="/auth",
        )

    def delete(self, *, response: Response) -> None:
        response.delete_cookie(
            key=_REFRESH_COOKIE_NAME,
            httponly=True,
            secure=self._secure,
            samesite=self._samesite,
            path="/auth",
        )


def build_session_router(
    *,
    service: AuthService,
    current_user: CurrentUser,
    refresh_cookie_secure: bool,
    refresh_cookie_samesite: Literal["lax", "strict", "none"],
    refresh_cookie_max_age: int,
) -> APIRouter:
    router: APIRouter = APIRouter(
        prefix="/auth",
        tags=["auth"],
    )
    refresh_cookie: RefreshCookie = RefreshCookie(
        secure=refresh_cookie_secure,
        samesite=refresh_cookie_samesite,
        max_age=refresh_cookie_max_age,
    )

    # TODO consider generalizing this to other providers
    @router.post(path="/google", status_code=200)
    async def sign_in_with_google(
        request: GoogleSignInRequest,
        response: Response,
    ) -> AccessTokenResponse:
        session: AuthSession = await service.sign_in(
            credential=request.id_token,
            username=request.username,
        )
        refresh_cookie.set(response=response, session=session)
        return AccessTokenResponse.from_session(session)

    @router.post(path="/refresh", status_code=200)
    async def refresh(
        response: Response,
        refresh_credential: Annotated[
            str | None,
            Cookie(alias=_REFRESH_COOKIE_NAME),
        ] = None,
    ) -> AccessTokenResponse:
        if refresh_credential is None:
            raise InvalidRefreshTokenError
        session: AuthSession = await service.refresh(credential=refresh_credential)
        refresh_cookie.set(response=response, session=session)
        return AccessTokenResponse.from_session(session)

    @router.get(path="/me", status_code=200)
    async def get_current_user(
        user_id: Annotated[str, Depends(current_user)],
        response: Response,
    ) -> CurrentUserResponse:
        profile: UserProfile = await service.get_current_user(user_id=user_id)
        response.headers["Cache-Control"] = "no-store"
        return CurrentUserResponse.from_profile(profile)

    @router.post(path="/logout", status_code=204)
    async def logout(
        response: Response,
        refresh_credential: Annotated[
            str | None,
            Cookie(alias=_REFRESH_COOKIE_NAME),
        ] = None,
    ) -> None:
        if refresh_credential is not None:
            await service.logout(credential=refresh_credential)

        refresh_cookie.delete(response=response)

    return router
