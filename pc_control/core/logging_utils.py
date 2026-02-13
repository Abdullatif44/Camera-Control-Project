from __future__ import annotations

from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler


def configure_logging(level: str, path: str, rotation_megabytes: int, backup_count: int) -> None:
    log_path = Path(path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level.upper())

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root.addHandler(console)

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=rotation_megabytes * 1024 * 1024,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
