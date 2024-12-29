from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "worker",
    backend=settings.CELERY_RESULT_BACKEND,
    broker=settings.CELERY_BROKER_URL
)

celery_app.conf.task_routes = {
    "app.worker.*": {"queue": "main-queue"}
} 