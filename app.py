from flask import Flask, flash, render_template, request, redirect, url_for, session
from functools import wraps
from dotenv import load_dotenv
load_dotenv()
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args,**kwargs):
        if not session.get('is_admin'):
            flash("⚠️ You must be logged in as admin.")
            return redirect(url_for('admin_login'))
        return f(*args,**kwargs)
    return decorated_function

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
    images = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('galary.html', images=images)

@app.route('/academics')
def academics():
    return render_template('academics.html')

@app.route('/faculty')
def faculty():
    return render_template('faculty.html')

@app.route('/admin/login',methods=['GET','POST'])
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
    images = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('admin.html', images=images)

@app.route('/admin/upload', methods=['POST'])
@admin_required
def upload_image():
    if 'file' not in request.files:
        flash('❌ Missing key variable file')
        return redirect(url_for('admin'))
    
    files = request.files.getlist('file')
    n = len(files)
    allowed_exts = {'png', 'jpg', 'jpeg', 'heic'}
    i=0
    
    for file in files:    
        if file.filename == '':
            flash('⚠️ file has no name')
            continue  
    
        ext = file.filename.rsplit('.', 1)[-1].lower()

        if ext not in allowed_exts:
            flash(f'🚫 Invalid file type! {file.filename}.')
            continue
        
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
        i=i+1
        
    flash(f'✅ {i} out of {n} files uploaded ')
    return redirect(url_for('admin'))

@app.route('/admin/remove', methods=['POST'])
@admin_required
def remove_image():
    selected_files=request.form.getlist('selected_files')
    
    if len(selected_files) == 0:
        flash("⚠️ No files selected for deletion!")
        return redirect(url_for('admin'))

    c=0
    for filename in selected_files:
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(path):
            os.remove(path)
            c=c+1
    flash(f"🗑️ {c} out of {len(selected_files)} file(s) deleted successfully.")
    return redirect(url_for('admin'))
    

if __name__ == '__main__':
    app.run(debug=True)
