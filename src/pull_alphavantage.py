"""Pull JPM dividends from Alpha Vantage.

Covers data spec field 2 (dividends, yield q).
Requires a free API key in a git-ignored .env file:

    ALPHAVANTAGE_API_KEY=your_key_here

Get a key at https://www.alphavantage.co/support/#api-key
Run from the repo root:  python src/pull_alphavantage.py
"""
from pathlib import Path
import os
import sys
import yaml
import requests
import pandas as pd
from dotenv import load_dotenv


def load_config():
    cfg_path = Path(__file__).resolve().parents[1] / "config.yaml"
    with open(cfg_path) as f:
        return yaml.safe_load(f)


def main():
    cfg = load_config()
    ticker = cfg["contract"]["underlying"]
    start = cfg["data"]["start"]
    end = cfg["data"]["end"]

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    key = os.getenv("ALPHAVANTAGE_API_KEY")
    if not key:
        print("[alphavantage] ERROR: ALPHAVANTAGE_API_KEY not found in .env", file=sys.stderr)
        sys.exit(1)

    raw_dir = Path(__file__).resolve().parents[1] / cfg["paths"]["raw_dir"]
    raw_dir.mkdir(parents=True, exist_ok=True)

    resp = requests.get(
        "https://www.alphavantage.co/query",
        params={"function": "DIVIDENDS", "symbol": ticker, "apikey": key},
        timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json()

    # Alpha Vantage returns a note (not data) when the rate limit is hit.
    if "data" not in payload:
        print(f"[alphavantage] unexpected response: {payload}", file=sys.stderr)
        sys.exit(1)

    df = pd.DataFrame(payload["data"])
    if df.empty:
        print("[alphavantage] WARNING: no dividend rows returned", file=sys.stderr)
        sys.exit(1)

    df["ex_dividend_date"] = pd.to_datetime(df["ex_dividend_date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df = (df.dropna(subset=["ex_dividend_date"])
            .loc[df["ex_dividend_date"].between(start, end)]
            .sort_values("ex_dividend_date")
            .set_index("ex_dividend_date")[["amount"]])
    df.index.name = "date"
    df.columns = ["dividend"]

    dest = raw_dir / "alphavantage_dividends.parquet"
    df.to_parquet(dest)

    print(f"[alphavantage] saved {dest}")
    print(f"[alphavantage] dividend events in window: {len(df)}")
    if len(df):
        print(f"[alphavantage] range={df.index.min().date()}..{df.index.max().date()}")


if __name__ == "__main__":
    main()
