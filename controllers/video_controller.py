# controllers/video_controller.py
from flask import Blueprint, render_template

video_bp = Blueprint('video', __name__)

@video_bp.route("/video/monitoring")
def video_monitoring():
    # On renvoie le dashboard, mais on lui dit d'inclure video_monitor.html
    return render_template(
        'dashboard.html', 
        page='video_monitor.html', 
        active_page='video'
    )