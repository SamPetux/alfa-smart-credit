#!/usr/bin/env python3
"""Записать contracts/openapi.json из FastAPI (snapshot для drift/ручной сверки)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.main import app  # noqa: E402


def main() -> int:
    out = ROOT / "contracts" / "openapi.json"
    payload = app.openapi()
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
