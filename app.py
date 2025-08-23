from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/aboutus.html')
def aboutus():
    return render_template('aboutus.html')

@app.route('/contactus')
def contactus():
    return render_template('contactus.html')

@app.route('/academics')
def academics():
    return render_template('academics.html')

if __name__ == '__main__':
    app.run(debug=True)
