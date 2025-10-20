import pandas as pd
import numpy as np
from datetime import datetime
import json

# Read Excel file
file_path = r"C:\Users\1\Documents\GitHub\realtor monthly data analysis\Realtor New Listings.xlsx"
xls = pd.ExcelFile(file_path)

print("=" * 80)
print("REAL ESTATE MARKET DATA ANALYSIS")
print("=" * 80)
print(f"\nAnalysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"\nAvailable Sheets: {xls.sheet_names}")
print("\n")

# Analyze each sheet
for sheet_name in xls.sheet_names:
    print("=" * 80)
    print(f"SHEET: {sheet_name}")
    print("=" * 80)

    df = pd.read_excel(file_path, sheet_name=sheet_name)

    print(f"\nDimensions: {df.shape[0]} rows x {df.shape[1]} columns")
    print(f"\nColumn Names:")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i}. {col}")

    print(f"\nFirst 5 rows:")
    print(df.head().to_string())

    print(f"\nData Types:")
    print(df.dtypes.to_string())

    print(f"\nMissing Values:")
    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(2)
    missing_df = pd.DataFrame({
        'Missing Count': missing,
        'Missing %': missing_pct
    })
    print(missing_df[missing_df['Missing Count'] > 0].to_string())

    # Numerical summary
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if numeric_cols:
        print(f"\nNumerical Summary Statistics:")
        print(df[numeric_cols].describe().to_string())

    print("\n")

print("=" * 80)
print("DETAILED ANALYSIS - RDC_Inventory_Core_Metrics_Metr Sheet")
print("=" * 80)

# Focus on the main metrics sheet
df_main = pd.read_excel(file_path, sheet_name='RDC_Inventory_Core_Metrics_Metr')

# Check if date column exists
date_cols = [col for col in df_main.columns if 'month' in col.lower() or 'date' in col.lower()]
print(f"\nDate-related columns: {date_cols}")

# Save detailed data for inspection
output_file = r"C:\Users\1\Documents\GitHub\realtor monthly data analysis\data_preview.txt"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("FULL DATA PREVIEW - RDC_Inventory_Core_Metrics_Metr\n")
    f.write("=" * 80 + "\n\n")
    f.write(df_main.to_string())

print(f"\nFull data preview saved to: {output_file}")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
