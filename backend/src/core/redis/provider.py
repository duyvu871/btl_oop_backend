from redis.asyncio import from_url

from src.settings.env import settings


async def get_redis():
    redis = await from_url(settings.REDIS_URL, decode_responses=False)
    try:
        yield redis
    finally:
        await redis.close()
