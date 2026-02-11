"""Scoring logic for distressed-market fit ranking."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

import pandas as pd

from .config_schema import DistressedFitConfig
from .features import MarketFeature, count_missing_core_fields


@dataclass
class ScoredMarket:
    rank: int
    market: str
    metro_code: str
    period: str
    distressed_fit_score: float
    decision_band: str
    disqualified_reason: str
    distress_inflow_idx: float
    rehab_risk_idx: float
    spread_reliability_idx: float
    exit_liquidity_idx: float
    investor_depth_idx: float
    competition_pressure_idx: float
    data_quality_flag: str
    source_mix: str
    feature: MarketFeature


def _winsorized_minmax(values: Sequence[Optional[float]], higher_is_better: bool = True) -> List[float]:
    numeric = [float(v) for v in values if v is not None]
    if not numeric:
        return [50.0 for _ in values]

    series = pd.Series(numeric)
    lower = float(series.quantile(0.05))
    upper = float(series.quantile(0.95))
    if lower > upper:
        lower, upper = upper, lower

    clipped: List[Optional[float]] = []
    for value in values:
        if value is None:
            clipped.append(None)
        else:
            clipped.append(float(min(max(float(value), lower), upper)))

    clipped_numeric = [v for v in clipped if v is not None]
    min_val = min(clipped_numeric)
    max_val = max(clipped_numeric)

    if min_val == max_val:
        base = [50.0 if v is not None else 50.0 for v in clipped]
    else:
        base = [
            50.0
            if v is None
            else ((float(v) - min_val) / (max_val - min_val) * 100.0)
            for v in clipped
        ]

    if not higher_is_better:
        return [100.0 - s for s in base]
    return base


def _weighted_average(components: List[tuple]) -> float:
    weighted_sum = 0.0
    total_weight = 0.0
    for value, weight in components:
        if value is None:
            continue
        weighted_sum += float(value) * float(weight)
        total_weight += float(weight)

    if total_weight == 0:
        return 50.0
    return weighted_sum / total_weight


def _score_mos(value: Optional[float]) -> float:
    if value is None:
        return 50.0
    if value < 1.0:
        return 70.0
    if value <= 3.5:
        return 100.0
    if value <= 5.0:
        return 80.0
    if value <= 6.5:
        return 55.0
    if value <= 8.0:
        return 30.0
    return 10.0


def _score_dom_liquidity(value: Optional[float]) -> float:
    if value is None:
        return 50.0
    if value <= 20:
        return 100.0
    if value <= 35:
        return 90.0
    if value <= 50:
        return 75.0
    if value <= 70:
        return 50.0
    if value <= 95:
        return 25.0
    return 5.0


def _score_pre_1980_fit(value: Optional[float], target: float = 0.45) -> float:
    if value is None:
        return 50.0
    distance = abs(value - target)
    score = 100.0 - min(1.0, distance / max(target, 0.01)) * 100.0
    return max(0.0, min(100.0, score))


def _confidence_adjust(raw_score: float, missing_core: int, stale_months: int) -> float:
    core_conf = 1.0 - (missing_core / 6.0)
    stale_conf = max(0.55, 1.0 - (0.10 * stale_months))
    confidence = max(0.30, min(core_conf, stale_conf))
    return 50.0 + (raw_score - 50.0) * confidence


def _decision_band(score: float, disqualified: bool) -> str:
    if disqualified:
        return "DISQUALIFIED"
    if score >= 80:
        return "GO_DEEP"
    if score >= 65:
        return "PRIORITY_WATCH"
    if score >= 50:
        return "WATCH"
    return "AVOID"


def score_markets(features: List[MarketFeature], config: DistressedFitConfig) -> List[ScoredMarket]:
    """Score markets and return ranked results."""
    if not features:
        return []

    # Cross-market normalized signals.
    inventory_yoy_s = _winsorized_minmax([f.inventory_yoy for f in features], higher_is_better=True)
    price_yoy_inverted_s = _winsorized_minmax([f.median_sale_price_yoy for f in features], higher_is_better=False)
    pending_yoy_inverted_s = _winsorized_minmax([f.pending_sales_yoy for f in features], higher_is_better=False)
    price_drop_rate_s = _winsorized_minmax([f.price_drops_rate for f in features], higher_is_better=True)

    dom_level_s = _winsorized_minmax([f.median_dom for f in features], higher_is_better=False)
    dom_volatility_s = _winsorized_minmax([f.dom_volatility_12m for f in features], higher_is_better=False)
    pre1940_s = _winsorized_minmax([f.pct_pre_1940 for f in features], higher_is_better=False)
    historic_s = _winsorized_minmax([f.historic_district_share for f in features], higher_is_better=False)

    price_cv_s = _winsorized_minmax([f.price_cv_12m for f in features], higher_is_better=False)
    swing_freq_s = _winsorized_minmax([f.extreme_swing_freq_12m for f in features], higher_is_better=False)
    abs_price_yoy_s = _winsorized_minmax(
        [abs(f.median_sale_price_yoy) if f.median_sale_price_yoy is not None else None for f in features],
        higher_is_better=False,
    )

    homes_sold_s = _winsorized_minmax([f.homes_sold for f in features], higher_is_better=True)
    buy_box_share_s = _winsorized_minmax([f.buy_box_share for f in features], higher_is_better=True)
    buy_box_homes_s = _winsorized_minmax([f.buy_box_homes_sold for f in features], higher_is_better=True)
    sales_persistence_s = _winsorized_minmax([f.sales_persistence_6m for f in features], higher_is_better=True)
    pending_sales_s = _winsorized_minmax([f.pending_sales for f in features], higher_is_better=True)

    wholesalers_s = _winsorized_minmax([f.active_wholesalers for f in features], higher_is_better=False)
    cash_buyers_s = _winsorized_minmax([f.active_cash_buyers for f in features], higher_is_better=False)
    cpc_s = _winsorized_minmax([f.ppc_cpc_sell_house_fast for f in features], higher_is_better=False)

    has_external_competition = any(
        f.active_wholesalers is not None or f.active_cash_buyers is not None or f.ppc_cpc_sell_house_fast is not None
        for f in features
    )

    scored_items: List[ScoredMarket] = []

    for idx, feature in enumerate(features):
        distress_inflow = _weighted_average(
            [
                (inventory_yoy_s[idx], 0.30),
                (price_yoy_inverted_s[idx], 0.25),
                (pending_yoy_inverted_s[idx], 0.25),
                (price_drop_rate_s[idx], 0.20),
            ]
        )

        pre1980_fit = _score_pre_1980_fit(feature.pct_pre_1980)
        rehab_risk = _weighted_average(
            [
                (dom_level_s[idx], 0.30),
                (dom_volatility_s[idx], 0.20),
                (pre1940_s[idx], 0.20),
                (historic_s[idx], 0.15),
                (pre1980_fit, 0.15),
            ]
        )

        spread_reliability = _weighted_average(
            [
                (price_cv_s[idx], 0.45),
                (swing_freq_s[idx], 0.35),
                (abs_price_yoy_s[idx], 0.20),
            ]
        )

        exit_liquidity = _weighted_average(
            [
                (homes_sold_s[idx], 0.40),
                (_score_mos(feature.months_of_supply), 0.25),
                (_score_dom_liquidity(feature.median_dom), 0.20),
                (buy_box_share_s[idx], 0.15),
            ]
        )

        investor_depth = _weighted_average(
            [
                (buy_box_homes_s[idx], 0.45),
                (homes_sold_s[idx], 0.30),
                (sales_persistence_s[idx], 0.15),
                (pending_sales_s[idx], 0.10),
            ]
        )

        if has_external_competition:
            competition_pressure = _weighted_average(
                [
                    (wholesalers_s[idx], 0.40),
                    (cash_buyers_s[idx], 0.40),
                    (cpc_s[idx], 0.20),
                ]
            )
        else:
            competition_pressure = _weighted_average(
                [
                    (100.0 - homes_sold_s[idx], 0.35),
                    (100.0 - buy_box_share_s[idx], 0.35),
                    (100.0 - dom_level_s[idx], 0.30),
                ]
            )

        weights = config.weights
        raw_score = (
            distress_inflow * weights["distress_inflow"]
            + rehab_risk * weights["rehab_risk"]
            + spread_reliability * weights["spread_reliability"]
            + exit_liquidity * weights["exit_liquidity"]
            + investor_depth * weights["investor_demand_depth"]
            + competition_pressure * weights["competition_pressure"]
        )

        missing_core = count_missing_core_fields(feature)
        adjusted_score = _confidence_adjust(raw_score, missing_core, feature.stale_months)

        disqualified_reasons: List[str] = []
        if feature.homes_sold is not None and feature.homes_sold < config.hard_filters.min_homes_sold:
            disqualified_reasons.append(f"homes_sold<{config.hard_filters.min_homes_sold}")
        if (
            feature.months_of_supply is not None
            and feature.months_of_supply > config.hard_filters.max_months_of_supply
        ):
            disqualified_reasons.append(f"months_of_supply>{config.hard_filters.max_months_of_supply}")
        if feature.median_dom is not None and feature.median_dom > config.hard_filters.max_median_dom:
            disqualified_reasons.append(f"median_dom>{config.hard_filters.max_median_dom}")

        disqualified = len(disqualified_reasons) > 0

        if missing_core >= 2:
            data_quality_flag = "LOW_CONFIDENCE"
        elif "+competition_csv" in feature.source_mix and "+housing_age_csv" in feature.source_mix:
            data_quality_flag = "FULL"
        else:
            data_quality_flag = "PARTIAL_EXTERNAL"

        scored_items.append(
            ScoredMarket(
                rank=0,
                market=feature.market,
                metro_code=feature.metro_code,
                period=feature.period,
                distressed_fit_score=round(max(0.0, min(100.0, adjusted_score)), 1),
                decision_band=_decision_band(adjusted_score, disqualified),
                disqualified_reason="; ".join(disqualified_reasons),
                distress_inflow_idx=round(distress_inflow, 1),
                rehab_risk_idx=round(rehab_risk, 1),
                spread_reliability_idx=round(spread_reliability, 1),
                exit_liquidity_idx=round(exit_liquidity, 1),
                investor_depth_idx=round(investor_depth, 1),
                competition_pressure_idx=round(competition_pressure, 1),
                data_quality_flag=data_quality_flag,
                source_mix=feature.source_mix,
                feature=feature,
            )
        )

    scored_items.sort(
        key=lambda item: (
            item.decision_band == "DISQUALIFIED",
            -item.distressed_fit_score,
            item.market,
        )
    )

    for idx, item in enumerate(scored_items, start=1):
        item.rank = idx

    return scored_items
