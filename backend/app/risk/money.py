"""Decimal-расчёты платежа, DSCR и доступной суммы. Без float."""

from __future__ import annotations

from decimal import ROUND_CEILING, ROUND_DOWN, ROUND_HALF_UP, Decimal

TWOPLACES = Decimal("0.01")
ZERO = Decimal("0")


def money(value: Decimal | str | int) -> Decimal:
    return Decimal(str(value)).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def ceil_money(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_CEILING)


def floor_to_step(value: Decimal, step: Decimal) -> Decimal:
    if step <= ZERO:
        raise ValueError("step must be positive")
    units = (value / step).to_integral_value(rounding=ROUND_DOWN)
    return (units * step).quantize(TWOPLACES, rounding=ROUND_DOWN)


def annuity_payment(principal: Decimal, annual_rate: Decimal, term_months: int) -> Decimal:
    """Регулярный платёж до округления вверх до копеек."""
    if term_months < 1:
        raise ValueError("term_months must be >= 1")
    p = Decimal(str(principal))
    if p < ZERO:
        raise ValueError("principal must be >= 0")
    if annual_rate == ZERO:
        return p / Decimal(term_months)
    r = annual_rate / Decimal(12)
    factor = (Decimal(1) + r) ** term_months
    return p * r * factor / (factor - Decimal(1))


def monthly_payment(principal: Decimal, annual_rate: Decimal, term_months: int) -> Decimal:
    """Консервативный ежемесячный платёж: ceil до копеек."""
    return ceil_money(annuity_payment(principal, annual_rate, term_months))


def schedule_total_payment(
    principal: Decimal, annual_rate: Decimal, term_months: int
) -> Decimal:
    """Сумма фактических платежей графика (проценты ROUND_HALF_UP)."""
    balance = money(principal)
    if balance == ZERO:
        return ZERO
    r = annual_rate / Decimal(12)
    regular = monthly_payment(principal, annual_rate, term_months)
    total = ZERO
    for i in range(1, term_months + 1):
        interest = (balance * r).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
        if i == term_months:
            payment = money(balance + interest)
        else:
            payment = regular
            principal_part = payment - interest
            if principal_part > balance:
                payment = money(balance + interest)
                principal_part = balance
            balance = money(balance - principal_part)
        total = money(total + payment)
    return total


def dscr(free_cashflow: Decimal, existing_debt: Decimal, new_payment: Decimal) -> Decimal | None:
    denom = existing_debt + new_payment
    if denom <= ZERO:
        return None
    # Высокая точность для сравнения и аудита; строка — без лишнего округления вниз.
    return (free_cashflow / denom).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)


def max_principal_for_payment(
    max_payment: Decimal, annual_rate: Decimal, term_months: int
) -> Decimal:
    """P из A_max при аннуитете (до округления шага суммы)."""
    if max_payment <= ZERO:
        return ZERO
    if annual_rate == ZERO:
        return max_payment * Decimal(term_months)
    r = annual_rate / Decimal(12)
    factor = (Decimal(1) + r) ** term_months
    return max_payment * (factor - Decimal(1)) / (r * factor)


def format_dscr(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return format(value, "f")
