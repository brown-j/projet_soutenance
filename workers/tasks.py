# workers/tasks.py
"""
Module de traitement des tâches Celery pour la reconnaissance faciale.
Gère la détection des visages, la reconnaissance et l'enregistrement des présences.
"""

import os
import cv2
import json
import numpy as np
import face_recognition
from datetime import datetime
from celery_worker import app
from database.db import get_connection
import base64
import redis

from socket_service import broadcast_processed_frame

# ============================================================================
# HELPERS - Fonctions utilitaires
# ============================================================================

def load_known_encodings_from_db():
    """
    Charge les encodages connus depuis la base de données.
    
    Returns:
        tuple: (known_encodings, known_ids) - Lists of numpy arrays and employee IDs
    """
    conn = get_connection()
    if not conn:
        print("❌ Erreur : Impossible de se connecter à la base de données.")
        return [], []

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT employe_id, encodage FROM visages")
        rows = cursor.fetchall()
        
        known_encodings = []
        known_ids = []
        
        for row in rows:
            try:
                raw_data = row['encodage']
                
                # Nettoyer les espaces blancs et guillemets superflus
                clean_data = raw_data.strip().strip('"').strip("'")
                
                # Conversion en liste Python
                encoding_list = json.loads(clean_data)
                
                # Conversion en numpy array
                encoding_np = np.array(encoding_list, dtype=np.float64)
                
                if encoding_np.size == 128:
                    known_encodings.append(encoding_np)
                    known_ids.append(row['employe_id'])
                else:
                    print(f"⚠️ Taille incorrecte ({encoding_np.size}) pour ID {row['employe_id']}")
            
            except Exception as e:
                print(f"❌ Erreur de formatage pour l'employé {row.get('employe_id')}: {e}")
        
        print(f"📊 {len(known_encodings)} encodages chargés depuis la DB")
        return known_encodings, known_ids

    except Exception as e:
        print(f"❌ Erreur lors du chargement des encodages: {e}")
        return [], []
    
    finally:
        cursor.close()
        conn.close()


def draw_label_on_image(img, left, top, right, bottom, label):
    """
    Dessine le rectangle et le texte sur l'image.
    L'image est modifiée en place pour la synchronisation vidéo.
    
    Args:
        img: Image OpenCV (BGR)
        left, top, right, bottom: Coordonnées du visage
        label: Texte à afficher
    """
    # Rectangle autour du visage (vert)
    cv2.rectangle(img, (left, top), (right, bottom), (0, 255, 0), 2)
    
    # Bandeau pour le texte
    cv2.rectangle(img, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
    
    # Texte avec le label
    font = cv2.FONT_HERSHEY_DUPLEX
    cv2.putText(img, label, (left + 6, bottom - 6), font, 0.8, (255, 255, 255), 1)
    
    # affichage du cache a l'image
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img, f"Cache: {len(last_seen_cache)}", (10, 30), font, 0.7, (0, 255, 255), 2)

def log_attendance(employe_id):
    """
    Enregistre un passage dans la table 'pointages'.
    Gère l'anti-spam (1 min) et définit le type d'action (ENTREE ou PASSAGE).
    """
    now = datetime.now()
    
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True) # dictionary=True pour faciliter la lecture

        # 1. On cherche le dernier passage de cet employé AUJOURD'HUI
        query_check = """
            SELECT timestamp, type_action 
            FROM pointages 
            WHERE employe_id = %s AND DATE(timestamp) = CURDATE() 
            ORDER BY timestamp DESC LIMIT 1
        """
        cursor.execute(query_check, (employe_id,))
        last_pointage = cursor.fetchone()

        action = "ENTREE" # Par défaut, si c'est le premier de la journée
        
        if last_pointage:
            # Calcul de l'écart entre maintenant et le dernier passage
            derniere_vue = last_pointage['timestamp']
            diff = now - derniere_vue

            # --- ANTI-SPAM ---
            # Si on l'a vu il y a moins de 60 secondes, on n'enregistre rien
            if diff.total_seconds() < 60:
                print(f"⏳ Scan ignoré pour {employe_id} (Trop récent)")
                return True 

            # Si on l'a déjà vu aujourd'hui, le type devient "PASSAGE"
            action = "PASSAGE"

        # 2. Insertion du nouveau pointage
        query_insert = """
            INSERT INTO pointages (employe_id, timestamp, type_action)
            VALUES (%s, %s, %s)
        """
        # On laisse MySQL gérer le timestamp ou on l'envoie manuellement
        cursor.execute(query_insert, (employe_id, now, action))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ [{action}] Enregistré pour l'ID {employe_id} à {now.strftime('%H:%M:%S')}")
        return True

    except Exception as e:
        print(f"❌ Erreur SQL pointages : {e}")
        return False

