from database.db import get_connection
from datetime import datetime, timedelta



def format_date_description(date_str):
    """
    Formate une description intelligente de la date:
    - Aujourd'hui, Hier, Avant-hier
    - Cette semaine, La semaine passée, Il y a 2, 3, ... n semaines
    - Ce mois, Le mois passé, Il y a 2, 3, ..., n mois
    - Cette année, L'année passée, Il y a 2, 3, ..., n ans
    """
    if isinstance(date_str, str):
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        except:
            return date_str
    else:
        date_obj = date_str
    
    today = datetime.now().date()
    
    # Jours
    if date_obj == today:
        return "Aujourd'hui"
    elif date_obj == today - timedelta(days=1):
        return "Hier"
    elif date_obj == today - timedelta(days=2):
        return "Avant-hier"
    
    # Semaines
    days_diff = (today - date_obj).days
    
    # Début de la semaine courante (lundi)
    today_weekday = today.weekday()
    week_start = today - timedelta(days=today_weekday)
    
    if week_start <= date_obj < today:
        return "Cette semaine"
    
    # Semaine passée
    last_week_start = week_start - timedelta(days=7)
    if last_week_start <= date_obj < week_start:
        return "La semaine passée"
    
    # Il y a n semaines
    if 7 < days_diff < 30:
        weeks = days_diff // 7
        if weeks == 2:
            return "Il y a 2 semaines"
        elif weeks == 3:
            return "Il y a 3 semaines"
        else:
            return f"Il y a {weeks} semaines"
    
    # Mois
    if date_obj.year == today.year and date_obj.month == today.month:
        return "Ce mois"
    
    # Mois passé
    if date_obj.year == today.year and date_obj.month == today.month - 1:
        return "Le mois passé"
    
    # Il y a n mois
    months_diff = (today.year - date_obj.year) * 12 + (today.month - date_obj.month)
    if 1 < months_diff < 12:
        if months_diff == 2:
            return "Il y a 2 mois"
        elif months_diff == 3:
            return "Il y a 3 mois"
        else:
            return f"Il y a {months_diff} mois"
    
    # Années
    if date_obj.year == today.year:
        return "Cette année"
    
    if date_obj.year == today.year - 1:
        return "L'année passée"
    
    # Il y a n ans
    years_diff = today.year - date_obj.year
    if years_diff == 2:
        return "Il y a 2 ans"
    elif years_diff == 3:
        return "Il y a 3 ans"
    else:
        return f"Il y a {years_diff} ans"


def get_all_presences():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # On récupère les présences en joignant la table employes pour avoir le NOM
    query = """
        SELECT e.nom, e.matricule, p.date_presence, p.heure_arrivee, p.heure_depart 
    FROM presences p
    JOIN employes e ON p.employe_id = e.id
    ORDER BY p.date_presence DESC, p.heure_arrivee DESC
    """

    cursor.execute(query)

    presences = cursor.fetchall()

    cursor.close()
    conn.close()

    return presences


def get_presences_by_date(date_obj):
    """
    Récupère les employés et leurs passages.
    Logique de statut par parité :
    - 0 passage : Absent
    - Nombre impair : Présent (Entrée)
    - Nombre pair : Parti (Sortie)
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Formatage de la date
    if not isinstance(date_obj, str):
        date_str = date_obj.isoformat()
    else:
        date_str = date_obj

    # Requête SQL : On compte le nombre de passages et on les récupère tous
    query = """
        SELECT 
            e.id, e.nom, e.prenom, e.matricule,
            GROUP_CONCAT(TIME(p.timestamp) ORDER BY p.timestamp DESC SEPARATOR ',') as tous_passages,
            COUNT(p.id) as nb_passages
        FROM employes e
        LEFT JOIN pointages p ON e.id = p.employe_id AND DATE(p.timestamp) = %s
        GROUP BY e.id
        ORDER BY e.nom ASC
    """

    cursor.execute(query, (date_str,))
    rows = cursor.fetchall()

    resultats = []

    for row in rows:
        # Transformation de la chaîne GROUP_CONCAT en liste Python
        passages_list = row['tous_passages'].split(',') if row['tous_passages'] else []
        nb = row['nb_passages']
        
        # --- LOGIQUE DE STATUT SIMPLE ---
        if nb == 0:
            statut = "Absent"
            heure_arrivee = None
        elif nb % 2 != 0:
            # Nombre impair (1, 3, 5...) -> Présent
            statut = "Présent"
            heure_arrivee = passages_list[-1]
        else:
            # Nombre pair (2, 4, 6...) -> Parti
            statut = "Parti"
            heure_arrivee = passages_list[-1]

        resultats.append({
            "matricule": row['matricule'],
            "nom": row['nom'],
            "prenom": row['prenom'],
            "heure_arrivee": heure_arrivee,
            "passages": passages_list,
            "statut": statut
        })

    cursor.close()
    conn.close()
    return resultats
