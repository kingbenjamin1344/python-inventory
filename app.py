import streamlit as st
from src.ingest import run_ingest

st.set_page_config(page_title="Inventory System", page_icon="📦", layout="wide")
st.title("📦 Inventory & Stock Reconciliation")

# Auto-ingest on startup
processed, rejected, errors = run_ingest()
st.success(f"✅ {processed} processed | ⚠️ {rejected} rejected")
if errors:
    with st.expander("See rejection reasons"):
        for e in errors:
            st.write("-", e)