import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from PIL import Image
from datetime import datetime

# ───── MATPLOTLIB THEME ─────
plt.rcParams.update({
    "axes.prop_cycle": plt.cycler(color=["#0055A4", "#E94E1B", "#F2C14E"]),
    "axes.edgecolor": "#B0B0B0",
    "axes.linewidth": 0.8,
    "grid.color": "#E0E0E0",
    "grid.linestyle": "--",
})

# ───── STREAMLIT CONFIG ─────
st.set_page_config(page_title="📊 Faviy Dairy Forecast Dashboard", layout="wide")

# ───── PATHS ─────
FORECAST_DIR = "data/processed/"
PROC_DIR = "data/processed/"
EVAL_PATH = "results/tables/accuracy_summary.csv"
IMG_FOLDER = "images"

# ───── HEADER BLOCK ─────
with st.container():
    cols = st.columns([0.1, 0.9])
    with cols[0]:
        st.image("images/logo1.jpeg", width=800)  # ← Streamlit serves the file
    with cols[1]:
        st.markdown(
            """
            <h2 style='margin-bottom:0'>Faviy Dairy – Demand Intelligence Dashboard</h2>
            <p style='margin-top:2px;color:#666'>
              Forecast • Inventory • Spoilage • Festival Impact
            </p>
            """,
            unsafe_allow_html=True,
        )
# ───── CSV LOADER ─────
@st.cache_data
def load_csv(path, parse_dates=None):
    return pd.read_csv(path, parse_dates=parse_dates) if os.path.exists(path) else None

# ───── SIDEBAR ─────
products = sorted(f.replace("_forecast.csv", "") for f in os.listdir(FORECAST_DIR) if f.endswith("_forecast.csv"))
selected_product = st.sidebar.selectbox("🧀 Select Product", products)
display_name = selected_product.replace("_", " ").title()

st.sidebar.markdown(f"### Viewing: **{display_name}**")

for ext in ("png", "jpeg"):
    img_path = os.path.join(IMG_FOLDER, f"{selected_product}.{ext}")
    if os.path.exists(img_path):
        st.sidebar.image(Image.open(img_path), caption=display_name, use_container_width=True)
        break
else:
    st.sidebar.info("🖼️ No product image.")

# ───── LOAD DATA ─────
forecast_df = load_csv(f"{FORECAST_DIR}{selected_product}_forecast.csv", parse_dates=["ds"])
stock_df    = load_csv(f"{PROC_DIR}stock_levels.csv", parse_dates=["Date"])
spoil_df    = load_csv(f"{PROC_DIR}spoilage_summary.csv")
fest_df     = load_csv(f"{PROC_DIR}festival_dates.csv", parse_dates=["Date"])
eval_df     = load_csv(EVAL_PATH)

