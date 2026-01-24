from database.db import get_connection


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
