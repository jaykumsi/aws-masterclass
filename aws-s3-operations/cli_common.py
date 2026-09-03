"""Small command-line helpers shared by the S3 examples."""

from __future__ import annotations

import mimetypes
from pathlib import Path

from botocore.exceptions import BotoCoreError, ClientError, ProfileNotFound


def read_input(file: str | None, text: str | None) -> tuple[bytes, str | None]:
    if (file is None) == (text is None):
        raise ValueError("Supply exactly one of --file or --text")
    if file:
        path = Path(file)
        return path.read_bytes(), mimetypes.guess_type(path.name)[0]
    return text.encode("utf-8"), "text/plain; charset=utf-8"


def run(main) -> None:
    try:
        main()
    except (ValueError, OSError, ClientError, BotoCoreError, ProfileNotFound) as error:
        raise SystemExit(f"ERROR: {error}") from error
