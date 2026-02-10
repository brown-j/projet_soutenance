from flask import Blueprint, render_template, request, redirect, url_for, flash

import os
from services.employe_service import (
    get_all_employes,
    create_employe,
    delete_employe,
    get_employe_by_id,
    update_employe,
)
from services.visage_service import upsert_visage

employe_bp = Blueprint("employe", __name__)

@employe_bp.route("/dashboard/employes/add", methods=["POST"])
def add_employe():
    matricule = request.form["matricule"]
    nom = request.form["nom"]
    prenom = request.form["prenom"]
    poste = request.form.get("poste")
    photo = request.files.get("photo_face")

    employe_id = create_employe(matricule, nom, prenom, poste)
    upsert_visage(employe_id, "face", photo)

    return redirect(url_for("employe.employes"))


@employe_bp.route("/dashboard/employes")
def employes():
    employes = get_all_employes()

    return render_template(
        "dashboard.html",
        page="pages/employes.html",
        active_page="employes",
        page_css="employes.css",
        employes=employes
    )


@employe_bp.route("/dashboard/employes/delete/<int:id>")
def delete(id):
    delete_employe(id)
    return redirect(url_for("employe.employes"))


@employe_bp.route("/dashboard/employes/edit/<int:id>", methods=["POST"])
def edit_employe(id):
    matricule = request.form["matricule"]
    nom = request.form["nom"]
    prenom = request.form["prenom"]
    poste = request.form.get("poste")
    photo = request.files.get("photo_face")

    result = update_employe(id, matricule, nom, prenom, poste)

    if result["status"] == "success":
        upsert_visage(id, "face", photo)
        print(result["message"])
    else:
        print(f"Erreur : {result['message']}")

    return redirect(url_for("employe.employes"))


@employe_bp.route('/dashboard/employes/photos/<int:id>', methods=['POST'])
def upload_photos(id):
    employe = get_employe_by_id(id)

    if not employe:
        flash("Employé introuvable.", "danger")
        return redirect(url_for("employe.employes"))

    for type_vue in ['face', 'profil_gauche', 'profil_droit']:
        photo = request.files.get(f'photo_{type_vue}')
        if photo and photo.filename != '':
            # On passe l'objet fichier directement
            resultat = upsert_visage(id, type_vue, photo)
        
            if resultat:
                flash(f"Photo {type_vue} enregistrée !", "success")
            else:
                flash(f"Erreur : Visage {type_vue} non détecté.", "danger")

    return redirect(url_for("employe.employes"))

