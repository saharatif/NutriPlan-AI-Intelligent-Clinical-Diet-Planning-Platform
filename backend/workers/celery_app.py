from celery import Celery

from utils.config import settings

celery_app = Celery(
    "nutriplan",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
)

celery_app.conf.update(
    include=[
        "workers.task_ocr",
        "workers.task_medical_profile",
        "workers.task_diet_plan",
    ]
)
