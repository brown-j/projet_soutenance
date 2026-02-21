# controllers/video_controller.py
from flask import Blueprint, render_template, request, jsonify
from workers.tasks import process_recognition_task
import os
import time
import subprocess
import signal
from flask import Response
import glob

# Variable globale pour stocker l'ID du processus de la caméra
camera_process = None

video_bp = Blueprint('video', __name__)

# Utiliser des chemins absolus pour que Celery trouve les fichiers
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMP_DIR = os.path.join(PROJECT_ROOT, "static/temp_frames/")
TEMP_FILE = os.path.join(TEMP_DIR, "processing.jpg")  # Fichier unique qui se réécrit

# Nettoyer les anciennes frames au démarrage
def cleanup_old_frames():
    """Supprime les anciennes frames (frame_*.jpg) pour éviter l'accumulation"""
    try:
        old_frames = glob.glob(os.path.join(TEMP_DIR, "frame_*.jpg"))
        for old_file in old_frames:
            try:
                os.remove(old_file)
                print(f"🗑️  Nettoyage: {old_file}")
            except Exception as e:
                print(f"⚠️  Impossible de supprimer {old_file}: {e}")
    except Exception as e:
        print(f"❌ Erreur lors du nettoyage: {e}")

cleanup_old_frames()

@video_bp.route("/video/stream", methods=["POST"])
def stream_handler():
    if 'image' not in request.files:
        return jsonify({"error": "No image"}), 400
        
    file = request.files['image']
    
    # Sauvegarde unique (overwrite à chaque frame) - pas d'accumulation!
    file.save(TEMP_FILE)

    # Envoi asynchrone vers Celery
    process_recognition_task.delay(TEMP_FILE)

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
            # Essayer de lire latest.jpg (image avec IA)
            latest_path = os.path.join(TEMP_DIR, "latest.jpg")
            processing_path = os.path.join(TEMP_DIR, "processing.jpg")
            
            # Préférer latest.jpg (avec IA), sinon fallback sur processing.jpg
            image_to_read = latest_path if os.path.exists(latest_path) else processing_path
            
            try:
                if os.path.exists(image_to_read):
                    with open(image_to_read, "rb") as f:
                        frame = f.read()
                    
                    if frame:  # Vérifier que le fichier n'est pas vide
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                    else:
                        print(f"⚠️ Fichier vide: {image_to_read}")
            except IOError as e:
                print(f"⚠️ Erreur lecture image: {e}")
            
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