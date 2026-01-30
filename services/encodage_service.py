import face_recognition
import json
import numpy as np

def get_encode(file_stream):
    """
    Génère l'encodage depuis un flux de fichier (mémoire)
    """
    try:
        # On charge l'image directement depuis le flux du formulaire
        image = face_recognition.load_image_file(file_stream)
        encodages = face_recognition.face_encodings(image)

        if len(encodages) > 0:
            # On retourne le premier visage trouvé sous forme de JSON
            return json.dumps(encodages[0].tolist())
        return None
    except Exception as e:
        print(f"Erreur encodage IA : {e}")
        return None