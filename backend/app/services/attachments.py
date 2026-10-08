import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.config import settings

MAX_BYTES = 5 * 1024 * 1024
MEDIA_TYPES = {"png": "image/png", "jpg": "image/jpeg", "gif": "image/gif", "webp": "image/webp"}


def detect_image_type(data: bytes) -> str | None:
    """Look at the file's first bytes; the client's Content-Type header can lie."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def save_image(file: UploadFile) -> str:
    data = file.file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "Image must be 5 MB or smaller")
    ext = detect_image_type(data)
    if ext is None:
        raise HTTPException(422, "Only PNG, JPEG, GIF or WEBP images are allowed")
    name = f"{uuid.uuid4().hex}.{ext}"
    folder = Path(settings.upload_dir)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_bytes(data)
    return name


def file_path(name: str) -> Path:
    return Path(settings.upload_dir) / name


def media_type(name: str) -> str:
    return MEDIA_TYPES[name.rsplit(".", 1)[1]]
