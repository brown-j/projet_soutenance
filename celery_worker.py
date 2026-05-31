from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

# Utilise 6373 pour correspondre à ton terminal local
redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6373')

app = Celery('tasks', 
             broker=redis_url, 
             backend=redis_url,
             include=['workers.tasks']) # On inclut les tâches ici directement

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Africa/Douala', # Adapté à ton fuseau horaire (Cameroun)
    enable_utc=True,
    task_track_started=True,
)