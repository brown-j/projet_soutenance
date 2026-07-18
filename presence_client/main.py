import cv2
import time
import sys
from src.camera.streamer import CameraStream
from src.network.socket_client import PresenceSocketClient
from src.network.http_client import PresenceHttpClient
from src.recognition.engine import RecognitionEngine

class AttendanceApp:
    def __init__(self):
        """
        Initialisation de l'application desktop.
        """
        
        # 1. Initialisation des drivers et du moteur
        # On les crée une seule fois ici pour éviter les fenêtres multiples
        self.http_client = PresenceHttpClient()
        self.engine = RecognitionEngine()
        self.camera = CameraStream(video_source=0) 
        
        # 2. Définition de la fonction de synchronisation des données
        def sync_data():
            """Récupère les derniers visages depuis l'API locale/distante."""
            print("🔄 [Main] Synchroninsation des encodages faciaux...")
            ids, encodings = self.http_client.fetch_encodings()
            if ids and encodings:
                self.engine.update_known_faces(ids, encodings)
            else:
                print("⚠️ [Main] Attention : Aucun encodage chargé.")

        # 3. Initialisation du WebSocket avec le callback de synchro
        # Dès que le serveur envoie 'encodings_updated', sync_data() est appelée
        self.socket_gateway = PresenceSocketClient(on_update_callback=sync_data)

    def run(self):
        """
        Boucle principale de traitement en temps réel.
        """
        try:
            # Connexion au serveur (Flask local ou Render)
            self.socket_gateway.connect()
            
            print("\n🚀 [Main] Application lancée avec succès.")
            print("💡 Appuyez sur 'q' pour fermer l'application.\n")
            
            while True:
                # A. Capture de la frame (resize_factor=0.5 pour la fluidité)
                ret, frame_orig, frame_rgb = self.camera.get_frame(resize_factor=0.5)
                
                if not ret:
                    print("❌ [Main] Erreur de flux vidéo. Arrêt...")
                    break

                # B. Traitement par le moteur de reconnaissance
                # Le moteur dessine directement les carrés sur frame_orig
                processed_frame, detected_ids = self.engine.process_frame(frame_rgb, frame_orig)

                # C. Envoi des détections au serveur via SocketIO
                for id in detected_ids:
                    self.socket_gateway.send_attendance(id)
                
                # D. NOUVEAU : Envoi de la frame pour le broadcast (vidéo)
                # On envoie la frame_orig qui contient déjà les carrés dessinés
                self.socket_gateway.send_video_frame(processed_frame)

                # E. Affichage unique
                # show_frame utilise le nom de fenêtre fixe défini dans camera.py
                self.camera.show_frame(processed_frame)

                # F. Gestion de la sortie clavier (touche 'q')
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        except KeyboardInterrupt:
            print("\n[Main] Interruption détectée (Ctrl+C).")
        except Exception as e:
            print(f"\n❌ [Main] Erreur critique : {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        """
        Fermeture propre de toutes les ressources.
        """
        print("\n🧹 [Main] Nettoyage des ressources...")
        self.camera.stop()
        self.socket_gateway.disconnect()
        print("✅ [Main] Système arrêté proprement. À bientôt !")
        sys.exit(0)

if __name__ == "__main__":
    # Point d'entrée du programme
    app = AttendanceApp()
    app.run()