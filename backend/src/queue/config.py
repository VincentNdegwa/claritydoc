from arq import create_pool
from arq.connections import RedisSettings
from loguru import logger
from src.config import settings


async def get_redis_pool():
    return await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))


async def enqueue_job(function_name: str, **kwargs):
    redis = await get_redis_pool()
    try:
        job = await redis.enqueue_job(function_name, **kwargs)
        logger.info(f"Enqueued job {function_name} with ID: {job.job_id}")
        return job.job_id
    finally:
        await redis.close()
