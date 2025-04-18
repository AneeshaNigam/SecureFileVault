from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from utils.s3_utils import upload_to_s3, allowed_file, generate_presigned_url, revoke_access, get_file_metadata
from config import Config
import os
from datetime import datetime, timedelta
from functools import wraps
from dotenv import load_dotenv
load_dotenv()  # Add this before app = Flask(__name__)

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

# --- Advanced Feature 1: Rate Limiting ---
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
limiter = Limiter(app=app, key_func=get_remote_address)

# --- Advanced Feature 2: Authentication Decorator ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@limiter.limit("10 per minute")
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['password'] == Config.ADMIN_PASSWORD:
            session['logged_in'] = True
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        flash('Invalid credentials', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/upload', methods=['POST'])
@login_required
@limiter.limit("5 per minute")
def upload_file():
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('index'))
    
    if not allowed_file(file.filename):
        flash('File type not allowed', 'error')
        return redirect(url_for('index'))
    
    try:
        custom_expiry = int(request.form.get('expiry', 3600))  # Advanced Feature 3: Custom Expiry
        upload_result = upload_to_s3(file)
        download_url = generate_presigned_url(upload_result['s3_key'], expiration=custom_expiry)
        
        # Advanced Feature 4: File Metadata Tracking
        file_metadata = {
            'original_name': upload_result['filename'],
            'uploader_ip': request.remote_addr,
            'expiry_time': (datetime.now() + timedelta(seconds=custom_expiry)).strftime("%Y-%m-%d %H:%M:%S"),
            'download_count': 0
        }
        
        return render_template('success.html',
                            filename=upload_result['filename'],
                            file_url=download_url,
                            upload_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            metadata=file_metadata)
    except Exception as e:
        flash(f'Upload failed: {str(e)}', 'error')
        return redirect(url_for('index'))

# Advanced Feature 5: File Management Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True)