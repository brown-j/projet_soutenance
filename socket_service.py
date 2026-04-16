import os
import redis
import threading
from flask_socketio import SocketIO

# 1. Connexion à Redis
# Sur Render, tu utiliseras l'URL fournie par ton instance Redis (ex: redis://red-...)
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6373')
r = redis.from_url(REDIS_URL)

# On initialise sans l'app pour l'instant
socketio = SocketIO(cors_allowed_origins="*")

@socketio.on('connect')
def handle_connect():
    print("✅ Client local (Agent) connecté au WebSocket !")

@socketio.on('video_frame')
def handle_frame(data):
    if data:
        try:
            r.set('live_frame', data)
            
            # Tente de poser un verrou de 10 secondes (sécurité si le worker crash)
            # .set(..., nx=True) renvoie True si la clé a été créée, False sinon.
            lock_acquired = r.set('is_processing', 'true', ex=10, nx=True)
            
            if lock_acquired:
                from workers.tasks import process_recognition_task
                broadcast_processed_frame()
                process_recognition_task.delay()
                print("🔒 Verrou posé, tâche envoyée")
            else:
                print("⏳ Worker occupé, on saute cette frame")

        except Exception as e:
            print(f"Erreur : {e}")
            
                        
# Si tu veux envoyer l'image APRES le passage de l'IA (avec les carrés verts)
# La tâche Celery écrit dans Redis, et cette fonction sera appelée depuis le serveur Flask
def broadcast_processed_frame():
    processed_data = r.get('processed_frame')
    if processed_data:
        # On décode si c'est en bytes, sinon on envoie la string base64
        frame_data = processed_data.decode('utf-8') if isinstance(processed_data, bytes) else processed_data
        socketio.emit('processed_feed', frame_data)

# Fonctions pour commander le client
def start_remote_capture():
    print("🚀 Envoi commande : START")
    socketio.emit('command', {'action': 'start'})

def stop_remote_capture():
    print("🛑 Envoi commande : STOP")
    socketio.emit('command', {'action': 'stop'})