import face_recognition
import numpy as np

def compare_two_faces(image_path_1, image_path_2, threshold=0.6):
    """
    Compare deux images et retourne True si c'est la même personne
    """

    # Charger les images
    img1 = face_recognition.load_image_file(image_path_1)
    img2 = face_recognition.load_image_file(image_path_2)

    # Encoder les visages
    enc1_list = face_recognition.face_encodings(img1)
    enc2_list = face_recognition.face_encodings(img2)

    if len(enc1_list) == 0 or len(enc2_list) == 0:
        return None  # Aucun visage détecté

    enc1 = enc1_list[0]
    enc2 = enc2_list[0]

    # Calcul de la distance
    distance = np.linalg.norm(enc1 - enc2)

    # Comparaison
    is_same = distance < threshold

    return {
        "same_person": is_same,
        "distance": round(float(distance), 4),
        "threshold": threshold
    }
