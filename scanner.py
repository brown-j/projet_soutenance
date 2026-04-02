import cv2
import requests
import time

# REMPLACE PAR TON URL DE DÉPLOIEMENT (ex: https://ton-app.render.com)
#SERVER_URL = "https://projet-soutenance-3cyw.onrender.com/video/stream"
SERVER_URL = "http://localhost:5000/video/stream"  # Pour tests locaux

cap = cv2.VideoCapture(0)

print("📷 Caméra de surveillance démarrée...")
print("📡 Envoi des flux vers :", SERVER_URL)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    cv2.imshow('Surveillance Locale', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

    # 1. On compresse l'image pour l'envoi (gain de rapidité)
    _, img_encoded = cv2.imencode('.jpg', frame)
    
    # 2. On prépare le fichier pour l'envoi
    files = {'image': ('frame.jpg', img_encoded.tobytes(), 'image/jpeg')}

    try:
        # 3. Envoi au serveur
        response = requests.post(SERVER_URL, files=files, timeout=30)
        
        if response.status_code == 200:
            print(f"✅ Image envoyée - Réponse: {response.text}", end="\r")
        else:
            print(f"⚠️ Erreur serveur: {response.status_code}", end="\r")
            
    except Exception as e:
        print(f"❌ Erreur de connexion au serveur : {e}")

    # On attend 0.5 seconde (pour envoyer 2 images par seconde)
    # Cela évite de saturer ta connexion internet et ton serveur
    time.sleep(0.5)

cap.release()