def save_processed_image_atomically(img_cv2, base_dir):
    """
    Sauvegarde l'image de manière atomique en latest.jpg.
    
    Args:
        img_cv2: Image OpenCV (BGR)
        base_dir: Répertoire de destination
    """
    latest_path = os.path.join(base_dir, "latest.jpg")
    temp_latest_path = os.path.join(base_dir, "latest_temp.jpg")
    
    try:
        cv2.imwrite(temp_latest_path, img_cv2)
        os.replace(temp_latest_path, latest_path)
        print(f"✅ latest.jpg sauvegardée")
    except Exception as e:
        print(f"⚠️ Erreur renommage: {e}")
        cv2.imwrite(latest_path, img_cv2)

# Cache global (Set pour la rapidité des opérations mathématiques d'ensemble)
# Il contient les IDs des employés actuellement visibles à l'image précédente
last_seen_cache = set()

def log_multiple_attendances(new_detected_ids):
    """
    Optimisation par soustraction d'ensembles :
    - Détecte qui vient d'arriver (new - last) -> Logique d'enregistrement
    - Détecte qui vient de partir (last - new) -> Optionnel : Logique de sortie
    - Met à jour le cache global
    """
    
    global last_seen_cache
    
    # Conversion de la liste reçue en Set pour des opérations ultra-rapides
    current_ids = set(new_detected_ids)
    
    # 1. ANALYSE : Qui vient d'entrer dans le champ de la caméra ?
    to_log_in = current_ids - last_seen_cache

    # ENREGISTREMENT DES ENTRÉES/MOUVEMENTS
    if to_log_in:
        print(f"--- Nouveaux mouvements détectés : {len(to_log_in)} ---")
        for emp_id in to_log_in:
            resultat = log_attendance(emp_id)
            if resultat:
                print(f"✅ Enregistré : id={emp_id}")
            else:
                print(f"❌ Échec SQL : id={emp_id}")

    # 3. MISE À JOUR DU CACHE : Le nouveau cache devient les IDs actuels
    last_seen_cache = current_ids
    
    
# --- Variables Globales (Cache) ---
KNOWN_ENCODINGS = None
KNOWN_IDS = None

def get_known_faces():
    """
    Récupère les encodages depuis la RAM si possible, 
    sinon charge depuis la DB.
    """
    global KNOWN_ENCODINGS, KNOWN_IDS
    
    if KNOWN_ENCODINGS is None or KNOWN_IDS is None:
        print("🔍 Cache vide : Chargement des encodages depuis la base de données...")
        KNOWN_ENCODINGS, KNOWN_IDS = load_known_encodings_from_db()
        print(f"✅ {len(KNOWN_IDS)} visages chargés en mémoire.")
    
    return KNOWN_ENCODINGS, KNOWN_IDS

def refresh_known_faces():
    """ Force le rechargement (à appeler après un ajout d'employé) """
    global KNOWN_ENCODINGS, KNOWN_IDS
    KNOWN_ENCODINGS = None
    KNOWN_IDS = None
    
# ============================================================================
# CELERY TASK - Tâche principale
# ============================================================================

# Connexion Redis
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6373')
r = redis.from_url(REDIS_URL)