# ───── KPI TILE FUNCTION ─────
def kpi(icon, label, value):
    st.markdown(
        f"""
        <div style='display:flex;align-items:center;border:1px solid #EEE;
                    border-radius:12px;padding:0.6rem 1rem;margin-bottom:4px;'>
            <span style='font-size:1.4rem;margin-right:0.7rem'>{icon}</span>
            <div>
              <div style='font-size:0.85rem;color:#6E6E6E'>{label}</div>
              <div style='font-weight:600;font-size:1.1rem'>{value}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ───── TABS ─────
tab_over, tab_fore, tab_eval = st.tabs(["📊 Overview", "📈 Forecast", "📏 Evaluation"])

# ╭────────────────────────────────────────────────────────╮
# │ OVERVIEW TAB                                           │
# ╰────────────────────────────────────────────────────────╯
with tab_over:
    st.markdown("### 📊 Overview – Portfolio Snapshot")

    # KPI tiles
    total_rows = forecast_df.shape[0] if forecast_df is not None else 0
    next_fest_date = None
    if fest_df is not None:
        future_fest = fest_df[fest_df["Date"] >= pd.Timestamp.today()]
        if not future_fest.empty:
            next_fest_date = future_fest["Date"].min().strftime("%d %b %Y")

    k1, k2, k3 = st.columns(3)
    with k1: kpi("🧀", "Total SKUs", len(products))
    with k2: kpi("📄", "Rows in Forecast", f"{total_rows:,}")
    with k3: kpi("🪔", "Next Festival", next_fest_date or "—")

    st.divider()

    # Top‑5 SKUs by 30‑day demand
    st.markdown("#### 🔝 Top‑5 SKUs by 30‑Day Forecast Demand")
    top_df_list = []
    for p in products:
        df_tmp = load_csv(f"{FORECAST_DIR}{p}_forecast.csv", parse_dates=["ds"])
        if df_tmp is not None:
            total_30 = df_tmp.tail(30)["yhat"].sum()
            top_df_list.append({"Product": p.replace("_", " ").title(), "Demand": total_30})
    top_df = pd.DataFrame(top_df_list).sort_values("Demand", ascending=False).head(5)

    if not top_df.empty:
        fig1, ax1 = plt.subplots(figsize=(7, 3))
        ax1.barh(top_df["Product"], top_df["Demand"])
        ax1.invert_yaxis()
        ax1.set_xlabel("Units")
        st.pyplot(fig1)
    else:
        st.info("No forecast data to display top SKUs.")

    # Upcoming festivals (next 30 days)
    st.markdown("#### 🎉 Upcoming Festivals (next 30 days)")
    if fest_df is None:
        st.info("No festival calendar loaded.")
    else:
        today = pd.Timestamp.today().normalize()
        next_30 = today + pd.Timedelta(days=30)
        nxt = fest_df[(fest_df["Date"] >= today) & (fest_df["Date"] < next_30)]

        if nxt.empty:
            st.write("No festivals in the next 30 days.")
        else:
            st.table(
                nxt.sort_values("Date")
                   .assign(Date=lambda d: d["Date"].dt.strftime("%d %b %Y"))
                   .rename(columns={"Festival_Name": "Festival"})
            )

# ╭────────────────────────────────────────────────────────╮
# │ FORECAST TAB                                           │
# ╰────────────────────────────────────────────────────────╯
with tab_fore:
    horizon = st.slider("Forecast Horizon", 7, 60, 30)
    if forecast_df is not None:
        today = datetime.today().date()
        todays_stock = 0
        if stock_df is not None:
            todays_stock = (
                stock_df.query("Product_Name == @display_name and Date == @today")["Ending_Stock"].sum()
            )
        demand_horizon = forecast_df.tail(horizon)["yhat"].sum()
        gap = todays_stock - demand_horizon

        c1, c2, c3 = st.columns(3)
        with c1: kpi("📦", "Current Stock", f"{todays_stock:.0f}")
        with c2: kpi("🛒", f"Demand ({horizon} d)", f"{demand_horizon:.0f}")
        with c3: kpi("📉", "Stock Gap", f"{gap:+.0f} units")

        # Spoilage risk
        shelf_life_days = 7
        if spoil_df is not None and "Shelf_Life_Days" in spoil_df.columns:
            row = spoil_df.query("Product_Name == @display_name")
            if not row.empty:
                shelf_life_days = int(row["Shelf_Life_Days"].iat[0])
        at_risk = max(todays_stock - forecast_df.head(shelf_life_days)["yhat"].sum(), 0)
        if at_risk > 0:
            st.warning(f"🧫 Spoilage risk: ~{at_risk:.0f} units may expire in {shelf_life_days} days.")
        else:
            st.success("✅ No spoilage risk in shelf life window.")

        # Forecast table
        disp = (
            forecast_df[["ds", "yhat", "yhat_lower", "yhat_upper"]]
            .tail(horizon)
            .rename(columns={"ds": "Date", "yhat": "Predicted", "yhat_lower": "Lower", "yhat_upper": "Upper"})
        )
        st.dataframe(disp, use_container_width=True)

        if st.download_button("📥 Download Forecast CSV", disp.to_csv(index=False), file_name=f"{selected_product}_forecast.csv"):
            st.toast("CSV downloaded!", icon="📁")

        # Forecast chart
        fig, ax = plt.subplots(figsize=(9, 4))
        ax.plot(forecast_df["ds"], forecast_df["yhat"], label="Forecast")
        ax.fill_between(forecast_df["ds"], forecast_df["yhat_lower"], forecast_df["yhat_upper"], alpha=0.1)
        if stock_df is not None:
            stock_line = stock_df.query("Product_Name == @display_name")
            ax.plot(stock_line["Date"], stock_line["Ending_Stock"], linestyle=":", label="Stock")
        if fest_df is not None:
            for d in fest_df["Date"]:
                ax.axvspan(d, d + pd.Timedelta(days=1), color="#9B59B6", alpha=0.15)
        ax.set_title(f"{display_name} – Forecast, Stock & Festivals")
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)

# ╭────────────────────────────────────────────────────────╮
# │ EVALUATION TAB                                         │
# ╰────────────────────────────────────────────────────────╯
with tab_eval:
    if eval_df is not None:
        st.subheader("Evaluation Metrics")
        metrics = eval_df[eval_df["Product"].str.lower() == display_name.lower()]
        if not metrics.empty:
            mape_col = next((c for c in metrics.columns if c.lower().startswith("mape")), "MAPE (%)")
            d1, d2, d3 = st.columns(3)
            d1.metric("MAE", f"{metrics['MAE'].iat[0]:.2f}")
            d2.metric("RMSE", f"{metrics['RMSE'].iat[0]:.2f}")
            d3.metric("MAPE", f"{metrics[mape_col].iat[0]:.2f}%")
        with st.expander("📊 All Product Accuracy"):
            st.dataframe(eval_df.sort_values("MAPE (%)"), use_container_width=True)

# FOOTER
st.markdown(
    """
    ---
    <p style='text-align:center;'>
      © 2025 <b>Faviy Dairy Analytics</b> • Built with Python, Prophet, and Streamlit •
      <a href='https://github.com/your-org/dairy-demand-forecast'>GitHub</a>
    </p>
    """,
    unsafe_allow_html=True,
)
