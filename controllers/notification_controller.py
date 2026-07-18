from flask import Blueprint, request, jsonify, render_template, current_app
from database.db import get_connection

# Import des fonctions de notre service de notifications
from services.notification_service import reprogrammer_tache_depuis_db, generer_et_envoyer_rapports

# Déclaration du Blueprint pour regrouper les routes liées aux notifications
notification_bp = Blueprint('notification', __name__)

@notification_bp.route('/dashboard/notifications')
def page_notification():
    """Affiche la page de configuration et l'historique dans le panel admin"""
    return render_template(
        "dashboard.html",
        page="pages/notification.html",
        page_css="notification.css",
        active_page="notification",
    )

@notification_bp.route('/api/admin/notifications/config', methods=['GET'])
def get_config():
    """Récupère la configuration active actuelle"""
    conn = get_connection()
    # On s'assure d'obtenir les résultats sous forme de dictionnaire pour le JSON
    cursor = conn.cursor(dictionary=True) if hasattr(conn, 'cursor') else conn.cursor()
    
    try:
        cursor.execute("""
            SELECT date_debut, date_fin, cron_hour, cron_minute, cron_day_of_week, is_active 
            FROM notification_config 
            WHERE is_active = 1 
            LIMIT 1
        """)
        config = cursor.fetchone()
        
        if config:
            # Normalisation du format de la date pour le calendrier HTML5 (YYYY-MM-DD)
            if hasattr(config['date_debut'], 'strftime'):
                config['date_debut'] = config['date_debut'].strftime('%Y-%m-%d')
                config['date_fin'] = config['date_fin'].strftime('%Y-%m-%d')
            return jsonify({"status": "success", "data": config})
        
        return jsonify({"status": "empty", "data": None})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Erreur de récupération : {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

@notification_bp.route('/api/admin/notifications/config', methods=['POST'])
def save_config():
    """Enregistre ou met à jour la planification automatique des e-mails"""
    data = request.json
    date_debut = data.get('date_debut')
    date_fin = data.get('date_fin')
    hour = data.get('hour', '18')
    minute = data.get('minute', '0')
    day_of_week = data.get('day_of_week', '*')

    if not date_debut or not date_fin:
        return jsonify({"status": "error", "message": "Les dates de début et de fin sont requises."}), 400

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Désactiver proprement l'ancienne configuration active
        cursor.execute("UPDATE notification_config SET is_active = 0 WHERE is_active = 1")
        
        # Insérer la nouvelle planification de référence
        query = """
            INSERT INTO notification_config (date_debut, date_fin, cron_hour, cron_minute, cron_day_of_week, is_active)
            VALUES (%s, %s, %s, %s, %s, 1)
        """
        cursor.execute(query, (date_debut, date_fin, hour, minute, day_of_week))
        conn.commit()
        
        # Reprogrammer dynamiquement la tâche de fond dans le Scheduler en arrière-plan
        reprogrammer_tache_depuis_db(current_app)
        
        return jsonify({"status": "success", "message": "Planification enregistrée et activée avec succès !"})
    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": f"Erreur BDD : {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()
        
@notification_bp.route('/api/admin/notifications/history', methods=['GET'])
def get_notification_history():
    """Récupère l'historique avec h.employe_id inclus pour l'envoi manuel ciblé"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # CORRECTION : h.employe_id est inclus. Il est indispensable pour récupérer 
        # l'ID de l'employé lors de la sélection multiple et l'envoi ciblé.
        query = """
            SELECT h.id, h.employe_id, e.matricule, e.nom, e.prenom, h.email, h.statut, 
                   LEFT(h.message_erreur, 60) as message_erreur, h.date_envoi
            FROM historique_notifications h
            JOIN employes e ON h.employe_id = e.id
            ORDER BY h.date_envoi DESC
        """
        cursor.execute(query)
        historique = cursor.fetchall()
        return jsonify({"status": "success", "data": historique})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Erreur de récupération : {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

@notification_bp.route('/api/admin/notifications/send_manual', methods=['POST'])
def send_manual_notifications():
    """Déclenche un envoi manuel immédiat aux employés sélectionnés"""
    data = request.json
    employe_ids = data.get('employe_ids', [])
    date_debut = data.get('date_debut')
    date_fin = data.get('date_fin')

    # Validation de sécurité sur la liste d'identifiants
    if not employe_ids or not isinstance(employe_ids, list):
        return jsonify({"status": "error", "message": "Aucun employé valide sélectionné."}), 400

    try:
        # Appel du service avec les paramètres personnalisés de l'administrateur
        generer_et_envoyer_rapports(
            app=current_app, 
            employe_ids=employe_ids, 
            custom_date_debut=date_debut, 
            custom_date_fin=date_fin
        )
        return jsonify({"status": "success", "message": f"Envoi terminé avec succès pour {len(employe_ids)} employé(s)."})
    except Exception as e:
        # Capturer l'exception si le serveur SMTP est injoignable ou si l'envoi crash globalement
        return jsonify({"status": "error", "message": f"Erreur système lors de l'envoi : {str(e)}"}), 500