from dishka import AsyncContainer, make_async_container

from app.di.providers import (
    ClientProvider,
    CoreProvider,
    RepositoryProvider,
    ServiceProvider,
    SessionProvider,
)


def build_container() -> AsyncContainer:
    return make_async_container(
        CoreProvider(),
        SessionProvider(),
        RepositoryProvider(),
        ClientProvider(),
        ServiceProvider(),
    )
