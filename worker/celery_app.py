from celery import Celery
from config import CELERY_CONFIG

celery_app = Celery("presence_worker")
celery_app.conf.update(CELERY_CONFIG)
