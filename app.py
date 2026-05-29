from flask import Flask, flash, render_template, request, redirect, url_for, session
from functools import wraps
from dotenv import load_dotenv
load_dotenv()
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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

@app.route('/')
def home():
    return render_template('index.html')

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
    return render_template('faculty.html')

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
    return render_template('admin.html', categories=categories, cat_images=cat_images)

@app.route('/admin/upload', methods=['POST'])
@admin_required
def upload_image():
    if 'file' not in request.files:
        flash('❌ Missing file in request.')
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
            flash('⚠️ One file had no name — skipped.')
            continue

        ext = file.filename.rsplit('.', 1)[-1].lower()
        if ext not in ALLOWED_EXTS:
            flash(f'🚫 Invalid file type: {file.filename}')
            continue

        save_path = os.path.join(cat_folder, file.filename)
        file.save(save_path)
        uploaded += 1

    flash(f'✅ {uploaded} of {n} file(s) uploaded to "{category}".')
    return redirect(url_for('admin'))

@app.route('/admin/remove', methods=['POST'])
@admin_required
def remove_image():
    # selected_files values are "category/filename"
    selected_files = request.form.getlist('selected_files')

    if not selected_files:
        flash("⚠️ No files selected for deletion!")
        return redirect(url_for('admin'))

    deleted = 0
    for entry in selected_files:
        path = os.path.join(app.config['UPLOAD_FOLDER'], entry)
        if os.path.isfile(path):
            os.remove(path)
            deleted += 1

    flash(f"🗑️ {deleted} of {len(selected_files)} file(s) deleted.")
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)