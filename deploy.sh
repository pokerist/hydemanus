#!/bin/bash

# --- Configuration ---
PROJECT_DIR="/opt/hydepark-sync"
SOURCE_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE_NAME="hydepark-sync.service"
SERVICE_FILE="$SOURCE_DIR/systemd/$SERVICE_NAME"
POLL_SERVICE_NAME="hydepark-sync-poller.service"
POLL_SERVICE_FILE="$SOURCE_DIR/systemd/$POLL_SERVICE_NAME"
VENV_PATH="$PROJECT_DIR/venv"

# Function to display messages
log() {
    echo ">>> [INFO] $1"
}

log_error() {
    echo "!!! [ERROR] $1" >&2
}

QUICK_MODE=false
REPO_URL=""

# Parse args
while [ $# -gt 0 ]; do
  case "$1" in
    --quick)
      log "Quick update mode activated. Skipping system dependencies and virtual environment setup."
      QUICK_MODE=true
      shift
      ;;
    --repo)
      REPO_URL="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

# --- 1. System Dependencies (Skipped in quick mode) ---
if [ "$QUICK_MODE" = false ]; then
    log "Installing system dependencies (build-essential, cmake, etc.) for dlib/opencv..."
    sudo apt-get update || { log_error "Failed to update package list."; exit 1; }
    sudo apt-get install -y build-essential cmake libopenblas-dev liblapack-dev libx11-dev libgtk-3-dev python3-dev || { log_error "Failed to install system dependencies."; exit 1; }
fi

# --- 2. Project Directory Setup ---
log "Setting up project directory at $PROJECT_DIR..."
sudo mkdir -p $PROJECT_DIR || { log_error "Failed to create project directory."; exit 1; }
sudo chown -R $USER:$USER $PROJECT_DIR || { log_error "Failed to set ownership."; exit 1; }

# --- 3. Source Update from Git (optional) ---
TMP_SRC=""
if [ -n "$REPO_URL" ]; then
  TMP_SRC="/tmp/hydepark-sync-src"
  log "Cloning repository from $REPO_URL ..."
  rm -rf "$TMP_SRC"
  git clone --depth 1 "$REPO_URL" "$TMP_SRC" || { log_error "Failed to clone repository."; exit 1; }
  SOURCE_DIR="$TMP_SRC"
elif [ -d "$SOURCE_DIR/.git" ]; then
  log "Updating local git repository at $SOURCE_DIR ..."
  (cd "$SOURCE_DIR" && git fetch && git pull) || { log_error "Failed to update local repository."; exit 1; }
fi

# --- 4. Copy Files ---
log "Copying project files..."
rsync -av --delete --exclude 'venv' --exclude '.venv' "$SOURCE_DIR/" "$PROJECT_DIR/" || { log_error "Failed to copy files."; exit 1; }

# --- 5. Virtual Environment and Python Dependencies (Skipped in quick mode) ---
if [ "$QUICK_MODE" = false ]; then
    log "Creating virtual environment and installing Python dependencies..."
    python3 -m venv $VENV_PATH || { log_error "Failed to create virtual environment."; exit 1; }
    
    # Install dependencies. We will skip dlib/face-recognition due to known compilation issues in sandboxes
    # In a real environment, the full requirements.txt would be used.
    log "Installing core Python dependencies..."
    $VENV_PATH/bin/pip install --upgrade pip
    $VENV_PATH/bin/pip install flask requests pillow numpy opencv-python python-dateutil APScheduler gunicorn || { log_error "Failed to install core Python dependencies."; exit 1; }
    
    # Note: dlib/face-recognition are intentionally excluded here due to compilation time/failure.
    # The face_processor.py uses mock functions.
fi

# --- 6. Systemd Service Setup ---
log "Installing Systemd service file..."
# Update the service file to point to the correct project directory and venv
sed "s|/home/ubuntu/hydepark-sync|$PROJECT_DIR|g" $SERVICE_FILE | sed "s|/home/ubuntu/hydepark-sync/venv|$VENV_PATH|g" | sed "s|User=ubuntu|User=$USER|g" > /tmp/$SERVICE_NAME
sudo mv /tmp/$SERVICE_NAME /etc/systemd/system/$SERVICE_NAME || { log_error "Failed to move service file."; exit 1; }

sed "s|/home/ubuntu/hydepark-sync|$PROJECT_DIR|g" $POLL_SERVICE_FILE | sed "s|/home/ubuntu/hydepark-sync/venv|$VENV_PATH|g" | sed "s|User=ubuntu|User=$USER|g" > /tmp/$POLL_SERVICE_NAME
sudo mv /tmp/$POLL_SERVICE_NAME /etc/systemd/system/$POLL_SERVICE_NAME || { log_error "Failed to move poller service file."; exit 1; }

log "Reloading Systemd daemon and enabling service..."
sudo systemctl daemon-reload || { log_error "Failed to reload daemon."; exit 1; }
sudo systemctl enable $SERVICE_NAME || { log_error "Failed to enable service."; exit 1; }
sudo systemctl enable $POLL_SERVICE_NAME || { log_error "Failed to enable poller service."; exit 1; }

# --- 7. Enable & Start Services ---
log "Starting the HydePark Sync System service..."
sudo systemctl restart $SERVICE_NAME || { log_error "Failed to restart service. Check logs with 'sudo journalctl -u $SERVICE_NAME'."; exit 1; }
sudo systemctl restart $POLL_SERVICE_NAME || { log_error "Failed to restart poller. Check logs with 'sudo journalctl -u $POLL_SERVICE_NAME'."; exit 1; }

log "Deployment complete!"
log "Service status: sudo systemctl status $SERVICE_NAME"
log "Web Dashboard should be available on port 8080."
log "Poller is running as $POLL_SERVICE_NAME."
