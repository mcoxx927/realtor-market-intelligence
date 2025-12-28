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

from market_radar.market_universe import load_simple_yaml


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
    data_source: str


@dataclass
class ScoredMarket:
    metrics: MarketMetrics
    liquidity_score: float
    inventory_pressure_score: float
    price_fit_score: float
    dealability_score: float
    bucket: str


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


def load_universe(universe_path: Path, limit: Optional[int]) -> List[dict]:
    payload = json.loads(universe_path.read_text())
    markets = payload.get("markets", [])
    if limit:
        markets = markets[:limit]
    return markets


def find_latest_period(metro_dir: Path) -> Optional[Path]:
    if not metro_dir.exists():
        return None
    period_dirs = [d for d in metro_dir.iterdir() if d.is_dir() and len(d.name) == 7 and d.name[4] == "-"]
    if not period_dirs:
        return None
    return sorted(period_dirs, key=lambda p: p.name)[-1]


def load_metrics_from_data_json(metro_dir: Path, slug: str) -> Optional[MarketMetrics]:
    period_dir = find_latest_period(metro_dir)
    if not period_dir:
        return None
    data_file = period_dir / f"{slug}_data.json"
    if not data_file.exists():
        return None

    data = json.loads(data_file.read_text())
    trends = data.get("full_metro_trends", [])
    if not trends:
        return None
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
        data_source=str(data_file),
    )


def calculate_weighted_median_price(df: pd.DataFrame) -> Optional[float]:
    total_sales = df["HOMES_SOLD"].sum()
    if total_sales == 0:
        return None
    return (df["MEDIAN_SALE_PRICE"] * df["HOMES_SOLD"]).sum() / total_sales


def load_metrics_from_tsv(tsv_path: Path, display_name: str, metro_code: str) -> Optional[MarketMetrics]:
    if not tsv_path.exists():
        return None

    df = pd.read_csv(tsv_path, sep="\t", low_memory=False)
    if df.empty:
        return None

    df["PERIOD_BEGIN"] = pd.to_datetime(df["PERIOD_BEGIN"])
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
        data_source=str(tsv_path),
    )


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


def score_markets(metrics: List[MarketMetrics], weights: dict, price_band: dict) -> List[ScoredMarket]:
    liquidity_values = [m.homes_sold or m.new_listings for m in metrics]
    inventory_values = [m.inventory_yoy for m in metrics]
    price_growth_values = [-(m.median_sale_price_yoy or 0) for m in metrics]

    liquidity_scores = normalize(liquidity_values)
    inventory_scores = normalize(inventory_values)
    price_growth_scores = normalize(price_growth_values)

    scored = []
    for idx, market in enumerate(metrics):
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
        inventory_pressure = (inventory_scores[idx] + price_growth_scores[idx]) / 2

        total = (
            liquidity * weights.get("liquidity", 0.4)
            + inventory_pressure * weights.get("inventory_pressure", 0.4)
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
                liquidity_score=round(liquidity, 1),
                inventory_pressure_score=round(inventory_pressure, 1),
                price_fit_score=round(price_fit, 1),
                dealability_score=round(total, 1),
                bucket=bucket,
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
                m.median_sale_price_yoy,
                m.inventory,
                m.inventory_yoy,
                m.new_listings,
                m.homes_sold,
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
        "## Ranked Markets",
        "",
    ]

    for idx, item in enumerate(scored, start=1):
        m = item.metrics
        lines.extend([
            f"{idx}. **{m.display_name}** — Dealability {item.dealability_score} ({item.bucket})",
            f"   - Median sale price: {m.median_sale_price}",
            f"   - Price YoY: {m.median_sale_price_yoy}",
            f"   - Inventory: {m.inventory}",
            f"   - Inventory YoY: {m.inventory_yoy}",
            f"   - Homes sold: {m.homes_sold}",
            f"   - New listings: {m.new_listings}",
            f"   - Data source: {m.data_source}",
            "",
        ])

    output_file.write_text("\n".join(lines))


def gather_metrics(
    markets: List[dict],
    config: dict,
    base_dir: Path,
    output_pattern: str,
) -> List[MarketMetrics]:
    metrics = []
    for market in markets:
        slug = market.get("output_directory") or market.get("market_name", "").lower().replace(" ", "-")
        display_name = market.get("display_name") or f"{market.get('market_name')}, {market.get('state')}"
        metro_code = market.get("metro_code", "")

        data_json_metrics = load_metrics_from_data_json(base_dir / slug, slug)
        if data_json_metrics:
            data_json_metrics.display_name = display_name
            data_json_metrics.metro_code = metro_code
            metrics.append(data_json_metrics)
            continue

        tsv_path = base_dir / output_pattern.format(name=slug)
        tsv_metrics = load_metrics_from_tsv(tsv_path, display_name, metro_code)
        if tsv_metrics:
            metrics.append(tsv_metrics)

    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the Roanoke 4-hour Market Radar summary.")
    parser.add_argument("--config", default="market_radar/roanoke_radar_config.yaml")
    parser.add_argument("--universe", default=None)
    parser.add_argument("--month", default=None, help="Report month YYYY-MM (defaults to current month).")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    config_path = Path(args.config)
    config = load_simple_yaml(config_path)
    paths = config.get("paths", {})

    universe_path = Path(args.universe or paths.get("universe_json", "market_radar/roanoke_4hr_universe.json"))
    output_dir = Path(paths.get("outputs_dir", "outputs"))
    metro_config_path = Path(paths.get("metro_config", "metro_config.json"))
    output_pattern = json.loads(metro_config_path.read_text()).get("data_settings", {}).get("output_file_pattern", "{name}_cities_filtered.tsv")

    month = args.month or datetime.utcnow().strftime("%Y-%m")

    markets = load_universe(universe_path, args.limit)
    base_dir = Path(__file__).resolve().parents[1]

    metrics = gather_metrics(markets, config, base_dir, output_pattern)
    if not metrics:
        raise RuntimeError("No market metrics were found. Run the pipeline or extract metros first.")

    weights = config.get("scoring_weights", {"liquidity": 0.4, "inventory_pressure": 0.4, "price_fit": 0.2})
    price_band = config.get("target_price_band", {"min": 110000, "max": 260000})

    scored = score_markets(metrics, weights, price_band)

    csv_path = output_dir / month / f"Market_Radar_Roanoke_4hr_{month}.csv"
    md_path = output_dir / month / f"Market_Radar_Roanoke_4hr_{month}.md"

    write_csv(scored, csv_path)
    write_markdown(scored, config, md_path, month)

    print(f"[OK] Market Radar written to {csv_path} and {md_path}")


if __name__ == "__main__":
    main()
