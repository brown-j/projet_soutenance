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
    
# ============================================================================
# CELERY TASK - Tâche principale
# ============================================================================

@app.task(name="process_recognition_task")
def process_recognition_task(image_path):
    """
    Tâche Celery principale : traitement de l'image et reconnaissance faciale.
    
    Flux:
    1. Vérifier que l'image existe
    2. Charger les encodages connus depuis la DB
    3. Détecter les visages dans l'image
    4. Comparer avec les encodages connus
    5. Dessiner les rectangles et labels
    6. Sauvegarder l'image traitée (latest.jpg pour synchronisation vidéo)
    7. Enregistrer les présences en DB
    
    Args:
        image_path: Chemin vers l'image à traiter
    
    Returns:
        str: Message de statut du traitement
    """
    
    # === ÉTAPE 1: Vérification ===
    if not os.path.exists(image_path):
        print(f"❌ Erreur : Le fichier {image_path} n'existe pas.")
        return "File not found"

    try:
        # === ÉTAPE 2: Charger les encodages connus ===
        known_encodings, known_ids = load_known_encodings_from_db()
        
        # === ÉTAPE 3: Lire et préparer l'image ===
        img_cv2 = cv2.imread(image_path)
        if img_cv2 is None:
            print(f"❌ Erreur : Impossible de lire l'image {image_path}")
            return "Image reading failed"
        
        rgb_img = cv2.cvtColor(img_cv2, cv2.COLOR_BGR2RGB)
        
        # === ÉTAPE 4: Détecter les visages ===
        face_locations = face_recognition.face_locations(rgb_img)
        face_encodings = face_recognition.face_encodings(rgb_img, face_locations)
        
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
        
        # === ÉTAPE 7: Sauvegarde atomique (synchronisation vidéo) ===
        base_dir = os.path.dirname(os.path.abspath(image_path))
        save_processed_image_atomically(img_cv2, base_dir)
        
        # === ÉTAPE 8: Enregistrement en base de données ===
        log_multiple_attendances(recognized_employees)
        
        return f"Processed: {len(recognized_employees)} employee(s) recognized"

    except Exception as e:
        print(f"❌ Erreur lors de la tâche Celery : {e}")
        return f"Error: {str(e)}"
    
    finally:
        # Nettoyage : processing.jpg se réécrit automatiquement, pas besoin de le supprimer
        pass
