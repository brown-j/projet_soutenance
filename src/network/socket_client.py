import base64
import os
import cv2
import socketio
from dotenv import load_dotenv

# Charge les variables du fichier .env
load_dotenv()

class PresenceSocketClient:
    def __init__(self, on_update_callback=None):
        """
        Initialise la passerelle WebSocket.
        :param on_update_callback: Fonction à exécuter quand le serveur demande une mise à jour.
        """
        self.sio = socketio.Client()
        # On récupère l'URL de ton serveur Render depuis le .env (ex: https://projet-soutenance-3cyw.onrender.com)
        self.server_url = os.getenv("RENDER_SERVER_URL", "http://localhost:5000")
        
        # Le callback permet de lier ce module HTTP sans importer le module HTTP ici (Clean Architecture)
        self.on_update_callback = on_update_callback 
        
        self._setup_events()

    def _setup_events(self):
        """Configure tous les écouteurs d'événements SocketIO."""
        
        @self.sio.on('connect')
        def on_connect():
            print("🟢 [WebSocket] Connecté avec succès au serveur Render.")
            # Au démarrage, on force une mise à jour pour avoir les derniers encodages
            if self.on_update_callback:
                print("➡️ [WebSocket] Synchronisation initiale des données...")
                self.on_update_callback()

        @self.sio.on('disconnect')
        def on_disconnect():
            print("🔴 [WebSocket] Déconnecté du serveur. En attente de reconnexion...")

        @self.sio.on('connect_error')
        def on_connect_error(data):
            print(f"⚠️ [WebSocket] Erreur de connexion : {data}")

        @self.sio.on('encodings_updated')
        def on_encodings_updated(data):
            """Événement reçu quand un nouvel étudiant est ajouté sur le site Web."""
            reason = data.get('reason', 'Mise à jour inconnue')
            print(f"🔄 [WebSocket] Signal de mise à jour reçu. Raison : {reason}")
            
            if self.on_update_callback:
                self.on_update_callback()

    def connect(self):
        """Lance la connexion au serveur."""
        try:
            print(f"⏳ Tentative de connexion à {self.server_url}...")
            # wait_timeout et reconnection automatique sont gérés par défaut
            self.sio.connect(self.server_url)
        except Exception as e:
            print(f"❌ Erreur lors du lancement du WebSocket : {e}")
            
    def disconnect(self):
        """Ferme la connexion proprement."""
        if self.sio.connected:
            self.sio.disconnect()
            print("🛑 [WebSocket] Connexion fermée manuellement.")

    def send_attendance(self, student_name):
        """
        Envoie une notification de présence au serveur Render.
        :param student_name: Le nom de l'étudiant reconnu (ex: "Joseph Brown")
        """
        if self.sio.connected:
            print(f"📤 Envoi de la présence pour l'étudiant : {student_name}")
            self.sio.emit('register_attendance', {'nom': student_name, 'status': 'Present'})
        else:
            print(f"⚠️ [Erreur] Impossible d'enregistrer {student_name}, le réseau est déconnecté.")
    

    def send_video_frame(self, frame):
        """
        Encode la frame en JPEG, puis en Base64 et l'envoie au serveur.
        :param frame: La frame OpenCV (BGR) à diffuser.
        """
        if self.sio.connected:
            try:
                # 1. Compression de l'image pour réduire la bande passante (qualité 50-70)
                # On réduit la taille si nécessaire, mais ici on compresse surtout le JPEG
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 65]
                _, buffer = cv2.imencode('.jpg', frame, encode_param)
                
                # 2. Conversion en Base64
                jpg_as_text = base64.b64encode(buffer).decode('utf-8')
                
                # 3. Émission via l'événement 'video_frame'
                # On ajoute le préfixe data:image pour que le frontend puisse l'afficher directement
                self.sio.emit('video_frame', f"data:image/jpeg;base64,{jpg_as_text}")
                
            except Exception as e:
                print(f"⚠️ [WebSocket] Erreur d'encodage vidéo : {e}")
