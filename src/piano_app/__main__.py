import asyncio

from piano_app.bootstrap.settings import Settings, load_environment, load_settings


async def main() -> None:
    load_environment()

    try:
        settings: Settings = load_settings()
    except Exception as exc:
        print(exc)
        return


if __name__ == "__main__":
    asyncio.run(main())
