"""Backtest utilities for distressed-fit scoring."""

from __future__ import annotations

from typing import Dict, List, Optional

import pandas as pd

from .config_schema import DistressedFitConfig
from .features import MarketSeed, build_feature_rows_for_month, count_missing_core_fields
from .scoring import score_markets


BAND_ORDER = {
    "DISQUALIFIED": -1,
    "AVOID": 0,
    "WATCH": 1,
    "PRIORITY_WATCH": 2,
    "GO_DEEP": 3,
}


def _next_month(period: str) -> str:
    ts = pd.Period(period, freq="M") + 1
    return ts.strftime("%Y-%m")


def _pending_yoy(monthly: pd.DataFrame, month: str) -> Optional[float]:
    current = monthly[monthly["period"] == month]
    if current.empty:
        return None

    period = pd.Period(month, freq="M")
    prev = monthly[monthly["period"] == (period - 12).strftime("%Y-%m")]
    if prev.empty:
        return None

    curr_value = float(current.iloc[0]["pending_sales"])
    prev_value = float(prev.iloc[0]["pending_sales"])
    if prev_value == 0:
        return None
    return (curr_value / prev_value) - 1.0


def _mean(values: List[float]) -> Optional[float]:
    clean = [v for v in values if v is not None]
    if not clean:
        return None
    return float(sum(clean) / len(clean))


def run_backtest(
    monthly_by_metro: Dict[str, pd.DataFrame],
    seeds: List[MarketSeed],
    config: DistressedFitConfig,
    all_periods: List[str],
    competition_map: Dict[str, dict],
    housing_map: Dict[str, dict],
    target_month: str,
) -> dict:
    """Run rolling backtest on the last six completed months."""
    eligible = [p for p in all_periods if p <= target_month]
    if len(eligible) < 7:
        return {
            "enabled": True,
            "status": "SKIPPED",
            "reason": "Need at least 7 months for six rolling month checks",
        }

    candidate_months = eligible[:-1]  # require next month outcomes
    months = candidate_months[-6:]

    month_results: List[dict] = []
    passed_months = 0
    missing_feature_violations = 0
    roanoke_bands: List[str] = []
    roanoke_volatility_flags: List[bool] = []

    for month in months:
        scored = score_markets(
            build_feature_rows_for_month(monthly_by_metro, seeds, month, competition_map, housing_map),
            config,
        )

        valid = [s for s in scored if s.decision_band != "DISQUALIFIED"]
        quartile_size = max(1, len(valid) // 4)
        top = valid[:quartile_size]
        bottom = valid[-quartile_size:] if quartile_size <= len(valid) else valid

        next_period = _next_month(month)

        def collect(group):
            dom_changes: List[float] = []
            mos_changes: List[float] = []
            pending_resilience: List[float] = []
            for item in group:
                monthly = monthly_by_metro.get(item.metro_code)
                if monthly is None or monthly.empty:
                    continue

                now_row = monthly[monthly["period"] == month]
                next_row = monthly[monthly["period"] == next_period]
                if now_row.empty or next_row.empty:
                    continue

                dom_now = now_row.iloc[0]["median_dom"]
                dom_next = next_row.iloc[0]["median_dom"]
                mos_now = now_row.iloc[0]["months_of_supply"]
                mos_next = next_row.iloc[0]["months_of_supply"]

                if pd.notna(dom_now) and pd.notna(dom_next):
                    dom_changes.append(float(dom_next - dom_now))
                if pd.notna(mos_now) and pd.notna(mos_next):
                    mos_changes.append(float(mos_next - mos_now))

                pending_yoy_next = _pending_yoy(monthly, next_period)
                if pending_yoy_next is not None:
                    pending_resilience.append(float(pending_yoy_next))

            return {
                "dom_change": _mean(dom_changes),
                "mos_change": _mean(mos_changes),
                "pending_resilience": _mean(pending_resilience),
            }

        top_outcomes = collect(top)
        bottom_outcomes = collect(bottom)

        dom_pass = (
            top_outcomes["dom_change"] is not None
            and bottom_outcomes["dom_change"] is not None
            and top_outcomes["dom_change"] < bottom_outcomes["dom_change"]
        )
        mos_pass = (
            top_outcomes["mos_change"] is not None
            and bottom_outcomes["mos_change"] is not None
            and top_outcomes["mos_change"] < bottom_outcomes["mos_change"]
        )
        pending_pass = (
            top_outcomes["pending_resilience"] is not None
            and bottom_outcomes["pending_resilience"] is not None
            and top_outcomes["pending_resilience"] > bottom_outcomes["pending_resilience"]
        )

        checks_passed = sum([dom_pass, mos_pass, pending_pass])
        month_pass = checks_passed >= 2
        if month_pass:
            passed_months += 1

        low_conf_count = sum(1 for s in scored if count_missing_core_fields(s.feature) >= 2)
        low_conf_ratio = (low_conf_count / len(scored)) if scored else 0.0
        if low_conf_ratio > 0.25:
            missing_feature_violations += 1

        roanoke = next((s for s in scored if s.market == "Roanoke, VA"), None)
        if roanoke:
            roanoke_bands.append(roanoke.decision_band)
            roanoke_volatility_flags.append(
                (roanoke.feature.extreme_swing_freq_12m or 0.0) > 0.50
                or (roanoke.feature.price_cv_12m or 0.0) > 0.18
            )

        month_results.append(
            {
                "month": month,
                "next_month": next_period,
                "quartile_size": quartile_size,
                "checks": {
                    "dom_change": dom_pass,
                    "mos_change": mos_pass,
                    "pending_resilience": pending_pass,
                    "checks_passed": checks_passed,
                },
                "top_outcomes": top_outcomes,
                "bottom_outcomes": bottom_outcomes,
                "month_pass": month_pass,
                "low_confidence_ratio": round(low_conf_ratio, 3),
            }
        )

    roanoke_oscillation_violation = False
    if len(roanoke_bands) >= 3:
        for idx in range(len(roanoke_bands) - 2):
            b0 = BAND_ORDER.get(roanoke_bands[idx], 0)
            b2 = BAND_ORDER.get(roanoke_bands[idx + 2], 0)
            if abs(b2 - b0) > 2:
                volatile = any(roanoke_volatility_flags[idx : idx + 3])
                if not volatile:
                    roanoke_oscillation_violation = True
                    break

    pass_criteria = {
        "quartile_outperformance": passed_months >= 4,
        "missing_feature_threshold": missing_feature_violations == 0,
        "roanoke_stability": not roanoke_oscillation_violation,
    }

    overall_pass = all(pass_criteria.values())

    return {
        "enabled": True,
        "status": "PASS" if overall_pass else "FAIL",
        "months_evaluated": months,
        "month_results": month_results,
        "summary": {
            "months_passing_quartile_rule": passed_months,
            "missing_feature_violations": missing_feature_violations,
            "roanoke_oscillation_violation": roanoke_oscillation_violation,
        },
        "pass_criteria": pass_criteria,
    }
