# --- ÉTAPE 1 : TOUJOURS EN PREMIER (LIGNE 1 & 2) ---
import eventlet
eventlet.monkey_patch()

import os
from flask import Flask, request
from controllers.login_controller import login_bp
from controllers.dashboard_controller import dashboard_bp
from controllers.employe_controller import employe_bp
from controllers.presence_controller import presence_bp
from controllers.apropos_controller import apropos_bp
from controllers.video_controller import video_bp
from controllers.history_controller import historique_bp
from utils.photos import get_photo_url
from celery_worker import app as celery_app
from socket_service import socketio

# Configuration des dossiers
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static/uploads')
os.makedirs(os.path.join(UPLOAD_FOLDER, 'photos'), exist_ok=True)

app = Flask(__name__)
app.secret_key = "super_secret_key_2026"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- ÉTAPE 2 : Liaison SocketIO ---
socketio.init_app(app)

# Enregistrement des Blueprints
app.register_blueprint(login_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(employe_bp)
app.register_blueprint(presence_bp)
app.register_blueprint(apropos_bp)
app.register_blueprint(video_bp)
app.register_blueprint(historique_bp)
    
app.celery = celery_app
app.jinja_env.globals.update(get_photo_url=get_photo_url)

if __name__ == "__main__":
    # --- ÉTAPE 3 : UTILISER socketio.run AU LIEU DE app.run ---
    print("🚀 Serveur de soutenance démarré sur http://localhost:5000")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)