import asyncio
import contextlib
import signal

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.di.container import build_container
from app.services.extraction import ExtractionService

logger = get_logger("extractor.main")


async def main() -> None:
    settings = get_settings()
    configure_logging(settings.app.LOG_LEVEL)

    container = build_container()
    stop_event = asyncio.Event()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, stop_event.set)  # Windows dev env lacks this; Docker/Linux prod supports it.

    logger.info("extractor_starting", poll_interval=settings.extractor.EXTRACTOR_POLL_INTERVAL)
    try:
        while not stop_event.is_set():
            async with container() as request_container:
                extraction_service = await request_container.get(ExtractionService)
                result = await extraction_service.process_pending()
            if result["claimed"]:
                logger.info("extractor_tick", **result)
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(
                    stop_event.wait(), timeout=settings.extractor.EXTRACTOR_POLL_INTERVAL
                )
    finally:
        logger.info("extractor_stopping")
        await container.close()


if __name__ == "__main__":
    asyncio.run(main())