# Chargement initial des encodages, a chaque ajoute d'employé, il faudra: 
# actualiser le cache (recharger les encodages) pour que le worker puisse les utiliser sans redémarrage
known_encodings, known_ids = load_known_encodings_from_db()

@app.task(name="process_recognition_task")
def process_recognition_task():
    """
    Tâche Celery adaptée : 
    Lit l'image depuis Redis au lieu du disque dur.
    """
    print("🚀 Tâche Celery démarrée : Traitement de la frame en cours...")
    
    try:
        # Au début de process_recognition_task :
        if r.get("refresh_cache_flag"):
            refresh_known_faces()
            r.delete("refresh_cache_flag") # On consomme le signal
    
        # === ÉTAPE 0 : Accès Cache (Optimisé) ===
        known_encodings, known_ids = get_known_faces()
        
        if not known_encodings:
            # On libère le verrou avant de quitter
            r.delete('is_processing')
            return "Base de données d'encodages vide"
        
        # === ÉTAPE 1: Récupérer l'image depuis Redis ===
        image_base64 = r.get('live_frame')
        if not image_base64:
            return "No frame in Redis"

        # === ÉTAPE 2: Décoder l'image Base64 en format OpenCV ===
        img_data = base64.b64decode(image_base64)
        nparr = np.frombuffer(img_data, np.uint8)
        img_cv2 = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img_cv2 is None:
            return "Image decoding failed"
        
        # 1. Amélioration instantanée du contraste (CLAHE)
        lab = cv2.cvtColor(img_cv2, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        cl = clahe.apply(l)
        limg = cv2.merge((cl,a,b));enhanced_img = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

        # 2. Conversion finale pour l'IA
        rgb_img = cv2.cvtColor(enhanced_img, cv2.COLOR_BGR2RGB)

        # === ÉTAPE 3: Détection ===#
        face_locations = face_recognition.face_locations(rgb_img)
        face_encodings = face_recognition.face_encodings(img_cv2, face_locations)
        
        recognized_employees = []
        
        # === ÉTAPE 5: Comparaison et reconnaissance ===
        for (top, right, bottom, left), face_to_check in zip(face_locations, face_encodings):
            label = "Inconnu"
            emp_id = None
            
            if len(known_encodings) > 0:
                # Comparaison avec tolérance 0.5
                matches = face_recognition.compare_faces(
                    known_encodings, 
                    face_to_check, 
                    tolerance=0.5
                )
                
                if True in matches:
                    first_match_index = matches.index(True)
                    emp_id = known_ids[first_match_index]
                    label = f"Employe ID: {emp_id}"
                    recognized_employees.append(emp_id)
                    print(f"✅ Match found: Employee ID {emp_id}")
                    
            # === ÉTAPE 6: Dessiner sur l'image ===
            draw_label_on_image(img_cv2, left, top, right, bottom, label)
            
        # === ÉTAPE 7: Sauvegarder la frame TRAITÉE dans Redis ===
        # Au lieu d'un fichier 'latest.jpg', on remet l'image dessinée dans Redis 
        # pour que le dashboard affiche les carrés verts en temps réel.
        _, buffer = cv2.imencode('.jpg', img_cv2)
        processed_base64 = base64.b64encode(buffer).decode('utf-8')
        r.set('processed_frame', processed_base64)
        
        # Publier l'image traitée sur le canal Redis pub/sub
        # Le serveur Flask écoute ce canal et émet via SocketIO au frontend
        r.set('processed_frames', processed_base64)
        print("✅ Frame traitée sauvegardée dans Redis")
        
        # === ÉTAPE 8: Enregistrement en DB ===
        if recognized_employees:
            log_multiple_attendances(recognized_employees)
            return f"Match(es) found: {recognized_employees}"
            
        return "No match found"

    except Exception as e: 
        print(f"❌ Erreur Celery : {e}")
        return str(e)
    
    finally:
        # Libérer le verrou de traitement à la fin de la tâche, même en cas d'erreur
        r.delete('is_processing')