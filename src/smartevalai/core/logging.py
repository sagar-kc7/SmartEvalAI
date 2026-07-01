"""Structured logging configuration using Loguru."""

import sys

from loguru import logger

from smartevalai.core.config import get_settings


def configure_logging() -> None:
    """Configure Loguru sinks for the application."""
    settings = get_settings()

    logger.remove()

    logger.add(
        sys.stderr,
        level="DEBUG" if settings.debug else "INFO",
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> "
            "- <level>{message}</level>"
        ),
        colorize=True,
    )

    if settings.environment == "production":
        logger.add(
            "logs/smartevalai.jsonl",
            level="INFO",
            serialize=True,
            rotation="50 MB",
            retention="30 days",
            enqueue=True,
        )