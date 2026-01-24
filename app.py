from flask import Flask
from controllers.login_controller import login_bp
from controllers.dashboard_controller import dashboard_bp
from controllers.employe_controller import employe_bp
from controllers.presence_controller import presence_bp
from controllers.apropos_controller import apropos_bp
from utils.photos import get_photo_url

app = Flask(__name__)
app.secret_key = "super_secret_key_2026"

app.register_blueprint(login_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(employe_bp)
app.register_blueprint(presence_bp)
app.register_blueprint(apropos_bp)

app.jinja_env.globals.update(get_photo_url=get_photo_url)

if __name__ == "__main__":
    app.run(debug=True)
