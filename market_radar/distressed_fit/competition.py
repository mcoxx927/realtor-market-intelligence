"""Optional external-data adapters for competition and housing age proxies."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import pandas as pd


def _normalize_key(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def _to_row_map(df: pd.DataFrame) -> Dict[str, dict]:
    out: Dict[str, dict] = {}
    for _, row in df.iterrows():
        payload = {k: row[k] for k in df.columns}
        metro_code = _normalize_key(payload.get("metro_code"))
        market = _normalize_key(payload.get("market"))
        display_name = _normalize_key(payload.get("display_name"))

        if metro_code:
            out[f"metro_code:{metro_code}"] = payload
        if market:
            out[f"market:{market}"] = payload
        if display_name:
            out[f"display_name:{display_name}"] = payload
    return out


def load_optional_proxy_csv(path: Optional[Path]) -> Dict[str, dict]:
    if not path or not path.exists():
        return {}

    df = pd.read_csv(path, low_memory=False)
    if df.empty:
        return {}

    df.columns = [str(col).strip() for col in df.columns]
    return _to_row_map(df)


def lookup_proxy(proxy_map: Dict[str, dict], metro_code: str, display_name: str) -> dict:
    if not proxy_map:
        return {}

    metro_key = f"metro_code:{_normalize_key(metro_code)}"
    if metro_key in proxy_map:
        return proxy_map[metro_key]

    market_key = f"market:{_normalize_key(display_name)}"
    if market_key in proxy_map:
        return proxy_map[market_key]

    display_key = f"display_name:{_normalize_key(display_name)}"
    return proxy_map.get(display_key, {})
