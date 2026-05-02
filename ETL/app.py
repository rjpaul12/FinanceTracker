from flask import Flask, render_template
import sqlite3

app = Flask(__name__)
DB_PATH = "database.db"

def get_data():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   
    cur = conn.cursor()
    cur.execute("SELECT * FROM financials_clean ORDER BY ticker, fiscal_year DESC")
    rows = cur.fetchall()
    conn.close()
    return rows

@app.route("/")
def index():
    data = get_data()
    return render_template("index.html", records=data)

@app.route("/run-etl")
def run_etl():
    import etl
    all_records = []
    for ticker in etl.TICKERS:
        raw   = etl.extract(ticker)
        clean = etl.transform(raw, ticker)
        all_records.extend(clean)
    etl.load(all_records)
    return "<h2>✅ ETL Complete! <a href='/'>Go back</a></h2>"

if __name__ == "__main__":
    app.run(debug=True)