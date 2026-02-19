from database.db import get_connection
from datetime import datetime


def get_all_presences():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT p.id, e.nom, e.prenom, p.date, p.heure_entree, p.heure_sortie
        FROM presences p
        JOIN employes e ON p.employe_id = e.id
        ORDER BY p.date DESC
    """)

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