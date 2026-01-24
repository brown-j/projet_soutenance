from worker.celery_app import celery_app
from services.visage_service import load_all_encodings

# CACHE RAM (GLOBAL AU WORKER)
KNOWN_ENCODINGS = []
KNOWN_EMPLOYE_IDS = []


@celery_app.task
def charger_donnees_initiales():
    global KNOWN_ENCODINGS, KNOWN_EMPLOYE_IDS

    KNOWN_ENCODINGS, KNOWN_EMPLOYE_IDS = load_all_encodings()

    print(f"[Worker] {len(KNOWN_ENCODINGS)} visages chargés en RAM")
