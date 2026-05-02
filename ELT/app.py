from flask import Flask, render_template
import sqlite3

app = Flask(__name__)
DB_PATH = "database.db"

def get_staging():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM staging_financials ORDER BY raw_ticker, raw_date DESC")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_production():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM production_financials ORDER BY ticker, fiscal_year DESC")
    rows = cur.fetchall()
    conn.close()
    return rows

@app.route("/")
def index():
    staging = get_staging()
    production = get_production()
    return render_template("index.html", staging=staging, production=production)

@app.route("/run-elt")
def run_elt():
    import elt
    for ticker in elt.TICKERS:
        elt.extract_and_load_raw(ticker)
    elt.transform_in_db()
    return "<h2>✅ ELT Complete! <a href='/'>Go back</a></h2>"

if __name__ == "__main__":
    app.run(debug=True, port=5001)