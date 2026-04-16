import cv2
import socketio
import base64
import time

#api_url = 'https://projet-soutenance-3cyw.onrender.com'  # en ligne
api_url = 'http://localhost:5000'  # en local

sio = socketio.Client(reconnection=True, reconnection_attempts=5, reconnection_delay=5)
cap = cv2.VideoCapture(0)
is_running = True

@sio.event
def connect():
    print("✅ Connecté au serveur Render !")

@sio.event
def connect_error(data):
    print(f"❌ Erreur de connexion : {data}")

@sio.on('command')
def on_command(data):
    global is_running
    action = data.get('action')
    if action == 'start':
        print("🚀 Démarrage de la capture...")
        is_running = True
    elif action == 'stop':
        print("🛑 Arrêt de la capture.")
        is_running = False

def stream_video():
    global is_running
    while True:
        # On ne tente l'envoi QUE si on est connecté ET que la capture est activée
        if sio.connected and is_running:
            success, frame = cap.read()
            if success:
                try:
                    # Redimensionner pour alléger le flux (Optionnel mais conseillé)
                    # frame = cv2.resize(frame, (640, 480))
                    
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
                    frame_encoded = base64.b64encode(buffer).decode('utf-8')
                    
                    sio.emit('video_frame', frame_encoded)
                except Exception as e:
                    print(f"Erreur envoi frame : {e}")
        
        # Un petit sleep pour ne pas saturer le CPU local
        time.sleep(0.1) 

if __name__ == '__main__':
    try:
        # Remplace par ton URL Render réelle
        sio.connect(api_url, wait_timeout=10)
        stream_video()
    except Exception as e:
        print(f"💥 Impossible de se connecter : {e}")