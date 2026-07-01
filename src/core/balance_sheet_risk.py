from __future__ import annotations

from typing import Any


def _num(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, float(value)))


def _ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator == 0:
        return None
    return round(numerator / denominator, 6)


def _sum_present(*values: float | None) -> float | None:
    present = [value for value in values if value is not None]
    if not present:
        return None
    return sum(present)


def _risk_bucket(score: float, insufficient: bool) -> str:
    if insufficient:
        return "data_insufficient"
    if score >= 80:
        return "extreme"
    if score >= 60:
        return "high"
    if score >= 35:
        return "moderate"
    return "low"


def evaluate_balance_sheet(row: dict[str, Any] | None) -> dict[str, Any]:
    row = row or {}
    cash = _num(row.get("cash_and_cash_equivalents"))
    marketable = _num(row.get("marketable_securities"))
    receivables = _num(row.get("accounts_receivable"))
    inventory = _num(row.get("inventory"))
    current_assets = _num(row.get("current_assets"))
    fixed_assets = _num(row.get("fixed_assets"))
    goodwill = _num(row.get("goodwill"))
    other_long_term_assets = _num(row.get("other_long_term_assets"))
    current_liabilities = _num(row.get("current_liabilities"))
    payables = _num(row.get("payables_accrued_expenses"))
    short_debt = _num(row.get("short_term_debt"))
    long_debt = _num(row.get("long_term_debt"))
    other_liabilities = _num(row.get("other_liabilities"))
    preferred_stock = _num(row.get("preferred_stock"))
    common_stock = _num(row.get("common_stock_paid_in_capital"))
    retained_earnings = _num(row.get("retained_earnings"))
    treasury_stock = _num(row.get("treasury_stock"))
    shareholder_equity = _num(row.get("shareholder_equity"))

    if current_assets is None:
        current_assets = _sum_present(cash, marketable, receivables, inventory)
    if current_liabilities is None:
        current_liabilities = _sum_present(payables, short_debt)
    total_assets = _sum_present(current_assets, fixed_assets, goodwill, other_long_term_assets)
    total_debt = _sum_present(short_debt, long_debt)
    total_liabilities = _sum_present(current_liabilities, long_debt, other_liabilities)

    current_ratio = _ratio(current_assets, current_liabilities)
    quick_assets = _sum_present(cash, marketable, receivables)
    quick_ratio = _ratio(quick_assets, current_liabilities)
    debt_to_equity = _ratio(total_liabilities, shareholder_equity)
    cash_to_debt = _ratio(cash, total_debt)

    required_values = [current_assets, current_liabilities, shareholder_equity]
    data_insufficient = any(value is None for value in required_values)
    blockers: list[str] = []
    warnings: list[str] = []
    if data_insufficient:
        blockers.append("balance_sheet_data_insufficient")

    risk = 25.0 if data_insufficient else 0.0
    if current_ratio is not None:
        if current_ratio < 0.75:
            risk += 24.0
            blockers.append("weak_current_ratio")
        elif current_ratio < 1.0:
            risk += 14.0
            warnings.append("thin_current_ratio")
    if quick_ratio is not None:
        if quick_ratio < 0.5:
            risk += 18.0
            blockers.append("weak_quick_ratio")
        elif quick_ratio < 0.9:
            risk += 8.0
            warnings.append("thin_quick_ratio")
    if shareholder_equity is not None and shareholder_equity <= 0:
        risk += 30.0
        blockers.append("negative_or_zero_shareholder_equity")
    elif debt_to_equity is not None:
        if debt_to_equity > 3.0:
            risk += 20.0
            blockers.append("high_debt_to_equity")
        elif debt_to_equity > 1.5:
            risk += 10.0
            warnings.append("elevated_debt_to_equity")
    if cash_to_debt is not None:
        if cash_to_debt < 0.1:
            risk += 15.0
            blockers.append("low_cash_to_debt")
        elif cash_to_debt < 0.35:
            risk += 8.0
            warnings.append("thin_cash_to_debt")
    if preferred_stock is not None and preferred_stock > 0:
        risk += 12.0
        warnings.append("preferred_stock_overhang")
    goodwill_ratio = _ratio(goodwill, total_assets)
    if goodwill_ratio is not None and goodwill_ratio > 0.4:
        risk += 10.0
        warnings.append("high_goodwill_asset_share")
    if row.get("dilution_risk_score") is not None:
        dilution_risk_score = _clamp(float(row.get("dilution_risk_score") or 0.0))
    else:
        dilution_risk_score = _clamp((20.0 if cash_to_debt is not None and cash_to_debt < 0.25 else 0.0) + (20.0 if shareholder_equity is not None and shareholder_equity <= 0 else 0.0))
    if row.get("offering_risk_score") is not None:
        offering_risk_score = _clamp(float(row.get("offering_risk_score") or 0.0))
    else:
        offering_risk_score = _clamp((25.0 if current_ratio is not None and current_ratio < 1.0 else 0.0) + (20.0 if preferred_stock and preferred_stock > 0 else 0.0))
    goodwill_risk_score = _clamp((goodwill_ratio or 0.0) * 100.0)
    preferred_stock_risk_score = 75.0 if preferred_stock is not None and preferred_stock > 0 else 0.0

    risk += dilution_risk_score * 0.20 + offering_risk_score * 0.20 + goodwill_risk_score * 0.08 + preferred_stock_risk_score * 0.08
    fundamental_risk_score = round(_clamp(risk), 2)
    balance_sheet_quality_score = round(_clamp(100.0 - fundamental_risk_score), 2)
    bucket = _risk_bucket(fundamental_risk_score, data_insufficient)
    force_status = None
    if not data_insufficient and (fundamental_risk_score >= 85.0 or offering_risk_score >= 85.0 or dilution_risk_score >= 85.0):
        force_status = "NO_REVIEW"
    elif not data_insufficient and fundamental_risk_score >= 65.0:
        force_status = "HIGH_RISK_REVIEW"

    if dilution_risk_score >= 75:
        blockers.append("extreme_dilution_risk")
    if offering_risk_score >= 75:
        blockers.append("extreme_offering_risk")

    assets_identity_gap = None
    if total_assets is not None and total_liabilities is not None and shareholder_equity is not None:
        assets_identity_gap = round(total_assets - total_liabilities - shareholder_equity, 2)

    return {
        "cash_and_cash_equivalents": cash,
        "marketable_securities": marketable,
        "accounts_receivable": receivables,
        "inventory": inventory,
        "current_assets": current_assets,
        "fixed_assets": fixed_assets,
        "goodwill": goodwill,
        "other_long_term_assets": other_long_term_assets,
        "current_liabilities": current_liabilities,
        "payables_accrued_expenses": payables,
        "short_term_debt": short_debt,
        "long_term_debt": long_debt,
        "other_liabilities": other_liabilities,
        "preferred_stock": preferred_stock,
        "common_stock_paid_in_capital": common_stock,
        "retained_earnings": retained_earnings,
        "treasury_stock": treasury_stock,
        "shareholder_equity": shareholder_equity,
        "total_assets": total_assets,
        "total_liabilities": total_liabilities,
        "total_debt": total_debt,
        "assets_identity_gap": assets_identity_gap,
        "current_ratio": current_ratio,
        "quick_ratio": quick_ratio,
        "debt_to_equity": debt_to_equity,
        "cash_to_debt": cash_to_debt,
        "cash_runway_score": round(_clamp((cash_to_debt or 0.0) * 100.0), 2) if cash_to_debt is not None else None,
        "dilution_risk_score": round(dilution_risk_score, 2),
        "offering_risk_score": round(offering_risk_score, 2),
        "goodwill_risk_score": round(goodwill_risk_score, 2),
        "preferred_stock_risk_score": round(preferred_stock_risk_score, 2),
        "balance_sheet_quality_score": balance_sheet_quality_score,
        "fundamental_risk_score": fundamental_risk_score,
        "balance_sheet_risk_bucket": bucket,
        "data_insufficient": data_insufficient,
        "risk_blockers": sorted(set(blockers)),
        "risk_warnings": sorted(set(warnings)),
        "force_status": force_status,
    }
