import mysql.connector
from database.config import DB_CONFIG
import os

def get_connection():
    config = {
        'host': os.environ.get('MYSQL_HOST'),
        'user': os.environ.get('MYSQL_USER'),
        'password': os.environ.get('MYSQL_PASSWORD'),
        'database': os.environ.get('MYSQL_DB'),
        'port': os.environ.get('MYSQL_PORT', 3306),
        # Ajoute cette ligne pour le SSL obligatoire sur Aiven
        'ssl_ca': '/etc/ssl/certs/ca-certificates.crt'
    }
    return mysql.connector.connect(**config)

def create_database():
    """Crée la base de données en important schema.sql"""
    conn = get_connection(None)  # Connexion sans BD
    cursor = conn.cursor()
    
    try:
        # Lire le fichier schema.sql
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        
        with open(schema_path, "r", encoding="utf-8") as file:
            sql_script = file.read()
        
        # Exécuter chaque instruction SQL
        for statement in sql_script.split(";"):
            statement = statement.strip()
            if statement:
                cursor.execute(statement)
        
        conn.commit()
        print("✓ Base de données créée avec succès")
    except FileNotFoundError:
        print(f"✗ Fichier schema.sql non trouvé : {schema_path}")
    except Exception as e:
        print(f"✗ Erreur lors de la création : {e}")
    finally:
        cursor.close()
        conn.close()


def drop_database():
    """Supprime la base de données"""
    conn = get_connection(None)  # Connexion sans BD
    cursor = conn.cursor()
    
    try:
        cursor.execute("DROP DATABASE IF EXISTS gestion_presence")
        conn.commit()
        print("✓ Base de données supprimée avec succès")
    except Exception as e:
        print(f"✗ Erreur lors de la suppression : {e}")
    finally:
        cursor.close()
        conn.close()


def reset_database():
    """Réinitialise la base de données"""
    drop_database()
    create_database()

# Pour exécuter ces fonctions directement depuis le terminal :
#python3 -c "from database.db import create_database; create_database()"
#python3 -c "from database.db import drop_database; drop_database()"
#python3 -c "from database.db import reset_database; reset_database()"
