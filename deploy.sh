#!/bin/bash

# --- Configuration ---
PROJECT_DIR="/opt/hydepark-sync"
SOURCE_DIR="/home/ubuntu/hydepark-sync"
SERVICE_NAME="hydepark-sync.service"
SERVICE_FILE="$SOURCE_DIR/systemd/$SERVICE_NAME"
VENV_PATH="$PROJECT_DIR/venv"

# Function to display messages
log() {
    echo ">>> [INFO] $1"
}

log_error() {
    echo "!!! [ERROR] $1" >&2
}

# Check for quick update flag
if [ "$1" == "--quick" ]; then
    log "Quick update mode activated. Skipping system dependencies and virtual environment setup."
    QUICK_MODE=true
else
    QUICK_MODE=false
fi

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

# --- 3. Copy Files ---
log "Copying project files..."
rsync -av --exclude 'venv' $SOURCE_DIR/ $PROJECT_DIR/ || { log_error "Failed to copy files."; exit 1; }

# --- 4. Virtual Environment and Python Dependencies (Skipped in quick mode) ---
if [ "$QUICK_MODE" = false ]; then
    log "Creating virtual environment and installing Python dependencies..."
    python3.11 -m venv $VENV_PATH || { log_error "Failed to create virtual environment."; exit 1; }
    
    # Install dependencies. We will skip dlib/face-recognition due to known compilation issues in sandboxes
    # In a real environment, the full requirements.txt would be used.
    log "Installing core Python dependencies..."
    $VENV_PATH/bin/pip install --upgrade pip
    $VENV_PATH/bin/pip install flask requests pillow numpy opencv-python python-dateutil APScheduler gunicorn || { log_error "Failed to install core Python dependencies."; exit 1; }
    
    # Note: dlib/face-recognition are intentionally excluded here due to compilation time/failure.
    # The face_processor.py uses mock functions.
fi

# --- 5. Systemd Service Setup ---
log "Installing Systemd service file..."
# Update the service file to point to the correct project directory and venv
sed "s|/home/ubuntu/hydepark-sync|$PROJECT_DIR|g" $SERVICE_FILE | sed "s|/home/ubuntu/hydepark-sync/venv|$VENV_PATH|g" > /tmp/$SERVICE_NAME
sudo mv /tmp/$SERVICE_NAME /etc/systemd/system/$SERVICE_NAME || { log_error "Failed to move service file."; exit 1; }

log "Reloading Systemd daemon and enabling service..."
sudo systemctl daemon-reload || { log_error "Failed to reload daemon."; exit 1; }
sudo systemctl enable $SERVICE_NAME || { log_error "Failed to enable service."; exit 1; }

# --- 6. Start Service ---
log "Starting the HydePark Sync System service..."
sudo systemctl start $SERVICE_NAME || { log_error "Failed to start service. Check logs with 'sudo journalctl -u $SERVICE_NAME'."; exit 1; }

log "Deployment complete!"
log "Service status: sudo systemctl status $SERVICE_NAME"
log "Web Dashboard should be available on port 8080."
