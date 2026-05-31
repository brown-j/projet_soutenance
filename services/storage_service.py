import os
import shutil
from pathlib import Path
from flask import current_app

# On suppose que UPLOAD_FOLDER est défini dans ta config Flask
# Sinon, importe-le depuis tes constantes

def save_file(file_obj, relative_path):
    """
    Sauvegarde un fichier de manière robuste.
    :param relative_path: ex: 'photos/EMP_1_face.jpg'
    """
    try:
        base_folder = Path(current_app.config['UPLOAD_FOLDER'])
        full_path = base_folder / relative_path
        
        # Création récursive des dossiers parents si inexistants
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Réinitialiser le curseur de lecture (CRUCIAL)
        file_obj.seek(0)
        
        # Sauvegarde (Compatible Windows/Linux)
        file_obj.save(str(full_path))
        
        print(f"✓ Fichier sauvegardé : {full_path.name}")
        return True
    except Exception as e:
        print(f"✗ Erreur critique écriture disque : {e}")
        return False

def delete_file(relative_path):
    """
    Supprime un fichier proprement.
    :param relative_path: ex: 'photos/EMP_1_face.jpg'
    """
    if not relative_path:
        return

    try:
        base_folder = Path(current_app.config['UPLOAD_FOLDER'])
        full_path = base_folder / relative_path

        if full_path.exists() and full_path.is_file():
            os.remove(full_path)
            print(f"🗑️ Fichier supprimé : {full_path.name}")
        else:
            print(f"⚠️ Fichier introuvable (déjà supprimé ?) : {relative_path}")
            
    except Exception as e:
        print(f"✗ Erreur suppression disque : {e}")