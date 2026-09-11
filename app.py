import streamlit as st
from src.ingest import run_ingest
from src.reconcile import run_reconcile
from src.analytics import load_reconciliations, summarize, group_by_period, group_by_location

st.set_page_config(page_title="Inventory System", page_icon="📦", layout="wide")
st.title("📦 Inventory & Stock Reconciliation")

# Auto-ingest on startup
processed, rejected, errors = run_ingest()
st.success(f"✅ {processed} processed | ⚠️ {rejected} rejected")
if errors:
    with st.expander("See rejection reasons"):
        for e in errors:
            st.write("-", e)

# 2. Reconcile
rows = run_reconcile()
st.success(f"Reconcile: {rows} rows reconciled")

# 3. Analytics sanity check
st.subheader("Quick totals")
df = load_reconciliations()
s = summarize(df)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Rows", s["total_rows"])
col2.metric("Variance Qty", s["total_variance_qty"])
col3.metric("Variance %", f"{s['total_variance_pct']}%")
col4.metric("Flagged", s["flagged_count"])

st.subheader("By month")
st.dataframe(group_by_period(df, "month"))

st.subheader("By location")
st.dataframe(group_by_location(df))