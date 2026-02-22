# celery_worker.py
from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()


# Récupère l'URL Redis de Render, ou utilise localhost par défaut pour tes tests locaux
redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')

app = Celery('tasks', 
             broker=redis_url, 
             backend=redis_url)

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

