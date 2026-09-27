"""LSEG Workspace pull - TEMPLATE.

Covers data spec fields 6 (news sentiment) and 7 (JPM option settlement prices).

This does NOT run from your machine like the other scripts. LSEG data lives
inside Workspace, so run this inside the Workspace CodeBook notebook, where the
`lseg.data` library is preauthenticated by your session. No .env key applies.

Field names and function signatures below are placeholders; confirm the exact
ones in CodeBook's documentation once you are in, since they vary by entitlement.
Save the result to data/raw/ so it joins the other sources.
"""
# --- Run inside Workspace CodeBook ---

# import lseg.data as ld
# ld.open_session()   # uses your active Workspace session

START = "2018-01-01"
END = "2024-12-31"
UNDERLYING = "JPM.N"     # LSEG RIC for JPMorgan on NYSE

# --- Field 6: news sentiment ---
# Reuters News sentiment. The exact call depends on your entitlement; typical
# shape pulls news/sentiment analytics for the RIC over the window, then reduces
# to one daily score in [0, 1].
#
# news = ld.news.get_headlines(query="R:JPM.N", start=START, end=END)
# sentiment_daily = summarize_sentiment(news)   # your reduction to a daily score

# --- Field 7: JPM option settlement prices ---
# Pull the JPM option chain and its end-of-day settlement prices. Each contract
# (strike, expiry) is its own row per date, so this is many rows per day.
#
# chain = ld.get_data(universe=["JPM.N"], fields=["TR.OptionChain"])
# settle = ld.get_data(
#     universe=chain_rics,
#     fields=["TR.SettlementPrice", "TR.StrikePrice", "TR.ExpirationDate"],
#     parameters={"SDate": START, "EDate": END, "Frq": "D"},
# )

# --- Save so it joins the other raw files ---
# sentiment_daily.to_parquet("data/raw/lseg_sentiment.parquet")
# settle.to_parquet("data/raw/lseg_option_settle.parquet")

# ld.close_session()

if __name__ == "__main__":
    raise SystemExit(
        "This is a CodeBook template. Run it inside LSEG Workspace, not locally."
    )
