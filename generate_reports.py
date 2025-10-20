import pandas as pd
import json
import os
from datetime import datetime

def format_currency(value):
    """Format value as currency"""
    return f"${value:,.0f}"

def format_percent(value):
    """Format value as percentage"""
    return f"{value:+.1f}%"

def format_number(value):
    """Format value as number"""
    return f"{value:,.0f}"

def generate_market_report(market_name, dashboard_data, alerts_data, df):
    """Generate comprehensive markdown report for a market"""

    current = dashboard_data['current_metrics']
    health_score = dashboard_data['health_score']
    sentiment = dashboard_data['sentiment']

    # Determine market short name
    market_short = market_name.split(',')[0]

    # Get historical context
    last_12 = df[df['month_date_yyyymm'] >= 202409].tail(12)
    last_3 = df[df['month_date_yyyymm'] >= 202507].tail(3)

    # Calculate 3-month averages
    avg_dom_3m = last_3['median_days_on_market'].mean()
    avg_price_3m = last_3['median_listing_price'].mean()
    avg_new_listings_3m = last_3['new_listing_count'].mean()

    report = f"""# Real Estate Market Intelligence Report
## {market_short}
### September 2025

---

## EXECUTIVE SUMMARY

The {market_short} real estate market in September 2025 shows **{sentiment}** conditions with a market health score of **{health_score}/100**. """

    # Add executive summary based on key metrics
    if sentiment == "BULLISH":
        report += f"Strong fundamentals indicate favorable market conditions with solid buyer demand and healthy pricing power."
    elif sentiment == "NEUTRAL":
        report += f"Market conditions are balanced with moderate activity levels and stable pricing dynamics."
    else:
        report += f"Market conditions show signs of softening with weakening demand indicators and pricing pressures."

    # Key takeaway
    if current['median_listing_price_mm'] > 0:
        price_direction = "rising"
    elif current['median_listing_price_mm'] < -1:
        price_direction = "declining"
    else:
        price_direction = "holding steady"

    report += f"""

**Key Takeaway:** Median listing prices are {price_direction} at {format_currency(current['median_listing_price'])}, while inventory levels {'increased' if current['active_listing_count_mm'] > 0 else 'decreased'} by {abs(current['active_listing_count_mm']):.1f}% month-over-month to {format_number(current['active_listing_count'])} active listings.

**Recommended Action:** """

    # Strategic recommendation based on conditions
    if health_score >= 70:
        report += "Capitalize on strong market conditions with confident pricing strategies."
    elif health_score >= 55:
        report += "Maintain balanced approach with competitive pricing and strong marketing."
    elif health_score >= 40:
        report += "Exercise caution with aggressive pricing and enhanced property presentation."
    else:
        report += "Focus on value positioning, realistic pricing, and differentiation strategies."

    report += f"""

---

## MARKET SNAPSHOT

### Current Month Performance (September 2025)

#### Pricing Metrics
- **Median Listing Price:** {format_currency(current['median_listing_price'])} ({format_percent(current['median_listing_price_mm'])} MoM, {format_percent(current['median_listing_price_yy'])} YoY)
- **Median Price per Sq Ft:** {format_currency(current['median_price_per_sqft'])}
- **Price Reductions:** {format_number(current['price_reduced_count'])} ({format_percent(current['price_reduced_count_mm'])} MoM)
- **Price Increases:** {format_number(current['price_increased_count'])} ({format_percent(current['price_increased_count_mm'])} MoM)

#### Inventory Metrics
- **Active Listings:** {format_number(current['active_listing_count'])} ({format_percent(current['active_listing_count_mm'])} MoM, {format_percent(current['active_listing_count_yy'])} YoY)
- **New Listings:** {format_number(current['new_listing_count'])} ({format_percent(current['new_listing_count_mm'])} MoM, {format_percent(current['new_listing_count_yy'])} YoY)
- **Pending Listings:** {format_number(current['pending_listing_count'])}

#### Market Velocity
- **Days on Market:** {current['median_days_on_market']} days ({format_percent(current['median_days_on_market_mm'])} MoM, {format_percent(current['median_days_on_market_yy'])} YoY)
- **Pending Ratio:** {current['pending_ratio']:.4f} ({format_percent(current['pending_ratio_mm'])} MoM, {format_percent(current['pending_ratio_yy'])} YoY)

---

## MONTH-OVER-MONTH TRENDS

### What Changed in September

**Pricing Dynamics:**
"""

    # Analyze pricing trends
    if abs(current['median_listing_price_mm']) < 1:
        report += f"\nMedian listing prices remained relatively stable, changing only {format_percent(current['median_listing_price_mm'])} from August. This suggests a balanced market with neither strong upward nor downward pricing pressure."
    elif current['median_listing_price_mm'] > 0:
        report += f"\nMedian listing prices increased {format_percent(current['median_listing_price_mm'])} from August, indicating sustained pricing power and seller confidence in the market."
    else:
        report += f"\nMedian listing prices declined {format_percent(abs(current['median_listing_price_mm']))} from August, suggesting some softening in pricing power as inventory dynamics shift."

    # Price reduction analysis
    reduction_ratio = current['price_reduced_count'] / current['active_listing_count']
    report += f"\n\nPrice reductions {'increased' if current['price_reduced_count_mm'] > 0 else 'decreased'} by {abs(current['price_reduced_count_mm']):.1f}% to {format_number(current['price_reduced_count'])} properties, representing {reduction_ratio:.1%} of active inventory. "

    if reduction_ratio > 0.50:
        report += "This high reduction rate indicates significant pricing pressure and suggests sellers may have initially overpriced properties relative to market conditions."
    elif reduction_ratio > 0.40:
        report += "This elevated reduction rate suggests moderate pricing pressure and some negotiation leverage for buyers."
    else:
        report += "This reduction rate is within normal ranges, indicating balanced pricing dynamics."

    report += f"""

**Inventory Flow:**

"""

    # Inventory analysis
    if current['active_listing_count_mm'] > 10:
        report += f"Active inventory surged by {format_percent(current['active_listing_count_mm'])}, a significant increase that suggests new supply is entering faster than homes are being absorbed. "
    elif current['active_listing_count_mm'] > 5:
        report += f"Active inventory grew by {format_percent(current['active_listing_count_mm'])}, indicating moderate inventory accumulation. "
    elif current['active_listing_count_mm'] > -5:
        report += f"Active inventory changed by {format_percent(current['active_listing_count_mm'])}, showing relative stability in inventory levels. "
    else:
        report += f"Active inventory declined by {format_percent(abs(current['active_listing_count_mm']))}, suggesting strong absorption of available homes. "

    if current['new_listing_count_mm'] > 5:
        report += f"New listings increased by {format_percent(current['new_listing_count_mm'])}, reflecting strong seller confidence and willingness to enter the market."
    elif current['new_listing_count_mm'] < -5:
        report += f"New listings declined by {format_percent(abs(current['new_listing_count_mm']))}, indicating seller hesitancy or potential supply constraints."
    else:
        report += f"New listings remained relatively stable with a {format_percent(current['new_listing_count_mm'])} change, suggesting consistent supply flow."

    report += f"""

**Sales Velocity:**

Days on market {'increased' if current['median_days_on_market_mm'] > 0 else 'decreased'} to {current['median_days_on_market']} days ({format_percent(current['median_days_on_market_mm'])} change). """

    if current['median_days_on_market'] < 45:
        report += "Properties are selling quickly, indicating strong buyer demand and competitive conditions."
    elif current['median_days_on_market'] < 60:
        report += "Properties are selling at a moderate pace, typical of balanced market conditions."
    elif current['median_days_on_market'] < 75:
        report += "Properties are taking longer to sell, suggesting buyers have more negotiating leverage."
    else:
        report += "Extended time on market indicates a buyer's market with reduced urgency and pricing pressure."

    report += f" The pending ratio of {current['pending_ratio']:.4f} "

    if current['pending_ratio'] > 0.60:
        report += "shows strong buyer urgency relative to available inventory."
    elif current['pending_ratio'] > 0.45:
        report += "indicates balanced buyer activity relative to inventory levels."
    else:
        report += "suggests weakening buyer demand relative to available supply."

    report += f"""

---

## YEAR-OVER-YEAR COMPARISON

### How September 2025 Compares to September 2024

"""

    # YoY analysis
    if current['median_listing_price_yy'] > 0:
        report += f"The market has seen price appreciation with median listings up {format_percent(current['median_listing_price_yy'])} year-over-year, "
        if current['median_listing_price_yy'] > 10:
            report += "reflecting strong demand fundamentals and limited supply."
        elif current['median_listing_price_yy'] > 5:
            report += "showing healthy price growth in line with economic conditions."
        else:
            report += "indicating modest price appreciation and market stability."
    else:
        report += f"Median listing prices have declined {format_percent(abs(current['median_listing_price_yy']))} year-over-year, "
        if current['median_listing_price_yy'] < -5:
            report += "representing a significant correction from last year's levels."
        else:
            report += "showing modest softening compared to last year."

    report += f"\n\nInventory conditions have shifted substantially with active listings up {format_percent(current['active_listing_count_yy'])} compared to last September. "

    if current['active_listing_count_yy'] > 30:
        report += "This dramatic increase in supply represents a fundamental shift toward a more balanced or buyer-favorable market compared to the tight inventory conditions of a year ago."
    elif current['active_listing_count_yy'] > 15:
        report += "This notable increase in available homes provides buyers with more options and potentially more negotiating power than last year."
    elif current['active_listing_count_yy'] > 0:
        report += "This modest increase in inventory suggests a normalizing market with improving supply conditions."
    else:
        report += "The decline in inventory suggests continued supply constraints relative to last year."

    report += f"\n\nMarket velocity has changed with days on market {'up' if current['median_days_on_market_yy'] > 0 else 'down'} {abs(current['median_days_on_market_yy']):.1f}% year-over-year. "

    if current['median_days_on_market_yy'] > 20:
        report += "This significant slowdown in sales velocity indicates a marked shift in market dynamics, with buyers taking more time to make decisions and having greater negotiating leverage."
    elif current['median_days_on_market_yy'] > 10:
        report += "This moderate slowdown suggests a shift toward more balanced market conditions with less urgency than last year."
    elif current['median_days_on_market_yy'] > -10:
        report += "Sales velocity remains relatively consistent with last year's pace."
    else:
        report += "Properties are selling faster than last year, indicating strengthening demand."

    report += f"""

---

## SUPPLY & DEMAND DYNAMICS

### Current Market Balance

**Inventory Assessment:**

The current inventory of {format_number(current['active_listing_count'])} active listings represents """

    # Calculate months of supply approximation
    if current['pending_listing_count'] > 0:
        months_supply = current['active_listing_count'] / current['pending_listing_count']
        report += f"approximately {months_supply:.1f} months of supply based on current pending activity. "

        if months_supply < 3:
            report += "This is a seller's market with limited supply relative to demand."
        elif months_supply < 5:
            report += "This suggests a balanced market with moderate supply levels."
        elif months_supply < 6:
            report += "This indicates ample supply, providing buyers with good selection and negotiating power."
        else:
            report += "This represents elevated supply levels that may pressure prices without corresponding demand growth."

    # New listing velocity
    report += f"\n\nNew listing velocity of {format_number(current['new_listing_count'])} properties per month "

    new_to_active_ratio = current['new_listing_count'] / current['active_listing_count']
    if new_to_active_ratio > 0.45:
        report += "is high relative to active inventory, indicating strong turnover and an active market."
    elif new_to_active_ratio > 0.30:
        report += "is moderate relative to active inventory, suggesting balanced market turnover."
    else:
        report += "is relatively low compared to active inventory, indicating slower market turnover."

    report += f"""

**Buyer Demand Indicators:**

The pending ratio of {current['pending_ratio']:.4f} """

    if current['pending_ratio_mm'] < -5:
        report += f"has weakened by {abs(current['pending_ratio_mm']):.1f}% month-over-month, "
        report += "suggesting declining buyer urgency or affordability constraints impacting demand."
    elif current['pending_ratio_mm'] > 5:
        report += f"has strengthened by {current['pending_ratio_mm']:.1f}% month-over-month, "
        report += "indicating improving buyer confidence and market momentum."
    else:
        report += "has remained relatively stable month-over-month, "
        report += "suggesting consistent buyer activity levels."

    report += f"\n\nWith {format_number(current['pending_listing_count'])} pending listings, the market shows "

    if current['pending_ratio'] > 0.60:
        report += "strong buyer activity with healthy demand absorbing new inventory quickly."
    elif current['pending_ratio'] > 0.45:
        report += "balanced buyer activity with moderate absorption of available inventory."
    else:
        report += "softer buyer activity with slower absorption of available homes."

    report += f"""

---

## PRICING POWER ASSESSMENT

### Seller vs Buyer Leverage

"""

    # Price reduction vs increase analysis
    reduction_to_increase_ratio = current['price_reduced_count'] / max(current['price_increased_count'], 1)

    report += f"In September, {format_number(current['price_reduced_count'])} properties reduced their asking price while {format_number(current['price_increased_count'])} increased prices, "
    report += f"a ratio of {reduction_to_increase_ratio:.1f}:1. "

    if reduction_to_increase_ratio > 30:
        report += "This heavily skewed ratio indicates strong buyer leverage with sellers frequently needing to adjust prices downward to attract offers."
    elif reduction_to_increase_ratio > 20:
        report += "This significant imbalance suggests buyers have considerable negotiating power and sellers face pricing pressure."
    elif reduction_to_increase_ratio > 10:
        report += "This moderate imbalance indicates a buyer-favorable environment with some pricing pressure on sellers."
    elif reduction_to_increase_ratio > 5:
        report += "This ratio suggests relatively balanced conditions with slight buyer leverage."
    else:
        report += "This favorable ratio for sellers indicates strong pricing power and confident market conditions."

    report += f"""

**Negotiation Environment:**

"""

    # Determine negotiation environment
    if health_score >= 70 and current['pending_ratio'] > 0.60:
        report += "Sellers maintain strong negotiating position with multiple offers likely on well-priced properties. Buyers should be prepared to act quickly and compete."
    elif health_score >= 55 and current['pending_ratio'] > 0.45:
        report += "Balanced negotiation environment where both parties have reasonable leverage. Success depends on property condition, pricing, and market timing."
    elif health_score >= 40:
        report += "Buyers have moderate negotiating leverage with time to evaluate options. Sellers should focus on competitive pricing and property presentation."
    else:
        report += "Buyers have strong negotiating position with multiple options and time to decide. Sellers should price aggressively and be prepared to negotiate on terms and price."

    report += f"""

**Recommended Pricing Strategy:**

"""

    # Pricing recommendations
    if current['median_listing_price_mm'] > 2 and current['median_days_on_market'] < 45:
        report += "Strong pricing momentum supports confident list prices at or slightly above comparable sales. Properties in excellent condition can test the high end of value ranges."
    elif current['median_listing_price_mm'] > -1 and current['median_days_on_market'] < 60:
        report += "Price at market value based on recent comparable sales. Avoid overpricing as competition exists, but well-presented properties should receive fair market value."
    elif current['price_reduced_count_mm'] > 20:
        report += "Price aggressively from the start to avoid being in the large pool of reduced properties. Consider pricing 3-5% below comparable sales to generate early interest and potential multiple offers."
    else:
        report += "Price competitively based on recent sales data. The market requires realistic pricing to generate showing activity and offers within reasonable timeframes."

    report += f"""

---

## STRATEGIC RECOMMENDATIONS

Based on September 2025 market conditions in {market_short}:

### Listing Strategy

1. **Timing Considerations**
"""

    # Timing recommendations
    if current['new_listing_count_mm'] > 10:
        report += "\n   - High new listing volume suggests increased competition; differentiation is critical"
        report += "\n   - Consider waiting for seasonal shifts if property isn't ready for optimal presentation"
    elif current['active_listing_count_yy'] > 30:
        report += "\n   - Elevated inventory levels mean quality presentation and pricing are essential"
        report += "\n   - First 2 weeks on market are critical for generating interest"
    else:
        report += "\n   - Current supply levels support listing well-prepared properties"
        report += "\n   - Market timing is favorable for move-up buyers who can list and buy concurrently"

    report += f"""

2. **Pricing Approach**
"""

    # Pricing approach based on conditions
    if reduction_ratio > 0.45:
        report += "\n   - Price 2-3% below comparable sales to avoid price reduction cycle"
        report += "\n   - Consider appraisal value as ceiling rather than target"
        report += "\n   - Build negotiation room into list price if market norms support it"
    elif current['median_days_on_market'] > 60:
        report += "\n   - Price within or below range of recent comparable sales"
        report += "\n   - Avoid aspirational pricing given current market velocity"
        report += "\n   - Consider buyer concessions if property has been on market 30+ days"
    else:
        report += "\n   - Price at fair market value based on recent comparable sales"
        report += "\n   - Well-presented properties can test upper end of value range"
        report += "\n   - Monitor showing activity closely in first week to gauge pricing accuracy"

    report += f"""

3. **Market Positioning**
"""

    # Positioning recommendations
    if health_score >= 60:
        report += "\n   - Emphasize property features and lifestyle benefits in marketing"
        report += "\n   - Professional photography and staging yield strong returns"
        report += "\n   - Target specific buyer profiles most likely to value property attributes"
    else:
        report += "\n   - Lead with value proposition and competitive pricing"
        report += "\n   - Highlight any recent updates, repairs, or unique features"
        report += "\n   - Address any condition issues proactively before listing"

    report += f"""

### Inventory Management

1. **Supply Level Considerations**
"""

    # Supply recommendations
    if current['active_listing_count_yy'] > 30:
        report += f"\n   - Inventory up {format_percent(current['active_listing_count_yy'])} YoY represents significant market shift"
        report += "\n   - Increased selection gives buyers more options and negotiating power"
        report += "\n   - Properties must compete on price, condition, and location"
    elif current['active_listing_count_mm'] > 15:
        report += "\n   - Rapid inventory build-up requires monitoring for market absorption"
        report += "\n   - New listings should be priced to stand out from competition"
        report += "\n   - Watch for inventory saturation in specific price ranges or locations"
    else:
        report += "\n   - Current inventory levels support balanced market dynamics"
        report += "\n   - Well-priced properties continue to attract buyer interest"
        report += "\n   - Limited supply in desirable areas may support pricing power"

    report += f"""

2. **Absorption Rate Analysis**
"""

    # Absorption analysis
    absorption_rate = current['pending_listing_count'] / current['active_listing_count']
    report += f"\n   - Current pending-to-active ratio of {absorption_rate:.2f} indicates "

    if absorption_rate > 0.60:
        report += "strong absorption"
        report += "\n   - Inventory is being absorbed quickly relative to supply"
        report += "\n   - Market can support additional new listings without oversupply"
    elif absorption_rate > 0.40:
        report += "moderate absorption"
        report += "\n   - Inventory absorption is balanced with new supply"
        report += "\n   - Monitor for changes in absorption rate as leading indicator"
    else:
        report += "slower absorption"
        report += "\n   - Inventory may be accumulating faster than being absorbed"
        report += "\n   - Price adjustments may be necessary if absorption slows further"

    report += f"""

### Market Positioning

1. **Competitive Advantages**
"""

    # Identify strengths to leverage
    if current['median_days_on_market'] < 50:
        report += "\n   - Relatively quick sales velocity favors ready-to-show properties"
    if current['pending_ratio'] > 0.50:
        report += "\n   - Healthy buyer demand supports well-positioned listings"
    if current['new_listing_count_yy'] < 0:
        report += "\n   - Limited new supply may reduce direct competition for quality properties"

    report += f"""

2. **Risk Factors to Consider**
"""

    # Identify risks
    if current['median_listing_price_yy'] < 0:
        report += f"\n   - Year-over-year price decline of {format_percent(abs(current['median_listing_price_yy']))} indicates pricing pressure"
    if current['median_days_on_market_yy'] > 20:
        report += f"\n   - Days on market up {format_percent(current['median_days_on_market_yy'])} YoY signals slower sales velocity"
    if reduction_ratio > 0.40:
        report += f"\n   - High price reduction rate ({reduction_ratio:.1%} of inventory) suggests initial overpricing is common"
    if current['pending_ratio_yy'] < -10:
        report += "\n   - Declining pending ratio year-over-year indicates weakening buyer demand"

    report += f"""

3. **Strategic Opportunities**
"""

    # Opportunities based on market conditions
    if health_score < 50 and current['median_listing_price_mm'] < 0:
        report += "\n   - Softening prices create opportunities for buyers to negotiate"
        report += "\n   - Sellers with flexibility on timing may want to wait for improved conditions"
    elif current['active_listing_count_yy'] > 25 and current['pending_ratio'] > 0.45:
        report += "\n   - Increased inventory with healthy demand supports buyer selection"
        report += "\n   - Well-priced properties can still attract competitive offers"
    else:
        report += "\n   - Balanced market conditions support transactions for motivated parties"
        report += "\n   - Focus on property-specific attributes rather than trying to time market"

    report += f"""

---

## KEY METRICS SUMMARY

| Metric | Current Value | MoM Change | YoY Change |
|--------|---------------|------------|------------|
| Median Listing Price | {format_currency(current['median_listing_price'])} | {format_percent(current['median_listing_price_mm'])} | {format_percent(current['median_listing_price_yy'])} |
| Active Listings | {format_number(current['active_listing_count'])} | {format_percent(current['active_listing_count_mm'])} | {format_percent(current['active_listing_count_yy'])} |
| Days on Market | {current['median_days_on_market']} days | {format_percent(current['median_days_on_market_mm'])} | {format_percent(current['median_days_on_market_yy'])} |
| New Listings | {format_number(current['new_listing_count'])} | {format_percent(current['new_listing_count_mm'])} | {format_percent(current['new_listing_count_yy'])} |
| Pending Ratio | {current['pending_ratio']:.4f} | {format_percent(current['pending_ratio_mm'])} | {format_percent(current['pending_ratio_yy'])} |
| Price Reductions | {format_number(current['price_reduced_count'])} | {format_percent(current['price_reduced_count_mm'])} | - |
| Price Increases | {format_number(current['price_increased_count'])} | {format_percent(current['price_increased_count_mm'])} | - |
| Price per Sq Ft | {format_currency(current['median_price_per_sqft'])} | - | - |

---

## NEXT MONTH OUTLOOK

Based on current trends and historical patterns, October 2025 expectations:

"""

    # Generate outlook based on trends
    outlook_points = []

    # Price outlook
    if current['median_listing_price_mm'] < -2 and current['price_reduced_count_mm'] > 10:
        outlook_points.append("**Pricing:** Continued downward pressure expected as sellers adjust to market realities. Price reductions likely to remain elevated.")
    elif current['median_listing_price_mm'] > 2:
        outlook_points.append("**Pricing:** Upward price momentum may continue if demand holds steady. Watch for seasonal slowdown.")
    else:
        outlook_points.append("**Pricing:** Relative price stability expected with typical seasonal patterns influencing month-over-month changes.")

    # Inventory outlook
    if current['new_listing_count_mm'] < -10:
        outlook_points.append("**Inventory:** Declining new listings may lead to tighter inventory if trend continues, potentially supporting prices.")
    elif current['active_listing_count_mm'] > 15:
        outlook_points.append("**Inventory:** Rapid inventory growth may continue, increasing competition among sellers and buyer selection.")
    else:
        outlook_points.append("**Inventory:** Moderate inventory changes expected with typical seasonal patterns as market heads into fall.")

    # Demand outlook
    if current['pending_ratio_mm'] < -5 and current['median_days_on_market_mm'] > 10:
        outlook_points.append("**Demand:** Weakening demand indicators suggest continued softening. Days on market likely to extend further.")
    elif current['pending_ratio'] > 0.60 and current['median_days_on_market'] < 50:
        outlook_points.append("**Demand:** Strong buyer activity expected to continue, supporting healthy absorption of inventory.")
    else:
        outlook_points.append("**Demand:** Moderate buyer activity expected with seasonal factors potentially impacting October volumes.")

    for point in outlook_points:
        report += f"\n{point}\n"

    report += f"""

**Key Items to Monitor:**

1. Price reduction rates - leading indicator of market sentiment shifts
2. New listing velocity - signals seller confidence and supply trends
3. Pending ratio changes - early indicator of demand strengthening or weakening
4. Days on market trend - reveals market absorption capacity

---

**Market Health Score: {health_score}/100 ({sentiment})**

*Report generated on October 15, 2025 | Data source: Realtor.com*
*Analysis Period: September 2025*
"""

    return report

