from datetime import datetime
from database.db import get_connection

def get_employee_history(matricule, start_date, end_date):
    db = None
    if not start_date or not end_date:
        return None

    try:
        db = get_connection()
        cursor = db.cursor(dictionary=True)
        
        # On force CAST(%s AS DATE) pour que MySQL renvoie des objets date
        query = """
            WITH RECURSIVE calendrier AS (
                SELECT CAST(%s AS DATE) AS date_jour
                UNION ALL
                SELECT DATE_ADD(date_jour, INTERVAL 1 DAY)
                FROM calendrier
                WHERE date_jour < CAST(%s AS DATE)
            )
            SELECT 
                cal.date_jour,
                e.nom, e.prenom,
                MIN(p.timestamp) as h_arrivee,
                MAX(p.timestamp) as h_sortie,
                IFNULL(TIMESTAMPDIFF(MINUTE, MIN(p.timestamp), MAX(p.timestamp)) / 60, 0) as duree_h
            FROM calendrier cal
            CROSS JOIN (SELECT nom, prenom, id FROM employes WHERE matricule = %s) e
            LEFT JOIN pointages p ON cal.date_jour = DATE(p.timestamp) AND p.employe_id = e.id
            GROUP BY cal.date_jour, e.nom, e.prenom
            ORDER BY cal.date_jour ASC;
        """
        
        cursor.execute(query, (start_date, end_date, matricule))
        history = cursor.fetchall()
        
        if not history: return None

        dates, heures_arrivee, heures_sortie, raw_data, durees = [], [], [], [], []

        for row in history:
            # --- 1. GESTION DE LA DATE DU CALENDRIER ---
            # Si MySQL renvoie une string, on la convertit en objet date
            d_jour = row['date_jour']
            if isinstance(d_jour, str):
                d_jour = datetime.strptime(d_jour, "%Y-%m-%d")

            # --- 2. GESTION DES POINTAGES (Arrivée/Sortie) ---
            dt_arr = row['h_arrivee']
            dt_sor = row['h_sortie']
            
            # Calcul décimal pour le graphique (sécurisé)
            dec_arr = dt_arr.hour + (dt_arr.minute / 60) if dt_arr else None
            dec_sor = dt_sor.hour + (dt_sor.minute / 60) if dt_sor else None
            
            # Remplissage des listes pour le graphique
            dates.append(d_jour.strftime("%d/%m"))
            heures_arrivee.append(round(dec_arr, 2) if dec_arr is not None else None)
            heures_sortie.append(round(dec_sor, 2) if dec_sor is not None else None)
            
            # --- 3. GESTION DU TABLEAU (raw_data) ---
            raw_data.append({
                "date_jour": d_jour.strftime("%Y-%m-%d"),
                "heure_arrivee": dt_arr.strftime("%H:%M") if dt_arr else "--:--",
                "heure_sortie": dt_sor.strftime("%H:%M") if dt_sor else "--:--",
                "duree_h": round(float(row['duree_h']), 2)
            })
            durees.append(round(float(row['duree_h']), 2))

        return {
            "nom_complet": f"{history[0]['nom']} {history[0]['prenom']}",
            "dates": dates,
            "heures_arrivee": heures_arrivee,
            "heures_sortie": heures_sortie,
            "raw_data": raw_data,
            "durees": durees
        }
    except Exception as e:
        print(f"Erreur service historique: {e}")
        return None
    finally:
        if db: db.close()