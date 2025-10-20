import pandas as pd
import numpy as np
from datetime import datetime

# Read the main data sheet
file_path = r"C:\Users\1\Documents\GitHub\realtor monthly data analysis\Realtor New Listings.xlsx"
df = pd.read_excel(file_path, sheet_name='RDC_Inventory_Core_Metrics_Metr')

# Convert month_date_yyyymm to datetime
df['date'] = pd.to_datetime(df['month_date_yyyymm'].astype(str), format='%Y%m')
df = df.sort_values('date')

print("=" * 100)
print("COMPREHENSIVE REAL ESTATE MARKET ANALYSIS REPORT")
print("=" * 100)
print(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Data Period: {df['date'].min().strftime('%B %Y')} to {df['date'].max().strftime('%B %Y')}")
print(f"Number of Months: {df['date'].nunique()}")

# Identify unique markets
markets = df['cbsa_title'].unique()
print(f"\nMarkets Analyzed: {len(markets)}")
for i, market in enumerate(markets, 1):
    print(f"  {i}. {market}")

print("\n" + "=" * 100)
print("1. MARKET-BY-MARKET DETAILED ANALYSIS")
print("=" * 100)

for market in markets:
    market_data = df[df['cbsa_title'] == market].copy()
    latest = market_data.iloc[-1]
    previous = market_data.iloc[-2] if len(market_data) > 1 else None
    oldest = market_data.iloc[0]

    print(f"\n{'=' * 100}")
    print(f"MARKET: {market}")
    print(f"{'=' * 100}")

    print(f"\nLatest Data Point: {latest['date'].strftime('%B %Y')}")
    print(f"Household Rank: #{latest['HouseholdRank']} (Market Size Indicator)")

    print(f"\n--- PRICING METRICS ---")
    print(f"Median Listing Price: ${latest['median_listing_price']:,}")
    if previous is not None:
        price_change_mom = ((latest['median_listing_price'] - previous['median_listing_price']) / previous['median_listing_price'] * 100)
        print(f"  Month-over-Month Change: {price_change_mom:+.2f}%")
    print(f"  Year-over-Year Change: {latest['median_listing_price_yy']*100:+.2f}%")

    print(f"\nAverage Listing Price: ${latest['average_listing_price']:,}")
    print(f"  Year-over-Year Change: {latest['average_listing_price_yy']*100:+.2f}%")

    print(f"\nPrice Per Square Foot: ${latest['median_listing_price_per_square_foot']}")
    print(f"  Year-over-Year Change: {latest['median_listing_price_per_square_foot_yy']*100:+.2f}%")

    print(f"\nMedian Square Feet: {latest['median_square_feet']:,} sq ft")
    print(f"  Year-over-Year Change: {latest['median_square_feet_yy']*100:+.2f}%")

    print(f"\n--- INVENTORY METRICS ---")
    print(f"Active Listings: {latest['active_listing_count']:,}")
    print(f"  Month-over-Month Change: {latest['active_listing_count_mm']*100:+.2f}%")
    print(f"  Year-over-Year Change: {latest['active_listing_count_yy']*100:+.2f}%")

    print(f"\nTotal Listings: {latest['total_listing_count']:,}")
    print(f"  Year-over-Year Change: {latest['total_listing_count_yy']*100:+.2f}%")

    print(f"\n--- MARKET VELOCITY METRICS ---")
    print(f"Median Days on Market: {latest['median_days_on_market']} days")
    print(f"  Month-over-Month Change: {latest['median_days_on_market_mm']*100:+.2f}%")
    print(f"  Year-over-Year Change: {latest['median_days_on_market_yy']*100:+.2f}%")

    print(f"\nNew Listings: {latest['new_listing_count']:,}")
    print(f"  Month-over-Month Change: {latest['new_listing_count_mm']*100:+.2f}%")
    print(f"  Year-over-Year Change: {latest['new_listing_count_yy']*100:+.2f}%")

    print(f"\nPending Listings: {latest['pending_listing_count']:,}")
    print(f"  Month-over-Month Change: {latest['pending_listing_count_mm']*100:+.2f}%")
    print(f"  Year-over-Year Change: {latest['pending_listing_count_yy']*100:+.2f}%")

    print(f"\nPending Ratio: {latest['pending_ratio']:.4f}")
    print(f"  (Ratio of pending to total listings - higher indicates stronger demand)")
    print(f"  Month-over-Month Change: {latest['pending_ratio_mm']*100:+.2f}%")
    print(f"  Year-over-Year Change: {latest['pending_ratio_yy']*100:+.2f}%")

    print(f"\n--- PRICING DYNAMICS ---")
    print(f"Price Increases: {latest['price_increased_count']:,} listings")
    print(f"  Year-over-Year Change: {latest['price_increased_count_yy']*100:+.2f}%")

    print(f"\nPrice Reductions: {latest['price_reduced_count']:,} listings")
    print(f"  Month-over-Month Change: {latest['price_reduced_count_mm']*100:+.2f}%")
    print(f"  Year-over-Year Change: {latest['price_reduced_count_yy']*100:+.2f}%")

    reduction_ratio = latest['price_reduced_count'] / latest['active_listing_count'] if latest['active_listing_count'] > 0 else 0
    print(f"\nPrice Reduction Ratio: {reduction_ratio*100:.2f}% of active listings")

    print(f"\n--- HISTORICAL TRENDS (Since {oldest['date'].strftime('%B %Y')}) ---")
    price_total_change = ((latest['median_listing_price'] - oldest['median_listing_price']) / oldest['median_listing_price'] * 100)
    inventory_total_change = ((latest['active_listing_count'] - oldest['active_listing_count']) / oldest['active_listing_count'] * 100)
    dom_total_change = ((latest['median_days_on_market'] - oldest['median_days_on_market']) / oldest['median_days_on_market'] * 100)

    print(f"Total Median Price Change: {price_total_change:+.2f}%")
    print(f"Total Active Inventory Change: {inventory_total_change:+.2f}%")
    print(f"Total Days on Market Change: {dom_total_change:+.2f}%")

    # Calculate 3-month averages
    if len(market_data) >= 3:
        recent_3mo = market_data.tail(3)
        print(f"\n--- 3-MONTH AVERAGES (Recent Trend) ---")
        print(f"Avg Median Price: ${recent_3mo['median_listing_price'].mean():,.0f}")
        print(f"Avg Active Listings: {recent_3mo['active_listing_count'].mean():,.0f}")
        print(f"Avg Days on Market: {recent_3mo['median_days_on_market'].mean():.0f} days")
        print(f"Avg New Listings: {recent_3mo['new_listing_count'].mean():,.0f}")
        print(f"Avg Pending Ratio: {recent_3mo['pending_ratio'].mean():.4f}")

print("\n" + "=" * 100)
print("2. COMPARATIVE MARKET ANALYSIS")
print("=" * 100)

# Latest data comparison
latest_data = df[df['date'] == df['date'].max()]

print(f"\nAs of {latest_data['date'].iloc[0].strftime('%B %Y')}:\n")

comparison_metrics = {
    'Median Price': 'median_listing_price',
    'Active Listings': 'active_listing_count',
    'Days on Market': 'median_days_on_market',
    'New Listings': 'new_listing_count',
    'Pending Ratio': 'pending_ratio',
    'Price/Sq Ft': 'median_listing_price_per_square_foot',
    'Price Reductions': 'price_reduced_count'
}

for metric_name, metric_col in comparison_metrics.items():
    print(f"\n{metric_name}:")
    for _, row in latest_data.iterrows():
        value = row[metric_col]
        if metric_name == 'Median Price' or metric_name == 'Price/Sq Ft':
            print(f"  {row['cbsa_title']:<45} ${value:>10,}")
        elif metric_name == 'Pending Ratio':
            print(f"  {row['cbsa_title']:<45} {value:>10.4f}")
        elif metric_name == 'Days on Market':
            print(f"  {row['cbsa_title']:<45} {value:>10} days")
        else:
            print(f"  {row['cbsa_title']:<45} {value:>10,}")

print("\n" + "=" * 100)
print("3. KEY INSIGHTS & PATTERNS")
print("=" * 100)

insights = []

# Analyze recent trends for each market
for market in markets:
    market_data = df[df['cbsa_title'] == market].copy()
    latest = market_data.iloc[-1]

    # High inventory growth
    if latest['active_listing_count_yy'] > 0.30:
        insights.append(f"[{market}] SIGNIFICANT INVENTORY INCREASE: Active listings up {latest['active_listing_count_yy']*100:.1f}% YoY - indicating increasing supply")

    # Price reductions surge
    if latest['price_reduced_count_yy'] > 0.30:
        insights.append(f"[{market}] HIGH PRICE REDUCTION ACTIVITY: {latest['price_reduced_count_yy']*100:.1f}% YoY increase - sellers adjusting expectations")

    # Days on market increasing
    if latest['median_days_on_market_yy'] > 0.20:
        insights.append(f"[{market}] SLOWING ABSORPTION: Days on market up {latest['median_days_on_market_yy']*100:.1f}% YoY - properties taking longer to sell")

    # Strong pending ratio
    if latest['pending_ratio'] > 0.50:
        insights.append(f"[{market}] HEALTHY DEMAND SIGNAL: Pending ratio at {latest['pending_ratio']:.2f} - good buyer activity")

    # Low pending ratio
    if latest['pending_ratio'] < 0.40:
        insights.append(f"[{market}] WEAKENING DEMAND: Pending ratio at {latest['pending_ratio']:.2f} - buyer activity moderating")

    # Price declines
    if latest['median_listing_price_yy'] < -0.02:
        insights.append(f"[{market}] PRICE SOFTENING: Median prices down {latest['median_listing_price_yy']*100:.1f}% YoY")

    # Price increases
    if latest['median_listing_price_yy'] > 0.05:
        insights.append(f"[{market}] STRONG PRICE APPRECIATION: Median prices up {latest['median_listing_price_yy']*100:.1f}% YoY")

print("\nKey Market Signals:")
for i, insight in enumerate(insights, 1):
    print(f"\n{i}. {insight}")

print("\n" + "=" * 100)
print("4. STATISTICAL OUTLIERS & ANOMALIES")
print("=" * 100)

for market in markets:
    market_data = df[df['cbsa_title'] == market].copy()
    latest = market_data.iloc[-1]

    print(f"\n{market}:")

    anomalies = []

    # Check for extreme month-over-month changes
    if abs(latest['median_listing_price_mm']) > 0.05:
        anomalies.append(f"  - Large price swing: {latest['median_listing_price_mm']*100:+.1f}% MoM")

    if abs(latest['active_listing_count_mm']) > 0.20:
        anomalies.append(f"  - Significant inventory shift: {latest['active_listing_count_mm']*100:+.1f}% MoM")

    if abs(latest['median_days_on_market_mm']) > 0.15:
        anomalies.append(f"  - Notable DOM change: {latest['median_days_on_market_mm']*100:+.1f}% MoM")

    if abs(latest['pending_ratio_mm']) > 0.10:
        anomalies.append(f"  - Sharp demand shift: Pending ratio changed {latest['pending_ratio_mm']*100:+.1f}% MoM")

    if anomalies:
        for anomaly in anomalies:
            print(anomaly)
    else:
        print("  No significant anomalies detected")

print("\n" + "=" * 100)
print("5. MARKET HEALTH ASSESSMENT")
print("=" * 100)

for market in markets:
    market_data = df[df['cbsa_title'] == market].copy()
    latest = market_data.iloc[-1]

    print(f"\n{market}:")

    # Calculate simple market health score (0-100)
    score = 50  # Base score

    # Price trends
    if latest['median_listing_price_yy'] > 0.05:
        score += 10
        print("  + Strong price appreciation (YoY)")
    elif latest['median_listing_price_yy'] < -0.02:
        score -= 10
        print("  - Price depreciation (YoY)")

    # Days on market
    if latest['median_days_on_market'] < 45:
        score += 10
        print("  + Quick sales velocity")
    elif latest['median_days_on_market'] > 60:
        score -= 10
        print("  - Slow sales velocity")

    # Pending ratio
    if latest['pending_ratio'] > 0.55:
        score += 10
        print("  + Strong buyer demand")
    elif latest['pending_ratio'] < 0.45:
        score -= 10
        print("  - Moderate buyer demand")

    # Inventory levels
    if latest['active_listing_count_yy'] < 0:
        score += 10
        print("  + Inventory declining (seller's market)")
    elif latest['active_listing_count_yy'] > 0.30:
        score -= 10
        print("  - Inventory surging (buyer's market)")

    # Price reductions
    reduction_pct = (latest['price_reduced_count'] / latest['active_listing_count']) * 100
    if reduction_pct < 20:
        score += 10
        print("  + Low price reduction rate")
    elif reduction_pct > 40:
        score -= 10
        print("  - High price reduction rate")

    print(f"\n  MARKET HEALTH SCORE: {score}/100")

    if score >= 70:
        sentiment = "STRONG SELLER'S MARKET"
    elif score >= 55:
        sentiment = "BALANCED MARKET (Slight Seller Advantage)"
    elif score >= 45:
        sentiment = "BALANCED MARKET"
    elif score >= 30:
        sentiment = "BALANCED MARKET (Slight Buyer Advantage)"
    else:
        sentiment = "BUYER'S MARKET"

    print(f"  MARKET SENTIMENT: {sentiment}")

print("\n" + "=" * 100)
print("6. TIME SERIES TRENDS SUMMARY")
print("=" * 100)

for market in markets:
    market_data = df[df['cbsa_title'] == market].copy()

    print(f"\n{market}:")
    print(f"  Data Points: {len(market_data)} months")
    print(f"  Period: {market_data['date'].min().strftime('%b %Y')} to {market_data['date'].max().strftime('%b %Y')}")

    # Price trend
    price_trend = market_data['median_listing_price'].values
    if len(price_trend) > 1:
        recent_trend = "INCREASING" if price_trend[-1] > price_trend[-2] else "DECREASING"
        overall_trend = "INCREASING" if price_trend[-1] > price_trend[0] else "DECREASING"
        print(f"\n  Price Trend:")
        print(f"    Recent (MoM): {recent_trend}")
        print(f"    Overall: {overall_trend}")
        print(f"    Range: ${price_trend.min():,} to ${price_trend.max():,}")

    # Inventory trend
    inventory_trend = market_data['active_listing_count'].values
    if len(inventory_trend) > 1:
        recent_inv_trend = "INCREASING" if inventory_trend[-1] > inventory_trend[-2] else "DECREASING"
        overall_inv_trend = "INCREASING" if inventory_trend[-1] > inventory_trend[0] else "DECREASING"
        print(f"\n  Inventory Trend:")
        print(f"    Recent (MoM): {recent_inv_trend}")
        print(f"    Overall: {overall_inv_trend}")
        print(f"    Range: {inventory_trend.min():,} to {inventory_trend.max():,}")

    # Days on market trend
    dom_trend = market_data['median_days_on_market'].values
    if len(dom_trend) > 1:
        recent_dom_trend = "INCREASING" if dom_trend[-1] > dom_trend[-2] else "DECREASING"
        print(f"\n  Days on Market Trend:")
        print(f"    Recent (MoM): {recent_dom_trend}")
        print(f"    Current: {dom_trend[-1]} days")
        print(f"    Range: {dom_trend.min()} to {dom_trend.max()} days")

print("\n" + "=" * 100)
print("REPORT COMPLETE")
print("=" * 100)
