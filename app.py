from os import getcwd, remove, system
from os.path import join

from hmac import compare_digest

from yaml import safe_load
from zipfile import ZipFile

from fastapi import FastAPI, Form, Request, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

from typing import Optional

app = FastAPI()

config_path = join(getcwd(), "config.yaml")
with open(config_path, "r") as config_file:
    config = safe_load(config_file)


def is_secret_key(secret_key: str) -> bool:
    return len(secret_key) == 60


def safe_compare(a: str, b: str) -> bool:
    a = a.encode("utf-8")
    b = b.encode("utf-8")
    return compare_digest(a, b)


def file_extension(filename: str) -> Optional[str]:
    if "." not in filename:
        return None
    return filename.rsplit(".", 1)[1].lower()


@app.middleware("http")
async def check_ip_access(request: Request, call_next):
    client_ip = request.client.host
    allowed_ips = config.get("ALLOWED_IPS", ["*"])
    if "*" not in allowed_ips and client_ip not in allowed_ips:
        return JSONResponse(
            content={"message": f"Access denied for IP: {client_ip}"},
            status_code=403,
        )
    return await call_next(request)


@app.get("/", response_class=HTMLResponse)
def index_page():
    return """
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
    """


@app.get("/robots.txt", response_class=PlainTextResponse)
def robots_txt():
    return "User-agent: *\nDisallow: /"


@app.post("/")
async def upload_zip(
    path: str = Form(...),
    password: str = Form(...),
    cmd: Optional[str] = Form(None),
    file: UploadFile = Form(...),
):
    secret_key = config.get("SECRET_KEY")
    is_format_pass = is_secret_key(secret_key) and is_secret_key(password)
    if not (is_format_pass and safe_compare(secret_key, password)):
        raise HTTPException(401, "wrong password")

    if file_extension(file.filename) != "zip":
        raise HTTPException(400, "file is not a zip")

    zip_filepath = file.filename
    with open(zip_filepath, "wb") as f:
        f.write(await file.read())

    with ZipFile(zip_filepath, mode="r") as zf:
        for name in zf.namelist():
            zf.extract(name, path)

    remove(zip_filepath)

    if not cmd:
        return JSONResponse(
            content={"message": "received"},
            status_code=200,
        )

    system(cmd)
    return JSONResponse(
        content={"message": "received and command executed"},
        status_code=200,
    )
