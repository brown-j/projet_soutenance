from flask import Blueprint, jsonify, render_template
from services.historique_service import get_employee_history
from flask import jsonify, request

historique_bp = Blueprint("historique", __name__)

@historique_bp.route("/api/history/<matricule>")
def employee_history_api(matricule):
    # On récupère les paramètres ?start=...&end=...
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    
    # On passe les 3 arguments au service
    data = get_employee_history(matricule, start_date, end_date)
    
    if not data:
        return jsonify({"error": "Historique introuvable pour cette période"}), 404
        
    return jsonify(data)

@historique_bp.route("/dashboard/historique")
def historique():
    return render_template(
        "dashboard.html",
        page="pages/historique.html",
        page_css="history.css",
        active_page="historique"
    )
    
    