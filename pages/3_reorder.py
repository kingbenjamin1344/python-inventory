import streamlit as st
import plotly.express as px

from src.analytics import load_reconciliations

st.set_page_config(page_title="Reorder", page_icon="📦", layout="wide")
st.title("📦 Reorder Alerts")

df = load_reconciliations()

if df.empty:
    st.warning("No data. Run ingest first.")
    st.stop()

# Keep only the latest row per SKU
latest = df.sort_values("count_date").groupby("sku", as_index=False).tail(1)

st.write(f"{len(latest)} unique SKUs loaded")

# Threshold
threshold = st.number_input("Reorder threshold (system qty at or below)", min_value=0, value=20, step=5)

# Filter low stock
low = latest[latest["system_qty"] <= threshold].copy()
low = low.sort_values("system_qty")

st.subheader(f"⚠️ {len(low)} SKUs need reorder")

display_cols = ["sku", "description", "location", "system_qty", "physical_qty", "variance_status"]
st.dataframe(low[display_cols], use_container_width=True, hide_index=True)

if not low.empty:
    st.subheader("Low stock ranked")
    fig = px.bar(
        low,
        x="sku",
        y="system_qty",
        color="variance_status",
        text="system_qty",
        color_discrete_map={"OK": "#28a745", "FLAG": "#ffc107", "CRITICAL": "#dc3545"},
    )
    fig.update_layout(height=350, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No SKUs below threshold.")