import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from PIL import Image
from datetime import datetime
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# --- Page Config ---
st.set_page_config(page_title="📊 Dairy Demand Forecast Dashboard", layout="wide")

# --- Header ---
st.title("Flavi Dairy Demand Forecast Dashboard")

st.markdown(
    f"""
This interactive dashboard enables demand forecasting analysis across key dairy SKUs at **Faviy Dairy**.  
It provides 30-day forward predictions, accuracy metrics, and downloadable forecast data — helping streamline inventory planning and supply chain operations.

**Features:**
- 🧀 Select a product from the sidebar to view forecast-specific insights
- 📉 Visualize 30-day demand trends with upper/lower confidence bounds
- 🧮 Assess model performance using MAE, RMSE, and MAPE
- 📥 Download product-specific forecasts for planning and reporting

_Last updated: {datetime.today().strftime("%B %d, %Y")}_
"""
)

# --- Paths ---
FORECAST_DIR = "data/processed/"
PLOT_DIR = "results/forecast_charts/"
EVAL_PATH = "results/tables/accuracy_summary.csv"
IMG_FOLDER = "images"

# --- Sidebar: product selector ---
products = [f.replace("_forecast.csv", "") for f in os.listdir(FORECAST_DIR) if f.endswith("_forecast.csv")]
selected_product = st.sidebar.selectbox("Select a Product", products)

display_name = selected_product.replace("_", " ").title()

st.sidebar.markdown(f"### Currently Viewing:\n**{display_name}**")

# --- Sidebar: product image ---
img_png = os.path.join(IMG_FOLDER, f"{selected_product}.png")
img_jpg = os.path.join(IMG_FOLDER, f"{selected_product}.jpeg")

if os.path.exists(img_png):
    st.sidebar.image(Image.open(img_png), caption=display_name, use_container_width=True)
elif os.path.exists(img_jpg):
    st.sidebar.image(Image.open(img_jpg), caption=display_name, use_container_width=True)
else:
    st.sidebar.info("🖼️ No image available for this product.")

# --- Forecast Table & Load Forecast ---
forecast_path = os.path.join(FORECAST_DIR, f"{selected_product}_forecast.csv")
if os.path.exists(forecast_path):
    forecast_df = pd.read_csv(forecast_path)
    forecast_df['ds'] = pd.to_datetime(forecast_df['ds'])

    forecast_display = (
        forecast_df[["ds", "yhat", "yhat_lower", "yhat_upper"]]
        .tail(30)
        .rename(columns={
            "ds": "Date",
            "yhat": "Predicted Demand",
            "yhat_lower": "Lower Bound",
            "yhat_upper": "Upper Bound",
        })
    )

    # --- KPI Summary ---
    st.markdown("## Forecast Summary ")
    col1, col2, col3 = st.columns(3)
    total_forecast_days = 30
    last_forecast_date = forecast_df['ds'].max().date()
    peak_demand = forecast_df['yhat'].max()

    col1.metric("📅 Days Forecasted", f"{total_forecast_days} days")
    col2.metric("📈 Last Forecast Date", f"{last_forecast_date}")
    col3.metric("🔥 Peak Predicted Demand", f"{peak_demand:.2f} units")

    st.subheader(f"📅 Forecast Data – {display_name} (Next 30 Days)")
    st.dataframe(forecast_display, use_container_width=True)
    st.download_button(
        label="📥 Download Forecast Data",
        data=forecast_display.to_csv(index=False).encode("utf-8"),
        file_name=f"{selected_product}_forecast.csv",
        mime="text/csv",
    )
else:
    st.warning("⚠️ Forecast data not found.")

# --- Forecast Plot ---
img_path = os.path.join(PLOT_DIR, f"{selected_product}_plot.png")
if os.path.exists(img_path):
    st.subheader(f"📈 Forecast Plot – {display_name}")
    st.image(img_path, use_container_width=True)
else:
    st.warning("⚠️ Forecast image not found.")

