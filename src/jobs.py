import logging
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from typing import List, Optional

from celery import Celery
from celery.exceptions import CeleryError

from .config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND, OUTPUT_FOLDER, REDIS_URL
from .pdf_ops import split_pdf, merge_pdfs, compress_pdf
from .doc_ops import pdf_to_docx
from .utils import safe_stem

log = logging.getLogger(__name__)

def _celery_available() -> bool:
    try:
        if not REDIS_URL:
            return False
        # Light check: try to instantiate Celery and ping control (may fail if no worker).
        c = Celery(__name__, broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)
        insp = c.control.inspect(timeout=0.5)
        _ = insp.ping()
        # If no workers, still allow enqueue; backend might be OK. We'll return True anyway.
        return True
    except Exception as e:
        log.warning("Celery backend/broker not available: %s", e)
        return False

CELERY_ENABLED = _celery_available()
celery = Celery(__name__, broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND) if CELERY_ENABLED else None
if celery:
    celery.conf.update(task_serializer='json', result_serializer='json', accept_content=['json'], task_track_started=True, timezone='UTC')

# ---- Tasks (only registered if celery is enabled) ----
if celery:
    @celery.task(bind=True)
    def task_split(self, file_path: str, original_name: str) -> str:
        src = Path(file_path)
        base = safe_stem(original_name)
        out_root = OUTPUT_FOLDER / f"split_{self.request.id}" / base
        written = split_pdf(src, out_root, base)
        zip_path = OUTPUT_FOLDER / f"split_{self.request.id}.zip"
        with ZipFile(zip_path, 'w', ZIP_DEFLATED) as zf:
            for p in written:
                zf.write(p, p.relative_to(OUTPUT_FOLDER / f"split_{self.request.id}"))
        return str(zip_path)

    @celery.task(bind=True)
    def task_merge(self, file_paths: List[str], out_name: str = 'merged.pdf') -> str:
        paths = [Path(p) for p in file_paths]
        out_path = OUTPUT_FOLDER / f"merge_{self.request.id}" / out_name
        merged = merge_pdfs(paths, out_path)
        return str(merged)

    @celery.task(bind=True)
    def task_compress(self, file_path: str) -> str:
        src = Path(file_path)
        out_path = OUTPUT_FOLDER / f"compress_{self.request.id}" / f"{src.stem}_compressed.pdf"
        compressed = compress_pdf(src, out_path)
        return str(compressed)

    @celery.task(bind=True)
    def task_pdf_to_docx(self, file_path: str) -> str:
        src = Path(file_path)
        out_docx = OUTPUT_FOLDER / f"docx_{self.request.id}" / f"{src.stem}.docx"
        docx_path = pdf_to_docx(src, out_docx)
        return str(docx_path)

# ---- Synchronous wrappers (used when Celery is disabled) ----
def run_split_sync(file_path: str, original_name: str) -> str:
    src = Path(file_path)
    base = safe_stem(original_name)
    out_root = OUTPUT_FOLDER / f"split_sync" / base
    written = split_pdf(src, out_root, base)
    zip_path = OUTPUT_FOLDER / f"split_sync_{src.stem}.zip"
    with ZipFile(zip_path, 'w', ZIP_DEFLATED) as zf:
        for p in written:
            zf.write(p, p.relative_to(OUTPUT_FOLDER))
    return str(zip_path)

def run_merge_sync(file_paths: List[str], out_name: str = 'merged.pdf') -> str:
    paths = [Path(p) for p in file_paths]
    out_path = OUTPUT_FOLDER / f"merge_sync" / out_name
    merged = merge_pdfs(paths, out_path)
    return str(merged)

def run_compress_sync(file_path: str) -> str:
    src = Path(file_path)
    out_path = OUTPUT_FOLDER / f"compress_sync" / f"{src.stem}_compressed.pdf"
    compressed = compress_pdf(src, out_path)
    return str(compressed)

def run_pdf_to_docx_sync(file_path: str) -> str:
    src = Path(file_path)
    out_docx = OUTPUT_FOLDER / f"docx_sync" / f"{src.stem}.docx"
    docx_path = pdf_to_docx(src, out_docx)
    return str(docx_path)
