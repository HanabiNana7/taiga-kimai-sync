import logging
import sys

from taiga_kimai_sync.core.config import get_settings


def configure_logging() -> None:
    settings = get_settings()

    logging.basicConfig(
        level=settings.log_level.upper(),
        format=("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"),
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
