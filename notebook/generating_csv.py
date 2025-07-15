"""
generate_dairy_reports.py
Create:
    - stock_levels.csv
    - spoilage_summary.csv
    - seasonal_demand.csv
    - festival_dates.csv
    - weather_demand.csv
All written to data/processed/.
"""

import pandas as pd
import os
from pathlib import Path

# --------------------------------------------------------------------
# CONFIG
# --------------------------------------------------------------------
RAW_DIR      = Path("data")
PROC_DIR     = RAW_DIR / "processed"
SOURCE_FILE  = RAW_DIR / "faviy_dairy_cleaned_extended_with_festivals.csv"

PROC_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------
# LOAD
# --------------------------------------------------------------------
df = pd.read_csv(SOURCE_FILE, parse_dates=["Date"])

# --------------------------------------------------------------------
# 1) STOCK LEVELS – daily ending stock per product
# --------------------------------------------------------------------
stock_df = df.copy()
stock_df["Ending_Stock"] = (
      stock_df["Restocked_Units"]
    - stock_df["Units_Sold"]
    - stock_df["Spoilage_Units"]
)

stock_levels = stock_df[["Date", "Product_ID",
                         "Product_Name", "Category", "Ending_Stock"]]

stock_levels.to_csv(PROC_DIR / "stock_levels.csv", index=False)

# --------------------------------------------------------------------
# 2) SPOILAGE SUMMARY – total & avg daily spoilage per product
# --------------------------------------------------------------------
spoilage_summary = (
    df.groupby(["Product_ID", "Product_Name", "Category"], as_index=False)
      .agg(Total_Spoilage_Units=("Spoilage_Units", "sum"),
           Avg_Daily_Spoilage=("Spoilage_Units", "mean"))
)

spoilage_summary.to_csv(PROC_DIR / "spoilage_summary.csv", index=False)

# --------------------------------------------------------------------
# 3) SEASONAL DEMAND – monthly totals & averages by category
# --------------------------------------------------------------------
df["Month"] = df["Date"].dt.month

seasonal_demand = (
    df.groupby(["Month", "Category"], as_index=False)
      .agg(Total_Units_Sold=("Units_Sold", "sum"),
           Avg_Units_Sold=("Units_Sold", "mean"))
      .sort_values(["Month", "Category"])
)

seasonal_demand.to_csv(PROC_DIR / "seasonal_demand.csv", index=False)

# --------------------------------------------------------------------
# 4) FESTIVAL DATES – unique festival days
# --------------------------------------------------------------------
festival_dates = (
    df.loc[df["Festival_Flag"] == 1, ["Date", "Festival_Name"]]
      .drop_duplicates()
      .sort_values("Date")
)

festival_dates.to_csv(PROC_DIR / "festival_dates.csv", index=False)

# --------------------------------------------------------------------
# 5) WEATHER DEMAND – sales aggregated by rounded temperature
# --------------------------------------------------------------------
df["Temp_Rounded"] = df["Temperature"].round()

weather_demand = (
    df.groupby("Temp_Rounded", as_index=False)
      .agg(Total_Units_Sold=("Units_Sold", "sum"),
           Avg_Units_Sold=("Units_Sold", "mean"),
           Observations=("Units_Sold", "count"))
      .rename(columns={"Temp_Rounded": "Temperature"})
)

weather_demand.to_csv(PROC_DIR / "weather_demand.csv", index=False)

print("✅ All five summary files written to", PROC_DIR.resolve())
