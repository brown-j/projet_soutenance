from flask import Blueprint, render_template, jsonify

from database.db import get_connection
from services.dashboard_service import get_dashboard_stats
# Importe ta connexion à la base de données ici
# from config.db import get_db_connection 

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard")
def dashboard():
    stats = get_dashboard_stats()
    kpi_list = [
        { "value": stats.get("total_employees", 0), "label": "Nombre d'employés", "icon": "fas fa-users", "type": "primary" },
        { "value": stats.get("total_presents", 0), "label": "Présents", "icon": "fas fa-user-check", "type": "success" },
        { "value": stats.get("total_late", 0), "label": "Retards (> 08:30)", "icon": "fas fa-history", "type": "warning" },
        { "value": stats.get("avg_hours", 0), "label": "Moyenne de Travail", "icon": "fas fa-chart-line", "type": "danger" }
    ]
    
    return render_template(
        "dashboard.html",
        page="pages/stats.html",
        active_page="stats",
        page_css="stats.css",
        kpi_list=kpi_list,
    )

@dashboard_bp.route("/api/stats/presence_today")
def stats_today_api():
    try:
        db = get_connection()
        cursor = db.cursor(dictionary=True)
        
        # Cette requête calcule la durée entre les pointages impairs (entrée) 
        # et les pointages pairs (sortie) pour chaque employé aujourd'hui.
        query = """
            SELECT 
                e.nom, 
                e.prenom,
                -- Calcul de la somme des durées entre pointage N et N+1 (où N est impair)
                ROUND(SUM(
                    CASE WHEN nb_passage % 2 = 0 THEN 
                        TIMESTAMPDIFF(SECOND, prev_time, p_timestamp) 
                    ELSE 0 END
                ) / 3600, 2) as duree
            FROM (
                SELECT 
                    employe_id, 
                    timestamp as p_timestamp,
                    LAG(timestamp) OVER (PARTITION BY employe_id ORDER BY timestamp) as prev_time,
                    ROW_NUMBER() OVER (PARTITION BY employe_id ORDER BY timestamp) as nb_passage
                FROM pointages
                WHERE DATE(timestamp) = CURDATE()
            ) p
            JOIN employes e ON p.employe_id = e.id
            GROUP BY e.id, e.nom, e.prenom
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        # Nettoyage pour JSON (sérialisation)
        for row in results:
            # Si un employé est "Présent" (nombre de passages impair), 
            # sa durée actuelle ne compte que ses sessions terminées.
            if row['duree'] is None:
                row['duree'] = 0.0
            else:
                row['duree'] = float(row['duree'])

        cursor.close()
        db.close()
        
        return jsonify(results)
        
    except Exception as e:
        print(f"Erreur API Stats : {e}")
        return jsonify({"error": str(e)}), 500
    
@dashboard_bp.route("/api/stats/presence_7days")
def stats_7days():
    """Retourne les données réelles de présence des 7 derniers jours via le service"""
    from services.dashboard_service import get_presence_7days_data
    data = get_presence_7days_data()
    return jsonify(data)