from os import getcwd, mkdir, remove
from os.path import join, exists

from yaml import full_load
from zipfile import ZipFile

from flask import Flask, request
from werkzeug.utils import secure_filename

from typing import Union

app = Flask(__name__)

config_path = join(getcwd(), "config.yaml")
app.config.from_file(config_path, load=full_load)

if not exists(app.config["UPLOAD_FOLDER"]):
    mkdir(app.config["UPLOAD_FOLDER"])


def file_extention(filename) -> Union[str, None]:
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
                    <input type="text" name="path" required placeholder="Path" />
                    <input type="text" name="password" required placeholder="Password" />
                    <input type="file" name="file" required accept=".zip" />
                    <input type="submit" value="Upload" />
                </form>
            </body>
        </html>
    '''


@app.route('/', methods=['POST'])
def upload_file_handler():
    if 'path' not in request.form \
        or 'password' not in request.form \
            or 'file' not in request.files:
        return "wrong request", 400

    if request.form.get('password') != app.config["SECRET_KEY"]:
        return "wrong password", 401

    file = request.files['file']
    if not file or file.filename == '':
        return "no file in request", 400

    if file_extention(file.filename) != 'zip':
        return "file is not a zip", 400

    zip_filename = secure_filename(file.filename)
    zip_filepath = join(app.config['UPLOAD_FOLDER'], zip_filename)
    file.save(zip_filepath)

    with ZipFile(zip_filepath, mode='r') as zf:
        name_list = zf.namelist()
        for name in name_list:
            zf.extract(name, request.form.get("path"))

    remove(zip_filepath)
    return "received", 201