def generate_alerts_markdown(market_name, alerts_data, dashboard_data):
    """Generate markdown alert summary"""

    market_short = market_name.split(',')[0]
    sentiment = alerts_data['sentiment']
    health_score = alerts_data['health_score']
    alerts = alerts_data['alerts']
    summary = alerts_data['summary']
    current = dashboard_data['current_metrics']

    alert_md = f"""# Market Alert Summary - {market_short}
## September 2025

---

## Overall Market Sentiment
**{sentiment}** (Market Health Score: {health_score}/100)

---
"""

    # High priority alerts
    high_alerts = [a for a in alerts if a['severity'] == 'HIGH']
    if high_alerts:
        alert_md += "\n## HIGH PRIORITY ALERTS\n\n"
        for alert in high_alerts:
            alert_md += f"### {alert['metric'].replace('_', ' ').title()}\n"
            alert_md += f"- **Alert:** {alert['trigger']}\n"
            if alert['before'] is not None:
                alert_md += f"- **Change:** {format_number(alert['before']) if isinstance(alert['before'], (int, float)) and alert['before'] > 100 else alert['before']} -> {format_number(alert['after']) if isinstance(alert['after'], (int, float)) and alert['after'] > 100 else alert['after']} ({format_percent(alert['change_pct'])})\n"
            else:
                alert_md += f"- **Current Value:** {alert['after']} ({format_percent(alert['change_pct'])})\n"
            alert_md += f"- **Why it matters:** {alert['context']}\n"
            alert_md += f"- **Action:** {alert['recommendation']}\n\n"

    # Medium priority alerts
    medium_alerts = [a for a in alerts if a['severity'] == 'MEDIUM']
    if medium_alerts:
        alert_md += "\n## MEDIUM PRIORITY ALERTS\n\n"
        for alert in medium_alerts:
            alert_md += f"### {alert['metric'].replace('_', ' ').title()}\n"
            alert_md += f"- **Alert:** {alert['trigger']}\n"
            if alert['before'] is not None:
                alert_md += f"- **Change:** {format_number(alert['before']) if isinstance(alert['before'], (int, float)) and alert['before'] > 100 else alert['before']} -> {format_number(alert['after']) if isinstance(alert['after'], (int, float)) and alert['after'] > 100 else alert['after']} ({format_percent(alert['change_pct'])})\n"
            else:
                alert_md += f"- **Current Value:** {alert['after']} ({format_percent(alert['change_pct'])})\n"
            alert_md += f"- **Why it matters:** {alert['context']}\n"
            alert_md += f"- **Action:** {alert['recommendation']}\n\n"

    # Low priority alerts
    low_alerts = [a for a in alerts if a['severity'] == 'LOW']
    if low_alerts:
        alert_md += "\n## LOW PRIORITY ALERTS\n\n"
        for alert in low_alerts:
            alert_md += f"### {alert['metric'].replace('_', ' ').title()}\n"
            alert_md += f"- **Alert:** {alert['trigger']}\n"
            if alert['before'] is not None:
                alert_md += f"- **Change:** {format_number(alert['before']) if isinstance(alert['before'], (int, float)) and alert['before'] > 100 else alert['before']} -> {format_number(alert['after']) if isinstance(alert['after'], (int, float)) and alert['after'] > 100 else alert['after']} ({format_percent(alert['change_pct'])})\n"
            else:
                alert_md += f"- **Current Value:** {alert['after']} ({format_percent(alert['change_pct'])})\n"
            alert_md += f"- **Why it matters:** {alert['context']}\n"
            alert_md += f"- **Action:** {alert['recommendation']}\n\n"

    # If no alerts
    if not alerts:
        alert_md += "\n## No Critical Alerts\n\n"
        alert_md += "All key metrics are within normal operating ranges. Market conditions are stable with no significant threshold breaches.\n\n"
        alert_md += "### Stable Indicators\n\n"
        alert_md += f"- Median listing price: {format_currency(current['median_listing_price'])} ({format_percent(current['median_listing_price_mm'])} MoM)\n"
        alert_md += f"- Active inventory: {format_number(current['active_listing_count'])} ({format_percent(current['active_listing_count_mm'])} MoM)\n"
        alert_md += f"- Days on market: {current['median_days_on_market']} days ({format_percent(current['median_days_on_market_mm'])} MoM)\n"
        alert_md += f"- Pending ratio: {current['pending_ratio']:.4f} ({format_percent(current['pending_ratio_mm'])} MoM)\n\n"

    # Positive indicators section
    alert_md += "\n## POSITIVE INDICATORS\n\n"

    positive_indicators = []

    if current['median_listing_price_mm'] > 1:
        positive_indicators.append(f"Median prices up {format_percent(current['median_listing_price_mm'])} MoM - healthy price appreciation")

    if current['pending_ratio'] > 0.55:
        positive_indicators.append(f"Pending ratio of {current['pending_ratio']:.4f} - strong buyer demand")

    if current['median_days_on_market'] < 50:
        positive_indicators.append(f"Days on market at {current['median_days_on_market']} days - healthy sales velocity")

    if current['active_listing_count_yy'] > 20:
        positive_indicators.append(f"Inventory up {format_percent(current['active_listing_count_yy'])} YoY - market normalization providing buyer choice")

    if current['new_listing_count_yy'] > 0:
        positive_indicators.append(f"New listings up {format_percent(current['new_listing_count_yy'])} YoY - sustained supply flow")

    if positive_indicators:
        for indicator in positive_indicators:
            alert_md += f"- {indicator}\n"
    else:
        alert_md += "- Market metrics within normal ranges\n"

    # Watch list
    alert_md += "\n---\n\n## WATCH LIST\n\n"
    alert_md += "Items to monitor closely next month:\n\n"

    watch_items = []

    if abs(current['price_reduced_count_mm']) > 10:
        watch_items.append(f"Price reduction rate ({format_percent(current['price_reduced_count_mm'])} MoM) - if continues accelerating, suggests correction")

    if abs(current['median_days_on_market_mm']) > 10:
        watch_items.append(f"Days on market trend ({format_percent(current['median_days_on_market_mm'])} MoM) - monitor for continued direction")

    if abs(current['pending_ratio_mm']) > 3:
        watch_items.append("Pending ratio momentum - early indicator of demand shifts")

    if abs(current['new_listing_count_mm']) > 10:
        watch_items.append("New listing flow - signals seller confidence trends")

    if watch_items:
        for i, item in enumerate(watch_items, 1):
            alert_md += f"{i}. {item}\n"
    else:
        alert_md += "1. Continue monitoring standard market metrics for emerging trends\n"

    # Scorecard table
    alert_md += f"""

---

## MARKET SCORECARD

| Metric | Value | Status |
|--------|-------|--------|
| Market Health Score | {health_score}/100 | {sentiment} |
| Median Listing Price | {format_currency(current['median_listing_price'])} | {'Stable' if abs(current['median_listing_price_mm']) < 1 else ('Rising' if current['median_listing_price_mm'] > 0 else 'Declining')} |
| Days on Market | {current['median_days_on_market']} days | {'Fast' if current['median_days_on_market'] < 45 else ('Moderate' if current['median_days_on_market'] < 60 else 'Slow')} |
| Pending Ratio | {current['pending_ratio']:.4f} | {'Strong' if current['pending_ratio'] > 0.55 else ('Balanced' if current['pending_ratio'] > 0.40 else 'Weak')} |
| Active Inventory | {format_number(current['active_listing_count'])} | {'Growing' if current['active_listing_count_mm'] > 5 else ('Stable' if abs(current['active_listing_count_mm']) <= 5 else 'Declining')} |

---

*Alerts generated on October 15, 2025 | Threshold: Flags changes >15% MoM or >25% YoY*
*Analysis Period: September 2025 | Source: Realtor.com*
"""

    return alert_md

