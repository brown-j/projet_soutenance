from database.db import get_connection
import json
import numpy as np

def save_visage(employe_id, chemin_image, encodage):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO visages (employe_id, chemin_image, encodage)
        VALUES (%s, %s, %s)
    """, (employe_id, chemin_image, json.dumps(encodage)))

    conn.commit()
    cursor.close()
    conn.close()





def load_all_encodings():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT employe_id, encodage
        FROM visages
    """)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    encodings = []
    employe_ids = []

    for row in rows:
        enc = json.loads(row["encodage"])
        encodings.append(np.array(enc))
        employe_ids.append(row["employe_id"])

    return encodings, employe_ids
