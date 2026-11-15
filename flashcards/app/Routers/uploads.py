from pathlib import PurePath

from fastapi import APIRouter, HTTPException, UploadFile, status

from ._stub import not_implemented

router = APIRouter(prefix="/uploads", tags=["uploads"])

ALLOWED_CONTENT_TYPES = {
    "image/png",
    "image/jpeg",
    "image/gif",
    "image/webp",
    "image/heic",
    "image/heif",
    "image/heic-sequence",
    "image/heif-sequence",
    "image/avif",
    "image/bmp",
    "image/tiff",
}

ALLOWED_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".heic",
    ".heif",
    ".avif",
    ".bmp",
    ".tif",
    ".tiff",
}


def _is_allowed_image(file: UploadFile) -> bool:
    if file.content_type in ALLOWED_CONTENT_TYPES:
        return True
    extension = PurePath(file.filename or "").suffix.lower()
    return extension in ALLOWED_EXTENSIONS


@router.post("/images", response_model=str, status_code=status.HTTP_201_CREATED)
def upload_image(file: UploadFile) -> str:
    if not _is_allowed_image(file):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported image type: {file.content_type}",
        )
    not_implemented()
