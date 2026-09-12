import streamlit as st
import plotly.express as px
from datetime import date, timedelta

from src.analytics import (
    load_reconciliations,
    summarize,
    group_by_period,
    group_by_location,
    top_variance_skus,
)

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
st.title("📊 Dashboard")

# Date range filter
today = date.today()
default_start = today - timedelta(days=90)

col1, col2 = st.columns(2)
start = col1.date_input("Start date", value=default_start)
end = col2.date_input("End date", value=today)

df = load_reconciliations(start_date=start, end_date=end)

if df.empty:
    st.warning("No data in selected range.")
    st.stop()

# Summary metrics
s = summarize(df)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Rows", s["total_rows"])
c2.metric("Variance Qty", s["total_variance_qty"])
c3.metric("Variance %", f"{s['total_variance_pct']}%")
c4.metric("Flagged", s["flagged_count"])

st.subheader("Variance by month")

by_month = group_by_period(df, "month")
if not by_month.empty:
    fig = px.bar(
        by_month,
        x="period",
        y="variance_qty",
        color="variance_qty",
        color_continuous_scale=["red", "lightgray", "green"],
        text="variance_qty",
    )
    fig.update_layout(showlegend=False, height=350)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No monthly data.")

st.subheader("Variance by location")

by_loc = group_by_location(df)
if not by_loc.empty:
    fig = px.bar(
        by_loc,
        x="location",
        y="variance_qty",
        color="variance_qty",
        color_continuous_scale=["red", "lightgray", "green"],
        text="variance_qty",
    )
    fig.update_layout(showlegend=False, height=350)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No location data.")

st.subheader("Variance trend")

by_day = group_by_period(df, "day")
if not by_day.empty:
    fig = px.line(
        by_day,
        x="period",
        y="variance_qty",
        markers=True,
    )
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No trend data.")

st.subheader("Top variance SKUs")

top = top_variance_skus(df, n=10)
if not top.empty:
    st.dataframe(top, use_container_width=True, hide_index=True)
else:
    st.info("No SKU data.")