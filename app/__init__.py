from flask import Flask
import os

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY", "chave_secreta")

    from .routes import bp
    app.register_blueprint(bp)

    return app
