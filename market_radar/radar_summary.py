"""
Generate the Roanoke 4-hour Market Radar summary.
"""

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))


def load_simple_yaml(path: Path) -> dict:
    """Load a minimal YAML config (mapping + nested mapping)."""
    config = {}
    stack = [(0, config)]

    for raw_line in path.read_text().splitlines():
        if not raw_line.strip() or raw_line.strip().startswith("#"):
            continue
        line = raw_line.split("#", 1)[0].rstrip()
        indent = len(line) - len(line.lstrip(" "))
        key, _, value = line.lstrip().partition(":")
        key = key.strip()
        value = value.strip()

        while stack and indent <= stack[-1][0] and len(stack) > 1:
            stack.pop()
        parent = stack[-1][1]

        if value == "":
            parent[key] = {}
            stack.append((indent, parent[key]))
        else:
            parent[key] = _parse_scalar(value)

    return config


@dataclass
class MarketMetrics:
    name: str
    display_name: str
    state: str
    metro_code: str
    period: str
    median_sale_price: Optional[int]
    median_sale_price_yoy: Optional[float]
    inventory: Optional[int]
    inventory_yoy: Optional[float]
    new_listings: Optional[int]
    homes_sold: Optional[int]
    # New fields for health score calculation
    median_dom: Optional[int]
    median_dom_yoy: Optional[float]
    months_of_supply: Optional[float]
    pending_sales: Optional[int]
    pending_sales_yoy: Optional[float]
    data_source: str


@dataclass
class ScoredMarket:
    metrics: MarketMetrics
    health_score: int  # 0-100 market strength (matches original pipeline)
    liquidity_score: float
    inventory_pressure_score: float
    price_fit_score: float
    dealability_score: float
    bucket: str
    health_bucket: str  # BULLISH/NEUTRAL/BEARISH


def _parse_scalar(value: str):
    if value is None:
        return None
    cleaned = value.strip().strip('"').strip("'")
    if cleaned.lower() in {"true", "false"}:
        return cleaned.lower() == "true"
    if cleaned.isdigit():
        return int(cleaned)
    try:
        return float(cleaned)
    except ValueError:
        return cleaned


