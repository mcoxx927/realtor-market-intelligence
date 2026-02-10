"""
Extract summary data from JSON files with strategic analysis
Replaces AI agent analysis with Python-generated insights
"""
import json
import re
from pathlib import Path


def load_metro_config(config_path: Path) -> dict:
    """Load metro configuration from JSON file."""
    with open(config_path, 'r') as f:
        return json.load(f)


def find_latest_data_file(metro_dir: str, metro_name: str) -> tuple:
    """Find the latest data JSON file for a metro and return (data_file, period)"""
    metro_path = Path(metro_dir)
    period_pattern = re.compile(r'^\d{4}-\d{2}$')

    period_folders = [
        d for d in metro_path.iterdir()
        if d.is_dir() and period_pattern.match(d.name)
    ]

    if not period_folders:
        raise FileNotFoundError(f"No period folders found in {metro_dir}")

    latest_folder = sorted(period_folders, key=lambda x: x.name)[-1]
    data_file = latest_folder / f'{metro_name}_data.json'

    if not data_file.exists():
        raise FileNotFoundError(f"Data file not found: {data_file}")

    return str(data_file), latest_folder.name


def classify_market_status(health_score: int, avg_dom: int) -> tuple:
    """Classify market status and return (status, description)"""
    if health_score >= 70:
        return "BULLISH", "Strong seller's market with high demand"
    elif health_score >= 55:
        return "SLIGHTLY_BULLISH", "Leaning toward sellers with moderate competition"
    elif health_score >= 45:
        return "NEUTRAL", "Balanced market transitioning between buyer/seller advantage"
    elif health_score >= 35:
        return "SLIGHTLY_BEARISH", "Leaning toward buyers with softening demand"
    else:
        return "BEARISH", "Buyer's market with excess inventory"


def classify_city_tier(city: dict) -> str:
    """Classify city into market tier based on health score and DOM"""
    health = city.get('health', 50)
    dom = city.get('dom', 60)

    if health >= 65 and dom < 45:
        return "HOT"
    elif health >= 50 or dom < 60:
        return "BALANCED"
    else:
        return "BUYER"


def generate_recommendations(status: str, avg_dom: int, avg_health: int) -> dict:
    """Generate strategic recommendations based on market status"""
    recommendations = {}

    if status in ("BULLISH", "SLIGHTLY_BULLISH"):
        recommendations['sellers'] = f"Price at market value or slightly above. Expect {avg_dom-10}-{avg_dom} days on market. Multiple offers possible in hot submarkets."
        recommendations['buyers'] = "Act quickly on well-priced listings. Be prepared for competition. Consider escalation clauses in competitive areas."
        recommendations['investors'] = "Focus on appreciation plays in hot submarkets. Fix-and-flip viable with quick turnover expected."
    elif status == "NEUTRAL":
        recommendations['sellers'] = f"Price competitively at market value. Expect {avg_dom}-{avg_dom+15} days on market. Consider minor concessions for faster sale."
        recommendations['buyers'] = "Good negotiating position. Take time for due diligence. Room for price negotiation on listings over 45 days."
        recommendations['investors'] = "Balance appreciation and cash flow. Long-term holds recommended. Watch for distressed opportunities."
    else:  # BEARISH
        recommendations['sellers'] = f"Price 3-5% below recent comps for competitive positioning. Expect {avg_dom+10}+ days on market. Offer buyer incentives."
        recommendations['buyers'] = "Strong negotiating power. Request concessions on closing costs. No rush - inventory available."
        recommendations['investors'] = "Focus on cash flow properties. Deep value plays available. Avoid speculation, prioritize fundamentals."

    return recommendations