# Main execution
if __name__ == "__main__":
    # Load data
    df = pd.read_excel('Realtor New Listings.xlsx', sheet_name='RDC_Inventory_Core_Metrics_Metr')
    df['month_date'] = pd.to_datetime(df['month_date_yyyymm'].astype(str), format='%Y%m')

    markets = [
        ('Charlotte-Concord-Gastonia, NC-SC', 'charlotte/2025-09'),
        ('Roanoke, VA', 'roanoke/2025-09')
    ]

    for market_name, output_dir in markets:
        market_short = market_name.split(',')[0].lower().replace('-', '_').replace(' ', '_')

        print(f"\nGenerating reports for {market_name}...")

        # Load dashboard and alerts data
        with open(os.path.join(output_dir, 'dashboard_data.json'), 'r') as f:
            dashboard_data = json.load(f)

        alert_files = [f for f in os.listdir(output_dir) if f.startswith('alerts_') and f.endswith('.json')]
        with open(os.path.join(output_dir, alert_files[0]), 'r') as f:
            alerts_data = json.load(f)

        # Get market dataframe
        market_df = df[df['cbsa_title'] == market_name].sort_values('month_date')

        # Generate report
        report = generate_market_report(market_name, dashboard_data, alerts_data, market_df)
        report_filename = f"market_report_{market_short}_2025-09.md"

        with open(os.path.join(output_dir, report_filename), 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"  - Created {report_filename}")

        # Generate alerts markdown
        alerts_md = generate_alerts_markdown(market_name, alerts_data, dashboard_data)
        alerts_filename = f"alerts_{market_short}_2025-09.md"

        with open(os.path.join(output_dir, alerts_filename), 'w', encoding='utf-8') as f:
            f.write(alerts_md)

        print(f"  - Created {alerts_filename}")

    print("\nAll reports generated successfully!")