def parse_report_month(report_month: Optional[str]) -> Optional[pd.Timestamp]:
    """Parse a YYYY-MM report month into a month-start timestamp."""
    if report_month is None:
        return None
    try:
        return pd.to_datetime(f"{report_month}-01", format="%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"Invalid --month value '{report_month}'. Expected YYYY-MM.") from exc


def load_seed_csv(seed_path: Path, limit: Optional[int] = None) -> List[dict]:
    """Load markets directly from seed CSV file."""
    markets = []
    with seed_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            metro_code = row.get("metro_code", "").strip()
            if not metro_code:
                continue
            markets.append({
                "market_name": row.get("market_name", "").strip(),
                "state": row.get("state", "").strip(),
                "metro_code": metro_code,
                "display_name": row.get("display_name", "").strip(),
                "output_directory": row.get("output_directory", "").strip(),
                "lat": _parse_scalar(row.get("lat", "")),
                "lon": _parse_scalar(row.get("lon", "")),
            })
    if limit:
        markets = markets[:limit]
    print(f"[INFO] Loaded {len(markets)} markets from {seed_path}")
    return markets


def load_universe(universe_path: Path, limit: Optional[int]) -> List[dict]:
    """Legacy function - load from universe JSON."""
    payload = json.loads(universe_path.read_text())
    markets = payload.get("markets", [])
    if limit:
        markets = markets[:limit]
    return markets


def find_latest_period(metro_dir: Path, report_month: Optional[str] = None) -> Optional[Path]:
    if not metro_dir.exists():
        return None
    if report_month:
        period_dir = metro_dir / report_month
        return period_dir if period_dir.exists() and period_dir.is_dir() else None
    period_dirs = [d for d in metro_dir.iterdir() if d.is_dir() and len(d.name) == 7 and d.name[4] == "-"]
    if not period_dirs:
        return None
    return sorted(period_dirs, key=lambda p: p.name)[-1]


def load_metrics_from_data_json(
    metro_dir: Path,
    slug: str,
    report_month: Optional[str] = None,
) -> Optional[MarketMetrics]:
    period_dir = find_latest_period(metro_dir, report_month)
    if not period_dir:
        return None
    data_file = period_dir / f"{slug}_data.json"
    if not data_file.exists():
        return None

    data = json.loads(data_file.read_text())
    trends = data.get("full_metro_trends", [])
    if not trends:
        return None
    if report_month:
        latest = next((row for row in trends if row.get("period") == report_month), None)
        if latest is None:
            return None
    else:
        latest = sorted(trends, key=lambda row: row.get("period", ""))[-1]

    return MarketMetrics(
        name=slug,
        display_name=data.get("metro", slug),
        state="",
        metro_code="",
        period=latest.get("period", data.get("period", "")),
        median_sale_price=_parse_scalar(str(latest.get("median_sale_price"))) if latest.get("median_sale_price") is not None else None,
        median_sale_price_yoy=latest.get("median_sale_price_yoy"),
        inventory=_parse_scalar(str(latest.get("inventory"))) if latest.get("inventory") is not None else None,
        inventory_yoy=latest.get("inventory_yoy"),
        new_listings=_parse_scalar(str(latest.get("new_listings"))) if latest.get("new_listings") is not None else None,
        homes_sold=_parse_scalar(str(latest.get("homes_sold"))) if latest.get("homes_sold") is not None else None,
        median_dom=_parse_scalar(str(latest.get("median_dom"))) if latest.get("median_dom") is not None else None,
        median_dom_yoy=latest.get("median_dom_yoy"),
        months_of_supply=latest.get("months_of_supply"),
        pending_sales=_parse_scalar(str(latest.get("pending_sales"))) if latest.get("pending_sales") is not None else None,
        pending_sales_yoy=latest.get("pending_sales_yoy"),
        data_source=str(data_file),
    )


def calculate_weighted_median_price(df: pd.DataFrame) -> Optional[float]:
    total_sales = df["HOMES_SOLD"].sum()
    if total_sales == 0:
        return None
    return (df["MEDIAN_SALE_PRICE"] * df["HOMES_SOLD"]).sum() / total_sales


def extract_metrics_from_df(
    df: pd.DataFrame,
    display_name: str,
    metro_code: str,
    report_month: Optional[str] = None,
) -> Optional[MarketMetrics]:
    """
    Extract market metrics from a pre-filtered DataFrame for a single metro.

    This is the core calculation logic, separated from file I/O for performance.
    The DataFrame should already be filtered to the target metro_code.
    """
    if df.empty:
        return None

    # Ensure PERIOD_BEGIN is datetime
    if not pd.api.types.is_datetime64_any_dtype(df["PERIOD_BEGIN"]):
        df = df.copy()
        df["PERIOD_BEGIN"] = pd.to_datetime(df["PERIOD_BEGIN"])

    target_period = parse_report_month(report_month)
    if target_period is not None:
        if not (df["PERIOD_BEGIN"] == target_period).any():
            return None
        df = df[df["PERIOD_BEGIN"] <= target_period]

    latest_period = df["PERIOD_BEGIN"].max()
    current_month = latest_period.strftime("%Y-%m")

    latest_df = df[df["PERIOD_BEGIN"] == latest_period]
    latest_price = calculate_weighted_median_price(latest_df)

    # Aggregate monthly metrics at metro level
    monthly = df.groupby("PERIOD_BEGIN").agg(
        inventory=("INVENTORY", "sum"),
        new_listings=("NEW_LISTINGS", "sum"),
        homes_sold=("HOMES_SOLD", "sum"),
        pending_sales=("PENDING_SALES", "sum"),
    ).reset_index()

    monthly = monthly.sort_values("PERIOD_BEGIN")
    latest_row = monthly.iloc[-1]

    def pct_change(curr: Optional[float], prev: Optional[float]) -> Optional[float]:
        if prev in (None, 0) or curr is None:
            return None
        return (float(curr) / float(prev)) - 1.0

    yoy_row = None
    if len(monthly) >= 13:
        yoy_row = monthly.iloc[-13]

    inventory_yoy = pct_change(latest_row["inventory"], yoy_row["inventory"] if yoy_row is not None else None)
    pending_sales_yoy = pct_change(latest_row["pending_sales"], yoy_row["pending_sales"] if yoy_row is not None else None)

    # Price YoY calculation
    price_yoy = None
    if len(df) >= 2:
        monthly_prices = df.groupby("PERIOD_BEGIN").apply(
            lambda g: calculate_weighted_median_price(g), include_groups=False
        ).reset_index()
        monthly_prices.columns = ["PERIOD_BEGIN", "price"]
        monthly_prices = monthly_prices.sort_values("PERIOD_BEGIN")
        if len(monthly_prices) >= 13:
            price_yoy = pct_change(monthly_prices.iloc[-1]["price"], monthly_prices.iloc[-13]["price"])

    # DOM: weighted average by homes sold for latest period
    median_dom = None
    if "MEDIAN_DOM" in latest_df.columns and "HOMES_SOLD" in latest_df.columns:
        valid_dom = latest_df[latest_df["MEDIAN_DOM"].notna() & (latest_df["HOMES_SOLD"] > 0)]
        if not valid_dom.empty:
            total_sales = valid_dom["HOMES_SOLD"].sum()
            if total_sales > 0:
                median_dom = int((valid_dom["MEDIAN_DOM"] * valid_dom["HOMES_SOLD"]).sum() / total_sales)

    # DOM YoY: compare weighted averages
    median_dom_yoy = None
    if "MEDIAN_DOM" in df.columns:
        def weighted_dom(g):
            valid = g[g["MEDIAN_DOM"].notna() & (g["HOMES_SOLD"] > 0)]
            if valid.empty or valid["HOMES_SOLD"].sum() == 0:
                return None
            return (valid["MEDIAN_DOM"] * valid["HOMES_SOLD"]).sum() / valid["HOMES_SOLD"].sum()

        monthly_dom = df.groupby("PERIOD_BEGIN").apply(weighted_dom, include_groups=False).reset_index()
        monthly_dom.columns = ["PERIOD_BEGIN", "dom"]
        monthly_dom = monthly_dom.sort_values("PERIOD_BEGIN").dropna()
        if len(monthly_dom) >= 13:
            median_dom_yoy = pct_change(monthly_dom.iloc[-1]["dom"], monthly_dom.iloc[-13]["dom"])

    # Months of Supply: inventory / homes_sold (metro level)
    months_of_supply = None
    if latest_row["homes_sold"] and latest_row["homes_sold"] > 0:
        months_of_supply = round(float(latest_row["inventory"]) / float(latest_row["homes_sold"]), 2)

    return MarketMetrics(
        name=display_name.lower().replace(",", "").replace(" ", "-"),
        display_name=display_name,
        state="",
        metro_code=metro_code,
        period=current_month,
        median_sale_price=int(latest_price) if latest_price else None,
        median_sale_price_yoy=price_yoy,
        inventory=int(latest_row["inventory"]) if pd.notna(latest_row["inventory"]) else None,
        inventory_yoy=inventory_yoy,
        new_listings=int(latest_row["new_listings"]) if pd.notna(latest_row["new_listings"]) else None,
        homes_sold=int(latest_row["homes_sold"]) if pd.notna(latest_row["homes_sold"]) else None,
        median_dom=median_dom,
        median_dom_yoy=median_dom_yoy,
        months_of_supply=months_of_supply,
        pending_sales=int(latest_row["pending_sales"]) if pd.notna(latest_row["pending_sales"]) else None,
        pending_sales_yoy=pending_sales_yoy,
        data_source="master_tsv",
    )


def load_master_tsv(tsv_path: Path) -> Optional[pd.DataFrame]:
    """
    Load the master TSV file once and prepare it for filtering.

    Returns a DataFrame filtered to 'All Residential' with PERIOD_BEGIN as datetime,
    or None if the file doesn't exist or can't be read.
    """
    if not tsv_path.exists():
        print(f"[WARN] Master TSV not found: {tsv_path}")
        return None

    print(f"[INFO] Loading master TSV: {tsv_path}")
    try:
        df = pd.read_csv(tsv_path, sep="\t", compression="gzip", low_memory=False)
    except Exception as e:
        print(f"[ERROR] Failed to load master TSV: {e}")
        return None

    # Pre-filter to All Residential and convert dates once
    df = df[df["PROPERTY_TYPE"] == "All Residential"].copy()
    df["PERIOD_BEGIN"] = pd.to_datetime(df["PERIOD_BEGIN"])
    df["PARENT_METRO_REGION_METRO_CODE"] = df["PARENT_METRO_REGION_METRO_CODE"].astype(str)

    print(f"[INFO] Loaded {len(df):,} rows for All Residential properties")
    return df


def load_metrics_from_master_tsv(
    tsv_path: Path,
    display_name: str,
    metro_code: str,
    report_month: Optional[str] = None,
) -> Optional[MarketMetrics]:
    """
    Load metrics directly from the master TSV file by filtering on metro_code.

    NOTE: This loads the entire TSV each time. For batch processing of multiple
    markets, use load_master_tsv() once and extract_metrics_from_df() per market.
    """
    if not tsv_path.exists():
        return None

    try:
        df = pd.read_csv(tsv_path, sep="\t", compression="gzip", low_memory=False)
    except Exception:
        return None

    # Filter by metro code and property type
    df = df[
        (df["PARENT_METRO_REGION_METRO_CODE"].astype(str) == str(metro_code)) &
        (df["PROPERTY_TYPE"] == "All Residential")
    ]

    return extract_metrics_from_df(df, display_name, metro_code, report_month=report_month)


def load_metrics_from_tsv(
    tsv_path: Path,
    display_name: str,
    metro_code: str,
    report_month: Optional[str] = None,
) -> Optional[MarketMetrics]:
    if not tsv_path.exists():
        return None

    df = pd.read_csv(tsv_path, sep="\t", low_memory=False)
    if df.empty:
        return None

    df["PERIOD_BEGIN"] = pd.to_datetime(df["PERIOD_BEGIN"])
    target_period = parse_report_month(report_month)
    if target_period is not None:
        if not (df["PERIOD_BEGIN"] == target_period).any():
            return None
        df = df[df["PERIOD_BEGIN"] <= target_period]

    latest_period = df["PERIOD_BEGIN"].max()
    current_month = latest_period.strftime("%Y-%m")

    latest_df = df[df["PERIOD_BEGIN"] == latest_period]
    latest_price = calculate_weighted_median_price(latest_df)

    monthly = df.groupby("PERIOD_BEGIN").agg(
        inventory=("INVENTORY", "sum"),
        new_listings=("NEW_LISTINGS", "sum"),
        homes_sold=("HOMES_SOLD", "sum"),
        median_sale_price=("MEDIAN_SALE_PRICE", lambda s: calculate_weighted_median_price(df.loc[s.index])),
    ).reset_index()

    monthly = monthly.sort_values("PERIOD_BEGIN")
    latest_row = monthly.iloc[-1]

    def pct_change(curr: Optional[float], prev: Optional[float]) -> Optional[float]:
        if prev in (None, 0) or curr is None:
            return None
        return (float(curr) / float(prev)) - 1.0

    yoy_row = None
    if len(monthly) >= 13:
        yoy_row = monthly.iloc[-13]

    inventory_yoy = pct_change(latest_row["inventory"], yoy_row["inventory"] if yoy_row is not None else None)
    price_yoy = pct_change(latest_row["median_sale_price"], yoy_row["median_sale_price"] if yoy_row is not None else None)

    # Calculate additional metrics if columns exist
    pending_sales = None
    pending_sales_yoy = None
    if "PENDING_SALES" in df.columns:
        monthly_pending = df.groupby("PERIOD_BEGIN").agg(pending=("PENDING_SALES", "sum")).reset_index()
        monthly_pending = monthly_pending.sort_values("PERIOD_BEGIN")
        if not monthly_pending.empty:
            pending_sales = int(monthly_pending.iloc[-1]["pending"])
            if len(monthly_pending) >= 13:
                pending_sales_yoy = pct_change(monthly_pending.iloc[-1]["pending"], monthly_pending.iloc[-13]["pending"])

    median_dom = None
    median_dom_yoy = None
    if "MEDIAN_DOM" in df.columns:
        valid_dom = latest_df[latest_df["MEDIAN_DOM"].notna() & (latest_df["HOMES_SOLD"] > 0)]
        if not valid_dom.empty:
            total_sales = valid_dom["HOMES_SOLD"].sum()
            if total_sales > 0:
                median_dom = int((valid_dom["MEDIAN_DOM"] * valid_dom["HOMES_SOLD"]).sum() / total_sales)

    months_of_supply = None
    if latest_row["homes_sold"] and latest_row["homes_sold"] > 0:
        months_of_supply = round(float(latest_row["inventory"]) / float(latest_row["homes_sold"]), 2)

    return MarketMetrics(
        name=tsv_path.stem.replace("_cities_filtered", ""),
        display_name=display_name,
        state="",
        metro_code=metro_code,
        period=current_month,
        median_sale_price=int(latest_price) if latest_price else None,
        median_sale_price_yoy=price_yoy,
        inventory=int(latest_row["inventory"]) if pd.notna(latest_row["inventory"]) else None,
        inventory_yoy=inventory_yoy,
        new_listings=int(latest_row["new_listings"]) if pd.notna(latest_row["new_listings"]) else None,
        homes_sold=int(latest_row["homes_sold"]) if pd.notna(latest_row["homes_sold"]) else None,
        median_dom=median_dom,
        median_dom_yoy=median_dom_yoy,
        months_of_supply=months_of_supply,
        pending_sales=pending_sales,
        pending_sales_yoy=pending_sales_yoy,
        data_source=str(tsv_path),
    )


def calculate_health_score(m: MarketMetrics) -> int:
    """
    Calculate health score (0-100) based on market fundamentals.

    Components (redistributed after removing price - focus on velocity/absorption):
    - Pending sales YOY (34 pts) - demand indicator
    - DOM velocity + absolute (33 pts) - market speed
    - Months of supply (33 pts) - inventory absorption

    Price YoY is intentionally excluded - for investors, price movement
    is not a health signal (declining prices can be opportunity).
    """
    score = 0

    # Pending sales strength (34 pts) - demand indicator
    pending_yoy = m.pending_sales_yoy
    if pending_yoy is not None:
        if pending_yoy > 0.10:
            score += 34
        elif pending_yoy > 0:
            score += 20
        else:
            score += 7
    else:
        score += 14  # Default middle ground

    # Velocity - DOM (33 pts) - considers BOTH trend AND absolute value
    # High absolute DOM is bad regardless of trend
    dom_yoy = m.median_dom_yoy
    dom_abs = m.median_dom

    # Start with YoY-based score
    if dom_yoy is not None:
        if dom_yoy < 0:
            dom_score = 33
        elif dom_yoy < 0.10:
            dom_score = 20
        else:
            dom_score = 7
    else:
        dom_score = 14

    # Apply absolute DOM penalty - high DOM is always bad
    if dom_abs is not None:
        if dom_abs > 90:
            dom_score = min(dom_score, 0)   # Very slow market - zero velocity points
        elif dom_abs > 70:
            dom_score = min(dom_score, 7)   # Slow market - cap at minimum
        elif dom_abs > 50:
            dom_score = min(dom_score, 20)  # Moderate - cap at mid

    score += dom_score

    # Inventory balance - Months of Supply (33 pts)
    mos = m.months_of_supply
    if mos is not None:
        if mos < 3:
            score += 33
        elif mos < 6:
            score += 20
        else:
            score += 7
    else:
        score += 14

    return min(score, 100)


def classify_health_bucket(health_score: int) -> str:
    """Classify market health into buckets."""
    if health_score >= 70:
        return "BULLISH"
    elif health_score >= 55:
        return "SLIGHTLY_BULLISH"
    elif health_score >= 45:
        return "NEUTRAL"
    elif health_score >= 35:
        return "SLIGHTLY_BEARISH"
    else:
        return "BEARISH"


def fmt_pct(val: Optional[float]) -> str:
    """Format a percentage value for output."""
    if val is None:
        return ""
    return f"{val:.1%}"


def normalize(values: List[Optional[float]]) -> List[float]:
    numeric = [v for v in values if v is not None]
    if not numeric:
        return [50.0 for _ in values]
    min_val = min(numeric)
    max_val = max(numeric)
    if min_val == max_val:
        return [50.0 for _ in values]
    normalized = []
    for val in values:
        if val is None:
            normalized.append(50.0)
        else:
            normalized.append((val - min_val) / (max_val - min_val) * 100)
    return normalized


def score_markets(
    metrics: List[MarketMetrics],
    weights: dict,
    price_band: dict,
    liquidity_floor: int = 50,
) -> List[ScoredMarket]:
    """
    Score markets using health score + investment criteria.

    Dealability formula:
    - Health Score (55%): Market strength (velocity, absorption, momentum, demand)
    - Price Fit (30%): Is price in your target investment band?
    - Liquidity (15%): Transaction volume with floor threshold

    Liquidity floor: markets with >= liquidity_floor homes sold get full (100) points.
    Below the floor, score scales linearly from 0 to 100.

    Health Score (0-100) uses the original pipeline formula:
    - Pending Sales YOY (25 pts)
    - DOM YOY (25 pts)
    - Months of Supply (25 pts)
    - Price YOY (25 pts)
    """
    # Calculate health scores
    health_scores = [calculate_health_score(m) for m in metrics]

    # Liquidity with floor threshold: >= floor gets 100, below scales linearly
    def calc_liquidity(m: MarketMetrics) -> float:
        volume = m.homes_sold or m.new_listings or 0
        if volume >= liquidity_floor:
            return 100.0
        return (volume / liquidity_floor) * 100.0

    liquidity_scores = [calc_liquidity(m) for m in metrics]

    scored = []
    for idx, market in enumerate(metrics):
        health = health_scores[idx]
        health_bucket = classify_health_bucket(health)

        # Price fit calculation
        price = market.median_sale_price
        band_min = price_band.get("min")
        band_max = price_band.get("max")
        if price is None or band_min is None or band_max is None:
            price_fit = 50.0
        elif band_min <= price <= band_max:
            price_fit = 100.0
        elif price < band_min:
            price_fit = max(0.0, 100 - ((band_min - price) / band_min) * 100)
        else:
            price_fit = max(0.0, 100 - ((price - band_max) / band_max) * 100)

        liquidity = liquidity_scores[idx]

        # Dealability = weighted combination
        # Health score is already 0-100, just use it directly
        total = (
            health * weights.get("health", 0.4)
            + liquidity * weights.get("liquidity", 0.4)
            + price_fit * weights.get("price_fit", 0.2)
        )

        if total >= 70:
            bucket = "GO DEEP"
        elif total >= 50:
            bucket = "WATCH"
        else:
            bucket = "AVOID"

        scored.append(
            ScoredMarket(
                metrics=market,
                health_score=health,
                liquidity_score=round(liquidity, 1),
                inventory_pressure_score=round(health, 1),  # Keep for compatibility
                price_fit_score=round(price_fit, 1),
                dealability_score=round(total, 1),
                bucket=bucket,
                health_bucket=health_bucket,
            )
        )

    scored.sort(key=lambda item: item.dealability_score, reverse=True)
    return scored


def write_csv(scored: List[ScoredMarket], output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "rank",
            "market",
            "period",
            "median_sale_price",
            "median_sale_price_yoy",
            "inventory",
            "inventory_yoy",
            "new_listings",
            "homes_sold",
            "median_dom",
            "median_dom_yoy",
            "months_of_supply",
            "pending_sales",
            "pending_sales_yoy",
            "health_score",
            "health_bucket",
            "dealability_score",
            "bucket",
            "data_source",
        ])
        for idx, item in enumerate(scored, start=1):
            m = item.metrics
            writer.writerow([
                idx,
                m.display_name,
                m.period,
                m.median_sale_price,
                fmt_pct(m.median_sale_price_yoy),
                m.inventory,
                fmt_pct(m.inventory_yoy),
                m.new_listings,
                m.homes_sold,
                m.median_dom,
                fmt_pct(m.median_dom_yoy),
                m.months_of_supply,
                m.pending_sales,
                fmt_pct(m.pending_sales_yoy),
                item.health_score,
                item.health_bucket,
                item.dealability_score,
                item.bucket,
                m.data_source,
            ])


