import streamlit as st
import pandas as pd
from datetime import date, timedelta

from src.analytics import load_reconciliations

st.set_page_config(page_title="Variance", page_icon="⚠️", layout="wide")
st.title("⚠️ Variance Detail")

# ---------- Date filter ----------
today = date.today()
default_start = today - timedelta(days=90)

col1, col2 = st.columns(2)
start = col1.date_input("Start date", value=default_start)
end = col2.date_input("End date", value=today)

df = load_reconciliations(start_date=start, end_date=end)

if df.empty:
    st.warning("No data in selected range.")
    st.stop()

st.write(f"{len(df)} rows loaded")

# ---------- Filters ----------
status_pick = st.radio("Status", ["All", "OK", "FLAG", "CRITICAL"], horizontal=True)

locations = ["All"] + sorted(df["location"].dropna().unique().tolist())
location_pick = st.selectbox("Location", locations)

search = st.text_input("Search SKU or description", "")

filtered = df.copy()

if status_pick != "All":
    filtered = filtered[filtered["variance_status"] == status_pick]

if location_pick != "All":
    filtered = filtered[filtered["location"] == location_pick]

if search.strip():
    q = search.strip().lower()
    filtered = filtered[
        filtered["sku"].astype(str).str.lower().str.contains(q, na=False)
        | filtered["description"].astype(str).str.lower().str.contains(q, na=False)
    ]

st.write(f"Showing {len(filtered)} of {len(df)} rows")

# ---------- Prepare display table ----------
display_cols = [
    "sku", "description", "location", "count_date",
    "system_qty", "physical_qty",
    "variance_qty", "variance_pct", "variance_status",
]
display_df = filtered[display_cols].copy()

# Emoji status labels (works on any pandas version)
status_map = {"OK": "🟢 OK", "FLAG": "🟡 FLAG", "CRITICAL": "🔴 CRITICAL"}
display_df["variance_status"] = display_df["variance_status"].map(status_map).fillna(display_df["variance_status"])

# ---------- Show table ----------
st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "sku": st.column_config.TextColumn("SKU", width="small"),
        "description": st.column_config.TextColumn("Description"),
        "location": st.column_config.TextColumn("Location", width="small"),
        "count_date": st.column_config.TextColumn("Count Date"),
        "system_qty": st.column_config.NumberColumn("System", format="%d"),
        "physical_qty": st.column_config.NumberColumn("Physical", format="%d"),
        "variance_qty": st.column_config.NumberColumn("Var Qty", format="%d"),
        "variance_pct": st.column_config.NumberColumn("Var %", format="%.2f%%"),
        "variance_status": st.column_config.TextColumn("Status"),
    },
)

# ---------- Download ----------
csv = display_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="⬇️ Download filtered CSV",
    data=csv,
    file_name="variance_filtered.csv",
    mime="text/csv",
)