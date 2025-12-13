from __future__ import annotations

from dotenv import find_dotenv, load_dotenv


def bootstrap(dotenv_path: str | None = None, *, override: bool = False) -> str | None:
    """Load environment variables from a .env file.

    Treats the current working directory as the project root ("code/").

    Returns the resolved dotenv path if found & loaded, else None.
    """
    resolved = dotenv_path or find_dotenv(usecwd=True)
    if not resolved:
        return None

    load_dotenv(resolved, override=override)
    return resolved