def write_markdown(scored: List[ScoredMarket], config: dict, output_file: Path, month: str) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Roanoke 4-hour Market Radar ({month})",
        "",
        f"Home base: {config.get('home_base', 'Roanoke City, VA')}",
        "",
        "## Score Interpretation",
        "",
        "- **Health Score** (0-100): Market velocity based on pending sales (34pts), DOM (33pts), and months of supply (33pts)",
        "  - DOM considers both trend AND absolute value (high DOM penalized regardless of improvement)",
        "  - Price YoY intentionally excluded (for investors, price decline can be opportunity)",
        "- **Dealability Score** (0-100): Investment fit combining health (55%), price fit (30%), and liquidity (15%)",
        "- **Liquidity floor**: Markets with 50+ homes sold/month get full liquidity points",
        "",
        "## Ranked Markets",
        "",
    ]

    for idx, item in enumerate(scored, start=1):
        m = item.metrics
        price_str = f"${m.median_sale_price:,}" if m.median_sale_price else "N/A"
        lines.extend([
            f"### {idx}. {m.display_name}",
            "",
            f"**Dealability: {item.dealability_score}** ({item.bucket}) | **Health: {item.health_score}** ({item.health_bucket})",
            "",
            "| Metric | Value | YoY |",
            "|--------|-------|-----|",
            f"| Median Sale Price | {price_str} | {fmt_pct(m.median_sale_price_yoy)} |",
            f"| Inventory | {m.inventory or 'N/A'} | {fmt_pct(m.inventory_yoy)} |",
            f"| Homes Sold | {m.homes_sold or 'N/A'} | - |",
            f"| New Listings | {m.new_listings or 'N/A'} | - |",
            f"| Median DOM | {m.median_dom or 'N/A'} | {fmt_pct(m.median_dom_yoy)} |",
            f"| Months of Supply | {m.months_of_supply or 'N/A'} | - |",
            f"| Pending Sales | {m.pending_sales or 'N/A'} | {fmt_pct(m.pending_sales_yoy)} |",
            "",
        ])

    output_file.write_text("\n".join(lines))


