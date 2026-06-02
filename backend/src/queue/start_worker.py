import asyncio
from arq import run_worker
from arq.connections import RedisSettings
from src.queue.worker import WorkerSettings
from src.config import settings


async def main():
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    await run_worker(WorkerSettings, redis_settings=redis_settings)


if __name__ == "__main__":
    asyncio.run(main())
