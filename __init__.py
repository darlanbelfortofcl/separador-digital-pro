import os
from flask import Flask
from .routes import bp

def create_app():
    app = Flask(__name__, static_url_path="/static", static_folder="app/static", template_folder="app/templates")
    # Segurança básica
    app.secret_key = os.getenv("SECRET_KEY", "change-me-in-production")
    # Diretórios
    app.config["UPLOAD_FOLDER"] = os.getenv("UPLOAD_FOLDER", "uploads")
    app.config["OUTPUT_FOLDER"] = os.getenv("OUTPUT_FOLDER", "outputs")
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["OUTPUT_FOLDER"], exist_ok=True)
    app.register_blueprint(bp)
    return app

# Suporte para executar localmente: python -m app
if __name__ == "__main__":
    app = create_app()
    app.run(host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", 5000)), debug=os.getenv("FLASK_DEBUG", "0") == "1")
