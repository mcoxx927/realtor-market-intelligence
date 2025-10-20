import pandas as pd
import json
from datetime import datetime
import os

def calculate_market_health_score(data_row):
    """Calculate market health score (0-100) based on multiple factors"""
    score = 50  # Start neutral

    # Positive factors
    if data_row['pending_ratio'] > 0.5:
        score += 10
    elif data_row['pending_ratio'] > 0.4:
        score += 5

    if data_row['median_days_on_market'] < 45:
        score += 15
    elif data_row['median_days_on_market'] < 60:
        score += 10
    elif data_row['median_days_on_market'] < 75:
        score += 5

    if data_row['new_listing_count_mm'] > 0:
        score += 5

    if data_row['median_listing_price_mm'] > 0:
        score += 10
    elif data_row['median_listing_price_mm'] > -0.01:
        score += 5

    # Negative factors
    if data_row['price_reduced_count'] / data_row['active_listing_count'] > 0.5:
        score -= 15
    elif data_row['price_reduced_count'] / data_row['active_listing_count'] > 0.4:
        score -= 10

    if data_row['median_days_on_market_yy'] > 0.2:
        score -= 10
    elif data_row['median_days_on_market_yy'] > 0.1:
        score -= 5

    if data_row['median_listing_price_yy'] < -0.05:
        score -= 15
    elif data_row['median_listing_price_yy'] < 0:
        score -= 5

    return max(0, min(100, score))

def determine_sentiment(health_score, data_row):
    """Determine market sentiment"""
    if health_score >= 70:
        return "BULLISH"
    elif health_score >= 45:
        return "NEUTRAL"
    else:
        return "BEARISH"

