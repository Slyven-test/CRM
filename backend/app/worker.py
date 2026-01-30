from celery import Celery

from app.settings import settings

celery_app = Celery(
    "ia_crm_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
)


@celery_app.task(name="tasks.ping")
def ping() -> str:
    return "pong"

