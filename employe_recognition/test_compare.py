from employe_recognition.recognizer import compare_two_faces

result = compare_two_faces(
    "uploads/employes/emp1.jpg",
    "uploads/employes/emp1_test.jpg"
)

if result is None:
    print("Aucun visage détecté")
else:
    print("Même personne :", result["same_person"])
    print("Distance :", result["distance"])
