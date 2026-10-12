import asyncio
import contextlib
import signal
from pathlib import Path

from pyrogram import Client

from app.backend_client import BackendClient
from app.config import get_settings
from app.logging import configure_logging, get_logger
from app.sync_runner import SyncRunner

logger = get_logger("userbot.main")


async def main() -> None:
    settings = get_settings()
    configure_logging(settings.LOG_LEVEL)

    client = Client(
        "userbot",
        api_id=settings.USERBOT_API_ID,
        api_hash=settings.USERBOT_API_HASH,
        session_string=settings.USERBOT_SESSION,
        ipv6=settings.USERBOT_IPV6,
        in_memory=True,
    )
    backend = BackendClient(settings)
    stop_event = asyncio.Event()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, stop_event.set)  # Windows dev env lacks this; Docker/Linux prod supports it.

    await client.start()
    # Client is constructed with in_memory=True, so Pyrogram's peer/access_hash
    # cache starts empty on every process start regardless of what this
    # account resolved in any previous run. Resolving the sync channel by raw
    # numeric id before the cache is warmed fails with "Peer id invalid" even
    # when the account is a genuine member. Enumerating dialogs once primes
    # the cache for every chat the account currently sees, channel included.
    async for _ in client.get_dialogs():
        pass
    logger.info("userbot_starting", poll_interval=settings.USERBOT_POLL_INTERVAL)
    try:
        while not stop_event.is_set():
            job = await backend.claim_job()
            if job is not None:
                channel_id = await backend.get_channel_id()
                runner = SyncRunner(
                    client=client,
                    backend=backend,
                    channel_id=channel_id,
                    media_root=Path(settings.MEDIA_ROOT),
                    batch_size=settings.USERBOT_BATCH_SIZE,
                )
                logger.info("sync_pass_starting", cursor=job.cursor, stop_id=job.stop_id)
                await runner.run_pass(job)
                logger.info("sync_pass_finished")

            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(
                    stop_event.wait(), timeout=settings.USERBOT_POLL_INTERVAL
                )
    finally:
        logger.info("userbot_stopping")
        await client.stop()
        await backend.close()


if __name__ == "__main__":
    asyncio.run(main())
