"""Хеши кандидатов и снимков для сверки officer approve."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_hash(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
