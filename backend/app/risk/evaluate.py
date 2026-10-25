"""Точка входа risk-модуля: score отдельно от policy.

Нет ORM, FastAPI, сети и БД. Money — Decimal. Missing ≠ 0.
Техническая ошибка контракта ≠ кредитный отказ.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from backend.app.risk import explanations as expl
from backend.app.risk.money import (
    ZERO,
    dscr,
    floor_to_step,
    format_dscr,
    max_principal_for_payment,
    money,
    monthly_payment,
    schedule_total_payment,
)
from backend.app.risk.policy import (
    MODEL_VERSION,
    POLICY_VERSION,
    PolicyError,
    d,
    dscr_threshold,
    load_policy,
    product_cfg,
    rate_for_band,
)
from backend.app.risk.score import compute_score
from backend.app.schemas.enums import RiskRecommendation
from backend.app.schemas.risk import Affordability, OfferCandidate, RiskInput, RiskResult


class RiskContractError(ValueError):
    """Невалидная структура входа — техническая ошибка, не кредитный отказ."""


def _result(**kwargs: Any) -> RiskResult:
    base = {
        "schema_version": "risk-v1",
        "model_version": MODEL_VERSION,
        "policy_version": POLICY_VERSION,
        "risk_score": None,
        "risk_band": None,
        "requires_officer": True,
        "reason_codes": [],
        "requested_fields": [],
        "factors": None,
        "candidate": None,
        "affordability": None,
        "client_explanations": [],
        "officer_explanations": [],
    }
    base.update(kwargs)
    return RiskResult(**base)


def _debt_mismatch(
    declared: Decimal, verified: Decimal, policy: dict[str, Any]
) -> bool:
    abs_thr = d(policy["debt_mismatch"]["absolute_rub"])
    rel = d(policy["debt_mismatch"]["relative"])
    threshold = max(abs_thr, rel * max(verified, Decimal("1")))
    return abs(declared - verified) > threshold


def _find_offer_amount(
    *,
    requested: Decimal,
    free_cashflow: Decimal,
    existing_debt: Decimal,
    annual_rate: Decimal,
    term_months: int,
    dscr_min: Decimal,
    amount_min: Decimal,
    amount_max: Decimal,
    amount_step: Decimal,
) -> tuple[Decimal | None, Decimal | None, Decimal | None, Decimal | None]:
    """Вернуть (amount, payment, dscr, total) или (None,...) если недоступно."""
    a_max = free_cashflow / dscr_min - existing_debt
    if a_max <= ZERO:
        return None, None, None, None

    p_max = max_principal_for_payment(a_max, annual_rate, term_months)
    candidate = min(requested, amount_max, p_max)
    candidate = floor_to_step(candidate, amount_step)

    while candidate >= amount_min:
        payment = monthly_payment(candidate, annual_rate, term_months)
        ratio = dscr(free_cashflow, existing_debt, payment)
        if ratio is not None and ratio >= dscr_min:
            total = schedule_total_payment(candidate, annual_rate, term_months)
            return candidate, payment, ratio, total
        candidate = floor_to_step(candidate - amount_step, amount_step)

    return None, None, None, None


def evaluate(input: RiskInput, policy: dict | None = None) -> RiskResult:
    """Чистая функция evaluate(input, policy) → RiskResult."""
    if not input.sources_complete:
        raise RiskContractError(
            "sources_complete=false: worker must not call evaluate; "
            "route to SOURCE_INCOMPLETE"
        )
    if input.schema_version != "risk-v1":
        raise RiskContractError(f"Unsupported schema_version: {input.schema_version}")

    try:
        pol = policy if policy is not None else load_policy()
        product = product_cfg(pol, input.product_code.value)
    except PolicyError as exc:
        raise RiskContractError(str(exc)) from exc

    # --- 2. Missing / conflicts (NEEDS_INFO) ---
    missing_fields: list[str] = []
    if input.monthly_revenue is None:
        missing_fields.append("monthly_revenue")
    if input.monthly_operating_costs is None:
        missing_fields.append("monthly_operating_costs")
    if input.declared_monthly_debt_payments is None:
        missing_fields.append("declared_monthly_debt_payments")
    if not input.required_documents_present:
        missing_fields.append("required_documents")
    if input.company_age_months is None:
        missing_fields.append("company_age_months")
    if input.registry_status is None:
        missing_fields.append("registry_status")
    if input.verified_monthly_debt_payments is None:
        missing_fields.append("verified_monthly_debt_payments")
    if input.max_overdue_days_12m is None:
        missing_fields.append("max_overdue_days_12m")

    if missing_fields:
        codes = ["MISSING_DATA"]
        return _result(
            recommendation=RiskRecommendation.NEEDS_INFO,
            reason_codes=codes,
            requested_fields=missing_fields,
            client_explanations=[expl.client_text("MISSING_DATA")],
            officer_explanations=[
                expl.officer_text(
                    "MISSING_DATA",
                    f"fields={missing_fields}",
                )
            ],
        )

    # Structural product checks (after fields present)
    term_ok = input.term_months in product["term_months"]
    amount = money(input.requested_amount)
    amount_min = d(product["amount_min"])
    amount_max = d(product["amount_max"])
    amount_step = d(product["amount_step"])
    if not term_ok or amount < amount_min or amount > amount_max:
        raise RiskContractError(
            "Product constraints violated on internal RiskInput "
            "(should be rejected at API validation before evaluate)"
        )

    declared = money(input.declared_monthly_debt_payments)  # type: ignore[arg-type]
    verified = money(input.verified_monthly_debt_payments)  # type: ignore[arg-type]
    if _debt_mismatch(declared, verified, pol):
        return _result(
            recommendation=RiskRecommendation.NEEDS_INFO,
            reason_codes=["DEBT_DATA_MISMATCH"],
            requested_fields=["declared_monthly_debt_payments"],
            client_explanations=[expl.client_text("DEBT_DATA_MISMATCH")],
            officer_explanations=[
                expl.officer_text(
                    "DEBT_DATA_MISMATCH",
                    f"declared={declared} verified={verified} "
                    f"abs={pol['debt_mismatch']['absolute_rub']} "
                    f"rel={pol['debt_mismatch']['relative']}",
                )
            ],
        )

    revenue = money(input.monthly_revenue)  # type: ignore[arg-type]
    costs = money(input.monthly_operating_costs)  # type: ignore[arg-type]
    age = int(input.company_age_months)  # type: ignore[arg-type]
    overdue = int(input.max_overdue_days_12m)  # type: ignore[arg-type]
    free_cashflow = money(revenue - costs)
    min_age = int(product["min_company_age_months"])
    overdue_limit = int(pol["stop_factors"]["max_overdue_days_12m"])

    # --- 3. Stop-factors (REJECT, score may be null) ---
    if input.registry_status == "INACTIVE":
        return _result(
            recommendation=RiskRecommendation.REJECT,
            reason_codes=["REGISTRY_INACTIVE"],
            client_explanations=[expl.client_text("REGISTRY_INACTIVE")],
            officer_explanations=[
                expl.officer_text(
                    "REGISTRY_INACTIVE",
                    f"status={input.registry_status}",
                )
            ],
            affordability=Affordability(
                free_cashflow=free_cashflow,
                existing_payment=verified,
            ),
        )

    if age < min_age:
        return _result(
            recommendation=RiskRecommendation.REJECT,
            reason_codes=["BUSINESS_TOO_YOUNG"],
            client_explanations=[
                expl.client_text("BUSINESS_TOO_YOUNG", min_age=min_age)
            ],
            officer_explanations=[
                expl.officer_text(
                    "BUSINESS_TOO_YOUNG",
                    f"age={age} min={min_age}",
                )
            ],
            affordability=Affordability(
                free_cashflow=free_cashflow,
                existing_payment=verified,
            ),
        )

    if overdue > overdue_limit:
        return _result(
            recommendation=RiskRecommendation.REJECT,
            reason_codes=["OVERDUE_LIMIT"],
            client_explanations=[expl.client_text("OVERDUE_LIMIT")],
            officer_explanations=[
                expl.officer_text(
                    "OVERDUE_LIMIT",
                    f"max_overdue_days_12m={overdue} threshold={overdue_limit}",
                )
            ],
            affordability=Affordability(
                free_cashflow=free_cashflow,
                existing_payment=verified,
            ),
        )

    if free_cashflow <= ZERO:
        return _result(
            recommendation=RiskRecommendation.REJECT,
            reason_codes=["CASHFLOW_NON_POSITIVE"],
            client_explanations=[expl.client_text("CASHFLOW_NON_POSITIVE")],
            officer_explanations=[
                expl.officer_text(
                    "CASHFLOW_NON_POSITIVE",
                    f"R={revenue} O={costs} C={free_cashflow}",
                )
            ],
            affordability=Affordability(
                free_cashflow=free_cashflow,
                existing_payment=verified,
            ),
        )

    # --- 4. Score ---
    score, band, factors = compute_score(input, policy=pol)
    if band == "C":
        return _result(
            recommendation=RiskRecommendation.REJECT,
            risk_score=score,
            risk_band=band,
            factors=factors,
            reason_codes=["RISK_POLICY_LIMIT"],
            client_explanations=[expl.client_text("RISK_POLICY_LIMIT")],
            officer_explanations=[
                expl.officer_text(
                    "RISK_POLICY_LIMIT",
                    f"score={score} band={band} factors="
                    + ",".join(f"{f.code}:{f.points}" for f in factors),
                )
            ],
            affordability=Affordability(
                free_cashflow=free_cashflow,
                existing_payment=verified,
            ),
        )

    annual_rate = rate_for_band(product, band)
    threshold = dscr_threshold(product, band)
    req_payment = monthly_payment(amount, annual_rate, input.term_months)
    req_dscr = dscr(free_cashflow, verified, req_payment)

    offered, off_payment, off_dscr, total = _find_offer_amount(
        requested=amount,
        free_cashflow=free_cashflow,
        existing_debt=verified,
        annual_rate=annual_rate,
        term_months=input.term_months,
        dscr_min=threshold,
        amount_min=amount_min,
        amount_max=amount_max,
        amount_step=amount_step,
    )

    if offered is None or off_payment is None or off_dscr is None:
        return _result(
            recommendation=RiskRecommendation.REJECT,
            risk_score=score,
            risk_band=band,
            factors=factors,
            reason_codes=["AFFORDABILITY_BELOW_MINIMUM"],
            client_explanations=[expl.client_text("AFFORDABILITY_BELOW_MINIMUM")],
            officer_explanations=[
                expl.officer_text(
                    "AFFORDABILITY_BELOW_MINIMUM",
                    f"C={free_cashflow} D={verified} threshold={threshold} "
                    f"requested={amount} rate={annual_rate}",
                )
            ],
            affordability=Affordability(
                free_cashflow=free_cashflow,
                existing_payment=verified,
                requested_payment=req_payment,
                requested_dscr=format_dscr(req_dscr),
            ),
        )

    is_alternative = offered < amount
    reason_codes: list[str] = []
    client_explanations: list[str] = []
    officer_explanations: list[str] = []
    if is_alternative:
        reason_codes.append("LOWER_AMOUNT_REQUIRED")
        client_explanations.append(expl.client_text("LOWER_AMOUNT_REQUIRED"))
        officer_explanations.append(
            expl.officer_text(
                "LOWER_AMOUNT_REQUIRED",
                f"requested={amount} offered={offered} "
                f"requested_dscr={format_dscr(req_dscr)} "
                f"offered_dscr={format_dscr(off_dscr)} "
                f"threshold={threshold}",
            )
        )

    candidate = OfferCandidate(
        product_code=input.product_code,
        amount=offered,
        term_months=input.term_months,
        annual_rate=annual_rate,
        currency="RUB",
        fees=money("0"),
        is_alternative=is_alternative,
    )

    return _result(
        recommendation=RiskRecommendation.OFFER,
        risk_score=score,
        risk_band=band,
        factors=factors,
        reason_codes=reason_codes,
        candidate=candidate,
        affordability=Affordability(
            free_cashflow=free_cashflow,
            existing_payment=verified,
            requested_payment=req_payment,
            requested_dscr=format_dscr(req_dscr),
            offered_payment=off_payment,
            offered_dscr=format_dscr(off_dscr),
            total_payment=total,
        ),
        client_explanations=client_explanations,
        officer_explanations=officer_explanations,
    )
