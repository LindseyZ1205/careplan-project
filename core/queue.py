"""Push care plan job ids to Redis (producer side only; no worker here)."""

from django.conf import settings

import redis


def enqueue_careplan_id(careplan_id: int) -> None:
    if not getattr(settings, "REDIS_HOST", ""):
        return
    client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        socket_connect_timeout=5,
        decode_responses=True,
    )
    client.rpush(settings.CAREPLAN_REDIS_QUEUE_KEY, str(careplan_id))
