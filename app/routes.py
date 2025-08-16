from flask import Blueprint, render_template, request, redirect, url_for, session, send_file, jsonify
import os
from .utils import dividir_pdf
from werkzeug.utils import secure_filename
import time

bp = Blueprint('main', __name__)

UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'results'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

LOGIN_USER = "lucyta"
LOGIN_PASS = "29031984bB@G"

@bp.route('/')
def home():
    if not session.get("logado"):
        return redirect(url_for('main.login'))
    return redirect(url_for('main.painel'))

@bp.route('/login', methods=['GET', 'POST'])
def login():
    erro = None
    if request.method == 'POST':
        user = request.form.get('usuario')
        senha = request.form.get('senha')
        if user == LOGIN_USER and senha == LOGIN_PASS:
            session['logado'] = True
            return redirect(url_for('main.painel'))
        else:
            erro = "Usuário ou senha inválidos."
    return render_template('login.html', erro=erro)

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login'))

@bp.route('/painel', methods=['GET', 'POST'])
def painel():
    if not session.get("logado"):
        return redirect(url_for('main.login'))

    filename = None
    if request.method == 'POST':
        pdf_file = request.files['pdf_file']
        if pdf_file.filename:
            filename = secure_filename(pdf_file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            pdf_file.save(filepath)
            session['pdf_file'] = filepath
            return render_template('painel.html', filename=filename)

    return render_template('painel.html', filename=filename)

@bp.route('/process', methods=['POST'])
def process():
    if not session.get("logado"):
        return redirect(url_for('main.login'))

    pages = request.form.get('pages')
    filepath = session.get('pdf_file')
    if not filepath:
        return redirect(url_for('main.painel'))

    result_path = dividir_pdf(filepath, pages, RESULT_FOLDER)
    return send_file(result_path, as_attachment=True)

# Simulação de progresso
progress = 0

@bp.route('/start-progress', methods=['POST'])
def start_progress():
    global progress
    progress = 0
    for i in range(1, 101):
        time.sleep(0.03)  # Simula trabalho
        progress = i
    return jsonify({"status": "done"})

@bp.route('/progress')
def get_progress():
    return jsonify({"progress": progress})
