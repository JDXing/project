from flask import Flask, render_template
import os

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] ='static/uploads'
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
    return render_template('galary.html',images=images)

@app.route('/academics')
def academics():
    return render_template('academics.html')

if __name__ == '__main__':
    app.run(debug=True)
