import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = Path(os.getenv("DATA_DIR", str(PROJECT_ROOT / "data")))
UPLOADS_DIR = Path(os.getenv("UPLOAD_DIR", str(PROJECT_ROOT / "Upload")))

def create_folders() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)