import yfinance as yf
import sqlite3
import json
from datetime import datetime

TICKERS = ["AAPL", "MSFT", "SONY"]
DB_PATH = "database.db"

# ── EXTRACT AND LOAD RAW ──────────────
def extract_and_load_raw(ticker):
    stock = yf.Ticker(ticker)
    raw_df = stock.financials

    if raw_df is None or raw_df.empty:
        print(f"No data for {ticker}")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS staging_financials (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_ticker   TEXT,
            raw_date     TEXT,
            raw_revenue  TEXT,
            raw_net_income TEXT,
            raw_gross_profit TEXT,
            raw_json     TEXT,
            loaded_at    TEXT
        )
    """)

    cur.execute("DELETE FROM staging_financials WHERE raw_ticker = ?", (ticker,))

    for col in raw_df.columns:
        date_str = str(col.date())
        revenue    = str(raw_df.loc["Total Revenue", col])  if "Total Revenue" in raw_df.index else "None"
        net_income = str(raw_df.loc["Net Income", col])     if "Net Income"    in raw_df.index else "None"
        gross      = str(raw_df.loc["Gross Profit", col])   if "Gross Profit"  in raw_df.index else "None"
        raw_json   = json.dumps({str(k): str(v) for k, v in raw_df[col].items()})

        cur.execute("""
            INSERT INTO staging_financials
            (raw_ticker, raw_date, raw_revenue, raw_net_income, raw_gross_profit, raw_json, loaded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (ticker, date_str, revenue, net_income, gross, raw_json,
              datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    conn.commit()
    conn.close()
    print(f"Loaded raw data for {ticker} into staging_financials")

# ── TRANSFORM INSIDE THE DATABASE (via SQL) ──
def transform_in_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS production_financials (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            company          TEXT,
            ticker           TEXT,
            fiscal_year      INTEGER,
            revenue          REAL,
            net_income       REAL,
            gross_profit     REAL,
            profit_margin    REAL,
            financial_health TEXT,
            transformed_at   TEXT
        )
    """)

    cur.execute("DELETE FROM production_financials")

    cur.execute("""
        INSERT INTO production_financials
            (company, ticker, fiscal_year, revenue, net_income, gross_profit, profit_margin, financial_health, transformed_at)
        SELECT
            raw_ticker,
            raw_ticker,
            CAST(SUBSTR(raw_date, 1, 4) AS INTEGER),
            ROUND(CAST(raw_revenue    AS REAL) / 1000000.0, 2),
            ROUND(CAST(raw_net_income AS REAL) / 1000000.0, 2),
            ROUND(CAST(raw_gross_profit AS REAL) / 1000000.0, 2),
            ROUND(
                CAST(raw_net_income AS REAL) /
                NULLIF(CAST(raw_revenue AS REAL), 0) * 100
            , 2),
            CASE
                WHEN CAST(raw_net_income AS REAL) / NULLIF(CAST(raw_revenue AS REAL), 0) >= 0.20 THEN 'Strong'
                WHEN CAST(raw_net_income AS REAL) / NULLIF(CAST(raw_revenue AS REAL), 0) >= 0.10 THEN 'Moderate'
                ELSE 'Weak'
            END,
            datetime('now', 'localtime')
        FROM staging_financials
        WHERE raw_revenue != 'None' AND raw_net_income != 'None'
    """)

    conn.commit()
    conn.close()
    print("SQL transformation complete! production_financials is ready.")

# ── RUN ──────────────────────────────────────────────
if __name__ == "__main__":
    for ticker in TICKERS:
        extract_and_load_raw(ticker)
    transform_in_db()