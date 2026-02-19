import cv2
import requests
import time

# Configuration
URL_API = "http://localhost:5000/video/stream"
CAMERA_INDEX = 0  # 0 pour la webcam intégrée

def start_capture():
    cap = cv2.VideoCapture(CAMERA_INDEX)
    
    print("📸 Caméra démarrée. Press 'q' to quit.")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Optionnel : On peut réduire la taille pour économiser de la bande passante
        # frame = cv2.resize(frame, (640, 480))

        # Encodage de l'image en JPG
        _, img_encoded = cv2.imencode('.jpg', frame)
        
        try:
            # Envoi de l'image au contrôleur Flask
            files = {'image': ('frame.jpg', img_encoded.tobytes(), 'image/jpeg')}
            response = requests.post(URL_API, files=files)
            
            if response.status_code == 202:
                print("📤 Frame envoyée au worker Celery")
        except Exception as e:
            print(f"❌ Erreur connexion serveur : {e}")

        # On attend un peu pour ne pas saturer le réseau (ex: 2 images par seconde)
        time.sleep(0.5)

        # Affichage local (optionnel)
        cv2.imshow('Camera Monitoring', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    start_capture()