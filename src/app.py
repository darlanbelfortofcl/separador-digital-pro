from flask import Flask, request, jsonify
import logging, os
from . import config

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
app.config.from_object(config)

@app.route('/')
def index():
    return '<h1>PDF Tool - Render Fix</h1><p>API rodando com sucesso.</p>'

@app.route('/health')
def health():
    return jsonify(status='ok', redis_enabled=bool(config.REDIS_URL))

if __name__ == '__main__':
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
