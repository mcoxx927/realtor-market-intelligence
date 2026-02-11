"""Feature extraction for distressed-market fit scoring."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

from .competition import lookup_proxy


@dataclass
class MarketSeed:
    metro_code: str
    market_name: str
    display_name: str
    state: str


@dataclass
class MarketFeature:
    market: str
    metro_code: str
    period: str
    source_mix: str
    stale_months: int
    median_sale_price: Optional[float]
    median_sale_price_yoy: Optional[float]
    inventory: Optional[float]
    inventory_yoy: Optional[float]
    new_listings: Optional[float]
    homes_sold: Optional[float]
    median_dom: Optional[float]
    median_dom_yoy: Optional[float]
    months_of_supply: Optional[float]
    pending_sales: Optional[float]
    pending_sales_yoy: Optional[float]
    price_drops: Optional[float]
    price_drops_rate: Optional[float]
    price_cv_12m: Optional[float]
    extreme_swing_freq_12m: Optional[float]
    dom_volatility_12m: Optional[float]
    buy_box_share: Optional[float]
    buy_box_homes_sold: Optional[float]
    sales_persistence_6m: Optional[float]
    pct_pre_1980: Optional[float]
    pct_pre_1940: Optional[float]
    historic_district_share: Optional[float]
    active_wholesalers: Optional[float]
    active_cash_buyers: Optional[float]
    ppc_cpc_sell_house_fast: Optional[float]


REQUIRED_COLUMNS = [
    "PERIOD_BEGIN",
    "PROPERTY_TYPE",
    "PARENT_METRO_REGION_METRO_CODE",
    "MEDIAN_SALE_PRICE",
    "HOMES_SOLD",
    "PENDING_SALES",
    "NEW_LISTINGS",
    "INVENTORY",
    "MEDIAN_DOM",
    "PRICE_DROPS",
]


def load_seed_markets(seed_path: Path, limit: Optional[int] = None) -> List[MarketSeed]:
    markets: List[MarketSeed] = []
    with seed_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            metro_code = str(row.get("metro_code", "")).strip()
            if not metro_code:
                continue
            display_name = str(row.get("display_name", "")).strip()
            market_name = str(row.get("market_name", "")).strip()
            state = str(row.get("state", "")).strip()
            markets.append(
                MarketSeed(
                    metro_code=metro_code,
                    market_name=market_name,
                    display_name=display_name or f"{market_name}, {state}",
                    state=state,
                )
            )

    if limit:
        markets = markets[:limit]

    return markets


def _pct_change(curr: Optional[float], prev: Optional[float]) -> Optional[float]:
    if curr is None or prev is None or prev == 0:
        return None
    return (curr / prev) - 1.0


def _coerce_numeric(frame: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    for col in columns:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    return frame


def load_master_monthly_series(
    tsv_path: Path,
    metro_codes: List[str],
    buy_box_min: int,
    buy_box_max: int,
) -> Tuple[Dict[str, pd.DataFrame], List[str]]:
    """Load and aggregate master TSV once, then split monthly series by metro code."""
    if not tsv_path.exists():
        raise FileNotFoundError(f"Master TSV not found: {tsv_path}")

    metro_set = {str(code) for code in metro_codes}

    frame = pd.read_csv(
        tsv_path,
        sep="\t",
        compression="gzip",
        low_memory=False,
        usecols=REQUIRED_COLUMNS,
    )

    frame = frame[frame["PROPERTY_TYPE"] == "All Residential"].copy()
    frame["PARENT_METRO_REGION_METRO_CODE"] = frame["PARENT_METRO_REGION_METRO_CODE"].astype(str)
    frame = frame[frame["PARENT_METRO_REGION_METRO_CODE"].isin(metro_set)].copy()

    numeric_cols = [
        "MEDIAN_SALE_PRICE",
        "HOMES_SOLD",
        "PENDING_SALES",
        "NEW_LISTINGS",
        "INVENTORY",
        "MEDIAN_DOM",
        "PRICE_DROPS",
    ]
    frame = _coerce_numeric(frame, numeric_cols)
    frame["PERIOD_BEGIN"] = pd.to_datetime(frame["PERIOD_BEGIN"], errors="coerce")
    frame = frame[frame["PERIOD_BEGIN"].notna()].copy()

    frame["weighted_price_component"] = frame["MEDIAN_SALE_PRICE"] * frame["HOMES_SOLD"].fillna(0)
    frame["dom_weight"] = frame["HOMES_SOLD"].where(frame["MEDIAN_DOM"].notna(), 0).fillna(0)
    frame["weighted_dom_component"] = frame["MEDIAN_DOM"].fillna(0) * frame["dom_weight"]
    in_buy_box = frame["MEDIAN_SALE_PRICE"].between(buy_box_min, buy_box_max, inclusive="both")
    frame["buy_box_homes_component"] = frame["HOMES_SOLD"].where(in_buy_box, 0).fillna(0)

    grouped = (
        frame.groupby(["PARENT_METRO_REGION_METRO_CODE", "PERIOD_BEGIN"], as_index=False)
        .agg(
            inventory=("INVENTORY", "sum"),
            new_listings=("NEW_LISTINGS", "sum"),
            homes_sold=("HOMES_SOLD", "sum"),
            pending_sales=("PENDING_SALES", "sum"),
            price_drops=("PRICE_DROPS", "sum"),
            weighted_price_component=("weighted_price_component", "sum"),
            weighted_dom_component=("weighted_dom_component", "sum"),
            dom_weight=("dom_weight", "sum"),
            buy_box_homes_sold=("buy_box_homes_component", "sum"),
        )
        .sort_values(["PARENT_METRO_REGION_METRO_CODE", "PERIOD_BEGIN"])
    )

    grouped["median_sale_price"] = grouped.apply(
        lambda row: row["weighted_price_component"] / row["homes_sold"] if row["homes_sold"] > 0 else None,
        axis=1,
    )
    grouped["median_dom"] = grouped.apply(
        lambda row: row["weighted_dom_component"] / row["dom_weight"] if row["dom_weight"] > 0 else None,
        axis=1,
    )
    grouped["months_of_supply"] = grouped.apply(
        lambda row: row["inventory"] / row["homes_sold"] if row["homes_sold"] > 0 else None,
        axis=1,
    )
    grouped["buy_box_share"] = grouped.apply(
        lambda row: row["buy_box_homes_sold"] / row["homes_sold"] if row["homes_sold"] > 0 else None,
        axis=1,
    )

    grouped = grouped.rename(columns={"PARENT_METRO_REGION_METRO_CODE": "metro_code"})

    monthly_by_metro: Dict[str, pd.DataFrame] = {}
    for metro_code, metro_df in grouped.groupby("metro_code"):
        metro_df = metro_df.sort_values("PERIOD_BEGIN").reset_index(drop=True)
        metro_df["period"] = metro_df["PERIOD_BEGIN"].dt.strftime("%Y-%m")
        monthly_by_metro[metro_code] = metro_df

    all_periods = sorted(grouped["PERIOD_BEGIN"].dt.strftime("%Y-%m").unique().tolist())
    return monthly_by_metro, all_periods


def _month_distance(target_period: pd.Period, current_period: pd.Period) -> int:
    return (target_period.year - current_period.year) * 12 + (target_period.month - current_period.month)


def _get_selected_row(monthly: pd.DataFrame, month: Optional[str]) -> Optional[pd.Series]:
    if monthly.empty:
        return None

    if not month:
        return monthly.iloc[-1]

    target = pd.Period(month, freq="M")
    periods = monthly["PERIOD_BEGIN"].dt.to_period("M")
    eligible = monthly[periods <= target]
    if eligible.empty:
        return None
    return eligible.iloc[-1]


def _trailing(monthly: pd.DataFrame, selected_ts: pd.Timestamp, months: int) -> pd.DataFrame:
    start = selected_ts - pd.DateOffset(months=months - 1)
    return monthly[(monthly["PERIOD_BEGIN"] >= start) & (monthly["PERIOD_BEGIN"] <= selected_ts)].copy()


def _fetch_previous_year(monthly: pd.DataFrame, selected_ts: pd.Timestamp) -> Optional[pd.Series]:
    target = selected_ts - pd.DateOffset(years=1)
    match = monthly[monthly["PERIOD_BEGIN"] == target]
    if match.empty:
        return None
    return match.iloc[0]


def _safe_float(value: object) -> Optional[float]:
    if value is None:
        return None
    if pd.isna(value):
        return None
    if not isinstance(value, (int, float, str)):
        return None
    return float(value)


def _attach_optional_features(
    feature: MarketFeature,
    competition_map: Dict[str, dict],
    housing_map: Dict[str, dict],
) -> None:
    comp_row = lookup_proxy(competition_map, feature.metro_code, feature.market)
    housing_row = lookup_proxy(housing_map, feature.metro_code, feature.market)

    def parse_optional(row: dict, key: str) -> Optional[float]:
        if not row:
            return None
        value = row.get(key)
        if value is None:
            return None
        if not isinstance(value, (int, float, str)):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    feature.active_wholesalers = parse_optional(comp_row, "active_wholesalers")
    feature.active_cash_buyers = parse_optional(comp_row, "active_cash_buyers")
    feature.ppc_cpc_sell_house_fast = parse_optional(comp_row, "ppc_cpc_sell_house_fast")

    feature.pct_pre_1980 = parse_optional(housing_row, "pct_pre_1980")
    feature.pct_pre_1940 = parse_optional(housing_row, "pct_pre_1940")
    feature.historic_district_share = parse_optional(housing_row, "historic_district_share")


CORE_RAW_FIELDS = [
    "median_sale_price_yoy",
    "inventory_yoy",
    "pending_sales_yoy",
    "homes_sold",
    "median_dom",
    "months_of_supply",
]


def build_feature_rows_for_month(
    monthly_by_metro: Dict[str, pd.DataFrame],
    seeds: List[MarketSeed],
    month: Optional[str],
    competition_map: Dict[str, dict],
    housing_map: Dict[str, dict],
) -> List[MarketFeature]:
    """Build per-market feature rows for a given month."""
    rows: List[MarketFeature] = []
    target_period = pd.Period(month, freq="M") if month else None

    for seed in seeds:
        monthly = monthly_by_metro.get(seed.metro_code)
        if monthly is None or monthly.empty:
            feature = MarketFeature(
                market=seed.display_name,
                metro_code=seed.metro_code,
                period=month or "",
                source_mix="unavailable",
                stale_months=0,
                median_sale_price=None,
                median_sale_price_yoy=None,
                inventory=None,
                inventory_yoy=None,
                new_listings=None,
                homes_sold=None,
                median_dom=None,
                median_dom_yoy=None,
                months_of_supply=None,
                pending_sales=None,
                pending_sales_yoy=None,
                price_drops=None,
                price_drops_rate=None,
                price_cv_12m=None,
                extreme_swing_freq_12m=None,
                dom_volatility_12m=None,
                buy_box_share=None,
                buy_box_homes_sold=None,
                sales_persistence_6m=None,
                pct_pre_1980=None,
                pct_pre_1940=None,
                historic_district_share=None,
                active_wholesalers=None,
                active_cash_buyers=None,
                ppc_cpc_sell_house_fast=None,
            )
            _attach_optional_features(feature, competition_map, housing_map)
            rows.append(feature)
            continue

        selected = _get_selected_row(monthly, month)
        if selected is None:
            continue

        selected_ts = pd.Timestamp(selected["PERIOD_BEGIN"])
        selected_period = selected_ts.to_period("M")
        stale_months = _month_distance(target_period, selected_period) if target_period else 0
        previous_year = _fetch_previous_year(monthly, selected_ts)

        trailing_12 = _trailing(monthly, selected_ts, 12)
        trailing_6 = _trailing(monthly, selected_ts, 6)

        price_cv_12m = None
        if not trailing_12.empty:
            price_mean = trailing_12["median_sale_price"].mean(skipna=True)
            price_std = trailing_12["median_sale_price"].std(skipna=True)
            if pd.notna(price_mean) and price_mean not in (None, 0):
                price_cv_12m = float(price_std / price_mean) if pd.notna(price_std) else None

        extreme_swing_freq_12m = None
        if len(trailing_12) >= 2:
            mom = trailing_12["median_sale_price"].pct_change().abs()
            valid = mom.dropna()
            if not valid.empty:
                extreme_swing_freq_12m = float((valid > 0.08).mean())

        dom_volatility_12m = None
        if len(trailing_12) >= 2:
            dom_vol = trailing_12["median_dom"].std(skipna=True)
            if pd.notna(dom_vol):
                dom_volatility_12m = float(dom_vol)

        sales_persistence_6m = None
        if not trailing_6.empty:
            persistence = (trailing_6["homes_sold"].fillna(0) > 0).mean()
            sales_persistence_6m = float(persistence)

        median_sale_price = _safe_float(selected.get("median_sale_price"))
        inventory = _safe_float(selected.get("inventory"))
        new_listings = _safe_float(selected.get("new_listings"))
        homes_sold = _safe_float(selected.get("homes_sold"))
        median_dom = _safe_float(selected.get("median_dom"))
        months_of_supply = _safe_float(selected.get("months_of_supply"))
        pending_sales = _safe_float(selected.get("pending_sales"))
        price_drops = _safe_float(selected.get("price_drops"))
        buy_box_share = _safe_float(selected.get("buy_box_share"))
        buy_box_homes = _safe_float(selected.get("buy_box_homes_sold"))

        price_drops_rate = None
        if price_drops is not None and homes_sold is not None and homes_sold != 0:
            price_drops_rate = price_drops / homes_sold

        median_sale_price_yoy = _pct_change(
            median_sale_price,
            _safe_float(previous_year.get("median_sale_price")) if previous_year is not None else None,
        )
        inventory_yoy = _pct_change(
            inventory,
            _safe_float(previous_year.get("inventory")) if previous_year is not None else None,
        )
        pending_sales_yoy = _pct_change(
            pending_sales,
            _safe_float(previous_year.get("pending_sales")) if previous_year is not None else None,
        )
        median_dom_yoy = _pct_change(
            median_dom,
            _safe_float(previous_year.get("median_dom")) if previous_year is not None else None,
        )

        feature = MarketFeature(
            market=seed.display_name,
            metro_code=seed.metro_code,
            period=selected_period.strftime("%Y-%m"),
            source_mix="master_tsv",
            stale_months=max(0, stale_months),
            median_sale_price=median_sale_price,
            median_sale_price_yoy=median_sale_price_yoy,
            inventory=inventory,
            inventory_yoy=inventory_yoy,
            new_listings=new_listings,
            homes_sold=homes_sold,
            median_dom=median_dom,
            median_dom_yoy=median_dom_yoy,
            months_of_supply=months_of_supply,
            pending_sales=pending_sales,
            pending_sales_yoy=pending_sales_yoy,
            price_drops=price_drops,
            price_drops_rate=price_drops_rate,
            price_cv_12m=price_cv_12m,
            extreme_swing_freq_12m=extreme_swing_freq_12m,
            dom_volatility_12m=dom_volatility_12m,
            buy_box_share=buy_box_share,
            buy_box_homes_sold=buy_box_homes,
            sales_persistence_6m=sales_persistence_6m,
            pct_pre_1980=None,
            pct_pre_1940=None,
            historic_district_share=None,
            active_wholesalers=None,
            active_cash_buyers=None,
            ppc_cpc_sell_house_fast=None,
        )
        _attach_optional_features(feature, competition_map, housing_map)
        if feature.active_cash_buyers is not None or feature.active_wholesalers is not None:
            feature.source_mix += "+competition_csv"
        if feature.pct_pre_1980 is not None or feature.pct_pre_1940 is not None:
            feature.source_mix += "+housing_age_csv"
        rows.append(feature)

    return rows


def count_missing_core_fields(feature: MarketFeature) -> int:
    missing = 0
    for field_name in CORE_RAW_FIELDS:
        if getattr(feature, field_name) is None:
            missing += 1
    return missing
