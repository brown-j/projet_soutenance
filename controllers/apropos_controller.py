from flask import Blueprint, render_template

apropos_bp = Blueprint("apropos", __name__)

@apropos_bp.route("/dashboard/apropos")
def apropos():
    return render_template(
        "dashboard.html",
        page="pages/apropos.html",
        page_css="apropos.css",
        active_page="apropos"
    )
