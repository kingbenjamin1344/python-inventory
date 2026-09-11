import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "inventory.db"

# Thresholds (in percent)
OK_THRESHOLD = 2.0
FLAG_THRESHOLD = 5.0

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reconciliations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT,
            description TEXT,
            location TEXT,
            count_date TEXT,
            system_qty INTEGER,
            physical_qty INTEGER,
            variance_qty INTEGER,
            variance_pct REAL,
            variance_status TEXT,
            reconciled_at TEXT
        )
    """)
    conn.commit()
    return conn

def load_counts():
    conn = get_db()
    df = pd.read_sql("SELECT * FROM counts", conn)
    conn.close()
    return df

def compute_variance(df):
    df = df.copy()

    df["system_qty"] = pd.to_numeric(df["system_qty"], errors="coerce").fillna(0)
    df["physical_qty"] = pd.to_numeric(df["physical_qty"], errors="coerce").fillna(0)

    df["variance_qty"] = df["physical_qty"] - df["system_qty"]

    df["variance_pct"] = df.apply(
        lambda r: (r["variance_qty"] / r["system_qty"] * 100) if r["system_qty"] != 0 else 0.0,
        axis=1,
    )

    def status(pct):
        a = abs(pct)
        if a <= OK_THRESHOLD:
            return "OK"
        if a <= FLAG_THRESHOLD:
            return "FLAG"
        return "CRITICAL"

    df["variance_status"] = df["variance_pct"].apply(status)
    return df

def save_reconciliations(df):
    df = df.copy()
    df["reconciled_at"] = datetime.now().isoformat()

    cols = [
        "sku", "description", "location", "count_date",
        "system_qty", "physical_qty",
        "variance_qty", "variance_pct", "variance_status",
        "reconciled_at",
    ]
    df = df[cols]

    conn = get_db()
    conn.execute("DELETE FROM reconciliations")  
    df.to_sql("reconciliations", conn, if_exists="append", index=False)
    conn.close()

def run_reconcile():
    df = load_counts()
    if df.empty:
        print("No data in counts. Run ingest first.")
        return 0

    df = compute_variance(df)
    save_reconciliations(df)

    flagged = (df["variance_status"] != "OK").sum()
    print(f"{len(df)} rows reconciled | {flagged} flagged")
    return len(df)

if __name__ == "__main__":
    run_reconcile()

