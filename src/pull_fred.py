"""Pull Treasury rates from FRED.

Covers data spec fields 4 (DGS1, risk-free r) and 5 (DGS3MO, rate-momentum feature).
No API key required (pandas_datareader uses the public FRED endpoint).
Rates are quoted in percent; converted to decimals here.

Run from the repo root:  python src/pull_fred.py
"""
from pathlib import Path
import sys
import yaml
import pandas_datareader.data as web


def load_config():
    cfg_path = Path(__file__).resolve().parents[1] / "config.yaml"
    with open(cfg_path) as f:
        return yaml.safe_load(f)


def main():
    cfg = load_config()
    start = cfg["data"]["start"]
    end = cfg["data"]["end"]

    raw_dir = Path(__file__).resolve().parents[1] / cfg["paths"]["raw_dir"]
    raw_dir.mkdir(parents=True, exist_ok=True)

    series = ["DGS1", "DGS3MO"]
    df = web.DataReader(series, "fred", start, end)
    df.columns = ["dgs1", "dgs3mo"]
    df = df / 100.0            # percent -> decimal
    df.index.name = "date"

    dest = raw_dir / "fred.parquet"
    df.to_parquet(dest)

    print(f"[fred] saved {dest}")
    print(f"[fred] rows={len(df)} range={df.index.min().date()}..{df.index.max().date()}")
    print(f"[fred] nulls: dgs1={int(df.dgs1.isna().sum())} "
          f"dgs3mo={int(df.dgs3mo.isna().sum())}  (blanks on non-trading days are expected)")
    if len(df) == 0:
        print("[fred] WARNING: empty result", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
