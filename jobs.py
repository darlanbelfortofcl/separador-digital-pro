import json
import logging
import queue
import threading
from pathlib import Path
from typing import Dict

from config import LOG_FOLDER, QUEUE_GET_TIMEOUT

job_queues: Dict[str, "queue.Queue"] = {}


def get_logger(job_id: str) -> logging.Logger:
    logger = logging.getLogger(f"job.{job_id}")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        LOG_FOLDER.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(Path(LOG_FOLDER) / f"{job_id}.log", encoding="utf-8")
        fmt = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    return logger


def start_thread(target, args: tuple) -> str:
    q = queue.Queue()
    job_id = args[0]  # 1º arg deve ser job_id
    job_queues[job_id] = q
    t = threading.Thread(target=target, args=args, daemon=True)
    t.start()
    return job_id


def sse_stream(job_id: str):
    if job_id not in job_queues:
        yield "data: " + json.dumps({"error": True, "msg": "job inválido"}, ensure_ascii=False) + "\n\n"
        return

    q: "queue.Queue" = job_queues[job_id]
    done = False
    while not done:
        try:
            item = q.get(timeout=QUEUE_GET_TIMEOUT)
            if isinstance(item, dict):
                if item.get("done"):
                    done = True
                yield "data: " + json.dumps(item, ensure_ascii=False) + "\n\n"
        except queue.Empty:
            # comentário (evento de keep-alive)
            yield ": ping\n\n"
    job_queues.pop(job_id, None)
