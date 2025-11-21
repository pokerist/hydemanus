import json
import os
import logging
from config import WORKERS_DB, REQUEST_LOGS_DB

logger = logging.getLogger('HydeParkSync.DB')

def _load_data(file_path, default_data):
    """Loads data from a JSON file, or returns default data if the file is not found."""
    if not os.path.exists(file_path):
        logger.warning(f"Database file not found: {file_path}. Creating with default data.")
        _save_data(file_path, default_data)
        return default_data
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from {file_path}. Returning default data.")
        return default_data
    except Exception as e:
        logger.error(f"An unexpected error occurred while loading {file_path}: {e}")
        return default_data

def _save_data(file_path, data):
    """Saves data to a JSON file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error saving data to {file_path}: {e}")
        return False

# --- Workers Database Functions ---

def load_workers():
    """Loads the workers database."""
    # The workers database is a dictionary where the key is the worker ID
    return _load_data(WORKERS_DB, {})

def save_workers(workers_data):
    """Saves the workers database."""
    return _save_data(WORKERS_DB, workers_data)

def get_worker(worker_id):
    """Retrieves a single worker by ID."""
    workers = load_workers()
    return workers.get(str(worker_id))

def add_or_update_worker(worker_data):
    """Adds a new worker or updates an existing one."""
    workers = load_workers()
    worker_id = str(worker_data.get('id'))
    if not worker_id:
        logger.error("Attempted to add/update worker without an ID.")
        return False
    
    workers[worker_id] = worker_data
    return save_workers(workers)

def delete_worker(worker_id):
    """Deletes a worker by ID."""
    workers = load_workers()
    worker_id = str(worker_id)
    if worker_id in workers:
        del workers[worker_id]
        return save_workers(workers)
    return False

# --- Request Logs Functions ---

def load_request_logs():
    """Loads the request logs database."""
    # The request logs database is a list of log entries
    return _load_data(REQUEST_LOGS_DB, [])

def add_request_log(log_entry):
    """Adds a new log entry to the request logs."""
    logs = load_request_logs()
    logs.insert(0, log_entry) # Insert at the beginning for easier viewing
    # Keep the log file from growing indefinitely (e.g., max 1000 entries)
    if len(logs) > 1000:
        logs = logs[:1000]
    return _save_data(REQUEST_LOGS_DB, logs)

def create_log_entry(api_type, endpoint, success, status_code, request_data, response_data, message=""):
    """Creates a standardized log entry."""
    return {
        "timestamp": datetime.now().isoformat(),
        "api_type": api_type, # e.g., "Supabase", "HikCentral"
        "endpoint": endpoint,
        "success": success,
        "status_code": status_code,
        "message": message,
        "request_data": request_data,
        "response_data": response_data
    }

from datetime import datetime # Re-importing for use in create_log_entry
