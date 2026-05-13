import os
import requests
import numpy as np
import json
from dotenv import load_dotenv

# Charge les variables du fichier .env
load_dotenv()

class PresenceHttpClient:
    def __init__(self):
        """
        Initialise le client HTTP pour récupérer les données.
        """
        self.base_url = os.getenv("RENDER_SERVER_URL", "http://localhost:5000").rstrip('/')
        self.endpoint = f"{self.base_url}/visages/encodings"

    def fetch_encodings(self):
        """
        Récupère les encodages depuis l'API Flask.
        Retourne : (liste_ids, liste_numpy_arrays)
        """
        print(f"🌐 [HTTP] Demande des encodages à {self.endpoint}...")
        
        try:
            response = requests.get(self.endpoint, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            raw_ids = data.get("ids", [])
            raw_encodings = data.get("encodings", [])
            
            if not raw_ids or not raw_encodings:
                print("⚠️ [HTTP] Aucun encodage trouvé ou format JSON incorrect.")
                return [], []

            known_encodings = []
            for enc in raw_encodings:
                try:
                    # Sécurité : Si l'encodage est une chaîne de caractères, on le transforme en liste
                    if isinstance(enc, str):
                        enc = json.loads(enc)
                    
                    # CORRECTION CRITIQUE : Conversion forcée en float64 pour éviter l'erreur ufunc subtract
                    np_enc = np.array(enc).astype('float64')
                    known_encodings.append(np_enc)
                except Exception as e:
                    print(f"⚠️ [HTTP] Encodage ignoré (format corrompu) : {e}")

            print(f"✅ [HTTP] Succès : {len(known_encodings)} encodages faciaux chargés.")
            return raw_ids[:len(known_encodings)], known_encodings
            
        except requests.exceptions.ConnectionError:
            print("❌ [HTTP] Erreur : Serveur injoignable.")
            return [], []
        except Exception as e:
            print(f"❌ [HTTP] Erreur lors de la récupération : {e}")
            return [], []