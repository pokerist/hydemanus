import logging
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from processors.event_processor import poll_and_process_events
from config import LOG_FILE, POLLING_INTERVAL_SECONDS

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('HydeParkSync.Poller')

def main():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        poll_and_process_events,
        'interval',
        seconds=POLLING_INTERVAL_SECONDS,
        id='event_polling_job',
        name='Supabase Event Poller',
        next_run_time=datetime.now()
    )
    scheduler.start()
    logger.info(f"Poller started. Interval: {POLLING_INTERVAL_SECONDS} seconds.")
    try:
        import time
        while True:
            time.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

if __name__ == '__main__':
    main()