from database.db import get_connection
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def create_employe(matricule, nom, prenom, poste, photo_reference):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO employes (matricule, nom, prenom, poste, photo_reference)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (matricule, nom, prenom, poste, photo_reference)
    )

    conn.commit()
    employe_id = cursor.lastrowid
    cursor.close()
    conn.close()

    return employe_id


def get_all_employes():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM employes")
    employes = cursor.fetchall()

    cursor.close()
    conn.close()

    return employes


def get_employe_by_id(employe_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM employes WHERE id = %s",
        (employe_id,)
    )
    employe = cursor.fetchone()

    cursor.close()
    conn.close()

    return employe


def update_employe(id, matricule=None, nom=None, prenom=None, poste=None, photo_reference=None):
    conn = get_connection()
    cursor = conn.cursor()

    fields = []
    values = []

    if matricule is not None:
        fields.append("matricule = %s")
        values.append(matricule)

    if nom is not None:
        fields.append("nom = %s")
        values.append(nom)

    if prenom is not None:
        fields.append("prenom = %s")
        values.append(prenom)

    if poste is not None:
        fields.append("poste = %s")
        values.append(poste)

    if photo_reference is not None:
        fields.append("photo_reference = %s")
        values.append(photo_reference)

    # Sécurité : rien à mettre à jour
    if not fields:
        cursor.close()
        conn.close()
        return

    query = f"""
        UPDATE employes
        SET {', '.join(fields)}
        WHERE id = %s
    """

    values.append(id)

    cursor.execute(query, tuple(values))
    conn.commit()

    cursor.close()
    conn.close()



def delete_employe(employe_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM employes WHERE id = %s",
        (employe_id,)
    )

    conn.commit()
    cursor.close()
    conn.close()


#supprimer la photo associée si elle existe
def delete_employe_photo(photo_reference):
    if photo_reference:
        photo_path = os.path.join(UPLOAD_FOLDER, photo_reference)
        if os.path.exists(photo_path):
            os.remove(photo_path)


#fonction pour sauvegarder la photo de l'employé
def save_employe_photo(photo, id):
    if photo and photo.filename != "":
        # Récupérer l'extension du fichier
        file_ext = os.path.splitext(photo.filename)[1]
        filename = f"photo_{id}{file_ext}"
        
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        photo_path = os.path.join(UPLOAD_FOLDER, filename)
        photo.save(photo_path)
        return filename
    return None