def gather_metrics(
    markets: List[dict],
    config: dict,
    base_dir: Path,
    output_pattern: str,
    master_tsv_path: Optional[Path] = None,
    report_month: Optional[str] = None,
) -> List[MarketMetrics]:
    """
    Gather metrics for all markets from available data sources.

    Tries sources in order of preference:
    1. Pre-generated data.json (from full pipeline)
    2. Per-metro filtered TSV files
    3. Master TSV (loaded ONCE and filtered per market)
    """
    metrics = []
    master_df = None  # Lazy-load only if needed
    markets_needing_master = []  # Track markets that need master TSV

    # First pass: try fast sources (data.json, filtered TSV)
    for market in markets:
        slug = market.get("output_directory") or market.get("market_name", "").lower().replace(" ", "-")
        display_name = market.get("display_name") or f"{market.get('market_name')}, {market.get('state')}"
        metro_code = market.get("metro_code", "")

        # Try 1: Load from pre-generated data.json (full pipeline output)
        data_json_metrics = load_metrics_from_data_json(base_dir / slug, slug, report_month=report_month)
        if data_json_metrics:
            data_json_metrics.display_name = display_name
            data_json_metrics.metro_code = metro_code
            metrics.append(data_json_metrics)
            continue

        # Try 2: Load from per-metro filtered TSV
        tsv_path = base_dir / output_pattern.format(name=slug)
        tsv_metrics = load_metrics_from_tsv(tsv_path, display_name, metro_code, report_month=report_month)
        if tsv_metrics:
            metrics.append(tsv_metrics)
            continue

        # Mark for master TSV lookup
        if master_tsv_path and metro_code:
            markets_needing_master.append((display_name, metro_code))

    # Second pass: load master TSV ONCE for all remaining markets
    if markets_needing_master and master_tsv_path:
        master_df = load_master_tsv(master_tsv_path)
        if master_df is not None:
            print(f"[INFO] Processing {len(markets_needing_master)} markets from master TSV...")
            for idx, (display_name, metro_code) in enumerate(markets_needing_master, 1):
                # Filter to this metro from the pre-loaded DataFrame
                metro_df = master_df[master_df["PARENT_METRO_REGION_METRO_CODE"] == str(metro_code)]
                master_metrics = extract_metrics_from_df(
                    metro_df,
                    display_name,
                    metro_code,
                    report_month=report_month,
                )
                if master_metrics:
                    metrics.append(master_metrics)
                if idx % 10 == 0:
                    print(f"[INFO] Processed {idx}/{len(markets_needing_master)} markets...")

    return metrics


