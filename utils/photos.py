import os
from flask import url_for, current_app

def get_photo_url(photo_path):
    """
    Retourne l'URL publique d'une photo si elle existe,
    sinon retourne None
    """
    if not photo_path:
        return None


    return url_for('static', filename=os.path.join('uploads/photos', photo_path))
