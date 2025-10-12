from flask import Flask, flash, render_template, request, redirect, url_for
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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

@app.route('/admin')
def admin():
    images = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('admin.html', images=images)

@app.route('/admin/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        flash('❌ Missing key variable file')
        return redirect(url_for('admin'))
    
    files = request.files.getlist('file')
    n = len(files)
    allowed_exts = {'png', 'jpg', 'jpeg', 'mp4', 'mov', 'avi', 'mkv', 'webm'}
    i=0
    
    for file in files:    
        if file.filename == '':
            flash('⚠️ file has no name')
            continue  
    
        ext =file.filename.rsplit('.', 1)[-1].lower()

        if ext not in allowed_exts:
            flash(f'🚫 Invalid file type! {file.filename}.')
            continue
    
        i=i+1
        
    flash(f'✅ {i} out of {n} files uploaded ')
    return redirect(url_for('admin'))

@app.route('/admin/remove', methods=['POST'])
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
