from __future__ import annotations

import uuid


def _new_image_id() -> str:
    return uuid.uuid4().hex[:8]


def format_markup_num(v: object) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)
