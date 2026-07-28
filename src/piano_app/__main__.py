import uvicorn

from piano_app.bootstrap.container import build_app
from piano_app.bootstrap.settings import load_environment


def main() -> None:
    load_environment()
    uvicorn.run(build_app(), host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
