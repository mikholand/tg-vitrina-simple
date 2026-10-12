import os

from granian.constants import Interfaces
from granian.server import Server


def main() -> None:
    host = os.environ.get("BACKEND_HOST", "0.0.0.0")
    port = int(os.environ.get("BACKEND_PORT", "8000"))

    server = Server(
        target="app.asgi.app:create_app",
        factory=True,
        address=host,
        port=port,
        interface=Interfaces.ASGI,
        workers=int(os.environ.get("BACKEND_WORKERS", "1")),
    )
    server.serve()


if __name__ == "__main__":
    main()
