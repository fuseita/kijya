from os import getcwd, mkdir, remove, system
from os.path import join, exists

from yaml import full_load
from zipfile import ZipFile

from flask import Flask, request, make_response
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
def index_page():
    return '''
        <!doctype html>
        <html>
            <head>
                <title>Kijya</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
                <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
            </head>
            <body>
                <div class="px-4 py-5 my-5 text-center">
                    <h1 class="display-5 text-body-emphasis">Kijya</h1>
                    <p class="lead mb-4">利用 ZIP壓縮檔 升級伺服器程式</p>
                    <form method="post" enctype="multipart/form-data" class="mx-auto p-4 p-md-5 border rounded-3 bg-body-tertiary">
                        <div class="form-floating mb-3">
                            <input type="text" name="path" required id="input-path" placeholder="Path" class="form-control" />
                            <label for="input-path">Path</label>
                        </div>
                        <div class="form-floating mb-3">
                            <input type="text" name="password" required id="input-password" placeholder="Password" class="form-control" />
                            <label for="input-password">Password</label>
                        </div>
                        <div class="form-floating mb-3">
                            <input type="text" name="cmd" id="input-cmd" placeholder="Command" class="form-control" />
                            <label for="input-cmd">Command</label>
                        </div>
                        <div class="mb-3">
                            <input type="file" name="file" required accept=".zip" class="form-control" />
                        </div>
                        <div class="form-floating mb-3">
                            <input type="submit" value="Upload" class="w-100 btn btn-lg btn-primary" />
                        </div>
                    </form>
                </div>
            </body>
        </html>
    '''


@app.route('/robots.txt', methods=['GET'])
def robots_txt():
    text = "User-agent: *\nDisallow: /"
    response = make_response(text, 200)
    response.mimetype = "text/plain"
    return response


@app.route('/', methods=['POST'])
def upload_zip():
    if 'path' not in request.form \
        or 'password' not in request.form \
            or 'cmd' not in request.form \
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

    extract_base_path = request.form.get("path")
    with ZipFile(zip_filepath, mode='r') as zf:
        name_list = zf.namelist()
        for name in name_list:
            zf.extract(name, extract_base_path)
    remove(zip_filepath)

    command = request.form.get("cmd")
    if command:
        system(command)
        return "received and loaded", 200
    else:
        return "received", 200
