import os
from flask import url_for, current_app

def get_photo_url(photo_path):
    """
    Retourne l'URL publique d'une photo si elle existe,
    sinon retourne None
    """
    if not photo_path:
        return None

    full_path = os.path.join(
        current_app.static_folder,
        "uploads",
        photo_path
    )

    if os.path.exists(full_path):
        return url_for("static", filename=f"uploads/{photo_path}")

    return None
