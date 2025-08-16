
import os
import io
from datetime import datetime, timedelta
from collections import defaultdict
from zipfile import ZipFile, ZIP_DEFLATED

from flask import (
    Flask, request, render_template, send_file, session,
    redirect, url_for
)
from PyPDF2 import PdfReader, PdfWriter

app = Flask(__name__)

# --- Config ---
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-me')
ADMIN_PASSWORD = os.environ.get('SENHA_ADMIN', 'admin')
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH_MB', '32')) * 1024 * 1024  # default 32MB
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

# Simple in-memory rate limit for login attempts (per IP)
ATTEMPT_WINDOW_MIN = int(os.environ.get('LOGIN_WINDOW_MIN', '15'))
ATTEMPT_MAX = int(os.environ.get('LOGIN_MAX_ATTEMPTS', '5'))
_attempts = defaultdict(list)

def too_many_attempts(ip):
    now = datetime.utcnow()
    window_start = now - timedelta(minutes=ATTEMPT_WINDOW_MIN)
    # keep only recent attempts
    _attempts[ip] = [t for t in _attempts[ip] if t >= window_start]
    return len(_attempts[ip]) >= ATTEMPT_MAX

def register_attempt(ip):
    _attempts[ip].append(datetime.utcnow())

# Very light CSRF protection
def get_csrf_token():
    tok = session.get('csrf_token')
    if not tok:
        tok = os.urandom(16).hex()
        session['csrf_token'] = tok
    return tok

@app.before_request
def _protect():
    if request.method == "POST":
        if request.endpoint in ('login', 'logout'):  # allow without token for login form (we'll check there)
            return
        token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
        if not token or token != session.get('csrf_token'):
            return "CSRF token inválido.", 400

def is_logged_in():
    return session.get('auth') is True

@app.route('/login', methods=['GET', 'POST'])
def login():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr or 'unknown').split(',')[0].strip()
    if request.method == 'POST':
        # basic CSRF for login
        token = request.form.get('csrf_token')
        if not token or token != session.get('csrf_token'):
            return render_template('login.html', error='Sessão expirada. Tente novamente.', attempts_left=max(0, ATTEMPT_MAX - len(_attempts[ip])), csrf_token=get_csrf_token())
        if too_many_attempts(ip):
            return render_template('login.html', error=f'Muitas tentativas. Aguarde {ATTEMPT_WINDOW_MIN} minutos.', attempts_left=0, csrf_token=get_csrf_token())
        pwd = request.form.get('password','')
        if pwd == ADMIN_PASSWORD:
            session['auth'] = True
            _attempts[ip] = []  # reset on success
            return redirect(url_for('index'))
        else:
            register_attempt(ip)
            left = max(0, ATTEMPT_MAX - len(_attempts[ip]))
            return render_template('login.html', error='Senha incorreta.', attempts_left=left, csrf_token=get_csrf_token())
    if is_logged_in():
        return redirect(url_for('index'))
    return render_template('login.html', attempts_left=max(0, ATTEMPT_MAX - len(_attempts[ip])), csrf_token=get_csrf_token())

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def index():
    if not is_logged_in():
        return redirect(url_for('login'))
    return render_template('index.html', csrf_token=get_csrf_token())

def parse_ranges(ranges_str):
    """
    Parses a string like "1-3,5,7-9" into a list of (start, end) 1-based inclusive tuples.
    """
    result = []
    if not ranges_str.strip():
        return result
    for part in ranges_str.split(','):
        part = part.strip()
        if '-' in part:
            a,b = part.split('-',1)
            a = int(a); b = int(b)
            if a > b:
                a, b = b, a
            result.append((a,b))
        else:
            n = int(part)
            result.append((n,n))
    return result

@app.route('/split', methods=['POST'])
def split():
    if not is_logged_in():
        return "Não autorizado", 401
    mode = request.form.get('mode', 'individual')
    try:
        pdf_file = request.files.get('file')
        if not pdf_file:
            return "Arquivo não enviado.", 400
        reader = PdfReader(pdf_file.stream)
    except Exception as e:
        return f"Falha ao ler PDF: {e}", 400

    output = io.BytesIO()

    if mode == 'individual':
        with ZipFile(output, 'w', compression=ZIP_DEFLATED) as zf:
            for i in range(len(reader.pages)):
                writer = PdfWriter()
                writer.add_page(reader.pages[i])
                bf = io.BytesIO()
                writer.write(bf)
                zf.writestr(f"pagina_{i+1}.pdf", bf.getvalue())
        output.seek(0)
        filename = "separado_paginas.zip"
        return send_file(output, as_attachment=True, download_name=filename, mimetype='application/zip')

    elif mode == 'ranges':
        ranges_str = request.form.get('ranges','').strip()
        try:
            ranges = parse_ranges(ranges_str)
        except Exception:
            return "Intervalos inválidos. Exemplo: 1-3,5,7-9", 400
        if not ranges:
            return "Nenhum intervalo informado.", 400

        multiple = len(ranges) > 1
        if multiple:
            with ZipFile(output, 'w', compression=ZIP_DEFLATED) as zf:
                for idx, (a,b) in enumerate(ranges, start=1):
                    a0 = max(1, a); b0 = min(len(reader.pages), b)
                    writer = PdfWriter()
                    for pg in range(a0-1, b0):
                        writer.add_page(reader.pages[pg])
                    bf = io.BytesIO()
                    writer.write(bf)
                    zf.writestr(f"intervalo_{idx}_{a0}-{b0}.pdf", bf.getvalue())
            output.seek(0)
            filename = "intervalos.zip"
            return send_file(output, as_attachment=True, download_name=filename, mimetype='application/zip')
        else:
            a,b = ranges[0]
            a0 = max(1, a); b0 = min(len(reader.pages), b)
            writer = PdfWriter()
            for pg in range(a0-1, b0):
                writer.add_page(reader.pages[pg])
            writer.write(output)
            output.seek(0)
            return send_file(output, as_attachment=True, download_name=f"intervalo_{a0}-{b0}.pdf", mimetype='application/pdf')
    else:
        return "Modo inválido.", 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
