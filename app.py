from flask import Flask, flash, render_template, request, redirect, url_for, session
from functools import wraps
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
load_dotenv()
import os
import json
import uuid

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

UPLOAD_FOLDER = 'static/uploads'
POSTER_FOLDER = 'static/posters'
FACULTY_FOLDER = 'static/faculty'
FACULTY_DATA_FILE = os.path.join(FACULTY_FOLDER, 'faculty.json')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['POSTER_FOLDER'] = POSTER_FOLDER
app.config['FACULTY_FOLDER'] = FACULTY_FOLDER

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['POSTER_FOLDER'], exist_ok=True)
os.makedirs(app.config['FACULTY_FOLDER'], exist_ok=True)

ALLOWED_IMAGE_EXTS = {'png', 'jpg', 'jpeg', 'heic', 'webp'}
ALLOWED_VIDEO_EXTS = {'mp4', 'mov', 'avi', 'webm'}
ALLOWED_EXTS = ALLOWED_IMAGE_EXTS | ALLOWED_VIDEO_EXTS

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            flash("⚠️ You must be logged in as admin.")
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def get_categories():
    """Return list of category subfolder names."""
    base = app.config['UPLOAD_FOLDER']
    return [
        d for d in os.listdir(base)
        if os.path.isdir(os.path.join(base, d))
    ]

def get_posters():
    """Return list of poster filenames."""
    base = app.config['POSTER_FOLDER']
    if not os.path.isdir(base):
        return []
    return [
        f for f in os.listdir(base)
        if os.path.isfile(os.path.join(base, f))
        and f.rsplit('.', 1)[-1].lower() in ALLOWED_IMAGE_EXTS
    ]

def get_teachers():
    """Return list of teacher dicts: [{'name': ..., 'photo': ...}, ...]."""
    if not os.path.isfile(FACULTY_DATA_FILE):
        return []
    try:
        with open(FACULTY_DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []
    except (json.JSONDecodeError, OSError):
        return []

def save_teachers(teachers):
    """Persist the teachers list to disk."""
    with open(FACULTY_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(teachers, f, ensure_ascii=False, indent=2)

@app.route('/')
def home():
    posters = get_posters()
    return render_template('index.html', posters=posters)

@app.route('/aboutus')
def aboutus():
    return render_template('aboutus.html')

@app.route('/contactus')
def contactus():
    return render_template('contactus.html')

@app.route('/galary')
def galary():
    categories = get_categories()
    selected_category = request.args.get('category')
    images = []

    if selected_category and selected_category in categories:
        cat_folder = os.path.join(app.config['UPLOAD_FOLDER'], selected_category)
        images = [
            f for f in os.listdir(cat_folder)
            if f.rsplit('.', 1)[-1].lower() in ALLOWED_EXTS
        ]

    return render_template(
        'galary.html',
        categories=categories,
        selected_category=selected_category,
        images=images
    )

@app.route('/academics')
def academics():
    return render_template('academics.html')

@app.route('/faculty')
def faculty():
    teachers = get_teachers()
    return render_template('faculty.html', teachers=teachers)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == os.getenv("ADMIN_PASSWORD"):
            session['is_admin'] = True
            flash('✅ Logged in successfully as admin!')
            return redirect(url_for('admin'))
        else:
            flash('🚫 Invalid credentials!')
            return redirect(url_for('admin_login'))
    return render_template('admin_login.html')

@app.route('/admin/logout', methods=['POST'])
def admin_logout():
    session.pop('is_admin', None)
    flash('Logged out successfully.')
    return redirect(url_for('home'))

@app.route('/admin')
@admin_required
def admin():
    categories = get_categories()
    # Build a dict: { category: [filenames] } for the remove panel
    cat_images = {}
    for cat in categories:
        cat_folder = os.path.join(app.config['UPLOAD_FOLDER'], cat)
        cat_images[cat] = [
            f for f in os.listdir(cat_folder)
            if f.rsplit('.', 1)[-1].lower() in ALLOWED_EXTS
        ]
    posters = get_posters()
    teachers = get_teachers()
    return render_template(
        'admin.html',
        categories=categories,
        cat_images=cat_images,
        posters=posters,
        teachers=teachers
    )

@app.route('/admin/upload', methods=['POST'])
@admin_required
def upload_image():
    if 'file' not in request.files:
        flash('❌ Missing file in request.', 'gallery')
        return redirect(url_for('admin'))

    # Sanitise category: lowercase, strip spaces, fallback to 'general'
    category = request.form.get('category', '').strip().lower()
    if not category:
        category = 'general'
    # Only allow alphanumeric + underscore/hyphen
    category = ''.join(c for c in category if c.isalnum() or c in ('-', '_'))
    if not category:
        category = 'general'

    cat_folder = os.path.join(app.config['UPLOAD_FOLDER'], category)
    os.makedirs(cat_folder, exist_ok=True)

    files = request.files.getlist('file')
    n = len(files)
    uploaded = 0

    for file in files:
        if file.filename == '':
            flash('⚠️ One file had no name — skipped.', 'gallery')
            continue

        ext = file.filename.rsplit('.', 1)[-1].lower()
        if ext not in ALLOWED_EXTS:
            flash(f'🚫 Invalid file type: {file.filename}', 'gallery')
            continue

        filename = secure_filename(file.filename)
        save_path = os.path.join(cat_folder, filename)
        file.save(save_path)
        uploaded += 1

    flash(f'✅ {uploaded} of {n} file(s) uploaded to "{category}".', 'gallery')
    return redirect(url_for('admin'))

@app.route('/admin/remove', methods=['POST'])
@admin_required
def remove_image():
    # selected_files values are "category/filename"
    selected_files = request.form.getlist('selected_files')

    if not selected_files:
        flash("⚠️ No files selected for deletion!", 'gallery')
        return redirect(url_for('admin'))

    deleted = 0
    base = os.path.abspath(app.config['UPLOAD_FOLDER'])
    for entry in selected_files:
        # Prevent path traversal
        norm = os.path.normpath(entry)
        if norm.startswith('..') or os.path.isabs(norm):
            continue
        path = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], norm))
        if not path.startswith(base):
            continue
        if os.path.isfile(path):
            os.remove(path)
            deleted += 1

    flash(f"🗑️ {deleted} of {len(selected_files)} file(s) deleted.", 'gallery')
    return redirect(url_for('admin'))