def run_radar(
    config_path: Path,
    seed_path: Path,
    month: Optional[str] = None,
    limit: Optional[int] = None,
) -> None:
    """
    Main entry point for running the market radar.

    Args:
        config_path: Path to radar YAML config
        seed_path: Path to seed CSV with markets
        month: Report month YYYY-MM (defaults to latest in data)
        limit: Limit number of markets for testing
    """
    config = load_simple_yaml(config_path)
    paths = config.get("paths", {})

    if month:
        parse_report_month(month)

    output_dir = Path(paths.get("outputs_dir", "market_radar/outputs"))
    master_tsv_path = BASE_DIR / paths.get("source_file", "city_market_tracker.tsv000.gz")

    # Load markets directly from seed CSV
    markets = load_seed_csv(seed_path, limit)
    if not markets:
        raise RuntimeError(f"No markets found in seed file: {seed_path}")

    # Gather metrics from master TSV
    output_pattern = "{name}_cities_filtered.tsv"
    metrics = gather_metrics(
        markets,
        config,
        BASE_DIR,
        output_pattern,
        master_tsv_path,
        report_month=month,
    )
    if not metrics:
        raise RuntimeError("No market metrics found. Ensure city_market_tracker.tsv000.gz exists.")

    # Use month from data if not specified
    if not month:
        month = metrics[0].period if metrics else datetime.utcnow().strftime("%Y-%m")

    # Score and rank markets
    weights = config.get("scoring_weights", {"health": 0.55, "liquidity": 0.15, "price_fit": 0.30})
    price_band = config.get("target_price_band", {"min": 110000, "max": 260000})
    liquidity_floor = config.get("liquidity_floor", 50)
    scored = score_markets(metrics, weights, price_band, liquidity_floor)

    # Write outputs
    csv_path = output_dir / month / f"Market_Radar_Roanoke_4hr_{month}.csv"
    md_path = output_dir / month / f"Market_Radar_Roanoke_4hr_{month}.md"

    write_csv(scored, csv_path)
    write_markdown(scored, config, md_path, month)

    print(f"[OK] Market Radar written to {csv_path} and {md_path}")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Generate the Roanoke 4-hour Market Radar summary.")
    parser.add_argument("--config", default="market_radar/roanoke_radar_config.yaml")
    parser.add_argument("--seeds", default="market_radar/seeds_roanoke_4hr.csv")
    parser.add_argument("--month", default=None, help="Report month YYYY-MM (defaults to latest in data).")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    run_radar(
        config_path=Path(args.config),
        seed_path=Path(args.seeds),
        month=args.month,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
