import streamlit as st

st.set_page_config(page_title="Ask AI", page_icon="🤖", layout="wide")
st.title("🤖 Ask About Your Inventory")
st.caption("Ask questions in plain English. Answers come from your real data.")

question = st.text_input("Your question", placeholder="e.g. Which SKU has the biggest variance?")

import json
import ollama
import pandas as pd

from src.analytics import (
    load_reconciliations,
    summarize,
    group_by_period,
    group_by_location,
    top_variance_skus,
)

MODEL = "qwen2.5:0.5b"

# ---------- Load data once ----------
df = load_reconciliations()

if df.empty:
    st.warning("No data. Ingest files first.")
    st.stop()

# ---------- Build a compact data summary for the LLM ----------
summary = summarize(df)
by_location = group_by_location(df).to_dict(orient="records")
by_month = group_by_period(df, "month").to_dict(orient="records")
top_skus = top_variance_skus(df, n=10).to_dict(orient="records")

data_context = {
    "summary": summary,
    "by_location": by_location,
    "by_month": by_month,
    "top_variance_skus": top_skus,
}

# ---------- System prompt ----------
system_prompt = f"""You are a data analyst for an inventory system.
Answer ONLY using the JSON data below. Never invent numbers.
If the answer is not in the data, say "I don't have that in the current data."

DATA:
{json.dumps(data_context, indent=2, default=str)}

Rules:
- Use exact numbers from the data.
- Be concise.
- If asked for totals, use summary fields.
- If asked about location, use by_location.
- If asked about time, use by_month.
- If asked about top SKUs, use top_variance_skus.
"""

# ---------- Handle question ----------
if st.button("Ask") and question.strip():
    with st.spinner("Thinking..."):
        response = ollama.chat(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
        )
    st.write(response["message"]["content"])