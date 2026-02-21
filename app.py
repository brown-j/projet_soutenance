import os
from flask import Flask, request
from controllers.login_controller import login_bp
from controllers.dashboard_controller import dashboard_bp
from controllers.employe_controller import employe_bp
from controllers.presence_controller import presence_bp
from controllers.apropos_controller import apropos_bp
from controllers.video_controller import video_bp
from workers.tasks import process_recognition_task
from utils.photos import get_photo_url
from celery_worker import app as celery_app

# Ajoute ceci au début de ton fichier app.py, après les imports
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER

app = Flask(__name__)
app.secret_key = "super_secret_key_2026"

# 1. Configuration du dossier
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static/uploads')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 2. Création des dossiers au démarrage (C'est ici qu'il faut le faire !)
# On crée le dossier principal et le sous-dossier 'photos'
os.makedirs(os.path.join(UPLOAD_FOLDER, 'photos'), exist_ok=True)

app.register_blueprint(login_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(employe_bp)
app.register_blueprint(presence_bp)
app.register_blueprint(apropos_bp)
app.register_blueprint(video_bp)
    
app.celery = celery_app

app.jinja_env.globals.update(get_photo_url=get_photo_url)

if __name__ == "__main__":
    app.run(debug=True)

    
    @app.route('/detect', methods=['POST'])
    def detect():
         # ... code pour sauvegarder le fichier sur le disque ...
        file_path = "temp_frames/frame_xyz.jpg"
    
        # On envoie la tâche à Redis et on libère Flask immédiatement
        process_recognition_task.delay(file_path)
    
        return {"status": "success", "message": "Image envoyée au worker"}, 200




@app.route('/api/camera_push', methods=['POST'])
def camera_push():
    if 'image' not in request.files:
        return {"error": "No image provided"}, 400
    
    file = request.files['image']
    # Sauvegarde temporaire pour que Celery puisse la traiter
    image_path = os.path.join("uploads", "frame_to_process.jpg")
    file.save(image_path)
    
    # On délègue le travail lourd à Celery
    from workers.tasks import process_recognition_task
    process_recognition_task.delay(image_path)
    
    return {"status": "received"}, 200