def generate_alerts(current_data, prev_data, market_name):
    """Generate alerts based on thresholds"""
    alerts = []

    # HIGH SEVERITY
    if current_data['median_listing_price_mm'] < -0.03:
        alerts.append({
            "severity": "HIGH",
            "category": "PRICING",
            "metric": "median_listing_price",
            "trigger": "Median price dropped >3% month-over-month",
            "before": int(prev_data['median_listing_price']),
            "after": int(current_data['median_listing_price']),
            "change_pct": round(current_data['median_listing_price_mm'] * 100, 2),
            "context": "Significant price decline indicates weakening market conditions",
            "recommendation": "Review pricing strategy immediately; consider market timing"
        })

    if current_data['price_reduced_count_mm'] > 0.30:
        alerts.append({
            "severity": "HIGH",
            "category": "PRICING",
            "metric": "price_reduced_count",
            "trigger": "Price reductions increased >30% month-over-month",
            "before": int(prev_data['price_reduced_count']),
            "after": int(current_data['price_reduced_count']),
            "change_pct": round(current_data['price_reduced_count_mm'] * 100, 2),
            "context": "Surge in price reductions indicates growing seller pressure and weakening pricing power",
            "recommendation": "Consider more aggressive initial pricing to avoid price reductions later"
        })

    if current_data['new_listing_count_mm'] < -0.20:
        alerts.append({
            "severity": "HIGH",
            "category": "INVENTORY",
            "metric": "new_listing_count",
            "trigger": "New listings dropped >20% month-over-month",
            "before": int(prev_data['new_listing_count']),
            "after": int(current_data['new_listing_count']),
            "change_pct": round(current_data['new_listing_count_mm'] * 100, 2),
            "context": "Sharp drop in new supply suggests sellers are hesitant or holding back",
            "recommendation": "Monitor for supply constraints that could support pricing"
        })

    if current_data['pending_ratio'] < 0.35:
        alerts.append({
            "severity": "HIGH",
            "category": "MOMENTUM",
            "metric": "pending_ratio",
            "trigger": "Pending ratio dropped below 0.35",
            "before": round(prev_data['pending_ratio'], 4),
            "after": round(current_data['pending_ratio'], 4),
            "change_pct": round(current_data['pending_ratio_mm'] * 100, 2),
            "context": "Low pending ratio indicates weakening buyer demand relative to inventory",
            "recommendation": "Focus on marketing and staging to differentiate listings"
        })

    # MEDIUM SEVERITY
    if current_data['median_days_on_market_mm'] > 0.20:
        alerts.append({
            "severity": "MEDIUM",
            "category": "MOMENTUM",
            "metric": "median_days_on_market",
            "trigger": "Days on market increased >20% month-over-month",
            "before": int(prev_data['median_days_on_market']),
            "after": int(current_data['median_days_on_market']),
            "change_pct": round(current_data['median_days_on_market_mm'] * 100, 2),
            "context": "Homes taking longer to sell suggests softening demand or pricing issues",
            "recommendation": "Review pricing relative to comparable sales; enhance marketing efforts"
        })

    if current_data['active_listing_count_mm'] > 0.25:
        alerts.append({
            "severity": "MEDIUM",
            "category": "INVENTORY",
            "metric": "active_listing_count",
            "trigger": "Active inventory increased >25% month-over-month",
            "before": int(prev_data['active_listing_count']),
            "after": int(current_data['active_listing_count']),
            "change_pct": round(current_data['active_listing_count_mm'] * 100, 2),
            "context": "Rapid inventory build-up could pressure prices if demand doesn't keep pace",
            "recommendation": "Monitor absorption rates; be prepared to adjust pricing expectations"
        })

    if current_data['price_increased_count_mm'] < -0.30:
        alerts.append({
            "severity": "MEDIUM",
            "category": "PRICING",
            "metric": "price_increased_count",
            "trigger": "Price increases decreased >30% month-over-month",
            "before": int(prev_data['price_increased_count']),
            "after": int(current_data['price_increased_count']),
            "change_pct": round(current_data['price_increased_count_mm'] * 100, 2),
            "context": "Fewer sellers raising prices indicates reduced pricing confidence",
            "recommendation": "Price competitively from the start"
        })

    # Check YoY for medium severity
    if current_data['median_days_on_market_yy'] > 0.30:
        alerts.append({
            "severity": "MEDIUM",
            "category": "YOY",
            "metric": "median_days_on_market_yy",
            "trigger": "Days on market increased >30% year-over-year",
            "before": None,
            "after": int(current_data['median_days_on_market']),
            "change_pct": round(current_data['median_days_on_market_yy'] * 100, 2),
            "context": "Sustained slowdown in sales velocity compared to last year",
            "recommendation": "Adjust expectations for time to sale; plan accordingly"
        })

    # LOW SEVERITY
    if abs(current_data['new_listing_count_mm']) > 0.15:
        if not any(a['metric'] == 'new_listing_count' for a in alerts):
            alerts.append({
                "severity": "LOW",
                "category": "INVENTORY",
                "metric": "new_listing_count",
                "trigger": "New listings changed >15% month-over-month",
                "before": int(prev_data['new_listing_count']),
                "after": int(current_data['new_listing_count']),
                "change_pct": round(current_data['new_listing_count_mm'] * 100, 2),
                "context": "Notable change in new supply flow" + (" - increased seller confidence" if current_data['new_listing_count_mm'] > 0 else " - sellers holding back"),
                "recommendation": "Monitor trend continuation over next 2-3 months"
            })

    if abs(current_data['pending_ratio_mm']) > 0.10:
        if not any(a['metric'] == 'pending_ratio' for a in alerts):
            alerts.append({
                "severity": "LOW",
                "category": "MOMENTUM",
                "metric": "pending_ratio",
                "trigger": "Pending ratio changed >10% month-over-month",
                "before": round(prev_data['pending_ratio'], 4),
                "after": round(current_data['pending_ratio'], 4),
                "change_pct": round(current_data['pending_ratio_mm'] * 100, 2),
                "context": "Shift in buyer urgency relative to available inventory",
                "recommendation": "Watch for trend continuation"
            })

    return alerts

