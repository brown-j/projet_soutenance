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
    Récupère les présences pour une date spécifique.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Convertir la date en string si nécessaire
    if not isinstance(date_obj, str):
        date_str = date_obj.isoformat()
    else:
        date_str = date_obj

    # On récupère les présences pour la date spécifiée
    query = """
        SELECT e.nom, e.matricule, p.date_presence, p.heure_arrivee, p.heure_depart 
        FROM presences p
        JOIN employes e ON p.employe_id = e.id
        WHERE p.date_presence = %s
        ORDER BY p.heure_arrivee DESC
    """

    cursor.execute(query, (date_str,))

    presences = cursor.fetchall()

    cursor.close()
    conn.close()

    return presences

# services/presence_service.py
def log_attendance(employe_id):
    """
    Enregistre le pointage d'un employé dans la table 'presence'.
    """
    now = datetime.now()
    date_today = now.date()
    current_time = now.time().strftime("%H:%M:%S")

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # On vérifie si l'employé n'a pas déjà pointé aujourd'hui pour éviter les doublons
        # (Anti-spam de 5 minutes par exemple ou simple check journalier)
        
        query = """
            INSERT INTO presence (employe_id, date_presence, heure_arrivee)
            VALUES (%s, %s, %s)
            ON CONFLICT (employe_id, date_presence) DO NOTHING;
        """
        # Note : Utilise ? au lieu de %s si tu es sur SQLite
        cursor.execute(query, (employe_id, date_today, current_time))
        
        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ Pointage réussi pour l'ID {employe_id} à {current_time}")
        return True

    except Exception as e:
        print(f"❌ Erreur SQL lors du pointage : {e}")
        return False