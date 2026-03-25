import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
import yfinance as yf

# =========================
# Configuration
# =========================
DB_PATH = Path("docs/fx_rates.db")
JSON_OUT_PATH = Path("docs/latest_rates.json")

# 監視対象の通貨ペア (Base, Target) - 全12方向の組み合わせ
TARGET_PAIRS = [
    ("USD", "EUR"), ("EUR", "USD"),
    ("USD", "CAD"), ("CAD", "USD"),
    ("USD", "MXN"), ("MXN", "USD"),
    ("USD", "JPY"), ("JPY", "USD"),
    ("USD", "GBP"), ("GBP", "USD"),
    ("EUR", "GBP"), ("GBP", "EUR")
]

# Mastercard API Base Settings
PAGE_URL = "https://www.mastercard.com/us/en/personal/get-support/currency-exchange-rate-converter.html"
CSRF_URL = "https://www.mastercard.com/libs/granite/csrf/token.json"
API_BASE_URL = (
    "https://www.mastercard.com/marketingservices/public/mccom-services/"
    "currency-conversions/conversion-rates"
    "?exchange_date=0000-00-00"
    "&bank_fee=0"
    "&transaction_amount=1"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "*/*",
    "Referer": PAGE_URL,
}

# =========================
# Database Functions
# =========================
def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS fx_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fetched_at_utc TEXT NOT NULL,
            currency_pair TEXT NOT NULL,
            mastercard_rate REAL,
            market_rate REAL,
            diff REAL,
            opportunity INTEGER,
            error_message TEXT
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_fx_snapshots_time ON fx_snapshots(fetched_at_utc)")
    conn.commit()
    conn.close()

def insert_snapshot(fetched_at_utc, pair_str, mc_rate, market_rate, diff, opportunity, error_msg):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO fx_snapshots (fetched_at_utc, currency_pair, mastercard_rate, market_rate, diff, opportunity, error_message)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (fetched_at_utc, pair_str, mc_rate, market_rate, diff, int(opportunity) if opportunity is not None else None, error_msg))
    conn.commit()
    conn.close()

# =========================
# Fetch Logic
# =========================
def get_mastercard_rate(session, base, target):
    url = f"{API_BASE_URL}&transaction_currency={base}&cardholder_billing_currency={target}"
    r = session.get(url, headers=HEADERS, timeout=20)
    if r.status_code != 200:
        raise RuntimeError(f"Mastercard API failed: {r.status_code}")
    return float(r.json()["data"]["conversionRate"])

def get_market_rate(base, target):
    ticker = f"{base}{target}=X"
    df = yf.download(tickers=ticker, period="1d", interval="1m", progress=False)
    if df.empty:
        raise RuntimeError(f"Yahoo Finance returned no data for {ticker}")
    close_data = df["Close"].dropna()
    if close_data.empty:
        raise RuntimeError(f"No valid Close price for {ticker}")
    
    if isinstance(close_data, pd.Series):
        return float(close_data.iloc[-1])
    else:
        return float(close_data.iloc[-1, 0])

def main():
    init_db()
    fetched_at_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    
    session = requests.Session()
    # Fetch CSRF token once
    session.get(CSRF_URL, headers=HEADERS, timeout=20)

    results = []

    for base, target in TARGET_PAIRS:
        pair_str = f"{base}/{target}"
        mc_rate, market_rate, diff, opportunity, err = None, None, None, None, None
        
        try:
            mc_rate = get_mastercard_rate(session, base, target)
            market_rate = get_market_rate(base, target)
            diff = mc_rate - market_rate
            opportunity = mc_rate <= market_rate
            
            print(f"[{pair_str}] MC: {mc_rate:.6f}, Yahoo: {market_rate:.6f}, Opp: {opportunity}")
        except Exception as e:
            err = str(e)
            print(f"[{pair_str}] ERROR: {err}")

        insert_snapshot(fetched_at_utc, pair_str, mc_rate, market_rate, diff, opportunity, err)
        
        results.append({
            "pair": pair_str,
            "base": base,
            "target": target,
            "mastercard_rate": mc_rate,
            "market_rate": market_rate,
            "diff": diff,
            "opportunity": opportunity,
            "error": err
        })

    # Export to JSON for frontend
    output_data = {
        "fetched_at_utc": fetched_at_utc,
        "rates": results
    }
    with open(JSON_OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
        
    print("-" * 40)
    print(f"✅ DB (fx_rates.db) に {len(TARGET_PAIRS)}ペアのデータを保存しました。")
    print(f"✅ JSON (latest_rates.json) を更新しました。")

if __name__ == "__main__":
    main()