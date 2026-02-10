from flask import Blueprint, render_template

dashboard_bp = Blueprint("dashboard", __name__)
# dashboard_controller.py
@dashboard_bp.route("/dashboard")
def dashboard():
    # Cette route charge UNIQUEMENT le contenu de l'iframe (stats.html)
    return render_template(
        "dashboard.html",
        page = "pages/stats.html",
        active_page="stats",
        page_css="stats.css"
    )
