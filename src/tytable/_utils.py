"""Small shared helpers (UUID generation, number-to-string formatting)."""

from __future__ import annotations

import uuid


def _new_image_id() -> str:
    """Return a short random hex id for unique image filenames."""
    return uuid.uuid4().hex[:8]


def format_markup_num(v: object) -> str:
    """Format a typed cell value for markup: ints stay clean, ``1.0`` → ``"1"``, bools → ``"true"/"false"``, ``None`` → ``""``."""
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)
