import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path

import pandas as pd

logger = logging.getLogger("inventra.db")

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
DB_PATH = Path(__file__).resolve().parent / "inventra.db"

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db(force_reload_csv: bool = False):
    with get_db_connection() as conn:
        cur = conn.cursor()

        # Check if core tables already exist to avoid unnecessary disk I/O on every Streamlit rerun
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='inventory'")
        already_seeded = cur.fetchone() is not None

        if not already_seeded or force_reload_csv:
            csv_table_map = {
                "vendors.csv": "vendors",
                "inventory.csv": "inventory",
                "finance.csv": "finance",
                "sales.csv": "sales_history",
            }
            for csv_filename, table_name in csv_table_map.items():
                csv_path = DATA_DIR / csv_filename
                if not csv_path.exists():
                    raise FileNotFoundError(f"Missing required CSV file: {csv_path}")
                df = pd.read_csv(csv_path)
                df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
                df.to_sql(table_name, conn, if_exists="replace", index=False)
                logger.info("Loaded %s (%d rows) into '%s'", csv_filename, len(df), table_name)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id TEXT PRIMARY KEY,
            sku TEXT,
            issue_type TEXT,
            rationale TEXT,
            forecasted_demand INTEGER,
            recommended_qty INTEGER,
            financial_impact REAL,
            vendor_id TEXT,
            status TEXT DEFAULT 'OPEN',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_query TEXT,
            region TEXT,
            weather_summary TEXT,
            agent_decisions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Auto-migrate existing audit_logs table if 'region' column is missing
        existing_cols = [row[1] for row in cur.execute("PRAGMA table_info(audit_logs)").fetchall()]
        if "region" not in existing_cols:
            cur.execute("ALTER TABLE audit_logs ADD COLUMN region TEXT DEFAULT 'All'")

def update_ticket_status(ticket_id: str, new_status: str):
    with get_db_connection() as conn:
        conn.execute(
            "UPDATE tickets SET status = ? WHERE ticket_id = ?",
            (new_status, ticket_id),
        )
