import os, uuid, mimetypes, logging, time, json
from pathlib import Path
from PyPDF2 import PdfReader
from werkzeug.utils import secure_filename
from flask import request
try:
    import magic
    HAVE_MAGIC=True
except Exception:
    HAVE_MAGIC=False

log=logging.getLogger(__name__)

def json_log(event: str, **kw):
    payload={'event':event,'ts':int(time.time()*1000),**kw}; log.info(json.dumps(payload, ensure_ascii=False))

def request_id()->str:
    return request.headers.get('X-Request-ID') or uuid.uuid4().hex

def allowed_file(filename:str)->bool:
    return '.' in filename and filename.rsplit('.',1)[1].lower() in {'pdf'}

def detect_mime(path:Path)->str:
    if HAVE_MAGIC:
        try:
            m=magic.Magic(mime=True)
            return m.from_file(str(path))
        except Exception as e:
            log.warning('magic failed: %s', e)
    ctype,_=mimetypes.guess_type(str(path))
    return ctype or 'application/octet-stream'

def is_pdf_real(path:Path)->bool:
    mime=detect_mime(path) or ''
    return path.suffix.lower()=='.pdf' and ('pdf' in mime.lower())

def validate_pdf(path:Path)->dict:
    # Open to ensure it's readable and not encrypted. Returns metadata.
    if not is_pdf_real(path):
        raise ValueError('Arquivo inválido. Envie um PDF de verdade (não renomeado).')
    try:
        reader=PdfReader(str(path))
    except Exception as e:
        raise ValueError('Arquivo inválido ou corrompido. Reexporte como PDF.') from e
    if reader.is_encrypted:
        raise ValueError('Arquivo protegido por senha. Envie um PDF sem senha.')
    pages=len(reader.pages)
    if pages<1:
        raise ValueError('PDF sem páginas.')
    return {'pages':pages}

def unique_safe_filename(name:str)->str:
    safe=secure_filename(name); base,ext=os.path.splitext(safe); return f"{base}_{uuid.uuid4().hex}{ext}"

def safe_stem(name:str)->str:
    safe=secure_filename(name); base,_=os.path.splitext(safe); return base or 'arquivo'
