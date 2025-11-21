from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from functools import wraps
import logging
from config import DASHBOARD_SECRET_KEY, DASHBOARD_USERNAME, DASHBOARD_PASSWORD, POLLING_INTERVAL_SECONDS
from database import load_workers, load_request_logs
import json
import os

logger = logging.getLogger('HydeParkSync.Dashboard')

# Initialize Flask App
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = DASHBOARD_SECRET_KEY

# --- Authentication Decorator ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# --- Routes ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == DASHBOARD_USERNAME and password == DASHBOARD_PASSWORD:
            session['logged_in'] = True
            session['username'] = username
            logger.info(f"User {username} logged in successfully.")
            return redirect(request.args.get('next') or url_for('dashboard'))
        else:
            return render_template('login.html', error='اسم المستخدم أو كلمة المرور غير صحيحة.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    logger.info("User logged out.")
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    workers = load_workers()
    logs = load_request_logs()
    
    # Calculate basic stats
    total_workers = len(workers)
    total_logs = len(logs)
    
    # Get last 5 logs
    latest_logs = logs[:5]
    
    stats = {
        "total_workers": total_workers,
        "total_logs": total_logs,
        "polling_interval": POLLING_INTERVAL_SECONDS
    }
    
    return render_template('dashboard.html', stats=stats, latest_logs=latest_logs)

@app.route('/workers')
@login_required
def workers_view():
    workers = load_workers()
    # Convert dict of workers to a list for easier template iteration
    workers_list = list(workers.values())
    return render_template('workers.html', workers=workers_list)

@app.route('/api-logs')
@login_required
def api_logs():
    logs = load_request_logs()
    return render_template('api_logs.html', logs=logs)

@app.route('/settings')
@login_required
def settings_view():
    # Load config data to display (excluding secrets)
    from config import HIKCENTRAL_BASE_URL, SUPABASE_BASE_URL, POLLING_INTERVAL_SECONDS, WORKERS_DB, REQUEST_LOGS_DB
    
    settings = {
        "HIKCENTRAL_BASE_URL": HIKCENTRAL_BASE_URL,
        "SUPABASE_BASE_URL": SUPABASE_BASE_URL,
        "POLLING_INTERVAL_SECONDS": POLLING_INTERVAL_SECONDS,
        "WORKERS_DB_PATH": WORKERS_DB,
        "REQUEST_LOGS_DB_PATH": REQUEST_LOGS_DB,
        "DASHBOARD_PORT": app.config.get('SERVER_NAME', '').split(':')[-1] if app.config.get('SERVER_NAME') else 8080
    }
    
    return render_template('settings.html', settings=settings)

@app.route('/api/stats')
@login_required
def api_stats():
    workers = load_workers()
    logs = load_request_logs()
    
    stats = {
        "total_workers": len(workers),
        "total_logs": len(logs),
        "last_log_timestamp": logs[0]['timestamp'] if logs else "N/A"
    }
    return jsonify(stats)

# Create static directory for CSS/JS
os.makedirs(os.path.join(app.root_path, 'static'), exist_ok=True)
os.makedirs(os.path.join(app.root_path, 'templates'), exist_ok=True)
