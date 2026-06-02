from arq import run_worker
from arq.connections import RedisSettings
from src.queue.worker import WorkerSettings
from src.config import settings


if __name__ == "__main__":
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    run_worker(WorkerSettings, redis_settings=redis_settings)
