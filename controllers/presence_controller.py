from flask import Blueprint, render_template, request
from datetime import datetime, timedelta

from services.presence_service import get_presences_by_date, format_date_description

presence_bp = Blueprint("presence", __name__)

@presence_bp.route("/dashboard/presences")
def presence():
    # Récupérer la date sélectionnée depuis la requête (par défaut aujourd'hui)
    selected_date = request.args.get('date', datetime.now().date().isoformat())
    
    if isinstance(selected_date, str):
        try:
            selected_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
        except:
            selected_date = datetime.now().date()
    
    # Récupérer les présences pour la date sélectionnée
    presences = get_presences_by_date(selected_date)
    
    # Générer la description de la date sélectionnée
    date_description = format_date_description(selected_date)
    
    return render_template(
        "dashboard.html",
        page="pages/presences.html",
        page_css="presences.css",
        active_page="presences",
        presences=presences,
        selected_date=selected_date.isoformat(),
        date_description=date_description
    )