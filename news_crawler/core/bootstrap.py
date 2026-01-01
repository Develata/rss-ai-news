from __future__ import annotations

import logging

from dotenv import find_dotenv, load_dotenv

logger = logging.getLogger(__name__)


def bootstrap(dotenv_path: str | None = None, *, override: bool = False) -> str | None:
    """Load environment variables from a .env file.

    Treats the current working directory as the project root.

    Returns the resolved dotenv path if found & loaded, else None.
    """
    resolved = dotenv_path or find_dotenv(usecwd=True)
    if not resolved:
        logger.warning(".env file not found, using system environment variables")
        logger.info("Ensure DB_URI, AI_API_KEY, etc. are configured in environment")
        return None

    load_dotenv(resolved, override=override)
    logger.info(f"Loaded environment configuration from: {resolved}")
    return resolved
