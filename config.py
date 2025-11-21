import os

# --- Project Configuration ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
LOG_FILE = os.path.join(PROJECT_ROOT, "hydepark_sync.log")
DRY_RUN = False

# --- Local Database Files ---
WORKERS_DB = os.path.join(DATA_DIR, "workers.json")
REQUEST_LOGS_DB = os.path.join(DATA_DIR, "request_logs.json")

# --- Supabase API Configuration ---
SUPABASE_BASE_URL = "https://xrkxxqhoglrimiljfnml.supabase.co/functions/v1"
SUPABASE_API_KEY = "XyZ9k2LmN4pQ7rS8tU0vW1xA3bC5dE6f7gH8iJ9kL0mN1o=="
SUPABASE_EVENTS_ENDPOINT = "/make-server-2c3121a9/admin/events/pending"
SUPABASE_COMPLETE_ENDPOINT = "/make-server-2c3121a9/admin/events/{eventId}/complete"
SUPABASE_FAIL_ENDPOINT = "/make-server-2c3121a9/admin/events/{eventId}/fail"
SUPABASE_ADMIN_BEARER = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhya3h4cWhvZ2xyaW1pbGpmbm1sIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI0MjIxMDEsImV4cCI6MjA3Nzk5ODEwMX0.3G20OL9ujCPyFOOMYc6UVbIv97v5LjsWbQLPZaqHRsk"
SUPABASE_UPDATE_STATUS_ENDPOINT = "/make-server-2c3121a9/admin/workers/update-status"

# --- HikCentral API Configuration ---
HIKCENTRAL_BASE_URL = "https://10.127.0.2/artemis"
HIKCENTRAL_APP_KEY = "27820465"
HIKCENTRAL_APP_SECRET = "eaLYrF1t8ZHq9qLKdHJO"
HIKCENTRAL_PRIVILEGE_GROUP_ID = "1"

# --- Polling Service Configuration ---
POLLING_INTERVAL_SECONDS = 60

# --- Web Dashboard Configuration ---
DASHBOARD_HOST = "0.0.0.0"
DASHBOARD_PORT = 8090
DASHBOARD_SECRET_KEY = "super_secret_key_for_session"
DASHBOARD_USERNAME = "admin"
DASHBOARD_PASSWORD = "123456"

# --- Face Recognition Configuration ---
# Threshold for face comparison (lower is stricter)
FACE_RECOGNITION_THRESHOLD = 0.6
# Directory to store worker face images (for comparison)
FACE_IMAGES_DIR = os.path.join(DATA_DIR, "faces")

# Ensure data directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(FACE_IMAGES_DIR, exist_ok=True)
