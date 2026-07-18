import os
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import make_msgid  # NOUVEAUTÉ : Import pour le threading
from datetime import datetime
from flask import current_app
from database.db import get_connection

# === DÉMARRAGE DU SCHEDULER ===
from apscheduler.schedulers.background import BackgroundScheduler

# On crée l'instance du planificateur de manière globale pour ce service
scheduler = BackgroundScheduler()
# On le démarre immédiatement
scheduler.start()
# ==========================================================

def generer_et_envoyer_rapports(app, employe_ids=None, custom_date_debut=None, custom_date_fin=None):
    """
    Génère et envoie les bilans de présence.
    - Si appelé par le planificateur : utilise la config de la BDD et envoie à tout le monde.
    - Si appelé manuellement : utilise les dates et les IDs fournis en paramètres.
    """
    with app.app_context():
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 1. Détermination de la période
        if custom_date_debut and custom_date_fin:
            date_debut = custom_date_debut
            date_fin = custom_date_fin
        else:
            cursor.execute("SELECT date_debut, date_fin FROM notification_config WHERE is_active = 1 LIMIT 1")
            config = cursor.fetchone()
            if not config:
                cursor.close()
                conn.close()
                return
            date_debut = config['date_debut']
            date_fin = config['date_fin']
        
        # 2. Récupérer les employés ciblés (tous, ou seulement ceux sélectionnés)
        if employe_ids and len(employe_ids) > 0:
            # Création dynamique des %s pour la clause IN (ex: %s, %s, %s)
            format_strings = ','.join(['%s'] * len(employe_ids))
            query_employes = f"SELECT id, matricule, nom, prenom, email FROM employes WHERE id IN ({format_strings}) AND email IS NOT NULL AND email != ''"
            cursor.execute(query_employes, tuple(employe_ids))
        else:
            cursor.execute("SELECT id, matricule, nom, prenom, email FROM employes WHERE email IS NOT NULL AND email != ''")
            
        employes = cursor.fetchall()
        
        if not employes:
            cursor.close()
            conn.close()
            return

        # Configuration du serveur de messagerie avec os.getenv()
        smtp_server = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
        smtp_port = os.getenv('MAIL_PORT', 587)
        smtp_user = os.getenv('MAIL_USERNAME', 'wbitjong@gmail.com')
        smtp_password = os.getenv('MAIL_PASSWORD', 'knle qdzh ewbz inzf')

        if not smtp_user or not smtp_password:
            print("Erreur : MAIL_USERNAME ou MAIL_PASSWORD est introuvable. Vérifie ton fichier .env !")
            cursor.close()
            conn.close()
            return

        server = None
        try:
            # On sort l'initialisation du serveur du bloc try principal pour ne pas crasher la boucle
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            
            # 3. Boucle d'envoi individuel sécurisée
            for emp in employes:
                try:
                    # Récupérer les pointages
                    query_pointages = """
                        SELECT DATE(timestamp) as date_p, MIN(timestamp) as arrivee, MAX(timestamp) as depart 
                        FROM pointages 
                        WHERE employe_id = %s AND DATE(timestamp) BETWEEN %s AND %s
                        GROUP BY DATE(timestamp)
                    """
                    cursor.execute(query_pointages, (emp['id'], date_debut, date_fin))
                    records = cursor.fetchall()
                    
                    jours_presents = len(records)
                    total_heures = 0.0
                    table_html_rows = ""
                    
                    for r in records:
                        arrivee_str = r['arrivee'].strftime('%H:%M') if r['arrivee'] else '--:--'
                        depart_str = r['depart'].strftime('%H:%M') if r['depart'] else '--:--'
                        
                        h_duree = 0.0
                        if r['arrivee'] and r['depart'] and r['arrivee'] != r['depart']:
                            diff = r['depart'] - r['arrivee']
                            h_duree = round(diff.total_seconds() / 3600, 2)
                            total_heures += h_duree
                            
                        table_html_rows += f"""
                            <tr>
                                <td style="padding:8px; border-bottom:1px solid #ddd;">{r['date_p']}</td>
                                <td style="padding:8px; border-bottom:1px solid #ddd; color: green;">Présent</td>
                                <td style="padding:8px; border-bottom:1px solid #ddd;">{arrivee_str}</td>
                                <td style="padding:8px; border-bottom:1px solid #ddd;">{depart_str}</td>
                                <td style="padding:8px; border-bottom:1px solid #ddd;">{h_duree} h</td>
                            </tr>
                        """

                    # Construction du mail
                    msg = MIMEMultipart()
                    msg['From'] = smtp_user
                    msg['To'] = emp['email']
                    
                    # RÈGLE 1 POUR LE THREADING : Le sujet doit être strictement identique à chaque envoi
                    msg['Subject'] = "PresenceApp - Votre Rapport Officiel des Présences"
                    
                    # === DÉBUT LOGIQUE DE THREADING (FILS DE DISCUSSION) ===
                    # ID de référence constant basé sur l'ID de l'employé (le "dossier" parent)
                    thread_id = f"presence_rapport_employe_{emp['id']}@presenceapp.local"
                    
                    # Identifiant unique pour ce mail précis envoyé aujourd'hui
                    msg['Message-ID'] = make_msgid(domain="presenceapp.local") 
                    
                    # Rattachement au thread parent
                    msg['In-Reply-To'] = f"<{thread_id}>"
                    msg['References'] = f"<{thread_id}>"
                    # === FIN LOGIQUE DE THREADING ===
                    
                    html_body = f"""
                    <html>
                    <body style="font-family: Arial, sans-serif; color: #333;">
                        <h2>Rapport Officiel des Présences</h2>
                        <p><strong>Employé :</strong> {emp['nom']} {emp['prenom']} ({emp['matricule']})</p>
                        <p><strong>Période :</strong> Du {date_debut} au {date_fin}</p>
                        <hr/>
                        <h3>Résumé de la période</h3>
                        <ul>
                            <li><strong>Jours présents :</strong> {jours_presents}</li>
                            <li><strong>Total heures :</strong> {round(total_heures, 2)} h</li>
                        </ul>
                        <table style="width:100%; border-collapse: collapse; margin-top:15px;">
                            <thead>
                                <tr style="background-color:#f2f2f2; text-align:left;">
                                    <th style="padding:8px;">Date</th>
                                    <th style="padding:8px;">Statut</th>
                                    <th style="padding:8px;">Heure Arrivée</th>
                                    <th style="padding:8px;">Heure Départ</th>
                                    <th style="padding:8px;">Durée</th>
                                </tr>
                            </thead>
                            <tbody>
                                {table_html_rows if table_html_rows else '<tr><td colspan="5" style="text-align:center;padding:10px;">Aucun pointage enregistré sur cette période.</td></tr>'}
                            </tbody>
                        </table>
                        <br><small style="color:#777;">Généré automatiquement par PresenceApp le {datetime.now().strftime('%d/%m/%Y')}</small>
                    </body>
                    </html>
                    """
                    msg.attach(MIMEText(html_body, 'html'))
                    
                    # Tentative d'envoi
                    server.sendmail(smtp_user, emp['email'], msg.as_string())
                    
                    # LOG DE SUCCÈS
                    cursor.execute("""
                        INSERT INTO historique_notifications (employe_id, email, statut, message_erreur) 
                        VALUES (%s, %s, 'Succès', NULL)
                    """, (emp['id'], emp['email']))
                    conn.commit()
                    
                    print(f"✔ Rapport envoyé à {emp['email']} pour l'employé {emp['nom']} {emp['prenom']}.")
                    time.sleep(2) # Pause stratégique anti-spam
                    
                except Exception as loop_e:
                    # LOG D'ÉCHEC POUR CET EMPLOYÉ PRÉCIS
                    cursor.execute("""
                        INSERT INTO historique_notifications (employe_id, email, statut, message_erreur) 
                        VALUES (%s, %s, 'Échec', %s)
                    """, (emp['id'], emp['email'], str(loop_e)))
                    conn.commit()
                    print(f"❌ Erreur pour {emp['email']} : {loop_e}")

        except Exception as main_e:
            print(f"Erreur globale SMTP (connexion impossible) : {main_e}")
        finally:
            if server:
                server.quit()
            cursor.close()
            conn.close()

def reprogrammer_tache_depuis_db(app):
    """Lit la BDD et réaligne la planification du Scheduler"""
    with app.app_context():
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT cron_hour, cron_minute, cron_day_of_week FROM notification_config WHERE is_active = 1 LIMIT 1")
        config = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if config:
            job_id = 'job_notification_automatique'
            
            if scheduler.get_job(job_id):
                scheduler.remove_job(job_id)
                
            real_app = app._get_current_object() if hasattr(app, '_get_current_object') else app
            
            scheduler.add_job(
                id=job_id,
                func=generer_et_envoyer_rapports,
                args=[real_app],
                trigger='cron',
                day_of_week=config['cron_day_of_week'],
                hour=config['cron_hour'],
                minute=config['cron_minute']
            )