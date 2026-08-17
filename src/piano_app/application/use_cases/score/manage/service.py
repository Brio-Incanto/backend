from piano_app.application.ports import ScoreUoWFactory


class ScoreManageService:
    def __init__(self, *, score_uow_factory: ScoreUoWFactory) -> None:
        self._score_uow_factory: ScoreUoWFactory = score_uow_factory

    async def update_visibility(self, *, score_id: str, is_public: bool) -> None:
        pass

    async def delete(self, *, score_id: str) -> None:
        pass
