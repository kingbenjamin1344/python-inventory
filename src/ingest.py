import os
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd

# ---------- STEP 1: Paths ----------
BASE_DIR = Path(__file__).resolve().parent.parent
INCOMING = BASE_DIR / "data" / "incoming"
PROCESSED = BASE_DIR / "data" / "processed"
REJECTED = BASE_DIR / "data" / "rejected"
DB_PATH = BASE_DIR / "data" / "inventory.db"

REQUIRED_COLUMNS = [
    "sku",
    "description",
    "location",
    "system_qty",
    "physical_qty",
    "count_date",
]

def get_db():
    """Open DB connection and create the 'counts' table if missing."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS counts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT,
            description TEXT,
            location TEXT,
            system_qty INTEGER,
            physical_qty INTEGER,
            count_date TEXT,
            ingested_at TEXT,
            source_file TEXT
        )
    """)
    conn.commit()
    return conn

def validate_columns(df):
    """Return (True, None) if valid, (False, reason) if not."""
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        return False, f"Missing columns: {missing}"
    return True, None

def save_to_db(df, filename):
    """Append dataframe rows into the counts table."""
    df = df.copy()
    df["ingested_at"] = datetime.now().isoformat()
    df["source_file"] = filename

    conn = get_db()
    df.to_sql("counts", conn, if_exists="append", index=False)
    conn.close()

def move_file(filepath, destination):
    """Move a file to destination folder."""
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / filepath.name
    shutil.move(str(filepath), str(target))

def run_ingest():
    """Read every file in incoming/, save to DB, move to processed or rejected."""
    processed = 0
    rejected = 0
    errors = []

    for filepath in INCOMING.iterdir():
        if not filepath.is_file():
            continue
        if filepath.suffix.lower() not in [".xlsx", ".xls", ".csv"]:
            continue

        try:
            if filepath.suffix.lower() == ".csv":
                df = pd.read_csv(filepath)
            else:
                df = pd.read_excel(filepath)

            ok, reason = validate_columns(df)
            if not ok:
                errors.append(f"{filepath.name}: {reason}")
                move_file(filepath, REJECTED)
                rejected += 1
                continue

            save_to_db(df, filepath.name)
            move_file(filepath, PROCESSED)
            processed += 1

        except Exception as e:
            errors.append(f"{filepath.name}: {e}")
            move_file(filepath, REJECTED)
            rejected += 1

    print(f"✅ {processed} processed | ⚠️ {rejected} rejected")
    for err in errors:
        print("  -", err)
    return processed, rejected, errors


if __name__ == "__main__":
    run_ingest()