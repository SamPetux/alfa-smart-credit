from decimal import Decimal

from backend.app.risk.money import (
    floor_to_step,
    max_principal_for_payment,
    monthly_payment,
)


def test_g02_payment_reference() -> None:
    payment = monthly_payment(Decimal("641000.00"), Decimal("0.22"), 12)
    assert payment == Decimal("59994.00")


def test_floor_step() -> None:
    assert floor_to_step(Decimal("641064.13"), Decimal("1000")) == Decimal("641000.00")


def test_p_max_positive() -> None:
    # A_max = 60000 for G02-like cashflow at DSCR 1.25
    p = max_principal_for_payment(Decimal("60000"), Decimal("0.22"), 12)
    assert p > Decimal("641000")
    assert p < Decimal("641100")
