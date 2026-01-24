from database.db import get_connection


def get_dashboard_stats():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM employes")
    total_employees = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM presences")
    total_presences = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return {
        "employees": total_employees,
        "presences": total_presences
    }
