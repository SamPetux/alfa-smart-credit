#!/usr/bin/env python3
"""Сверка paths/methods contracts/openapi.yaml ↔ FastAPI app (B10).

Контракт — источник истины для путей. Реализация должна покрывать все
paths+methods из contracts; лишние runtime-пути допускаются (meta и т.п.).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    print("need PyYAML: pip install 'PyYAML==6.0.3'", file=sys.stderr)
    raise SystemExit(2) from exc


def _normalize_app_path(path: str) -> str:
    """/api/v1/applications/{application_id} → /applications/{id}-style contract path."""
    prefix = "/api/v1"
    if path.startswith(prefix):
        path = path[len(prefix) :] or "/"
    # FastAPI: {application_id} vs contract {id}
    path = path.replace("{application_id}", "{id}")
    return path


def main() -> int:
    contract_path = ROOT / "contracts" / "openapi.yaml"
    raw = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    contract_paths: dict[str, set[str]] = {}
    for path, item in (raw.get("paths") or {}).items():
        methods = {m.lower() for m in item if m.lower() in {"get", "post", "put", "patch", "delete"}}
        contract_paths[path] = methods

    from backend.app.main import app

    schema = app.openapi()
    app_paths: dict[str, set[str]] = {}
    for path, item in (schema.get("paths") or {}).items():
        norm = _normalize_app_path(path)
        methods = {m.lower() for m in item if m.lower() in {"get", "post", "put", "patch", "delete"}}
        app_paths.setdefault(norm, set()).update(methods)

    missing: list[str] = []
    for path, methods in sorted(contract_paths.items()):
        have = app_paths.get(path, set())
        for method in sorted(methods):
            if method not in have:
                missing.append(f"{method.upper()} {path}")

    if missing:
        print("OpenAPI drift: contract operations missing in FastAPI:", file=sys.stderr)
        for row in missing:
            print(f"  - {row}", file=sys.stderr)
        return 1

    print(f"openapi contract ok: {sum(len(m) for m in contract_paths.values())} operations covered")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
