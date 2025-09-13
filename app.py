from os import getcwd, remove, system
from os.path import join

from re import fullmatch

from pathlib import Path
from uuid import uuid4

from logging import getLogger
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

logger = getLogger("kijya")
logger.setLevel(config.get("LOG_LEVEL", "INFO"))


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


def is_cmd_allowed(cmd: str) -> bool:
    allowed_cmds = config.get("ALLOWED_CMDS", ["^.+$"])
    for pattern in allowed_cmds:
        if fullmatch(pattern, cmd):
            return True
    return False


@app.middleware("http")
async def check_ip_access(request: Request, call_next):
    client_ip = request.client.host
    allowed_ips = config.get("ALLOWED_IPS", ["*"])
    if "*" not in allowed_ips and client_ip not in allowed_ips:
        logger.warning(f"Access denied for IP: {client_ip}")
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
                            <input type="text" name="precmd" id="input-precmd" placeholder="Pre-Command" class="form-control" />
                            <label for="input-cmd">Pre-Command</label>
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


def verify_password(input_password: str) -> None:
    secret_key = config.get("SECRET_KEY")
    is_format_pass = is_secret_key(secret_key) and is_secret_key(input_password)
    if not (is_format_pass and safe_compare(secret_key, input_password)):
        logger.warning("Wrong password attempt")
        raise HTTPException(401, "wrong password")


def validate_file(file: UploadFile, raw: bool) -> None:
    if (not raw) and file_extension(file.filename) != "zip":
        logger.warning(f"Invalid file type: {file.filename}")
        raise HTTPException(400, "file is not a zip")


async def save_upload(file: UploadFile, target_path: str, raw: bool) -> str:
    filepath = file.filename if raw else f"j{uuid4()}.zip"
    filepath = join(target_path, filepath) if raw else filepath
    with open(filepath, "wb") as f:
        f.write(await file.read())
    logger.info(f"File saved: {file.filename} as {filepath}")
    return filepath


def extract_zip(zip_filepath: str, target_path: str) -> None:
    untrust_zip = config.get("UNTRUST_ZIP", False)
    with ZipFile(zip_filepath, mode="r") as zf:
        for name in zf.namelist():
            member_path = Path(name)
            if untrust_zip and (member_path.is_absolute() or ".." in member_path.parts):
                logger.warning(f"Unsafe path detected in zip: {name}")
                remove(zip_filepath)
                logger.info(f"Removed temporary file: {zip_filepath}")
                raise HTTPException(400, f"Unsafe path detected in zip: {name}")
            zf.extract(name, target_path)
            logger.info(f"Extracted: {name} to {target_path}")

    remove(zip_filepath)
    logger.info(f"Removed temporary file: {zip_filepath}")


def execute_cmd(cmd: str) -> None:
    if not cmd:
        logger.info("No command to execute")
        return
    if not is_cmd_allowed(cmd):
        logger.warning(f"Command not allowed: {cmd}")
        raise HTTPException(400, f"Command not allowed: {cmd}")
    logger.info(f"Executing command: {cmd}")
    system(cmd)
    logger.info("Command executed")


@app.post("/")
async def upload_zip(
    path: str = Form(...),
    password: str = Form(...),
    file: UploadFile = Form(...),
    precmd: Optional[str] = Form(None),
    cmd: Optional[str] = Form(None),
    raw: Optional[str] = Form(None),
):
    # read config
    raw = config.get("ALLOW_RAW", False) and raw == "true"

    # logging
    logger.info(f"Upload received for path: {path}")
    logger.info(f"Uploaded a f{'raw' if raw else 'zip'} file")

    # verify/validate
    verify_password(password)
    validate_file(file, raw)

    # execute precmd
    execute_cmd(precmd)

    # handle file
    filepath = await save_upload(file, path, raw)

    # handle zip file
    if not raw:
        extract_zip(filepath, path)

    # execute cmd
    execute_cmd(cmd)

    # return
    msg = "received and command executed" if cmd else "received"
    return JSONResponse(content={"message": msg}, status_code=200)


if __name__ == "__main__":
    from uvicorn import run
    from sys import platform

    if platform == "win32":
        system("")

    bind_host = config.get("BIND_HOST", "0.0.0.0")
    bind_port = config.get("BIND_PORT", 8000)
    run_workers = config.get("RUN_WORKERS", 1)
    uvicorn_opts = config.get("UVICORN_OPTS", {})

    logger.info(f"Starting {run_workers} server workers on {bind_host}:{bind_port}")
    run("app:app", host=bind_host, port=bind_port, workers=run_workers, **uvicorn_opts)
