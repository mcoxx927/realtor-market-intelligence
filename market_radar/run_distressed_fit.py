"""CLI runner for distressed-market fit scoring."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import List

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from market_radar.distressed_fit.backtest import run_backtest
from market_radar.distressed_fit.competition import load_optional_proxy_csv
from market_radar.distressed_fit.config_schema import load_config, resolve_optional_path
from market_radar.distressed_fit.features import (
    build_feature_rows_for_month,
    load_master_monthly_series,
    load_seed_markets,
)
from market_radar.distressed_fit.scoring import ScoredMarket, score_markets


def _format_pct(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.4f}"


def _write_csv(scored: List[ScoredMarket], output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "rank",
                "market",
                "metro_code",
                "period",
                "distressed_fit_score",
                "decision_band",
                "disqualified_reason",
                "distress_inflow_idx",
                "rehab_risk_idx",
                "spread_reliability_idx",
                "exit_liquidity_idx",
                "investor_depth_idx",
                "competition_pressure_idx",
                "median_sale_price",
                "median_sale_price_yoy",
                "inventory",
                "inventory_yoy",
                "homes_sold",
                "median_dom",
                "months_of_supply",
                "pending_sales_yoy",
                "data_quality_flag",
                "source_mix",
            ]
        )
        for row in scored:
            f = row.feature
            writer.writerow(
                [
                    row.rank,
                    row.market,
                    row.metro_code,
                    row.period,
                    row.distressed_fit_score,
                    row.decision_band,
                    row.disqualified_reason,
                    row.distress_inflow_idx,
                    row.rehab_risk_idx,
                    row.spread_reliability_idx,
                    row.exit_liquidity_idx,
                    row.investor_depth_idx,
                    row.competition_pressure_idx,
                    f.median_sale_price,
                    _format_pct(f.median_sale_price_yoy),
                    f.inventory,
                    _format_pct(f.inventory_yoy),
                    f.homes_sold,
                    f.median_dom,
                    f.months_of_supply,
                    _format_pct(f.pending_sales_yoy),
                    row.data_quality_flag,
                    row.source_mix,
                ]
            )


def _write_markdown(scored: List[ScoredMarket], output_file: Path, month: str) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)

    top = [s for s in scored if s.decision_band != "DISQUALIFIED"][:20]
    disqualified = [s for s in scored if s.decision_band == "DISQUALIFIED"]

    lines = [
        f"# Distressed Market Fit ({month})",
        "",
        "## What This Ranks",
        "",
        "Markets are ranked by distressed fit: distress inflow, rehab risk, spread reliability, exit liquidity, investor demand depth, and competition pressure.",
        "",
        "## Top Ranked Markets",
        "",
        "| Rank | Market | Score | Band | Homes Sold | MOS | DOM | Price YoY | Pending YoY |",
        "|------|--------|-------|------|------------|-----|-----|-----------|-------------|",
    ]

    for row in top:
        f = row.feature
        price_yoy = "" if f.median_sale_price_yoy is None else f"{f.median_sale_price_yoy:.1%}"
        pending_yoy = "" if f.pending_sales_yoy is None else f"{f.pending_sales_yoy:.1%}"
        mos = "" if f.months_of_supply is None else f"{f.months_of_supply:.2f}"
        dom = "" if f.median_dom is None else f"{f.median_dom:.0f}"
        homes = "" if f.homes_sold is None else f"{f.homes_sold:.0f}"
        lines.append(
            f"| {row.rank} | {row.market} | {row.distressed_fit_score:.1f} | {row.decision_band} | {homes} | {mos} | {dom} | {price_yoy} | {pending_yoy} |"
        )

    if disqualified:
        lines.extend(
            [
                "",
                "## Disqualified Markets",
                "",
                "| Rank | Market | Score | Reason |",
                "|------|--------|-------|--------|",
            ]
        )
        for row in disqualified:
            lines.append(
                f"| {row.rank} | {row.market} | {row.distressed_fit_score:.1f} | {row.disqualified_reason or 'N/A'} |"
            )

    output_file.write_text("\n".join(lines), encoding="utf-8")


def _write_diagnostics(
    scored: List[ScoredMarket],
    output_file: Path,
    config_path: Path,
    target_month: str,
    backtest_result: dict | None,
) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)

    scores = [s.distressed_fit_score for s in scored]
    decision_counts = {}
    quality_counts = {}
    for row in scored:
        decision_counts[row.decision_band] = decision_counts.get(row.decision_band, 0) + 1
        quality_counts[row.data_quality_flag] = quality_counts.get(row.data_quality_flag, 0) + 1

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "target_month": target_month,
        "config_path": str(config_path),
        "markets_scored": len(scored),
        "score_summary": {
            "avg": round(mean(scores), 3) if scores else None,
            "min": min(scores) if scores else None,
            "max": max(scores) if scores else None,
        },
        "decision_counts": decision_counts,
        "data_quality_counts": quality_counts,
        "backtest": backtest_result,
    }
    output_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run distressed-market fit scoring")
    parser.add_argument(
        "--config",
        default="market_radar/distressed_fit_config.yaml",
        help="Path to distressed-fit config YAML",
    )
    parser.add_argument("--month", default=None, help="Target month YYYY-MM (default: latest)")
    parser.add_argument("--limit", type=int, default=None, help="Limit markets for quick testing")
    parser.add_argument("--with-backtest", action="store_true", help="Run six-month rolling backtest")
    parser.add_argument("--competition-csv", default=None, help="Optional override path for competition proxy CSV")
    parser.add_argument("--housing-age-csv", default=None, help="Optional override path for housing age proxy CSV")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = BASE_DIR / config_path

    config = load_config(config_path)

    if args.month:
        config.target_month = args.month
    if args.competition_csv:
        config.data_paths.competition_csv = args.competition_csv
    if args.housing_age_csv:
        config.data_paths.housing_age_csv = args.housing_age_csv

    seed_path = Path(config.markets_seed)
    if not seed_path.is_absolute():
        seed_path = BASE_DIR / seed_path

    print(f"[INFO] Loading seed markets from {seed_path}")
    seeds = load_seed_markets(seed_path, limit=args.limit)
    if not seeds:
        raise RuntimeError("No markets found in seed file")
    print(f"[INFO] Loaded {len(seeds)} market seeds")

    competition_path = resolve_optional_path(config.data_paths.competition_csv, BASE_DIR)
    housing_path = resolve_optional_path(config.data_paths.housing_age_csv, BASE_DIR)
    competition_map = load_optional_proxy_csv(competition_path)
    housing_map = load_optional_proxy_csv(housing_path)

    if competition_map:
        print(f"[INFO] Loaded competition proxy rows from {competition_path}")
    else:
        print(f"[WARN] Competition proxy missing or empty: {competition_path}")

    if housing_map:
        print(f"[INFO] Loaded housing-age proxy rows from {housing_path}")
    else:
        print(f"[WARN] Housing-age proxy missing or empty: {housing_path}")

    master_tsv = Path(config.data_paths.master_tsv)
    if not master_tsv.is_absolute():
        master_tsv = BASE_DIR / master_tsv

    print(f"[INFO] Aggregating master market data from {master_tsv}")
    monthly_by_metro, all_periods = load_master_monthly_series(
        master_tsv,
        metro_codes=[seed.metro_code for seed in seeds],
        buy_box_min=config.buy_box.target_price_min,
        buy_box_max=config.buy_box.target_price_max,
    )

    if not all_periods:
        raise RuntimeError("No periods available after filtering master TSV")

    target_month = config.target_month or all_periods[-1]
    print(f"[INFO] Target month: {target_month}")

    feature_rows = build_feature_rows_for_month(
        monthly_by_metro=monthly_by_metro,
        seeds=seeds,
        month=target_month,
        competition_map=competition_map,
        housing_map=housing_map,
    )

    scored = score_markets(feature_rows, config)

    output_root = Path(config.output_dir)
    if not output_root.is_absolute():
        output_root = BASE_DIR / output_root
    output_dir = output_root / target_month
    csv_path = output_dir / "distressed_fit_ranked.csv"
    md_path = output_dir / "distressed_fit_ranked.md"
    diag_path = output_dir / "distressed_fit_diagnostics.json"

    _write_csv(scored, csv_path)
    _write_markdown(scored, md_path, target_month)

    backtest_result = None
    if args.with_backtest:
        print("[INFO] Running six-month rolling backtest")
        backtest_result = run_backtest(
            monthly_by_metro=monthly_by_metro,
            seeds=seeds,
            config=config,
            all_periods=all_periods,
            competition_map=competition_map,
            housing_map=housing_map,
            target_month=target_month,
        )

    _write_diagnostics(
        scored=scored,
        output_file=diag_path,
        config_path=config_path,
        target_month=target_month,
        backtest_result=backtest_result,
    )

    print(f"[OK] Distressed-fit CSV: {csv_path}")
    print(f"[OK] Distressed-fit markdown: {md_path}")
    print(f"[OK] Distressed-fit diagnostics: {diag_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
