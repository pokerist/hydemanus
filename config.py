import os

# --- Project Configuration ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
LOG_FILE = os.path.join(PROJECT_ROOT, "hydepark_sync.log")
DRY_RUN = True

# --- Local Database Files ---
WORKERS_DB = os.path.join(DATA_DIR, "workers.json")
REQUEST_LOGS_DB = os.path.join(DATA_DIR, "request_logs.json")

# --- Supabase API Configuration ---
SUPABASE_BASE_URL = "https://xrkxxqhoglrimiljfnml.supabase.co/functions/v1"
SUPABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." # Placeholder, replace with actual key
SUPABASE_EVENTS_ENDPOINT = "/make-server-2c3121a9/admin/events/pending"
SUPABASE_COMPLETE_ENDPOINT = "/make-server-2c3121a9/admin/events/{eventId}/complete"
SUPABASE_FAIL_ENDPOINT = "/make-server-2c3121a9/admin/events/{eventId}/fail"
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
DASHBOARD_SECRET_KEY = "super_secret_key_for_session" # Change this in production
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
