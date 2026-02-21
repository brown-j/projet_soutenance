# celery_worker.py
from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration Celery avec Redis comme Broker
app = Celery('presence_worker',
             broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
             backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'))


app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Paris',
    enable_utc=True,
    task_track_started=True,
)

# Importer les tasks APRÈS l'initialisation de app (éviter circular import)
import workers.tasks