def extract_metro_summary(json_path: str) -> dict:
    """Extract key metrics with strategic analysis"""
    with open(json_path, 'r') as f:
        data = json.load(f)

    top_cities = data.get('top_cities', [])

    # Calculate metro-level metrics
    total_sales = sum(c.get('sales', 0) or 0 for c in top_cities)
    total_inventory = sum(c.get('inventory', 0) or 0 for c in top_cities)

    # Weighted averages
    if total_sales > 0:
        price_sum = sum((c.get('price', 0) or 0) * (c.get('sales', 0) or 0) for c in top_cities)
        avg_price = int(price_sum / total_sales)

        dom_sum = sum((c.get('dom', 0) or 0) * (c.get('sales', 0) or 0) for c in top_cities)
        avg_dom = int(dom_sum / total_sales)
    else:
        avg_price = 0
        avg_dom = 0

    # Average health score
    health_scores = [c.get('health', 50) for c in top_cities if c.get('health')]
    avg_health = int(sum(health_scores) / len(health_scores)) if health_scores else 50

    # Market status classification
    market_status, market_description = classify_market_status(avg_health, avg_dom)

    # City tier classification
    city_tiers = {"HOT": [], "BALANCED": [], "BUYER": []}
    for city in top_cities:
        tier = classify_city_tier(city)
        city_tiers[tier].append(city.get('name', ''))

    # Generate recommendations
    recommendations = generate_recommendations(market_status, avg_dom, avg_health)

    # Identify alert cities
    alert_cities = []
    for city in top_cities:
        alerts = []
        severity = 'LOW'

        price_yoy = city.get('price_yoy') or 0
        dom = city.get('dom') or 0
        months_supply = city.get('months_supply') or 0
        health = city.get('health') or 50

        # Price decline alert
        if price_yoy < -0.05:
            alerts.append(f"Price down {abs(price_yoy)*100:.1f}% YoY")
            severity = 'MEDIUM'

        # High DOM alert
        if dom > 70:
            alerts.append(f"High days on market: {dom} days")
            if severity == 'LOW':
                severity = 'MEDIUM'

        # Excess inventory alert
        if months_supply and months_supply > 6:
            alerts.append(f"Excess inventory: {months_supply:.1f} months supply")
            severity = 'HIGH'

        # Low health score alert
        if health < 40:
            alerts.append(f"Low health score: {health}/100")
            if severity == 'LOW':
                severity = 'MEDIUM'

        if alerts:
            # Generate city-specific recommendation
            if severity == 'HIGH':
                city_rec = "Aggressive pricing needed. Consider incentives. Extended timeline expected."
            elif severity == 'MEDIUM':
                city_rec = "Monitor closely. Price competitively. May need adjustment if no activity in 30 days."
            else:
                city_rec = "Minor concerns. Standard marketing approach should suffice."

            alert_cities.append({
                'name': city.get('name', ''),
                'sales': city.get('sales', 0),
                'price': city.get('price', 0),
                'price_yoy': price_yoy,
                'dom': dom,
                'inventory': city.get('inventory', 0),
                'months_supply': months_supply,
                'health': health,
                'severity': severity,
                'alerts': alerts,
                'recommendation': city_rec
            })

    # Sort alerts by severity
    severity_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
    alert_cities.sort(key=lambda x: severity_order.get(x['severity'], 3))

    # Build summary
    summary = {
        'metro_name': data.get('metro', ''),
        'report_period': data.get('period', ''),
        'metro_health_score': avg_health,
        'market_status': market_status,
        'market_description': market_description,

        'key_metrics': {
            'total_sales': total_sales,
            'total_inventory': total_inventory,
            'weighted_avg_price': avg_price,
            'weighted_avg_dom': avg_dom,
            'cities_analyzed': len(top_cities)
        },

        'city_tiers': {
            'hot_markets': city_tiers['HOT'],
            'balanced_markets': city_tiers['BALANCED'],
            'buyer_markets': city_tiers['BUYER']
        },

        'recommendations': recommendations,

        'alert_cities': alert_cities,
        'alert_count': {
            'high': len([a for a in alert_cities if a['severity'] == 'HIGH']),
            'medium': len([a for a in alert_cities if a['severity'] == 'MEDIUM']),
            'low': len([a for a in alert_cities if a['severity'] == 'LOW'])
        },

        'top_cities': top_cities,
        'metro_trends_12m': data.get('metro_trends', [])
    }

    return summary


def main():
    base_dir = Path(__file__).parent
    config_file = base_dir / 'metro_config.json'
    if not config_file.exists():
        raise FileNotFoundError("metro_config.json not found")

    config = load_metro_config(config_file)
    metros = [m for m in config.get('metros', []) if m.get('enabled', True)]
    if not metros:
        raise ValueError("No enabled metros found in metro_config.json")

    summaries = []

    for metro in metros:
        metro_slug = metro.get('name')
        metro_display = metro.get('display_name', metro_slug)
        if not metro_slug:
            raise ValueError("Metro config entry missing required field: name")

        metro_output_dir = base_dir / metro.get('output_directory', metro_slug)
        metro_json, period = find_latest_data_file(str(metro_output_dir), metro_slug)
        metro_summary = extract_metro_summary(metro_json)

        summary_output = metro_output_dir / period / f'{metro_slug}_summary.json'
        with open(summary_output, 'w') as f:
            json.dump(metro_summary, f, indent=2)
        print(f"[OK] {metro_display} summary: {summary_output}")

        summaries.append((metro_display, metro_summary))

    print(f"\n{'='*60}")
    print("METRO SUMMARY SNAPSHOT")
    print('='*60)
    for metro_display, summary in summaries:
        metrics = summary.get('key_metrics', {})
        print(
            f"{metro_display}: "
            f"period={summary.get('report_period', 'N/A')}, "
            f"health={summary.get('metro_health_score', 'N/A')}/100, "
            f"status={summary.get('market_status', 'N/A')}, "
            f"avg_dom={metrics.get('weighted_avg_dom', 'N/A')} days, "
            f"avg_price=${metrics.get('weighted_avg_price', 0):,}, "
            f"alerts={len(summary.get('alert_cities', []))}"
        )


if __name__ == '__main__':
    main()
