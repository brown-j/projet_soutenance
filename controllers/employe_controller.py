from flask import Blueprint, render_template, request, redirect, url_for, abort

from services.employe_service import (
    get_all_employes,
    create_employe,
    delete_employe,
    get_employe_by_id,
    update_employe,
    save_employe_photo,
    delete_employe_photo
)

employe_bp = Blueprint("employe", __name__)

@employe_bp.route("/dashboard/employes/add", methods=["POST"])
def add_employe():
    matricule = request.form["matricule"]
    nom = request.form["nom"]
    prenom = request.form["prenom"]
    poste = request.form.get("poste")
    photo = request.files.get("photo")

    employe_id = create_employe(matricule, nom, prenom, poste, None)

    if photo and photo.filename:
        filename = save_employe_photo(photo, employe_id)
        update_employe(
            id=employe_id,
            photo_reference=filename
        )

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
    employe = get_employe_by_id(id)

    if employe:
        if employe.get("photo_reference"):
            delete_employe_photo(employe["photo_reference"])
        delete_employe(id)

    return redirect(url_for("employe.employes"))


@employe_bp.route("/dashboard/employes/edit/<int:id>", methods=["POST"])
def edit_employe(id):
    matricule = request.form["matricule"]
    nom = request.form["nom"]
    prenom = request.form["prenom"]
    poste = request.form.get("poste")
    photo = request.files.get("photo")

    if photo and photo.filename:
        employe = get_employe_by_id(id)
        if employe and employe.get("photo_reference"):
            delete_employe_photo(employe["photo_reference"])

        filename = save_employe_photo(photo, id)
        photo = filename

    update_employe(id, matricule, nom, prenom, poste, photo)

    return redirect(url_for("employe.employes"))

