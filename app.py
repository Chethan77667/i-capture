from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///icapture.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

db = SQLAlchemy(app)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Database Models
class College(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    participants = db.relationship('Participant', backref='college', lazy=True)

class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.String(50), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    college_id = db.Column(db.Integer, db.ForeignKey('college.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploads = db.relationship('FileUpload', backref='participant', lazy=True)

class FileUpload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # 'image' or 'video'
    participant_id = db.Column(db.Integer, db.ForeignKey('participant.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)

# Routes
@app.route('/')
def index():
    # If user is logged in, redirect to their dashboard
    if session.get('user_logged_in'):
        return redirect(url_for('user_dashboard'))
    # If not logged in, redirect to login
    return redirect(url_for('user_login'))

@app.route('/home')
def home():
    return render_template('index.html')

@app.route('/admin')
def admin():
    # If admin is logged in, redirect to admin dashboard
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
    # If not logged in, redirect to admin login
    return redirect(url_for('admin_login'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password_hash, password):
            session['admin_logged_in'] = True
            session['admin_id'] = admin.id
            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials!', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    colleges = College.query.all()
    participants = Participant.query.all()
    return render_template('admin_dashboard.html', colleges=colleges, participants=participants)

@app.route('/admin/add_college', methods=['POST'])
def add_college():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    name = request.form['name']
    if College.query.filter_by(name=name).first():
        flash('College already exists!', 'error')
    else:
        college = College(name=name)
        db.session.add(college)
        db.session.commit()
        flash('College added successfully!', 'success')
    
    return redirect(url_for('admin_dashboard') + '?tab=colleges')

@app.route('/admin/add_participant', methods=['POST'])
def add_participant():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    participant_id = request.form['participant_id']
    name = request.form['name']
    phone = request.form['phone']
    college_id = request.form['college_id']
    
    if Participant.query.filter_by(participant_id=participant_id).first():
        flash('Participant ID already exists!', 'error')
    else:
        participant = Participant(
            participant_id=participant_id,
            name=name,
            phone=phone,
            college_id=college_id
        )
        db.session.add(participant)
        db.session.commit()
        flash('Participant added successfully!', 'success')
    
    return redirect(url_for('admin_dashboard') + '?tab=participants')

@app.route('/admin/participants/<int:participant_id>/delete', methods=['POST'])
def delete_participant(participant_id):
    if not session.get('admin_logged_in'):
        return jsonify(success=False, message='Unauthorized'), 401
    participant = Participant.query.get_or_404(participant_id)
    # Delete files from disk and db
    uploads = FileUpload.query.filter_by(participant_id=participant_id).all()
    base_user_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(participant_id))
    images_folder = os.path.join(base_user_folder, 'images')
    for upload in uploads:
        # Try new structure first
        file_path = os.path.join(images_folder, upload.filename)
        if not os.path.exists(file_path):
            file_path = os.path.join(base_user_folder, upload.filename)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass
        db.session.delete(upload)
    try:
        # Clean up empty images folder and base folder if applicable
        if os.path.isdir(images_folder) and not os.listdir(images_folder):
            os.rmdir(images_folder)
        if os.path.isdir(base_user_folder):
            remaining = [f for f in os.listdir(base_user_folder) if f != 'images' or os.path.isdir(os.path.join(base_user_folder,'images')) and os.listdir(os.path.join(base_user_folder,'images'))]
            if not remaining:
                os.rmdir(base_user_folder)
    except Exception:
        pass
    db.session.delete(participant)
    db.session.commit()
    return jsonify(success=True, message='Participant deleted')

@app.route('/admin/participants/<int:participant_id>/edit', methods=['POST'])
def edit_participant(participant_id):
    if not session.get('admin_logged_in'):
        return jsonify(success=False, message='Unauthorized'), 401
    participant = Participant.query.get_or_404(participant_id)
    data = request.get_json(silent=True) or {}
    name = data.get('name')
    phone = data.get('phone')
    new_pid = data.get('participant_id')
    college_id = data.get('college_id')
    if name:
        participant.name = name
    if phone:
        participant.phone = phone
    if new_pid:
        # Ensure uniqueness
        existing = Participant.query.filter(Participant.participant_id == new_pid, Participant.id != participant_id).first()
        if existing:
            return jsonify(success=False, message='Participant ID already exists'), 400
        participant.participant_id = new_pid
    # College is fixed; ignore incoming college_id updates
    db.session.commit()
    return jsonify(success=True, message='Participant updated')

@app.route('/admin/colleges/<int:college_id>/delete', methods=['POST'])
def delete_college(college_id):
    if not session.get('admin_logged_in'):
        return jsonify(success=False, message='Unauthorized'), 401
    college = College.query.get_or_404(college_id)
    if college.participants:
        return jsonify(success=False, message='Cannot delete college with participants'), 400
    db.session.delete(college)
    db.session.commit()
    return jsonify(success=True, message='College deleted')

@app.route('/admin/colleges/<int:college_id>/edit', methods=['POST'])
def edit_college(college_id):
    if not session.get('admin_logged_in'):
        return jsonify(success=False, message='Unauthorized'), 401
    college = College.query.get_or_404(college_id)
    data = request.get_json(silent=True) or {}
    name = data.get('name')
    if not name:
        return jsonify(success=False, message='Name required'), 400
    # Prevent duplicates
    existing = College.query.filter(College.name == name, College.id != college_id).first()
    if existing:
        return jsonify(success=False, message='College name already exists'), 400
    college.name = name
    db.session.commit()
    return jsonify(success=True, message='College updated')

@app.route('/user/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        participant_id = (request.form['participant_id'] or '').strip()
        phone = (request.form['phone'] or '').strip()
        
        # Case-insensitive lookup for participant_id
        participant = Participant.query.filter(
            db.func.lower(Participant.participant_id) == participant_id.lower(),
            Participant.phone == phone
        ).first()
        
        if participant:
            session['user_logged_in'] = True
            session['participant_id'] = participant.id
            session['participant_name'] = participant.name
            session['college_name'] = participant.college.name
            # Save human-readable participant identifier for folder naming
            session['participant_code'] = participant.participant_id
            flash('Login successful!', 'success')
            return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid credentials!', 'error')
    
    return render_template('user_login.html')

@app.route('/user/dashboard')
def user_dashboard():
    if not session.get('user_logged_in'):
        return redirect(url_for('user_login'))
    
    participant = Participant.query.get(session['participant_id'])
    uploads = FileUpload.query.filter_by(participant_id=participant.id).all()
    
    return render_template('user_dashboard.html', 
                         participant=participant, 
                         uploads=uploads)

@app.route('/user/upload', methods=['POST'])
def upload_file():
    if not session.get('user_logged_in'):
        return redirect(url_for('user_login'))
    
    if 'file' not in request.files:
        flash('No file selected!', 'error')
        return redirect(url_for('user_dashboard'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected!', 'error')
        return redirect(url_for('user_dashboard'))
    
    if file:
        # Create user-specific folder and images subfolder
        # Numeric database id for relations
        participant_id = session.get('participant_id')
        participant_code = session.get('participant_code')
        if not participant_code:
            # Fallback to numeric id if not present
            participant_code = str(participant_id)
        base_user_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(participant_code))
        images_folder = os.path.join(base_user_folder, 'images')
        os.makedirs(images_folder, exist_ok=True)
        
        # Get next file number
        existing_files = FileUpload.query.filter_by(participant_id=participant_id).count()
        file_number = existing_files + 1
        
        # Determine file type
        file_type = 'image' if file.content_type.startswith('image/') else 'video'
        
        # Generate filename as numeric sequence (e.g., 1.jpg, 2.png)
        file_extension = os.path.splitext(file.filename)[1]
        filename = f"{file_number}{file_extension}"
        
        # Save file inside images folder (as requested structure)
        file_path = os.path.join(images_folder, filename)
        file.save(file_path)
        
        # Save to database
        upload = FileUpload(
            filename=filename,
            original_filename=file.filename,
            file_type=file_type,
            participant_id=participant_id
        )
        db.session.add(upload)
        db.session.commit()
        
        flash('File uploaded successfully!', 'success')
    
    return redirect(url_for('user_dashboard'))

@app.route('/user/view')
def view_files():
    if not session.get('user_logged_in'):
        return redirect(url_for('user_login'))
    
    participant = Participant.query.get(session['participant_id'])
    uploads = FileUpload.query.filter_by(participant_id=participant.id).all()
    
    return render_template('view_files.html', uploads=uploads, participant=participant)

@app.route('/admin/files')
def admin_files():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    participants = Participant.query.all()
    return render_template('admin_files.html', participants=participants)

@app.route('/admin/files/<int:participant_id>')
def admin_participant_files(participant_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    participant = Participant.query.get_or_404(participant_id)
    uploads = FileUpload.query.filter_by(participant_id=participant_id).all()
    
    return render_template('admin_participant_files.html', 
                         participant=participant, 
                         uploads=uploads)

@app.route('/admin/upload/<int:upload_id>/delete', methods=['POST'])
def admin_delete_upload(upload_id):
    if not session.get('admin_logged_in'):
        return jsonify(success=False, message='Unauthorized'), 401
    upload = FileUpload.query.get_or_404(upload_id)
    participant_id = upload.participant_id
    participant = Participant.query.get(participant_id)
    participant_code = participant.participant_id if participant else str(participant_id)
    # Try both new (participant_code) and legacy (numeric id) folder structures
    candidate_paths = [
        os.path.join(app.config['UPLOAD_FOLDER'], str(participant_code), 'images', upload.filename),
        os.path.join(app.config['UPLOAD_FOLDER'], str(participant_code), upload.filename),
        os.path.join(app.config['UPLOAD_FOLDER'], str(participant_id), 'images', upload.filename),
        os.path.join(app.config['UPLOAD_FOLDER'], str(participant_id), upload.filename),
    ]
    for p in candidate_paths:
        try:
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            pass
    db.session.delete(upload)
    db.session.commit()
    return jsonify(success=True)

@app.route('/user/upload/<int:upload_id>/delete', methods=['POST'])
def user_delete_upload(upload_id):
    if not session.get('user_logged_in'):
        return jsonify(success=False, message='Unauthorized'), 401
    upload = FileUpload.query.get_or_404(upload_id)
    # Ensure the upload belongs to the logged-in user
    if upload.participant_id != session.get('participant_id'):
        return jsonify(success=False, message='Forbidden'), 403
    participant_id = upload.participant_id
    participant = Participant.query.get(participant_id)
    participant_code = session.get('participant_code') or (participant.participant_id if participant else str(participant_id))
    # Try multiple possible file locations
    candidate_paths = [
        os.path.join(app.config['UPLOAD_FOLDER'], str(participant_code), 'images', upload.filename),
        os.path.join(app.config['UPLOAD_FOLDER'], str(participant_code), upload.filename),
        os.path.join(app.config['UPLOAD_FOLDER'], str(participant_id), 'images', upload.filename),
        os.path.join(app.config['UPLOAD_FOLDER'], str(participant_id), upload.filename),
    ]
    deleted_from_disk = False
    for p in candidate_paths:
        try:
            if os.path.exists(p):
                os.remove(p)
                deleted_from_disk = True
                break
        except Exception:
            pass
    # Remove from database regardless of disk deletion success to keep UI consistent
    db.session.delete(upload)
    db.session.commit()
    return jsonify(success=True, removed=deleted_from_disk)

@app.route('/uploads/<participant_folder>/<filename>')
def uploaded_file(participant_folder, filename):
    # Prefer new structure: uploads/<id>/images/<filename>
    images_path = os.path.join(app.config['UPLOAD_FOLDER'], str(participant_folder), 'images', filename)
    if os.path.exists(images_path):
        return send_file(images_path)
    # Backward compatibility: old structure uploads/<id>/<filename>
    legacy_path = os.path.join(app.config['UPLOAD_FOLDER'], str(participant_folder), filename)
    return send_file(legacy_path)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('user_login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create default admin if not exists
        if not Admin.query.filter_by(username='admin').first():
            admin = Admin(
                username='admin',
                password_hash=generate_password_hash('admin123')
            )
            db.session.add(admin)
            db.session.commit()
    
    app.run(debug=True)
