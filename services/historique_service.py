from datetime import datetime
from database.db import get_connection

def get_one_employee_history(matricule, start_date, end_date):
    # 1. On récupère TOUTE l'histoire via la fonction globale
    all_data = get_all_employees_history(start_date, end_date)
    
    if not all_data:
        return None

    # 2. On filtre pour ne garder que l'employé souhaité
    employee_records = all_data.get(matricule)

    if not employee_records:
        return None
    
    return employee_records
    

def get_all_employees_history(start_date, end_date):
    db = None
    if not start_date or not end_date:
        return None

    try:
        db = get_connection()
        cursor = db.cursor(dictionary=True)
        
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
                e.matricule,
                e.nom, 
                e.prenom,
                MIN(p.timestamp) as h_arrivee,
                MAX(p.timestamp) as h_sortie,
                IFNULL(TIMESTAMPDIFF(MINUTE, MIN(p.timestamp), MAX(p.timestamp)) / 60, 0) as duree_h
            FROM calendrier cal
            CROSS JOIN employes e
            LEFT JOIN pointages p ON cal.date_jour = DATE(p.timestamp) AND p.employe_id = e.id
            GROUP BY cal.date_jour, e.id, e.nom, e.prenom, e.matricule
            ORDER BY cal.date_jour ASC, e.nom ASC;
        """
        
        cursor.execute(query, (start_date, end_date))
        history = cursor.fetchall()
        
        if not history:
            return {}

        # Initialisation de la Map (Dictionnaire)
        history_map = {}

        for row in history:
            mat = row['matricule']
            
            # Si c'est la première fois qu'on voit ce matricule, on initialise sa structure
            if mat not in history_map:
                history_map[mat] = {
                    "nom_complet": f"{row['nom']} {row['prenom']}",
                    "matricule": mat,
                    "dates": [],           # Pour l'axe X du graphique (02/04)
                    "heures_arrivee": [],  # Pour les points du graphique (decimal)
                    "heures_sortie": [],   # Pour les points du graphique (decimal)
                    "durees": [],          # Liste des durées (float)
                    "raw_data": []         # Pour remplir le tableau HTML
                }

            # --- 1. GESTION DE LA DATE ---
            d_jour = row['date_jour']
            if isinstance(d_jour, str):
                d_jour = datetime.strptime(d_jour, "%Y-%m-%d")

            # --- 2. GESTION DES POINTAGES (Datetimes) ---
            dt_arr = row['h_arrivee']
            dt_sor = row['h_sortie']
            
            # Conversion décimale pour Chart.js (ex: 08h30 -> 8.5)
            dec_arr = round(dt_arr.hour + (dt_arr.minute / 60), 2) if dt_arr else None
            dec_sor = round(dt_sor.hour + (dt_sor.minute / 60), 2) if dt_sor else None
            
            # --- 3. REMPLISSAGE DE LA MAP POUR CET EMPLOYÉ ---
            emp_data = history_map[mat]
            
            # Données Graphiques
            emp_data["dates"].append(d_jour.strftime("%d/%m"))
            emp_data["heures_arrivee"].append(dec_arr)
            emp_data["heures_sortie"].append(dec_sor)
            emp_data["durees"].append(round(float(row['duree_h']), 2))
            
            # Données Tableau (formatées en texte)
            emp_data["raw_data"].append({
                "date_jour": d_jour.strftime("%Y-%m-%d"),
                "heure_arrivee": dt_arr.strftime("%H:%M") if dt_arr else "--:--",
                "heure_sortie": dt_sor.strftime("%H:%M") if dt_sor else "--:--",
                "duree_h": round(float(row['duree_h']), 2),
                "statut": "Présent" if dt_arr else "Absent"
            })

        return history_map

    except Exception as e:
        print(f"Erreur service historique global: {e}")
        return None
    finally:
        if db:
            db.close()