from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database.db import get_connection

login_bp = Blueprint("login", __name__)

@login_bp.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        # Test simple (temporaire)
        if username == "admin" and password == "admin":
            session["user"] = username
            return redirect(url_for("dashboard.dashboard"))
        else:
            flash("Identifiants invalides", "danger")
            return redirect(url_for("login.login"))

    # GET -> afficher le formulaire de connexion
    return render_template("login.html")