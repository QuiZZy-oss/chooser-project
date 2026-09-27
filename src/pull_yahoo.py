"""Pull JPM close price and VIX close from Yahoo Finance.

Covers data spec fields 1 (JPM close, S) and 3 (VIX close, feature).
No API key required.

Run from the repo root:  python src/pull_yahoo.py
"""
from pathlib import Path
import sys
import yaml
import yfinance as yf


def load_config():
    cfg_path = Path(__file__).resolve().parents[1] / "config.yaml"
    with open(cfg_path) as f:
        return yaml.safe_load(f)


def main():
    cfg = load_config()
    start = cfg["data"]["start"]
    end = cfg["data"]["end"]
    ticker = cfg["contract"]["underlying"]
    vix_ticker = cfg["data"]["vix_ticker"]
    adjusted = cfg["data"]["adjusted_close"]

    raw_dir = Path(__file__).resolve().parents[1] / cfg["paths"]["raw_dir"]
    raw_dir.mkdir(parents=True, exist_ok=True)

    # auto_adjust=True gives split/dividend-adjusted close; False gives raw close.
    jpm = yf.download(ticker, start=start, end=end,
                      auto_adjust=adjusted, progress=False)[["Close"]]
    jpm.columns = ["jpm_close"]

    vix = yf.download(vix_ticker, start=start, end=end,
                      auto_adjust=False, progress=False)[["Close"]]
    vix.columns = ["vix_close"]

    out = jpm.join(vix, how="outer")
    out.index.name = "date"

    dest = raw_dir / "yahoo.parquet"
    out.to_parquet(dest)

    close_kind = "adjusted" if adjusted else "raw"
    print(f"[yahoo] saved {dest}")
    print(f"[yahoo] JPM close = {close_kind}")
    print(f"[yahoo] rows={len(out)} range={out.index.min().date()}..{out.index.max().date()}")
    print(f"[yahoo] nulls: jpm_close={int(out.jpm_close.isna().sum())} "
          f"vix_close={int(out.vix_close.isna().sum())}")
    if len(out) == 0:
        print("[yahoo] WARNING: empty result", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
