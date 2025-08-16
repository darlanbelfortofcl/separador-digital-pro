from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from config import CLEANUP_ENABLED, CLEANUP_AGE_HOURS, CLEANUP_INTERVAL_MINUTES, UPLOAD_FOLDER, OUTPUT_FOLDER
from file_utils import remove_older_than
import logging


def _cleanup_job():
    removed_u = remove_older_than(UPLOAD_FOLDER, CLEANUP_AGE_HOURS)
    removed_o = remove_older_than(OUTPUT_FOLDER, CLEANUP_AGE_HOURS)
    logging.getLogger("cleanup").info(f"Limpeza executada. uploads: {removed_u}, outputs: {removed_o}")


def start_cleanup_scheduler():
    if not CLEANUP_ENABLED:
        return None
    scheduler = BackgroundScheduler(daemon=True)
    trigger = IntervalTrigger(minutes=CLEANUP_INTERVAL_MINUTES)
    scheduler.add_job(_cleanup_job, trigger, id="cleanup_job", replace_existing=True)
    scheduler.start()
    return scheduler
