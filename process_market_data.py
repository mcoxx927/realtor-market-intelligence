"""
Real Estate Market Data Processor
Processes Redfin TSV files into structured JSON for dashboard generation and agent analysis
Includes 12-month historical trends for metro and top 5 cities
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime

def safe_float(value):
    """Convert value to float, handling 'N/A' strings"""
    if pd.isna(value) or value == 'N/A':
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def safe_int(value):
    """Convert value to int, handling 'N/A' strings"""
    if pd.isna(value) or value == 'N/A':
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None

def calculate_health_score(row):
    """Calculate health score (0-100) based on market fundamentals"""
    score = 0

    # Pending sales strength (25 pts)
    pending_yoy = safe_float(row.get('PENDING_SALES_YOY'))
    if pending_yoy and pending_yoy > 0.10:
        score += 25
    elif pending_yoy and pending_yoy > 0:
        score += 15
    else:
        score += 5

    # Velocity - DOM YoY (25 pts)
    dom_yoy = safe_float(row.get('MEDIAN_DOM_YOY'))
    if dom_yoy and dom_yoy < 0:  # Faster is better
        score += 25
    elif dom_yoy and dom_yoy < 0.10:
        score += 15
    else:
        score += 5

    # Inventory balance (25 pts)
    mos = safe_float(row.get('MONTHS_OF_SUPPLY'))
    if mos and mos < 3:
        score += 25
    elif mos and mos < 6:
        score += 15
    else:
        score += 5

    # Price momentum (25 pts)
    price_yoy = safe_float(row.get('MEDIAN_SALE_PRICE_YOY'))
    if price_yoy and price_yoy > 0.05:
        score += 25
    elif price_yoy and price_yoy > 0:
        score += 15
    else:
        score += 5

    return min(score, 100)

def process_metro_data(tsv_file: str, metro_name: str, lookback_months: int = 12) -> dict:
    """Process TSV file and extract metro-level + city-level historical trends"""

    print(f"\nProcessing {metro_name} data from {tsv_file}...")

    # Read TSV file
    df = pd.read_csv(tsv_file, sep='\t', low_memory=False)

    # Filter to "All Residential" property type only
    df = df[df['PROPERTY_TYPE'] == 'All Residential'].copy()

    # Convert PERIOD_BEGIN to datetime
    df['PERIOD_BEGIN'] = pd.to_datetime(df['PERIOD_BEGIN'])

    # Get latest period (current month)
    latest_period = df['PERIOD_BEGIN'].max()
    current_month = latest_period.strftime('%Y-%m')

    # Get earliest period for full history
    earliest_period = df['PERIOD_BEGIN'].min()
    total_months = len(df['PERIOD_BEGIN'].unique())

    print(f"  Latest period: {current_month}")
    print(f"  Full history: {earliest_period.strftime('%Y-%m')} to {current_month} ({total_months} months)")

    # Filter to last 12 months for summary
    cutoff_date_12m = latest_period - pd.DateOffset(months=lookback_months-1)
    df_recent_12m = df[df['PERIOD_BEGIN'] >= cutoff_date_12m].copy()

    print(f"  12-month summary: {cutoff_date_12m.strftime('%Y-%m')} to {current_month}")

    # Get current month data only
    df_current = df[df['PERIOD_BEGIN'] == latest_period].copy()

    # ========== HELPER FUNCTION FOR METRO TRENDS ==========
    def calculate_metro_trends(dataframe):
        """Calculate metro trends from a dataframe"""
        trends = []
        for period in sorted(dataframe['PERIOD_BEGIN'].unique()):
            period_data = dataframe[dataframe['PERIOD_BEGIN'] == period]

            # Sum totals
            total_sales = safe_float(period_data['HOMES_SOLD'].sum())
            total_inventory = safe_float(period_data['INVENTORY'].sum())

            if total_sales and total_sales > 0:
                # Weighted averages by sales volume
                weighted_price = (period_data['MEDIAN_SALE_PRICE'] * period_data['HOMES_SOLD']).sum() / total_sales
                weighted_dom = (period_data['MEDIAN_DOM'] * period_data['HOMES_SOLD']).sum() / total_sales

                trends.append({
                    'period': period.strftime('%Y-%m'),
                    'inventory': safe_int(total_inventory),
                    'new_listings': safe_int(period_data['NEW_LISTINGS'].sum()),
                    'pending_sales': safe_int(period_data['PENDING_SALES'].sum()),
                    'homes_sold': safe_int(total_sales),
                    'price_drops': safe_int(period_data['PRICE_DROPS'].sum()),
                    'median_sale_price': safe_int(weighted_price),
                    'median_dom': safe_int(weighted_dom),
                    'pending_ratio': safe_float(period_data['PENDING_SALES'].sum() / total_inventory) if total_inventory > 0 else None
                })
        return trends

    # ========== METRO-LEVEL TRENDS (12 months for default view) ==========
    metro_trends_12m = calculate_metro_trends(df_recent_12m)
    print(f"  Metro trends (12m): {len(metro_trends_12m)} months")

    # ========== METRO-LEVEL TRENDS (FULL HISTORY) ==========
    full_metro_trends = calculate_metro_trends(df)
    print(f"  Metro trends (full): {len(full_metro_trends)} months")

    # ========== TOP 10 CITIES (Current Month) ==========
    df_current['HEALTH_SCORE'] = df_current.apply(calculate_health_score, axis=1)

    city_data = df_current.groupby('CITY').agg({
        'HOMES_SOLD': 'sum',
        'MEDIAN_SALE_PRICE': 'first',
        'MEDIAN_SALE_PRICE_YOY': 'first',
        'MEDIAN_DOM': 'first',
        'INVENTORY': 'sum',
        'PENDING_SALES': 'sum',
        'NEW_LISTINGS': 'sum',
        'PRICE_DROPS': 'sum',
        'MONTHS_OF_SUPPLY': 'first',
        'HEALTH_SCORE': 'first'
    }).reset_index()

    city_data = city_data.sort_values('HOMES_SOLD', ascending=False).head(10)

    top_cities = []
    for _, row in city_data.iterrows():
        top_cities.append({
            'name': row['CITY'],
            'sales': safe_int(row['HOMES_SOLD']),
            'price': safe_int(row['MEDIAN_SALE_PRICE']),
            'price_yoy': safe_float(row['MEDIAN_SALE_PRICE_YOY']),
            'dom': safe_int(row['MEDIAN_DOM']),
            'inventory': safe_int(row['INVENTORY']),
            'pending': safe_int(row['PENDING_SALES']),
            'new_listings': safe_int(row['NEW_LISTINGS']),
            'price_drops': safe_int(row['PRICE_DROPS']),
            'months_supply': safe_float(row['MONTHS_OF_SUPPLY']),
            'health': int(row['HEALTH_SCORE']) if pd.notna(row['HEALTH_SCORE']) else 50
        })

    print(f"  Top cities: {len(top_cities)}")

    # ========== HELPER FUNCTION FOR CITY TRENDS ==========
    def calculate_city_trends(dataframe, city_list):
        """Calculate historical trends for a list of cities"""
        trends = {}
        for city_name in city_list:
            city_df = dataframe[dataframe['CITY'] == city_name]
            city_history = []

            for period in sorted(city_df['PERIOD_BEGIN'].unique()):
                period_row = city_df[city_df['PERIOD_BEGIN'] == period].iloc[0]

                inventory_val = safe_int(period_row['INVENTORY'])
                pending_val = safe_int(period_row['PENDING_SALES'])

                city_history.append({
                    'period': period.strftime('%Y-%m'),
                    'inventory': inventory_val,
                    'new_listings': safe_int(period_row['NEW_LISTINGS']),
                    'pending_sales': pending_val,
                    'homes_sold': safe_int(period_row['HOMES_SOLD']),
                    'price_drops': safe_int(period_row['PRICE_DROPS']),
                    'median_sale_price': safe_int(period_row['MEDIAN_SALE_PRICE']),
                    'median_dom': safe_int(period_row['MEDIAN_DOM']),
                    'pending_ratio': safe_float(pending_val / inventory_val) if (pending_val and inventory_val and inventory_val > 0) else None
                })

            trends[city_name] = city_history
        return trends

    # ========== TOP 5 CITIES - 12 MONTH TRENDS (for default dashboard view) ==========
    top_5_cities = [city['name'] for city in top_cities[:5]]
    city_trends_12m = calculate_city_trends(df_recent_12m, top_5_cities)
    print(f"  Top 5 cities (12m): {len(top_5_cities)} cities")

    # ========== ALL CITIES - FULL HISTORICAL TRENDS ==========
    all_cities = sorted(df['CITY'].unique())
    full_city_trends = calculate_city_trends(df, all_cities)
    print(f"  All cities (full): {len(all_cities)} cities, {len(full_metro_trends)} months each")

    # ========== CURRENT MONTH METRO STATS ==========
    current_metro_stats = {
        'total_sales': safe_int(df_current['HOMES_SOLD'].sum()),
        'total_inventory': safe_int(df_current['INVENTORY'].sum()),
        'total_cities': len(df_current)
    }

    return {
        'metro': metro_name,
        'period': current_month,
        'current_stats': current_metro_stats,
        'metro_trends': metro_trends_12m,  # 12-month default view
        'top_cities': top_cities,
        'city_trends': city_trends_12m,  # Top 5 cities, 12 months
        'full_metro_trends': full_metro_trends,  # All available history
        'full_city_trends': full_city_trends,  # All cities, all history
        'available_cities': all_cities  # List of all city names
    }

def main():
    """Process both Charlotte and Roanoke data"""

    base_dir = Path(__file__).parent

    # Process Charlotte
    charlotte_data = process_metro_data(
        tsv_file=str(base_dir / 'charlotte_cities_filtered.tsv'),
        metro_name='Charlotte, NC',
        lookback_months=12
    )

    # Save Charlotte JSON
    output_file = base_dir / 'charlotte' / '2025-09' / 'charlotte_data.json'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(charlotte_data, f, indent=2)
    print(f"\n[OK] Saved: {output_file}")

    # Process Roanoke
    roanoke_data = process_metro_data(
        tsv_file=str(base_dir / 'roanoke_cities_filtered.tsv'),
        metro_name='Roanoke, VA',
        lookback_months=12
    )

    # Save Roanoke JSON
    output_file = base_dir / 'roanoke' / '2025-09' / 'roanoke_data.json'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(roanoke_data, f, indent=2)
    print(f"[OK] Saved: {output_file}")

    print("\n" + "="*60)
    print("[OK] DATA PROCESSING COMPLETE!")
    print("="*60)
    print(f"\nCharlotte: {charlotte_data['current_stats']['total_cities']} cities, {charlotte_data['current_stats']['total_sales']} sales")
    print(f"Roanoke:   {roanoke_data['current_stats']['total_cities']} cities, {roanoke_data['current_stats']['total_sales']} sales")
    print(f"\n12-month default view: {len(charlotte_data['metro_trends'])} months, {len(charlotte_data['city_trends'])} cities")
    print(f"Full historical data: {len(charlotte_data['full_metro_trends'])} months, {len(charlotte_data['available_cities'])} cities")

if __name__ == '__main__':
    main()
