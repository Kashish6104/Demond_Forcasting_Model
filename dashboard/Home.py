import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from PIL import Image
from datetime import datetime

# ───── STREAMLIT CONFIG ─────
st.set_page_config(page_title="📊 Faviy Dairy Forecast Dashboard", layout="wide")

# ───── PATHS ─────
FORECAST_DIR = "data/processed/"
PROC_DIR     = "data/processed/"
EVAL_PATH    = "results/tables/accuracy_summary.csv"
IMG_FOLDER   = "images"

# ───── HEADER ─────
with st.container():
    c1, c2 = st.columns([0.12, 0.88])
    with c1:
        st.image("images/logo1.jpeg", width=300)
    with c2:
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
display_name     = selected_product.replace("_", " ").title()
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

# ╭── OVERVIEW ───────────────────────────────────────────╮
with tab_over:
    st.markdown("### 📊 Overview – Portfolio Snapshot")

    total_rows = forecast_df.shape[0] if forecast_df is not None else 0
    next_fest = None
    if fest_df is not None:
        fut = fest_df[fest_df["Date"] >= pd.Timestamp.today()]
        if not fut.empty:
            next_fest = fut["Date"].min().strftime("%d %b %Y")

    k1, k2, k3 = st.columns(3)
    with k1: kpi("🧀", "Total SKUs", len(products))
    with k2: kpi("📄", "Rows in Forecast", f"{total_rows:,}")
    with k3: kpi("🪔", "Next Festival", next_fest or "—")

    st.divider()

    # Top‑5 plot (Plotly)
    st.markdown("#### 🔝 Top‑5 SKUs by 30‑Day Demand")
    lst = []
    for p in products:
        df_tmp = load_csv(f"{FORECAST_DIR}{p}_forecast.csv", parse_dates=["ds"])
        if df_tmp is not None:
            lst.append({"Product": p.replace("_", " ").title(), "Demand": df_tmp.tail(30)["yhat"].sum()})
    top_df = pd.DataFrame(lst).sort_values("Demand", ascending=False).head(5)
    if not top_df.empty:
        fig_top = px.bar(
            top_df, x="Demand", y="Product", orientation="h",
            color="Demand", color_continuous_scale=["#0055A4", "#E94E1B"],
            labels={"Demand": "Units", "Product": ""}
        )
        fig_top.update_layout(yaxis=dict(categoryorder="total ascending"), coloraxis_showscale=False,
                              margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_top, use_container_width=True)
    else:
        st.info("No data for top SKUs.")

    # Upcoming festivals list
    st.markdown("#### 🎉 Upcoming Festivals (next 30 days)")
    if fest_df is not None:
        today = pd.Timestamp.today().normalize()
        nxt30 = fest_df[(fest_df["Date"] >= today) & (fest_df["Date"] < today + pd.Timedelta(days=30))]
        if nxt30.empty:
            st.write("No festivals in the next 30 days.")
        else:
            st.table(
                nxt30.sort_values("Date")
                     .assign(Date=lambda d: d["Date"].dt.strftime("%d %b %Y"))
                     .rename(columns={"Festival_Name": "Festival"})
            )
    else:
        st.info("No festival calendar loaded.")

# ╭── FORECAST ───────────────────────────────────────────╮
with tab_fore:
    horizon = st.slider("Forecast Horizon (days)", 7, 60, 30)
    if forecast_df is not None:
        today = datetime.today().date()
        curr_stock = stock_df.query("Product_Name == @display_name and Date == @today")["Ending_Stock"].sum() if stock_df is not None else 0
        demand_h = forecast_df.tail(horizon)["yhat"].sum()
        gap = curr_stock - demand_h

        c1, c2, c3 = st.columns(3)
        with c1: kpi("📦", "Current Stock", f"{curr_stock:.0f}")
        with c2: kpi("🛒", f"Demand ({horizon}d)", f"{demand_h:.0f}")
        with c3: kpi("📉", "Gap", f"{gap:+.0f}")

        # Spoilage risk
        shelf_life = 7
        if spoil_df is not None and "Shelf_Life_Days" in spoil_df.columns:
            row = spoil_df.query("Product_Name == @display_name")
            if not row.empty:
                shelf_life = int(row["Shelf_Life_Days"].iat[0])
        at_risk = max(curr_stock - forecast_df.head(shelf_life)["yhat"].sum(), 0)
        if at_risk > 0:
            st.warning(f"🧫 {at_risk:.0f} units risk spoilage in {shelf_life} days.")
        else:
              st.success("✅ No spoilage risk.")


        # Forecast table
        disp = forecast_df[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(horizon)
        disp = disp.rename(columns={"ds": "Date", "yhat": "Predicted", "yhat_lower": "Lower", "yhat_upper": "Upper"})
        st.dataframe(disp, use_container_width=True)

        if st.download_button("📥 Download CSV", disp.to_csv(index=False), file_name=f"{selected_product}_{horizon}d_forecast.csv"):
            st.toast("CSV downloaded!", icon="📁")

        # Interactive line chart
        fig = go.Figure()

        fig.add_trace(go.Scatter(x=forecast_df["ds"], y=forecast_df["yhat"],
                                 mode="lines", name="Forecast", line=dict(color="#0055A4")))
        fig.add_trace(go.Scatter(
            x=pd.concat([forecast_df["ds"], forecast_df["ds"][::-1]]),
            y=pd.concat([forecast_df["yhat_upper"], forecast_df["yhat_lower"][::-1]]),
            fill="toself", fillcolor="rgba(0,85,164,0.15)", line=dict(width=0),
            hoverinfo="skip", showlegend=False
        ))
        if stock_df is not None:
            stock_line = stock_df.query("Product_Name == @display_name")
            fig.add_trace(go.Scatter(x=stock_line["Date"], y=stock_line["Ending_Stock"],
                                     mode="lines", name="Stock", line=dict(color="#E94E1B", dash="dot")))
        if fest_df is not None:
            for d in fest_df["Date"]:
                fig.add_vrect(x0=d, x1=d + pd.Timedelta(days=1),
                              fillcolor="#9B59B6", opacity=0.15, line_width=0)

        fig.update_layout(
            title=f"{display_name} – Forecast, Stock & Festivals",
            yaxis_title="Units", hovermode="x unified",
            legend=dict(orientation="h", y=1.02, x=1, xanchor="right"),
            template="plotly_white", margin=dict(l=20, r=10, t=50, b=30)
        )
        st.plotly_chart(fig, use_container_width=True)

# ╭── EVALUATION ─────────────────────────────────────────╮
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

# ───── FOOTER ─────
st.markdown(
    """
    ---
    <p style='text-align:center;'>
      © 2025 <b>Faviy Dairy Analytics</b> • Built with Python, Prophet, Plotly & Streamlit •
      <a href='https://github.com/your-org/dairy-demand-forecast'>GitHub</a>
    </p>
    """,
    unsafe_allow_html=True,
)
