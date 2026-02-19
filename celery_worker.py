# celery_worker.py
from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration Celery avec Redis comme Broker
app = Celery('presence_worker',
             broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
             backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'))

# On importe les tâches depuis le dossier workers
import workers.tasks