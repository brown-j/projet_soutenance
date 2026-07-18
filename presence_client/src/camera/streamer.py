import cv2

class CameraStream:
    def __init__(self, video_source=0):
        self.video_source = video_source
        self.vid = cv2.VideoCapture(self.video_source)
        
        # FIX : On définit un nom de fenêtre fixe et on l'initialise ici
        self.window_name = "Soutenance ICT4D - Presence"
        if self.vid.isOpened():
            # WINDOW_NORMAL permet de redimensionner la fenêtre si besoin
            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
            print(f"🟢 [Camera] Fenêtre '{self.window_name}' initialisée.")

    def get_frame(self, resize_factor=0.5):
        ret, frame = self.vid.read()
        if not ret:
            return False, None, None

        # Redimensionnement pour les performances
        width = int(frame.shape[1] * resize_factor)
        height = int(frame.shape[0] * resize_factor)
        frame_small = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)
        
        # Conversion pour face_recognition
        rgb_small_frame = cv2.cvtColor(frame_small, cv2.COLOR_BGR2RGB)

        return True, frame, rgb_small_frame

    def show_frame(self, frame):
        """Affiche la frame dans l'UNIQUE fenêtre définie."""
        # FIX : On utilise toujours le même self.window_name
        cv2.imshow(self.window_name, frame)

    def stop(self):
        self.vid.release()
        cv2.destroyAllWindows()