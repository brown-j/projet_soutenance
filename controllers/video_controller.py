# controllers/video_controller.py
from flask import Blueprint, render_template, request, jsonify
from workers.tasks import process_recognition_task
import os
import time
import subprocess
import signal
import time
from flask import Response

# Variable globale pour stocker l'ID du processus de la caméra
camera_process = None

video_bp = Blueprint('video', __name__)

TEMP_DIR = "static/temp_frames/"

@video_bp.route("/video/stream", methods=["POST"])
def stream_handler():
    if 'image' not in request.files:
        return jsonify({"error": "No image"}), 400
        
    file = request.files['image']
    
    # Sauvegarde rapide sur disque
    filename = f"frame_{int(time.time() * 1000)}.jpg"
    filepath = os.path.join(TEMP_DIR, filename)
    file.save(filepath)

    # Envoi asynchrone vers Celery
    process_recognition_task.delay(filepath)

    return jsonify({"status": "received"}), 202



@video_bp.route("/video/control", methods=["POST"])
def control_camera():
    global camera_process
    data = request.get_json()
    producer_path = "camera_producer/camera_producer.py";
    
    if not data:
        return jsonify({"status": "error", "message": "Aucune donnée reçue"}), 400
        
    action = data.get("action")
    print(f"DEBUG: Action reçue -> {action}") # Regarde ton terminal Flask

    if action == "start":
        if camera_process is None or camera_process.poll() is not None:
            # Commande précise pour Ubuntu
            camera_process = subprocess.Popen(["python3", producer_path])
            return jsonify({"status": "success", "message": "Caméra démarrée"}), 200
        return jsonify({"status": "success", "message": "Déjà lancée"}), 200

    elif action == "stop":
        if camera_process:
            camera_process.terminate()
            camera_process = None
            print("DEBUG: Processus caméra terminé")
            return jsonify({"status": "success", "message": "Arrêt réussi"}), 200
        else:
            # On renvoie 200 même si c'était déjà arrêté pour éviter l'erreur 400 côté JS
            return jsonify({"status": "success", "message": "Déjà arrêtée"}), 200

    return jsonify({"status": "error", "message": "Action inconnue"}), 400


@video_bp.route("/video/feed")
def video_feed():
    """Route qui génère le flux vidéo pour la balise <img>"""
    def generate():
        while True:
            # On cherche l'image 'latest.jpg' (celle avec les rectangles de l'IA)
            # Si elle n'existe pas, on peut lire la frame brute
            path = os.path.join(TEMP_DIR, "latest.jpg")
            
            if os.path.exists(path):
                with open(path, "rb") as f:
                    frame = f.read()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            
            # On limite à 10 FPS pour ne pas saturer le CPU/Réseau
            time.sleep(0.1)

    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@video_bp.route("/video/monitoring")
def video_monitoring():
    # On renvoie le dashboard, mais on lui dit d'inclure video_monitor.html
    return render_template(
        'dashboard.html', 
        page='video_monitor.html', 
        active_page='video'
    )