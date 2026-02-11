import unittest
from typing import Any

from market_radar.distressed_fit.config_schema import BuyBox, DataPaths, DistressedFitConfig, HardFilters
from market_radar.distressed_fit.features import MarketFeature
from market_radar.distressed_fit.scoring import score_markets


class DistressedFitScoringTests(unittest.TestCase):
    def setUp(self):
        self.config = DistressedFitConfig(
            target_month="2025-12",
            markets_seed="market_radar/seeds_roanoke_4hr.csv",
            data_paths=DataPaths(),
            weights={
                "distress_inflow": 0.20,
                "rehab_risk": 0.22,
                "spread_reliability": 0.20,
                "exit_liquidity": 0.18,
                "investor_demand_depth": 0.12,
                "competition_pressure": 0.08,
            },
            hard_filters=HardFilters(min_homes_sold=20, max_months_of_supply=6.5, max_median_dom=95),
            buy_box=BuyBox(),
            output_dir="market_radar/outputs_distressed_fit",
        )

    def _feature(self, market: str, metro_code: str, **overrides: Any) -> MarketFeature:
        base: dict[str, Any] = dict(
            market=market,
            metro_code=metro_code,
            period="2025-12",
            source_mix="master_tsv",
            stale_months=0,
            median_sale_price=250000.0,
            median_sale_price_yoy=0.01,
            inventory=300.0,
            inventory_yoy=0.10,
            new_listings=120.0,
            homes_sold=80.0,
            median_dom=45.0,
            median_dom_yoy=-0.05,
            months_of_supply=3.2,
            pending_sales=90.0,
            pending_sales_yoy=0.08,
            price_drops=12.0,
            price_drops_rate=0.15,
            price_cv_12m=0.08,
            extreme_swing_freq_12m=0.12,
            dom_volatility_12m=8.0,
            buy_box_share=0.62,
            buy_box_homes_sold=50.0,
            sales_persistence_6m=1.0,
            pct_pre_1980=None,
            pct_pre_1940=None,
            historic_district_share=None,
            active_wholesalers=None,
            active_cash_buyers=None,
            ppc_cpc_sell_house_fast=None,
        )
        base.update(overrides)
        return MarketFeature(**base)

    def test_disqualifies_low_volume_market(self):
        strong = self._feature("Strong Market", "11111", homes_sold=120)
        weak = self._feature("Weak Market", "22222", homes_sold=8)

        scored = score_markets([strong, weak], self.config)
        by_market = {row.market: row for row in scored}

        self.assertEqual(by_market["Weak Market"].decision_band, "DISQUALIFIED")
        self.assertIn("homes_sold<20", by_market["Weak Market"].disqualified_reason)

    def test_missing_core_fields_sets_low_confidence(self):
        healthy = self._feature("Healthy", "11111")
        missing = self._feature(
            "Missing",
            "22222",
            median_sale_price_yoy=None,
            inventory_yoy=None,
            pending_sales_yoy=None,
            median_dom=None,
            months_of_supply=None,
        )

        scored = score_markets([healthy, missing], self.config)
        by_market = {row.market: row for row in scored}

        self.assertEqual(by_market["Missing"].data_quality_flag, "LOW_CONFIDENCE")

    def test_ranks_non_disqualified_first(self):
        top = self._feature("Top", "11111", homes_sold=200, months_of_supply=2.0, median_dom=30)
        bottom = self._feature("Bottom", "22222", homes_sold=10, months_of_supply=7.0, median_dom=120)

        scored = score_markets([top, bottom], self.config)

        self.assertEqual(scored[0].market, "Top")
        self.assertEqual(scored[-1].decision_band, "DISQUALIFIED")


if __name__ == "__main__":
    unittest.main()
