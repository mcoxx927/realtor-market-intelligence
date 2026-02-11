"""Configuration schema and loader for Distressed Market Fit scoring."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class DataPaths:
    master_tsv: str = "city_market_tracker.tsv000.gz"
    core_market_root: str = "core_markets"
    competition_csv: str = "market_radar/inputs/competition_proxy.csv"
    housing_age_csv: str = "market_radar/inputs/housing_age_proxy.csv"


@dataclass
class HardFilters:
    min_homes_sold: int = 20
    max_months_of_supply: float = 6.5
    max_median_dom: float = 95.0


@dataclass
class BuyBox:
    target_price_min: int = 120000
    target_price_max: int = 380000
    target_rehab_level: str = "light_medium"


@dataclass
class DistressedFitConfig:
    target_month: Optional[str]
    markets_seed: str
    data_paths: DataPaths
    weights: Dict[str, float]
    hard_filters: HardFilters
    buy_box: BuyBox
    output_dir: str


DEFAULT_WEIGHTS: Dict[str, float] = {
    "distress_inflow": 0.20,
    "rehab_risk": 0.22,
    "spread_reliability": 0.20,
    "exit_liquidity": 0.18,
    "investor_demand_depth": 0.12,
    "competition_pressure": 0.08,
}


def _parse_scalar(raw: str) -> Any:
    value = raw.strip().strip('"').strip("'")
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    if value.lower() in {"none", "null"}:
        return None
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def load_simple_yaml(path: Path) -> Dict[str, Any]:
    """Load a minimal YAML config (nested mappings only)."""
    config: Dict[str, Any] = {}
    stack = [(0, config)]

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
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


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _as_data_paths(payload: Dict[str, Any]) -> DataPaths:
    return DataPaths(
        master_tsv=str(payload.get("master_tsv", DataPaths.master_tsv)),
        core_market_root=str(payload.get("core_market_root", DataPaths.core_market_root)),
        competition_csv=str(payload.get("competition_csv", DataPaths.competition_csv)),
        housing_age_csv=str(payload.get("housing_age_csv", DataPaths.housing_age_csv)),
    )


def _as_hard_filters(payload: Dict[str, Any]) -> HardFilters:
    return HardFilters(
        min_homes_sold=int(payload.get("min_homes_sold", HardFilters.min_homes_sold)),
        max_months_of_supply=float(payload.get("max_months_of_supply", HardFilters.max_months_of_supply)),
        max_median_dom=float(payload.get("max_median_dom", HardFilters.max_median_dom)),
    )


def _as_buy_box(payload: Dict[str, Any]) -> BuyBox:
    return BuyBox(
        target_price_min=int(payload.get("target_price_min", BuyBox.target_price_min)),
        target_price_max=int(payload.get("target_price_max", BuyBox.target_price_max)),
        target_rehab_level=str(payload.get("target_rehab_level", BuyBox.target_rehab_level)),
    )


def _validate_weights(weights: Dict[str, float]) -> None:
    missing = [k for k in DEFAULT_WEIGHTS if k not in weights]
    if missing:
        raise ValueError(f"Missing weight keys: {', '.join(missing)}")

    total = float(sum(weights.values()))
    if not (0.99 <= total <= 1.01):
        raise ValueError(f"Weights must sum to ~1.0, got {total:.4f}")


def load_config(config_path: Path) -> DistressedFitConfig:
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    defaults: Dict[str, Any] = {
        "target_month": None,
        "markets_seed": "market_radar/seeds_roanoke_4hr.csv",
        "data_paths": {
            "master_tsv": DataPaths.master_tsv,
            "core_market_root": DataPaths.core_market_root,
            "competition_csv": DataPaths.competition_csv,
            "housing_age_csv": DataPaths.housing_age_csv,
        },
        "weights": dict(DEFAULT_WEIGHTS),
        "hard_filters": {
            "min_homes_sold": HardFilters.min_homes_sold,
            "max_months_of_supply": HardFilters.max_months_of_supply,
            "max_median_dom": HardFilters.max_median_dom,
        },
        "buy_box": {
            "target_price_min": BuyBox.target_price_min,
            "target_price_max": BuyBox.target_price_max,
            "target_rehab_level": BuyBox.target_rehab_level,
        },
        "output_dir": "market_radar/outputs_distressed_fit",
    }

    raw = load_simple_yaml(config_path)
    merged = _deep_merge(defaults, raw)

    weights = {k: float(v) for k, v in merged.get("weights", {}).items()}
    _validate_weights(weights)

    return DistressedFitConfig(
        target_month=merged.get("target_month"),
        markets_seed=str(merged.get("markets_seed", defaults["markets_seed"])),
        data_paths=_as_data_paths(merged.get("data_paths", {})),
        weights=weights,
        hard_filters=_as_hard_filters(merged.get("hard_filters", {})),
        buy_box=_as_buy_box(merged.get("buy_box", {})),
        output_dir=str(merged.get("output_dir", defaults["output_dir"])),
    )


def resolve_optional_path(path_text: Optional[str], base_dir: Path) -> Optional[Path]:
    if not path_text:
        return None
    path = Path(path_text)
    if not path.is_absolute():
        path = base_dir / path
    return path
