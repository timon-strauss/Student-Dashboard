import os
from pathlib import Path

from sqlalchemy.orm import declarative_base

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = Path(os.getenv("DATA_DIR", str(PROJECT_ROOT / "data")))
UPLOADS_DIR = Path(os.getenv("UPLOAD_DIR", str(PROJECT_ROOT / "Upload")))

Base = declarative_base()
