"""Clean the raw pulls and build the feature table.

Reads the raw files in data/raw/ (yahoo, fred, alphavantage), aligns them to
JPM's trading calendar, computes the feature columns, and writes one table to
data/processed/features.parquet.

Covers 11 features from the three sources you already have. The two
LSEG-dependent columns (news sentiment, and optionally a second correlation
feature) are left as labeled slots to fill once that pull works.

Run from the repo root:  python src/build_features.py
"""
from pathlib import Path
import sys
import yaml
import numpy as np
import pandas as pd

TRADING_DAYS = 252  # trading days per year, for annualizing volatility


def load_config():
    cfg_path = Path(__file__).resolve().parents[1] / "config.yaml"
    with open(cfg_path) as f:
        return yaml.safe_load(f)


def iqr_flags(s: pd.Series, k: float = 1.5) -> int:
    """Count points beyond k*IQR of the quartiles. Report only, do not clip:
    real spikes (e.g. March 2020) are data, not errors."""
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    lo, hi = q1 - k * iqr, q3 + k * iqr
    return int(((s < lo) | (s > hi)).sum())


def main():
    cfg = load_config()
    root = Path(__file__).resolve().parents[1]
    raw_dir = root / cfg["paths"]["raw_dir"]
    proc_dir = root / cfg["paths"].get("processed_dir", "data/processed")
    proc_dir.mkdir(parents=True, exist_ok=True)

    # ---- load raw ----
    yahoo = pd.read_parquet(raw_dir / "yahoo.parquet")            # jpm_close, vix_close
    fred = pd.read_parquet(raw_dir / "fred.parquet")             # dgs1, dgs3mo
    div = pd.read_parquet(raw_dir / "alphavantage_dividends.parquet")  # dividend (events)

    # ---- master calendar: JPM trading days ----
    # Yahoo's index is the true set of days the market was open; everything
    # else aligns to it.
    calendar = yahoo.index
    df = pd.DataFrame(index=calendar)
    df.index.name = "date"

    # ---- carry the raw levels onto the calendar ----
    df["jpm_close"] = yahoo["jpm_close"]
    df["vix_close"] = yahoo["vix_close"]

    # FRED: reindex to trading days, forward-fill holiday gaps (a rate holds
    # until the next quote).
    fred_aligned = fred.reindex(calendar).ffill()
    df["dgs1"] = fred_aligned["dgs1"]
    df["dgs3mo"] = fred_aligned["dgs3mo"]

    # Dividends: expand 28 events onto the daily calendar.
    # daily_div = amount on ex-dates, 0 otherwise.
    daily_div = div["dividend"].reindex(calendar).fillna(0.0)
    # trailing 12-month dividend = rolling 252-day sum (warms up over year 1).
    trailing_annual_div = daily_div.rolling(TRADING_DAYS, min_periods=1).sum()

    # ================= features =================
    # log return: ln(S_t / S_{t-1}); basis for volatility and a feature itself.
    ret = np.log(df["jpm_close"] / df["jpm_close"].shift(1))

    df["ret"] = ret                                              # 1. daily return
    df["vol_20"] = ret.rolling(20).std() * np.sqrt(TRADING_DAYS)  # 2. realized vol 20d
    df["vol_60"] = ret.rolling(60).std() * np.sqrt(TRADING_DAYS)  # 3. realized vol 60d
    df["momentum_20"] = df["jpm_close"] / df["jpm_close"].shift(20) - 1   # 4
    df["momentum_60"] = df["jpm_close"] / df["jpm_close"].shift(60) - 1   # 5
    # 6. vix_close already a column (the volatility signal)
    # 7. dgs1 already a column (1-year rate level)
    # 8. dgs3mo already a column (3-month rate level)
    df["rate_momentum"] = df["dgs1"].diff(20)                    # 9. change in 1y rate
    df["dividend_yield"] = trailing_annual_div / df["jpm_close"]  # 10. q

    # 11. rolling 60-day correlation between JPM returns and VIX change.
    #     Buildable now since VIX is present.
    df["vix_jpm_corr_60"] = ret.rolling(60).corr(df["vix_close"].diff())

    # ---- LSEG slots (fill after the Workspace pull) ----
    df["sentiment"] = np.nan            # 12. news sentiment score [0,1]  (LSEG)

    # ---- report ----
    print(f"[features] rows={len(df)} "
          f"range={df.index.min().date()}..{df.index.max().date()}")
    print(f"[features] columns={list(df.columns)}")
    print("[features] IQR outlier flags (report only, not clipped):")
    for col in ["jpm_close", "vix_close", "dgs1", "ret"]:
        print(f"           {col}: {iqr_flags(df[col].dropna())}")
    # early rows carry NaN from the rolling windows warming up; this is expected.
    print(f"[features] rows with any NaN (window warm-up + empty LSEG slot): "
          f"{int(df.drop(columns=['sentiment']).isna().any(axis=1).sum())}")

    dest = proc_dir / "features.parquet"
    df.to_parquet(dest)
    print(f"[features] saved {dest}")


if __name__ == "__main__":
    main()
