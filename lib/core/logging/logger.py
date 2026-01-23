"""Logging helpers for MCP server."""

import logging
import os
import sys

from lib.core.constants.app_constants import DEFAULT_LOG_LEVEL


def configure_logger() -> None:
    """Configure root logger to stderr to avoid MCP stdio interference."""
    log_level_name = os.getenv("IOS_SIM_LOG_LEVEL", DEFAULT_LOG_LEVEL).upper()
    log_level = getattr(logging, log_level_name, logging.INFO)
    logging.basicConfig(
        level=log_level,
        stream=sys.stderr,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
