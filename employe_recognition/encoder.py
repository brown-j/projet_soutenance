import face_recognition
import numpy as np
import os


def encode_face(image_path):
    # Convertir en chemin absolu si nécessaire
    if not os.path.isabs(image_path):
        image_path = os.path.join(os.path.dirname(__file__), "..", image_path)
    
    if not os.path.exists(image_path):
        print(f"✗ Fichier non trouvé : {image_path}")
        return None
    
    image = face_recognition.load_image_file(image_path)
    encodings = face_recognition.face_encodings(image)

    if len(encodings) == 0:
        return None

    return encodings[0].tolist()


def face_encoding_test():
    # Utiliser un chemin absolu depuis le projet
    test_image = os.path.join(
        os.path.dirname(__file__), 
        "..", 
        "static", 
        "uploads", 
        "photo_2"
    )
    
    enc = encode_face(test_image)
    if enc:
        print("✓ Visage encodé avec succès")
        print(f"  Encodage : {len(enc)} dimensions")
    else:
        print("✗ Aucun visage détecté")