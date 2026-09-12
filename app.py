import streamlit as st
import pandas as pd
import sqlite3

from src.ingest import run_ingest, REQUIRED_COLUMNS, INCOMING
from src.reconcile import run_reconcile
from src.analytics import load_reconciliations, summarize, group_by_period, group_by_location

st.set_page_config(page_title="Inventory System", page_icon="📦", layout="wide")
st.title("📦 Inventory & Stock Reconciliation")

# ================= UPLOAD & INGEST =================
st.subheader("📤 Upload & Ingest")

uploaded = st.file_uploader(
    "Choose Excel or CSV",
    type=["xlsx", "xls", "csv"],
    key="uploader_main",
)

if uploaded is not None:
    try:
        if uploaded.name.lower().endswith(".csv"):
            preview_df = pd.read_csv(uploaded)
        else:
            preview_df = pd.read_excel(uploaded)

        st.write(f"**{uploaded.name}** — {len(preview_df)} rows × {len(preview_df.columns)} columns")
        st.write("Preview (first 5 rows):")
        st.dataframe(preview_df.head(), use_container_width=True, hide_index=True)

        missing = [c for c in REQUIRED_COLUMNS if c not in preview_df.columns]
        if missing:
            st.error(f"❌ Cannot ingest — missing columns: {missing}")
        else:
            st.success("✅ All required columns found.")

            if st.button("✅ Ingest this file", key="btn_ingest"):
                # Save uploaded bytes to data/incoming/
                INCOMING.mkdir(parents=True, exist_ok=True)
                target = INCOMING / uploaded.name
                with open(target, "wb") as f:
                    f.write(uploaded.getbuffer())

                # Run pipeline
                processed, rejected, errors = run_ingest()
                rows = run_reconcile()

                st.success(f"Ingest: {processed} processed | {rejected} rejected")
                st.success(f"Reconcile: {rows} rows reconciled")
                if errors:
                    with st.expander("Rejection reasons"):
                        for e in errors:
                            st.write("-", e)
                st.rerun()

    except Exception as e:
        st.error(f"Failed to read file: {e}")

st.divider()

# ================= TOTALS =================
st.subheader("📊 Quick totals")
df = load_reconciliations()

if not df.empty:
    s = summarize(df)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Rows", s["total_rows"])
    col2.metric("Variance Qty", s["total_variance_qty"])
    col3.metric("Variance %", f"{s['total_variance_pct']}%")
    col4.metric("Flagged", s["flagged_count"])

    st.subheader("By month")
    st.dataframe(group_by_period(df, "month"), use_container_width=True)

    st.subheader("By location")
    st.dataframe(group_by_location(df), use_container_width=True)
else:
    st.info("No data yet. Upload a file above.")

# ================= RESET =================
st.divider()
st.subheader("🗑️ Reset")

with st.expander("⚠️ Danger zone — wipe all data"):
    st.warning("This deletes ALL rows from counts and reconciliations. Cannot be undone.")
    confirm = st.text_input("Type WIPE to confirm", key="wipe_confirm")
    if st.button("Reset database", key="btn_reset"):
        if confirm == "WIPE":
            conn = sqlite3.connect("data/inventory.db")
            conn.execute("DELETE FROM counts")
            conn.execute("DELETE FROM reconciliations")
            conn.commit()
            conn.close()
            st.success("Database cleared.")
            st.rerun()
        else:
            st.error("Type WIPE exactly to confirm.")