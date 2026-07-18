import cv2
import face_recognition
import numpy as np
from datetime import datetime

class RecognitionEngine:
    def __init__(self):
        self.known_ids = []
        self.known_encodings = []
        self.last_seen_cache = {} 
        self.cooldown_seconds = 60 # Anti-doublon d'une minute
        
    def update_known_faces(self, ids, encodings):
        """Met à jour les visages en mémoire avec vérification de type stricte."""
        valid_ids = []
        valid_encodings = []
        
        for i, enc in enumerate(encodings):
            try:
                # Conversion forcée en float64 pour éviter l'erreur ufunc subtract
                clean_enc = np.array(enc).astype('float64')
                if clean_enc.size == 128:
                    valid_encodings.append(clean_enc)
                    valid_ids.append(ids[i])
            except Exception as e:
                print(f"⚠️ [Engine] Encodage invalide ignoré pour l'ID {ids[i]}: {e}")

        self.known_ids = valid_ids
        self.known_encodings = valid_encodings
        print(f"📊 [Engine] Mémoire mise à jour : {len(self.known_ids)} visages chargés.")
        
    def process_frame(self, frame_rgb, frame_bgr):
        """
        Analyse les frames et retourne (frame_dessinée, liste_ids).
        :param frame_rgb: Image pour l'IA (format RGB, scale 0.5)
        :param frame_bgr: Image originale pour le dessin (format BGR)
        """
        detected_ids = []
        
        if not self.known_encodings:
            return frame_bgr, []

        # --- ÉTAPE 1 : AMÉLIORATION DU CONTRASTE (CLAHE) ---
        lab = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        cl = clahe.apply(l)
        limg = cv2.merge((cl,a,b))
        enhanced_rgb = cv2.cvtColor(limg, cv2.COLOR_LAB2RGB)

        # --- ÉTAPE 2 : DÉTECTION ---
        face_locations = face_recognition.face_locations(enhanced_rgb)
        
        # --- ÉTAPE 3 : ENCODAGE ---
        # Coordonnées x2 car frame_rgb est à 0.5 de l'originale (frame_bgr)
        scaled_locations = [(top*2, right*2, bottom*2, left*2) for (top, right, bottom, left) in face_locations]
        face_encodings = face_recognition.face_encodings(frame_bgr, scaled_locations)

        for (loc, face_to_check) in zip(scaled_locations, face_encodings):
            top, right, bottom, left = loc
            label = "Inconnu"
            color = (0, 0, 255) # Rouge par défaut

            # --- ÉTAPE 4 : COMPARAISON ---
            if len(self.known_encodings) > 0:
                matches = face_recognition.compare_faces(self.known_encodings, face_to_check, tolerance=0.45)
                
                if True in matches:
                    first_match_index = matches.index(True)
                    emp_id = self.known_ids[first_match_index]
                    label = f"ID: {emp_id}"
                    color = (0, 255, 0) # Vert
                    
                    # Logique anti-spam pour ne renvoyer l'ID que si le cooldown est passé
                    if self._should_trigger_attendance(emp_id):
                        detected_ids.append(emp_id)

            # --- ÉTAPE 5 : DESSIN (issu du 2eme code) ---
            self._draw_label_on_image(frame_bgr, left, top, right, bottom, label, color)

        return frame_bgr, detected_ids

    def _should_trigger_attendance(self, id):
        """Évite de spammer le serveur avec le même ID en continu."""
        now = datetime.now()
        last_time = self.last_seen_cache.get(id)
        if last_time is None or (now - last_time).total_seconds() > self.cooldown_seconds:
            self.last_seen_cache[id] = now
            return True
        return False

    def _draw_label_on_image(self, img, left, top, right, bottom, label, color):
        """
        Dessine le rectangle et le texte sur l'image.
        """
        # Rectangle autour du visage
        cv2.rectangle(img, (left, top), (right, bottom), color, 2)
        
        # Bandeau pour le texte en bas du carré
        cv2.rectangle(img, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
        
        # Texte (ID ou Inconnu)
        text = str(label)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(img, text, (left + 6, bottom - 6), font, 0.8, (255, 255, 255), 1)
        
        # Optionnel : Afficher le nombre de personnes en cache en haut à gauche
        cv2.putText(img, f"Visages actifs: {len(self.last_seen_cache)}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)