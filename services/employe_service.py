from flask import current_app
from database.db import get_connection
import os
from werkzeug.utils import secure_filename
from services.storage_service import delete_file


def create_employe(matricule, nom, prenom, poste):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO employes (matricule, nom, prenom, poste)
        VALUES (%s, %s, %s, %s)
        """,
        (matricule, nom, prenom, poste)
    )

    conn.commit()
    cursor.close()
    conn.close()


def get_employe_by_id(employe_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT 
            e.id, e.matricule, e.nom, e.prenom, e.poste, e.created_at,
            JSON_ARRAYAGG(
                JSON_OBJECT(
                    'id', v.id, 'type_vue', v.type_vue, 'chemin_image', v.chemin_image, 'created_at', v.created_at
                )
            ) AS photos
        FROM employes e
        LEFT JOIN visages v ON e.id = v.employe_id
        WHERE e.id = %s
        GROUP BY e.id, e.matricule, e.nom, e.prenom, e.poste, e.created_at
    """
    
    try:
        cursor.execute(query, (employe_id,))
        employe = cursor.fetchone()
        
        if employe and employe['photos']:
            # Convertir la chaîne JSON en liste Python
            import json
            employe['photos'] = json.loads(employe['photos'])
        
        return employe
    except Exception as e:
        print(f"✗ Erreur lors de la récupération : {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def format_employe_photos(employe):
    """
    Convertit la liste des photos d'un employé en dictionnaire indexé par type_vue
    Avant : [{'type_vue': 'face', 'chemin_image': 'path1'}, ...]
    Après : {'face': 'path1', 'profil_droit': 'path2', 'profil_gauche': 'path3'}
    """
    if not employe:
        return None

    photos_dict = {
        "face": None,
        "profil_droit": None,
        "profil_gauche": None
    }
    
    for photo in employe['photos']:
        type_vue = photo.get('type_vue')
        chemin = photo.get('chemin_image')
        
        if type_vue in photos_dict and chemin:
            photos_dict[type_vue] = chemin
    
    employe['photos'] = photos_dict
    return employe


def get_all_employes():
    """Récupère tous les employés avec leurs photos"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT 
            e.id, e.matricule, e.nom, e.prenom, e.poste, e.created_at,
            JSON_ARRAYAGG(
                JSON_OBJECT(
                    'type_vue', v.type_vue, 
                    'chemin_image', v.chemin_image
                )
            ) AS photos
        FROM employes e
        LEFT JOIN visages v ON e.id = v.employe_id
        GROUP BY e.id
        ORDER BY e.created_at DESC
    """
    
    try:
        cursor.execute(query)
        employes_list = cursor.fetchall()
        
        import json
        for employe in employes_list:
            if employe['photos']:
                employe['photos'] = json.loads(employe['photos'])

                # Convertir en dictionnaire par type_vue
                employe = format_employe_photos(employe)

        return employes_list
    except Exception as e:
        print(f"✗ Erreur lors de la récupération : {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def delete_employe(employe_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Récupérer l'employé avec toutes ses photos
        employe = get_employe_by_id(employe_id)
        
        if not employe:
            print(f"✗ Employé {employe_id} introuvable")
            return False
        

        # Supprimer toutes les photos de visage (visages table)
        if employe.get('photos'):
            for photo in employe['photos']:
                if photo.get('chemin_image'):
                    delete_file(photo['chemin_image'])
                    print(f"✓ Photo visage supprimée : {photo['chemin_image']}")
        
        # Supprimer l'employé de la base de données
        cursor.execute(
            "DELETE FROM employes WHERE id = %s",
            (employe_id,)
        )
        
        conn.commit()
        print(f"✓ Employé {employe_id} supprimé de la BD")
        return True
        
    except Exception as e:
        print(f"✗ Erreur lors de la suppression : {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