def process_market(df, market_name, output_dir):
    """Process data for a single market and generate all outputs"""

    # Filter for this market
    market_df = df[df['cbsa_title'] == market_name].sort_values('month_date').copy()

    # Get latest data (September 2025)
    latest = market_df[market_df['month_date_yyyymm'] == 202509].iloc[0]
    prev_month = market_df[market_df['month_date_yyyymm'] == 202508].iloc[0]

    # Calculate metrics
    health_score = calculate_market_health_score(latest)
    sentiment = determine_sentiment(health_score, latest)

    # Generate alerts
    alerts = generate_alerts(latest, prev_month, market_name)

    # Calculate derived metrics for last 12 months
    last_12_months = market_df[market_df['month_date_yyyymm'] >= 202410].tail(12)

    # Prepare data for dashboard
    dashboard_data = {
        "market_name": market_name,
        "report_date": "2025-09-01",
        "current_month": "September 2025",
        "health_score": health_score,
        "sentiment": sentiment,
        "current_metrics": {
            "median_listing_price": int(latest['median_listing_price']),
            "median_listing_price_mm": round(latest['median_listing_price_mm'] * 100, 2),
            "median_listing_price_yy": round(latest['median_listing_price_yy'] * 100, 2),
            "active_listing_count": int(latest['active_listing_count']),
            "active_listing_count_mm": round(latest['active_listing_count_mm'] * 100, 2),
            "active_listing_count_yy": round(latest['active_listing_count_yy'] * 100, 2),
            "median_days_on_market": int(latest['median_days_on_market']),
            "median_days_on_market_mm": round(latest['median_days_on_market_mm'] * 100, 2),
            "median_days_on_market_yy": round(latest['median_days_on_market_yy'] * 100, 2),
            "new_listing_count": int(latest['new_listing_count']),
            "new_listing_count_mm": round(latest['new_listing_count_mm'] * 100, 2),
            "new_listing_count_yy": round(latest['new_listing_count_yy'] * 100, 2),
            "pending_ratio": round(latest['pending_ratio'], 4),
            "pending_ratio_mm": round(latest['pending_ratio_mm'] * 100, 2),
            "pending_ratio_yy": round(latest['pending_ratio_yy'] * 100, 2),
            "price_reduced_count": int(latest['price_reduced_count']),
            "price_reduced_count_mm": round(latest['price_reduced_count_mm'] * 100, 2),
            "price_increased_count": int(latest['price_increased_count']),
            "price_increased_count_mm": round(latest['price_increased_count_mm'] * 100, 2),
            "median_price_per_sqft": int(latest['median_listing_price_per_square_foot']),
            "pending_listing_count": int(latest['pending_listing_count'])
        },
        "historical_data": market_df[market_df['month_date_yyyymm'] >= 202409].to_dict('records'),
        "alerts_count": len(alerts)
    }

    # Save dashboard data
    with open(os.path.join(output_dir, 'dashboard_data.json'), 'w') as f:
        json.dump(dashboard_data, f, default=str, indent=2)

    # Generate alerts JSON
    alerts_json = {
        "report_date": "2025-09-01",
        "market_name": market_name,
        "sentiment": sentiment,
        "health_score": health_score,
        "alerts": alerts,
        "summary": {
            "total_alerts": len(alerts),
            "high_severity": len([a for a in alerts if a['severity'] == 'HIGH']),
            "medium_severity": len([a for a in alerts if a['severity'] == 'MEDIUM']),
            "low_severity": len([a for a in alerts if a['severity'] == 'LOW'])
        }
    }

    with open(os.path.join(output_dir, f'alerts_{market_name.split(",")[0].lower().replace("-", "_").replace(" ", "_")}_2025-09.json'), 'w') as f:
        json.dump(alerts_json, f, indent=2)

    return dashboard_data, alerts_json, latest, market_df

# Main execution
if __name__ == "__main__":
    # Load data
    df = pd.read_excel('Realtor New Listings.xlsx', sheet_name='RDC_Inventory_Core_Metrics_Metr')
    df['month_date'] = pd.to_datetime(df['month_date_yyyymm'].astype(str), format='%Y%m')

    # Process Charlotte
    print("Processing Charlotte market...")
    charlotte_data, charlotte_alerts, charlotte_latest, charlotte_df = process_market(
        df,
        'Charlotte-Concord-Gastonia, NC-SC',
        'charlotte/2025-09'
    )

    # Process Roanoke
    print("Processing Roanoke market...")
    roanoke_data, roanoke_alerts, roanoke_latest, roanoke_df = process_market(
        df,
        'Roanoke, VA',
        'roanoke/2025-09'
    )

    print("\nProcessing complete!")
    print(f"Charlotte Health Score: {charlotte_data['health_score']} ({charlotte_data['sentiment']})")
    print(f"Charlotte Alerts: {charlotte_alerts['summary']['total_alerts']} total")
    print(f"\nRoanoke Health Score: {roanoke_data['health_score']} ({roanoke_data['sentiment']})")
    print(f"Roanoke Alerts: {roanoke_alerts['summary']['total_alerts']} total")
