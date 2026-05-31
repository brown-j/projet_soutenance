from database.db import get_connection

def get_total_employees(cursor):
    """Récupère le nombre total d'employés enregistrés."""
    cursor.execute("SELECT COUNT(*) as total FROM employes")
    return cursor.fetchone()['total']

def get_daily_presents(cursor):
    """Compte les employés ayant pointé au moins une fois aujourd'hui."""
    cursor.execute("""
        SELECT COUNT(DISTINCT employe_id) as total 
        FROM pointages 
        WHERE DATE(timestamp) = CURDATE()
    """)
    return cursor.fetchone()['total']

def get_daily_late_count(cursor, limit_time="08:30:00"):
    """Compte les employés arrivés après l'heure limite (format HH:MM:SS)."""
    query = """
        SELECT COUNT(*) as total FROM (
            SELECT employe_id, MIN(timestamp) as premier_pointage
            FROM pointages
            WHERE DATE(timestamp) = CURDATE()
            GROUP BY employe_id
        ) as sub
        WHERE TIME(premier_pointage) > %s
    """
    cursor.execute(query, (limit_time,))
    return cursor.fetchone()['total']
def get_daily_avg_work_hours(cursor):
    """Calcule la moyenne d'heures travaillées pour la journée en cours."""
    cursor.execute("""
        SELECT AVG(TIMESTAMPDIFF(SECOND, arrivee, depart)) / 3600 as avg_h
        FROM (
            SELECT employe_id, MIN(timestamp) as arrivee, MAX(timestamp) as depart
            FROM pointages
            WHERE DATE(timestamp) = CURDATE()
            GROUP BY employe_id
            HAVING arrivee != depart
        ) as daily_work
    """)
    res = cursor.fetchone()
    avg = round(res['avg_h'], 1) if res and res['avg_h'] is not None else 0.0
    return f"{avg}h"

def get_dashboard_stats():
    db = None
    # On définit l'heure limite ici pour une modification facile
    LATE_THRESHOLD = "13:32:00" 
    
    try:
        db = get_connection()
        cursor = db.cursor(dictionary=True)
        
        stats = {
            "total_employees": get_total_employees(cursor),
            "total_presents": get_daily_presents(cursor),
            "total_late": get_daily_late_count(cursor, LATE_THRESHOLD),
            "avg_hours": get_daily_avg_work_hours(cursor)
        }
        
        cursor.close()
        return stats

    except Exception as e:
        print(f"Erreur lors de la récupération des stats: {e}")
        return {
            "total_employees": "--", "total_presents": "--", 
            "total_late": "--", "avg_hours": "--"
        }
    finally:
        if db:
            db.close()
            
            
            
def get_presence_7days_data():
    """Récupère les présences avec correction du mode ONLY_FULL_GROUP_BY."""
    db = None
    try:
        db = get_connection()
        cursor = db.cursor(dictionary=True)
        
        # Correction : On trie par l'alias ou par la fonction d'agrégation directement
        query = """
            SELECT 
                e.nom, 
                e.prenom, 
                IFNULL(DATE_FORMAT(MIN(p.timestamp), '%H:%i'), '--:--') as arrivee,
                CASE WHEN MIN(p.timestamp) IS NOT NULL THEN 1 ELSE 0 END as present
            FROM employes e
            LEFT JOIN pointages p ON e.id = p.employe_id 
                AND p.timestamp >= DATE_SUB(CURDATE(), INTERVAL 6 DAY)
            GROUP BY e.id, e.nom, e.prenom, DATE(p.timestamp)
            ORDER BY MIN(p.timestamp) DESC, e.nom ASC
        """
        
        cursor.execute(query)
        data = cursor.fetchall()
        
        cursor.close()
        return data

    except Exception as e:
        print(f"Erreur lors de la récupération des données 7 jours: {e}")
        return []
    finally:
        if db:
            db.close()