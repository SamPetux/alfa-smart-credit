"""Загрузка и доступ к версионированной policy-v1 (JSON). Без сети/БД."""

from __future__ import annotations

import json
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import Any

POLICY_VERSION = "policy-v1"
MODEL_VERSION = "score-v1"

_CONTRACTS = Path(__file__).resolve().parents[3] / "contracts" / "schemas" / "policy-v1.json"


class PolicyError(ValueError):
    """Повреждённый или неизвестный policy-контракт — техническая ошибка."""


@lru_cache(maxsize=4)
def load_policy(path: str | None = None) -> dict[str, Any]:
    policy_path = Path(path) if path else _CONTRACTS
    if not policy_path.is_file():
        raise PolicyError(f"Policy file not found: {policy_path}")
    data = json.loads(policy_path.read_text(encoding="utf-8"))
    if data.get("version") != POLICY_VERSION:
        raise PolicyError(
            f"Unsupported policy version {data.get('version')!r}; expected {POLICY_VERSION}"
        )
    return data


def product_cfg(policy: dict[str, Any], product_code: str) -> dict[str, Any]:
    products = policy.get("products") or {}
    cfg = products.get(product_code)
    if cfg is None:
        raise PolicyError(f"Unknown product_code: {product_code}")
    return cfg


def d(value: str | Decimal) -> Decimal:
    return Decimal(str(value))


def band_for_score(policy: dict[str, Any], score: int) -> str:
    bands = policy["score_bands"]
    if score >= bands["A"]["min"]:
        return "A"
    if score >= bands["B"]["min"]:
        return "B"
    return "C"


def rate_for_band(product: dict[str, Any], band: str) -> Decimal:
    rates = product["rates"]
    if band not in rates:
        raise PolicyError(f"No rate for band {band}")
    return d(rates[band])


def dscr_threshold(product: dict[str, Any], band: str) -> Decimal:
    thresholds = product["dscr_min"]
    if band not in thresholds:
        raise PolicyError(f"No DSCR threshold for band {band}")
    return d(thresholds[band])
