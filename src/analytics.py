import sqlite3
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "inventory.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    return conn


def load_reconciliations(start_date=None, end_date=None):
    """Return reconciliations filtered by date range (inclusive)."""
    conn = get_db()
    df = pd.read_sql("SELECT * FROM reconciliations", conn)
    conn.close()

    if df.empty:
        return df

    df["count_date"] = pd.to_datetime(df["count_date"], errors="coerce")
    df = df.dropna(subset=["count_date"])

    if start_date is not None:
        df = df[df["count_date"] >= pd.to_datetime(start_date)]
    if end_date is not None:
        df = df[df["count_date"] <= pd.to_datetime(end_date)]

    return df.reset_index(drop=True)


def summarize(df):
    """Return a dict of total metrics for the given dataframe."""
    if df.empty:
        return {
            "total_rows": 0,
            "total_system_qty": 0,
            "total_physical_qty": 0,
            "total_variance_qty": 0,
            "total_variance_pct": 0.0,
            "flagged_count": 0,
            "critical_count": 0,
        }

    total_system = int(df["system_qty"].sum())
    total_variance = int(df["variance_qty"].sum())

    return {
        "total_rows": len(df),
        "total_system_qty": total_system,
        "total_physical_qty": int(df["physical_qty"].sum()),
        "total_variance_qty": total_variance,
        "total_variance_pct": round((total_variance / total_system * 100) if total_system else 0.0, 2),
        "flagged_count": int((df["variance_status"] != "OK").sum()),
        "critical_count": int((df["variance_status"] == "CRITICAL").sum()),
    }

def group_by_period(df, period="month"):
    """
    Group by 'day', 'month', 'quarter', or 'year'.
    Returns a dataframe with totals per period.
    """
    if df.empty:
        return pd.DataFrame()

    df = df.copy()
    df["count_date"] = pd.to_datetime(df["count_date"], errors="coerce")
    df = df.dropna(subset=["count_date"])

    if period == "day":
        df["period"] = df["count_date"].dt.strftime("%Y-%m-%d")
    elif period == "month":
        df["period"] = df["count_date"].dt.strftime("%Y-%m")
    elif period == "quarter":
        df["period"] = df["count_date"].dt.year.astype(str) + "-Q" + df["count_date"].dt.quarter.astype(str)
    elif period == "year":
        df["period"] = df["count_date"].dt.year.astype(str)
    else:
        raise ValueError("period must be day, month, quarter, or year")

    grouped = df.groupby("period").agg(
        rows=("sku", "count"),
        system_qty=("system_qty", "sum"),
        physical_qty=("physical_qty", "sum"),
        variance_qty=("variance_qty", "sum"),
        flagged=("variance_status", lambda s: (s != "OK").sum()),
    ).reset_index()

    grouped["variance_pct"] = grouped.apply(
        lambda r: round((r["variance_qty"] / r["system_qty"] * 100) if r["system_qty"] else 0.0, 2),
        axis=1,
    )

    return grouped.sort_values("period").reset_index(drop=True)

def group_by_location(df):
    if df.empty:
        return pd.DataFrame()

    grouped = df.groupby("location").agg(
        rows=("sku", "count"),
        system_qty=("system_qty", "sum"),
        physical_qty=("physical_qty", "sum"),
        variance_qty=("variance_qty", "sum"),
        flagged=("variance_status", lambda s: (s != "OK").sum()),
    ).reset_index()

    grouped["variance_pct"] = grouped.apply(
        lambda r: round((r["variance_qty"] / r["system_qty"] * 100) if r["system_qty"] else 0.0, 2),
        axis=1,
    )
    return grouped.sort_values("variance_qty").reset_index(drop=True)

def top_variance_skus(df, n=10):
    """Return top N SKUs by absolute variance quantity."""
    if df.empty:
        return pd.DataFrame()

    df = df.copy()
    df["abs_variance"] = df["variance_qty"].abs()

    result = df.sort_values("abs_variance", ascending=False).head(n)
    return result[["sku", "description", "location", "system_qty", "physical_qty",
                   "variance_qty", "variance_pct", "variance_status"]].reset_index(drop=True)


if __name__ == "__main__":
    df = load_reconciliations()
    print("--- Top variance SKUs ---")
    print(top_variance_skus(df, n=10))