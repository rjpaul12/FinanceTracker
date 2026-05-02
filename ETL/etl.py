import requests
import sqlite3
from datetime import datetime

# ── CONFIG ──────────────────────────────────────────
API_KEY  = "yiIAtQOnuvVOHRlxJCki6iBk9QCEsz3L"
TICKERS  = ["AAPL", "MSFT", "SONY"]
DB_PATH  = "database.db"

# ── EXTRACT ─────────────────────────────────
def extract(ticker):
    url = f"https://financialmodelingprep.com/stable/income-statement?symbol={ticker}&limit=5&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()
    if not isinstance(data, list):
        raise ValueError(f"Unexpected API response for {ticker}: {data}")
    return data

# ── TRANSFORM ────────────────────────────────
def transform(raw_data, ticker):
    cleaned = []
    for record in raw_data:
        revenue    = record.get("revenue", 0) or 0
        net_income = record.get("netIncome", 0) or 0
        gross      = record.get("grossProfit", 0) or 0
        date_str   = record.get("date", "")
        year       = int(date_str[:4]) if date_str else 0

        margin = round((net_income / revenue) * 100, 2) if revenue else 0

        if margin >= 20:
            health = "Strong"
        elif margin >= 10:
            health = "Moderate"
        else:
            health = "Weak"

        cleaned.append({
            "company"         : record.get("symbol", ticker),
            "ticker"          : ticker,
            "fiscal_year"     : year,
            "revenue"         : round(revenue / 1_000_000, 2),
            "net_income"      : round(net_income / 1_000_000, 2),
            "gross_profit"    : round(gross / 1_000_000, 2),
            "profit_margin"   : margin,
            "financial_health": health,
            "loaded_at"       : datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    return cleaned

# ──LOAD ─────────────────────────────────────
def load(records):
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS financials_clean (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            company          TEXT,
            ticker           TEXT,
            fiscal_year      INTEGER,
            revenue          REAL,
            net_income       REAL,
            gross_profit     REAL,
            profit_margin    REAL,
            financial_health TEXT,
            loaded_at        TEXT
        )
    """)

    cur.execute("DELETE FROM financials_clean")

    for r in records:
        cur.execute("""
            INSERT INTO financials_clean
            (company, ticker, fiscal_year, revenue, net_income, gross_profit, profit_margin, financial_health, loaded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (r["company"], r["ticker"], r["fiscal_year"], r["revenue"],
              r["net_income"], r["gross_profit"], r["profit_margin"],
              r["financial_health"], r["loaded_at"]))

    conn.commit()
    conn.close()
    print(f"ETL complete! {len(records)} records loaded into database.")

# ── RUN ──────────────────────────────────────────────
if __name__ == "__main__":
    all_records = []
    for ticker in TICKERS:
        print(f"Fetching {ticker}...")
        raw   = extract(ticker)
        clean = transform(raw, ticker)
        print(f"  → {len(clean)} records")
        all_records.extend(clean)
    load(all_records)