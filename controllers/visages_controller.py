from flask import Blueprint, jsonify
from services.visage_service import load_all_encodings

visages_bp = Blueprint("visages", __name__)

@visages_bp.route("/visages/encodings")
def get_encodings():
    try:
        # 1. Récupérer les données
        encodings_list, employe_ids = load_all_encodings()
        
        # 2. Convertir les numpy arrays en listes Python (pour le JSON)
        # load_all_encodings renvoie déjà des listes ou des arrays
        serializable_encodings = [
            enc.tolist() if hasattr(enc, "tolist") else enc 
            for enc in encodings_list
        ]
        
        # 3. Retourner une réponse JSON structurée
        return jsonify({
            "ids": employe_ids,
            "encodings": serializable_encodings
        }), 200

    except Exception as e:
        print(f"❌ Erreur lors de la récupération des encodages : {e}")
        return jsonify({"error": "Erreur interne du serveur"}), 500