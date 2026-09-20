"""Local-disk storage for the original knowledge-base files (replaces the Supabase bucket)."""

import shutil
from pathlib import Path

from utils.config import Config


def _resolve(storage_name: str) -> Path:
    root = Path(Config.FILE_STORAGE_DIR)
    root.mkdir(parents=True, exist_ok=True)
    # Only the final path component is honoured, so stored names can't escape the root.
    return root / Path(storage_name).name


def save_file(local_file_path: str, storage_name: str) -> str:
    target = _resolve(storage_name)
    shutil.copyfile(local_file_path, target)
    return str(target)


def remove_file(storage_name: str) -> None:
    _resolve(storage_name).unlink(missing_ok=True)
