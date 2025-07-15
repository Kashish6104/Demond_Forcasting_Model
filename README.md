
#  Dairy – Demand Intelligence Dashboard

A Streamlit-based interactive dashboard for **demand forecasting, inventory planning, and spoilage risk analysis** in the dairy supply chain. Built using **Prophet**, **pandas**, and **matplotlib**, this tool helps planners make smarter stock decisions by visualizing forecasted demand alongside current stock levels and festival impact.


# Architecture

CSV ─┐ ┌─► accuracy_summary.csv

├► 01_data_preprocessing.py


├► 02_prophet_forecasting.py ──► *_forecast.csv + *_plot.png

├► 03_evaluation_metrics.py ──► results/tables/


└► generate_dairy_reports.py ──► stock_levels.csv, spoilage_summary.csv, ...
▼



# Project Structure

📦 dairy-demand-forecast/

├── streamlit_app.py # Main Streamlit app

├── data/

│ └── processed/ # Cleaned + model outputs

├── results/

│ └── tables/ # Evaluation metrics

├── images/ # Logos, SKU thumbnails, screenshots

├── notebook/ # ETL, forecasting, evaluation scripts

│ ├── 01_data_preprocessing.py

│ ├── 02_prophet_forecasting.py

│ ├── 03_evaluation_metrics.py

│ └── generate_dairy_reports.py

├── requirements.txt

└── README.md




# Features

- **Forecast Viewer**: 7 to 60-day daily forecasts for each SKU using Prophet
- **Inventory Snapshot**: Live stock vs forecast demand & gap insights
- **Spoilage Alerts**: Estimate at-risk stock based on shelf life
- **Festival Impact Overlay**: Highlight demand spikes on festival dates
- **Top SKUs Overview**: See high-demand products across the next 30 days
- **CSV Export**: Download forecasts for local analysis
- **Interactive Charts**: Plot demand vs stock with shaded confidence intervals
# Quick Start

```bash
# 1.  Clone
git clone https://github.com/your‑org/dairy-demand-forecast.git
cd dairy-demand-forecast

# 2.  Install dependencies
pip install -r requirements.txt

# 3.  Run ETL + forecast pipeline
python scripts/01_data_preprocessing.py
python scripts/02_prophet_forecasting.py
python scripts/03_evaluation_metrics.py
python scripts/generate_dairy_reports.py

# 4.  Launch dashboard
streamlit run streamlit_app.py
```

# Forecast Logic
**Model**: Facebook Prophet

**Inputs**: Product-level daily sales, stock levels, festival calendar

**Output**: SKU-specific forecasts with 80% confidence intervals

**💡 Forecast smarter. Waste less. Stay fresh.**