@app.route('/admin/poster/upload', methods=['POST'])
@admin_required
def upload_poster():
    if 'poster' not in request.files:
        flash('❌ Missing poster file in request.', 'poster')
        return redirect(url_for('admin'))

    file = request.files['poster']

    if file.filename == '':
        flash('⚠️ No file selected.', 'poster')
        return redirect(url_for('admin'))

    ext = file.filename.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED_IMAGE_EXTS:
        flash(f'🚫 Invalid file type: {file.filename}', 'poster')
        return redirect(url_for('admin'))

    filename = secure_filename(file.filename)
    save_path = os.path.join(app.config['POSTER_FOLDER'], filename)
    file.save(save_path)

    flash('✅ Poster uploaded successfully.', 'poster')
    return redirect(url_for('admin'))

@app.route('/admin/poster/remove', methods=['POST'])
@admin_required
def remove_poster():
    selected_posters = request.form.getlist('selected_posters')

    if not selected_posters:
        flash("⚠️ No posters selected for deletion!", 'poster')
        return redirect(url_for('admin'))

    deleted = 0
    base = os.path.abspath(app.config['POSTER_FOLDER'])
    for entry in selected_posters:
        filename = secure_filename(entry)
        path = os.path.abspath(os.path.join(app.config['POSTER_FOLDER'], filename))
        if not path.startswith(base):
            continue
        if os.path.isfile(path):
            os.remove(path)
            deleted += 1

    flash(f"🗑️ {deleted} of {len(selected_posters)} poster(s) deleted.", 'poster')
    return redirect(url_for('admin'))

@app.route('/admin/faculty/upload', methods=['POST'])
@admin_required
def upload_teacher():
    teacher_name = request.form.get('teacher_name', '').strip()
    if not teacher_name:
        flash('⚠️ Please enter a teacher name.', 'faculty')
        return redirect(url_for('admin'))

    if 'teacher_photo' not in request.files:
        flash('❌ Missing teacher photo in request.', 'faculty')
        return redirect(url_for('admin'))

    file = request.files['teacher_photo']

    if file.filename == '':
        flash('⚠️ No photo selected.', 'faculty')
        return redirect(url_for('admin'))

    ext = file.filename.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED_IMAGE_EXTS:
        flash(f'🚫 Invalid file type: {file.filename}', 'faculty')
        return redirect(url_for('admin'))

    # Generate a unique filename to avoid collisions between teachers
    filename = secure_filename(f"{uuid.uuid4().hex}.{ext}")
    save_path = os.path.join(app.config['FACULTY_FOLDER'], filename)
    file.save(save_path)

    teachers = get_teachers()
    teachers.append({'name': teacher_name, 'photo': filename})
    save_teachers(teachers)

    flash(f'✅ Teacher "{teacher_name}" added.', 'faculty')
    return redirect(url_for('admin'))

@app.route('/admin/faculty/remove', methods=['POST'])
@admin_required
def remove_teacher():
    selected_teachers = request.form.getlist('selected_teachers')

    if not selected_teachers:
        flash("⚠️ No teachers selected for deletion!", 'faculty')
        return redirect(url_for('admin'))

    teachers = get_teachers()
    base = os.path.abspath(app.config['FACULTY_FOLDER'])
    deleted = 0
    remaining = []

    for teacher in teachers:
        photo = teacher.get('photo', '')
        if photo in selected_teachers:
            filename = secure_filename(photo)
            path = os.path.abspath(os.path.join(app.config['FACULTY_FOLDER'], filename))
            if path.startswith(base) and os.path.isfile(path):
                os.remove(path)
            deleted += 1
        else:
            remaining.append(teacher)

    save_teachers(remaining)
    flash(f"🗑️ {deleted} of {len(selected_teachers)} teacher(s) deleted.", 'faculty')
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)