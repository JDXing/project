@app.route('/upload', methods=['POST'])
def remove_image():
    images = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('galary.html', images=images)