import os
import cv2
import json
import numpy as np
import face_recognition
from celery_worker import app
from database.db import get_connection

@app.task(name="process_recognition_task")
def process_recognition_task(image_path):
    # 1. Initialisation de la connexion
    conn = get_connection()
    if not conn:
        print("Erreur : Impossible de se connecter à la base de données.")
        return

    try:
        cursor = conn.cursor(dictionary=True)

        # 2. Charger les visages connus depuis la DB
        cursor.execute("SELECT employe_id, encodage FROM visages")
        rows = cursor.fetchall()
        
        known_encodings = []
        known_ids = []
        
        for row in rows:
            try:
                raw_data = row['encodage']
            
                # 1 On retire les espaces blancs et les guillemets superflus (au cas où la DB ait stocké '"[...]"')
                clean_data = raw_data.strip().strip('"').strip("'")

                # 2. Conversion en liste Python
                encoding_list = json.loads(clean_data)

                # 3. Conversion en numpy array
                encoding_np = np.array(encoding_list, dtype=np.float64)
        
                if encoding_np.size == 128:
                    known_encodings.append(encoding_np)
                    known_ids.append(row['employe_id'])
                else:
                    print(f"⚠️ Taille incorrecte ({encoding_np.size}) pour ID {row['employe_id']}")

            except Exception as e:
                print(f"❌ Erreur de formatage pour l'employé {row.get('employe_id')}: {e}")


        # 3. Traitement de l'image reçue de la caméra
        if not os.path.exists(image_path):
            print(f"Erreur : Le fichier {image_path} n'existe pas.")
            return

        img_cv2 = cv2.imread(image_path)
        if img_cv2 is None:
            return
            
        rgb_img = cv2.cvtColor(img_cv2, cv2.COLOR_BGR2RGB)
        
        # Détection des visages sur l'image actuelle
        face_locations = face_recognition.face_locations(rgb_img)
        face_encodings = face_recognition.face_encodings(rgb_img, face_locations)

        label = "Inconnu"

        # 4. Comparaison des visages détectés
        for (top, right, bottom, left), face_to_check in zip(face_locations, face_encodings):
            if len(known_encodings) > 0:
                # Comparaison (tolérance 0.5 pour être plus strict, 0.6 par défaut)
                matches = face_recognition.compare_faces(known_encodings, face_to_check, tolerance=0.5)
                
                if True in matches:
                    first_match_index = matches.index(True)
                    emp_id = known_ids[first_match_index]
                    label = f"Employe ID: {emp_id}"
                    
                    # Optionnel : Enregistrer la présence en base ici
                    # cursor.execute("INSERT INTO presences (employe_id) VALUES (%s)", (emp_id,))
                    # conn.commit()
                
            # Dessiner le rectangle et le label sur l'image
            draw_label(image_path, left, top, right, bottom, label)

    except Exception as e:
        print(f"Erreur lors de la tâche Celery : {e}")
    finally:
        cursor.close()
        conn.close()


def draw_label(image_path, left, top, right, bottom, label):
    """Dessine le rectangle et le texte, puis sauvegarde dans latest.jpg"""
    img = cv2.imread(image_path)
    if img is None:
        return

    # 1. Rectangle autour du visage
    cv2.rectangle(img, (left, top), (right, bottom), (0, 255, 0), 2)

    # 2. Bandeau pour le texte
    cv2.rectangle(img, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
    
    # 3. Texte
    font = cv2.FONT_HERSHEY_DUPLEX
    cv2.putText(img, label, (left + 6, bottom - 6), font, 0.8, (255, 255, 255), 1)

    # 4. Sauvegarde pour l'affichage (Latest)
    # On remonte d'un dossier pour aller dans le dossier parent (racine du projet ou temp_frames)
    base_dir = os.path.dirname(os.path.abspath(image_path))
    latest_path = os.path.join(base_dir, "latest.jpg")
    
    cv2.imwrite(latest_path, img)