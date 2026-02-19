# workers/tasks.py
import cv2
from celery_worker import app
import face_recognition
import numpy as np
from services.presence_service import log_attendance # À créer
import os

# Cache global en RAM pour le Worker
KNOWN_ENCODINGS = []
KNOWN_IDS = []

@app.task
def load_signatures_to_ram():
    """Charge les signatures SQL vers la RAM du worker"""
    global KNOWN_ENCODINGS, KNOWN_IDS
    # Ici tu appelleras ton service SQL
    # signatures = get_all_signatures()
    # KNOWN_ENCODINGS = [np.array(s['vector']) for s in signatures]
    # KNOWN_IDS = [s['employe_id'] for s in signatures]
    print("🚀 RAM updated with employee signatures")

@app.task(name="process_recognition_task")
def process_recognition_task(image_path):
    """Traitement de l'image et reconnaissance"""
    if not os.path.exists(image_path):
        return "File not found"

    # 1. Chargement et Encodage
    image = face_recognition.load_image_file(image_path)
    face_encodings = face_recognition.face_encodings(image)

    for unknown_encoding in face_encodings:
        # 2. Comparaison NumPy
        matches = face_recognition.compare_faces(KNOWN_ENCODINGS, unknown_encoding, tolerance=0.6)
        
        if True in matches:
            first_match_index = matches.index(True)
            emp_id = KNOWN_IDS[first_match_index]
            
            # 3. Enregistrement en DB
            log_attendance(emp_id)
            print(f"✅ Match found: Employee ID {emp_id}")

    latest_path = os.path.join(os.path.dirname(image_path), "latest.jpg")
    
    # On peut même dessiner ici si on veut (optionnel pour l'instant)
    img = cv2.imread(image_path)
    cv2.imwrite(latest_path, img) # Sauvegarde pour le stream
    
    if os.path.exists(image_path):
        os.remove(image_path)


