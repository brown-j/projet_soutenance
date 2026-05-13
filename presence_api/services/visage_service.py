from database.db import get_connection
import json
import numpy as np
import os

from flask import current_app
from services.encodage_service import get_encode
from services.storage_service import delete_file, save_file

def load_all_encodings():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT employe_id, encodage
        FROM visages
    """)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    encodings = []
    employe_ids = []

    for row in rows:
        enc = json.loads(row["encodage"])
        encodings.append(np.array(enc))
        employe_ids.append(row["employe_id"])

    return encodings, employe_ids


def upsert_visage(employe_id, type_vue, file_obj, isInsertion=None):
    """
    Orchestre la mise à jour BDD et Disque avec nettoyage des anciens fichiers.
    """
    # 1. Validation de l'entrée
    if not file_obj or not file_obj.filename:
        print("❌ Erreur : Fichier invalide")
        return False
    
    # 2. Encodage IA
    # Note: Assure-toi que get_encode gère le seek(0) ou rembobine après
    encodage = get_encode(file_obj) 
    
    if encodage is None: # Attention: "if not encodage" peut être faux si c'est un array vide
        print("❌ Erreur : Aucun visage détecté")
        return False
        
    # Sécurisation pour JSON : Conversion Numpy Array -> Liste Python
    if isinstance(encodage, np.ndarray):
        encodage = encodage.tolist()
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 3. Préparation des noms
    # Récupère l'extension réelle du fichier envoyé (ex: .png)
    extension = os.path.splitext(file_obj.filename)[1].lower()
    final_filename = f"EMP_{employe_id}_{type_vue}{extension}"
    
    # Chemin relatif pour nos fonctions utilitaires
    relative_path_new = os.path.join('photos', final_filename)

    try:
        # 4. Vérification de l'état actuel en BDD
        cursor.execute(
            "SELECT id, chemin_image FROM visages WHERE employe_id = %s AND type_vue = %s",
            (employe_id, type_vue)
        )
        record = cursor.fetchone()
        exists_in_db = record is not None

        # 5. Logique de décision (Insert vs Update)
        action = "INSERT"
        if isInsertion is True:
            if exists_in_db:
                raise Exception(f"Doublon : Employé {employe_id} vue {type_vue} existe déjà.")
            action = "INSERT"
        elif isInsertion is False:
            if not exists_in_db:
                raise Exception(f"Introuvable : Impossible de mettre à jour l'employé {employe_id}.")
            action = "UPDATE"
        else:
            action = "UPDATE" if exists_in_db else "INSERT"

        # 6. Exécution SQL + Gestion du nettoyage (Orphelins)
        if action == "UPDATE":
            # --- NETTOYAGE CRITIQUE ---
            # Si le nom de fichier change (ex: changement d'extension .jpg -> .png)
            # On doit supprimer l'ancien fichier physique pour ne pas polluer le disque
            if record['chemin_image'] and record['chemin_image'] != final_filename:
                old_relative_path = os.path.join('photos', record['chemin_image'])
                delete_file(old_relative_path) # On supprime l'ancien

            query = "UPDATE visages SET chemin_image = %s, encodage = %s WHERE employe_id = %s AND type_vue = %s"
            params = (final_filename, json.dumps(encodage), employe_id, type_vue)
        else:
            query = "INSERT INTO visages (employe_id, type_vue, chemin_image, encodage) VALUES (%s, %s, %s, %s)"
            params = (employe_id, type_vue, final_filename, json.dumps(encodage))

        cursor.execute(query, params)

        # 7. Sauvegarde Physique (Disque)
        # On passe le chemin RELATIF ('photos/EMP_X.jpg') à notre fonction robuste
        if not save_file(file_obj, relative_path_new):
            raise Exception("Impossible d'écrire le fichier sur le disque.")

        # 8. Validation finale
        conn.commit()
        print(f"✅ {action} terminé : {final_filename}")
        return True

    except Exception as e:
        conn.rollback()
        print(f"❌ Erreur Upsert (Rollback effectué) : {e}")
        # Optionnel : Si on a créé le fichier mais que le SQL a planté, on pourrait le supprimer ici
        return False

    finally:
        cursor.close()
        conn.close()