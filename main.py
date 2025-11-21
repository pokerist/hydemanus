import logging
import os
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from config import POLLING_INTERVAL_SECONDS, LOG_FILE, DASHBOARD_HOST, DASHBOARD_PORT
from dashboard.app import app
from processors.event_processor import poll_and_process_events

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('HydeParkSync')

def start_polling_service():
    """Initializes and starts the background polling service."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        poll_and_process_events,
        'interval',
        seconds=POLLING_INTERVAL_SECONDS,
        id='event_polling_job',
        name='Supabase Event Poller',
        next_run_time=datetime.now() # Run immediately on start
    )
    scheduler.start()
    logger.info(f"Polling service started. Interval: {POLLING_INTERVAL_SECONDS} seconds.")
    return scheduler

def start_web_dashboard():
    """Starts the Flask web dashboard."""
    logger.info(f"Starting Web Dashboard on http://{DASHBOARD_HOST}:{DASHBOARD_PORT}")
    # Use Gunicorn for production-like environment, but Flask's built-in server for simplicity in this script
    # For actual deployment, we will use the systemd service with gunicorn
    try:
        app.run(host=DASHBOARD_HOST, port=DASHBOARD_PORT, debug=False)
    except Exception as e:
        logger.error(f"Failed to start Web Dashboard: {e}")

if __name__ == "__main__":
    logger.info("--- HydePark Sync System Starting Up ---")

    # 1. Start the background polling service
    scheduler = start_polling_service()

    # 2. Start the web dashboard (this will block the main thread)
    try:
        start_web_dashboard()
    except (KeyboardInterrupt, SystemExit):
        logger.info("System shutdown initiated.")
        scheduler.shutdown()
        logger.info("Scheduler shut down.")
    except Exception as e:
        logger.critical(f"A critical error occurred in the main loop: {e}")

    logger.info("--- HydePark Sync System Shut Down ---")
