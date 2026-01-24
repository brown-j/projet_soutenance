from flask import Blueprint, render_template

presence_bp = Blueprint("presence", __name__)

@presence_bp.route("/dashboard/presences")
def presence():
    return render_template(
        "dashboard.html",
        page="pages/presences.html",
        page_css="presences.css",
        active_page="presences"
    )
