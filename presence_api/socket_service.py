import os
import redis
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
def handle_frame(processed_data):
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