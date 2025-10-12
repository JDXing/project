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
    return render_template('admin.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        flash('❌ No file part')
        return redirect(url_for('admin'))
    file = request.files['file']
    
    if file.filename == '':
        flash('⚠️ No file selected')
        return redirect(url_for('admin'))
    
    allowed_exts = {'png', 'jpg', 'jpeg', 'mp4', 'mov', 'avi', 'mkv', 'webm'}
    ext = ext = file.filename.rsplit('.', 1)[-1].lower()

    if ext not in allowed_exts:
        flash('🚫 Invalid file type! Only images or videos are allowed.')
        return redirect(url_for('admin'))
    
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
    flash('✅ Image uploaded successfully!')
    return redirect(url_for('admin'))


if __name__ == '__main__':
    app.run(debug=True)
