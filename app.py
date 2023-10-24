from os import getcwd, mkdir
from os.path import join, exists

from flask import Flask, request
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = join(getcwd(), "upload")
ALLOWED_EXTENSIONS = {'zip'}

if not exists(UPLOAD_FOLDER):
    mkdir(UPLOAD_FOLDER)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def file_extention(filename) -> str | None:
    if '.' not in filename:
        return None
    return filename.rsplit('.', 1)[1].lower()

@app.route('/', methods=['GET'])
def upload_file_page():
    return '''
        <!doctype html>
        <html>
            <head>
                <title>Upload zip file</title>
            </head>
            <body>
                <h1>Upload zip file</h1>
                <form method="post" enctype="multipart/form-data">
                    <input type="file" name="file" />
                    <input type="submit" value="Upload" />
                </form>
            </body>
        </html>
    '''

@app.route('/', methods=['POST'])
def upload_file_handler():
    if 'file' not in request.files:
        return "bad request", 400

    file = request.files['file']
    if not file or file.filename == '':
        return "bad request", 400

    if file_extention(file.filename) != 'zip':
        return "bad request", 400

    dist_filename = secure_filename(file.filename)
    dist_filepath = join(app.config['UPLOAD_FOLDER'], dist_filename)
    file.save(dist_filepath)

    return "received", 201