# --- Forecast vs Actual Chart & Seasonality ---
with st.expander(f"📉 Forecast vs Actual & Seasonality – {display_name}", expanded=True):

    cleaned_path = os.path.join('data/processed/', f"{selected_product}_cleaned.csv")

    if os.path.exists(cleaned_path):
        actual_df = pd.read_csv(cleaned_path)
        actual_df.columns = actual_df.columns.str.strip().str.lower()

        # Debug logs
        st.write("📋 Columns in actual_df:", actual_df.columns.tolist())

           # ✅ Replace this block
        y_col = 'units_sold' if 'units_sold' in actual_df.columns else None
        date_col = 'date' if 'date' in actual_df.columns else None

        st.write("🟢 Using columns – Date:", date_col, " | Value:", y_col)

        if date_col and y_col:
            actual_df.rename(columns={date_col: 'ds', y_col: 'y'}, inplace=True)
            actual_df['ds'] = pd.to_datetime(actual_df['ds'], errors='coerce')
            forecast_df['ds'] = pd.to_datetime(forecast_df['ds'], errors='coerce')

            st.write("🔗 Forecast date range:", forecast_df['ds'].min().date(), "to", forecast_df['ds'].max().date())
            st.write("🔗 Actuals date range:", actual_df['ds'].min().date(), "to", actual_df['ds'].max().date())

            merged_df = pd.merge(forecast_df, actual_df[['ds', 'y']], on='ds', how='inner')
            merged_df = merged_df.sort_values('ds')

            st.write("📊 Merged rows for plotting:", len(merged_df))

            if not merged_df.empty:
                st.subheader(f"📊 Forecast vs Actual – {display_name}")
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.plot(merged_df['ds'], merged_df['yhat'], label='Forecasted', color='blue')
                ax.plot(merged_df['ds'], merged_df['y'], label='Actual', color='green')
                ax.fill_between(merged_df['ds'], merged_df['yhat_lower'], merged_df['yhat_upper'],
                                color='blue', alpha=0.1, label='Forecast Uncertainty')
                ax.set_xlabel('Date')
                ax.set_ylabel('Units Sold')
                ax.set_title(f"{display_name} – Forecast vs Actual Demand", fontsize=16)
                ax.legend(loc='upper left', fontsize=10)
                st.pyplot(fig)

                # --- Seasonality Tabs ---
                st.subheader(f"📊 Seasonality Insights – {display_name}")
                seasonality_df = actual_df.copy()
                seasonality_df['Weekday'] = seasonality_df['ds'].dt.day_name()
                seasonality_df['Month'] = seasonality_df['ds'].dt.month_name()

                tab1, tab2 = st.tabs(["🗓️ Weekly Pattern", "📅 Monthly Pattern"])

                with tab1:
                    weekday_avg = seasonality_df.groupby('Weekday')['y'].mean()
                    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    weekday_avg = weekday_avg.reindex(weekday_order)

                    fig1, ax1 = plt.subplots()
                    ax1.bar(weekday_avg.index, weekday_avg.values, color='skyblue')
                    ax1.set_ylabel("Avg Demand")
                    ax1.set_title("Average Demand by Weekday")
                    ax1.tick_params(axis='x', rotation=45)
                    st.pyplot(fig1)

                with tab2:
                    month_avg = seasonality_df.groupby('Month')['y'].mean()
                    month_order = [
                        'January', 'February', 'March', 'April', 'May', 'June',
                        'July', 'August', 'September', 'October', 'November', 'December'
                    ]
                    month_avg = month_avg.reindex(month_order)

                    fig2, ax2 = plt.subplots()
                    ax2.bar(month_avg.index, month_avg.values, color='salmon')
                    ax2.set_ylabel("Avg Demand")
                    ax2.set_title("Average Demand by Month")
                    ax2.tick_params(axis='x', rotation=45)
                    st.pyplot(fig2)
            else:
                st.warning("⚠️ No overlapping dates between forecast and actual data.")
        else:
            st.warning("⚠️ Required columns not found in actual data.")
    else:
        st.info("📭 Actual data not available for this product.")

# --- Accuracy Metrics Table ---
if os.path.exists(EVAL_PATH):
    eval_df = pd.read_csv(EVAL_PATH)
    metrics = eval_df[eval_df["Product"].str.lower() == display_name.lower()]

    if not metrics.empty:
        st.subheader(f"📏 Evaluation Metrics – {display_name}")
        col1, col2, col3 = st.columns(3)
        col1.metric("MAE (Average Error)", f"{metrics['MAE'].values[0]}")
        col2.metric("RMSE (Error Spread)", f"{metrics['RMSE'].values[0]}")
        col3.metric("MAPE (%)", f"{metrics['MAPE (%)'].values[0]}%")

        mape_val = metrics["MAPE (%)"].values[0]
        if mape_val < 5:
            st.success("🟢 High forecast accuracy! Demand trend is stable.")
        elif mape_val < 10:
            st.info("🟡 Moderate accuracy. Some demand variation possible.")
        else:
            st.warning("🔴 Low accuracy. Demand is highly variable.")
    else:
        st.info("No evaluation metrics found for this product.")
else:
    st.warning("⚠️ Accuracy summary file not found.")

# --- Full Accuracy Table ---
with st.expander("📊 View Accuracy Summary for All Products"):
    if os.path.exists(EVAL_PATH):
        st.dataframe(
            eval_df.rename(columns={
                "Product": "Product Name",
                "MAE": "Mean Absolute Error",
                "RMSE": "Root Mean Squared Error",
                "MAPE (%)": "MAPE (%)",
            }).sort_values("MAPE (%)"),
            use_container_width=True,
        )
    else:
        st.info("No accuracy summary available.")
        
        

# --- Footer ---
st.markdown(
    """
---
© 2025 **Faviy Dairy Analytics Team**  
Powered by **Python**, **Facebook Prophet**, and **Streamlit**  
For internal use – demand planning, supply chain optimization, and strategic decision-making.  

🔗 [View project repository on GitHub](https://github.com/your-org/dairy-demand-forecast)  
📧 Contact: analytics-team@faviydairy.com
"""
)
