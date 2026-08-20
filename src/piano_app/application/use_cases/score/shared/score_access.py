from piano_app.application.errors import ScoreNotFoundError, ScoreNotOwnedError
from piano_app.application.ports import ScoreRepository
from piano_app.domain.score import Score, ScoreMeta


async def require_readable_score(
    *,
    score_repository: ScoreRepository,
    score_id: str,
    viewer_id: str | None,
) -> Score:
    score: Score | None = await score_repository.get(score_id=score_id)

    if score is None:
        raise ScoreNotFoundError(score_id=score_id)

    if not score.is_public and score.author_id != viewer_id:
        raise ScoreNotFoundError(score_id=score_id)

    return score


async def require_readable_score_meta(
    *,
    score_repository: ScoreRepository,
    score_id: str,
    viewer_id: str | None,
) -> ScoreMeta:
    meta: ScoreMeta | None = await score_repository.get_meta(score_id=score_id)
    if meta is None:
        raise ScoreNotFoundError(score_id=score_id)

    if not meta.is_public and meta.author_id != viewer_id:
        raise ScoreNotFoundError(score_id=score_id)

    return meta


# TODO add frozen logic
async def require_score_write_access(
    *,
    score_repository: ScoreRepository,
    score_id: str,
    actor_id: str,
) -> None:
    meta: ScoreMeta | None = await score_repository.get_meta(score_id=score_id)
    if meta is None:
        raise ScoreNotFoundError(score_id=score_id)

    if meta.author_id != actor_id:
        if meta.is_public:
            raise ScoreNotOwnedError(score_id=score_id)

        raise ScoreNotFoundError(score_id=score_id)
